"""
Medical Prescription AI APIs - Main Application Entry Point.
Simplified version with only health and upload APIs.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.settings.config import settings
from src.core.settings.logging import logger

# Import only the essential routers
from src.modules.system_health_management.router import router as health_router
from src.modules.prescriptions_management.router import router as prescriptions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Medical Prescription AI APIs")
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Medical Prescription AI APIs")


# Create FastAPI application
app = FastAPI(
    title="Medical Prescription AI APIs",
    description="AI-powered medical prescription analysis using Gemini 2.5 Pro and RxNorm KG",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only essential routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(prescriptions_router, prefix="/api/v1")


@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint with basic API information"""
    return {
        "message": "Medical Prescription AI APIs",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health/"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True, #settings.debug,
        log_level=settings.log_level.lower()
    )

