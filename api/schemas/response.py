from typing import Literal
from pydantic import BaseModel, Field

class DeficiencyPrediction(BaseModel):
    """
    Результат предсказания для одного дефицита.
    """

    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Вероятность дефицита, рассчитанная моделью",
    )
    threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Порог принятия решения",
    )
    screen_positive: bool = Field(
        ...,
        description="Превышает ли вероятность установленный threshold",
    )
    status: Literal[
        "elevated_screening_risk",
        "low_screening_risk",
        "insufficient_data",
    ]
class PredictionResponse(BaseModel):
    """
    Итоговый ответ API для одного пациента.
    """

    vitamin_d: DeficiencyPrediction
    iron: DeficiencyPrediction