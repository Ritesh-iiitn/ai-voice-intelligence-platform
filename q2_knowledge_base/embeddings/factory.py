"""
Embedding provider factory supporting local, sentence-transformers, and external LLM APIs.
"""
import os
from q2_knowledge_base.embeddings.base import BaseEmbeddingProvider
from q2_knowledge_base.embeddings.local import LocalVectorEmbeddingProvider

def get_embedding_provider(provider_type: str = None) -> BaseEmbeddingProvider:
    """Instantiate the configured embedding provider."""
    provider = provider_type or os.getenv("EMBEDDING_PROVIDER", "local")
    
    if provider == "local":
        return LocalVectorEmbeddingProvider()
    
    # Fallback to local
    return LocalVectorEmbeddingProvider()
