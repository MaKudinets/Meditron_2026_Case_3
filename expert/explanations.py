from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
import pandas as pd

from .knowledge_base import (
    CLINICAL,
    RULE_TARGETS,
    _present,
    confidence_label,
    overall_screening_confidence,
    predicted_state_confidence,
)


def build_evidence(row: pd.Series) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []

    sex = row.get("sex")
    hb = row.get("hemoglobin", np.nan)

    if _present(hb) and str(sex).upper() in {"F", "M"}:
        sex_u = str(sex).upper()
        cfg = (
            CLINICAL["hemoglobin_female_anemia"]
            if sex_u == "F"
            else CLINICAL["hemoglobin_male_anemia"]
        )
        evidence.append({
            "target": "anemia",
            "feature": "hemoglobin",
            "value": float(hb),
            "criterion": f"< {cfg['value']} g/L",
            "direction": "supports" if hb < cfg["value"] else "against",
            "strength": "hard deterministic",
            "source_url": cfg["source_url"],
        })

    iron_checks = [
        ("Ret_He", "Ret_He_low", lambda x, c: x < c, "<"),
        ("ferritin", "ferritin_low", lambda x, c: x < c, "<"),
        ("serum_iron", "serum_iron_low", lambda x, c: x < c, "<"),
        ("TSAT", "TSAT_low", lambda x, c: x < c, "<"),
        ("TIBC", "TIBC_high", lambda x, c: x > c, ">"),
    ]

    for feature, key, fn, symbol in iron_checks:
        value = row.get(feature, np.nan)
        if not _present(value):
            continue

        cfg = CLINICAL[key]
        positive = bool(fn(value, cfg["value"]))

        evidence.append({
            "target": "iron_deficiency",
            "feature": feature,
            "value": float(value),
            "criterion": f"{symbol} {cfg['value']} {cfg['unit']}",
            "direction": "supports" if positive else "against",
            "strength": cfg["strength"],
            "source_url": cfg["source_url"],
        })

    b12 = row.get("vitamin_B12", np.nan)
    if _present(b12):
        cfg = CLINICAL["vitamin_B12_deficiency"]

        if b12 < cfg["value"]:
            direction = "supports"
            strength = cfg["strength"]
        else:
            direction = "unknown"
            strength = "insufficient to exclude functional deficiency"

        evidence.append({
            "target": "B12_deficiency",
            "feature": "vitamin_B12",
            "value": float(b12),
            "criterion": f"< {cfg['value']} {cfg['unit']}",
            "direction": direction,
            "strength": strength,
            "source_url": cfg["source_url"],
        })

    folate = row.get("folate", np.nan)
    if _present(folate):
        low_cfg = CLINICAL["folate_deficiency"]
        high_cfg = CLINICAL["folate_borderline_high"]

        if folate < low_cfg["value"]:
            direction = "supports"
            strength = low_cfg["strength"]
        elif folate <= high_cfg["value"]:
            direction = "unknown"
            strength = "conditional evidence"
        else:
            direction = "against"
            strength = "supporting negative evidence"

        evidence.append({
            "target": "folate_deficiency",
            "feature": "folate",
            "value": float(folate),
            "criterion": (
                f"< {low_cfg['value']} strong; "
                f"{low_cfg['value']}–{high_cfg['value']} borderline"
            ),
            "direction": direction,
            "strength": strength,
            "source_url": low_cfg["source_url"],
        })

    return evidence


def branch_confidence(probability: float, prediction: int) -> dict:
    certainty = predicted_state_confidence(probability, prediction)
    return {
        "selected_state": "positive" if int(prediction) == 1 else "negative",
        "certainty": round(float(certainty), 4),
        "level": confidence_label(certainty),
    }


def build_explanation_payload(
    patient_id,
    ml_result: dict,
    expert_result: dict,
) -> dict:
    probabilities = {
        target: float(ml_result["deficiencies"][target]["probability"])
        for target in RULE_TARGETS
    }
    predictions = {
        target: int(bool(ml_result["deficiencies"][target]["prediction"]))
        for target in RULE_TARGETS
    }

    deficiencies = {}

    for target in RULE_TARGETS:
        deficiencies[target] = {
            "probability": round(probabilities[target], 4),
            "prediction": bool(predictions[target]),
            "rule_score": round(
                float(expert_result["rule_scores"][target]),
                4,
            ),
            "rule_state": expert_result["rule_states"][target],
            "confidence": branch_confidence(
                probabilities[target],
                predictions[target],
            ),
        }

    return {
        "patient_id": patient_id,
        "prediction": ml_result["prediction"],
        "confidence": overall_screening_confidence(
            probabilities,
            predictions,
        ),
        "deficiencies": deficiencies,
        "evidence": expert_result["evidence"],
        "fired_rules": expert_result["fired_rules"],
        "conflicts": expert_result["conflicts"],
        "recommended_next_tests": expert_result["recommended_next_tests"],
        "coverage": ml_result.get("coverage"),
        "warnings": ml_result.get("warnings", []),
        "disclaimer": (
            "Decision-support output. Не является самостоятельным "
            "клиническим диагнозом и требует интерпретации врачом."
        ),
    }
