"""
Clinical engineered features for Meditron.

Модуль создаёт дополнительные признаки на основе
медицинских гипотез.

Важно:
- признаки не содержат target;
- здесь не формируется готовый диагноз;
- не используются бинарные target-флаги;
- исходные признаки сохраняются;
- деление на 0 безопасно обрабатывается через NaN.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ============================================================
# СПИСОК ДОПОЛНИТЕЛЬНЫХ CLINICAL FEATURES
# ============================================================

MEDICAL_FEATURE_COLUMNS = [
    # H1 / H2: железодефицит и воспаление
    "iron_tibc_ratio",
    "ferritin_crp_ratio",
    "ferritin_esr_ratio",
    "stfr_ferritin_ratio",

    # H4 / H5: B12 / folate metabolism
    "mma_b12_ratio",
    "homocysteine_b12_ratio",
    "homocysteine_folate_ratio",
    "mma_folate_ratio",

    # H6: mixed deficiency / erythrocyte heterogeneity
    "rdw_mcv_ratio",
    "rdw_mch_ratio",
]


# ============================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ
# ============================================================

def _safe_divide(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """
    Безопасно делит одну Series на другую.

    Если знаменатель равен 0, он заменяется на NaN,
    чтобы не создавать бесконечные значения.

    Parameters
    ----------
    numerator : pd.Series
        Числитель.

    denominator : pd.Series
        Знаменатель.

    Returns
    -------
    pd.Series
        Результат деления.
    """

    safe_denominator = denominator.replace(
        0,
        np.nan,
    )

    return numerator / safe_denominator


# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def add_medical_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Добавляет дополнительные medical features.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame с исходными признаками модели.

    Returns
    -------
    pd.DataFrame
        Исходные признаки + engineered medical features.

    Raises
    ------
    TypeError
        Если передан объект, отличный от pandas.DataFrame.

    ValueError
        Если отсутствуют исходные признаки,
        необходимые для расчёта medical features.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "add_medical_features ожидает pandas.DataFrame."
        )

    # --------------------------------------------------------
    # Проверяем наличие необходимых исходных признаков
    # --------------------------------------------------------

    required_columns = [
        "serum_iron",
        "TIBC",
        "ferritin",
        "CRP",
        "ESR",
        "sTfR",
        "MMA",
        "vitamin_B12",
        "homocysteine",
        "folate",
        "RDW",
        "MCV",
        "MCH",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Для расчёта medical features отсутствуют признаки: "
            + ", ".join(missing_columns)
        )

    # Не изменяем исходный DataFrame.
    X = df.copy()

    # ========================================================
    # H1 / H2
    # IRON DEFICIENCY / INFLAMMATION
    # ========================================================

    # Соотношение serum iron / TIBC.
    # Характеризует доступность железа относительно
    # общей железосвязывающей способности.
    X["iron_tibc_ratio"] = _safe_divide(
        X["serum_iron"],
        X["TIBC"],
    )

    # Соотношение ferritin и CRP.
    # Может быть полезно для различения изменений ferritin,
    # связанных с запасами железа и воспалительным состоянием.
    X["ferritin_crp_ratio"] = _safe_divide(
        X["ferritin"],
        X["CRP"],
    )

    # Аналогичное взаимодействие ferritin и ESR.
    X["ferritin_esr_ratio"] = _safe_divide(
        X["ferritin"],
        X["ESR"],
    )

    # Соотношение soluble transferrin receptor и ferritin.
    X["stfr_ferritin_ratio"] = _safe_divide(
        X["sTfR"],
        X["ferritin"],
    )

    # ========================================================
    # H4 / H5
    # B12 FUNCTIONAL PROFILE / B12 VS FOLATE
    # ========================================================

    # Связь функционального маркера MMA с уровнем B12.
    X["mma_b12_ratio"] = _safe_divide(
        X["MMA"],
        X["vitamin_B12"],
    )

    # Homocysteine относительно B12.
    X["homocysteine_b12_ratio"] = _safe_divide(
        X["homocysteine"],
        X["vitamin_B12"],
    )

    # Homocysteine относительно folate.
    X["homocysteine_folate_ratio"] = _safe_divide(
        X["homocysteine"],
        X["folate"],
    )

    # MMA относительно folate.
    X["mma_folate_ratio"] = _safe_divide(
        X["MMA"],
        X["folate"],
    )

    # ========================================================
    # H6
    # MIXED DEFICIENCY / ERYTHROCYTE HETEROGENEITY
    # ========================================================

    # RDW относительно MCV.
    # Может отражать сочетание анизоцитоза и среднего
    # объёма эритроцита.
    X["rdw_mcv_ratio"] = _safe_divide(
        X["RDW"],
        X["MCV"],
    )

    # RDW относительно MCH.
    X["rdw_mch_ratio"] = _safe_divide(
        X["RDW"],
        X["MCH"],
    )

    return X