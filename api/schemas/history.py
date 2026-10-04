from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from api.schemas.imports import (
    ImportedLabMetadata,
)

from api.schemas.request import (
    PatientFeatures,
)

from api.schemas.response import (
    PredictionSummary,
)


class MeScreeningRequest(BaseModel):
    """
    Новый скрининг авторизованного пациента.

    features идут в ML.

    lab_metadata содержит единицы измерения
    и референсные интервалы и в ML НЕ передается.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    features: PatientFeatures

    lab_metadata: dict[
        str,
        ImportedLabMetadata,
    ] = Field(
        default_factory=dict,
    )

    source_filename: str | None = Field(
        default=None,
        max_length=255,
    )


class ScreeningHistoryItem(BaseModel):
    screening_id: str

    created_at: datetime

    prediction: PredictionSummary

    coverage: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    source_type: str

    bundle_version: str | None = None


class ScreeningHistoryResponse(BaseModel):
    items: list[ScreeningHistoryItem]

    total: int


class DeleteScreeningResponse(BaseModel):
    message: str

    screening_id: str