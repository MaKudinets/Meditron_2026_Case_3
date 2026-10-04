from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


EPS = 1e-6
RANDOM_STATE = 42


def probability_to_logit(probabilities):
    p = np.clip(
        np.asarray(probabilities, dtype=float),
        EPS,
        1.0 - EPS,
    )
    return np.log(p / (1.0 - p)).reshape(-1, 1)


def fit_platt_calibrator(
    oof_probabilities,
    y_true,
    *,
    random_state: int = RANDOM_STATE,
):
    calibrator = LogisticRegression(
        solver="lbfgs",
        random_state=random_state,
    )
    calibrator.fit(
        probability_to_logit(oof_probabilities),
        np.asarray(y_true, dtype=int),
    )
    return calibrator


def apply_platt_calibrator(calibrator, probabilities):
    return calibrator.predict_proba(
        probability_to_logit(probabilities)
    )[:, 1]
