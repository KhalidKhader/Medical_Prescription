"""
Brand Search Module
Handles brand name searching in RxNorm using brand-specific queries
"""

from src.core.services.neo4j.search.brand_search.methods import search_brand_exact
from src.core.services.neo4j.search.brand_search.methods import search_brand_fuzzy
from src.core.services.neo4j.search.brand_search.methods import search_generic_to_brand
from src.core.services.neo4j.search.brand_search.methods import search_brand_with_strength

class BrandSearchService:
    """Service for brand-specific drug searching in RxNorm"""
    def __init__(self):
        self.search_brand_exact=search_brand_exact
        self.search_brand_fuzzy=search_brand_fuzzy
        self.search_generic_to_brand=search_generic_to_brand
        self.search_brand_with_strength=search_brand_with_strength