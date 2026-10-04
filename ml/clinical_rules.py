"""
Clinical rule configuration and explanation helpers for Meditron.

Important:
- Clinical rules are decision-support evidence, not a standalone diagnosis.
- Numeric constants are source-controlled and must not be tuned on validation/test labels.
- B6/copper remain neutral until a suitable confirmed diagnostic cutoff is approved.
"""

from __future__ import annotations

from typing import Dict, List, Any
import math
import numpy as np
import pandas as pd


CLINICAL = {
    "hemoglobin_female_anemia": {
        "value": 120.0,
        "unit": "g/L",
        "role": "anemia threshold",
        "strength": "hard deterministic",
        "source": "Минздрав РФ / критерий анемии в КР",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2",
    },
    "hemoglobin_male_anemia": {
        "value": 130.0,
        "unit": "g/L",
        "role": "anemia threshold",
        "strength": "hard deterministic",
        "source": "Минздрав РФ / критерий анемии в КР",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2",
    },
    "serum_iron_low": {
        "value": 10.7,
        "unit": "umol/L",
        "role": "lower reference boundary; supporting iron evidence",
        "strength": "moderate/supporting",
        "source": "Минздрав РФ, КР ЖДА 2024, ID 669_2",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2",
    },
    "TIBC_low": {
        "value": 46.0,
        "unit": "umol/L",
        "role": "lower reference boundary",
        "strength": "moderate/supporting",
        "source": "Минздрав РФ, КР ЖДА 2024, ID 669_2",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2",
    },
    "TIBC_high": {
        "value": 78.0,
        "unit": "umol/L",
        "role": "upper reference boundary; high TIBC supports absolute iron deficiency",
        "strength": "moderate/supporting",
        "source": "Минздрав РФ, КР ЖДА 2024, ID 669_2",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2",
    },
    "TSAT_low": {
        "value": 17.8,
        "unit": "%",
        "role": "lower reference boundary; supporting iron evidence",
        "strength": "moderate/supporting",
        "source": "Минздрав РФ, КР ЖДА 2024, ID 669_2",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2",
    },
    "ferritin_low": {
        "value": 11.0,
        "unit": "ng/mL",
        "role": "lower reference boundary; strong iron-store evidence",
        "strength": "strong evidence within iron profile",
        "source": "Минздрав РФ, КР ЖДА 2024, ID 669_2",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2",
    },
    "Ret_He_low": {
        "value": 30.6,
        "unit": "pg",
        "role": "Ret-He below this value indicates iron-deficient erythropoiesis",
        "strength": "strong diagnostic evidence",
        "source": "Минздрав РФ, КР ЖДА 2024, ID 669_2",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2",
    },
    "ferritin_repletion_marker": {
        "value": 30.0,
        "unit": "ng/mL",
        "role": "supporting only; NOT standalone diagnostic cutoff",
        "strength": "weak/supporting only",
        "source": "Минздрав РФ, КР ЖДА 2024, контроль восстановления запасов",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/669_2",
    },
    "vitamin_B12_deficiency": {
        "value": 140.0,
        "unit": "pg/mL",
        "role": "low serum B12; main laboratory criterion in B12-deficiency anemia",
        "strength": "strong diagnostic evidence",
        "source": "Минздрав РФ, КР Витамин-B12-дефицитная анемия 2024, ID 536_3",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/536_3",
    },
    "folate_deficiency": {
        "value": 4.0,
        "unit": "numeric cutoff; dataset scale consistent with ng/mL",
        "role": "serum folate below this value supports folate deficiency",
        "strength": "strong diagnostic evidence",
        "source": "Минздрав РФ, КР Фолиеводефицитная анемия 2024, ID 540_3",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/540_3",
    },
    "folate_borderline_high": {
        "value": 8.0,
        "unit": "same numeric scale as folate",
        "role": "upper edge of borderline folate interval 4–8",
        "strength": "conditional evidence",
        "source": "Минздрав РФ, КР Фолиеводефицитная анемия 2024, ID 540_3",
        "source_url": "https://cr.minzdrav.gov.ru/preview-cr/540_3",
    },
}


RULE_TARGETS = [
    "iron_deficiency",
    "B12_deficiency",
    "folate_deficiency",
    "B6_deficiency",
    "copper_deficiency",
    "inflammation_anemia",
]


def _present(x: Any) -> bool:
    return pd.notna(x)


def anemia_rule(row: pd.Series) -> int:
    sex = row.get("sex")
    hb = row.get("hemoglobin", np.nan)
    if not _present(hb):
        return 0
    if sex == "F":
        return int(hb < CLINICAL["hemoglobin_female_anemia"]["value"])
    if sex == "M":
        return int(hb < CLINICAL["hemoglobin_male_anemia"]["value"])
    return 0


def weighted_evidence(conditions) -> float:
    available_weight = sum(w for available, _, w in conditions if available)
    if available_weight == 0:
        return 0.5
    positive = sum(w for available, cond, w in conditions if available and cond)
    return 0.05 + 0.90 * (positive / available_weight)


def iron_rule_score(row: pd.Series) -> float:
    ferritin = row.get("ferritin", np.nan)
    iron = row.get("serum_iron", np.nan)
    tsat = row.get("TSAT", np.nan)
    tibc = row.get("TIBC", np.nan)
    ret_he = row.get("Ret_He", np.nan)

    conditions = [
        (_present(ret_he), ret_he < CLINICAL["Ret_He_low"]["value"], 0.30),
        (_present(ferritin), ferritin < CLINICAL["ferritin_low"]["value"], 0.25),
        (_present(iron), iron < CLINICAL["serum_iron_low"]["value"], 0.15),
        (_present(tsat), tsat < CLINICAL["TSAT_low"]["value"], 0.20),
        (_present(tibc), tibc > CLINICAL["TIBC_high"]["value"], 0.10),
    ]
    score = weighted_evidence(conditions)

    if (
        _present(ferritin)
        and CLINICAL["ferritin_low"]["value"] <= ferritin
        < CLINICAL["ferritin_repletion_marker"]["value"]
    ):
        score = min(0.95, score + 0.05)

    return float(score)


def b12_rule_score(row: pd.Series) -> float:
    """
    B12 v2:
    - serum B12 < 140 pg/mL -> strong positive evidence;
    - serum B12 >= 140 pg/mL does NOT reliably exclude functional B12 deficiency,
      therefore the automated rule remains neutral rather than strongly negative.
    """
    b12 = row.get("vitamin_B12", np.nan)

    if not _present(b12):
        return 0.5

    if b12 < CLINICAL["vitamin_B12_deficiency"]["value"]:
        return 0.95

    return 0.5


def folate_rule_score(row: pd.Series) -> float:
    folate = row.get("folate", np.nan)
    if not _present(folate):
        return 0.5
    if folate < CLINICAL["folate_deficiency"]["value"]:
        return 0.95
    if folate <= CLINICAL["folate_borderline_high"]["value"]:
        return 0.5
    return 0.10


def inflammation_rule_score(row: pd.Series) -> float:
    """
    Inflammation v2.

    Strong evidence is allowed only when:
    1) anemia is present;
    2) at least two informative iron-profile markers are available.

    This prevents one available marker (for example ferritin alone)
    from producing an artificial rule_score ~= 0.95.
    """
    anemia = anemia_rule(row)

    if anemia == 0:
        return 0.05

    ferritin = row.get("ferritin", np.nan)
    iron = row.get("serum_iron", np.nan)
    tibc = row.get("TIBC", np.nan)

    observations = []

    if _present(iron):
        observations.append(
            iron < CLINICAL["serum_iron_low"]["value"]
        )

    if _present(tibc):
        observations.append(
            tibc <= CLINICAL["TIBC_high"]["value"]
        )

    if _present(ferritin):
        observations.append(
            ferritin >= CLINICAL["ferritin_low"]["value"]
        )

    if len(observations) < 2:
        return 0.5

    positive = sum(observations)
    ratio = positive / len(observations)

    if len(observations) == 3 and positive == 3:
        return 0.95

    if len(observations) == 2 and positive == 2:
        return 0.80

    if positive == 0:
        return 0.10

    if ratio >= 2 / 3:
        return 0.70

    if ratio >= 0.5:
        return 0.55

    return 0.30


def compute_rule_scores(row: pd.Series) -> Dict[str, float]:
    return {
        "iron_deficiency": iron_rule_score(row),
        "B12_deficiency": b12_rule_score(row),
        "folate_deficiency": folate_rule_score(row),
        "B6_deficiency": 0.5,
        "copper_deficiency": 0.5,
        "inflammation_anemia": inflammation_rule_score(row),
    }


def build_evidence(row: pd.Series) -> List[Dict[str, Any]]:
    """
    Build human-readable clinical evidence.

    v2 principle:
    absence of a positive criterion is not automatically negative evidence.
    In particular, B12 >= 140 pg/mL is treated as "unknown", not "against".
    """
    evidence: List[Dict[str, Any]] = []

    sex = row.get("sex")
    hb = row.get("hemoglobin", np.nan)

    if _present(hb) and sex in {"F", "M"}:
        cutoff = (
            CLINICAL["hemoglobin_female_anemia"]["value"]
            if sex == "F"
            else CLINICAL["hemoglobin_male_anemia"]["value"]
        )
        evidence.append({
            "target": "anemia",
            "feature": "hemoglobin",
            "value": float(hb),
            "criterion": f"< {cutoff} g/L",
            "direction": "supports" if hb < cutoff else "against",
            "strength": "hard deterministic",
            "source_url": CLINICAL["hemoglobin_female_anemia"]["source_url"],
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

def rule_state(
    score: float,
    strong_rule: float = 0.75,
    weak_rule: float = 0.25,
) -> str:
    if score >= strong_rule:
        return "supports"
    if score <= weak_rule:
        return "against"
    return "unknown"


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
    Conflict v2:
    neutral/unknown clinical evidence never creates a conflict.
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

def recommended_next_tests(row: pd.Series, probabilities: Dict[str, float]) -> List[Dict[str, str]]:
    """
    Returns confirmatory-data suggestions, not treatment advice.
    A suggestion is produced mainly when an informative marker is missing.
    """
    suggestions: List[Dict[str, str]] = []

    def add_if_missing(feature, target, reason):
        if feature not in row.index or pd.isna(row.get(feature, np.nan)):
            suggestions.append({
                "test": feature,
                "target": target,
                "reason": reason,
            })

    if probabilities.get("iron_deficiency", 0) >= 0.50:
        for feature in ["ferritin", "TSAT", "Ret_He"]:
            add_if_missing(feature, "iron_deficiency", "Уточнение железодефицитного профиля.")

    if probabilities.get("B12_deficiency", 0) >= 0.50:
        for feature in ["vitamin_B12", "active_B12", "MMA", "homocysteine"]:
            add_if_missing(feature, "B12_deficiency", "Уточнение B12-дефицита при неполных данных.")

    if probabilities.get("folate_deficiency", 0) >= 0.50:
        for feature in ["folate", "homocysteine"]:
            add_if_missing(feature, "folate_deficiency", "Уточнение фолатного статуса.")

    if probabilities.get("copper_deficiency", 0) >= 0.50:
        for feature in ["copper", "ceruloplasmin"]:
            add_if_missing(feature, "copper_deficiency", "Уточнение обмена меди.")

    if probabilities.get("B6_deficiency", 0) >= 0.50:
        add_if_missing("vitamin_B6", "B6_deficiency", "Уточнение обеспеченности витамином B6.")

    return suggestions


def predicted_state_confidence(
    probability: float,
    prediction: int,
) -> float:
    """
    Confidence in the state selected by the frozen ensemble.

    Positive prediction -> P(target)
    Negative prediction -> 1 - P(target)
    """
    p = float(np.clip(probability, 0.0, 1.0))

    if int(prediction) == 1:
        return p

    return 1.0 - p


def confidence_label(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.65:
        return "moderate"
    return "low"