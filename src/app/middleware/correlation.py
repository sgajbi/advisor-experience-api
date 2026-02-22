from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def resolve_correlation_id(request: Request) -> str:
    incoming = request.headers.get("X-Correlation-Id")
    return incoming if incoming else f"corr_{uuid4().hex[:12]}"


async def correlation_middleware(request: Request, call_next):
    correlation_id = resolve_correlation_id(request)
    token = correlation_id_var.set(correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    correlation_id_var.reset(token)
    return response
