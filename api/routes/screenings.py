import logging

from fastapi import APIRouter, HTTPException

from api.schemas.request import ScreeningRequest
from api.schemas.response import ScreeningResponse
from api.services.screening_service import run_screening


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/screenings",
    tags=["Screenings"],
)


@router.post(
    "",
    response_model=ScreeningResponse,
    summary="Run deficiency screening",
)
def create_screening(
    request: ScreeningRequest,
) -> ScreeningResponse:
    """
    Выполняет полный скрининг одного пациента.

    Pipeline:
    - validation
    - ML inference
    - expert rules
    - explanations
    - recommendations
    """

    try:
        result = run_screening(
        features=request.features.model_dump(exclude_none=True),
            patient_id=request.patient_id,
        )

        return ScreeningResponse(
            **result
        )

    except ValueError as error:
        logger.warning(
            "Invalid screening input: %s",
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

    except RuntimeError as error:
        logger.exception(
            "Screening engine error"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Unexpected screening error"
        )

        raise HTTPException(
            status_code=500,
            detail="Screening failed",
        ) from error