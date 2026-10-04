from api.routes.auth import router as auth_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.metadata import router as metadata_router
from api.routes.health import router as health_router
from api.routes.screenings import router as screenings_router
from api.routes.history import (
    router as history_router,
)
from api.routes.imports import (
    router as imports_router,
)
from api.routes.trends import (
    router as trends_router,
)
from api.routes.doctor_imports import (
    router as doctor_imports_router,
)
from api.routes.doctor_screenings import (
    router as doctor_screenings_router,
)
from api.routes.doctor_patients import (
    router as doctor_patients_router,
)
app = FastAPI(
    title="Meditron API",
    description=(
        "API for AI screening of latent deficiency states "
        "using laboratory and demographic data."
    ),
    version="0.1.0",
)


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
app.include_router(doctor_patients_router)
app.include_router(doctor_screenings_router)
app.include_router(doctor_imports_router)
app.include_router(trends_router)
app.include_router(imports_router)
app.include_router(history_router)
app.include_router(health_router)
app.include_router(screenings_router)
app.include_router(metadata_router)
app.include_router(auth_router)
@app.get(
    "/",
    tags=["Root"],
)
def root():
    return {
        "service": "Meditron API",
        "status": "running",
        "docs": "/docs",
    }