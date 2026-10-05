from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

import joblib
import pandas as pd
from catboost import CatBoostClassifier

from .ensemble import extract_ensemble_settings


@dataclass
class TargetArtifacts:
    target: str
    l1_model: Any
    l1_calibrator: Any
    catboost_model: CatBoostClassifier
    catboost_calibrator: Any
    threshold: float
    l1_weight: float
    catboost_weight: float
    rule_weight: float


@dataclass
class InferenceBundle:
    bundle_dir: Path
    feature_contract: dict
    manifest: dict
    settings: dict[str, dict[str, float]]
    targets: dict[str, TargetArtifacts]


_BUNDLE_CACHE: dict[str, InferenceBundle] = {}


def _find_default_bundle_dir() -> Path:
    env = os.getenv("MEDITRON_BUNDLE_DIR")
    if env:
        path = Path(env).expanduser().resolve()
        if path.exists():
            return path

    start = Path.cwd().resolve()
    for candidate in [start, *start.parents]:
        path = candidate / "artifacts" / "inference_bundle"
        if (path / "feature_contract.json").exists():
            return path

    raise FileNotFoundError(
        "Inference bundle not found. Set MEDITRON_BUNDLE_DIR or place "
        "artifacts/inference_bundle under the project root."
    )


def load_inference_bundle(
    bundle_dir: str | Path | None = None,
    *,
    refresh: bool = False,
) -> InferenceBundle:
    bundle_dir = (
        Path(bundle_dir).expanduser().resolve()
        if bundle_dir is not None
        else _find_default_bundle_dir()
    )

    cache_key = str(bundle_dir)
    if not refresh and cache_key in _BUNDLE_CACHE:
        return _BUNDLE_CACHE[cache_key]

    contract_path = bundle_dir / "feature_contract.json"
    manifest_path = bundle_dir / "manifest.json"
    meta_path = bundle_dir / "ensemble_meta_settings.csv"
    model_dir = bundle_dir / "models"

    for path in (contract_path, manifest_path, meta_path, model_dir):
        if not path.exists():
            raise FileNotFoundError(path)

    with contract_path.open("r", encoding="utf-8") as f:
        contract = json.load(f)

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    targets = list(contract["targets"])
    meta = pd.read_csv(meta_path)
    settings = extract_ensemble_settings(meta, targets)

    loaded: dict[str, TargetArtifacts] = {}

    for target in targets:
        target_dir = model_dir / target

        required = {
            "l1_model": target_dir / "l1_pipeline.joblib",
            "l1_calibrator": target_dir / "l1_platt_calibrator.joblib",
            "catboost_model": target_dir / "catboost_model.cbm",
            "catboost_calibrator": target_dir / "catboost_platt_calibrator.joblib",
        }

        missing = [str(path) for path in required.values() if not path.exists()]
        if missing:
            raise FileNotFoundError(
                f"Bundle incomplete for {target}: " + ", ".join(missing)
            )

        catboost_model = CatBoostClassifier()
        catboost_model.load_model(str(required["catboost_model"]))

        cfg = settings[target]

        loaded[target] = TargetArtifacts(
            target=target,
            l1_model=joblib.load(required["l1_model"]),
            l1_calibrator=joblib.load(required["l1_calibrator"]),
            catboost_model=catboost_model,
            catboost_calibrator=joblib.load(required["catboost_calibrator"]),
            threshold=float(cfg["threshold"]),
            l1_weight=float(cfg["l1_weight"]),
            catboost_weight=float(cfg["catboost_weight"]),
            rule_weight=float(cfg.get("rule_weight", 0.0)),
        )

    bundle = InferenceBundle(
        bundle_dir=bundle_dir,
        feature_contract=contract,
        manifest=manifest,
        settings=settings,
        targets=loaded,
    )
    _BUNDLE_CACHE[cache_key] = bundle
    return bundle
