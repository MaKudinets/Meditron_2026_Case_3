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

from api.schemas.history import (
    DeleteScreeningResponse,
    MeScreeningRequest,
    ScreeningHistoryItem,
    ScreeningHistoryResponse,
)

from api.schemas.response import (
    PredictionSummary,
    ScreeningResponse,
)

from api.security.auth import (
    get_current_user,
)

from api.services.history_service import (
    PatientProfileNotFoundError,
    PatientRoleRequiredError as HistoryPatientRoleRequiredError,
    ScreeningNotFoundError,
    delete_screening,
    get_patient_profile,
    get_screening_by_id,
    get_screening_history,
    save_screening,
)

from api.services.report_service import (
    PatientRoleRequiredError as ReportPatientRoleRequiredError,
    ReportGenerationError,
    ReportScreeningNotFoundError,
    build_screening_report_pdf,
    get_patient_screening_for_report,
    get_screening_lab_values,
)

from api.services.screening_service import (
    run_screening,
)


router = APIRouter(
    prefix="/api/v1/me/screenings",
    tags=["My Screenings"],
)


# ============================================================
# HELPERS
# ============================================================


def require_patient_profile(
    db: Session,
    user: User,
):
    """
    Получает PatientProfile текущего пользователя.

    Endpoint /me/screenings предназначен
    только для аккаунта пациента.
    """

    try:

        return get_patient_profile(
            db,
            user,
        )

    except HistoryPatientRoleRequiredError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                error
            ),
        )

    except PatientProfileNotFoundError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(
                error
            ),
        )


# ============================================================
# CREATE SCREENING
# ============================================================


@router.post(
    "",
    response_model=ScreeningResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run and save patient screening",
)
def create_my_screening(
    request: MeScreeningRequest,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> ScreeningResponse:
    """
    Выполняет скрининг текущего пациента
    и сохраняет результат в историю.

    features:
        передаются в существующий ML.

    lab_metadata:
        используется только для БД и графиков.
        В ML не передается.
    """

    patient_profile = (
        require_patient_profile(
            db,
            user,
        )
    )

    # ========================================================
    # INPUT FEATURES
    # ========================================================

    features = (
        request.features.model_dump(
            exclude_none=True,
            mode="json",
        )
    )

    # ========================================================
    # LAB METADATA
    # ========================================================

    lab_metadata = {}

    for feature, metadata in (
        request.lab_metadata.items()
    ):

        # Не сохраняем metadata для показателя,
        # которого нет среди введённых значений.
        if feature not in features:
            continue

        lab_metadata[
            feature
        ] = metadata.model_dump(
            mode="json"
        )

    # ========================================================
    # EXISTING ML PIPELINE
    # ========================================================

    # ВАЖНО:
    # lab_metadata сюда не передаётся.
    # ML получает только features.

    result = run_screening(
        features=features,
        patient_id=(
            patient_profile.id
        ),
    )

    # Приводим результат к официальной
    # API-схеме.
    response = ScreeningResponse(
        **result
    )

    # Получаем JSON-compatible dict
    # для сохранения в SQLite.
    result_for_storage = (
        response.model_dump(
            mode="json"
        )
    )

    # ========================================================
    # SOURCE
    # ========================================================

    source_type = (
        "file"
        if request.source_filename
        else "manual"
    )

    # ========================================================
    # STORAGE
    # ========================================================

    save_screening(
        db,

        user=user,

        patient_profile=(
            patient_profile
        ),

        features=features,

        result=(
            result_for_storage
        ),

        lab_metadata=(
            lab_metadata
        ),

        source_type=(
            source_type
        ),

        source_filename=(
            request.source_filename
        ),
    )

    return response


# ============================================================
# SCREENING HISTORY
# ============================================================


@router.get(
    "",
    response_model=(
        ScreeningHistoryResponse
    ),
    summary="Get screening history",
)
def list_my_screenings(
    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> ScreeningHistoryResponse:
    """
    Возвращает список предыдущих
    скринингов текущего пациента.
    """

    patient_profile = (
        require_patient_profile(
            db,
            user,
        )
    )

    screenings = (
        get_screening_history(
            db,
            patient_profile=(
                patient_profile
            ),
        )
    )

    items = []

    for screening in screenings:

        result = (
            screening.result_data
            or {}
        )

        prediction = (
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
                        **prediction
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
# GET ONE SCREENING
# ============================================================


@router.get(
    "/{screening_id}",
    response_model=(
        ScreeningResponse
    ),
    summary="Get saved screening",
)
def get_my_screening(
    screening_id: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> ScreeningResponse:
    """
    Возвращает полный сохранённый результат
    одного скрининга.
    """

    patient_profile = (
        require_patient_profile(
            db,
            user,
        )
    )

    try:

        screening = (
            get_screening_by_id(
                db,

                patient_profile=(
                    patient_profile
                ),

                screening_id=(
                    screening_id
                ),
            )
        )

    except ScreeningNotFoundError:

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
# DELETE SCREENING
# ============================================================


@router.delete(
    "/{screening_id}",
    response_model=(
        DeleteScreeningResponse
    ),
    summary="Delete saved screening",
)
def delete_my_screening(
    screening_id: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> DeleteScreeningResponse:
    """
    Удаляет скрининг только текущего пациента.

    Связанные LabValue удаляются
    через FOREIGN KEY CASCADE.
    """

    patient_profile = (
        require_patient_profile(
            db,
            user,
        )
    )

    try:

        delete_screening(
            db,

            patient_profile=(
                patient_profile
            ),

            screening_id=(
                screening_id
            ),
        )

    except ScreeningNotFoundError:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Screening not found"
            ),
        )

    return DeleteScreeningResponse(
        message=(
            "Screening successfully deleted."
        ),
        screening_id=(
            screening_id
        ),
    )


# ============================================================
# PDF REPORT
# ============================================================


@router.get(
    "/{screening_id}/report.pdf",
    summary=(
        "Download screening PDF report"
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
def download_screening_report(
    screening_id: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
) -> Response:
    """
    Формирует PDF из уже сохранённого
    screening.

    Модель повторно не запускается.
    """

    # ========================================================
    # SCREENING ACCESS
    # ========================================================

    try:

        screening = (
            get_patient_screening_for_report(
                db,

                user=user,

                screening_id=(
                    screening_id
                ),
            )
        )

    except ReportPatientRoleRequiredError:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Patient account required"
            ),
        )

    except ReportScreeningNotFoundError:

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
        "meditron_screening_"
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