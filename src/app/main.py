from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.contracts.errors import ProblemDetails
from app.middleware.correlation import correlation_id_var, correlation_middleware
from app.routers.platform import router as platform_router
from app.routers.proposals import router as proposals_router

app = FastAPI(title="Advisor Experience API", version="0.1.0")
app.middleware("http")(correlation_middleware)
app.include_router(proposals_router)
app.include_router(platform_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    problem = ProblemDetails(
        title="Internal Server Error",
        status=500,
        detail="An unexpected error occurred.",
        instance=str(request.url.path),
        correlation_id=correlation_id_var.get() or "",
        error_code="INTERNAL_ERROR",
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/problem+json",
        content=problem.model_dump(),
    )
