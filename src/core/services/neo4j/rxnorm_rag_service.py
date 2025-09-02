"""
RxNorm Knowledge Graph Service - Simplified Main Service
Coordinates parallel search methods for optimal drug matching
"""

import asyncio
from typing import Dict, Any, List, Optional
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .parallel_search_orchestrator import ParallelSearchOrchestrator
from .queries import (
    HEALTH_CHECK_QUERY,
    SAMPLE_DRUG_QUERY,
    DRUG_DETAILS_QUERY
)


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

    async def test_connection(self) -> Dict[str, Any]:
        """Test Neo4j connection and RxNorm data availability"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                # Test basic connection
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                
                if not record or record["test"] != 1:
                    return {"connected": False, "error": "Basic connection test failed"}
                
                # Check RxNorm data
                health_result = await session.run(HEALTH_CHECK_QUERY)
                health_record = await health_result.single()
                
                if not health_record:
                    return {"connected": True, "rxnorm_available": False, "error": "No RxNorm data found"}
                
                # Get sample drug
                sample_result = await session.run(SAMPLE_DRUG_QUERY)
                sample_records = await sample_result.fetch(1)
                sample_record = sample_records[0] if sample_records else None
                
                sample_drug = None
                if sample_record:
                    sample_drug = {
                        "concept_id": sample_record["concept_id"],
                        "drug_name": sample_record["drug_name"],
                        "strength": sample_record.get("strength"),
                        "route": sample_record.get("route")
                    }
                
                return {
                    "connected": True,
                    "database": settings.neo4j_database,
                    "uri": settings.neo4j_uri,
                    "rxnorm_available": True,
                    "parallel_search_enabled": True,
                    "database_stats": {
                        "total_concepts": health_record["total_concepts"],
                        "total_attributes": health_record["total_attributes"],
                        "total_sources": health_record["total_sources"],
                        "total_semantic_types": health_record["total_semantic_types"]
                    },
                    "sample_drug": sample_drug,
                    "query_stats": self.query_stats
                }
                
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return {"connected": False, "error": str(e)}

    async def get_comprehensive_drug_info(self, drug_name: str, strength: str = None, instructions: str = None, context: Dict[str, Any] = None, safety_assessment: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Comprehensive drug search using parallel orchestrator with all context"""
        try:
            logger.info(f"🔍 Comprehensive parallel search for: '{drug_name}', strength: '{strength or 'N/A'}', instructions: '{instructions or 'N/A'}'")

            self.query_stats["total_queries"] += 1
            
            # Use parallel search orchestrator with all context
            all_results = await self.search_orchestrator.comprehensive_parallel_search(
                drug_name=drug_name,
                strength=strength,
                instructions=instructions,
                safety_context=safety_assessment,
                limit_per_method=5
            )

            if all_results:
                # Deduplicate and merge results
                merged_results = self.search_orchestrator.deduplicate_and_merge_results(all_results)
                
                # Calculate comprehensive scores with all context
                scored_results = self.search_orchestrator.calculate_comprehensive_scores(
                    merged_results, drug_name, strength, instructions, safety_assessment
                )
                
                self.query_stats["successful_queries"] += 1
                self.query_stats["comprehensive_matches"] += 1
                logger.info(f"✅ Comprehensive search found {len(scored_results)} matches for '{drug_name}'")
                return scored_results[:10]  # Return top 10 matches for better selection
            else:
                logger.warning(f"❌ No matches found for '{drug_name}' in comprehensive search")
                return []

        except Exception as e:
            logger.error(f"Comprehensive drug search failed: {e}")
            return []
    
    async def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            await self.driver.close()

# Global RxNorm service instance
rxnorm_service = RxNormService()
