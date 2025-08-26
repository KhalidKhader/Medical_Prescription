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


class ComponentHealthResponse(BaseModel):
    """Health response for a single component"""
    component_name: str = Field(description="Name of the component")
    health_details: ComponentHealthDetails = Field(description="Component health details")
    timestamp: datetime = Field(description="Health check timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GeminiHealthDetails(BaseModel):
    """Specific health details for Gemini API"""
    api_key_configured: bool = Field(description="Whether API key is configured")
    vision_model_available: bool = Field(description="Whether vision model is available")
    task_model_available: bool = Field(description="Whether task model is available")
    models_configured: Dict[str, str] = Field(description="Configured model names")
    vision_model_test: Optional[str] = Field(None, description="Vision model test result")
    api_response_time_ms: Optional[float] = Field(None, description="API response time")


class Neo4jHealthDetails(BaseModel):
    """Specific health details for Neo4j RxNorm database"""
    connection_established: bool = Field(description="Whether connection is established")
    database_accessible: bool = Field(description="Whether database is accessible")
    node_count: Optional[int] = Field(None, description="Number of nodes in database")
    query_response_time_ms: Optional[float] = Field(None, description="Query response time")
    configuration: Dict[str, str] = Field(description="Database configuration details")


class LangFuseHealthDetails(BaseModel):
    """Specific health details for LangFuse observability"""
    handler_available: bool = Field(description="Whether LangFuse handler is available")
    keys_configured: bool = Field(description="Whether API keys are configured")
    tracing_test: Optional[str] = Field(None, description="Tracing functionality test result")
    host_configured: str = Field(description="Configured LangFuse host")


class AgentHealthDetails(BaseModel):
    """Specific health details for AI agents"""
    agent_status: Dict[str, str] = Field(description="Status of each agent")
    healthy_agents_count: int = Field(description="Number of healthy agents")
    total_agents_count: int = Field(description="Total number of agents")
    health_ratio: float = Field(ge=0.0, le=1.0, description="Ratio of healthy agents")


class StorageHealthDetails(BaseModel):
    """Specific health details for storage system"""
    write_permissions: bool = Field(description="Whether write permissions are available")
    disk_space: Dict[str, Any] = Field(description="Disk space information")
    temp_directory_accessible: bool = Field(description="Whether temp directory is accessible")


class HealthCheckRequest(BaseModel):
    """Request model for health checks"""
    components: Optional[List[str]] = Field(
        None,
        description="Specific components to check (if None, check all)"
    )
    include_details: bool = Field(
        True,
        description="Whether to include detailed health information"
    )
    timeout_seconds: Optional[int] = Field(
        30,
        description="Timeout for health checks in seconds"
    )


class HealthMetrics(BaseModel):
    """Health metrics for monitoring and alerting"""
    component_name: str = Field(description="Name of the component")
    metric_name: str = Field(description="Name of the metric")
    metric_value: float = Field(description="Metric value")
    metric_unit: str = Field(description="Unit of measurement")
    timestamp: datetime = Field(description="Metric timestamp")
    tags: Dict[str, str] = Field(default_factory=dict, description="Metric tags")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthAlert(BaseModel):
    """Health alert model for critical issues"""
    alert_id: str = Field(description="Unique alert identifier")
    component_name: str = Field(description="Component that triggered the alert")
    alert_level: str = Field(description="Alert level (critical, warning, info)")
    message: str = Field(description="Alert message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Alert details")
    timestamp: datetime = Field(description="Alert timestamp")
    resolved: bool = Field(False, description="Whether the alert has been resolved")
    resolution_timestamp: Optional[datetime] = Field(None, description="Resolution timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthTrend(BaseModel):
    """Health trend data for monitoring system performance over time"""
    component_name: str = Field(description="Component name")
    metric_name: str = Field(description="Metric name")
    time_period: str = Field(description="Time period (hourly, daily, weekly)")
    data_points: List[Dict[str, Any]] = Field(description="Time series data points")
    trend_direction: str = Field(description="Trend direction (improving, stable, declining)")
    average_value: float = Field(description="Average value over the time period")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemMaintenanceStatus(BaseModel):
    """System maintenance status"""
    maintenance_mode: bool = Field(False, description="Whether system is in maintenance mode")
    maintenance_start: Optional[datetime] = Field(None, description="Maintenance start time")
    maintenance_end: Optional[datetime] = Field(None, description="Planned maintenance end time")
    maintenance_reason: Optional[str] = Field(None, description="Reason for maintenance")
    affected_components: List[str] = Field(
        default_factory=list,
        description="List of components affected by maintenance"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
