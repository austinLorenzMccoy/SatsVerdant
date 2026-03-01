from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, submissions, validators, rewards, stats

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(validators.router, prefix="/validators", tags=["validators"])
api_router.include_router(rewards.router, prefix="/rewards", tags=["rewards"])
api_router.include_router(stats.router, prefix="/stats", tags=["statistics"])
