"""
Synonym Search Module
Handles synonym mapping from Excel sheet and searches in RxNorm
"""

from pathlib import Path
from src.core.services.neo4j.search.synonym_search.methods import (
search_by_synonyms,
search_synonyms_with_strength,
)
from src.core.services.neo4j.search.synonym_search.service import SynonymSearch
class SynonymSearchService:
    """Service for synonym-based drug searching using Excel mapping"""

    def __init__(self):
        self.synonym_search = SynonymSearch()
        self.search_by_synonyms = search_by_synonyms
        self.search_synonyms_with_strength = search_synonyms_with_strength
        self.get_synonyms = self.synonym_search.get_synonyms
