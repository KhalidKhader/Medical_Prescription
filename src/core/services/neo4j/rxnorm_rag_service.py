"""
RxNorm Knowledge Graph Service - Simplified Main Service
Coordinates parallel search methods for optimal drug matching
"""

import asyncio
from typing import Dict, Any, List, Optional
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.services.neo4j.orchestrator.parallel_search_orchestrator import ParallelSearchOrchestrator


class RxNormService:
    """Simplified RxNorm service coordinating parallel search methods"""
    
    def __init__(self):
        """Initialize RxNorm service with parallel search orchestrator"""
        self.driver = None
        self._initialize_driver()
        
        # Initialize parallel search orchestrator
        self.search_orchestrator = ParallelSearchOrchestrator(self.driver)

        # Statistics tracking
        self.query_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "parallel_searches": 0,
            "comprehensive_matches": 0
        }
    
    def _initialize_driver(self):
        """Initialize Neo4j driver"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_lifetime=settings.neo4j_max_connection_lifetime,
                max_connection_pool_size=settings.neo4j_max_connections,
                connection_timeout=settings.neo4j_connection_timeout
            )
            logger.info("Neo4j RxNorm driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            raise

    async def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            await self.driver.close()

# Global RxNorm service instance
rxnorm_service = RxNormService()
