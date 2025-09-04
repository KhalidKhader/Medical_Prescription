"""
System Health Checker
Monitors health of all system components and external services
"""

import asyncio
import psutil
from typing import Dict, Any, List
from datetime import datetime
from src.core.settings.logging import logger
from src.core.services.gemini.test_connection import gemini_test_connection
from src.core.services.neo4j.rxnorm_rag_service import rxnorm_service
from src.core.settings.observability import AuditLogger
from src.core.settings.threading import global_performance_monitor, global_cache
from src.core.services.neo4j.test_connection.test_connection import rx_norm_test_connection


class SystemHealthChecker:
    """Comprehensive system health monitoring"""
    
    def __init__(self):
        """Initialize health checker"""
        self.audit_logger = AuditLogger()
        logger.info("System health checker initialized")
    
    async def handle_comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Handle comprehensive health check request
        
        Returns:
            Comprehensive health report
        """
        return await self.check_all_services()
    
    async def check_all_services(self) -> Dict[str, Any]:
        """
        Check health of all system services
        
        Returns:
            Comprehensive health report
        """
        logger.info("Starting comprehensive health check")
        
        health_checks = await asyncio.gather(
            self.check_gemini_health(),
            self.check_neo4j_health(),
            self.check_langfuse_health(),
            self.check_system_resources(),
            return_exceptions=True
        )
        
        gemini_health, neo4j_health, langfuse_health, system_health = health_checks
        
        # Calculate overall health
        overall_status = self._calculate_overall_status([
            gemini_health, neo4j_health, langfuse_health, system_health
        ])
        
        # Get performance metrics
        performance_stats = global_performance_monitor.get_stats()
        cache_stats = global_cache.get_stats()
        
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "services": {
                "gemini": gemini_health,
                "neo4j_rxnorm": neo4j_health,
                "langfuse": langfuse_health,
                "system": system_health
            },
            "performance": {
                "metrics": performance_stats,
                "cache": cache_stats,
                "optimizations": {
                    "parallel_processing": "enabled",
                    "circuit_breakers": "enabled",
                    "caching": "enabled",
                    "performance_tracking": "enabled"
                }
            }
        }
        
        logger.info(f"Health check completed - Overall status: {overall_status}")
        return health_report
    
    async def check_gemini_health(self) -> Dict[str, Any]:
        """Check Google Gemini API health"""
        try:
            logger.info("Checking Gemini API health")
            
            health_data = await gemini_test_connection()
            
            # Extract status from health data
            status = health_data.get("status", "unhealthy")
            
            # Additional validation: if test_passed is False, mark as unhealthy
            if health_data.get("test_passed") is False:
                status = "unhealthy"
            
            return {
                "service": "Google Gemini API",
                "status": status,
                "details": health_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return {
                "service": "Google Gemini API",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_neo4j_health(self) -> Dict[str, Any]:
        """Check Neo4j RxNorm database health"""
        try:
            logger.info("Checking Neo4j RxNorm health")
            
            health_data = await rx_norm_test_connection()
            
            return {
                "service": "Neo4j RxNorm Database",
                "status": "healthy" if health_data.get("connected") else "unhealthy",
                "details": health_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return {
                "service": "Neo4j RxNorm Database",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_langfuse_health(self) -> Dict[str, Any]:
        """Check LangFuse observability service health"""
        try:
            logger.info("Checking LangFuse health")
            
            # Test LangFuse connection by attempting to log an event
            self.audit_logger.log_agent_execution(
                agent_name="health_check",
                execution_time=0.1,
                success=True
            )
            
            return {
                "service": "LangFuse Observability",
                "status": "healthy",
                "details": {
                    "connected": True,
                    "test_event_logged": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LangFuse health check failed: {e}")
            return {
                "service": "LangFuse Observability",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource health"""
        try:
            logger.info("Checking system resources")
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine health status
            status = "healthy"
            warnings = []
            
            if cpu_percent > 80:
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 85:
                status = "warning"
                warnings.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                status = "critical"
                warnings.append(f"High disk usage: {disk.percent}%")
            
            return {
                "service": "System Resources",
                "status": status,
                "details": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "warnings": warnings
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except ImportError:
            return {
                "service": "System Resources",
                "status": "unknown",
                "error": "psutil not available for system monitoring",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                "service": "System Resources",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_overall_status(self, health_checks: List[Dict[str, Any]]) -> str:
        """
        Calculate overall system health status
        
        Args:
            health_checks: List of individual service health checks
            
        Returns:
            Overall status: "healthy", "warning", "critical", or "unhealthy"
        """
        statuses = []
        
        for check in health_checks:
            if isinstance(check, dict):
                status = check.get("status", "unknown")
                statuses.append(status)
        
        # Determine overall status
        if "critical" in statuses or "unhealthy" in statuses:
            return "unhealthy"
        elif "warning" in statuses:
            return "warning"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "unknown"