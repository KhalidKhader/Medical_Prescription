"""
System Health Router
FastAPI router for health monitoring endpoints
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from .handlers import SystemHealthChecker

# Create router instance
router = APIRouter(prefix="/health", tags=["health"])

# Dependency to get health handler
def get_health_handler() -> SystemHealthChecker:
    """Get system health handler instance"""
    return SystemHealthChecker()


@router.get(
    "/",
    summary="Comprehensive health check",
    description="Get comprehensive health status of all system components"
)
async def comprehensive_health_check(
    handler: SystemHealthChecker = Depends(get_health_handler)
) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint
    
    Returns:
        Complete system health report including all services
    """
    return await handler.handle_comprehensive_health_check()
