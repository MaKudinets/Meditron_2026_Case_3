from __future__ import annotations

from pathlib import Path
import sys
import json
import time

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.inference import predict_one
from expert.engine import run_expert_engine
from expert.explanations import build_explanation_payload

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "deficiency_anemia.csv"
BUNDLE_DIR = PROJECT_ROOT / "artifacts" / "inference_bundle"
OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "batch_validation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

BINARY_TARGETS = [
    "iron_deficiency",
    "B12_deficiency",
    "folate_deficiency",
    "B6_deficiency",
    "copper_deficiency",
    "inflammation_anemia",
]


def safe_patient_features(row: pd.Series) -> dict:
    features = row.drop(
        labels=[c for c in TARGET_COLUMNS if c in row.index]
    ).to_dict()
    features.pop("patient_id", None)
    return features


def binary_metrics(y_true, y_pred) -> dict:
    return {
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
    }


def main():
    started = time.time()

    print("=" * 88)
    print("MEDITRON — BATCH VALIDATION OF PRODUCTION ML + DURABLE RULES")
    print("=" * 88)

    df = pd.read_csv(DATA_PATH)

    print(f"\nDataset shape: {df.shape}")
    print(f"Patients: {len(df)}")
    print(f"Bundle: {BUNDLE_DIR}")

    patient_rows = []
    binary_rows = []
    conflict_rows = []
    rule_state_rows = []
    recommendation_rows = []
    failures = []
    payloads = []

    print("\nRunning production pipeline on all patients...")

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        patient_id = row.get("patient_id", f"row_{i}")
        patient_features = safe_patient_features(row)

        try:
            ml_result = predict_one(
                patient_features,
                bundle_dir=BUNDLE_DIR,
                min_feature_coverage=0.70,
                allow_low_coverage=True,
            )

            probabilities = {
                t: float(ml_result["deficiencies"][t]["probability"])
                for t in BINARY_TARGETS
            }

            predictions = {
                t: int(bool(ml_result["deficiencies"][t]["prediction"]))
                for t in BINARY_TARGETS
            }

            expert_result = run_expert_engine(
                patient_features,
                probabilities,
                predictions,
            )

            payloads.append(
                build_explanation_payload(
                    patient_id=patient_id,
                    ml_result=ml_result,
                    expert_result=expert_result,
                )
            )

            patient_rows.append({
                "patient_id": patient_id,
                "true_anemia_class": row.get("anemia_class"),
                "pred_anemia_class": ml_result["prediction"]["anemia_class"],
                "class_match": (
                    ml_result["prediction"]["anemia_class"]
                    == row.get("anemia_class")
                ),
                "true_deficiency_cause": row.get("deficiency_cause"),
                "pred_deficiency_cause": ml_result["prediction"]["deficiency_cause"],
                "cause_match": (
                    ml_result["prediction"]["deficiency_cause"]
                    == row.get("deficiency_cause")
                ),
                "coverage": float(ml_result["coverage"]),
                "n_warnings": len(ml_result.get("warnings", [])),
                "n_conflicts": len(expert_result["conflicts"]),
                "n_recommendations": len(
                    expert_result["recommended_next_tests"]
                ),
            })

            for target in BINARY_TARGETS:
                binary_rows.append({
                    "patient_id": patient_id,
                    "target": target,
                    "true": int(row[target]),
                    "probability": probabilities[target],
                    "pred": predictions[target],
                    "threshold": float(
                        ml_result["deficiencies"][target]["threshold"]
                    ),
                    "rule_score": float(
                        expert_result["rule_scores"][target]
                    ),
                    "rule_state": expert_result["rule_states"][target],
                })

                rule_state_rows.append({
                    "patient_id": patient_id,
                    "target": target,
                    "rule_state": expert_result["rule_states"][target],
                    "rule_score": float(
                        expert_result["rule_scores"][target]
                    ),
                })

            for conflict in expert_result["conflicts"]:
                conflict_rows.append({
                    "patient_id": patient_id,
                    **conflict,
                })

            for item in expert_result["recommended_next_tests"]:
                recommendation_rows.append({
                    "patient_id": patient_id,
                    **item,
                })

        except Exception as exc:
            failures.append({
                "patient_id": patient_id,
                "error_type": type(exc).__name__,
                "error": str(exc),
            })

        if i % 50 == 0 or i == len(df):
            print(
                f"  processed {i:>3}/{len(df)} | failures={len(failures)}"
            )

    patient_df = pd.DataFrame(patient_rows)
    binary_df = pd.DataFrame(binary_rows)
    conflicts_df = pd.DataFrame(conflict_rows)
    rule_states_df = pd.DataFrame(rule_state_rows)
    recommendations_df = pd.DataFrame(recommendation_rows)
    failures_df = pd.DataFrame(failures)

    print("\n" + "=" * 88)
    print("1. PIPELINE STABILITY")
    print("=" * 88)
    print(f"Successful patients: {len(patient_df)}/{len(df)}")
    print(f"Failures: {len(failures_df)}")

    if len(failures_df):
        print("\nFailure examples:")
        print(failures_df.head(10).to_string(index=False))

    coverage_summary = pd.DataFrame()
    class_summary = pd.DataFrame()
    class_distribution = pd.DataFrame()

    print("\n" + "=" * 88)
    print("2. FEATURE COVERAGE")
    print("=" * 88)

    if not patient_df.empty:
        coverage = patient_df["coverage"]

        coverage_summary = pd.DataFrame([{
            "min": coverage.min(),
            "q25": coverage.quantile(0.25),
            "median": coverage.median(),
            "q75": coverage.quantile(0.75),
            "max": coverage.max(),
            "mean": coverage.mean(),
            "below_70pct_n": int((coverage < 0.70).sum()),
            "below_70pct_pct": float((coverage < 0.70).mean() * 100),
        }])

        print(coverage_summary.to_string(index=False))

    print("\n" + "=" * 88)
    print("3. PRODUCTION REFIT — DESCRIPTIVE CLASSIFICATION CHECK")
    print("=" * 88)

    print(
        "IMPORTANT: deployment models were fitted on all 840 patients.\n"
        "These are NOT unbiased quality estimates.\n"
        "Use notebook 04 OOF metrics as the official ML quality.\n"
    )

    if not patient_df.empty:
        y_true = patient_df["true_anemia_class"]
        y_pred = patient_df["pred_anemia_class"]

        class_summary = pd.DataFrame([{
            "accuracy_on_refit_cohort": accuracy_score(y_true, y_pred),
            "macro_f1_on_refit_cohort": f1_score(
                y_true, y_pred, average="macro", zero_division=0
            ),
            "balanced_accuracy_on_refit_cohort": balanced_accuracy_score(
                y_true, y_pred
            ),
            "class_match_n": int(patient_df["class_match"].sum()),
            "class_match_pct": float(
                patient_df["class_match"].mean() * 100
            ),
        }])

        print(class_summary.to_string(index=False))

        print("\nPredicted class distribution:")
        class_distribution = (
            patient_df["pred_anemia_class"]
            .value_counts()
            .rename_axis("pred_anemia_class")
            .reset_index(name="n")
        )
        print(class_distribution.to_string(index=False))

    print("\n" + "=" * 88)
    print("4. BINARY TARGET CHECK")
    print("=" * 88)

    binary_metric_rows = []

    if not binary_df.empty:
        for target in BINARY_TARGETS:
            part = binary_df[binary_df["target"] == target]
            metrics = binary_metrics(
                part["true"].astype(int),
                part["pred"].astype(int),
            )
            metrics["target"] = target
            metrics["positive_predictions"] = int(part["pred"].sum())
            metrics["true_positives_in_dataset"] = int(part["true"].sum())
            binary_metric_rows.append(metrics)

        binary_metric_df = pd.DataFrame(binary_metric_rows)[
            [
                "target",
                "f1",
                "precision",
                "recall",
                "accuracy",
                "balanced_accuracy",
                "positive_predictions",
                "true_positives_in_dataset",
            ]
        ]
        print(binary_metric_df.to_string(index=False))
    else:
        binary_metric_df = pd.DataFrame()

    print("\n" + "=" * 88)
    print("5. DURABLE RULE STATES")
    print("=" * 88)

    if not rule_states_df.empty:
        rule_state_summary = (
            rule_states_df
            .groupby(["target", "rule_state"])
            .size()
            .reset_index(name="n")
            .sort_values(["target", "rule_state"])
        )
        print(rule_state_summary.to_string(index=False))
    else:
        rule_state_summary = pd.DataFrame()

    print("\n" + "=" * 88)
    print("6. ML ↔ RULE CONFLICTS")
    print("=" * 88)

    if not conflicts_df.empty:
        conflict_summary = (
            conflicts_df
            .groupby(["target", "type"])
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
        )
        print(conflict_summary.to_string(index=False))
    else:
        conflict_summary = pd.DataFrame()
        print("No strong conflicts.")

    print("\n" + "=" * 88)
    print("7. RECOMMENDED NEXT TESTS")
    print("=" * 88)

    if not recommendations_df.empty:
        recommendation_summary = (
            recommendations_df
            .groupby(["target", "test"])
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
        )
        print(recommendation_summary.to_string(index=False))
    else:
        recommendation_summary = pd.DataFrame()
        print("No recommendations.")

    print("\n" + "=" * 88)
    print("8. OFFICIAL INTERNAL ML QUALITY TO REPORT")
    print("=" * 88)
    print(
        "Notebook 04 OOF evaluation:\n"
        "  Macro-F1           ≈ 0.8997\n"
        "  Balanced Accuracy  ≈ 0.8860\n"
        "  Accuracy           ≈ 0.9048\n"
    )
    print("Do NOT replace these with the refit-cohort metrics above.")

    patient_df.to_csv(
        OUTPUT_DIR / "batch_patient_results.csv", index=False
    )
    binary_df.to_csv(
        OUTPUT_DIR / "batch_binary_results.csv", index=False
    )
    conflicts_df.to_csv(
        OUTPUT_DIR / "batch_conflicts.csv", index=False
    )
    rule_states_df.to_csv(
        OUTPUT_DIR / "batch_rule_states.csv", index=False
    )
    recommendations_df.to_csv(
        OUTPUT_DIR / "batch_recommendations.csv", index=False
    )
    failures_df.to_csv(
        OUTPUT_DIR / "batch_failures.csv", index=False
    )

    if not coverage_summary.empty:
        coverage_summary.to_csv(
            OUTPUT_DIR / "coverage_summary.csv", index=False
        )

    if not class_summary.empty:
        class_summary.to_csv(
            OUTPUT_DIR / "refit_class_summary.csv", index=False
        )

    if not class_distribution.empty:
        class_distribution.to_csv(
            OUTPUT_DIR / "predicted_class_distribution.csv", index=False
        )

    if not binary_metric_df.empty:
        binary_metric_df.to_csv(
            OUTPUT_DIR / "refit_binary_metrics.csv", index=False
        )

    if not rule_state_summary.empty:
        rule_state_summary.to_csv(
            OUTPUT_DIR / "rule_state_summary.csv", index=False
        )

    if not conflict_summary.empty:
        conflict_summary.to_csv(
            OUTPUT_DIR / "conflict_summary.csv", index=False
        )

    if not recommendation_summary.empty:
        recommendation_summary.to_csv(
            OUTPUT_DIR / "recommendation_summary.csv", index=False
        )

    with (
        OUTPUT_DIR / "batch_expert_payloads.jsonl"
    ).open("w", encoding="utf-8") as f:
        for payload in payloads:
            f.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    default=str,
                ) + "\n"
            )

    elapsed = time.time() - started

    print("\n" + "=" * 88)
    print("9. SAVED ARTIFACTS")
    print("=" * 88)
    print("Output directory:", OUTPUT_DIR)
    print(f"Elapsed: {elapsed:.1f} sec")

    print("\n" + "=" * 88)
    if len(failures_df) == 0:
        print("BATCH VALIDATION FINISHED SUCCESSFULLY")
    else:
        print(
            "BATCH VALIDATION FINISHED WITH FAILURES — "
            "inspect batch_failures.csv"
        )
    print("=" * 88)


if __name__ == "__main__":
    main()
