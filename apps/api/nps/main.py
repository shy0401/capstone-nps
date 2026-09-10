import json
import logging
import time
from uuid import UUID, uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from nps.config import settings
from nps.errors import DomainError
from nps.api import router
from nps.work_api import router as work_router, ws_router
from nps.artifacts import router as artifact_router
from nps.auth import audit_correlation

app = FastAPI(title="연금술사 Prototype API", version="0.1.2", openapi_version="3.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Correlation-ID"],
)
app.include_router(router)
app.include_router(work_router)
app.include_router(ws_router)
app.include_router(artifact_router)


@app.middleware("http")
async def correlation(request: Request, call_next):
    try:
        correlation_id = str(UUID(request.headers.get("X-Correlation-ID", "")))
    except ValueError:
        correlation_id = str(uuid4())
    request.state.correlation_id = correlation_id
    audit_correlation.set(correlation_id)
    start = time.monotonic()
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    # Never log URI, query, headers or request/response bodies.
    logging.getLogger("nps").info(
        json.dumps(
            {
                "correlation_id": correlation_id,
                "method": request.method,
                "status": response.status_code,
                "elapsed_ms": round((time.monotonic() - start) * 1000),
            }
        )
    )
    return response


@app.exception_handler(DomainError)
async def domain_error(request, exc):
    return JSONResponse(
        status_code=exc.status,
        content={
            "error": {"code": exc.code, "message": exc.code, "correlation_id": request.state.correlation_id}
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "CONTRACT_INVALID",
                "message": "입력 형식을 확인하세요.",
                "correlation_id": request.state.correlation_id,
            }
        },
    )


@app.get("/api/v1/health/live")
def live():
    return {"status": "alive", "version": "0.1.2"}


@app.get("/api/v1/health/ready")
def ready():
    from nps.db import engine
    import redis
    import httpx

    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        redis.Redis.from_url(settings().redis_url, socket_connect_timeout=2, socket_timeout=2).ping()
        for url in (settings().llm_adapter_url, settings().comfy_adapter_url):
            httpx.get(f"{url}/health", timeout=2, trust_env=False).raise_for_status()
        return {"status": "ready"}
    except Exception:
        raise DomainError("DEPENDENCY_UNAVAILABLE", 503) from None
