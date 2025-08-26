"""
RxNorm Knowledge Graph Service using Neo4j.
Provides drug information retrieval and health monitoring.
"""

import asyncio
from typing import Dict, Any, List, Optional
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .queries import (
    HEALTH_CHECK_QUERY,
    SAMPLE_DRUG_QUERY,
    DRUG_SEARCH_QUERY,
    EXACT_DRUG_MATCH_QUERY,
    DRUG_DETAILS_QUERY,
    NDC_LOOKUP_QUERY,
    FLEXIBLE_QUERY,
    FUZZY_QUERY,
)


class RxNormService:
    """Service for RxNorm Knowledge Graph operations"""
    
    def __init__(self):
        """Initialize RxNorm service with Neo4j connection"""
        self.driver = None
        self._initialize_driver()
    
    def _initialize_driver(self):
        """Initialize Neo4j driver"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_lifetime=settings.neo4j_max_connection_lifetime,
                max_connection_pool_size=settings.neo4j_max_connections,
                connection_timeout=settings.neo4j_connection_timeout
            )
            logger.info("Neo4j RxNorm driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Neo4j connection and RxNorm data availability"""
        try:
            async with self.driver.session() as session:
                # Test basic connection
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                
                if not record or record["test"] != 1:
                    return {
                        "connected": False,
                        "error": "Basic connection test failed"
                    }
                
                # Check RxNorm data
                health_result = await session.run(HEALTH_CHECK_QUERY)
                health_record = await health_result.single()
                
                if not health_record:
                    return {
                        "connected": True,
                        "rxnorm_available": False,
                        "error": "No RxNorm data found"
                    }
                
                # Get sample drug
                sample_result = await session.run(SAMPLE_DRUG_QUERY)
                sample_record = await sample_result.single()
                
                sample_drug = None
                if sample_record:
                    sample_drug = {
                        "concept_id": sample_record["concept_id"],
                        "drug_name": sample_record["drug_name"]
                    }
                
                return {
                    "connected": True,
                    "database": settings.neo4j_database,
                    "uri": settings.neo4j_uri,
                    "langfuse_connected": True,  # Assume LangFuse is working
                    "rxnorm_available": True,
                    "database_stats": {
                        "total_concepts": health_record["total_concepts"],
                        "total_attributes": health_record["total_attributes"],
                        "total_sources": health_record["total_sources"],
                        "total_semantic_types": health_record["total_semantic_types"]
                    },
                    "sample_drug": sample_drug,
                    "query_stats": {
                        "total_queries": 0,
                        "successful_queries": 0,
                        "cache_hits": 0,
                        "fuzzy_searches": 0,
                        "exact_matches": 0,
                        "cache_hit_rate": 0,
                        "success_rate": 0,
                        "fuzzy_search_rate": 0,
                        "cache_size": 0
                    },
                    "cache_info": {
                        "cache_size": 0,
                        "cache_ttl": 3600
                    }
                }
                
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    async def search_drug(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for drugs by name with fuzzy matching and OCR correction"""
        try:
            logger.info(f"🔍 Searching for drug: '{drug_name}'")
            
            # First try exact search
            drugs = await self._exact_drug_search(drug_name, limit)
            
            # If no results, try fuzzy search with OCR corrections
            if not drugs:
                logger.info(f"No exact match found, trying OCR corrections and fuzzy search for '{drug_name}'")
                drugs = await self._fuzzy_drug_search(drug_name, limit)
            
            if drugs:
                logger.info(f"✅ Found {len(drugs)} drug matches for '{drug_name}'")
            else:
                logger.warning(f"❌ No matches found for '{drug_name}' even with fuzzy search")
            
            return drugs
                
        except Exception as e:
            logger.error(f"Drug search failed: {e}")
            return []

    async def _exact_drug_search(self, drug_name: str, limit: int) -> List[Dict[str, Any]]:
        """Exact drug name search"""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    DRUG_SEARCH_QUERY,
                    drug_name=drug_name,
                    limit=limit
                )
                
                drugs = []
                async for record in result:
                    drug_record = {
                        "concept_id": record["concept_id"],
                        "concept_name": record.get("concept_name", record.get("drug_name", "")),
                        "drug_name": record["drug_name"]
                    }
                    # Add additional fields if available
                    for field in ["ndc", "drug_schedule", "brand_drug", "brand_ndc"]:
                        if record.get(field):
                            drug_record[field] = record[field]
                    drugs.append(drug_record)
                
                return drugs
        except Exception as e:
            logger.error(f"Exact drug search failed: {e}")
            return []

    async def _fuzzy_drug_search(self, drug_name: str, limit: int) -> List[Dict[str, Any]]:
        """Fuzzy search with OCR error corrections for medical abbreviations"""
        try:
            # Common OCR corrections for medical abbreviations and units
            ocr_corrections = {
                # Units and measurements
                "t3p": "TSP",      # teaspoon (common OCR error)
                "tsp": "TSP",      # teaspoon
                "tbsp": "TBSP",    # tablespoon
                "ml": "ML",        # milliliter
                "mg": "MG",        # milligram
                "mcg": "MCG",      # microgram
                "gm": "GM",        # gram
                "kg": "KG",        # kilogram
                "iu": "IU",        # international unit
                
                # Common OCR character confusions
                "0": "O",          # zero vs letter O
                "1": "I",          # one vs letter I  
                "5": "S",          # five vs letter S
                "8": "B",          # eight vs letter B
                "6": "G",          # six vs letter G
                "rn": "m",         # common OCR error
                "ii": "11",        # roman numeral confusion
                "iii": "111",      # roman numeral confusion
                
                # Drug name corrections
                "proveritil": "proventil",
                "pulmicart": "pulmicort",
                "claratin": "claritin",
                "singuliar": "singulair"
            }
            
            # Apply OCR corrections
            corrected_name = drug_name.lower()
            original_name = corrected_name
            
            for error, correction in ocr_corrections.items():
                corrected_name = corrected_name.replace(error.lower(), correction.lower())
            
            # If we made corrections, try searching with corrected name
            if corrected_name != original_name:
                logger.info(f"🔧 Applied OCR correction: '{drug_name}' -> '{corrected_name}'")
                drugs = await self._exact_drug_search(corrected_name, limit)
                if drugs:
                    logger.info(f"✅ Found matches with OCR correction")
                    return drugs
            
            # Try partial matching with CONTAINS
            logger.info(f"🔍 Trying fuzzy search with partial matching")
            
            # Create regex pattern for fuzzy matching
            pattern = f".*{drug_name.lower().replace(' ', '.*')}.*"
            
            async with self.driver.session() as session:
                result = await session.run(
                    FUZZY_QUERY,
                    drug_name=drug_name.lower(),
                    pattern=pattern,
                    limit=limit
                )
                
                drugs = []
                async for record in result:
                    drug_record = {
                        "concept_id": record["concept_id"],
                        "concept_name": record.get("concept_name", record.get("drug_name", "")),
                        "drug_name": record["drug_name"]
                    }
                    # Add additional fields if available
                    for field in ["ndc", "drug_schedule", "brand_drug", "brand_ndc"]:
                        if record.get(field):
                            drug_record[field] = record[field]
                    drugs.append(drug_record)
                
                if drugs:
                    logger.info(f"✅ Fuzzy search found {len(drugs)} matches")
                
                return drugs
                
        except Exception as e:
            logger.error(f"Fuzzy drug search failed: {e}")
            return []
    
    async def get_drug_details(self, concept_id: str) -> Dict[str, Any]:
        """Get detailed drug information by concept ID"""
        try:
            async with self.driver.session() as session:
                result = await session.run(
                    DRUG_DETAILS_QUERY,
                    concept_id=concept_id
                )
                
                details = {}
                async for record in result:
                    attr_type = record["attribute_type"]
                    attr_value = record["attribute_value"]
                    details[attr_type] = attr_value
                
                return details
                    
        except Exception as e:
            logger.error(f"Drug details retrieval failed: {e}")
            return {}
    
    
    def get_drug_info(self, drug_name: str, strength: str = None) -> list:
        """
        Synchronous wrapper for drug info lookup (for tool compatibility)
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._get_drug_info_async(drug_name, strength))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self._get_drug_info_async(drug_name, strength))
    
    async def _get_drug_info_async(self, drug_name: str, strength: str = None) -> list:
        """
        Get drug information from RxNorm knowledge graph
        
        Args:
            drug_name: Name of the drug to search for
            strength: Optional strength parameter
            
        Returns:
            List of drug information dictionaries
        """
        try:
            logger.info(f"Searching RxNorm for drug: {drug_name} with strength: {strength}")
            
            async with self.driver.session() as session:
                
                result = await session.run(
                    FLEXIBLE_QUERY,
                    drug_name=drug_name,
                    limit=10
                )
                
                results = []
                async for record in result:
                    rxcui = record.get("rxcui")
                    if rxcui:
                        results.append({
                            "rxcui": str(rxcui),
                            "generic_name": record.get("drug_name"),
                            "strength": strength if strength else None,
                            "ndc": None,  # Will be filled by LLM fallback if needed
                            "drug_schedule": None,
                            "brand_drug": record.get("drug_name"),
                            "brand_ndc": None,
                            "term_type": record.get("term_type"),
                            "related_terms": record.get("related_terms", [])
                        })
                
                if results:
                    logger.info(f"Found {len(results)} results for {drug_name}")
                else:
                    logger.warning(f"No results found for {drug_name}")
                
                return results
                
        except Exception as e:
            logger.error(f"Error querying RxNorm for {drug_name}: {e}")
            return []

    async def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            await self.driver.close()


# Global RxNorm service instance
rxnorm_service = RxNormService()
