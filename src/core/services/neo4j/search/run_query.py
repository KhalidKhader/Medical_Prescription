from typing import Dict, Any, List
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from src.core.services.neo4j.search.driver import SearchServiceDriver

async def run_query(
    query: str,
    params: Dict[str, Any],
    search_method: str,
    match_confidence: float = 0.0,
) -> List[Dict[str, Any]]:
    """Generic helper to execute search queries and return structured results."""
    try:
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        client = SearchServiceDriver(driver)

        async with client.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, **params)

            drugs: List[Dict[str, Any]] = []
            async for record in result:
                drug: Dict[str, Any] = {
                    "rxcui": record.get("rxcui"),
                    "drug_name": record.get("drug_name"),
                    "full_name": record.get("full_name"),
                    "generic_name": record.get("generic_name"),
                    "strength": record.get("strength"),
                    "route": record.get("route"),
                    "dose_form": record.get("dose_form"),
                    "term_type": record.get("term_type"),
                    "search_method": search_method,
                    "match_confidence": float(record.get("confidence_score", match_confidence)),
                }

                # Add optional fields if they exist in the record
                if "brand_name" in record:
                    drug["brand_name"] = record.get("brand_name")

                if "embedding" in record:
                    drug["embedding"] = record.get("embedding")

                drugs.append(drug)

            logger.info(f"{search_method} found {len(drugs)} results with params {params}")
            return drugs

    except Exception as e:
        logger.error(f"{search_method} failed: {e}")
        return []
