"""
Exact Match Search Module
Handles exact string matching for drug names in RxNorm
"""

from typing import Dict, Any, List
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.services.neo4j.search.exact_match_search.methods import search_exact_drug_name
from src.core.services.neo4j.search.exact_match_search.methods import search_exact_with_strength
class ExactMatchSearchService:
    """Service for exact drug name matching in RxNorm"""
    
    def __init__(self):
        self.search_exact_drug_name = search_exact_drug_name
        self.search_exact_with_strength = search_exact_with_strength
