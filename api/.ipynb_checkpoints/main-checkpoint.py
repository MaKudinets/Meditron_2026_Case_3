from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.health import router as health_router
from api.routes.predict import router as predict_router


app = FastAPI(
    title="Meditron API",
    description=(
        "API for AI screening of latent deficiency states "
        "using laboratory and demographic data."
    ),
    version="0.1.0",
)


# CORS нужен для подключения frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключаем маршруты
app.include_router(
    health_router
)

app.include_router(
    predict_router
)


@app.get(
    "/",
    tags=["Root"],
)
def root():
    """
    Базовый endpoint API.
    """

    return {
        "service": "Meditron API",
        "status": "running",
        "docs": "/docs",
    }