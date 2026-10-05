import io

from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database.models import (
    LabValue,
    PatientProfile,
    Screening,
    User,
)


# ============================================================
# EXCEPTIONS
# ============================================================


class ReportGenerationError(
    RuntimeError
):
    pass


class ReportScreeningNotFoundError(
    ValueError
):
    pass


class PatientRoleRequiredError(
    ValueError
):
    pass


# ============================================================
# CONSTANTS
# ============================================================


REPORT_FONT_NAME = (
    "MeditronDejaVu"
)


FONT_CANDIDATES = [
    Path(
        "/usr/share/fonts/truetype/"
        "dejavu/DejaVuSans.ttf"
    ),
    Path(
        "/usr/share/fonts/dejavu/"
        "DejaVuSans.ttf"
    ),
]


TARGET_LABELS = {
    "iron_deficiency": (
        "Дефицит железа"
    ),
    "B12_deficiency": (
        "Дефицит витамина B12"
    ),
    "folate_deficiency": (
        "Дефицит фолатов"
    ),
    "B6_deficiency": (
        "Дефицит витамина B6"
    ),
    "copper_deficiency": (
        "Дефицит меди"
    ),
    "inflammation_anemia": (
        "Анемия воспаления"
    ),
}


KEY_LABELS = {
    "prediction": "Результат скрининга",
    "confidence": "Уверенность",
    "probability": "Вероятность",
    "risk": "Риск",
    "risk_level": "Уровень риска",
    "label": "Результат",
    "state": "Состояние",
    "status": "Статус",
    "coverage": "Полнота данных",
    "feature": "Показатель",
    "value": "Значение",
    "reason": "Причина",
    "message": "Описание",
    "test": "Исследование",
    "priority": "Приоритет",
    "name": "Название",
}


# ============================================================
# FONT
# ============================================================


def register_report_font() -> str:
    """
    Регистрирует Unicode-шрифт
    для русского текста.
    """

    if (
        REPORT_FONT_NAME
        in pdfmetrics.getRegisteredFontNames()
    ):
        return REPORT_FONT_NAME

    font_path = None

    for candidate in FONT_CANDIDATES:

        if candidate.exists():

            font_path = candidate

            break

    if font_path is None:

        raise ReportGenerationError(
            (
                "DejaVuSans.ttf was not found. "
                "Install DejaVu Sans fonts."
            )
        )

    pdfmetrics.registerFont(
        TTFont(
            REPORT_FONT_NAME,
            str(
                font_path
            ),
        )
    )

    return REPORT_FONT_NAME


# ============================================================
# ACCESS
# ============================================================


def get_patient_screening_for_report(
    db: Session,
    *,
    user: User,
    screening_id: str,
) -> Screening:
    """
    Возвращает screening только
    текущего пациента.
    """

    if user.role != "patient":

        raise PatientRoleRequiredError(
            "Patient account required"
        )

    patient_profile = db.scalar(
        select(
            PatientProfile
        ).where(
            PatientProfile.user_id
            == user.id
        )
    )

    if patient_profile is None:

        raise ReportScreeningNotFoundError(
            "Screening not found"
        )

    screening = db.scalar(
        select(
            Screening
        ).where(
            Screening.id
            == screening_id,

            Screening.patient_profile_id
            == patient_profile.id,
        )
    )

    if screening is None:

        raise ReportScreeningNotFoundError(
            "Screening not found"
        )

    return screening


def get_screening_lab_values(
    db: Session,
    *,
    screening_id: str,
) -> list[LabValue]:
    """
    Все лабораторные значения
    конкретного screening.
    """

    statement = (
        select(
            LabValue
        )
        .where(
            LabValue.screening_id
            == screening_id
        )
        .order_by(
            LabValue.feature.asc()
        )
    )

    return list(
        db.scalars(
            statement
        ).all()
    )


# ============================================================
# FORMAT HELPERS
# ============================================================


def format_datetime(
    value,
) -> str:

    if not isinstance(
        value,
        datetime,
    ):
        return "-"

    return value.strftime(
        "%d.%m.%Y %H:%M"
    )


def format_number(
    value,
) -> str:

    if value is None:
        return "-"

    if isinstance(
        value,
        float,
    ):

        return (
            f"{value:.4f}"
            .rstrip("0")
            .rstrip(".")
        )

    return str(
        value
    )


def format_reference(
    lab_value: LabValue,
) -> str:

    low = (
        lab_value.reference_low
    )

    high = (
        lab_value.reference_high
    )

    if (
        low is not None
        and high is not None
    ):

        return (
            f"{format_number(low)}"
            " - "
            f"{format_number(high)}"
        )

    if low is not None:

        return (
            ">= "
            f"{format_number(low)}"
        )

    if high is not None:

        return (
            "<= "
            f"{format_number(high)}"
        )

    return "-"


def humanize_key(
    key: str,
) -> str:

    if key in TARGET_LABELS:

        return TARGET_LABELS[
            key
        ]

    if key in KEY_LABELS:

        return KEY_LABELS[
            key
        ]

    text = (
        str(
            key
        )
        .replace(
            "_",
            " ",
        )
        .strip()
    )

    if not text:
        return "-"

    return (
        text[0].upper()
        + text[1:]
    )


def format_scalar(
    value,
) -> str:

    if value is None:
        return "-"

    if isinstance(
        value,
        bool,
    ):

        return (
            "Да"
            if value
            else "Нет"
        )

    if isinstance(
        value,
        float,
    ):

        # Часто probabilities приходят
        # как 0..1. Здесь ничего не
        # преобразуем, чтобы не менять
        # смысл ответа модели.
        return format_number(
            value
        )

    return str(
        value
    )


def safe_text(
    value,
) -> str:

    return escape(
        format_scalar(
            value
        )
    )


# ============================================================
# GENERIC DICT TABLE
# ============================================================


def mapping_table(
    data: dict,
    *,
    font_name: str,
    max_rows: int = 50,
):
    """
    Отображает простые key/value поля dict.

    Вложенные dict/list здесь пропускаются
    и выводятся отдельными секциями.
    """

    rows = []

    for key, value in data.items():

        if isinstance(
            value,
            (
                dict,
                list,
            ),
        ):
            continue

        rows.append([
            Paragraph(
                escape(
                    humanize_key(
                        key
                    )
                ),
                ParagraphStyle(
                    name=(
                        "MapKey"
                    ),
                    fontName=(
                        font_name
                    ),
                    fontSize=9,
                    leading=12,
                ),
            ),

            Paragraph(
                safe_text(
                    value
                ),
                ParagraphStyle(
                    name=(
                        "MapValue"
                    ),
                    fontName=(
                        font_name
                    ),
                    fontSize=9,
                    leading=12,
                ),
            ),
        ])

        if len(
            rows
        ) >= max_rows:

            break

    if not rows:
        return None

    table = Table(
        rows,
        colWidths=[
            60 * mm,
            110 * mm,
        ],
    )

    table.setStyle(
        TableStyle([
            (
                "FONTNAME",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                font_name,
            ),
            (
                "VALIGN",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                "TOP",
            ),
            (
                "GRID",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                0.3,
                colors.HexColor(
                    "#D8DEE6"
                ),
            ),
            (
                "BACKGROUND",
                (
                    0,
                    0,
                ),
                (
                    0,
                    -1,
                ),
                colors.HexColor(
                    "#F3F6F9"
                ),
            ),
            (
                "LEFTPADDING",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                6,
            ),
            (
                "RIGHTPADDING",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                6,
            ),
            (
                "TOPPADDING",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                5,
            ),
            (
                "BOTTOMPADDING",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                5,
            ),
        ])
    )

    return table


# ============================================================
# LAB TABLE
# ============================================================


def build_lab_table(
    lab_values: list[LabValue],
    *,
    font_name: str,
):
    """
    Таблица исходных лабораторных
    показателей.
    """

    cell_style = ParagraphStyle(
        name="LabCell",
        fontName=font_name,
        fontSize=8,
        leading=10,
    )

    header_style = ParagraphStyle(
        name="LabHeader",
        fontName=font_name,
        fontSize=8,
        leading=10,
    )

    data = [[
        Paragraph(
            "Показатель",
            header_style,
        ),
        Paragraph(
            "Значение",
            header_style,
        ),
        Paragraph(
            "Ед.",
            header_style,
        ),
        Paragraph(
            "Референс",
            header_style,
        ),
    ]]

    for item in lab_values:

        data.append([
            Paragraph(
                escape(
                    humanize_key(
                        item.feature
                    )
                ),
                cell_style,
            ),

            Paragraph(
                escape(
                    format_number(
                        item.value
                    )
                ),
                cell_style,
            ),

            Paragraph(
                escape(
                    item.unit
                    or "-"
                ),
                cell_style,
            ),

            Paragraph(
                escape(
                    format_reference(
                        item
                    )
                ),
                cell_style,
            ),
        ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            70 * mm,
            32 * mm,
            32 * mm,
            40 * mm,
        ],
    )

    table.setStyle(
        TableStyle([
            (
                "FONTNAME",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                font_name,
            ),
            (
                "BACKGROUND",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    0,
                ),
                colors.HexColor(
                    "#EAF0F6"
                ),
            ),
            (
                "GRID",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                0.3,
                colors.HexColor(
                    "#D0D7DF"
                ),
            ),
            (
                "VALIGN",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                "MIDDLE",
            ),
            (
                "LEFTPADDING",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                5,
            ),
            (
                "RIGHTPADDING",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                5,
            ),
            (
                "TOPPADDING",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                5,
            ),
            (
                "BOTTOMPADDING",
                (
                    0,
                    0,
                ),
                (
                    -1,
                    -1,
                ),
                5,
            ),
        ])
    )

    return table


# ============================================================
# LIST SECTION
# ============================================================


def add_list_section(
    story: list,
    *,
    title: str,
    items,
    heading_style,
    body_style,
    font_name: str,
) -> None:

    if not items:
        return

    story.append(
        Paragraph(
            escape(
                title
            ),
            heading_style,
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    if not isinstance(
        items,
        list,
    ):
        items = [
            items
        ]

    for index, item in enumerate(
        items,
        start=1,
    ):

        if isinstance(
            item,
            dict,
        ):

            elements = [
                Paragraph(
                    f"{index}.",
                    body_style,
                )
            ]

            table = mapping_table(
                item,
                font_name=(
                    font_name
                ),
            )

            if table is not None:

                elements.append(
                    Spacer(
                        1,
                        1 * mm,
                    )
                )

                elements.append(
                    table
                )

            story.append(
                KeepTogether(
                    elements
                )
            )

        else:

            story.append(
                Paragraph(
                    (
                        f"{index}. "
                        f"{safe_text(item)}"
                    ),
                    body_style,
                )
            )

        story.append(
            Spacer(
                1,
                2 * mm,
            )
        )


# ============================================================
# PDF
# ============================================================


def build_screening_report_pdf(
    *,
    screening: Screening,
    lab_values: list[LabValue],
    patient_code: str | None = None,
) -> bytes:
    """
    Создаёт PDF из уже сохранённого
    результата screening.

    ML здесь НЕ запускается.
    """

    font_name = (
        register_report_font()
    )

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,

        pagesize=A4,

        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,

        title=(
            "Meditron screening report"
        ),

        author="Meditron",
    )

    base_styles = (
        getSampleStyleSheet()
    )

    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=base_styles[
            "Title"
        ],
        fontName=font_name,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor(
            "#1E3557"
        ),
        spaceAfter=5 * mm,
    )

    heading_style = ParagraphStyle(
        name="ReportHeading",
        parent=base_styles[
            "Heading2"
        ],
        fontName=font_name,
        fontSize=12,
        leading=15,
        textColor=colors.HexColor(
            "#1E3557"
        ),
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )

    body_style = ParagraphStyle(
        name="ReportBody",
        parent=base_styles[
            "BodyText"
        ],
        fontName=font_name,
        fontSize=9,
        leading=13,
    )

    small_style = ParagraphStyle(
        name="ReportSmall",
        parent=body_style,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor(
            "#555555"
        ),
    )

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            (
                "Отчёт ИИ-скрининга "
                "латентных дефицитных состояний"
            ),
            title_style,
        )
    )

    story.append(
        Paragraph(
            (
                "Meditron"
            ),
            small_style,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # ========================================================
    # METADATA
    # ========================================================

    metadata = {
        "ID исследования": (
            screening.id
        ),

        "Дата": (
            format_datetime(
                screening.created_at
            )
        ),

        "Источник данных": (
            screening.source_type
            or "-"
        ),

        "Файл": (
            screening.source_filename
            or "-"
        ),
    }

    if patient_code:

        metadata[
            "Код пациента"
        ] = patient_code

    metadata_table = (
        mapping_table(
            metadata,
            font_name=font_name,
        )
    )

    if metadata_table is not None:

        story.append(
            metadata_table
        )

    # ========================================================
    # DATA QUALITY
    # ========================================================

    story.append(
        Paragraph(
            "Качество входных данных",
            heading_style,
        )
    )

    coverage = (
        screening.coverage
    )

    coverage_text = (
        "-"
        if coverage is None
        else format_number(
            coverage
        )
    )

    story.append(
        Paragraph(
            (
                "Полнота данных: "
                f"{escape(coverage_text)}"
            ),
            body_style,
        )
    )

    # ========================================================
    # LAB VALUES
    # ========================================================

    if lab_values:

        story.append(
            Paragraph(
                "Лабораторные показатели",
                heading_style,
            )
        )

        story.append(
            build_lab_table(
                lab_values,
                font_name=font_name,
            )
        )

    # ========================================================
    # RESULT DATA
    # ========================================================

    result_data = (
        screening.result_data
        or {}
    )

    if not isinstance(
        result_data,
        dict,
    ):

        result_data = {}

    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    prediction = (
        result_data.get(
            "prediction"
        )
    )

    if isinstance(
        prediction,
        dict,
    ):

        story.append(
            Paragraph(
                "Результат скрининга",
                heading_style,
            )
        )

        prediction_table = (
            mapping_table(
                prediction,
                font_name=font_name,
            )
        )

        if prediction_table is not None:

            story.append(
                prediction_table
            )

    # --------------------------------------------------------
    # DEFICIENCIES
    # --------------------------------------------------------

    add_list_section(
        story,

        title=(
            "Оценка дефицитных состояний"
        ),

        items=(
            result_data.get(
                "deficiencies"
            )
        ),

        heading_style=(
            heading_style
        ),

        body_style=(
            body_style
        ),

        font_name=(
            font_name
        ),
    )

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    add_list_section(
        story,

        title="Основания результата",

        items=(
            result_data.get(
                "evidence"
            )
        ),

        heading_style=(
            heading_style
        ),

        body_style=(
            body_style
        ),

        font_name=(
            font_name
        ),
    )

    # --------------------------------------------------------
    # CONFLICTS
    # --------------------------------------------------------

    add_list_section(
        story,

        title=(
            "Противоречивые данные"
        ),

        items=(
            result_data.get(
                "conflicts"
            )
        ),

        heading_style=(
            heading_style
        ),

        body_style=(
            body_style
        ),

        font_name=(
            font_name
        ),
    )

    # --------------------------------------------------------
    # RECOMMENDED TESTS
    # --------------------------------------------------------

    add_list_section(
        story,

        title=(
            "Рекомендуемые дополнительные "
            "исследования"
        ),

        items=(
            result_data.get(
                "recommended_next_tests"
            )
        ),

        heading_style=(
            heading_style
        ),

        body_style=(
            body_style
        ),

        font_name=(
            font_name
        ),
    )

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model_info = (
        result_data.get(
            "model"
        )
    )

    if isinstance(
        model_info,
        dict,
    ):

        story.append(
            Paragraph(
                "Информация о модели",
                heading_style,
            )
        )

        model_table = (
            mapping_table(
                model_info,
                font_name=font_name,
            )
        )

        if model_table is not None:

            story.append(
                model_table
            )

    # ========================================================
    # DISCLAIMER
    # ========================================================

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            "Важно",
            heading_style,
        )
    )

    disclaimer = (
        result_data.get(
            "disclaimer"
        )
    )

    if not disclaimer:

        disclaimer = (
            "Результат является инструментом "
            "скрининга и не является медицинским "
            "диагнозом. Интерпретация результатов "
            "должна выполняться медицинским "
            "специалистом с учётом клинической "
            "картины и других данных."
        )

    story.append(
        Paragraph(
            escape(
                str(
                    disclaimer
                )
            ),
            body_style,
        )
    )

    # ========================================================
    # BUILD
    # ========================================================

    try:

        document.build(
            story
        )

    except Exception as error:

        raise ReportGenerationError(
            "Failed to generate PDF report"
        ) from error

    pdf_bytes = (
        buffer.getvalue()
    )

    buffer.close()

    if not pdf_bytes.startswith(
        b"%PDF"
    ):

        raise ReportGenerationError(
            "Generated document is not a PDF"
        )

    return pdf_bytes