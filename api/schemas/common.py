from typing import Literal

from pydantic import BaseModel, Field


ConfidenceLevel = Literal[
    "high",
    "moderate",
    "low",
]


class Confidence(BaseModel):
    """
    Оценка уверенности итогового скринингового вывода.
    """

    basis: str | None = None

    limiting_target: str | None = None

    certainty: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    level: ConfidenceLevel


class DataQuality(BaseModel):
    """
    Информация о полноте входных данных.
    """

    coverage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    used_features: list[str] = Field(
        default_factory=list,
    )

    missing_features: list[str] = Field(
        default_factory=list,
    )

    warnings: list[str] = Field(
        default_factory=list,
    )