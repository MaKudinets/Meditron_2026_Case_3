from pathlib import Path
import json
import sys
import pandas as pd



PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.inference import predict_one
from expert.engine import run_expert_engine
from expert.explanations import build_explanation_payload


def find_project_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()

    for candidate in [start, *start.parents]:
        if (candidate / "data" / "raw" / "deficiency_anemia.csv").exists():
            return candidate

    raise FileNotFoundError(
        "Не найден корень проекта с data/raw/deficiency_anemia.csv"
    )


PROJECT_ROOT = find_project_root()

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "deficiency_anemia.csv"
)

BUNDLE_DIR = (
    PROJECT_ROOT
    / "artifacts"
    / "inference_bundle"
)


def main():
    print("=" * 80)
    print("MEDITRON ML + EXPERT VALIDATION")
    print("=" * 80)

    # ------------------------------------------------------------
    # 1. Загружаем исходный датасет
    # ------------------------------------------------------------
    df = pd.read_csv(DATA_PATH)

    print("\nDataset shape:")
    print(df.shape)

    # Берём первого пациента
    row = df.iloc[0].copy()

    patient_id = row.get("patient_id", "unknown")

    print("\nPatient ID:")
    print(patient_id)

    # ------------------------------------------------------------
    # 2. Убираем target columns
    # ------------------------------------------------------------
    TARGET_COLUMNS = [
        "anemia",
        "iron_deficiency",
        "B12_deficiency",
        "folate_deficiency",
        "B6_deficiency",
        "copper_deficiency",
        "inflammation_anemia",
        "mixed_deficiency",
        "anemia_class",
        "deficiency_cause",
    ]

    patient_features = row.drop(
        labels=[
            col
            for col in TARGET_COLUMNS
            if col in row.index
        ]
    ).to_dict()

    # patient_id не является feature модели
    patient_features.pop("patient_id", None)

    # ------------------------------------------------------------
    # 3. Frozen ML inference
    # ------------------------------------------------------------
    print("\n" + "=" * 80)
    print("1. FROZEN ML INFERENCE")
    print("=" * 80)

    ml_result = predict_one(
        patient_features,
        bundle_dir=BUNDLE_DIR,
        min_feature_coverage=0.70,
        allow_low_coverage=True,
    )

    print("\nFinal prediction:")
    print(
        json.dumps(
            ml_result["prediction"],
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\nBinary targets:")

    for target, result in ml_result["deficiencies"].items():
        print(
            f"{target:25s} "
            f"p={result['probability']:.4f} "
            f"pred={int(result['prediction'])} "
            f"threshold={result['threshold']:.4f}"
        )

    print("\nCoverage:")
    print(f"{ml_result['coverage']:.2%}")

    if ml_result["warnings"]:
        print("\nWarnings:")
        for warning in ml_result["warnings"]:
            print("-", warning)

    # ------------------------------------------------------------
    # 4. Подготавливаем ML outputs для expert layer
    # ------------------------------------------------------------
    probabilities = {
        target: float(result["probability"])
        for target, result in ml_result["deficiencies"].items()
    }

    predictions = {
        target: int(result["prediction"])
        for target, result in ml_result["deficiencies"].items()
    }

    # ------------------------------------------------------------
    # 5. Durable Rules expert engine
    # ------------------------------------------------------------
    print("\n" + "=" * 80)
    print("2. DURABLE RULES EXPERT ENGINE")
    print("=" * 80)

    expert_result = run_expert_engine(
        patient_features,
        probabilities,
        predictions,
    )

    print("\nRule states:")
    for target, state in expert_result["rule_states"].items():
        score = expert_result["rule_scores"][target]

        print(
            f"{target:25s} "
            f"state={state:10s} "
            f"score={score:.4f}"
        )

    print("\nFired rules:")
    for rule in expert_result["fired_rules"]:
        print("-", rule)

    # ------------------------------------------------------------
    # 6. Conflicts
    # ------------------------------------------------------------
    print("\n" + "=" * 80)
    print("3. ML ↔ RULE CONFLICTS")
    print("=" * 80)

    if expert_result["conflicts"]:
        for conflict in expert_result["conflicts"]:
            print(
                json.dumps(
                    conflict,
                    indent=2,
                    ensure_ascii=False,
                )
            )
    else:
        print("No strong ML ↔ rule conflicts.")

    # ------------------------------------------------------------
    # 7. Recommended next tests
    # ------------------------------------------------------------
    print("\n" + "=" * 80)
    print("4. RECOMMENDED NEXT TESTS")
    print("=" * 80)

    if expert_result["recommended_next_tests"]:
        for item in expert_result["recommended_next_tests"]:
            print(
                f"- {item['test']} "
                f"[{item['target']}]: "
                f"{item['reason']}"
            )
    else:
        print("No additional confirmatory tests recommended.")

    # ------------------------------------------------------------
    # 8. Evidence
    # ------------------------------------------------------------
    print("\n" + "=" * 80)
    print("5. CLINICAL EVIDENCE")
    print("=" * 80)

    for item in expert_result["evidence"]:
        print(
            f"- target={item['target']}; "
            f"feature={item['feature']}; "
            f"value={item['value']}; "
            f"direction={item['direction']}; "
            f"criterion={item['criterion']}"
        )

    # ------------------------------------------------------------
    # 9. Финальный explanation payload
    # ------------------------------------------------------------
    print("\n" + "=" * 80)
    print("6. FINAL EXPLANATION PAYLOAD")
    print("=" * 80)

    payload = build_explanation_payload(
        patient_id=patient_id,
        ml_result=ml_result,
        expert_result=expert_result,
    )

    print(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )

    # ------------------------------------------------------------
    # 10. Сравнение с true label
    # Только для внутренней проверки, НЕ для inference
    # ------------------------------------------------------------
    print("\n" + "=" * 80)
    print("7. INTERNAL TRUE LABEL CHECK")
    print("=" * 80)

    true_class = row.get("anemia_class")
    true_cause = row.get("deficiency_cause")

    predicted_class = ml_result["prediction"]["anemia_class"]
    predicted_cause = ml_result["prediction"]["deficiency_cause"]

    print("True anemia_class:")
    print(true_class)

    print("\nPredicted anemia_class:")
    print(predicted_class)

    print("\nClass match:")
    print(predicted_class == true_class)

    print("\nTrue deficiency_cause:")
    print(true_cause)

    print("\nPredicted deficiency_cause:")
    print(predicted_cause)

    print("\nCause match:")
    print(predicted_cause == true_cause)

    print("\n" + "=" * 80)
    print("VALIDATION FINISHED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()