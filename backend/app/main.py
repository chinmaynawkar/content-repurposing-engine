"""Content Repurposing API - FastAPI application entry point."""

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import configure_logging, get_logger

# Configure logging before first log (must run before get_logger in routers/services)
configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown lifecycle."""
    log.info("application_startup", version="0.1.0")
    yield
    log.info("application_shutdown")


app = FastAPI(
    title="Content Repurposing API",
    description="AI-powered API to repurpose long-form content into LinkedIn, Twitter, Instagram, and more.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log each request with method, path, status, duration, and client IP."""
    start = time.perf_counter()
    client_host = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    log.info(
        "request_completed",
        method=method,
        path=path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
        client_ip=client_host,
    )
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint returning API identification."""
    return {"msg": "Content Repurposing API"}


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "ok"}


@app.get("/api/health", tags=["Health"])
async def api_health():
    """Health check for frontend integration."""
    return {"status": "healthy", "message": "All systems operational"}
