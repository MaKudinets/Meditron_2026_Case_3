import io
import re

from pypdf import PdfReader

from api.services.file_parser_service import (
    ALIAS_LOOKUP,
    LabFileParsingError,
    normalize_name,
    parse_number,
    parse_reference,
)


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================


def extract_pdf_text(
    content: bytes,
) -> str:
    """
    Извлекает текст из PDF с текстовым слоем.

    Для отсканированных PDF без текста
    возвращаем понятную ошибку.
    """

    try:
        reader = PdfReader(
            io.BytesIO(content)
        )

    except Exception as error:
        raise LabFileParsingError(
            "Failed to open PDF file"
        ) from error

    pages = []

    for page in reader.pages:

        try:
            text = (
                page.extract_text()
                or ""
            )

        except Exception:
            text = ""

        if text.strip():
            pages.append(
                text
            )

    full_text = "\n".join(
        pages
    ).strip()

    if not full_text:
        raise LabFileParsingError(
            (
                "No selectable text was found in the PDF. "
                "The document may be scanned and require OCR."
            )
        )

    return full_text


# ============================================================
# ALIAS PREPARATION
# ============================================================


def build_pdf_aliases():
    """
    Формирует список:

    [
        ("общая железосвязывающая способность", "TIBC"),
        ("ферритин", "ferritin"),
        ...
    ]

    Более длинные названия идут первыми.
    """

    aliases = []

    for alias, canonical in (
        ALIAS_LOOKUP.items()
    ):

        aliases.append(
            (
                normalize_name(
                    alias
                ),
                canonical,
            )
        )

    aliases.sort(
        key=lambda item: len(
            item[0]
        ),
        reverse=True,
    )

    return aliases


PDF_ALIASES = (
    build_pdf_aliases()
)


# ============================================================
# LINE CLEANUP
# ============================================================


def clean_pdf_line(
    line: str,
) -> str:
    """
    Нормализует строку PDF,
    не удаляя числовые данные.
    """

    line = str(
        line
    )

    line = line.replace(
        "\u00a0",
        " ",
    )

    line = line.replace(
        "\t",
        " ",
    )

    line = re.sub(
        r"\s+",
        " ",
        line,
    )

    return line.strip()


# ============================================================
# FEATURE SEARCH
# ============================================================


def find_feature_in_line(
    line: str,
) -> tuple[
    str | None,
    str | None,
]:
    """
    Пытается определить лабораторный показатель
    по тексту строки.

    Возвращает:
        canonical feature
        найденный alias
    """

    normalized_line = normalize_name(
        line
    )

    for alias, canonical in PDF_ALIASES:

        # Предпочитаем ситуацию,
        # когда название показателя находится
        # в начале строки.

        if (
            normalized_line == alias
            or normalized_line.startswith(
                alias + " "
            )
            or normalized_line.startswith(
                alias + ":"
            )
        ):
            return (
                canonical,
                alias,
            )

    return (
        None,
        None,
    )


# ============================================================
# VALUE EXTRACTION
# ============================================================


def remove_feature_name(
    line: str,
    alias: str,
) -> str:
    """
    Удаляет название показателя,
    чтобы оставшийся текст было проще разобрать.

    Например:

    Ферритин 8 нг/мл 15-150

        ↓

    8 нг/мл 15-150
    """

    normalized = normalize_name(
        line
    )

    if normalized.startswith(
        alias
    ):
        # Здесь len(alias) безопасен для
        # большинства лабораторных строк,
        # потому что normalize_name не меняет
        # длину латинских/кириллических букв
        # кроме пробелов.
        remainder = line[
            len(alias):
        ]

        return remainder.strip(
            " :-"
        )

    return line


def extract_first_number(
    text: str,
) -> tuple[
    float | None,
    str,
]:
    """
    Берёт первое число как значение анализа
    и возвращает оставшуюся часть строки.
    """

    normalized = str(
        text
    ).replace(
        ",",
        ".",
    )

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        normalized,
    )

    if match is None:
        return (
            None,
            text,
        )

    try:
        value = float(
            match.group()
        )

    except ValueError:
        return (
            None,
            text,
        )

    remainder = (
        normalized[
            match.end():
        ]
        .strip()
    )

    return (
        value,
        remainder,
    )


# ============================================================
# UNIT / REFERENCE
# ============================================================


def extract_reference_text(
    text: str,
) -> str | None:
    """
    Ищет типичные референсные диапазоны:

    15-150
    15 - 150
    15–150
    < 10
    > 20
    """

    range_match = re.search(
        (
            r"-?\d+(?:[.,]\d+)?"
            r"\s*[-–—]\s*"
            r"-?\d+(?:[.,]\d+)?"
        ),
        text,
    )

    if range_match is not None:
        return (
            range_match.group()
            .strip()
        )

    one_sided_match = re.search(
        (
            r"(?:<=|>=|<|>|≤|≥)"
            r"\s*"
            r"-?\d+(?:[.,]\d+)?"
        ),
        text,
    )

    if one_sided_match is not None:
        return (
            one_sided_match.group()
            .strip()
        )

    return None


def extract_unit(
    text: str,
    reference_text: str | None,
) -> str | None:
    """
    Из оставшейся строки пытается получить
    единицу измерения.

    Например:

    нг/мл 15-150

        ↓

    нг/мл
    """

    unit_text = str(
        text
    ).strip()

    if reference_text:

        unit_text = unit_text.replace(
            reference_text,
            "",
            1,
        ).strip()

    unit_text = unit_text.strip(
        " ;:,()"
    )

    # Защита от слишком большого куска текста,
    # если PDF разобрал строку нестандартно.
    if len(unit_text) > 40:
        return None

    if not unit_text:
        return None

    return unit_text


# ============================================================
# PARSE ONE LINE
# ============================================================


def parse_pdf_lab_line(
    line: str,
) -> dict | None:
    """
    Разбирает строку вида:

    Ферритин 8 нг/мл 15-150
    """

    line = clean_pdf_line(
        line
    )

    if not line:
        return None

    (
        feature,
        alias,
    ) = find_feature_in_line(
        line
    )

    if feature is None:
        return None

    remainder = remove_feature_name(
        line,
        alias,
    )

    # sex обрабатывается отдельно.
    if feature == "sex":

        normalized = normalize_name(
            remainder
        )

        female_values = {
            "f",
            "female",
            "жен",
            "женский",
            "женщина",
            "ж",
        }

        male_values = {
            "m",
            "male",
            "муж",
            "мужской",
            "мужчина",
            "м",
        }

        if normalized in female_values:

            return {
                "feature": "sex",
                "value": "F",
                "unit": None,
                "reference_low": None,
                "reference_high": None,
                "reference_text": None,
            }

        if normalized in male_values:

            return {
                "feature": "sex",
                "value": "M",
                "unit": None,
                "reference_low": None,
                "reference_high": None,
                "reference_text": None,
            }

        return None

    (
        value,
        after_value,
    ) = extract_first_number(
        remainder
    )

    if value is None:
        return None

    reference_text = (
        extract_reference_text(
            after_value
        )
    )

    (
        reference_low,
        reference_high,
    ) = parse_reference(
        reference_text
    )

    unit = extract_unit(
        after_value,
        reference_text,
    )

    return {
        "feature": feature,

        "value": value,

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


# ============================================================
# PDF TEXT PARSER
# ============================================================


def parse_pdf_text(
    text: str,
) -> dict:
    """
    Разбирает уже извлечённый текст PDF.
    """

    features = {}

    metadata = {}

    warnings = []

    unrecognized = []

    lines = text.splitlines()

    for raw_line in lines:

        line = clean_pdf_line(
            raw_line
        )

        if not line:
            continue

        parsed = parse_pdf_lab_line(
            line
        )

        if parsed is None:
            continue

        feature = parsed[
            "feature"
        ]

        value = parsed[
            "value"
        ]

        # Если один показатель встретился
        # несколько раз, сохраняем последнее
        # распознанное значение и сообщаем об этом.
        if feature in features:

            warnings.append(
                (
                    "Multiple values were found "
                    f"for {feature}. "
                    "The last recognized value was used."
                )
            )

        features[
            feature
        ] = value

        if feature not in {
            "sex",
            "age_years",
        }:

            metadata[
                feature
            ] = {
                "unit": parsed[
                    "unit"
                ],

                "reference_low": parsed[
                    "reference_low"
                ],

                "reference_high": parsed[
                    "reference_high"
                ],

                "reference_text": parsed[
                    "reference_text"
                ],
            }

    if not features:

        warnings.append(
            (
                "PDF text was extracted, but no supported "
                "laboratory indicators were recognized."
            )
        )

    return {
        "features": features,

        "metadata": metadata,

        "unrecognized": unrecognized,

        "warnings": warnings,
    }


# ============================================================
# MAIN PDF PARSER
# ============================================================


def parse_pdf_lab_file(
    content: bytes,
) -> dict:
    """
    Полный цикл:

    PDF bytes
        ↓
    text
        ↓
    supported laboratory values
    """

    text = extract_pdf_text(
        content
    )

    return parse_pdf_text(
        text
    )