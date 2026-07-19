import uvicorn
from app.api.v1.routes.auth import router as auth_router
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

app = FastAPI(
    title="CodePilotAI Backend",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.include_router(auth_router)


@app.get("/scalar", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
