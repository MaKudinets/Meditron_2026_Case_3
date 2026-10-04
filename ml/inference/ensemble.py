from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


EPS = 1e-6


def probability_to_logit(probabilities):
    p = np.clip(
        np.asarray(probabilities, dtype=float),
        EPS,
        1.0 - EPS,
    )
    return np.log(p / (1.0 - p)).reshape(-1, 1)


def apply_platt_calibrator(calibrator, probabilities):
    return calibrator.predict_proba(
        probability_to_logit(probabilities)
    )[:, 1]


def first_existing_column(columns: Iterable[str], candidates: Iterable[str]):
    lookup = {str(c).lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def extract_ensemble_settings(
    meta: pd.DataFrame,
    targets: Iterable[str],
) -> dict[str, dict[str, float]]:
    """
    Convert the fold-specific settings saved by notebook 04 into one
    deployable setting per target.

    The deployment bundle uses the median across the five fold-specific
    weights/thresholds. This is the same policy used in notebook 06.
    """
    cols = list(meta.columns)

    target_col = first_existing_column(cols, ["target", "task", "label"])
    threshold_col = first_existing_column(
        cols,
        [
            "threshold",
            "ensemble_threshold",
            "best_threshold",
            "selected_threshold",
            "decision_threshold",
        ],
    )
    l1_weight_col = first_existing_column(
        cols,
        ["l1_weight", "weight_l1", "w_l1", "logreg_weight", "logistic_weight"],
    )
    cat_weight_col = first_existing_column(
        cols,
        [
            "catboost_weight",
            "weight_catboost",
            "w_catboost",
            "w_cb",
            "cat_weight",
            "weight_cat",
        ],
    )
    rule_weight_col = first_existing_column(
        cols,
        ["rule_weight", "weight_rule", "w_rule", "clinical_weight", "weight_clinical"],
    )

    required = {
        "target": target_col,
        "threshold": threshold_col,
        "l1_weight": l1_weight_col,
        "catboost_weight": cat_weight_col,
    }
    missing = [name for name, col in required.items() if col is None]
    if missing:
        raise ValueError(
            f"Cannot parse ensemble metadata; missing fields={missing}; columns={cols}"
        )

    settings: dict[str, dict[str, float]] = {}

    for target in targets:
        rows = meta.loc[
            meta[target_col].astype(str).eq(str(target))
        ].copy()

        if rows.empty:
            raise ValueError(f"No ensemble metadata rows for target={target}")

        values = {
            "l1_weight": float(rows[l1_weight_col].median()),
            "catboost_weight": float(rows[cat_weight_col].median()),
            "rule_weight": (
                float(rows[rule_weight_col].median())
                if rule_weight_col is not None
                else 0.0
            ),
            "threshold": float(rows[threshold_col].median()),
            "n_folds": int(len(rows)),
        }

        if values["l1_weight"] + values["catboost_weight"] <= 0:
            raise ValueError(f"{target}: L1 + CatBoost weights must be positive.")

        settings[str(target)] = values

    return settings


def weighted_ensemble_probability(
    l1_calibrated,
    catboost_calibrated,
    *,
    l1_weight: float,
    catboost_weight: float,
):
    denominator = float(l1_weight + catboost_weight)
    if denominator <= 0:
        raise ValueError("l1_weight + catboost_weight must be > 0")

    return (
        l1_weight * np.asarray(l1_calibrated, dtype=float)
        + catboost_weight * np.asarray(catboost_calibrated, dtype=float)
    ) / denominator
