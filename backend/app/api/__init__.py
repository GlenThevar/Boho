from fastapi import APIRouter
from .rules import router as rules_router
from .datasets import router as datasets_router
from .simulations import router as simulations_router
from .dashboard import router as dashboard_router
from .analysis import router as analysis_router
from .comparisons import router as comparisons_router
from .ai import router as ai_router

api_router = APIRouter()
api_router.include_router(rules_router)
api_router.include_router(datasets_router)
api_router.include_router(simulations_router)
api_router.include_router(dashboard_router)
api_router.include_router(analysis_router)
api_router.include_router(comparisons_router)
api_router.include_router(ai_router)

__all__ = ["api_router"]

