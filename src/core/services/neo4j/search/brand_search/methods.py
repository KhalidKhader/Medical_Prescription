"""
Brand Search Module
Handles brand name searching in RxNorm using brand-specific queries
"""

from typing import Dict, Any, List
from src.core.services.neo4j.search.brand_search.queries import (
search_brand_exact_query,
search_brand_fuzzy_query, 
search_brand_with_strength_query,
search_generic_to_brand_query
)
from src.core.services.neo4j.search.run_query import run_query

async def search_brand_exact(drug_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for exact brand name matches"""
    return await run_query(
        query=search_brand_exact_query,
        params={"drug_name": drug_name, "limit": limit},
        search_method="brand_exact_match",
        match_confidence=0.9,
    )

async def search_brand_fuzzy(drug_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for fuzzy brand name matches"""
    return await run_query(
        query=search_brand_fuzzy_query,
        params={"drug_name": drug_name, "limit": limit},
        search_method="brand_fuzzy_match",
        match_confidence=0.75,
    )

async def search_brand_with_strength(drug_name: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for brand drugs with specific strength"""
    return await run_query(
        query=search_brand_with_strength_query,
        params={"drug_name": drug_name, "strength": strength, "limit": limit},
        search_method="brand_with_strength",
        match_confidence=0.85,
    )

async def search_generic_to_brand(generic_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for brand equivalents of a generic drug"""
    return await run_query(
        query=search_generic_to_brand_query,
        params={"generic_name": generic_name, "limit": limit},
        search_method="generic_to_brand_direct",
        match_confidence=0.75,
    )