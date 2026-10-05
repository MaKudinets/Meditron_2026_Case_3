from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


# Source-controlled clinical configuration.
# These values are NOT tuned on validation/test labels.
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

PHYSICIAN_PANELS = {
    "iron_deficiency": {
        "key_markers": [
            "serum_iron",
            "ferritin",
            "transferrin",
            "TIBC",
        ],
        "supporting_markers": [
            "TSAT",
            "sTfR",
            "Ret_He",
        ],
        "expert_note": (
            "Ключевые показатели для оценки дефицита железа: "
            "сывороточное железо, ферритин, трансферрин и ОЖСС."
        ),
    },

    "B12_deficiency": {
        "key_markers": [
            "vitamin_B12",
            "MMA",
        ],
        "supporting_markers": [
            "active_B12",
            "homocysteine",
        ],
        "expert_note": (
            "Ключевые показатели для оценки B12-дефицита: "
            "витамин B12 и метилмалоновая кислота."
        ),
    },

    "folate_deficiency": {
        "key_markers": [
            "folate",
        ],
        "supporting_markers": [
            "homocysteine",
        ],
        "expert_note": (
            "Ключевой показатель для оценки фолатного дефицита — folate."
        ),
    },

    "B6_deficiency": {
        "key_markers": [
            "vitamin_B6",
            "MCV",
        ],
        "supporting_markers": [],
        "expert_note": (
            "Ключевые показатели для оценки B6-дефицита: "
            "витамин B6 и MCV."
        ),
    },

    "copper_deficiency": {
        "key_markers": [
            "copper",
            "ceruloplasmin",
        ],
        "supporting_markers": [
            "vitamin_B12",
            "folate",
            "ferritin",
        ],
        "expert_note": (
            "Ключевые показатели для оценки дефицита меди: "
            "copper и ceruloplasmin. Дополнительно необходимо "
            "учитывать альтернативные дефицитные состояния."
        ),
    },

    "inflammation_anemia": {
        "key_markers": [
            "CRP",
            "ESR",
        ],
        "supporting_markers": [
            "ferritin",
            "serum_iron",
            "TIBC",
            "eGFR",
        ],
        "expert_note": (
            "Основные маркеры воспалительного контекста: CRP и ESR. "
            "Для оценки почечного контекста используется eGFR."
        ),
    },
}

STRONG_RULE = 0.75
WEAK_RULE = 0.25
HIGH_ML_PROBABILITY = 0.75
LOW_ML_PROBABILITY = 0.25


def _present(x: Any) -> bool:
    return pd.notna(x)

def _safe_lt(value, threshold) -> bool:
    return _present(value) and value < threshold


def _safe_gt(value, threshold) -> bool:
    return _present(value) and value > threshold
    
def anemia_rule(row: pd.Series) -> int:
    sex = row.get("sex")
    hb = row.get("hemoglobin", np.nan)

    if not _present(hb):
        return 0

    sex = str(sex).strip().upper()

    if sex in {"F", "FEMALE", "Ж", "ЖЕН"}:
        return int(hb < CLINICAL["hemoglobin_female_anemia"]["value"])

    if sex in {"M", "MALE", "М", "МУЖ"}:
        return int(hb < CLINICAL["hemoglobin_male_anemia"]["value"])

    return 0


def assess_hypothesis_completeness(
    row: pd.Series,
    target: str,
) -> Dict[str, Any]:
    """
    Оценивает, достаточно ли ключевых данных
    для проверки конкретной гипотезы.
    """

    panel = PHYSICIAN_PANELS.get(target)

    if panel is None:
        return {
            "target": target,
            "status": "unknown",
            "complete": False,
            "available_key_markers": [],
            "missing_key_markers": [],
            "available_supporting_markers": [],
            "missing_supporting_markers": [],
        }

    key_markers = panel["key_markers"]
    supporting_markers = panel["supporting_markers"]

    available_key = [
        feature
        for feature in key_markers
        if feature in row.index and _present(row.get(feature))
    ]

    missing_key = [
        feature
        for feature in key_markers
        if feature not in row.index or not _present(row.get(feature))
    ]

    available_supporting = [
        feature
        for feature in supporting_markers
        if feature in row.index and _present(row.get(feature))
    ]

    missing_supporting = [
        feature
        for feature in supporting_markers
        if feature not in row.index or not _present(row.get(feature))
    ]

    if len(missing_key) == 0:
        status = "complete"
        complete = True

    elif len(available_key) == 0:
        status = "insufficient"
        complete = False

    else:
        status = "partial"
        complete = False

    return {
        "target": target,
        "status": status,
        "complete": complete,
        "available_key_markers": available_key,
        "missing_key_markers": missing_key,
        "available_supporting_markers": available_supporting,
        "missing_supporting_markers": missing_supporting,
        "expert_note": panel["expert_note"],
    }


def assess_all_hypotheses(
    row: pd.Series,
) -> Dict[str, Dict[str, Any]]:
    """
    Оценивает полноту данных по всем гипотезам.
    """

    return {
        target: assess_hypothesis_completeness(row, target)
        for target in RULE_TARGETS
    }


def weighted_evidence(conditions) -> float:
    available_weight = sum(w for available, _, w in conditions if available)
    if available_weight == 0:
        return 0.5

    positive = sum(
        w for available, condition, w in conditions
        if available and condition
    )
    return 0.05 + 0.90 * (positive / available_weight)


def iron_rule_score(row: pd.Series) -> float:
    ferritin = row.get("ferritin", np.nan)
    iron = row.get("serum_iron", np.nan)
    tsat = row.get("TSAT", np.nan)
    tibc = row.get("TIBC", np.nan)
    ret_he = row.get("Ret_He", np.nan)

    conditions = [
    (
        _present(ret_he),
        _safe_lt(ret_he, CLINICAL["Ret_He_low"]["value"]),
        0.30,
    ),
    (
        _present(ferritin),
        _safe_lt(ferritin, CLINICAL["ferritin_low"]["value"]),
        0.25,
    ),
    (
        _present(iron),
        _safe_lt(iron, CLINICAL["serum_iron_low"]["value"]),
        0.15,
    ),
    (
        _present(tsat),
        _safe_lt(tsat, CLINICAL["TSAT_low"]["value"]),
        0.20,
    ),
    (
        _present(tibc),
        _safe_gt(tibc, CLINICAL["TIBC_high"]["value"]),
        0.10,
    ),
]

    score = weighted_evidence(conditions)

    if (
        _present(ferritin)
        and CLINICAL["ferritin_low"]["value"]
        <= ferritin
        < CLINICAL["ferritin_repletion_marker"]["value"]
    ):
        score = min(0.95, score + 0.05)

    return float(score)


def b12_rule_score(row: pd.Series) -> float:
    """
    B12 v2:
    - <140 pg/mL -> strong positive evidence
    - >=140 pg/mL -> neutral/unknown, not strong negative evidence
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
    Inflammation v2:
    strong evidence requires anemia + at least two informative
    iron-profile markers.
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


def rule_state(
    score: float,
    strong_rule: float = STRONG_RULE,
    weak_rule: float = WEAK_RULE,
) -> str:
    if score >= strong_rule:
        return "supports"
    if score <= weak_rule:
        return "against"
    return "unknown"


def predicted_state_confidence(probability: float, prediction: int) -> float:
    p = float(np.clip(probability, 0.0, 1.0))
    return p if int(prediction) == 1 else 1.0 - p


def confidence_label(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.65:
        return "moderate"
    return "low"


def overall_screening_confidence(
    probabilities: Dict[str, float],
    predictions: Dict[str, int],
) -> dict:
    positive_targets = [
        target
        for target in RULE_TARGETS
        if int(predictions[target]) == 1
    ]

    if positive_targets:
        certainties = {
            target: predicted_state_confidence(
                probabilities[target],
                predictions[target],
            )
            for target in positive_targets
        }
        limiting_target = min(certainties, key=certainties.get)
        certainty = certainties[limiting_target]
        return {
            "basis": "weakest_positive_branch",
            "limiting_target": limiting_target,
            "certainty": round(float(certainty), 4),
            "level": confidence_label(certainty),
        }

    strongest_possible_deficiency = max(
        probabilities,
        key=probabilities.get,
    )
    certainty = 1.0 - float(
        probabilities[strongest_possible_deficiency]
    )

    return {
        "basis": "all_binary_branches_negative",
        "limiting_target": strongest_possible_deficiency,
        "certainty": round(float(certainty), 4),
        "level": confidence_label(certainty),
    }
