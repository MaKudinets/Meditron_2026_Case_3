# Meditron production modules

This folder is the production split of notebooks 01–07.

## What is frozen

The ML architecture remains:

- 37-feature contract
- six binary targets
- L1 Logistic Regression
- CatBoost
- Platt calibration
- weighted L1 + CatBoost ensemble
- fold-derived deployment weights/thresholds from notebook 04
- deterministic anemia rule
- hierarchical 12-class assembly

Internal quality continues to be reported from notebook 04 OOF evaluation,
not from the full-data deployment models.

## Expert layer

Production expert inference uses **Durable Rules** in:

`expert/engine.py`

Medical constants live separately in:

`expert/knowledge_base.py`

This is deliberate: a physician can later change a threshold or rule without
retraining the ML models.

`ml/clinical_rules.py` is only a backwards-compatible wrapper for the old
notebooks/API imports.

## Installation

```bash
conda activate project.sechenov
python -m pip install -r requirements-production.txt
```

Durable Rules 2.0.28 is distributed as source and contains a C extension.
If installation fails because `gcc` is absent in WSL:

```bash
sudo apt update
sudo apt install -y build-essential
python -m pip install durable_rules==2.0.28
```

Official import used by the engine:

```python
from durable.lang import ruleset, when_all, m, post
```

## Existing artifacts expected

The inference code expects the bundle already created by notebook 06:

```text
artifacts/inference_bundle/
├── feature_contract.json
├── manifest.json
├── ensemble_meta_settings.csv
└── models/
    ├── iron_deficiency/
    ├── B12_deficiency/
    ├── folate_deficiency/
    ├── B6_deficiency/
    ├── copper_deficiency/
    └── inflammation_anemia/
```

Each target directory must contain:

```text
l1_pipeline.joblib
l1_platt_calibrator.joblib
catboost_model.cbm
catboost_platt_calibrator.joblib
training_settings.json
```

## ML inference

```python
from ml.inference import predict_one

result = predict_one({
    "sex": "F",
    "hemoglobin": 108,
    # ...other available features...
})
```

The production coverage threshold defaults to 70%.

## Durable expert inference

```python
from expert.engine import run_expert_engine

expert = run_expert_engine(
    patient=patient_features,
    probabilities={
        target: result["deficiencies"][target]["probability"]
        for target in result["deficiencies"]
    },
    predictions={
        target: int(result["deficiencies"][target]["prediction"])
        for target in result["deficiencies"]
    },
)
```

## Tests

```bash
pytest -q tests
```

`test_durable_engine.py` is skipped automatically if Durable Rules is not
installed. In the final project environment it should NOT be skipped.
