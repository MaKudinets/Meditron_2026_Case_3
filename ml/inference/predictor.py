from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ml.preprocessing.features import prepare_features, prepare_catboost_frame
from ml.clinical_rules import anemia_rule

from .ensemble import apply_platt_calibrator, weighted_ensemble_probability
from .loader import InferenceBundle, load_inference_bundle


CORE_TARGETS = [
    "iron_deficiency",
    "B12_deficiency",
    "folate_deficiency",
]


def assemble_predicted_class(
    anemia: int,
    probabilities: Mapping[str, float],
    predictions: Mapping[str, int],
) -> str:
    if sum(int(predictions[t]) for t in CORE_TARGETS) >= 2:
        return "mixed_deficiency"

    candidates: list[tuple[float, str]] = []

    if predictions["iron_deficiency"]:
        candidates.append((
            float(probabilities["iron_deficiency"]),
            "iron_deficiency_anemia" if anemia else "latent_deficiency",
        ))

    if predictions["B12_deficiency"]:
        candidates.append((
            float(probabilities["B12_deficiency"]),
            "B12_deficiency_anemia" if anemia else "B12_deficiency_no_anemia",
        ))

    if predictions["folate_deficiency"]:
        candidates.append((
            float(probabilities["folate_deficiency"]),
            "folate_deficiency_anemia" if anemia else "folate_deficiency_no_anemia",
        ))

    if predictions["B6_deficiency"]:
        candidates.append((
            float(probabilities["B6_deficiency"]),
            "B6_deficiency",
        ))

    if predictions["copper_deficiency"]:
        candidates.append((
            float(probabilities["copper_deficiency"]),
            "copper_deficiency",
        ))

    if anemia and predictions["inflammation_anemia"]:
        candidates.append((
            float(probabilities["inflammation_anemia"]),
            "inflammation_anemia",
        ))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    return "anemia_other" if anemia else "no_anemia_no_deficiency"


def assemble_predicted_cause(
    predicted_class: str,
    probabilities: Mapping[str, float],
) -> str:
    if predicted_class == "mixed_deficiency":
        core = {
            "iron": float(probabilities["iron_deficiency"]),
            "B12": float(probabilities["B12_deficiency"]),
            "folate": float(probabilities["folate_deficiency"]),
        }
        top_two = sorted(core, key=core.get, reverse=True)[:2]
        pair = frozenset(top_two)

        if pair == frozenset(["iron", "B12"]):
            return "iron_B12"
        if pair == frozenset(["iron", "folate"]):
            return "iron_folate"
        return "B12_folate"

    mapping = {
        "iron_deficiency_anemia": "iron_deficiency",
        "latent_deficiency": "iron_deficiency",
        "B12_deficiency_anemia": "B12_deficiency",
        "B12_deficiency_no_anemia": "B12_deficiency",
        "folate_deficiency_anemia": "folate_deficiency",
        "folate_deficiency_no_anemia": "folate_deficiency",
        "B6_deficiency": "B6_deficiency",
        "copper_deficiency": "copper_deficiency",
        "inflammation_anemia": "inflammation",
        "anemia_other": "undetermined",
        "no_anemia_no_deficiency": "none",
    }
    return mapping[predicted_class]


def _predict_frame(
    raw_frame: pd.DataFrame,
    bundle: InferenceBundle,
    *,
    min_feature_coverage: float,
    allow_low_coverage: bool,
):
    X, report = prepare_features(
        raw_frame,
        bundle.feature_contract,
        min_feature_coverage=min_feature_coverage,
        require_anemia_fields=True,
        reject_low_coverage=not allow_low_coverage,
    )

    feature_columns = list(bundle.feature_contract["features"])
    categorical_features = list(
        bundle.feature_contract.get("categorical_features", [])
    )
    X_cat = prepare_catboost_frame(
        X,
        feature_columns,
        categorical_features,
    )

    target_probabilities: dict[str, np.ndarray] = {}
    target_predictions: dict[str, np.ndarray] = {}
    target_debug: dict[str, dict[str, np.ndarray | float]] = {}

    for target, artifacts in bundle.targets.items():
        if abs(artifacts.rule_weight) > 1e-12:
            raise ValueError(
                f"{target}: deployment inference expects rule_weight=0, "
                f"got {artifacts.rule_weight}."
            )

        l1_raw = artifacts.l1_model.predict_proba(X)[:, 1]
        l1_cal = apply_platt_calibrator(
            artifacts.l1_calibrator,
            l1_raw,
        )

        cb_raw = artifacts.catboost_model.predict_proba(X_cat)[:, 1]
        cb_cal = apply_platt_calibrator(
            artifacts.catboost_calibrator,
            cb_raw,
        )

        ensemble_prob = weighted_ensemble_probability(
            l1_cal,
            cb_cal,
            l1_weight=artifacts.l1_weight,
            catboost_weight=artifacts.catboost_weight,
        )
        pred = (ensemble_prob >= artifacts.threshold).astype(int)

        target_probabilities[target] = ensemble_prob
        target_predictions[target] = pred
        target_debug[target] = {
            "l1_raw": l1_raw,
            "l1_calibrated": l1_cal,
            "catboost_raw": cb_raw,
            "catboost_calibrated": cb_cal,
            "threshold": artifacts.threshold,
            "l1_weight": artifacts.l1_weight,
            "catboost_weight": artifacts.catboost_weight,
        }

    outputs = []

    for row_pos, (_, raw_row) in enumerate(raw_frame.iterrows()):
        probabilities = {
            target: float(target_probabilities[target][row_pos])
            for target in bundle.targets
        }
        predictions = {
            target: int(target_predictions[target][row_pos])
            for target in bundle.targets
        }

        anemia = int(anemia_rule(raw_row))
        predicted_class = assemble_predicted_class(
            anemia,
            probabilities,
            predictions,
        )
        predicted_cause = assemble_predicted_cause(
            predicted_class,
            probabilities,
        )

        outputs.append({
            "prediction": {
                "anemia": bool(anemia),
                "anemia_class": predicted_class,
                "deficiency_cause": predicted_cause,
            },
            "deficiencies": {
                target: {
                    "probability": probabilities[target],
                    "prediction": bool(predictions[target]),
                    "threshold": float(bundle.targets[target].threshold),
                }
                for target in bundle.targets
            },
            "coverage": float(report.coverage),
            "used_features": list(report.used_features),
            "dropped_features": list(report.missing_features),
            "warnings": list(report.warnings),
        })

    return outputs


def predict(
    data: Mapping[str, Any] | pd.DataFrame,
    *,
    bundle_dir: str | Path | None = None,
    min_feature_coverage: float = 0.70,
    allow_low_coverage: bool = False,
):
    bundle = load_inference_bundle(bundle_dir)

    if isinstance(data, pd.DataFrame):
        raw_frame = data.copy()
    else:
        raw_frame = pd.DataFrame([dict(data)])

    return _predict_frame(
        raw_frame,
        bundle,
        min_feature_coverage=min_feature_coverage,
        allow_low_coverage=allow_low_coverage,
    )


def predict_one(
    data: Mapping[str, Any],
    *,
    bundle_dir: str | Path | None = None,
    min_feature_coverage: float = 0.70,
    allow_low_coverage: bool = False,
):
    return predict(
        data,
        bundle_dir=bundle_dir,
        min_feature_coverage=min_feature_coverage,
        allow_low_coverage=allow_low_coverage,
    )[0]
