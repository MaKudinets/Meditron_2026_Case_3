import logging

from fastapi import APIRouter, HTTPException

from api.schemas.request import PredictionRequest
from api.schemas.response import PredictionResponse
from api.services.prediction_service import get_prediction


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/predict",
    tags=["Prediction"],
)


@router.post(
    "",
    response_model=PredictionResponse,
    summary="Screen patient for latent deficiency risks",
)
def predict_patient(
    request: PredictionRequest,
) -> PredictionResponse:
    """
    Выполняет скрининговое ML-предсказание
    для одного пациента.

    Возвращает оценки риска:
    - Vitamin D deficiency
    - Iron deficiency
    """

    try:
        result = get_prediction(
            features=request.features
        )

        return PredictionResponse(
            **result
        )

    except ValueError as error:
        logger.warning(
            "Invalid prediction input: %s",
            error,
        )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except FileNotFoundError as error:
        logger.exception(
            "Required ML artifact was not found"
        )

        raise HTTPException(
            status_code=500,
            detail="Required ML artifact was not found",
        ) from error

    except Exception as error:
        logger.exception(
            "Unexpected prediction error"
        )

        raise HTTPException(
            status_code=500,
            detail="Prediction failed",
        ) from error