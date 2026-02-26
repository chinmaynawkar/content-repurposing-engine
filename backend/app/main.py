"""Content Repurposing API - FastAPI application entry point."""

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine, get_db
from app.logging_config import configure_logging, get_logger
from app.routers import content, generate

# Configure logging before first log (must run before get_logger in routers/services)
configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown lifecycle."""
    log.info("application_startup", version="0.1.0")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    log.info("application_shutdown")


app = FastAPI(
    title="Content Repurposing API",
    description="AI-powered API to repurpose long-form content into LinkedIn, Twitter, Instagram, and more.",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow both localhost and 127.0.0.1 so CORS works whether user opens app via localhost:5173 or 127.0.0.1:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5174",
    ],
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


app.include_router(content.router)
app.include_router(generate.router)


@app.get("/api/health", tags=["Health"])
async def api_health(db: AsyncSession = Depends(get_db)):
    """Health check with DB connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "message": "All systems operational"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "detail": str(e)}
