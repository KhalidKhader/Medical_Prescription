"""
RxNorm Knowledge Graph Service with Gemini Embeddings.
Clean implementation using actual schema and proper Gemini embedding similarity search.
"""

import asyncio
import numpy as np
from typing import Dict, Any, List, Optional
from neo4j import AsyncGraphDatabase
import google.generativeai as genai
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .queries import (
    HEALTH_CHECK_QUERY,
    SAMPLE_DRUG_QUERY,
    DRUG_SEARCH_QUERY,
    EXACT_DRUG_MATCH_QUERY,
    COMPREHENSIVE_DRUG_SEARCH,
    EMBEDDING_SIMILARITY_SEARCH,
    DRUG_DETAILS_QUERY
)

class RxNormService:
    """Enhanced RxNorm service using Gemini embeddings and actual KG schema"""
    
    def __init__(self):
        """Initialize RxNorm service with Neo4j connection and Gemini embeddings"""
        self.driver = None
        self._initialize_driver()
        self._initialize_gemini()
        
        # Statistics tracking
        self.query_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "exact_matches": 0,
            "embedding_searches": 0
        }
    
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
    
    def _initialize_gemini(self):
        """Initialize Gemini for embedding generation"""
        try:
            genai.configure(api_key=settings.google_api_key)
            logger.info("Gemini embedding model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini embeddings: {e}")

    async def test_connection(self) -> Dict[str, Any]:
        """Test Neo4j connection and RxNorm embedding data availability"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                # Test basic connection
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                
                if not record or record["test"] != 1:
                    return {"connected": False, "error": "Basic connection test failed"}
                
                # Check RxNorm embedding data
                health_result = await session.run(HEALTH_CHECK_QUERY)
                health_record = await health_result.single()
                
                if not health_record:
                    return {"connected": True, "rxnorm_available": False, "error": "No RxNorm data found"}
                
                # Get sample drug
                sample_result = await session.run(SAMPLE_DRUG_QUERY)
                sample_records = await sample_result.fetch(1)  # Get first record only
                sample_record = sample_records[0] if sample_records else None
                
                sample_drug = None
                if sample_record:
                    sample_drug = {
                        "concept_id": sample_record["concept_id"],
                        "drug_name": sample_record["drug_name"],
                        "strength": sample_record.get("strength"),
                        "route": sample_record.get("route")
                    }
                
                return {
                    "connected": True,
                    "database": settings.neo4j_database,
                    "uri": settings.neo4j_uri,
                    "rxnorm_available": True,
                    "embedding_enabled": True,
                    "database_stats": {
                        "total_concepts": health_record["total_concepts"],
                        "total_attributes": health_record["total_attributes"],
                        "total_sources": health_record["total_sources"],
                        "total_semantic_types": health_record["total_semantic_types"]
                    },
                    "sample_drug": sample_drug,
                    "query_stats": self.query_stats
                }
                
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return {"connected": False, "error": str(e)}

    def _generate_query_embedding(self, drug_name: str) -> Optional[List[float]]:
        """Generate embedding for drug name using Gemini"""
        try:
            response = genai.embed_content(
                model="models/embedding-001",
                content=drug_name
            )
            return response['embedding']
        except Exception as e:
            logger.warning(f"Embedding generation failed for '{drug_name}': {e}")
            return None

    def _cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        except Exception:
            return 0.0

    async def search_drug(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Enhanced drug search using embeddings and brand mapping"""
        try:
            self.query_stats["total_queries"] += 1
            logger.info(f"🔍 Enhanced search for drug: '{drug_name}'")
            
            # Pure embedding-based search without static mappings
            search_terms = [drug_name.lower()]
            
            # Try each search term
            for term in search_terms:
                drugs = await self._search_with_strategies(term, limit)
                if drugs:
                    self.query_stats["successful_queries"] += 1
                    logger.info(f"✅ Found {len(drugs)} matches for '{term}'")
                    return drugs
            
            logger.warning(f"❌ No matches found for '{drug_name}' or its mappings")
            return []
                
        except Exception as e:
            logger.error(f"Drug search failed: {e}")
            return []

    async def _search_with_strategies(self, drug_name: str, limit: int) -> List[Dict[str, Any]]:
        """Search using multiple strategies"""
        
        # Strategy 1: Exact text match
        drugs = await self._exact_text_search(drug_name, limit)
        if drugs:
            self.query_stats["exact_matches"] += 1
            return drugs
        
        # Strategy 2: Comprehensive text search
        drugs = await self._comprehensive_text_search(drug_name, limit)
        if drugs:
            return drugs
        
        # Strategy 3: Embedding similarity search
        drugs = await self._embedding_similarity_search(drug_name, limit)
        if drugs:
            self.query_stats["embedding_searches"] += 1
            return drugs
        
        return []

    async def _exact_text_search(self, drug_name: str, limit: int) -> List[Dict[str, Any]]:
        """Exact text match search"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                result = await session.run(EXACT_DRUG_MATCH_QUERY, drug_name=drug_name)
                
                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record["concept_id"],
                        "drug_name": record["drug_name"],
                        "strength": record.get("strength"),
                        "brand_name": record.get("brand_name"),
                        "search_method": "exact_match"
                    })
                
                return drugs
        except Exception as e:
            logger.error(f"Exact text search failed: {e}")
            return []

    async def _comprehensive_text_search(self, drug_name: str, limit: int) -> List[Dict[str, Any]]:
        """Comprehensive text search with relationships"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                result = await session.run(
                    COMPREHENSIVE_DRUG_SEARCH,
                    drug_name=drug_name,
                    strength=None,
                    limit=limit
                )
                
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
                        "psn": record.get("psn"),
                        "brand_drug": record.get("brand_drug"),
                        "instruction_template": record.get("instruction_template"),
                        "therapeutic_class": record.get("therapeutic_class"),
                        "ingredients": record.get("ingredients", []),
                        "match_score": record.get("match_score", 0),
                        "search_method": "comprehensive"
                    })
                
                return drugs
        except Exception as e:
            logger.error(f"Comprehensive text search failed: {e}")
            return []

    async def _embedding_similarity_search(self, drug_name: str, limit: int) -> List[Dict[str, Any]]:
        """Search using Gemini embedding similarity"""
        try:
            # Generate query embedding
            query_embedding = self._generate_query_embedding(drug_name)
            if not query_embedding:
                logger.warning(f"Could not generate embedding for '{drug_name}'")
                return []
            
            async with self.driver.session(database=settings.neo4j_database) as session:
                # Get drugs with embeddings for similarity calculation
                result = await session.run(
                    "MATCH (d:Drug) WHERE d.embedding IS NOT NULL RETURN d LIMIT 1000"
                )
                
                similarities = []
                async for record in result:
                    drug = dict(record["d"])
                    drug_embedding = drug.get("embedding")
                    
                    if drug_embedding:
                        similarity = self._cosine_similarity(query_embedding, drug_embedding)
                        if similarity > 0.7:  # Threshold for relevant matches
                            similarities.append({
                                "drug": drug,
                                "similarity": similarity
                            })
                
                # Sort by similarity and return top matches
                similarities.sort(key=lambda x: x["similarity"], reverse=True)
                
                drugs = []
                for item in similarities[:limit]:
                    drug = item["drug"]
                    drugs.append({
                        "rxcui": drug["rxcui"],
                        "drug_name": drug["name"],
                        "full_name": drug.get("full_name"),
                        "generic_name": drug.get("generic_name"),
                        "brand_name": drug.get("sxdg_name"),
                        "strength": drug.get("strength"),
                        "route": drug.get("route"),
                        "dose_form": drug.get("dose_form"),
                        "similarity_score": item["similarity"],
                        "search_method": "embedding_similarity"
                    })
                
                return drugs
                
        except Exception as e:
            logger.error(f"Embedding similarity search failed: {e}")
            return []

    async def get_drug_details(self, concept_id: str) -> Dict[str, Any]:
        """Get detailed drug information by concept ID"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                result = await session.run(DRUG_DETAILS_QUERY, concept_id=concept_id)
                record = await result.single()
                
                if not record:
                    return {}
                
                return {
                    "rxcui": record.get("rxcui"),
                    "drug_name": record.get("drug_name"),
                    "full_name": record.get("full_name"),
                    "generic_name": record.get("generic_name"),
                    "brand_name": record.get("brand_name"),
                    "strength": record.get("strength"),
                    "route": record.get("route"),
                    "dose_form": record.get("dose_form"),
                    "term_type": record.get("term_type"),
                    "psn": record.get("psn"),
                    "brand_drug": record.get("brand_drugs", [])[0] if record.get("brand_drugs") else None,
                    "instruction_template": record.get("instruction_templates", [])[0] if record.get("instruction_templates") else None,
                    "therapeutic_class": record.get("therapeutic_classes", [])[0] if record.get("therapeutic_classes") else None,
                    "generic_equivalent": record.get("generic_equivalents", [])[0] if record.get("generic_equivalents") else None,
                    "branded_equivalent": record.get("branded_equivalents", [])[0] if record.get("branded_equivalents") else None,
                    "ingredients": record.get("ingredients", [])
                }
                
        except Exception as e:
            logger.error(f"Drug details retrieval failed: {e}")
            return {}

    # Legacy compatibility methods
    def get_drug_info(self, drug_name: str, strength: str = None) -> list:
        """Synchronous wrapper for drug info lookup (for tool compatibility)"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._get_drug_info_async(drug_name, strength))
        except RuntimeError:
            return asyncio.run(self._get_drug_info_async(drug_name, strength))
    
    async def _get_drug_info_async(self, drug_name: str, strength: str = None) -> list:
        """Get drug information - legacy format for compatibility"""
        try:
            drugs = await self.get_comprehensive_drug_info(drug_name, strength)
            
            # Convert to legacy format
            legacy_results = []
            for drug in drugs:
                legacy_results.append({
                    "rxcui": drug["rxcui"],
                    "generic_name": drug.get("generic_name", drug["drug_name"]),
                    "drug_name": drug["drug_name"],
                    "strength": drug.get("strength"),
                    "ndc": None,  # Not available in new schema
                    "drug_schedule": None,  # Not available in new schema
                    "brand_drug": drug.get("brand_name", drug["drug_name"]),
                    "brand_ndc": None,  # Not available in new schema
                    "term_type": drug.get("term_type"),
                    "route": drug.get("route"),
                    "dose_form": drug.get("dose_form"),
                    "ingredients": drug.get("ingredients", []),
                    "instruction_template": drug.get("instruction_template"),
                    "search_method": drug.get("search_method", "embedding_enhanced")
                })
            
            return legacy_results
                
        except Exception as e:
            logger.error(f"Error querying RxNorm for {drug_name}: {e}")
            return []

    async def get_comprehensive_drug_info(self, drug_name: str, strength: str = None, instructions: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get comprehensive drug information using the proven search_drug method"""
        try:
            logger.info(f"🔍 Comprehensive search for: '{drug_name}', strength: '{strength or 'N/A'}'")
            
            # Use the working search_drug method directly
            results = await self.search_drug(drug_name, limit=10)
            
            if not results:
                logger.warning(f"❌ No matches found for '{drug_name}'")
                return []
            
            # Filter by strength if provided
            if strength:
                strength_filtered = []
                for drug in results:
                    drug_name_str = drug.get('drug_name', '').lower()
                    if strength.lower() in drug_name_str:
                        strength_filtered.append(drug)
                
                if strength_filtered:
                    results = strength_filtered
                    logger.info(f"✅ Filtered to {len(results)} drugs matching strength '{strength}'")
            
            # Enhance with full details
            enhanced_results = []
            for drug in results[:3]:  # Top 3 matches
                rxcui = drug.get('rxcui')
                if rxcui:
                    enhanced_drug = await self.get_drug_details(rxcui)
                    if enhanced_drug:
                        enhanced_drug.update({
                            'match_score': drug.get('match_score', 0),
                            'search_method': 'comprehensive_embedding'
                        })
                        enhanced_results.append(enhanced_drug)
            
            if enhanced_results:
                logger.info(f"✅ Comprehensive search found {len(enhanced_results)} matches for '{drug_name}'")
            else:
                logger.warning(f"❌ No enhanced matches found for '{drug_name}'")
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Comprehensive drug search failed: {e}")
            return []

    async def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            await self.driver.close()

# Global RxNorm service instance
rxnorm_service = RxNormService()