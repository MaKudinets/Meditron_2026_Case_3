import io
import re

from pathlib import Path

import pandas as pd


# ============================================================
# EXCEPTIONS
# ============================================================


class UnsupportedFileFormatError(ValueError):
    pass


class LabFileParsingError(ValueError):
    pass


# ============================================================
# CANONICAL FEATURES
# ============================================================


CANONICAL_FEATURES = {
    "age_years",
    "sex",
    "hemoglobin",
    "RBC",
    "hematocrit",
    "MCV",
    "MCH",
    "MCHC",
    "RDW",
    "platelets",
    "WBC",
    "reticulocytes",
    "ferritin",
    "serum_iron",
    "transferrin",
    "TIBC",
    "UIBC",
    "TSAT",
    "sTfR",
    "Ret_He",
    "vitamin_B12",
    "active_B12",
    "MMA",
    "homocysteine",
    "folate",
    "vitamin_B6",
    "copper",
    "ceruloplasmin",
    "CRP",
    "ESR",
    "creatinine",
    "eGFR",
    "TSH",
    "albumin",
    "LDH",
    "indirect_bilirubin",
    "haptoglobin",
}


# ============================================================
# NORMALIZATION
# ============================================================


def normalize_name(
    value,
) -> str:
    """
    Нормализует названия колонок,
    лабораторных показателей и алиасов.
    """

    if value is None:
        return ""

    text = str(
        value
    ).strip().lower()

    text = text.replace(
        "_",
        " ",
    )

    text = text.replace(
        "ё",
        "е",
    )

    text = text.replace(
        "\u00a0",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# FEATURE ALIASES
# ============================================================


FEATURE_ALIASES = {
    "age_years": {
        "age",
        "age years",
        "возраст",
        "возраст лет",
    },

    "sex": {
        "sex",
        "gender",
        "пол",
    },

    "hemoglobin": {
        "hemoglobin",
        "haemoglobin",
        "hb",
        "hgb",
        "гемоглобин",
    },

    "RBC": {
        "rbc",
        "эритроциты",
        "red blood cells",
        "red blood cell count",
    },

    "hematocrit": {
        "hematocrit",
        "haematocrit",
        "hct",
        "гематокрит",
    },

    "MCV": {
        "mcv",
        "средний объем эритроцита",
        "средний объем эритроцитов",
    },

    "MCH": {
        "mch",
        "среднее содержание гемоглобина",
        "среднее содержание hb",
    },

    "MCHC": {
        "mchc",
        "средняя концентрация гемоглобина",
    },

    "RDW": {
        "rdw",
        "ширина распределения эритроцитов",
    },

    "platelets": {
        "platelets",
        "plt",
        "тромбоциты",
    },

    "WBC": {
        "wbc",
        "лейкоциты",
        "white blood cells",
        "white blood cell count",
    },

    "reticulocytes": {
        "reticulocytes",
        "ret",
        "ретикулоциты",
    },

    "ferritin": {
        "ferritin",
        "ферритин",
    },

    "serum_iron": {
        "serum iron",
        "iron",
        "fe",
        "сывороточное железо",
        "железо",
        "железо сывороточное",
    },

    "transferrin": {
        "transferrin",
        "трансферрин",
    },

    "TIBC": {
        "tibc",
        "ожсс",
        "общая железосвязывающая способность",
        "общая железосвязывающая способность сыворотки",
    },

    "UIBC": {
        "uibc",
        "нжсс",
        "ненасыщенная железосвязывающая способность",
    },

    "TSAT": {
        "tsat",
        "насыщение трансферрина",
        "насыщение трансферрина железом",
        "коэффициент насыщения трансферрина",
    },

    "sTfR": {
        "stfr",
        "растворимый рецептор трансферрина",
        "растворимые рецепторы трансферрина",
    },

    "Ret_He": {
        "ret-he",
        "ret he",
        "rethe",
        "гемоглобин ретикулоцитов",
    },

    "vitamin_B12": {
        "vitamin b12",
        "b12",
        "витамин b12",
        "витамин в12",
        "витамин в 12",
        "цианокобаламин",
    },

    "active_B12": {
        "active b12",
        "активный b12",
        "активный в12",
        "холотранскобаламин",
    },

    "MMA": {
        "mma",
        "methylmalonic acid",
        "метилмалоновая кислота",
    },

    "homocysteine": {
        "homocysteine",
        "гомоцистеин",
    },

    "folate": {
        "folate",
        "folic acid",
        "фолат",
        "фолаты",
        "фолиевая кислота",
    },

    "vitamin_B6": {
        "vitamin b6",
        "b6",
        "витамин b6",
        "витамин в6",
        "витамин в 6",
    },

    "copper": {
        "copper",
        "cu",
        "медь",
    },

    "ceruloplasmin": {
        "ceruloplasmin",
        "церулоплазмин",
    },

    "CRP": {
        "crp",
        "срб",
        "с реактивный белок",
        "с-реактивный белок",
        "c-reactive protein",
    },

    "ESR": {
        "esr",
        "соэ",
        "скорость оседания эритроцитов",
    },

    "creatinine": {
        "creatinine",
        "креатинин",
    },

    "eGFR": {
        "egfr",
        "скф",
        "расчетная скф",
        "скорость клубочковой фильтрации",
    },

    "TSH": {
        "tsh",
        "ттг",
        "тиреотропный гормон",
    },

    "albumin": {
        "albumin",
        "альбумин",
    },

    "LDH": {
        "ldh",
        "лдг",
        "лактатдегидрогеназа",
    },

    "indirect_bilirubin": {
        "indirect bilirubin",
        "непрямой билирубин",
        "билирубин непрямой",
    },

    "haptoglobin": {
        "haptoglobin",
        "гаптоглобин",
    },
}


# ============================================================
# ALIAS LOOKUP
# ============================================================


ALIAS_LOOKUP = {}


for canonical, aliases in FEATURE_ALIASES.items():

    # Каноническое имя тоже принимаем.
    ALIAS_LOOKUP[
        normalize_name(
            canonical
        )
    ] = canonical

    for alias in aliases:

        ALIAS_LOOKUP[
            normalize_name(
                alias
            )
        ] = canonical


# ============================================================
# SEX NORMALIZATION
# ============================================================


def normalize_sex(
    value,
) -> str | None:
    """
    Приводит различные варианты пола
    к F или M.
    """

    text = normalize_name(
        value
    )

    female_values = {
        "f",
        "female",
        "woman",
        "жен",
        "жен.",
        "женский",
        "женщина",
        "ж",
    }

    male_values = {
        "m",
        "male",
        "man",
        "муж",
        "муж.",
        "мужской",
        "мужчина",
        "м",
    }

    if text in female_values:
        return "F"

    if text in male_values:
        return "M"

    return None


# ============================================================
# NUMBER PARSING
# ============================================================


def parse_number(
    value,
) -> float | None:
    """
    Извлекает число из значений вида:

    108
    "108"
    "7,5"
    "7.5 мкмоль/л"
    """

    if value is None:
        return None

    try:
        if pd.isna(
            value
        ):
            return None

    except (
        TypeError,
        ValueError,
    ):
        pass

    if isinstance(
        value,
        (int, float),
    ):
        return float(
            value
        )

    text = str(
        value
    ).strip()

    if not text:
        return None

    text = text.replace(
        ",",
        ".",
    )

    text = text.replace(
        "\u00a0",
        " ",
    )

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        text,
    )

    if match is None:
        return None

    try:
        return float(
            match.group()
        )

    except ValueError:
        return None


# ============================================================
# REFERENCE RANGE PARSING
# ============================================================


def parse_reference(
    value,
) -> tuple[
    float | None,
    float | None,
]:
    """
    Извлекает референсный диапазон.

    Примеры:

    15-150
        -> (15, 150)

    15,5 - 150,5
        -> (15.5, 150.5)

    < 10
        -> (None, 10)

    > 20
        -> (20, None)
    """

    if value is None:
        return None, None

    try:
        if pd.isna(
            value
        ):
            return None, None

    except (
        TypeError,
        ValueError,
    ):
        pass

    text = str(
        value
    ).strip()

    if not text:
        return None, None

    text = text.replace(
        ",",
        ".",
    )

    text = text.replace(
        "–",
        "-",
    )

    text = text.replace(
        "—",
        "-",
    )

    # --------------------------------------------------------
    # RANGE
    # --------------------------------------------------------

    range_match = re.search(
        (
            r"(-?\d+(?:\.\d+)?)"
            r"\s*-\s*"
            r"(-?\d+(?:\.\d+)?)"
        ),
        text,
    )

    if range_match is not None:

        try:
            low = float(
                range_match.group(
                    1
                )
            )

            high = float(
                range_match.group(
                    2
                )
            )

            return (
                low,
                high,
            )

        except ValueError:
            return None, None

    # --------------------------------------------------------
    # UPPER LIMIT
    # --------------------------------------------------------

    upper_match = re.search(
        (
            r"(?:<=|≤|<)"
            r"\s*"
            r"(-?\d+(?:\.\d+)?)"
        ),
        text,
    )

    if upper_match is not None:

        try:
            return (
                None,
                float(
                    upper_match.group(
                        1
                    )
                ),
            )

        except ValueError:
            return None, None

    # --------------------------------------------------------
    # LOWER LIMIT
    # --------------------------------------------------------

    lower_match = re.search(
        (
            r"(?:>=|≥|>)"
            r"\s*"
            r"(-?\d+(?:\.\d+)?)"
        ),
        text,
    )

    if lower_match is not None:

        try:
            return (
                float(
                    lower_match.group(
                        1
                    )
                ),
                None,
            )

        except ValueError:
            return None, None

    return None, None


# ============================================================
# CSV READING
# ============================================================


def read_csv_with_fallback(
    content: bytes,
) -> pd.DataFrame:
    """
    Читает CSV с поддержкой типичных
    кодировок и разделителей.

    Кодировки:
    - UTF-8 BOM
    - UTF-8
    - Windows-1251
    - Latin-1

    Разделители:
    - ,
    - ;
    - TAB
    """

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1251",
        "latin1",
    ]

    separators = [
        ",",
        ";",
        "\t",
    ]

    last_error = None

    for encoding in encodings:

        # Сначала проверяем,
        # декодируется ли файл.
        try:
            content.decode(
                encoding
            )

        except UnicodeDecodeError as error:
            last_error = error
            continue

        for separator in separators:

            try:
                dataframe = pd.read_csv(
                    io.BytesIO(
                        content
                    ),
                    encoding=encoding,
                    sep=separator,
                )

                # Если всё прочиталось как
                # одна колонка, вероятнее всего
                # разделитель выбран неверно.
                if len(
                    dataframe.columns
                ) <= 1:
                    continue

                return dataframe

            except (
                UnicodeDecodeError,
                pd.errors.ParserError,
            ) as error:

                last_error = error
                continue

            except Exception as error:

                last_error = error
                continue

    raise LabFileParsingError(
        (
            "Failed to read CSV file. "
            "Supported encodings include "
            "UTF-8 and Windows-1251."
        )
    ) from last_error


# ============================================================
# DATAFRAME LOADING
# ============================================================


def load_dataframe(
    filename: str,
    content: bytes,
) -> tuple[
    pd.DataFrame,
    str,
]:
    """
    Загружает CSV или XLSX.

    PDF обрабатывается отдельно
    в parse_lab_file().
    """

    suffix = Path(
        filename
    ).suffix.lower()

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    if suffix == ".csv":

        dataframe = (
            read_csv_with_fallback(
                content
            )
        )

        return (
            dataframe,
            "csv",
        )

    # --------------------------------------------------------
    # XLSX
    # --------------------------------------------------------

    if suffix == ".xlsx":

        try:
            dataframe = pd.read_excel(
                io.BytesIO(
                    content
                ),
                engine="openpyxl",
            )

        except Exception as error:
            raise LabFileParsingError(
                (
                    "Failed to read "
                    "XLSX laboratory file"
                )
            ) from error

        return (
            dataframe,
            "xlsx",
        )

    raise UnsupportedFileFormatError(
        (
            "Supported file formats: "
            "CSV, XLSX, PDF"
        )
    )


# ============================================================
# COLUMN ALIASES
# ============================================================


NAME_COLUMN_ALIASES = {
    "показатель",
    "показатели",
    "анализ",
    "наименование",
    "наименование показателя",
    "исследование",
    "parameter",
    "test",
    "analyte",
    "name",
}


VALUE_COLUMN_ALIASES = {
    "значение",
    "результат",
    "результаты",
    "value",
    "result",
}


UNIT_COLUMN_ALIASES = {
    "ед",
    "ед.",
    "единица",
    "единицы",
    "единицы измерения",
    "ед. изм.",
    "unit",
    "units",
}


REFERENCE_COLUMN_ALIASES = {
    "референс",
    "референсные значения",
    "референсный интервал",
    "референсный диапазон",
    "норма",
    "нормальные значения",
    "reference",
    "reference range",
    "range",
}


# ============================================================
# COLUMN SEARCH
# ============================================================


def find_column(
    dataframe: pd.DataFrame,
    aliases: set[str],
) -> str | None:
    """
    Находит колонку таблицы
    по известным названиям.
    """

    normalized_aliases = {
        normalize_name(
            alias
        )
        for alias in aliases
    }

    for column in dataframe.columns:

        normalized_column = (
            normalize_name(
                column
            )
        )

        if (
            normalized_column
            in normalized_aliases
        ):
            return column

    return None


# ============================================================
# LONG FORMAT
# ============================================================


def parse_long_format(
    dataframe: pd.DataFrame,
) -> dict | None:
    """
    Обрабатывает таблицу вида:

    Показатель | Значение | Ед. | Референс
    """

    name_column = find_column(
        dataframe,
        NAME_COLUMN_ALIASES,
    )

    value_column = find_column(
        dataframe,
        VALUE_COLUMN_ALIASES,
    )

    # Если нет колонок Показатель + Значение,
    # это не long format.
    if (
        name_column is None
        or value_column is None
    ):
        return None

    unit_column = find_column(
        dataframe,
        UNIT_COLUMN_ALIASES,
    )

    reference_column = find_column(
        dataframe,
        REFERENCE_COLUMN_ALIASES,
    )

    features = {}

    metadata = {}

    unrecognized = []

    warnings = []

    # --------------------------------------------------------
    # ROWS
    # --------------------------------------------------------

    for _, row in dataframe.iterrows():

        raw_name = row.get(
            name_column
        )

        if raw_name is None:
            continue

        try:
            if pd.isna(
                raw_name
            ):
                continue

        except (
            TypeError,
            ValueError,
        ):
            pass

        normalized_name = (
            normalize_name(
                raw_name
            )
        )

        canonical = (
            ALIAS_LOOKUP.get(
                normalized_name
            )
        )

        raw_value = row.get(
            value_column
        )

        # ----------------------------------------------------
        # UNKNOWN FEATURE
        # ----------------------------------------------------

        if canonical is None:

            displayed_value = None

            if raw_value is not None:

                try:
                    if not pd.isna(
                        raw_value
                    ):
                        displayed_value = str(
                            raw_value
                        )

                except (
                    TypeError,
                    ValueError,
                ):
                    displayed_value = str(
                        raw_value
                    )

            unrecognized.append(
                {
                    "name": str(
                        raw_name
                    ),
                    "value": (
                        displayed_value
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # VALUE
        # ----------------------------------------------------

        if canonical == "sex":

            value = normalize_sex(
                raw_value
            )

            if value is None:

                warnings.append(
                    (
                        "Could not recognize "
                        "sex value"
                    )
                )

                continue

        else:

            value = parse_number(
                raw_value
            )

            if value is None:

                warnings.append(
                    (
                        "Could not parse value "
                        f"for {canonical}"
                    )
                )

                continue

        features[
            canonical
        ] = value

        # ----------------------------------------------------
        # UNIT
        # ----------------------------------------------------

        unit = None

        if unit_column is not None:

            raw_unit = row.get(
                unit_column
            )

            if raw_unit is not None:

                try:
                    unit_missing = pd.isna(
                        raw_unit
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    unit_missing = False

                if not unit_missing:

                    unit = str(
                        raw_unit
                    ).strip()

        # ----------------------------------------------------
        # REFERENCE
        # ----------------------------------------------------

        reference_low = None

        reference_high = None

        reference_text = None

        if reference_column is not None:

            raw_reference = row.get(
                reference_column
            )

            if raw_reference is not None:

                try:
                    reference_missing = (
                        pd.isna(
                            raw_reference
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    reference_missing = False

                if not reference_missing:

                    reference_text = str(
                        raw_reference
                    ).strip()

                    (
                        reference_low,
                        reference_high,
                    ) = parse_reference(
                        raw_reference
                    )

        # Пол и возраст не являются
        # лабораторными показателями.
        if canonical not in {
            "sex",
            "age_years",
        }:

            metadata[
                canonical
            ] = {
                "unit": unit,

                "reference_low": (
                    reference_low
                ),

                "reference_high": (
                    reference_high
                ),

                "reference_text": (
                    reference_text
                ),
            }

    return {
        "features": features,

        "metadata": metadata,

        "unrecognized": (
            unrecognized
        ),

        "warnings": warnings,
    }


# ============================================================
# WIDE FORMAT
# ============================================================


def parse_wide_format(
    dataframe: pd.DataFrame,
) -> dict:
    """
    Обрабатывает таблицу вида:

    sex | hemoglobin | ferritin | TIBC | ...
    F   | 108        | 8        | 82   | ...

    Для пациентского импорта пока используется
    первая строка.
    """

    features = {}

    metadata = {}

    unrecognized = []

    warnings = []

    # --------------------------------------------------------
    # EMPTY FILE
    # --------------------------------------------------------

    if dataframe.empty:

        return {
            "features": {},

            "metadata": {},

            "unrecognized": [],

            "warnings": [
                (
                    "The file contains "
                    "no data"
                )
            ],
        }

    # --------------------------------------------------------
    # FIRST PATIENT
    # --------------------------------------------------------

    row = dataframe.iloc[
        0
    ]

    if len(
        dataframe
    ) > 1:

        warnings.append(
            (
                "The file contains multiple rows. "
                "Only the first row was imported."
            )
        )

    # --------------------------------------------------------
    # COLUMNS
    # --------------------------------------------------------

    for column in dataframe.columns:

        normalized_column = (
            normalize_name(
                column
            )
        )

        canonical = (
            ALIAS_LOOKUP.get(
                normalized_column
            )
        )

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
        # UNKNOWN COLUMN
        # ----------------------------------------------------

        if canonical is None:

            unrecognized.append(
                {
                    "name": str(
                        column
                    ),
                    "value": str(
                        raw_value
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # VALUE
        # ----------------------------------------------------

        if canonical == "sex":

            value = normalize_sex(
                raw_value
            )

        else:

            value = parse_number(
                raw_value
            )

        if value is None:

            warnings.append(
                (
                    "Could not parse value "
                    f"for {canonical}"
                )
            )

            continue

        features[
            canonical
        ] = value

    return {
        "features": features,

        "metadata": metadata,

        "unrecognized": (
            unrecognized
        ),

        "warnings": warnings,
    }


# ============================================================
# MAIN PARSER
# ============================================================


def parse_lab_file(
    filename: str,
    content: bytes,
) -> dict:
    """
    Главная функция импорта лабораторного файла.

    Поддерживает:

    - CSV
    - XLSX
    - PDF с текстовым слоем

    Возвращает:

    {
        "features": ...,
        "metadata": ...,
        "unrecognized": ...,
        "warnings": ...,
        "format": ...
    }

    ML здесь НЕ запускается.
    """

    suffix = Path(
        filename
    ).suffix.lower()

    # ========================================================
    # PDF
    # ========================================================

    if suffix == ".pdf":

        # Импорт выполняем здесь,
        # а не наверху файла,
        # чтобы избежать циклического импорта:
        #
        # file_parser_service
        #       ↕
        # pdf_lab_parser_service

        from api.services.pdf_lab_parser_service import (
            parse_pdf_lab_file,
        )

        parsed = (
            parse_pdf_lab_file(
                content
            )
        )

        parsed[
            "format"
        ] = "pdf"

        return parsed

    # ========================================================
    # CSV / XLSX
    # ========================================================

    dataframe, file_format = (
        load_dataframe(
            filename,
            content,
        )
    )

    # Сначала пытаемся разобрать формат:
    #
    # Показатель | Значение | Ед. | Референс

    parsed = parse_long_format(
        dataframe
    )

    # Если соответствующие колонки
    # не найдены, пробуем wide format:
    #
    # sex | hemoglobin | ferritin | ...
    # F   | 108        | 8        | ...

    if parsed is None:

        parsed = parse_wide_format(
            dataframe
        )

    parsed[
        "format"
    ] = file_format

    return parsed