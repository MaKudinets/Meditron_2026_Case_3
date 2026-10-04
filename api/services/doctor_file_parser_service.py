from pathlib import Path

import pandas as pd

from api.services.file_parser_service import (
    ALIAS_LOOKUP,
    LabFileParsingError,
    UnsupportedFileFormatError,
    load_dataframe,
    normalize_name,
    normalize_sex,
    parse_number,
)


# ============================================================
# PATIENT IDENTIFIER
# ============================================================


PATIENT_CODE_ALIASES = {
    "patient_id",
    "patient id",
    "patient code",
    "patient_code",
    "external_code",
    "external code",

    "id пациента",
    "код пациента",
    "ид пациента",
    "пациент",
}


def find_patient_code_column(
    dataframe: pd.DataFrame,
) -> str | None:
    """
    Находит колонку с кодом пациента.
    """

    normalized_aliases = {
        normalize_name(
            alias
        )
        for alias in PATIENT_CODE_ALIASES
    }

    for column in dataframe.columns:

        normalized = normalize_name(
            column
        )

        if normalized in normalized_aliases:
            return column

    return None


# ============================================================
# PATIENT CODE
# ============================================================


def parse_patient_code(
    value,
) -> str | None:

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None

    except (
        TypeError,
        ValueError,
    ):
        pass

    text = str(
        value
    ).strip()

    if not text:
        return None

    return text


# ============================================================
# ONE PATIENT ROW
# ============================================================


def parse_patient_row(
    row,
    *,
    row_number: int,
    patient_code_column: str | None,
) -> dict:
    """
    Разбирает одну строку таблицы.

    ML здесь НЕ запускается.
    """

    features = {}

    warnings = []

    patient_code = None

    if patient_code_column is not None:

        patient_code = parse_patient_code(
            row.get(
                patient_code_column
            )
        )

    if patient_code is None:

        warnings.append(
            "Patient code was not found"
        )

    # ========================================================
    # FEATURES
    # ========================================================

    for column in row.index:

        # Колонка patient_id не является
        # медицинским показателем.
        if (
            patient_code_column is not None
            and column == patient_code_column
        ):
            continue

        canonical = ALIAS_LOOKUP.get(
            normalize_name(
                column
            )
        )

        if canonical is None:
            continue

        raw_value = row.get(
            column
        )

        if raw_value is None:
            continue

        try:
            if pd.isna(
                raw_value
            ):
                continue

        except (
            TypeError,
            ValueError,
        ):
            pass

        # ----------------------------------------------------
        # SEX
        # ----------------------------------------------------

        if canonical == "sex":

            value = normalize_sex(
                raw_value
            )

            if value is None:

                warnings.append(
                    "Could not recognize sex"
                )

                continue

        # ----------------------------------------------------
        # NUMERIC FEATURE
        # ----------------------------------------------------

        else:

            value = parse_number(
                raw_value
            )

            if value is None:

                warnings.append(
                    (
                        "Could not parse "
                        f"{canonical}"
                    )
                )

                continue

        features[
            canonical
        ] = value

    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    required = {
        "sex",
        "hemoglobin",
    }

    missing_required = sorted(
        required
        - set(
            features
        )
    )

    return {
        "row_number": row_number,

        "patient_code": (
            patient_code
        ),

        "features": features,

        "missing_required": (
            missing_required
        ),

        "warnings": warnings,
    }


# ============================================================
# MAIN BULK PARSER
# ============================================================


def parse_doctor_bulk_file(
    filename: str,
    content: bytes,
) -> dict:
    """
    Разбирает CSV/XLSX с несколькими пациентами.

    Одна строка = один пациент.

    На этом этапе данные только распознаются.
    ML НЕ запускается.
    """

    suffix = Path(
        filename
    ).suffix.lower()

    # Для нескольких пациентов пока
    # поддерживаем только табличные форматы.
    if suffix not in {
        ".csv",
        ".xlsx",
    }:

        raise UnsupportedFileFormatError(
            (
                "Doctor bulk import supports "
                "CSV and XLSX files"
            )
        )

    dataframe, file_format = (
        load_dataframe(
            filename,
            content,
        )
    )

    if dataframe.empty:

        raise LabFileParsingError(
            "The file contains no patient rows"
        )

    patient_code_column = (
        find_patient_code_column(
            dataframe
        )
    )

    global_warnings = []

    if patient_code_column is None:

        global_warnings.append(
            (
                "Patient identifier column "
                "was not found"
            )
        )

    patients = []

    # Excel/CSV строка 1 обычно содержит заголовки,
    # поэтому для пользователя первая строка данных = 2.
    for index, (_, row) in enumerate(
        dataframe.iterrows(),
        start=2,
    ):

        patient = parse_patient_row(
            row,
            row_number=index,
            patient_code_column=(
                patient_code_column
            ),
        )

        patients.append(
            patient
        )

    recognized_patients = sum(
        1
        for patient in patients
        if patient[
            "features"
        ]
    )

    return {
        "filename": filename,

        "format": file_format,

        "total_rows": len(
            patients
        ),

        "recognized_patients": (
            recognized_patients
        ),

        "patients": patients,

        "warnings": (
            global_warnings
        ),
    }