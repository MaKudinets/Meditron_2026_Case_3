from api.services.file_parser_service import (
    parse_lab_file,
)

from api.services.pdf_lab_parser_service import (
    parse_pdf_text,
)


def test_parse_pdf_lab_text():

    text = """
Гемоглобин 108 г/л 120-150
MCV 74 фл 80-100
MCH 23 пг 27-34
Ферритин 8 нг/мл 15-150
Железо 7.5 мкмоль/л 9-30
ОЖСС 82 мкмоль/л 45-72
TSAT 10 % 20-45
"""

    result = parse_pdf_text(
        text
    )

    assert (
        result["features"][
            "hemoglobin"
        ]
        == 108
    )

    assert (
        result["features"][
            "ferritin"
        ]
        == 8
    )

    assert (
        result["features"][
            "serum_iron"
        ]
        == 7.5
    )

    assert (
        result["features"][
            "TIBC"
        ]
        == 82
    )

    assert (
        result["features"][
            "TSAT"
        ]
        == 10
    )

    assert (
        result["metadata"][
            "ferritin"
        ][
            "unit"
        ]
        == "нг/мл"
    )

    assert (
        result["metadata"][
            "ferritin"
        ][
            "reference_low"
        ]
        == 15
    )

    assert (
        result["metadata"][
            "ferritin"
        ][
            "reference_high"
        ]
        == 150
    )
def test_parse_lab_csv():

    csv_content = (
        "Показатель,Значение,Ед.,Референс\n"
        "Гемоглобин,108,г/л,120-150\n"
        "Ферритин,8,нг/мл,15-150\n"
        "Железо,7.5,мкмоль/л,9-30\n"
    ).encode(
        "utf-8"
    )

    result = parse_lab_file(
        "labs.csv",
        csv_content,
    )

    assert (
        result["features"][
            "hemoglobin"
        ]
        == 108
    )

    assert (
        result["features"][
            "ferritin"
        ]
        == 8
    )

    assert (
        result["features"][
            "serum_iron"
        ]
        == 7.5
    )

    assert (
        result["metadata"][
            "ferritin"
        ]["reference_low"]
        == 15
    )

    assert (
        result["metadata"][
            "ferritin"
        ]["reference_high"]
        == 150
    )