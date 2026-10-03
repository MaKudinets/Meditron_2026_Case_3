"""
Валидация входных данных для модели Meditron.

Модуль отвечает за проверку данных ДО передачи их в модель:

1. проверяет тип входных данных;
2. проверяет наличие всех признаков модели;
3. не допускает передачу идентификаторов пациента;
4. проверяет значения категориальных признаков;
5. проверяет числовой формат лабораторных показателей;
6. обнаруживает пропуски;
7. обнаруживает бесконечные значения;
8. хранит официальные единицы измерения признаков.

Названия признаков и единицы измерения взяты из variables.xlsx.

Важно:
медицинские референсные диапазоны в variables.xlsx не заданы,
поэтому validator не пытается определять, является ли конкретное
лабораторное значение клинически нормальным или патологическим.
"""

from typing import Any

import numpy as np
import pandas as pd

from ml.preprocessing.features import (
    FEATURE_COLUMNS,
    ID_COLUMNS,
)


# ============================================================
# ЕДИНИЦЫ ИЗМЕРЕНИЯ
# ============================================================

# Официальные единицы измерения входных признаков.
#
# Используются как единый источник информации об ожидаемых
# единицах при работе API, frontend и импорта файлов.
#
# Для age_years и sex лабораторная единица не требуется,
# но сохраняем обозначения из variables.xlsx.

FEATURE_UNITS = {
    "age_years": "years",
    "sex": None,
    "hemoglobin": "g/L",
    "RBC": "10^12/L",
    "hematocrit": "%",
    "MCV": "fL",
    "MCH": "pg",
    "MCHC": "g/L",
    "RDW": "%",
    "platelets": "10^9/L",
    "WBC": "10^9/L",
    "reticulocytes": "%",
    "ferritin": "µg/L",
    "serum_iron": "µmol/L",
    "transferrin": "g/L",
    "TIBC": "µmol/L",
    "UIBC": "µmol/L",
    "TSAT": "%",
    "sTfR": "mg/L",
    "Ret_He": "pg",
    "vitamin_B12": "pg/mL",
    "active_B12": "pmol/L",
    "MMA": "µmol/L",
    "homocysteine": "µmol/L",
    "folate": "ng/mL",
    "vitamin_B6": "nmol/L",
    "copper": "µmol/L",
    "ceruloplasmin": "g/L",
    "CRP": "mg/L",
    "ESR": "mm/h",
    "creatinine": "µmol/L",
    "eGFR": "mL/min/1.73m²",
    "TSH": "mIU/L",
    "albumin": "g/L",
    "LDH": "U/L",
    "indirect_bilirubin": "µmol/L",
    "haptoglobin": "g/L",
}


# ============================================================
# ДОПУСТИМЫЕ КАТЕГОРИАЛЬНЫЕ ЗНАЧЕНИЯ
# ============================================================

# В features.py значение sex приводится:
#
#   .str.strip()
#   .str.lower()
#
# Поэтому здесь используем нормализованный формат.
ALLOWED_SEX_VALUES = {"f", "m"}


# Все признаки модели, кроме sex, должны быть числовыми.
NUMERIC_FEATURES = [
    column
    for column in FEATURE_COLUMNS
    if column != "sex"
]


# ============================================================
# ОСНОВНАЯ ВАЛИДАЦИЯ
# ============================================================

def validate_input(df: pd.DataFrame) -> list[str]:
    """
    Проверяет входные данные перед передачей в модель.

    Parameters
    ----------
    df : pd.DataFrame
        Данные одного или нескольких пациентов.

    Returns
    -------
    list[str]
        Список предупреждений.

        Пустой список означает, что предупреждений нет.

    Raises
    ------
    TypeError
        Если передан объект, отличный от pandas.DataFrame.

    ValueError
        Если обнаружена критическая проблема:
        - пустой DataFrame;
        - идентификаторы пациента;
        - отсутствующие признаки;
        - неподдерживаемое значение sex;
        - нечисловые значения;
        - бесконечные значения.
    """

    # --------------------------------------------------------
    # 1. Проверяем тип объекта
    # --------------------------------------------------------

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Ожидался pandas.DataFrame, "
            f"получен {type(df).__name__}."
        )

    # --------------------------------------------------------
    # 2. Проверяем, что данные не пустые
    # --------------------------------------------------------

    if df.empty:
        raise ValueError(
            "Передан пустой DataFrame."
        )

    # --------------------------------------------------------
    # 3. Не допускаем идентификаторы пациента
    # --------------------------------------------------------
    #
    # patient_id не является признаком модели.
    # Согласно архитектуре Meditron идентификаторы не должны
    # передаваться в ML.

    forbidden_columns = [
        column
        for column in ID_COLUMNS
        if column in df.columns
    ]

    if forbidden_columns:
        raise ValueError(
            "Идентификаторы пациента не должны "
            "передаваться в модель: "
            + ", ".join(forbidden_columns)
        )

    # --------------------------------------------------------
    # 4. Проверяем наличие всех 37 признаков
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in FEATURE_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Отсутствуют обязательные признаки модели: "
            + ", ".join(missing_columns)
        )

    # --------------------------------------------------------
    # 5. Проверяем sex
    # --------------------------------------------------------

    normalized_sex = (
        df["sex"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    invalid_sex_mask = (
        normalized_sex.notna()
        & ~normalized_sex.isin(ALLOWED_SEX_VALUES)
    )

    if invalid_sex_mask.any():

        invalid_values = (
            normalized_sex[invalid_sex_mask]
            .dropna()
            .unique()
            .tolist()
        )

        raise ValueError(
            "Недопустимое значение sex: "
            + ", ".join(map(str, invalid_values))
            + ". Допустимые значения: f, m."
        )

    # --------------------------------------------------------
    # 6. Проверяем числовые признаки
    # --------------------------------------------------------

    invalid_numeric_columns = []

    for column in NUMERIC_FEATURES:

        # Проверяем только заполненные значения.
        # NaN рассматривается отдельно как пропуск.
        non_missing_mask = df[column].notna()

        if not non_missing_mask.any():
            continue

        converted = pd.to_numeric(
            df.loc[non_missing_mask, column],
            errors="coerce",
        )

        # Если исходное значение существовало,
        # но после преобразования стало NaN,
        # значит оно не является корректным числом.
        if converted.isna().any():
            invalid_numeric_columns.append(column)

    if invalid_numeric_columns:
        raise ValueError(
            "Нечисловые значения обнаружены в признаках: "
            + ", ".join(invalid_numeric_columns)
        )

    # --------------------------------------------------------
    # 7. Проверяем бесконечные значения
    # --------------------------------------------------------

    infinite_columns = []

    for column in NUMERIC_FEATURES:

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if np.isinf(numeric_values).any():
            infinite_columns.append(column)

    if infinite_columns:
        raise ValueError(
            "Обнаружены бесконечные значения в признаках: "
            + ", ".join(infinite_columns)
        )

    # --------------------------------------------------------
    # 8. Формируем предупреждения
    # --------------------------------------------------------

    warnings = []

    # Проверяем пропущенные значения.
    missing_counts = (
        df[FEATURE_COLUMNS]
        .isna()
        .sum()
    )

    columns_with_missing = (
        missing_counts[missing_counts > 0]
        .index
        .tolist()
    )

    if columns_with_missing:
        warnings.append(
            "Обнаружены пропущенные значения: "
            + ", ".join(columns_with_missing)
        )

    return warnings


# ============================================================
# ВАЛИДАЦИЯ ОДНОГО ПАЦИЕНТА
# ============================================================

def validate_patient(data: dict[str, Any]) -> list[str]:
    """
    Проверяет данные одного пациента.

    Эта функция предназначена прежде всего для Predictor/API.

    Полученный JSON/dict преобразуется в DataFrame из одной
    строки, после чего используется общая функция validate_input().

    Parameters
    ----------
    data : dict
        Данные одного пациента.

    Returns
    -------
    list[str]
        Список предупреждений.
    """

    if not isinstance(data, dict):
        raise TypeError(
            "Данные пациента должны быть переданы как dict."
        )

    if not data:
        raise ValueError(
            "Передан пустой словарь пациента."
        )

    patient_df = pd.DataFrame([data])

    return validate_input(patient_df)


# ============================================================
# ПОЛУЧЕНИЕ ОЖИДАЕМОЙ ЕДИНИЦЫ
# ============================================================

def get_feature_unit(feature_name: str) -> str | None:
    """
    Возвращает ожидаемую единицу измерения признака.

    Например:
        get_feature_unit("hemoglobin") -> "g/L"
        get_feature_unit("ferritin") -> "µg/L"

    Parameters
    ----------
    feature_name : str
        Название признака.

    Returns
    -------
    str | None
        Единица измерения.

    Raises
    ------
    KeyError
        Если признак отсутствует в схеме модели.
    """

    if feature_name not in FEATURE_UNITS:
        raise KeyError(
            f"Неизвестный признак: {feature_name}"
        )

    return FEATURE_UNITS[feature_name]