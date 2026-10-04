LAB_GROUPS = {
    "cbc": {
        "label": "Общий анализ крови",

        "features": [
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
        ],
    },

    "iron": {
        "label": "Обмен железа",

        "features": [
            "ferritin",
            "serum_iron",
            "transferrin",
            "TIBC",
            "UIBC",
            "TSAT",
            "sTfR",
            "Ret_He",
        ],
    },

    "vitamins": {
        "label": "Витамины группы B",

        "features": [
            "vitamin_B12",
            "active_B12",
            "MMA",
            "homocysteine",
            "folate",
            "vitamin_B6",
        ],
    },

    "copper": {
        "label": "Обмен меди",

        "features": [
            "copper",
            "ceruloplasmin",
        ],
    },

    "inflammation": {
        "label": "Воспаление",

        "features": [
            "CRP",
            "ESR",
            "albumin",
        ],
    },

    "renal_thyroid": {
        "label": "Почки и щитовидная железа",

        "features": [
            "creatinine",
            "eGFR",
            "TSH",
        ],
    },

    "hemolysis": {
        "label": "Маркеры гемолиза",

        "features": [
            "LDH",
            "indirect_bilirubin",
            "haptoglobin",
        ],
    },
}


FEATURE_LABELS = {
    "hemoglobin": "Гемоглобин",
    "RBC": "Эритроциты",
    "hematocrit": "Гематокрит",
    "MCV": "MCV",
    "MCH": "MCH",
    "MCHC": "MCHC",
    "RDW": "RDW",
    "platelets": "Тромбоциты",
    "WBC": "Лейкоциты",
    "reticulocytes": "Ретикулоциты",

    "ferritin": "Ферритин",
    "serum_iron": "Железо",
    "transferrin": "Трансферрин",
    "TIBC": "ОЖСС",
    "UIBC": "НЖСС",
    "TSAT": "Насыщение трансферрина",
    "sTfR": "Растворимый рецептор трансферрина",
    "Ret_He": "Ret-He",

    "vitamin_B12": "Витамин B12",
    "active_B12": "Активный B12",
    "MMA": "Метилмалоновая кислота",
    "homocysteine": "Гомоцистеин",
    "folate": "Фолат",
    "vitamin_B6": "Витамин B6",

    "copper": "Медь",
    "ceruloplasmin": "Церулоплазмин",

    "CRP": "С-реактивный белок",
    "ESR": "СОЭ",
    "albumin": "Альбумин",

    "creatinine": "Креатинин",
    "eGFR": "СКФ",
    "TSH": "ТТГ",

    "LDH": "ЛДГ",
    "indirect_bilirubin": "Непрямой билирубин",
    "haptoglobin": "Гаптоглобин",
}