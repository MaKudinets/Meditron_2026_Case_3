import pandas as pd

from expert.knowledge_base import (
    b12_rule_score,
    inflammation_rule_score,
    rule_state,
)
from expert.recommendations import recommended_next_tests
from ml.inference.ensemble import extract_ensemble_settings
from ml.inference.predictor import (
    assemble_predicted_class,
    assemble_predicted_cause,
)


def test_b12_v2_is_neutral_above_cutoff():
    row = pd.Series({"vitamin_B12": 257.0})
    assert b12_rule_score(row) == 0.5
    assert rule_state(0.5) == "unknown"


def test_inflammation_needs_at_least_two_markers():
    row = pd.Series({
        "sex": "F",
        "hemoglobin": 110.0,
        "ferritin": 100.0,
    })
    assert inflammation_rule_score(row) == 0.5


def test_recommendations_are_contextual():
    row = pd.Series({
        "ferritin": None,
        "TSAT": None,
        "Ret_He": None,
        "sTfR": None,
    })

    low = recommended_next_tests(
        row,
        {"iron_deficiency": 0.10},
    )
    high = recommended_next_tests(
        row,
        {"iron_deficiency": 0.90},
    )

    assert low == []
    assert {x["test"] for x in high} >= {"ferritin", "TSAT", "Ret_He", "sTfR"}


def test_ensemble_settings_use_fold_median():
    meta = pd.DataFrame({
        "target": ["iron_deficiency"] * 5,
        "fold": [1, 2, 3, 4, 5],
        "w_l1": [0.4, 0.5, 0.4, 0.3, 0.4],
        "w_cb": [0.6, 0.5, 0.6, 0.7, 0.6],
        "w_rule": [0, 0, 0, 0, 0],
        "threshold": [0.41, 0.40, 0.42, 0.48, 0.33],
    })

    result = extract_ensemble_settings(
        meta,
        ["iron_deficiency"],
    )["iron_deficiency"]

    assert result["l1_weight"] == 0.4
    assert result["catboost_weight"] == 0.6
    assert result["rule_weight"] == 0.0
    assert result["threshold"] == 0.41


def test_class_assembly():
    probs = {
        "iron_deficiency": 0.9,
        "B12_deficiency": 0.8,
        "folate_deficiency": 0.1,
        "B6_deficiency": 0.1,
        "copper_deficiency": 0.1,
        "inflammation_anemia": 0.1,
    }
    preds = {
        "iron_deficiency": 1,
        "B12_deficiency": 1,
        "folate_deficiency": 0,
        "B6_deficiency": 0,
        "copper_deficiency": 0,
        "inflammation_anemia": 0,
    }

    cls = assemble_predicted_class(1, probs, preds)
    cause = assemble_predicted_cause(cls, probs)

    assert cls == "mixed_deficiency"
    assert cause == "iron_B12"
