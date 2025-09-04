from typing import Dict, Any, List
from src.core.services.neo4j.search.run_query import run_query
from src.core.services.neo4j.search.exact_match_search.queries import(
    search_exact_drug_name_query,
    search_exact_with_strength_query
)
async def search_exact_drug_name(drug_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    return await run_query(
        query=search_exact_drug_name_query,
        params={"drug_name": drug_name, "limit": limit},
        search_method="exact_match",
        match_confidence=1.0,
    )

async def search_exact_with_strength(drug_name: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
    return await run_query(
        query=search_exact_with_strength_query,
        params={"drug_name": drug_name, "strength": strength, "limit": limit},
        search_method="exact_match_with_strength",
        match_confidence=1.0,
    )