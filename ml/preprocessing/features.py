from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from .validator import load_feature_contract, validate_input


def _to_frame(data: Mapping[str, Any] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, Mapping):
        return pd.DataFrame([dict(data)])
    raise TypeError("data must be a mapping or pandas.DataFrame")


def prepare_features(
    data: Mapping[str, Any] | pd.DataFrame,
    feature_contract: Mapping[str, Any] | str | Path,
    *,
    min_feature_coverage: float = 0.70,
    require_anemia_fields: bool = True,
    reject_low_coverage: bool = True,
):
    """
    Convert incoming data to the exact frozen 37-feature schema.

    Returns
    -------
    X : pd.DataFrame
        Features in the exact contract order.
    report : ValidationReport
        Validation/coverage report.
    """
    contract = load_feature_contract(feature_contract)
    report = validate_input(
        data,
        contract,
        min_feature_coverage=min_feature_coverage,
        require_anemia_fields=require_anemia_fields,
    )

    if report.errors:
        raise ValueError("; ".join(report.errors))

    if reject_low_coverage and report.coverage < min_feature_coverage:
        raise ValueError(
            f"Feature coverage {report.coverage:.1%} is below "
            f"minimum {min_feature_coverage:.1%}."
        )

    frame = _to_frame(data)
    feature_columns = list(contract["features"])
    categorical = set(contract.get("categorical_features", []))

    X = pd.DataFrame(index=frame.index)

    for feature in feature_columns:
        if feature in frame.columns:
            X[feature] = frame[feature]
        else:
            X[feature] = np.nan

    for feature in feature_columns:
        if feature not in categorical:
            X[feature] = pd.to_numeric(X[feature], errors="coerce")

    return X[feature_columns], report


def prepare_catboost_frame(
    frame: pd.DataFrame,
    feature_columns: list[str],
    categorical_features: list[str],
) -> pd.DataFrame:
    out = frame[feature_columns].copy()

    for col in categorical_features:
        out[col] = out[col].astype("object")
        out[col] = out[col].where(out[col].notna(), "__MISSING__")
        out[col] = out[col].astype(str)

    return out
