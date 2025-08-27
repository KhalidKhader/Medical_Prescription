"""
Pydantic models for system health management.
Defines data structures for health check responses and monitoring data.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    ERROR = "error"


class ComponentHealthDetails(BaseModel):
    """Health details for a specific system component"""
    status: HealthStatus = Field(description="Component health status")
    score: float = Field(ge=0.0, le=1.0, description="Health score from 0.0 to 1.0")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed health information")
    issues: List[str] = Field(default_factory=list, description="List of health issues")
    last_checked: Optional[datetime] = Field(None, description="Last health check timestamp")
    response_time_ms: Optional[float] = Field(None, description="Component response time in milliseconds")


class SystemHealthResponse(BaseModel):
    """Complete system health response"""
    status: HealthStatus = Field(description="Overall system health status")
    timestamp: datetime = Field(description="Health check timestamp")
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall system health score")
    components: Dict[str, ComponentHealthDetails] = Field(
        description="Health status for each system component"
    )
    critical_issues: List[str] = Field(
        default_factory=list, 
        description="List of critical issues requiring immediate attention"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings that should be monitored"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="List of recommended actions to improve system health"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
