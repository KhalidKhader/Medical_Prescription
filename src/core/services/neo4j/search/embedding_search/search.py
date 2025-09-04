
"""
Embedding Search Module
Handles semantic similarity search using Gemini embeddings for drug names in RxNorm
"""


from src.core.services.neo4j.search.embedding_search.methods import (
    search_by_embedding,
    search_by_embedding_with_strength,
)

class EmbeddingSearchService:
    """Service for embedding-based drug name matching in RxNorm"""
    
    def __init__(self):
        self.search_by_embedding = search_by_embedding
        self.search_by_embedding_with_strength = search_by_embedding_with_strength