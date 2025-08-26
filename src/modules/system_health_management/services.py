"""
System Health Management Service.
Provides comprehensive health monitoring for all system components.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.core.settings.logging import logger
from src.core.settings.config import settings


class SystemHealthService:
    """
    Service for monitoring and reporting system health status.
    Checks all critical system components and external dependencies.
    """
    
    def __init__(self):
        """Initialize the system health service"""
        self.last_health_check = None
        self.health_cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
        logger.info("System health service initialized")
    
    async def get_comprehensive_health(self, include_details: bool = False) -> Dict[str, Any]:
        """Perform comprehensive health check of all system components"""
        
        logger.info("Performing comprehensive health check")
        
        # Check if we have recent cached results
        if (self.last_health_check and 
            time.time() - self.last_health_check < self.cache_ttl and 
            self.health_cache):
            logger.debug("Returning cached health check results")
            return self.health_cache
        
        # Perform health checks
        health_checks = await asyncio.gather(
            self._check_gemini_health(),
            self._check_neo4j_health(),
            self._check_langfuse_health(),
            return_exceptions=True
        )
        
        # Process results
        gemini_health, neo4j_health, langfuse_health = health_checks
        
        # Determine overall status
        overall_status = "healthy"
        overall_score = 1.0
        issues = []
        
        # Check Gemini health
        if isinstance(gemini_health, Exception):
            gemini_health = {"status": "unhealthy", "error": str(gemini_health)}
        
        if gemini_health.get("status") != "healthy":
            overall_status = "degraded"
            overall_score = min(overall_score, 0.5)
            issues.append("Gemini API issues")
        
        # Check Neo4j health
        if isinstance(neo4j_health, Exception):
            neo4j_health = {"status": "unhealthy", "error": str(neo4j_health)}
        
        if neo4j_health.get("status") != "healthy":
            overall_status = "degraded"
            overall_score = min(overall_score, 0.5)
            issues.append("Neo4j database issues")
        
        # Check LangFuse health
        if isinstance(langfuse_health, Exception):
            langfuse_health = {"status": "unhealthy", "error": str(langfuse_health)}
        
        if langfuse_health.get("status") != "healthy":
            # LangFuse issues don't affect overall health as much
            if overall_status == "healthy":
                overall_status = "degraded"
                overall_score = min(overall_score, 0.8)
            issues.append("LangFuse observability issues")
        
        # Build response
        health_result = {
            "status": overall_status,
            "score": overall_score,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "services": {
                "gemini": gemini_health,
                "neo4j": neo4j_health,
                "langfuse": langfuse_health
            },
            "issues": issues
        }
        
        # Add details if requested
        if include_details:
            health_result["details"] = {
                "gemini_details": gemini_health,
                "neo4j_details": neo4j_health,
                "langfuse_details": langfuse_health
            }
        
        # Cache results
        self.health_cache = health_result
        self.last_health_check = time.time()
        
        logger.info(f"Comprehensive health check completed: {overall_status}")
        
        return health_result
    
    async def get_component_health(self, component: str) -> Dict[str, Any]:
        """Get health status for a specific component"""
        
        try:
            if component == "gemini":
                return await self._check_gemini_health()
            elif component == "neo4j":
                return await self._check_neo4j_health()
            elif component == "langfuse":
                return await self._check_langfuse_health()
            else:
                return {
                    "status": "unknown",
                    "error": f"Unknown component: {component}",
                    "score": 0.0
                }
        except Exception as e:
            logger.error(f"Error checking {component} health: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "score": 0.0
            }
    
    async def _check_gemini_health(self) -> Dict[str, Any]:
        """Check Google Gemini API health with Gemini 2.5 Pro"""
        try:
            logger.debug("Checking Gemini API health")
            
            from src.core.services.gemini.gemini import gemini_service
            
            health_result = {
                "status": "healthy",
                "score": 1.0,
                "details": {},
                "issues": []
            }
            
            # Test new client and legacy models
            model_tests = {}
            models_to_test = [
                ("primary", "gemini-2.5-pro", "Primary vision model"),
                ("secondary", "gemini-2.5-pro", "Secondary task model"), 
                ("fallback", "gemini-2.5-pro", "Fallback model")
            ]
            
            healthy_models = 0
            total_models = len(models_to_test)
            
            # Test new client first
            if gemini_service.use_new_client and gemini_service.new_client:
                try:
                    new_client_results = await gemini_service.new_client.test_connection()
                    health_result["details"]["new_client"] = new_client_results
                    health_result["details"]["new_client_available"] = True
                    
                    # Count healthy models from new client
                    for model_type, model_name, description in models_to_test:
                        if model_type in new_client_results:
                            model_result = new_client_results[model_type]
                            if model_result.get("available", False):
                                healthy_models += 1
                                model_tests[model_type] = {
                                    "status": "healthy",
                                    "model": model_name,
                                    "description": description
                                }
                            else:
                                model_tests[model_type] = {
                                    "status": "unhealthy",
                                    "model": model_name,
                                    "description": description,
                                    "error": model_result.get("error", "Model not available")
                                }
                                health_result["issues"].append(f"{description} unavailable")
                        else:
                            model_tests[model_type] = {
                                "status": "unknown",
                                "model": model_name,
                                "description": description,
                                "error": "Model not tested"
                            }
                            health_result["issues"].append(f"{description} not tested")
                    
                except Exception as e:
                    logger.warning(f"New client health check failed: {str(e)}")
                    health_result["details"]["new_client"] = {"error": str(e)}
                    health_result["details"]["new_client_available"] = False
                    health_result["issues"].append("New client unavailable")
            
            # Test legacy models if new client failed or for additional coverage
            if healthy_models == 0:
                try:
                    legacy_results = await gemini_service.models.test_all_models()
                    health_result["details"]["legacy_models"] = legacy_results
                    
                    # Count healthy legacy models
                    for model_type, model_name, description in models_to_test:
                        if model_type in legacy_results:
                            model_result = legacy_results[model_type]
                            if model_result.get("available", False):
                                healthy_models += 1
                                if model_type not in model_tests:
                                    model_tests[model_type] = {
                                        "status": "healthy",
                                        "model": model_name,
                                        "description": description,
                                        "source": "legacy"
                                    }
                            else:
                                if model_type not in model_tests:
                                    model_tests[model_type] = {
                                        "status": "unhealthy",
                                        "model": model_name,
                                        "description": description,
                                        "error": model_result.get("error", "Model not available"),
                                        "source": "legacy"
                                    }
                                    health_result["issues"].append(f"{description} unavailable (legacy)")
                    
                except Exception as e:
                    logger.warning(f"Legacy models health check failed: {str(e)}")
                    health_result["details"]["legacy_models"] = {"error": str(e)}
                    health_result["issues"].append("Legacy models unavailable")
            
            # Calculate overall Gemini health
            if healthy_models == 0:
                health_result["status"] = "unhealthy"
                health_result["score"] = 0.0
                health_result["issues"].append("No Gemini models available")
            elif healthy_models < total_models:
                health_result["status"] = "degraded"
                health_result["score"] = healthy_models / total_models
                health_result["issues"].append(f"Only {healthy_models}/{total_models} models available")
            
            health_result["details"]["model_tests"] = model_tests
            health_result["details"]["healthy_models"] = healthy_models
            health_result["details"]["total_models"] = total_models
            
            return health_result
            
        except Exception as e:
            logger.error(f"Gemini health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "score": 0.0,
                "error": str(e),
                "issues": ["Gemini health check failed"]
            }
    
    async def _check_neo4j_health(self) -> Dict[str, Any]:
        """Check Neo4j RxNorm health"""
        try:
            logger.debug("Checking Neo4j RxNorm health")
            
            from src.core.services.neo4j.rxnorm_rag_service import rxnorm_service
            
            health_result = {
                "status": "healthy",
                "score": 1.0,
                "details": {},
                "issues": []
            }
            
            # Test Neo4j connection
            connection_test = await rxnorm_service.test_connection()
            
            if connection_test.get("connected", False):
                health_result["details"]["connection"] = connection_test
                health_result["details"]["database_stats"] = connection_test.get("database_stats", {})
                health_result["details"]["sample_drug"] = connection_test.get("sample_drug")
                
                # Check if RxNorm data is available
                if not connection_test.get("rxnorm_available", False):
                    health_result["status"] = "degraded"
                    health_result["score"] = 0.5
                    health_result["issues"].append("RxNorm data not available")
                
                # Check LangFuse connection
                if not connection_test.get("langfuse_connected", False):
                    health_result["issues"].append("LangFuse connection failed")
                
            else:
                health_result["status"] = "unhealthy"
                health_result["score"] = 0.0
                health_result["error"] = connection_test.get("error", "Unknown connection error")
                health_result["issues"].append("Neo4j connection failed")
            
            return health_result
            
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "score": 0.0,
                "error": str(e),
                "issues": ["Neo4j health check failed"]
            }
    
    async def _check_langfuse_health(self) -> Dict[str, Any]:
        """Check LangFuse health"""
        try:
            logger.debug("Checking LangFuse health")
            
            from langfuse import Langfuse
            
            health_result = {
                "status": "healthy",
                "score": 1.0,
                "details": {},
                "issues": []
            }
            
            # Test LangFuse connection
            langfuse = Langfuse(
                secret_key=settings.langfuse_secret_key,
                public_key=settings.langfuse_public_key,
                host=settings.langfuse_host
            )
            
            try:
                # Try to create a test event
                langfuse.create_event(
                    name="health_check",
                    input={"test": True, "timestamp": datetime.utcnow().isoformat()}
                )
                
                health_result["details"]["connection"] = "successful"
                health_result["details"]["host"] = settings.langfuse_host
                
            except Exception as e:
                health_result["status"] = "unhealthy"
                health_result["score"] = 0.0
                health_result["error"] = str(e)
                health_result["issues"].append("LangFuse connection failed")
            
            return health_result
            
        except Exception as e:
            logger.error(f"LangFuse health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "score": 0.0,
                "error": str(e),
                "issues": ["LangFuse health check failed"]
            }
    

