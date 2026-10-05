from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping
import json

import numpy as np
import pandas as pd


@dataclass
class ValidationReport:
    n_rows: int
    n_expected_features: int
    used_features: list[str]
    missing_features: list[str]
    unknown_features: list[str]
    coverage: float
    warnings: list[str]
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["ok"] = self.ok
        return result


def load_feature_contract(contract: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(contract, Mapping):
        return dict(contract)

    path = Path(contract)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _to_frame(data: Mapping[str, Any] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.copy()

    if isinstance(data, Mapping):
        return pd.DataFrame([dict(data)])

    raise TypeError("data must be a mapping or pandas.DataFrame")


def validate_input(
    data: Mapping[str, Any] | pd.DataFrame,
    feature_contract: Mapping[str, Any] | str | Path,
    *,
    min_feature_coverage: float = 0.70,
    require_anemia_fields: bool = True,
) -> ValidationReport:
    """
    Validate incoming patient data against the frozen feature contract.

    Coverage is calculated from actually non-missing expected features.
    Unknown/extraneous fields are reported but not treated as an error.
    """
    frame = _to_frame(data)
    contract = load_feature_contract(feature_contract)

    expected = list(contract["features"])
    categorical = set(contract.get("categorical_features", []))

    present_columns = [c for c in expected if c in frame.columns]
    unknown = [c for c in frame.columns if c not in expected]

    used = []
    missing = []

    for feature in expected:
        if feature not in frame.columns:
            missing.append(feature)
            continue

        if frame[feature].notna().any():
            used.append(feature)
        else:
            missing.append(feature)

    coverage = len(used) / len(expected) if expected else 0.0

    warnings: list[str] = []
    errors: list[str] = []

    if unknown:
        warnings.append(
            "Unknown fields will not be passed to the frozen models: "
            + ", ".join(sorted(unknown))
        )

    if coverage < min_feature_coverage:
        warnings.append(
            f"Feature coverage {coverage:.1%} is below the production "
            f"reference threshold {min_feature_coverage:.1%}."
        )

    if require_anemia_fields:
        for feature in ("sex", "hemoglobin"):
            if feature not in frame.columns or frame[feature].isna().all():
                errors.append(
                    f"{feature} is required to assemble the final anemia class."
                )

    if "sex" in frame.columns:
        bad_sex = (
            frame["sex"]
            .dropna()
            .astype(str)
            .str.upper()
            .map(lambda x: x not in {"F", "M", "FEMALE", "MALE", "Ж", "М", "ЖЕН", "МУЖ"})
        )
        if bad_sex.any():
            errors.append("sex contains unsupported values; expected F/M.")

    numeric_features = [
        c for c in expected
        if c not in categorical and c in frame.columns
    ]

    for col in numeric_features:
        original_non_missing = frame[col].notna()
        converted = pd.to_numeric(frame[col], errors="coerce")
        invalid = original_non_missing & converted.isna()
        if invalid.any():
            errors.append(f"{col} contains non-numeric values.")

    return ValidationReport(
        n_rows=len(frame),
        n_expected_features=len(expected),
        used_features=used,
        missing_features=missing,
        unknown_features=unknown,
        coverage=float(coverage),
        warnings=warnings,
        errors=errors,
    )
