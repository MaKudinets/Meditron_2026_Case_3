from __future__ import annotations

from typing import Any, Mapping
import uuid

import pandas as pd

from .knowledge_base import RULE_TARGETS


def as_series(patient: Mapping[str, Any] | pd.Series) -> pd.Series:
    if isinstance(patient, pd.Series):
        return patient.copy()
    return pd.Series(dict(patient))


def new_run_id() -> str:
    return uuid.uuid4().hex


def build_rule_score_events(
    run_id: str,
    rule_scores: Mapping[str, float],
):
    return [
        {
            "kind": "rule_state",
            "run_id": run_id,
            "target": target,
            "score": float(rule_scores[target]),
        }
        for target in RULE_TARGETS
    ]


def build_conflict_events(
    run_id: str,
    probabilities: Mapping[str, float],
    predictions: Mapping[str, int],
    rule_scores: Mapping[str, float],
):
    return [
        {
            "kind": "decision",
            "run_id": run_id,
            "target": target,
            "probability": float(probabilities[target]),
            "prediction": int(predictions[target]),
            "rule_score": float(rule_scores[target]),
        }
        for target in RULE_TARGETS
    ]
