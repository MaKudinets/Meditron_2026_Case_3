from pydantic import (
    BaseModel,
    Field,
)


class DoctorPatientPreview(BaseModel):
    row_number: int

    patient_code: str | None = None

    features: dict[
        str,
        float | str,
    ] = Field(
        default_factory=dict
    )

    missing_required: list[
        str
    ] = Field(
        default_factory=list
    )

    warnings: list[
        str
    ] = Field(
        default_factory=list
    )


class DoctorBulkImportResponse(BaseModel):
    filename: str

    format: str

    total_rows: int

    recognized_patients: int

    patients: list[
        DoctorPatientPreview
    ] = Field(
        default_factory=list
    )

    warnings: list[
        str
    ] = Field(
        default_factory=list
    )