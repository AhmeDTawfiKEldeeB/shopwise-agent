from fastapi import APIRouter

from src.api.routes.base import router as base_router
from src.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(base_router)
api_router.include_router(health_router)

__all__ = ["api_router"]