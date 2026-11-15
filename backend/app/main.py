
from fastapi import FastAPI
from backend.app.api.jobs import router as jobs_router

app = FastAPI(
    title="HireSense API",
    description="AI-Powered Resume Matching and Candidate Ranking System",
    version="1.0.0"
)

app.include_router(jobs_router)

@app.get("/")
def root():
    return {
        "application": "HireSense",
        "message": "Welcome to HireSense API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "HireSense"
    }
