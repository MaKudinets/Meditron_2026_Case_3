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
    assess_all_hypotheses,
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


# ============================================================
# Durable Rules availability
# ============================================================

def ensure_durable_available() -> None:
    """
    Проверяет, установлен ли Durable Rules.

    Production expert inference должен использовать Durable Rules,
    поэтому при отсутствии библиотеки выполнение останавливается.
    """

    if not DURABLE_AVAILABLE:
        raise RuntimeError(
            "Durable Rules is required for production expert inference. "
            "Install it with `pip install durable_rules==2.0.28`. "
            f"Original import error: {_DURABLE_IMPORT_ERROR!r}"
        )


# ============================================================
# Internal collectors
# ============================================================

def _collector(run_id: str) -> dict[str, Any]:
    """
    Возвращает контейнер результатов конкретного запуска.
    """

    return _RESULTS[run_id]


def _record_fired(
    run_id: str,
    rule_id: str,
) -> None:
    """
    Сохраняет идентификатор сработавшего правила.
    """

    _collector(run_id)["fired_rules"].append(rule_id)


# ============================================================
# Durable Rules knowledge engine
# ============================================================

if DURABLE_AVAILABLE:

    with ruleset(RULESET_NAME):

        # ----------------------------------------------------
        # Rule state: supports
        # ----------------------------------------------------

        @when_all(
            (m.kind == "rule_state")
            & (m.score >= STRONG_RULE)
        )
        def state_supports(c):

            rid = str(c.m.run_id)
            target = str(c.m.target)

            _collector(rid)["rule_states"][target] = "supports"

            _record_fired(
                rid,
                f"{target}:RULE_STATE_SUPPORTS",
            )

        # ----------------------------------------------------
        # Rule state: against
        # ----------------------------------------------------

        @when_all(
            (m.kind == "rule_state")
            & (m.score <= WEAK_RULE)
        )
        def state_against(c):

            rid = str(c.m.run_id)
            target = str(c.m.target)

            _collector(rid)["rule_states"][target] = "against"

            _record_fired(
                rid,
                f"{target}:RULE_STATE_AGAINST",
            )

        # ----------------------------------------------------
        # Rule state: unknown
        # ----------------------------------------------------

        @when_all(
            (m.kind == "rule_state")
            & (m.score > WEAK_RULE)
            & (m.score < STRONG_RULE)
        )
        def state_unknown(c):

            rid = str(c.m.run_id)
            target = str(c.m.target)

            _collector(rid)["rule_states"][target] = "unknown"

            _record_fired(
                rid,
                f"{target}:RULE_STATE_UNKNOWN",
            )

        # ----------------------------------------------------
        # Conflict:
        # ML strongly positive,
        # rules strongly negative
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Conflict:
        # ML strongly negative,
        # rules strongly positive
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Recommendation:
        # missing clinically useful test
        # ----------------------------------------------------

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

            # Если новое recommendations.py передаёт priority,
            # сохраняем его при наличии.
            try:
                item["priority"] = str(c.m.priority)
            except Exception:
                pass

            seen = _collector(rid)["recommendation_keys"]

            key = (
                item["test"],
                item["target"],
            )

            if key not in seen:

                seen.add(key)

                _collector(rid)[
                    "recommended_next_tests"
                ].append(item)

            _record_fired(
                rid,
                f"{c.m.target}:RECOMMEND_{c.m.test}",
            )

        # ----------------------------------------------------
        # Catch-all
        # ----------------------------------------------------
        #
        # Предотвращает MessageNotHandledException для событий,
        # которые специально не удовлетворяют action-condition.
        # ----------------------------------------------------

        @when_all(
            m.kind != "__never__"
        )
        def observed(c):
            pass


# ============================================================
# Production entry point
# ============================================================

def run_expert_engine(
    patient: Mapping[str, Any] | pd.Series,
    probabilities: Mapping[str, float],
    predictions: Mapping[str, int],
) -> Dict[str, Any]:
    """
    Запускает production expert layer через Durable Rules.

    Важно:
    ML probabilities и ML predictions экспертной системой
    НЕ переписываются.

    Expert layer формирует:

    - clinical rule scores;
    - supports / against / unknown;
    - полноту проверки клинических гипотез;
    - конфликты ML <-> rules;
    - mandatory review;
    - clinical priority;
    - рекомендации дополнительных исследований;
    - список сработавших правил;
    - clinical evidence.
    """

    ensure_durable_available()

    # --------------------------------------------------------
    # Patient data
    # --------------------------------------------------------

    row = as_series(patient)

    # --------------------------------------------------------
    # Проверяем наличие outputs от ML
    # --------------------------------------------------------

    missing_targets = [
        target
        for target in RULE_TARGETS
        if (
            target not in probabilities
            or target not in predictions
        )
    ]

    if missing_targets:

        raise ValueError(
            "Missing ML outputs for targets: "
            + ", ".join(missing_targets)
        )

    # --------------------------------------------------------
    # Нормализуем ML outputs
    # --------------------------------------------------------

    probabilities = {
        target: float(probabilities[target])
        for target in RULE_TARGETS
    }

    predictions = {
        target: int(predictions[target])
        for target in RULE_TARGETS
    }

    # --------------------------------------------------------
    # Clinical rule scores
    # --------------------------------------------------------

    rule_scores = compute_rule_scores(row)

    # --------------------------------------------------------
    # Physician-reviewed completeness
    # --------------------------------------------------------
    #
    # Здесь определяется:
    #
    # complete
    # partial
    # insufficient
    #
    # Missing marker != normal marker.
    # --------------------------------------------------------

    hypothesis_completeness = assess_all_hypotheses(
        row
    )

    # --------------------------------------------------------
    # Unique Durable Rules run
    # --------------------------------------------------------

    run_id = uuid.uuid4().hex

    # --------------------------------------------------------
    # Result collector
    # --------------------------------------------------------

    result = {

        "rule_scores": dict(rule_scores),

        "rule_states": {},

        "conflicts": [],

        "recommended_next_tests": [],

        # Временное внутреннее поле для удаления дублей.
        "recommendation_keys": set(),

        "fired_rules": [],

        "evidence": build_evidence(row),

        # Physician-reviewed completeness.
        "hypothesis_completeness": (
            hypothesis_completeness
        ),

        # Заполняются после завершения Durable Rules.
        "incomplete_hypotheses": [],

        "mandatory_review": False,

        "clinical_priority": "combined",

        "review_targets": [],
    }

    # --------------------------------------------------------
    # Durable Rules execution
    # --------------------------------------------------------

    with _ENGINE_LOCK:

        _RESULTS[run_id] = result

        try:

            # 1. supports / against / unknown
            for event in build_rule_score_events(
                run_id,
                rule_scores,
            ):
                post(
                    RULESET_NAME,
                    event,
                )

            # 2. ML <-> rules conflicts
            for event in build_conflict_events(
                run_id,
                probabilities,
                predictions,
                rule_scores,
            ):
                post(
                    RULESET_NAME,
                    event,
                )

            # 3. Recommendations
            for event in build_recommendation_events(
                run_id,
                row,
                probabilities,
            ):
                post(
                    RULESET_NAME,
                    event,
                )

            completed = _RESULTS.pop(
                run_id
            )

        except Exception:

            _RESULTS.pop(
                run_id,
                None,
            )

            raise

    # ========================================================
    # Defensive fallback
    # ========================================================
    #
    # Каждый rule score должен иметь одно состояние:
    #
    # supports
    # against
    # unknown
    #
    # Если Durable Rules по какой-либо причине не записал
    # состояние, вычисляем его обычной функцией.
    # ========================================================

    for target in RULE_TARGETS:

        completed["rule_states"].setdefault(
            target,
            rule_state(
                rule_scores[target]
            ),
        )

    # ========================================================
    # Physician-reviewed interpretation layer
    # ========================================================

    # --------------------------------------------------------
    # 1. Неполностью проверенные гипотезы
    # --------------------------------------------------------

    incomplete_hypotheses = []

    for (
        target,
        completeness,
    ) in completed[
        "hypothesis_completeness"
    ].items():

        if not completeness["complete"]:

            incomplete_hypotheses.append({
                "target": target,
                "status": completeness[
                    "status"
                ],
                "missing_key_markers": (
                    completeness[
                        "missing_key_markers"
                    ]
                ),
                "available_key_markers": (
                    completeness[
                        "available_key_markers"
                    ]
                ),
            })

    completed[
        "incomplete_hypotheses"
    ] = incomplete_hypotheses

    # --------------------------------------------------------
    # 2. Mandatory review
    # --------------------------------------------------------
    #
    # Врач рекомендовал:
    #
    # strong ML <-> rule conflict
    # -> обязательный врачебный review.
    # --------------------------------------------------------

    completed[
        "mandatory_review"
    ] = bool(
        completed["conflicts"]
    )

    # --------------------------------------------------------
    # 3. Clinical priority
    # --------------------------------------------------------
    #
    # При конфликте clinical rules имеют приоритет
    # в интерпретации.
    #
    # При этом исходная ML probability НЕ изменяется.
    # --------------------------------------------------------

    if completed["mandatory_review"]:

        completed[
            "clinical_priority"
        ] = "rules_on_conflict"

    else:

        completed[
            "clinical_priority"
        ] = "combined"

    # --------------------------------------------------------
    # 4. Targets requiring review
    # --------------------------------------------------------

    completed["review_targets"] = sorted({
        conflict["target"]
        for conflict in completed["conflicts"]
    })

    # --------------------------------------------------------
    # 5. Обогащаем conflict payload
    # --------------------------------------------------------

    for conflict in completed["conflicts"]:

        conflict["mandatory_review"] = True

        conflict[
            "clinical_priority"
        ] = "rules"

        conflict["message"] = (
            conflict["message"]
            + " Требуется обязательный врачебный review. "
            + "Приоритет клинической интерпретации "
              "отдается верифицированным rules."
        )

    # --------------------------------------------------------
    # Удаляем внутреннее техническое поле
    # --------------------------------------------------------

    completed.pop(
        "recommendation_keys",
        None,
    )

    return completed
