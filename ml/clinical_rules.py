"""
Backward-compatible clinical rule API.

The source of truth now lives under expert/ so medical knowledge can be
updated independently from ML. Old notebooks/imports can continue using
`ml.clinical_rules`.
"""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
import pandas as pd

from expert.knowledge_base import (
    CLINICAL,
    RULE_TARGETS,
    anemia_rule,
    weighted_evidence,
    iron_rule_score,
    b12_rule_score,
    folate_rule_score,
    inflammation_rule_score,
    compute_rule_scores,
    rule_state,
    predicted_state_confidence,
    confidence_label,
    overall_screening_confidence,
)
from expert.explanations import build_evidence
from expert.recommendations import recommended_next_tests


def build_conflicts(
    probabilities: Dict[str, float],
    predictions: Dict[str, int],
    rule_scores: Dict[str, float],
    high_probability: float = 0.75,
    low_probability: float = 0.25,
    strong_rule: float = 0.75,
    weak_rule: float = 0.25,
) -> List[Dict[str, Any]]:
    """
    Pure-Python compatibility implementation from the validated v2 notebook.
    Production expert inference uses Durable Rules in expert.engine.
    """
    conflicts = []

    for target in RULE_TARGETS:
        p = float(probabilities.get(target, np.nan))
        r = float(rule_scores.get(target, 0.5))

        if not np.isfinite(p):
            continue

        state = rule_state(
            r,
            strong_rule=strong_rule,
            weak_rule=weak_rule,
        )

        if p >= high_probability and state == "against":
            conflicts.append({
                "target": target,
                "type": "ml_positive_rule_negative",
                "severity": "review",
                "ensemble_probability": p,
                "rule_score": r,
                "rule_state": state,
                "message": (
                    "Высокая ML-вероятность при явном clinical evidence "
                    "против соответствующего состояния."
                ),
            })

        elif p <= low_probability and state == "supports":
            conflicts.append({
                "target": target,
                "type": "ml_negative_rule_positive",
                "severity": "review",
                "ensemble_probability": p,
                "rule_score": r,
                "rule_state": state,
                "message": (
                    "Clinical rule layer сильно поддерживает состояние, "
                    "а ML-вероятность низкая."
                ),
            })

    return conflicts


__all__ = [
    "CLINICAL",
    "RULE_TARGETS",
    "anemia_rule",
    "weighted_evidence",
    "iron_rule_score",
    "b12_rule_score",
    "folate_rule_score",
    "inflammation_rule_score",
    "compute_rule_scores",
    "build_evidence",
    "rule_state",
    "build_conflicts",
    "recommended_next_tests",
    "predicted_state_confidence",
    "confidence_label",
    "overall_screening_confidence",
]
