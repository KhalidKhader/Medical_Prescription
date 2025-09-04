from typing import Dict, Any
from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.services.neo4j.test_connection.queries import (
    HEALTH_CHECK_QUERY,
    SAMPLE_DRUG_QUERY,
)
from src.core.services.neo4j.rxnorm_rag_service import RxNormService

client = RxNormService()

async def rx_norm_test_connection() -> Dict[str, Any]:
    """Test Neo4j connection and RxNorm data availability"""
    try:
        async with client.driver.session(database=settings.neo4j_database) as session:
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
                "query_stats": client.query_stats
            }
            
    except Exception as e:
        logger.error(f"Neo4j connection test failed: {e}")
        return {"connected": False, "error": str(e)}