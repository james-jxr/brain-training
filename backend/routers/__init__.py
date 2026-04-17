from backend.routers.auth import router as auth_router
from backend.routers.baseline import router as baseline_router
from backend.routers.sessions import router as sessions_router
from backend.routers.progress import router as progress_router
from backend.routers.lifestyle import router as lifestyle_router
from backend.routers.account import router as account_router
from backend.routers.feedback import router as feedback_router
from backend.routers.adaptive_baseline import router as adaptive_baseline_router

__all__ = [
    "auth_router",
    "baseline_router",
    "sessions_router",
    "progress_router",
    "lifestyle_router",
    "account_router",
    "feedback_router",
    "adaptive_baseline_router",
]
