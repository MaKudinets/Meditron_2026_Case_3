from __future__ import annotations

from collections import defaultdict
from threading import RLock
from typing import Any, Dict, Mapping
import uuid

import pandas as pd

from .facts import (
    as_series,
    build_conflict_events,
    build_rule_score_events,
)
from .knowledge_base import (
    RULE_TARGETS,
    STRONG_RULE,
    WEAK_RULE,
    HIGH_ML_PROBABILITY,
    LOW_ML_PROBABILITY,
    compute_rule_scores,
    rule_state,
)
from .recommendations import build_recommendation_events
from .explanations import build_evidence


RULESET_NAME = "meditron_expert_v1"
RECOMMENDATION_PROBABILITY = 0.50

try:
    from durable.lang import ruleset, when_all, m, post
    DURABLE_AVAILABLE = True
    _DURABLE_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - environment dependent
    DURABLE_AVAILABLE = False
    _DURABLE_IMPORT_ERROR = exc


_ENGINE_LOCK = RLock()
_RESULTS: dict[str, dict[str, Any]] = {}


def ensure_durable_available() -> None:
    if not DURABLE_AVAILABLE:
        raise RuntimeError(
            "Durable Rules is required for production expert inference. "
            "Install it with `pip install durable_rules==2.0.28`. "
            f"Original import error: {_DURABLE_IMPORT_ERROR!r}"
        )


def _collector(run_id: str) -> dict[str, Any]:
    return _RESULTS[run_id]


def _record_fired(run_id: str, rule_id: str) -> None:
    _collector(run_id)["fired_rules"].append(rule_id)


if DURABLE_AVAILABLE:
    with ruleset(RULESET_NAME):

        @when_all(
            (m.kind == "rule_state")
            & (m.score >= STRONG_RULE)
        )
        def state_supports(c):
            rid = str(c.m.run_id)
            target = str(c.m.target)
            _collector(rid)["rule_states"][target] = "supports"
            _record_fired(rid, f"{target}:RULE_STATE_SUPPORTS")

        @when_all(
            (m.kind == "rule_state")
            & (m.score <= WEAK_RULE)
        )
        def state_against(c):
            rid = str(c.m.run_id)
            target = str(c.m.target)
            _collector(rid)["rule_states"][target] = "against"
            _record_fired(rid, f"{target}:RULE_STATE_AGAINST")

        @when_all(
            (m.kind == "rule_state")
            & (m.score > WEAK_RULE)
            & (m.score < STRONG_RULE)
        )
        def state_unknown(c):
            rid = str(c.m.run_id)
            target = str(c.m.target)
            _collector(rid)["rule_states"][target] = "unknown"
            _record_fired(rid, f"{target}:RULE_STATE_UNKNOWN")

        @when_all(
            (m.kind == "decision")
            & (m.probability >= HIGH_ML_PROBABILITY)
            & (m.rule_score <= WEAK_RULE)
        )
        def conflict_ml_positive_rule_negative(c):
            rid = str(c.m.run_id)
            item = {
                "target": str(c.m.target),
                "type": "ml_positive_rule_negative",
                "severity": "review",
                "ensemble_probability": float(c.m.probability),
                "rule_score": float(c.m.rule_score),
                "rule_state": "against",
                "message": (
                    "Высокая ML-вероятность при явном clinical evidence "
                    "против соответствующего состояния."
                ),
            }
            _collector(rid)["conflicts"].append(item)
            _record_fired(
                rid,
                f"{c.m.target}:CONFLICT_ML_POSITIVE_RULE_NEGATIVE",
            )

        @when_all(
            (m.kind == "decision")
            & (m.probability <= LOW_ML_PROBABILITY)
            & (m.rule_score >= STRONG_RULE)
        )
        def conflict_ml_negative_rule_positive(c):
            rid = str(c.m.run_id)
            item = {
                "target": str(c.m.target),
                "type": "ml_negative_rule_positive",
                "severity": "review",
                "ensemble_probability": float(c.m.probability),
                "rule_score": float(c.m.rule_score),
                "rule_state": "supports",
                "message": (
                    "Clinical rule layer сильно поддерживает состояние, "
                    "а ML-вероятность низкая."
                ),
            }
            _collector(rid)["conflicts"].append(item)
            _record_fired(
                rid,
                f"{c.m.target}:CONFLICT_ML_NEGATIVE_RULE_POSITIVE",
            )

        @when_all(
            (m.kind == "recommendation")
            & (m.missing == True)
            & (m.probability >= RECOMMENDATION_PROBABILITY)
        )
        def recommend_missing_test(c):
            rid = str(c.m.run_id)
            item = {
                "test": str(c.m.test),
                "target": str(c.m.target),
                "reason": str(c.m.reason),
            }

            seen = _collector(rid)["recommendation_keys"]
            key = (item["test"], item["target"])

            if key not in seen:
                seen.add(key)
                _collector(rid)["recommended_next_tests"].append(item)

            _record_fired(
                rid,
                f"{c.m.target}:RECOMMEND_{c.m.test}",
            )

        # Catch-all: prevents MessageNotHandledException for events that
        # intentionally do not meet a clinical action condition.
        @when_all(m.kind != "__never__")
        def observed(c):
            pass


def run_expert_engine(
    patient: Mapping[str, Any] | pd.Series,
    probabilities: Mapping[str, float],
    predictions: Mapping[str, int],
) -> Dict[str, Any]:
    """
    Run the production expert layer through Durable Rules.

    ML probabilities are never modified by the rule engine.
    The engine produces interpretation only:
    rule states, conflicts, fired rules and recommended tests.
    """
    ensure_durable_available()

    row = as_series(patient)

    missing_targets = [
        target for target in RULE_TARGETS
        if target not in probabilities or target not in predictions
    ]
    if missing_targets:
        raise ValueError(
            "Missing ML outputs for targets: " + ", ".join(missing_targets)
        )

    probabilities = {
        target: float(probabilities[target])
        for target in RULE_TARGETS
    }
    predictions = {
        target: int(predictions[target])
        for target in RULE_TARGETS
    }

    rule_scores = compute_rule_scores(row)
    run_id = uuid.uuid4().hex

    result = {
        "rule_scores": dict(rule_scores),
        "rule_states": {},
        "conflicts": [],
        "recommended_next_tests": [],
        "recommendation_keys": set(),
        "fired_rules": [],
        "evidence": build_evidence(row),
    }

    with _ENGINE_LOCK:
        _RESULTS[run_id] = result
        try:
            for event in build_rule_score_events(run_id, rule_scores):
                post(RULESET_NAME, event)

            for event in build_conflict_events(
                run_id,
                probabilities,
                predictions,
                rule_scores,
            ):
                post(RULESET_NAME, event)

            for event in build_recommendation_events(
                run_id,
                row,
                probabilities,
            ):
                post(RULESET_NAME, event)

            completed = _RESULTS.pop(run_id)
        except Exception:
            _RESULTS.pop(run_id, None)
            raise

    # Defensive fallback: every score should have fired exactly one
    # supports/against/unknown rule.
    for target in RULE_TARGETS:
        completed["rule_states"].setdefault(
            target,
            rule_state(rule_scores[target]),
        )

    completed.pop("recommendation_keys", None)
    return completed
