"""
Fuzzy Match Search Module
Handles fuzzy/partial string matching for drug names in RxNorm
"""

from typing import Dict, Any, List
from src.core.services.neo4j.search.fuzzy_match_search.queries import (
    search_fuzzy_drug_name_query,
    search_fuzzy_with_strength_query,
    word_conditions_query,
    search_word_overlap_query
)
from src.core.services.neo4j.search.run_query import run_query  


async def search_fuzzy_drug_name(drug_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for fuzzy/partial drug name matches"""
    return await run_query(
        query=search_fuzzy_drug_name_query,
        params={"drug_name": drug_name, "limit": limit},
        search_method="fuzzy_match",
        match_confidence=0.65,
    )


async def search_fuzzy_with_strength(drug_name: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for fuzzy drug name matches with strength consideration"""
    return await run_query(
        query=search_fuzzy_with_strength_query,
        params={"drug_name": drug_name, "strength": strength or "", "limit": limit},
        search_method="fuzzy_match_with_strength",
        match_confidence=0.65,
    )

async def search_word_overlap(drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for drugs with word overlap"""
    words = [word.strip() for word in drug_name.lower().split() if len(word.strip()) > 2]
    if not words:
        return []

    # Build dynamic condition string
    word_conditions = [
        word_conditions_query(word)
        for word in words
    ]
    word_clause = " OR ".join(word_conditions)

    return await run_query(
        query=search_word_overlap_query(word_clause),
        params={"limit": limit},
        search_method="word_overlap",
        match_confidence=0.65,
    )