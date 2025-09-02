"""
Embedding Search Module
Handles semantic similarity search using Gemini embeddings for drug names in RxNorm
"""

from typing import Dict, Any, List, Optional
import numpy as np
import google.generativeai as genai
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .queries import (
    search_by_embedding,
    search_by_embedding_with_strength,
)


class EmbeddingSearchService:
    """Service for embedding-based drug name matching in RxNorm"""
    
    def __init__(self, driver):
        self.driver = driver
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini for embedding generation"""
        try:
            genai.configure(api_key=settings.google_api_key)
            logger.info("Gemini embedding model initialized for search")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini embeddings: {e}")
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using Gemini"""
        try:
            response = genai.embed_content(
                model="models/embedding-001",
                content=text
            )
            return response['embedding']
        except Exception as e:
            logger.warning(f"Embedding generation failed for '{text}': {e}")
            return None
    
    def _cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
        except Exception:
            return 0.0
    
    async def search_by_embedding(self, drug_name: str, limit: int = 10, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for drugs using embedding similarity"""
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(drug_name)
            if not query_embedding:
                logger.warning(f"Could not generate embedding for '{drug_name}'")
                return []
            
            async with self.driver.session(database=settings.neo4j_database) as session:
                # Get drugs with embeddings for similarity calculation
                query = search_by_embedding
                
                result = await session.run(query)
                
                similarities = []
                async for record in result:
                    drug_embedding = record.get("embedding")
                    
                    if drug_embedding:
                        similarity = self._cosine_similarity(query_embedding, drug_embedding)
                        if similarity >= similarity_threshold:
                            similarities.append({
                                "rxcui": record.get("rxcui"),
                                "drug_name": record.get("drug_name"),
                                "full_name": record.get("full_name"),
                                "generic_name": record.get("generic_name"),
                                "strength": record.get("strength"),
                                "route": record.get("route"),
                                "dose_form": record.get("dose_form"),
                                "term_type": record.get("term_type"),
                                "search_method": "embedding_similarity",
                                "match_confidence": similarity
                            })
                
                # Sort by similarity score
                similarities.sort(key=lambda x: x["match_confidence"], reverse=True)
                
                results = similarities[:limit]
                logger.info(f"Embedding search found {len(results)} results for '{drug_name}' (threshold: {similarity_threshold})")
                return results
                
        except Exception as e:
            logger.error(f"Embedding search failed: {e}")
            return []
    
    async def search_by_embedding_with_strength(self, drug_name: str, strength: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for drugs using embedding similarity with strength consideration"""
        try:
            # Create combined query text for better matching
            combined_query = f"{drug_name} {strength}" if strength else drug_name
            query_embedding = self._generate_embedding(combined_query)
            
            if not query_embedding:
                return []
            
            async with self.driver.session(database=settings.neo4j_database) as session:
                # Get drugs with embeddings, optionally filter by strength
                strength_filter = "AND toLower(d.strength) CONTAINS toLower($strength)" if strength else ""
                
                query = search_by_embedding_with_strength(strength_filter) 
                
                params = {"strength": strength} if strength else {}
                result = await session.run(query, **params)
                
                similarities = []
                async for record in result:
                    drug_embedding = record.get("embedding")
                    
                    if drug_embedding:
                        similarity = self._cosine_similarity(query_embedding, drug_embedding)
                        if similarity >= 0.6:  # Lower threshold for strength matching
                            # Boost score if strength matches
                            if strength and strength.lower() in record.get("strength", "").lower():
                                similarity = min(similarity + 0.1, 1.0)
                            
                            similarities.append({
                                "rxcui": record.get("rxcui"),
                                "drug_name": record.get("drug_name"),
                                "full_name": record.get("full_name"),
                                "generic_name": record.get("generic_name"),
                                "strength": record.get("strength"),
                                "route": record.get("route"),
                                "dose_form": record.get("dose_form"),
                                "term_type": record.get("term_type"),
                                "search_method": "embedding_similarity_with_strength",
                                "match_confidence": similarity
                            })
                
                # Sort by similarity score
                similarities.sort(key=lambda x: x["match_confidence"], reverse=True)
                
                results = similarities[:limit]
                logger.info(f"Embedding search with strength found {len(results)} results for '{drug_name} {strength}'")
                return results
                
        except Exception as e:
            logger.error(f"Embedding search with strength failed: {e}")
            return []
