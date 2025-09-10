import asyncio
from typing import Dict, Any, List, Optional
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.services.neo4j.rxnorm_rag_service import RxNormService
from src.core.services.neo4j.orchestrator.parallel_search import parallel_search
client = RxNormService()

async def get_drug_info(drug_name: str, strength: str = None, instructions: str = None, context: Dict[str, Any] = None, safety_assessment: Dict[str, Any] = None, search_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Comprehensive drug search using parallel orchestrator with all context"""
    try:
        logger.info(f"🔍 Comprehensive parallel search for: '{drug_name}', strength: '{strength or 'N/A'}', instructions: '{instructions or 'N/A'}'")

        client.query_stats["total_queries"] += 1
        
        # Use parallel search orchestrator with all context
        all_results = await parallel_search(
            drug_name=drug_name,
            strength=strength,
            instructions=instructions,
            safety_context=safety_assessment,
            limit_per_method=5,
            search_type=search_type
        )

        if all_results:
            # Deduplicate and merge results
            merged_results = client.search_orchestrator.deduplicate_and_merge_results(all_results)
            
            # Calculate comprehensive scores with all context
            scored_results = client.search_orchestrator.calculate_scores(
                merged_results, drug_name, strength, instructions, safety_assessment
            )
            
            client.query_stats["successful_queries"] += 1
            client.query_stats["comprehensive_matches"] += 1
            logger.info(f"✅ Comprehensive search found {len(scored_results)} matches for '{drug_name}'")
            return scored_results[:10]  # Return top 10 matches for better selection
        else:
            logger.warning(f"❌ No matches found for '{drug_name}' in comprehensive search")
            return []

    except Exception as e:
        logger.error(f"Comprehensive drug search failed: {e}")
        return []