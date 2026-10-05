from __future__ import annotations

from typing import Sequence

import pandas as pd
from catboost import CatBoostClassifier

from ml.preprocessing.features import prepare_catboost_frame


RANDOM_STATE = 42

DEFAULT_CATBOOST_PARAMS = {
    "iterations": 300,
    "depth": 5,
    "learning_rate": 0.05,
    "l2_leaf_reg": 5,
    "loss_function": "Logloss",
    "auto_class_weights": "Balanced",
    "random_seed": RANDOM_STATE,
    "verbose": False,
    "allow_writing_files": False,
}


def make_catboost_classifier(**overrides) -> CatBoostClassifier:
    params = dict(DEFAULT_CATBOOST_PARAMS)
    params.update(overrides)
    return CatBoostClassifier(**params)


def train_final_catboost(
    X: pd.DataFrame,
    y,
    *,
    feature_columns: Sequence[str],
    categorical_features: Sequence[str],
    **overrides,
):
    X_cb = prepare_catboost_frame(
        X,
        list(feature_columns),
        list(categorical_features),
    )

    model = make_catboost_classifier(**overrides)
    model.fit(
        X_cb,
        y,
        cat_features=list(categorical_features),
    )
    return model
