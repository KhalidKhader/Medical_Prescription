
"""
Embedding Search Module
Handles semantic similarity search using Gemini embeddings for drug names in RxNorm
"""

from typing import List, Optional
import numpy as np
import google.generativeai as genai
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger



class EmbeddingSearch:
    """Service for embedding-based drug name matching in RxNorm"""
    
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
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
    
 