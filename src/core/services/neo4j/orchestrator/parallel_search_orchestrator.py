"""
Parallel Search Orchestrator
Coordinates all search methods in parallel for optimal performance
"""

import asyncio
from typing import Dict, Any, List, Optional
from src.core.settings.logging import logger
from src.core.services.neo4j.search.exact_match_search.search import ExactMatchSearchService
from src.core.services.neo4j.search.fuzzy_match_search.search import FuzzyMatchSearchService
from src.core.services.neo4j.search.embedding_search.search import EmbeddingSearchService
from src.core.services.neo4j.search.brand_search.search import BrandSearchService
from src.core.services.neo4j.search.synonym_search.search import SynonymSearchService
from src.core.services.neo4j.search.instruction_search.search import InstructionSearchService
from src.core.services.neo4j.search.strength_instruction_search.search import StrengthInstructionSearchService
from src.core.services.neo4j.orchestrator.deduplicate_and_merge_results import deduplicate_and_merge_results
from src.core.services.neo4j.orchestrator.calculate_scores import calculate_scores

class ParallelSearchOrchestrator:
    """Orchestrates parallel drug searches across all search methods"""
    
    def __init__(self, driver):
        self.driver = driver
        
        # Initialize all search services
        self.exact_search = ExactMatchSearchService()
        self.fuzzy_search = FuzzyMatchSearchService()
        self.embedding_search = EmbeddingSearchService()
        self.brand_search = BrandSearchService()
        self.synonym_search = SynonymSearchService()
        self.instruction_search = InstructionSearchService()
        self.strength_instruction_search = StrengthInstructionSearchService()
        self.deduplicate_and_merge_results = deduplicate_and_merge_results
        self.calculate_scores = calculate_scores

    
    async def _run_search_method(self, method_name: str, search_func, *args) -> tuple:
        """Run a single search method and return results with method name"""
        try:
            results = await search_func(*args)
            return method_name, results
        except Exception as e:
            logger.error(f"Search method '{method_name}' failed: {e}")
            return method_name, []
    

    
 