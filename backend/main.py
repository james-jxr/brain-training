from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db, settings
from backend.routers import (
    auth_router,
    baseline_router,
    sessions_router,
    progress_router,
    lifestyle_router,
    account_router,
    feedback_router,
    adaptive_baseline_router,
)

app = FastAPI(title="Brain Training API")

init_db()

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(baseline_router)
app.include_router(adaptive_baseline_router)
app.include_router(sessions_router)
app.include_router(progress_router)
app.include_router(lifestyle_router)
app.include_router(account_router)
app.include_router(feedback_router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
