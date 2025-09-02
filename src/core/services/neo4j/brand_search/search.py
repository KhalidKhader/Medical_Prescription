"""
Brand Search Module
Handles brand name searching in RxNorm using brand-specific queries
"""

from typing import Dict, Any, List
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .queries import (
search_brand_exact,
search_brand_fuzzy, 
search_generic_to_brand,
search_brand_with_strength,
)


class BrandSearchService:
    """Service for brand-specific drug searching in RxNorm"""
    
    def __init__(self, driver):
        self.driver = driver
    
    async def search_brand_exact(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for exact brand name matches"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_brand_exact 
                
                result = await session.run(query, drug_name=drug_name, limit=limit)
                
                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "brand_name": record.get("brand_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "search_method": "brand_exact_match",
                        "match_confidence": 1.0
                    })
                
                logger.info(f"Brand exact search found {len(drugs)} results for '{drug_name}'")
                return drugs
                
        except Exception as e:
            logger.error(f"Brand exact search failed: {e}")
            return []
    
    async def search_brand_fuzzy(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for fuzzy brand name matches"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_brand_fuzzy 
                
                result = await session.run(query, drug_name=drug_name, limit=limit)
                
                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "brand_name": record.get("brand_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "search_method": "brand_fuzzy_match",
                        "match_confidence": float(record.get("match_confidence", 0.7))
                    })
                
                logger.info(f"Brand fuzzy search found {len(drugs)} results for '{drug_name}'")
                return drugs
                
        except Exception as e:
            logger.error(f"Brand fuzzy search failed: {e}")
            return []
    
    async def search_generic_to_brand(self, generic_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for brand equivalents of a generic drug using direct queries"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                # Simple direct search without relationships
                query = search_generic_to_brand 

                result = await session.run(query, generic_name=generic_name, limit=limit)

                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "brand_name": record.get("brand_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "search_method": "generic_to_brand_direct",
                        "match_confidence": 0.8
                    })

                logger.info(f"Generic to brand search found {len(drugs)} results for '{generic_name}'")
                return drugs

        except Exception as e:
            logger.error(f"Generic to brand search failed: {e}")
            return []
    
    async def search_brand_with_strength(self, drug_name: str, strength: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for brand drugs with specific strength"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_brand_with_strength 
                
                result = await session.run(query, drug_name=drug_name, strength=strength, limit=limit)
                
                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "brand_name": record.get("brand_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "search_method": "brand_with_strength",
                        "match_confidence": 0.9
                    })
                
                logger.info(f"Brand with strength search found {len(drugs)} results for '{drug_name} {strength}'")
                return drugs
                
        except Exception as e:
            logger.error(f"Brand with strength search failed: {e}")
            return []
