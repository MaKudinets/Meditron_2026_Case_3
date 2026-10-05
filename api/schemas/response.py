from typing import Any, Literal

from pydantic import BaseModel, Field

from api.schemas.common import Confidence, DataQuality


class PredictionSummary(BaseModel):
    """
    Итоговый результат скрининга.
    """

    anemia: bool

    anemia_class: str

    deficiency_cause: str


class DeficiencyResult(BaseModel):
    """
    Результат отдельной ветки скрининга.
    """

    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    prediction: bool

    threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    rule_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    rule_state: Literal[
        "supports",
        "against",
        "unknown",
    ] | None = None

    confidence: dict[str, Any] | None = None


class EvidenceItem(BaseModel):
    """
    Клинический признак, использованный экспертным слоем.
    """

    target: str

    feature: str

    value: float

    criterion: str

    direction: Literal[
        "supports",
        "against",
        "unknown",
    ]

    strength: str

    source_url: str | None = None


class ConflictItem(BaseModel):
    """
    Конфликт между ML-предсказанием
    и экспертными правилами.
    """

    target: str

    type: str

    severity: str

    ensemble_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    rule_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    rule_state: str

    message: str


class RecommendedTest(BaseModel):
    """
    Анализ, который может помочь уточнить
    скрининговый результат.
    """

    test: str

    target: str

    reason: str


class ModelInfo(BaseModel):
    """
    Информация о production ML bundle.
    """

    bundle_name: str | None = None

    bundle_version: str | None = None


class ScreeningResponse(BaseModel):
    """
    Полный API-ответ одного скрининга.
    """

    screening_id: str

    patient_id: str | None = None

    prediction: PredictionSummary

    confidence: Confidence

    deficiencies: dict[str, DeficiencyResult]

    data_quality: DataQuality

    evidence: list[EvidenceItem] = Field(
        default_factory=list,
    )

    conflicts: list[ConflictItem] = Field(
        default_factory=list,
    )

    recommended_next_tests: list[RecommendedTest] = Field(
        default_factory=list,
    )

    model: ModelInfo

    disclaimer: str