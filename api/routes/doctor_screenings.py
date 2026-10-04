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

from api.database.models import (
    User,
)

from api.schemas.doctor_screenings import (
    DoctorBulkScreeningRequest,
    DoctorBulkScreeningResponse,
    DoctorBulkScreeningResultItem,
)

from api.security.auth import (
    get_current_user,
)

from api.services.doctor_screening_service import (
    DoctorRoleRequiredError,
    run_doctor_patient_screening,
)


router = APIRouter(
    prefix="/api/v1/doctor/screenings",
    tags=["Doctor Screenings"],
)


# ============================================================
# BULK SCREENING
# ============================================================


@router.post(
    "/bulk",
    response_model=(
        DoctorBulkScreeningResponse
    ),
    summary=(
        "Run screenings for "
        "multiple patients"
    ),
)
def create_bulk_screenings(
    request: DoctorBulkScreeningRequest,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> DoctorBulkScreeningResponse:
    """
    Выполняет скрининг для пациентов,
    которых врач уже проверил
    на этапе preview.
    """

    # ========================================================
    # ROLE
    # ========================================================

    if user.role != "doctor":

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Doctor account required"
            ),
        )

    # ========================================================
    # RESULTS
    # ========================================================

    results = []

    succeeded = 0

    failed = 0

    # ========================================================
    # PATIENTS
    # ========================================================

    for patient in request.patients:

        try:

            response = (
                run_doctor_patient_screening(
                    db,

                    doctor=user,

                    patient=patient,

                    source_filename=(
                        request.source_filename
                    ),
                )
            )

            results.append(
                DoctorBulkScreeningResultItem(
                    patient_code=(
                        patient.patient_code
                    ),

                    status="success",

                    screening_id=(
                        response.screening_id
                    ),

                    prediction=(
                        response.prediction
                    ),

                    coverage=(
                        response.data_quality.coverage
                    ),

                    error=None,
                )
            )

            succeeded += 1

        except DoctorRoleRequiredError:

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Doctor account required"
                ),
            )

        except Exception:

            # На случай ошибки одной строки
            # остальные пациенты всё равно
            # продолжают обрабатываться.

            db.rollback()

            results.append(
                DoctorBulkScreeningResultItem(
                    patient_code=(
                        patient.patient_code
                    ),

                    status="error",

                    screening_id=None,

                    prediction=None,

                    coverage=None,

                    error=(
                        "Screening could not "
                        "be completed"
                    ),
                )
            )

            failed += 1

    return DoctorBulkScreeningResponse(
        total=len(
            request.patients
        ),

        succeeded=succeeded,

        failed=failed,

        results=results,
    )