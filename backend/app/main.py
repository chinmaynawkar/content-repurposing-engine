"""Content Repurposing API - FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="Content Repurposing API",
    description="AI-powered API to repurpose long-form content into LinkedIn, Twitter, Instagram, and more.",
    version="0.1.0",
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint returning API identification."""
    return {"msg": "Content Repurposing API"}


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "ok"}
