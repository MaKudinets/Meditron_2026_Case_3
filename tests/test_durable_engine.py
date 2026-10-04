import pytest
import pandas as pd

pytest.importorskip("durable.lang")

from expert.engine import run_expert_engine


def test_durable_engine_smoke():
    row = pd.Series({
        "sex": "F",
        "hemoglobin": 105.0,
        "ferritin": 5.0,
        "serum_iron": 7.0,
        "TSAT": 10.0,
        "TIBC": 80.0,
        "Ret_He": 25.0,
        "vitamin_B12": 250.0,
        "folate": 10.0,
    })

    probabilities = {
        "iron_deficiency": 0.95,
        "B12_deficiency": 0.10,
        "folate_deficiency": 0.05,
        "B6_deficiency": 0.05,
        "copper_deficiency": 0.05,
        "inflammation_anemia": 0.05,
    }
    predictions = {
        target: int(probabilities[target] >= 0.5)
        for target in probabilities
    }

    result = run_expert_engine(
        row,
        probabilities,
        predictions,
    )

    assert result["rule_states"]["iron_deficiency"] == "supports"
    assert isinstance(result["fired_rules"], list)
