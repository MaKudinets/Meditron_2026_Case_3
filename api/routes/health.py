from fastapi import APIRouter

from expert.engine import DURABLE_AVAILABLE
from ml.inference.loader import load_inference_bundle


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    summary="Check API health",
)
def health_check():
    """
    Проверяет состояние:
    - FastAPI
    - ML inference bundle
    - expert engine
    """

    ml_bundle_loaded = False
    bundle_version = None

    try:
        bundle = load_inference_bundle()

        ml_bundle_loaded = True
        bundle_version = bundle.manifest.get(
            "bundle_version"
        )

    except Exception:
        ml_bundle_loaded = False

    status = (
        "ok"
        if ml_bundle_loaded and DURABLE_AVAILABLE
        else "degraded"
    )

    return {
        "status": status,
        "api": "ok",
        "ml_bundle_loaded": ml_bundle_loaded,
        "expert_engine_available": DURABLE_AVAILABLE,
        "bundle_version": bundle_version,
    }