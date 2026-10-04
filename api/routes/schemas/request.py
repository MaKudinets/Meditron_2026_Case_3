from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PatientFeatures(BaseModel):
    """
    Лабораторные и демографические данные одного пациента.

    Названия признаков соответствуют frozen feature contract
    production ML-модели.
    """

    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )

    # ---------------------------------------------------------
    # Demographics
    # ---------------------------------------------------------

    age_years: float | None = Field(
        default=None,
        ge=0,
        le=120,
        description="Возраст пациента в годах",
    )

    sex: Literal["F", "M"] = Field(
        ...,
        description="Пол пациента: F — женский, M — мужской",
    )

    # ---------------------------------------------------------
    # CBC
    # ---------------------------------------------------------

    hemoglobin: float = Field(
        ...,
        ge=0,
        description="Гемоглобин",
    )

    RBC: float | None = Field(
        default=None,
        ge=0,
    )

    hematocrit: float | None = Field(
        default=None,
        ge=0,
    )

    MCV: float | None = Field(
        default=None,
        ge=0,
    )

    MCH: float | None = Field(
        default=None,
        ge=0,
    )

    MCHC: float | None = Field(
        default=None,
        ge=0,
    )

    RDW: float | None = Field(
        default=None,
        ge=0,
    )

    platelets: float | None = Field(
        default=None,
        ge=0,
    )

    WBC: float | None = Field(
        default=None,
        ge=0,
    )

    reticulocytes: float | None = Field(
        default=None,
        ge=0,
    )

    # ---------------------------------------------------------
    # Iron metabolism
    # ---------------------------------------------------------

    ferritin: float | None = Field(
        default=None,
        ge=0,
    )

    serum_iron: float | None = Field(
        default=None,
        ge=0,
    )

    transferrin: float | None = Field(
        default=None,
        ge=0,
    )

    TIBC: float | None = Field(
        default=None,
        ge=0,
    )

    UIBC: float | None = Field(
        default=None,
        ge=0,
    )

    TSAT: float | None = Field(
        default=None,
        ge=0,
    )

    sTfR: float | None = Field(
        default=None,
        ge=0,
    )

    Ret_He: float | None = Field(
        default=None,
        ge=0,
    )

    # ---------------------------------------------------------
    # Vitamins
    # ---------------------------------------------------------

    vitamin_B12: float | None = Field(
        default=None,
        ge=0,
    )

    active_B12: float | None = Field(
        default=None,
        ge=0,
    )

    MMA: float | None = Field(
        default=None,
        ge=0,
    )

    homocysteine: float | None = Field(
        default=None,
        ge=0,
    )

    folate: float | None = Field(
        default=None,
        ge=0,
    )

    vitamin_B6: float | None = Field(
        default=None,
        ge=0,
    )

    # ---------------------------------------------------------
    # Copper
    # ---------------------------------------------------------

    copper: float | None = Field(
        default=None,
        ge=0,
    )

    ceruloplasmin: float | None = Field(
        default=None,
        ge=0,
    )

    # ---------------------------------------------------------
    # Inflammation / general laboratory context
    # ---------------------------------------------------------

    CRP: float | None = Field(
        default=None,
        ge=0,
    )

    ESR: float | None = Field(
        default=None,
        ge=0,
    )

    creatinine: float | None = Field(
        default=None,
        ge=0,
    )

    eGFR: float | None = Field(
        default=None,
        ge=0,
    )

    TSH: float | None = Field(
        default=None,
        ge=0,
    )

    albumin: float | None = Field(
        default=None,
        ge=0,
    )

    # ---------------------------------------------------------
    # Hemolysis
    # ---------------------------------------------------------

    LDH: float | None = Field(
        default=None,
        ge=0,
    )

    indirect_bilirubin: float | None = Field(
        default=None,
        ge=0,
    )

    haptoglobin: float | None = Field(
        default=None,
        ge=0,
    )


class ScreeningRequest(BaseModel):
    """
    Запрос на выполнение одного скрининга.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    patient_id: str | None = Field(
        default=None,
        description=(
            "Необязательный внешний идентификатор пациента. "
            "Не передаётся в ML-модель."
        ),
    )

    features: PatientFeatures