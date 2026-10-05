"""
Backend fallback catalog for laboratory metadata.

Правила:
- metadata из лабораторного файла всегда имеют приоритет;
- единицы измерения соответствуют существующему frontend-каталогу;
- референсные интервалы указаны только там, где они уже явно
  присутствуют в текущем проекте;
- диагностические пороги expert system не используются
  как лабораторные референсные интервалы.
"""


LAB_CATALOG = {
    # ========================================================
    # CBC
    # ========================================================

    "hemoglobin": {
        "unit": "г/л",
        "reference_low": 120.0,
        "reference_high": 150.0,
    },

    "RBC": {
        "unit": "10¹²/л",
        "reference_low": None,
        "reference_high": None,
    },

    "hematocrit": {
        "unit": "%",
        "reference_low": None,
        "reference_high": None,
    },

    "MCV": {
        "unit": "фл",
        "reference_low": 80.0,
        "reference_high": 100.0,
    },

    "MCH": {
        "unit": "пг",
        "reference_low": 27.0,
        "reference_high": 34.0,
    },

    "MCHC": {
        "unit": "г/л",
        "reference_low": None,
        "reference_high": None,
    },

    "RDW": {
        "unit": "%",
        "reference_low": None,
        "reference_high": None,
    },

    "platelets": {
        "unit": "10⁹/л",
        "reference_low": None,
        "reference_high": None,
    },

    "WBC": {
        "unit": "10⁹/л",
        "reference_low": None,
        "reference_high": None,
    },

    "reticulocytes": {
        "unit": "%",
        "reference_low": None,
        "reference_high": None,
    },

    # ========================================================
    # IRON
    # ========================================================

    "ferritin": {
        "unit": "нг/мл",
        "reference_low": 15.0,
        "reference_high": 150.0,
    },

    "serum_iron": {
        "unit": "мкмоль/л",
        "reference_low": 9.0,
        "reference_high": 30.0,
    },

    "transferrin": {
        "unit": "г/л",
        "reference_low": None,
        "reference_high": None,
    },

    "TIBC": {
        "unit": "мкмоль/л",
        "reference_low": 45.0,
        "reference_high": 72.0,
    },

    "UIBC": {
        "unit": "мкмоль/л",
        "reference_low": None,
        "reference_high": None,
    },

    "TSAT": {
        "unit": "%",
        "reference_low": 20.0,
        "reference_high": 45.0,
    },

    "sTfR": {
        "unit": None,
        "reference_low": None,
        "reference_high": None,
    },

    "Ret_He": {
        "unit": "пг",
        "reference_low": None,
        "reference_high": None,
    },

    # ========================================================
    # VITAMINS
    # ========================================================

    "vitamin_B12": {
        "unit": "пг/мл",
        "reference_low": None,
        "reference_high": None,
    },

    "active_B12": {
        "unit": None,
        "reference_low": None,
        "reference_high": None,
    },

    "MMA": {
        "unit": None,
        "reference_low": None,
        "reference_high": None,
    },

    "homocysteine": {
        "unit": "мкмоль/л",
        "reference_low": None,
        "reference_high": None,
    },

    "folate": {
        "unit": "нг/мл",
        "reference_low": None,
        "reference_high": None,
    },

    "vitamin_B6": {
        "unit": None,
        "reference_low": None,
        "reference_high": None,
    },

    # ========================================================
    # COPPER
    # ========================================================

    "copper": {
        "unit": None,
        "reference_low": None,
        "reference_high": None,
    },

    "ceruloplasmin": {
        "unit": None,
        "reference_low": None,
        "reference_high": None,
    },

    # ========================================================
    # INFLAMMATION
    # ========================================================

    "CRP": {
        "unit": "мг/л",
        "reference_low": None,
        "reference_high": None,
    },

    "ESR": {
        "unit": "мм/ч",
        "reference_low": None,
        "reference_high": None,
    },

    # ========================================================
    # RENAL / THYROID / GENERAL
    # ========================================================

    "creatinine": {
        "unit": "мкмоль/л",
        "reference_low": None,
        "reference_high": None,
    },

    "eGFR": {
        "unit": "мл/мин/1,73 м²",
        "reference_low": None,
        "reference_high": None,
    },

    "TSH": {
        "unit": "мМЕ/л",
        "reference_low": None,
        "reference_high": None,
    },

    "albumin": {
        "unit": "г/л",
        "reference_low": None,
        "reference_high": None,
    },

    # ========================================================
    # HEMOLYSIS
    # ========================================================

    "LDH": {
        "unit": "Ед/л",
        "reference_low": None,
        "reference_high": None,
    },

    "indirect_bilirubin": {
        "unit": "мкмоль/л",
        "reference_low": None,
        "reference_high": None,
    },

    "haptoglobin": {
        "unit": None,
        "reference_low": None,
        "reference_high": None,
    },
}


def get_lab_catalog_metadata(
    feature: str,
) -> dict:
    """
    Возвращает копию metadata для показателя.

    Копия нужна, чтобы вызывающий код
    случайно не изменил глобальный каталог.
    """

    return dict(
        LAB_CATALOG.get(
            feature,
            {},
        )
    )