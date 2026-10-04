from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


RANDOM_STATE = 42
C_GRID = np.logspace(-4, 0, 9)


def infer_feature_groups(
    X: pd.DataFrame,
    feature_columns: Sequence[str] | None = None,
):
    columns = list(feature_columns or X.columns)

    categorical = [
        col for col in columns
        if (
            pd.api.types.is_object_dtype(X[col])
            or pd.api.types.is_string_dtype(X[col])
            or isinstance(X[col].dtype, pd.CategoricalDtype)
        )
    ]

    numeric = [col for col in columns if col not in categorical]
    return numeric, categorical


def make_l1_pipeline(
    *,
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
    C: float = 1.0,
    random_state: int = RANDOM_STATE,
) -> Pipeline:
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, list(numeric_features)),
            ("cat", categorical_pipeline, list(categorical_features)),
        ],
        remainder="drop",
    )

    model = LogisticRegression(
        penalty="l1",
        solver="saga",
        C=float(C),
        class_weight="balanced",
        max_iter=5000,
        random_state=random_state,
    )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])


def select_l1_c(
    X: pd.DataFrame,
    y,
    *,
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
    c_grid=C_GRID,
    n_splits: int = 5,
    random_state: int = RANDOM_STATE,
    n_jobs: int = -1,
):
    cv = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    search = GridSearchCV(
        estimator=make_l1_pipeline(
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            random_state=random_state,
        ),
        param_grid={"model__C": np.asarray(c_grid, dtype=float)},
        scoring="average_precision",
        cv=cv,
        n_jobs=n_jobs,
        refit=True,
    )

    search.fit(X, y)
    return search


def train_final_l1(
    X: pd.DataFrame,
    y,
    *,
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
    c_grid=C_GRID,
    random_state: int = RANDOM_STATE,
    n_jobs: int = -1,
):
    search = select_l1_c(
        X,
        y,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        c_grid=c_grid,
        n_splits=5,
        random_state=random_state,
        n_jobs=n_jobs,
    )

    return search.best_estimator_, float(search.best_params_["model__C"])
