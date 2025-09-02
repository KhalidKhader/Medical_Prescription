"""
Fuzzy Match Search Module
Handles fuzzy/partial string matching for drug names in RxNorm
"""

from typing import Dict, Any, List
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .queries import (search_fuzzy_drug_name, search_fuzzy_with_strength, search_word_overlap)

class FuzzyMatchSearchService:
    """Service for fuzzy drug name matching in RxNorm"""
    
    def __init__(self, driver):
        self.driver = driver
    
    async def search_fuzzy_drug_name(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for fuzzy/partial drug name matches"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_fuzzy_drug_name 
                
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
                        "search_method": "fuzzy_match",
                        "match_confidence": float(record.get("match_confidence", 0.6))
                    })
                
                logger.info(f"Fuzzy match search found {len(drugs)} results for '{drug_name}'")
                return drugs
                
        except Exception as e:
            logger.error(f"Fuzzy match search failed: {e}")
            return []
    
    async def search_fuzzy_with_strength(self, drug_name: str, strength: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for fuzzy drug name matches with strength consideration"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_fuzzy_with_strength 
                
                result = await session.run(query, drug_name=drug_name, strength=strength or "", limit=limit)
                
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
                        "search_method": "fuzzy_match_with_strength",
                        "match_confidence": float(record.get("match_confidence", 0.6))
                    })
                
                logger.info(f"Fuzzy match with strength found {len(drugs)} results for '{drug_name} {strength}'")
                return drugs
                
        except Exception as e:
            logger.error(f"Fuzzy match with strength search failed: {e}")
            return []
    
    async def search_word_overlap(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for drugs with word overlap"""
        try:
            words = [word.strip() for word in drug_name.lower().split() if len(word.strip()) > 2]
            if not words:
                return []
            
            async with self.driver.session(database=settings.neo4j_database) as session:
                # Build dynamic query for word overlap
                word_conditions = []
                for word in words:
                    word_conditions.append(f"toLower(d.name) CONTAINS '{word}' OR toLower(d.full_name) CONTAINS '{word}'")
                
                word_clause = " OR ".join(word_conditions)
                
                query = search_word_overlap(word_clause)
                
                result = await session.run(query, limit=limit)
                
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
                        "search_method": "word_overlap",
                        "match_confidence": 0.7
                    })
                
                logger.info(f"Word overlap search found {len(drugs)} results for '{drug_name}'")
                return drugs
                
        except Exception as e:
            logger.error(f"Word overlap search failed: {e}")
            return []
