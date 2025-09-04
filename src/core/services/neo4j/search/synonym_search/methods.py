from typing import Dict, Any, List
import pandas as pd
from pathlib import Path
from src.core.settings.logging import logger
from src.core.services.neo4j.search.run_query import run_query
from src.core.services.neo4j.search.synonym_search.queries import (
    search_synonym_in_rxnorm_query,
    search_synonym_with_strength_in_rxnorm_query
)
from src.core.services.neo4j.search.synonym_search.service import SynonymSearch
synonym_search = SynonymSearch()


async def search_by_synonyms(drug_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for drugs using synonym mappings"""
    try:
        synonyms = synonym_search.get_synonyms(drug_name)
        if not synonyms:
            logger.info(f"No synonyms found for '{drug_name}'")
            return []
        
        all_results = []
        
        # Search for each synonym
        for synonym in synonyms:
            # Replace internal DB call with generic run_query
            results = await run_query(
                query=search_synonym_in_rxnorm_query,
                params={"synonym": synonym, "limit": 5}, # Fetch a few candidates per synonym
                search_method="synonym_mapping",
                match_confidence=0.75, # Default confidence for this search type
            )

            for result in results:
                result["original_query"] = drug_name
                result["synonym_used"] = synonym
            all_results.extend(results)
        
        # Remove duplicates based on rxcui
        seen_rxcuis = set()
        unique_results = []
        for result in all_results:
            rxcui = result.get("rxcui")
            if rxcui and rxcui not in seen_rxcuis:
                seen_rxcuis.add(rxcui)
                unique_results.append(result)
        
        logger.info(f"Synonym search found {len(unique_results)} unique results for '{drug_name}' using {len(synonyms)} synonyms")
        return unique_results[:limit]
        
    except Exception as e:
        logger.error(f"Synonym search failed: {e}")
        return []

async def search_synonyms_with_strength(drug_name: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for drugs using synonym mappings with strength consideration"""
    try:
        synonyms = synonym_search.get_synonyms(drug_name)
        if not synonyms:
            return []
        
        all_results = []
        
        # Search for each synonym with strength
        for synonym in synonyms:
                # Replace internal DB call with generic run_query
            results = await run_query(
                query=search_synonym_with_strength_in_rxnorm_query,
                params={"synonym": synonym, "strength": strength, "limit": 5},
                search_method="synonym_mapping_with_strength",
                match_confidence=0.8, # Default confidence for strength match
            )

            for result in results:
                result["original_query"] = drug_name
                result["synonym_used"] = synonym
            all_results.extend(results)
        
        # Remove duplicates
        seen_rxcuis = set()
        unique_results = []
        for result in all_results:
            rxcui = result.get("rxcui")
            if rxcui and rxcui not in seen_rxcuis:
                seen_rxcuis.add(rxcui)
                unique_results.append(result)
        
        # Sort by confidence
        unique_results.sort(key=lambda x: x.get("match_confidence", 0), reverse=True)
        
        logger.info(f"Synonym search with strength found {len(unique_results)} results for '{drug_name} {strength}'")
        return unique_results[:limit]
        
    except Exception as e:
        logger.error(f"Synonym search with strength failed: {e}")
        return []