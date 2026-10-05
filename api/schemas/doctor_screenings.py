from typing import Literal

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


class DoctorBulkScreeningPatient(
    BaseModel
):
    """
    Один подтверждённый пациент
    из врачебного preview.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    patient_code: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    features: PatientFeatures

    lab_metadata: dict[
        str,
        ImportedLabMetadata,
    ] = Field(
        default_factory=dict,
    )


class DoctorBulkScreeningRequest(
    BaseModel
):
    """
    Подтверждение врачом bulk screening.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    source_filename: str | None = Field(
        default=None,
        max_length=255,
    )

    patients: list[
        DoctorBulkScreeningPatient
    ] = Field(
        ...,
        min_length=1,
        max_length=200,
    )


class DoctorBulkScreeningResultItem(
    BaseModel
):
    """
    Результат обработки одного пациента.
    """

    patient_code: str

    status: Literal[
        "success",
        "error",
    ]

    screening_id: str | None = None

    prediction: (
        PredictionSummary
        | None
    ) = None

    coverage: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    error: str | None = None


class DoctorBulkScreeningResponse(
    BaseModel
):
    total: int

    succeeded: int

    failed: int

    results: list[
        DoctorBulkScreeningResultItem
    ] = Field(
        default_factory=list,
    )