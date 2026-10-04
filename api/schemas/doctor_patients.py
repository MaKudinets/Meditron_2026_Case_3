from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
)


class DoctorPatientListItem(BaseModel):
    patient_code: str

    screening_count: int = Field(
        ge=0,
    )

    last_screening_at: (
        datetime
        | None
    ) = None


class DoctorPatientListResponse(
    BaseModel
):
    items: list[
        DoctorPatientListItem
    ] = Field(
        default_factory=list,
    )

    total: int = Field(
        ge=0,
    )