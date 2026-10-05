from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from api.database.models import User

from api.schemas.doctor_imports import (
    DoctorBulkImportResponse,
)

from api.security.auth import (
    get_current_user,
)

from api.services.doctor_file_parser_service import (
    parse_doctor_bulk_file,
)

from api.services.file_parser_service import (
    LabFileParsingError,
    UnsupportedFileFormatError,
)


router = APIRouter(
    prefix="/api/v1/doctor/imports",
    tags=["Doctor Imports"],
)


MAX_DOCTOR_FILE_SIZE = (
    10 * 1024 * 1024
)


@router.post(
    "/lab-file",
    response_model=(
        DoctorBulkImportResponse
    ),
    summary=(
        "Preview laboratory data "
        "for multiple patients"
    ),
)
async def import_doctor_lab_file(
    file: UploadFile = File(...),

    user: User = Depends(
        get_current_user
    ),
) -> DoctorBulkImportResponse:
    """
    Разбирает врачебный CSV/XLSX.

    Никакие screening'и здесь
    автоматически НЕ запускаются.
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
    # FILE
    # ========================================================

    filename = (
        file.filename
        or "uploaded-file"
    )

    content = await file.read()

    if not content:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Uploaded file is empty"
            ),
        )

    if (
        len(content)
        > MAX_DOCTOR_FILE_SIZE
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            ),
            detail=(
                "File size exceeds 10 MB"
            ),
        )

    # ========================================================
    # PARSE
    # ========================================================

    try:

        result = (
            parse_doctor_bulk_file(
                filename,
                content,
            )
        )

    except UnsupportedFileFormatError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail=str(
                error
            ),
        )

    except LabFileParsingError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                error
            ),
        )

    return DoctorBulkImportResponse(
        **result
    )