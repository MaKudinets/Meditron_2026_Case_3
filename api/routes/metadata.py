from fastapi import APIRouter

from ml.inference.loader import load_inference_bundle


router = APIRouter(
    prefix="/api/v1/meta",
    tags=["Metadata"],
)


@router.get(
    "/features",
    summary="Get supported ML features",
)
def get_features():
    """
    Возвращает feature contract production ML-модели.
    """

    bundle = load_inference_bundle()

    contract = bundle.feature_contract

    return {
        "n_features": contract["n_features"],
        "features": contract["features"],
        "numeric_features": contract["numeric_features"],
        "categorical_features": contract["categorical_features"],
        "targets": contract["targets"],
    }


@router.get(
    "/model",
    summary="Get production model information",
)
def get_model_info():
    """
    Возвращает metadata текущего inference bundle.
    """

    bundle = load_inference_bundle()

    manifest = bundle.manifest

    return {
        "bundle_name": manifest.get("bundle_name"),
        "bundle_version": manifest.get("bundle_version"),
        "purpose": manifest.get("purpose"),
        "n_features": manifest.get("n_features"),
        "targets": manifest.get("targets"),
        "architecture": manifest.get("architecture"),
    }