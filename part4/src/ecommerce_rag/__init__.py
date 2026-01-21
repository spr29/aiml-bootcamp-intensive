"""
E-commerce RAG Chatbot Package

Production-ready RAG system with multiple retrieval strategies,
conversation memory, and source attribution.
"""

__version__ = "1.0.0"

from .retrieval import VectorRetriever, BM25Retriever, HybridRetriever
from .rag import RAGPipeline, ConversationalRAG

__all__ = [
    'VectorRetriever',
    'BM25Retriever',
    'HybridRetriever',
    'RAGPipeline',
    'ConversationalRAG'
]
