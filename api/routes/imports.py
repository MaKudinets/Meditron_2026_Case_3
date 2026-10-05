from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from api.database.models import User

from api.schemas.imports import (
    FileImportResponse,
)

from api.security.auth import (
    get_current_user,
)

from api.services.file_parser_service import (
    LabFileParsingError,
    UnsupportedFileFormatError,
    parse_lab_file,
)


router = APIRouter(
    prefix="/api/v1/me/imports",
    tags=["Lab File Import"],
)


MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post(
    "/lab-file",
    response_model=FileImportResponse,
    summary="Extract laboratory values from file",
)
async def import_lab_file(
    file: UploadFile = File(...),

    user: User = Depends(
        get_current_user
    ),
) -> FileImportResponse:

    if user.role != "patient":
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Patient account required"
            ),
        )

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
            detail="Uploaded file is empty",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            ),
            detail=(
                "File size exceeds 5 MB"
            ),
        )

    try:
        parsed = parse_lab_file(
            filename,
            content,
        )

    except UnsupportedFileFormatError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail=str(error),
        )

    except LabFileParsingError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        )

    features = parsed[
        "features"
    ]

    warnings = parsed[
        "warnings"
    ]

    # Эти поля нужны существующему
    # screening endpoint.
    required = {
        "sex",
        "hemoglobin",
    }

    missing_required = (
        required
        - set(features)
    )

    if missing_required:

        warnings.append(
            (
                "Some required screening fields "
                "were not found: "
                + ", ".join(
                    sorted(
                        missing_required
                    )
                )
            )
        )

    return FileImportResponse(
        filename=filename,
        format=parsed[
            "format"
        ],
        features=features,
        metadata=parsed[
            "metadata"
        ],
        recognized_count=len(
            features
        ),
        unrecognized=parsed[
            "unrecognized"
        ],
        warnings=warnings,
    )