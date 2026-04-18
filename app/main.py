"""
Main FastAPI application entry point.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import APP_NAME, APP_VERSION, APP_DESCRIPTION, logger
from app.routers.api import router

# Configure logging
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info("Application initialized successfully")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {APP_NAME}")


# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint returning application info."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "documentation": "/docs",
        "alternative_docs": "/redoc",
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


@app.get("/api/status", tags=["status"])
async def api_status():
    """API status endpoint."""
    return {
        "api": "online",
        "endpoints": {
            "health_check": "/api/health-check",
            "load_test": "/api/load-test",
            "upload_code": "/api/upload-code",
            "analyze_github": "/api/analyze-github",
            "suggestions": "/api/suggestions",
            "report": "/api/report",
            "text_report": "/api/report/text",
            "clear_cache": "/api/cache/clear",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
