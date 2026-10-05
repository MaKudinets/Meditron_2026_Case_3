from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from api.database.database import (
    get_db,
)

from api.database.models import User

from api.schemas.trends import (
    TrendsResponse,
)

from api.security.auth import (
    get_current_user,
)

from api.services.history_service import (
    PatientProfileNotFoundError,
    PatientRoleRequiredError,
    get_patient_profile,
)

from api.services.trends_service import (
    get_patient_trends,
)


router = APIRouter(
    prefix="/api/v1/me/trends",
    tags=["Trends"],
)


@router.get(
    "",
    response_model=TrendsResponse,
    summary="Get grouped laboratory trends",
)
def get_my_trends(
    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> TrendsResponse:

    try:
        patient_profile = (
            get_patient_profile(
                db,
                user,
            )
        )

    except PatientRoleRequiredError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(error),
        )

    except PatientProfileNotFoundError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        )

    result = get_patient_trends(
        db,
        patient_profile=(
            patient_profile
        ),
    )

    return TrendsResponse(
        **result
    )