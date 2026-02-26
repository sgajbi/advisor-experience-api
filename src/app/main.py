from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.contracts.errors import ProblemDetails
from app.enterprise_readiness import build_enterprise_audit_middleware, validate_enterprise_runtime_config
from app.middleware.correlation import correlation_id_var, correlation_middleware, setup_logging
from app.routers.intake import router as intake_router
from app.routers.platform import router as platform_router
from app.routers.proposals import router as proposals_router
from app.routers.reporting import router as reporting_router
from app.routers.workbench import router as workbench_router


@asynccontextmanager
async def _app_lifespan(application: FastAPI):
    application.state.is_draining = False
    yield
    application.state.is_draining = True


app = FastAPI(title="Advisor Experience API", version="0.1.0", lifespan=_app_lifespan)
setup_logging()
validate_enterprise_runtime_config()
app.middleware("http")(correlation_middleware)
app.middleware("http")(build_enterprise_audit_middleware("advisor-experience-api"))
Instrumentator().instrument(app).expose(app)
app.include_router(proposals_router)
app.include_router(platform_router)
app.include_router(intake_router)
app.include_router(workbench_router)
app.include_router(reporting_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
async def health_ready(response: Response) -> dict[str, str]:
    if bool(getattr(app.state, "is_draining", False)):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "draining"}
    return {"status": "ready"}


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
