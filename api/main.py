from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.metadata import router as metadata_router
from api.routes.health import router as health_router
from api.routes.screenings import router as screenings_router


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


app.include_router(health_router)
app.include_router(screenings_router)
app.include_router(metadata_router)

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