"""
Fuzzy Match Search Module
Handles fuzzy/partial string matching for drug names in RxNorm
"""

from src.core.services.neo4j.search.fuzzy_match_search.methods import search_fuzzy_drug_name
from src.core.services.neo4j.search.fuzzy_match_search.methods import search_fuzzy_with_strength
from src.core.services.neo4j.search.fuzzy_match_search.methods import search_word_overlap


class FuzzyMatchSearchService:
    """Service for fuzzy drug name matching in RxNorm"""
    
    def __init__(self):
        self.search_fuzzy_drug_name=search_fuzzy_drug_name
        self.search_fuzzy_with_strength=search_fuzzy_with_strength
        self.search_word_overlap=search_word_overlap
    