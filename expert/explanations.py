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


# ============================================================
# Human-readable target names
# ============================================================

TARGET_LABELS_RU = {
    "iron_deficiency": "дефицит железа",
    "B12_deficiency": "дефицит витамина B12",
    "folate_deficiency": "дефицит фолатов",
    "B6_deficiency": "дефицит витамина B6",
    "copper_deficiency": "дефицит меди",
    "inflammation_anemia": "анемию воспаления",
}


# ============================================================
# Clinical evidence
# ============================================================

def build_evidence(
    row: pd.Series,
) -> List[Dict[str, Any]]:
    """
    Формирует структурированное клиническое evidence.

    Важно:
    - missing != normal;
    - evidence используется как decision-support;
    - отсутствие положительного критерия не всегда означает
      отрицание гипотезы.
    """

    evidence: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # Anemia: deterministic hemoglobin rule
    # --------------------------------------------------------

    sex = row.get("sex")
    hb = row.get("hemoglobin", np.nan)

    if (
        _present(hb)
        and str(sex).upper() in {"F", "M"}
    ):
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
            "criterion": (
                f"< {cfg['value']} g/L"
            ),
            "direction": (
                "supports"
                if hb < cfg["value"]
                else "against"
            ),
            "strength": "hard deterministic",
            "source_url": cfg["source_url"],
        })

    # --------------------------------------------------------
    # Iron deficiency
    # --------------------------------------------------------

    iron_checks = [
        (
            "Ret_He",
            "Ret_He_low",
            lambda x, c: x < c,
            "<",
        ),
        (
            "ferritin",
            "ferritin_low",
            lambda x, c: x < c,
            "<",
        ),
        (
            "serum_iron",
            "serum_iron_low",
            lambda x, c: x < c,
            "<",
        ),
        (
            "TSAT",
            "TSAT_low",
            lambda x, c: x < c,
            "<",
        ),
        (
            "TIBC",
            "TIBC_high",
            lambda x, c: x > c,
            ">",
        ),
    ]

    for feature, key, fn, symbol in iron_checks:

        value = row.get(
            feature,
            np.nan,
        )

        if not _present(value):
            continue

        cfg = CLINICAL[key]

        positive = bool(
            fn(
                value,
                cfg["value"],
            )
        )

        evidence.append({
            "target": "iron_deficiency",
            "feature": feature,
            "value": float(value),
            "criterion": (
                f"{symbol} "
                f"{cfg['value']} "
                f"{cfg['unit']}"
            ),
            "direction": (
                "supports"
                if positive
                else "against"
            ),
            "strength": cfg["strength"],
            "source_url": cfg["source_url"],
        })

    # --------------------------------------------------------
    # B12 deficiency
    # --------------------------------------------------------

    b12 = row.get(
        "vitamin_B12",
        np.nan,
    )

    if _present(b12):

        cfg = CLINICAL[
            "vitamin_B12_deficiency"
        ]

        if b12 < cfg["value"]:

            direction = "supports"
            strength = cfg["strength"]

        else:

            # Нормальный/не сниженный B12 сам по себе
            # не используется как жёсткое исключение
            # функционального дефицита.
            direction = "unknown"

            strength = (
                "insufficient to exclude "
                "functional deficiency"
            )

        evidence.append({
            "target": "B12_deficiency",
            "feature": "vitamin_B12",
            "value": float(b12),
            "criterion": (
                f"< {cfg['value']} "
                f"{cfg['unit']}"
            ),
            "direction": direction,
            "strength": strength,
            "source_url": cfg["source_url"],
        })

    # --------------------------------------------------------
    # Folate deficiency
    # --------------------------------------------------------

    folate = row.get(
        "folate",
        np.nan,
    )

    if _present(folate):

        low_cfg = CLINICAL[
            "folate_deficiency"
        ]

        high_cfg = CLINICAL[
            "folate_borderline_high"
        ]

        if folate < low_cfg["value"]:

            direction = "supports"
            strength = low_cfg["strength"]

        elif folate <= high_cfg["value"]:

            direction = "unknown"
            strength = "conditional evidence"

        else:

            direction = "against"

            strength = (
                "supporting negative evidence"
            )

        evidence.append({
            "target": "folate_deficiency",
            "feature": "folate",
            "value": float(folate),
            "criterion": (
                f"< {low_cfg['value']} strong; "
                f"{low_cfg['value']}–"
                f"{high_cfg['value']} borderline"
            ),
            "direction": direction,
            "strength": strength,
            "source_url": low_cfg[
                "source_url"
            ],
        })

    return evidence


# ============================================================
# Confidence helpers
# ============================================================

def branch_confidence(
    probability: float,
    prediction: int,
) -> dict:
    """
    Confidence именно в выбранном бинарном состоянии.
    """

    certainty = predicted_state_confidence(
        probability,
        prediction,
    )

    return {
        "selected_state": (
            "positive"
            if int(prediction) == 1
            else "negative"
        ),
        "certainty": round(
            float(certainty),
            4,
        ),
        "level": confidence_label(
            certainty
        ),
    }


# ============================================================
# Human-readable clinical wording
# ============================================================

def build_clinical_messages(
    probabilities: Dict[str, float],
    predictions: Dict[str, int],
    expert_result: dict,
) -> List[str]:
    """
    Формирует короткие врачебные формулировки.

    По рекомендации врача:
    - не утверждаем окончательный диагноз;
    - используем формулировку
      "подозрение ... по доступным данным";
    - явно указываем неполноту оценки;
    - конфликт ML/rules требует review.
    """

    messages: List[str] = []

    # --------------------------------------------------------
    # Positive ML hypotheses
    # --------------------------------------------------------

    positive_targets = [
        target
        for target in RULE_TARGETS
        if int(predictions[target]) == 1
    ]

    if positive_targets:

        for target in positive_targets:

            label = TARGET_LABELS_RU.get(
                target,
                target,
            )

            state = expert_result[
                "rule_states"
            ].get(
                target,
                "unknown",
            )

            if state == "supports":

                messages.append(
                    f"Подозрение на {label} "
                    f"по доступным данным. "
                    f"Клинические правила "
                    f"поддерживают гипотезу."
                )

            elif state == "against":

                messages.append(
                    f"ML указывает на возможный "
                    f"{label}, однако клинические "
                    f"правила гипотезу не "
                    f"поддерживают."
                )

            else:

                messages.append(
                    f"Подозрение на {label} "
                    f"по доступным данным. "
                    f"Клинических данных "
                    f"недостаточно для уверенного "
                    f"подтверждения или исключения."
                )

    else:

        messages.append(
            "По доступным данным ML-модель не "
            "выделила дефицитную гипотезу выше "
            "рабочего порога. Это не исключает "
            "состояния, которые невозможно полноценно "
            "оценить из-за отсутствующих исследований."
        )

    # --------------------------------------------------------
    # Mandatory review
    # --------------------------------------------------------

    if expert_result.get(
        "mandatory_review",
        False,
    ):

        review_targets = expert_result.get(
            "review_targets",
            [],
        )

        readable_targets = [
            TARGET_LABELS_RU.get(
                target,
                target,
            )
            for target in review_targets
        ]

        messages.append(
            "Выявлено существенное расхождение "
            "между ML и клиническими правилами. "
            "Требуется обязательный врачебный review. "
            "Приоритет клинической интерпретации "
            "отдаётся верифицированным правилам."
            + (
                " Конфликтующие гипотезы: "
                + ", ".join(readable_targets)
                + "."
                if readable_targets
                else ""
            )
        )

    return messages


# ============================================================
# Missing-data limitations
# ============================================================

def build_data_limitations(
    expert_result: dict,
) -> List[Dict[str, Any]]:
    """
    Формирует явные ограничения из-за отсутствующих
    ключевых лабораторных данных.
    """

    limitations: List[
        Dict[str, Any]
    ] = []

    for item in expert_result.get(
        "incomplete_hypotheses",
        [],
    ):

        target = item["target"]

        missing = item.get(
            "missing_key_markers",
            [],
        )

        available = item.get(
            "available_key_markers",
            [],
        )

        status = item.get(
            "status",
            "unknown",
        )

        limitations.append({
            "target": target,
            "target_label": (
                TARGET_LABELS_RU.get(
                    target,
                    target,
                )
            ),
            "status": status,
            "available_key_markers": (
                available
            ),
            "missing_key_markers": (
                missing
            ),
            "message": (
                "Гипотеза проверена не полностью. "
                "Отсутствуют ключевые показатели: "
                + (
                    ", ".join(missing)
                    if missing
                    else "не определены"
                )
                + ". Отсутствие данных не "
                  "интерпретируется как норма."
            ),
        })

    return limitations


# ============================================================
# Final explanation payload
# ============================================================

def build_explanation_payload(
    patient_id,
    ml_result: dict,
    expert_result: dict,
) -> dict:
    """
    Собирает итоговый explanation payload для API/frontend.

    ML prediction остаётся неизменным.
    Expert layer добавляет клиническую интерпретацию,
    полноту данных, review и рекомендации.
    """

    probabilities = {
        target: float(
            ml_result[
                "deficiencies"
            ][target]["probability"]
        )
        for target in RULE_TARGETS
    }

    predictions = {
        target: int(
            bool(
                ml_result[
                    "deficiencies"
                ][target]["prediction"]
            )
        )
        for target in RULE_TARGETS
    }

    deficiencies = {}

    completeness_all = (
        expert_result.get(
            "hypothesis_completeness",
            {},
        )
    )

    review_targets = set(
        expert_result.get(
            "review_targets",
            [],
        )
    )

    for target in RULE_TARGETS:

        completeness = (
            completeness_all.get(
                target,
                {},
            )
        )

        deficiencies[target] = {
            "probability": round(
                probabilities[target],
                4,
            ),

            "prediction": bool(
                predictions[target]
            ),

            "rule_score": round(
                float(
                    expert_result[
                        "rule_scores"
                    ][target]
                ),
                4,
            ),

            "rule_state": (
                expert_result[
                    "rule_states"
                ][target]
            ),

            "confidence": branch_confidence(
                probabilities[target],
                predictions[target],
            ),

            # Новый врачебный слой
            "assessment_status": (
                completeness.get(
                    "status",
                    "unknown",
                )
            ),

            "assessment_complete": (
                bool(
                    completeness.get(
                        "complete",
                        False,
                    )
                )
            ),

            "available_key_markers": (
                completeness.get(
                    "available_key_markers",
                    [],
                )
            ),

            "missing_key_markers": (
                completeness.get(
                    "missing_key_markers",
                    [],
                )
            ),

            "requires_review": (
                target in review_targets
            ),
        }

    clinical_messages = (
        build_clinical_messages(
            probabilities,
            predictions,
            expert_result,
        )
    )

    data_limitations = (
        build_data_limitations(
            expert_result
        )
    )

    return {
        "patient_id": patient_id,

        # Исходный итог ML не меняем.
        "prediction": ml_result[
            "prediction"
        ],

        "confidence": (
            overall_screening_confidence(
                probabilities,
                predictions,
            )
        ),

        "deficiencies": deficiencies,

        # Physician-reviewed interpretation
        "clinical_messages": (
            clinical_messages
        ),

        "mandatory_review": (
            bool(
                expert_result.get(
                    "mandatory_review",
                    False,
                )
            )
        ),

        "clinical_priority": (
            expert_result.get(
                "clinical_priority",
                "combined",
            )
        ),

        "review_targets": (
            expert_result.get(
                "review_targets",
                [],
            )
        ),

        "data_limitations": (
            data_limitations
        ),

        "incomplete_hypotheses": (
            expert_result.get(
                "incomplete_hypotheses",
                [],
            )
        ),

        "hypothesis_completeness": (
            expert_result.get(
                "hypothesis_completeness",
                {},
            )
        ),

        "evidence": expert_result[
            "evidence"
        ],

        "fired_rules": expert_result[
            "fired_rules"
        ],

        "conflicts": expert_result[
            "conflicts"
        ],

        "recommended_next_tests": (
            expert_result[
                "recommended_next_tests"
            ]
        ),

        "coverage": ml_result.get(
            "coverage"
        ),

        "warnings": ml_result.get(
            "warnings",
            [],
        ),

        "disclaimer": (
            "Предварительная оценка по доступным "
            "данным. Результат является системой "
            "поддержки принятия решений, не является "
            "самостоятельным клиническим диагнозом "
            "и требует интерпретации врачом. "
            "Отсутствующие лабораторные показатели "
            "могут ограничивать проверку "
            "альтернативных диагностических гипотез."
        ),
    }