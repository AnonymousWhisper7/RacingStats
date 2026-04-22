from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.config import router as config_router
from app.api.routes.health import router as health_router
from app.api.routes.telemetry import router as telemetry_router
from app.api.routes.tracks import router as tracks_router

app = FastAPI(title="LMU Racing Coach API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(config_router)
app.include_router(telemetry_router)
app.include_router(tracks_router)
