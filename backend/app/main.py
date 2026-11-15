
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from backend.app.api.jobs import router as jobs_router
from backend.app.api.resumes import router as resumes_router


app = FastAPI(
    title="HireSense API",
    description="AI-Powered Resume Matching and Candidate Ranking System",
    version="1.0.0",
)

# Register API routers
app.include_router(jobs_router)
app.include_router(resumes_router)


@app.get("/")
def root():
    return {
        "application": "HireSense",
        "message": "Welcome to HireSense API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# Fix Swagger file-upload schema compatibility
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    upload_schema = openapi_schema["components"]["schemas"].get(
        "Body_upload_resumes_api_resumes_upload_post"
    )

    if upload_schema:
        file_items = upload_schema["properties"]["files"]["items"]

        file_items.clear()
        file_items.update({
            "type": "string",
            "format": "binary",
        })

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
