from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.bundle import router as bundle_router
from app.api.routes.court_intelligence import router as court_intelligence_router
from app.api.routes.documents import router as documents_router
from app.api.routes.drafting import router as drafting_router
from app.api.routes.health import router as health_router
from app.api.routes.institutional import router as institutional_router
from app.api.routes.matters import router as matters_router
from app.api.routes.research import router as research_router
from app.api.routes.strategy import router as strategy_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(matters_router, prefix="/matters", tags=["matters"])
api_router.include_router(bundle_router, prefix="/matters", tags=["bundle"])
api_router.include_router(court_intelligence_router, tags=["court-intelligence"])
api_router.include_router(drafting_router, prefix="/drafting", tags=["drafting"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(institutional_router, prefix="/institutional", tags=["institutional"])
api_router.include_router(research_router, prefix="/research", tags=["research"])
api_router.include_router(strategy_router, prefix="/strategy", tags=["strategy"])
