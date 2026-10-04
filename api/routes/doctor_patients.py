from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from sqlalchemy.orm import Session

from api.database.database import (
    get_db,
)

from api.database.models import (
    User,
)

from api.schemas.doctor_patients import (
    DoctorPatientListItem,
    DoctorPatientListResponse,
)

from api.schemas.history import (
    ScreeningHistoryItem,
    ScreeningHistoryResponse,
)

from api.schemas.response import (
    PredictionSummary,
    ScreeningResponse,
)

from api.schemas.trends import (
    TrendsResponse,
)

from api.security.auth import (
    get_current_user,
)

from api.services.doctor_patient_service import (
    DoctorPatientNotFoundError,
    DoctorRoleRequiredError,
    DoctorScreeningNotFoundError,
    get_doctor_patient,
    get_doctor_patient_screening,
    list_doctor_patient_screenings,
    list_doctor_patients,
)

from api.services.report_service import (
    ReportGenerationError,
    build_screening_report_pdf,
    get_screening_lab_values,
)

from api.services.trends_service import (
    get_patient_trends,
)


router = APIRouter(
    prefix="/api/v1/doctor/patients",
    tags=["Doctor Patients"],
)


# ============================================================
# HELPERS
# ============================================================


def ensure_doctor(
    user: User,
) -> None:
    """
    Проверяет, что текущий пользователь
    имеет роль doctor.
    """

    if user.role != "doctor":

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Doctor account required"
            ),
        )


# ============================================================
# PATIENT LIST
# ============================================================


@router.get(
    "",
    response_model=(
        DoctorPatientListResponse
    ),
    summary="Get doctor's patients",
)
def get_my_patients(
    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> DoctorPatientListResponse:
    """
    Возвращает список пациентов,
    связанных с текущим врачом.

    Для каждого пациента возвращается:
    - patient_code;
    - количество screening;
    - дата последнего screening.
    """

    ensure_doctor(
        user
    )

    try:

        patients = (
            list_doctor_patients(
                db,
                doctor=user,
            )
        )

    except DoctorRoleRequiredError:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Doctor account required"
            ),
        )

    items = [
        DoctorPatientListItem(
            **patient
        )
        for patient in patients
    ]

    return DoctorPatientListResponse(
        items=items,

        total=len(
            items
        ),
    )


# ============================================================
# PATIENT SCREENING HISTORY
# ============================================================


@router.get(
    "/{patient_code}/screenings",
    response_model=(
        ScreeningHistoryResponse
    ),
    summary=(
        "Get patient's screening history"
    ),
)
def get_patient_screenings(
    patient_code: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> ScreeningHistoryResponse:
    """
    Возвращает историю скринингов
    выбранного пациента врача.
    """

    ensure_doctor(
        user
    )

    try:

        screenings = (
            list_doctor_patient_screenings(
                db,

                doctor=user,

                patient_code=(
                    patient_code
                ),
            )
        )

    except DoctorPatientNotFoundError:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Patient not found"
            ),
        )

    items = []

    for screening in screenings:

        result = (
            screening.result_data
            or {}
        )

        prediction_data = (
            result.get(
                "prediction",
                {},
            )
        )

        items.append(
            ScreeningHistoryItem(
                screening_id=(
                    screening.id
                ),

                created_at=(
                    screening.created_at
                ),

                prediction=(
                    PredictionSummary(
                        **prediction_data
                    )
                ),

                coverage=(
                    screening.coverage
                ),

                source_type=(
                    screening.source_type
                ),

                bundle_version=(
                    screening.bundle_version
                ),
            )
        )

    return ScreeningHistoryResponse(
        items=items,

        total=len(
            items
        ),
    )


# ============================================================
# GET ONE PATIENT SCREENING
# ============================================================


@router.get(
    (
        "/{patient_code}"
        "/screenings/{screening_id}"
    ),
    response_model=(
        ScreeningResponse
    ),
    summary=(
        "Get one patient's screening"
    ),
)
def get_patient_screening(
    patient_code: str,
    screening_id: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> ScreeningResponse:
    """
    Возвращает полный сохранённый
    результат одного screening пациента.

    Screening должен принадлежать пациенту,
    к которому текущий врач имеет доступ.
    """

    ensure_doctor(
        user
    )

    try:

        screening = (
            get_doctor_patient_screening(
                db,

                doctor=user,

                patient_code=(
                    patient_code
                ),

                screening_id=(
                    screening_id
                ),
            )
        )

    except DoctorPatientNotFoundError:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Patient not found"
            ),
        )

    except DoctorScreeningNotFoundError:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Screening not found"
            ),
        )

    return ScreeningResponse(
        **screening.result_data
    )


# ============================================================
# PATIENT TRENDS
# ============================================================


@router.get(
    "/{patient_code}/trends",
    response_model=(
        TrendsResponse
    ),
    summary=(
        "Get patient's laboratory trends"
    ),
)
def get_doctor_patient_trends(
    patient_code: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> TrendsResponse:
    """
    Возвращает динамику лабораторных
    показателей выбранного пациента.

    Используются уже сохранённые LabValue.
    ML повторно не запускается.
    """

    ensure_doctor(
        user
    )

    try:

        patient_profile = (
            get_doctor_patient(
                db,

                doctor=user,

                patient_code=(
                    patient_code
                ),
            )
        )

    except DoctorPatientNotFoundError:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Patient not found"
            ),
        )

    result = (
        get_patient_trends(
            db,

            patient_profile=(
                patient_profile
            ),
        )
    )

    return TrendsResponse(
        **result
    )


# ============================================================
# PATIENT PDF REPORT
# ============================================================


@router.get(
    (
        "/{patient_code}"
        "/screenings/{screening_id}"
        "/report.pdf"
    ),
    summary=(
        "Download patient's "
        "screening PDF report"
    ),
    responses={
        200: {
            "content": {
                "application/pdf": {}
            },
            "description": (
                "Screening PDF report"
            ),
        }
    },
)
def download_patient_screening_report(
    patient_code: str,
    screening_id: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> Response:
    """
    Создаёт PDF-отчёт из уже
    сохранённого screening пациента.

    Модель повторно НЕ запускается.
    """

    ensure_doctor(
        user
    )

    # ========================================================
    # SCREENING ACCESS
    # ========================================================

    try:

        screening = (
            get_doctor_patient_screening(
                db,

                doctor=user,

                patient_code=(
                    patient_code
                ),

                screening_id=(
                    screening_id
                ),
            )
        )

    except DoctorPatientNotFoundError:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Patient not found"
            ),
        )

    except DoctorScreeningNotFoundError:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Screening not found"
            ),
        )

    # ========================================================
    # LAB VALUES
    # ========================================================

    lab_values = (
        get_screening_lab_values(
            db,

            screening_id=(
                screening.id
            ),
        )
    )

    # ========================================================
    # PDF GENERATION
    # ========================================================

    try:

        pdf_bytes = (
            build_screening_report_pdf(
                screening=(
                    screening
                ),

                lab_values=(
                    lab_values
                ),

                patient_code=(
                    patient_code
                ),
            )
        )

    except ReportGenerationError:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Could not generate PDF report"
            ),
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    filename = (
        "meditron_"
        f"{patient_code}_"
        f"{screening.id}.pdf"
    )

    return Response(
        content=(
            pdf_bytes
        ),

        media_type=(
            "application/pdf"
        ),

        headers={
            "Content-Disposition": (
                "attachment; "
                f'filename="{filename}"'
            )
        },
    )