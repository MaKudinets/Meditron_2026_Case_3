from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from expert.engine import run_expert_engine
from expert.explanations import build_explanation_payload

from ml.inference.loader import load_inference_bundle
from ml.inference.predictor import predict_one


DEFAULT_MIN_FEATURE_COVERAGE = 0.70


def _prepare_expert_inputs(
    ml_result: dict[str, Any],
) -> tuple[dict[str, float], dict[str, int]]:
    """
    Преобразует результат ML inference в формат,
    необходимый expert engine.
    """

    deficiencies = ml_result["deficiencies"]

    probabilities = {
        target: float(result["probability"])
        for target, result in deficiencies.items()
    }

    predictions = {
        target: int(bool(result["prediction"]))
        for target, result in deficiencies.items()
    }

    return probabilities, predictions


def _build_data_quality(
    ml_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Формирует единый блок информации
    о качестве и полноте входных данных.
    """

    return {
        "coverage": float(
            ml_result.get("coverage", 0.0)
        ),
        "used_features": list(
            ml_result.get("used_features", [])
        ),
        "missing_features": list(
            ml_result.get("dropped_features", [])
        ),
        "warnings": list(
            ml_result.get("warnings", [])
        ),
    }


def _build_model_info(
    bundle_dir: str | Path | None = None,
) -> dict[str, Any]:
    """
    Получает информацию о версии ML bundle.

    load_inference_bundle использует внутренний cache,
    поэтому модели повторно с диска не загружаются.
    """

    bundle = load_inference_bundle(
        bundle_dir=bundle_dir
    )

    manifest = bundle.manifest

    return {
        "bundle_name": manifest.get("bundle_name"),
        "bundle_version": manifest.get("bundle_version"),
    }


def _merge_deficiency_results(
    explanation_payload: dict[str, Any],
    ml_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Объединяет результаты ML и expert layer
    для каждой диагностической ветки.

    build_explanation_payload уже добавляет:
    - probability
    - prediction
    - rule_score
    - rule_state
    - confidence

    Но threshold хранится в ML result,
    поэтому добавляем его отдельно.
    """

    result = {}

    expert_deficiencies = explanation_payload[
        "deficiencies"
    ]

    ml_deficiencies = ml_result[
        "deficiencies"
    ]

    for target, expert_result in expert_deficiencies.items():
        item = dict(expert_result)

        item["threshold"] = float(
            ml_deficiencies[target]["threshold"]
        )

        result[target] = item

    return result


def run_screening(
    features: Mapping[str, Any],
    *,
    patient_id: str | None = None,
    bundle_dir: str | Path | None = None,
    min_feature_coverage: float = DEFAULT_MIN_FEATURE_COVERAGE,
    allow_low_coverage: bool = True,
) -> dict[str, Any]:
    """
    Выполняет полный скрининг одного пациента.

    Pipeline:
        input
        -> ML inference
        -> expert system
        -> explanation
        -> API response

    Функция не зависит от FastAPI и может использоваться
    отдельно в тестах, CLI или будущих сервисах.
    """

    patient_features = dict(features)

    # ---------------------------------------------------------
    # 1. ML inference
    # ---------------------------------------------------------

    ml_result = predict_one(
        patient_features,
        bundle_dir=bundle_dir,
        min_feature_coverage=min_feature_coverage,
        allow_low_coverage=allow_low_coverage,
    )

    # ---------------------------------------------------------
    # 2. Подготавливаем выход ML для expert engine
    # ---------------------------------------------------------

    probabilities, predictions = _prepare_expert_inputs(
        ml_result
    )

    # ---------------------------------------------------------
    # 3. Expert layer
    # ---------------------------------------------------------

    expert_result = run_expert_engine(
        patient=patient_features,
        probabilities=probabilities,
        predictions=predictions,
    )

    # ---------------------------------------------------------
    # 4. Explanation payload
    # ---------------------------------------------------------

    explanation_payload = build_explanation_payload(
        patient_id=patient_id,
        ml_result=ml_result,
        expert_result=expert_result,
    )

    # ---------------------------------------------------------
    # 5. Собираем окончательный API response
    # ---------------------------------------------------------

    response = {
        "screening_id": uuid4().hex,

        "patient_id": patient_id,

        "prediction": explanation_payload[
            "prediction"
        ],

        "confidence": explanation_payload[
            "confidence"
        ],

        "deficiencies": _merge_deficiency_results(
            explanation_payload,
            ml_result,
        ),

        "data_quality": _build_data_quality(
            ml_result
        ),

        "evidence": explanation_payload.get(
            "evidence",
            [],
        ),

        "conflicts": explanation_payload.get(
            "conflicts",
            [],
        ),

        "recommended_next_tests": explanation_payload.get(
            "recommended_next_tests",
            [],
        ),

        "model": _build_model_info(
            bundle_dir=bundle_dir
        ),

        "disclaimer": explanation_payload[
            "disclaimer"
        ],
    }

    return response