from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    """
    Данные одного пациента для выполнения ML-предсказания.
    """

    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )

    features: dict[str, float | None] = Field(
        ...,
        min_length=1,
        description="Признаки пациента, используемые ML-моделями",
    )