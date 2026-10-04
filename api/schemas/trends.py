from datetime import datetime

from pydantic import BaseModel, Field


class TrendPoint(BaseModel):
    screening_id: str

    date: datetime

    value: float

    reference_low: float | None = None

    reference_high: float | None = None

    reference_source: str | None = None


class TrendSeries(BaseModel):
    feature: str

    label: str

    unit: str | None = None

    reference_low: float | None = None

    reference_high: float | None = None

    points: list[
        TrendPoint
    ] = Field(
        default_factory=list
    )


class TrendGroup(BaseModel):
    key: str

    label: str

    series: list[
        TrendSeries
    ] = Field(
        default_factory=list
    )


class TrendsResponse(BaseModel):
    groups: list[
        TrendGroup
    ] = Field(
        default_factory=list
    )