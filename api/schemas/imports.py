from typing import Any

from pydantic import BaseModel, Field


class ImportedLabMetadata(BaseModel):
    unit: str | None = None

    reference_low: float | None = None

    reference_high: float | None = None

    reference_text: str | None = None


class UnrecognizedItem(BaseModel):
    name: str

    value: Any | None = None


class FileImportResponse(BaseModel):
    filename: str

    format: str

    features: dict[str, float | str] = Field(
        default_factory=dict,
    )

    metadata: dict[
        str,
        ImportedLabMetadata,
    ] = Field(
        default_factory=dict,
    )

    recognized_count: int

    unrecognized: list[
        UnrecognizedItem
    ] = Field(
        default_factory=list,
    )

    warnings: list[str] = Field(
        default_factory=list,
    )