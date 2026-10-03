from fastapi import APIRouter


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
    Проверяет, что FastAPI-приложение
    запущено и отвечает на запросы.
    """

    return {
        "status": "ok"
    }