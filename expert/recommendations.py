from __future__ import annotations

from typing import Dict, List
import numpy as np
import pandas as pd


RECOMMENDATION_PLAN = {
    "iron_deficiency": [
        ("ferritin", "Уточнение железодефицитного профиля."),
        ("TSAT", "Уточнение железодефицитного профиля."),
        ("Ret_He", "Уточнение железодефицитного эритропоэза."),
        ("sTfR", "Уточнение железодефицита при неоднозначном профиле."),
    ],
    "B12_deficiency": [
        ("vitamin_B12", "Уточнение B12-дефицита."),
        ("active_B12", "Уточнение функционального B12-статуса."),
        ("MMA", "Уточнение функционального B12-дефицита."),
        ("homocysteine", "Уточнение B12-дефицита при неполных данных."),
    ],
    "folate_deficiency": [
        ("folate", "Уточнение фолатного статуса."),
        ("homocysteine", "Уточнение фолатного статуса."),
    ],
    "B6_deficiency": [
        ("vitamin_B6", "Уточнение обеспеченности витамином B6."),
    ],
    "copper_deficiency": [
        ("copper", "Уточнение обмена меди."),
        ("ceruloplasmin", "Уточнение обмена меди."),
    ],
    "inflammation_anemia": [
        ("CRP", "Уточнение воспалительного контекста."),
        ("ferritin", "Уточнение железного профиля при воспалении."),
        ("serum_iron", "Уточнение железного профиля при воспалении."),
        ("TIBC", "Уточнение железного профиля при воспалении."),
        ("TSAT", "Уточнение железного профиля при воспалении."),
        ("sTfR", "Дифференциация абсолютного дефицита и воспалительного профиля."),
    ],
}


def _missing(row: pd.Series, feature: str) -> bool:
    return feature not in row.index or pd.isna(row.get(feature, np.nan))


def build_recommendation_events(
    run_id: str,
    row: pd.Series,
    probabilities: Dict[str, float],
):
    """
    Build candidates. Durable Rules decides whether they fire.
    Missing test alone is NOT enough: the ML probability must also
    meet the rule-engine trigger.
    """
    events = []

    for target, tests in RECOMMENDATION_PLAN.items():
        probability = float(probabilities.get(target, 0.0))

        for test, reason in tests:
            events.append({
                "kind": "recommendation",
                "run_id": run_id,
                "target": target,
                "test": test,
                "reason": reason,
                "missing": bool(_missing(row, test)),
                "probability": probability,
            })

    return events


def recommended_next_tests(
    row: pd.Series,
    probabilities: Dict[str, float],
    *,
    probability_threshold: float = 0.50,
) -> List[Dict[str, str]]:
    """
    Pure-Python compatibility helper used by old notebooks.
    Production expert inference uses Durable Rules in engine.py.
    """
    suggestions = []

    for target, tests in RECOMMENDATION_PLAN.items():
        if float(probabilities.get(target, 0.0)) < probability_threshold:
            continue

        for test, reason in tests:
            if _missing(row, test):
                suggestions.append({
                    "test": test,
                    "target": target,
                    "reason": reason,
                })

    return suggestions
