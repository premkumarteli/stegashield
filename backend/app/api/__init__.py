"""API router aggregating all v1 route endpoints."""

from fastapi import APIRouter

from app.api.attack_lab import router as attack_lab_router
from app.api.files import router as files_router
from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.stego import router as stego_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(stego_router)
api_router.include_router(attack_lab_router)
api_router.include_router(history_router)
api_router.include_router(files_router)

__all__ = ["api_router"]
