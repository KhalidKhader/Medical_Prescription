"""
Exact Match Search Module
Handles exact string matching for drug names in RxNorm
"""

from typing import Dict, Any, List
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .queries import(
    search_exact_drug_name,
    search_exact_with_strength
)

class ExactMatchSearchService:
    """Service for exact drug name matching in RxNorm"""
    
    def __init__(self, driver):
        self.driver = driver
    
    async def search_exact_drug_name(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for exact drug name matches"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_exact_drug_name
                
                result = await session.run(query, drug_name=drug_name, limit=limit)
                
                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "search_method": "exact_match",
                        "match_confidence": 1.0
                    })
                
                logger.info(f"Exact match search found {len(drugs)} results for '{drug_name}'")
                return drugs
                
        except Exception as e:
            logger.error(f"Exact match search failed: {e}")
            return []
    
    async def search_exact_with_strength(self, drug_name: str, strength: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for exact drug name with specific strength"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_exact_with_strength 
                
                result = await session.run(query, drug_name=drug_name, strength=strength, limit=limit)
                
                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "search_method": "exact_match_with_strength",
                        "match_confidence": 1.0
                    })
                
                logger.info(f"Exact match with strength found {len(drugs)} results for '{drug_name} {strength}'")
                return drugs
                
        except Exception as e:
            logger.error(f"Exact match with strength search failed: {e}")
            return []
