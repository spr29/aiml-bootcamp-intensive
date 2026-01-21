"""
Configuration management for RAG system.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration for RAG system."""

    # AWS Configuration
    AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID')

    # LLM Configuration
    LLM_BASE_URL = os.getenv('LLM_BASE_URL')
    LLM_API_KEY = os.getenv('LLM_API_KEY')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o')

    # Retrieval Configuration
    DEFAULT_NUM_RESULTS = 3
    HYBRID_ALPHA = 0.5  # 0.5 = balanced vector/BM25

    # Generation Configuration
    TEMPERATURE = 0.1
    MAX_TOKENS = 500

    # Conversation Configuration
    MAX_HISTORY_LENGTH = 6  # Number of conversation turns to keep

    # Data Paths
    CHUNKS_FILE = 'data/knowledge_base_chunks.json'

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration is present."""
        required = [
            cls.KNOWLEDGE_BASE_ID,
            cls.LLM_BASE_URL,
            cls.LLM_API_KEY
        ]
        return all(required)

    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary (safe for logging)."""
        return {
            'aws_region': cls.AWS_REGION,
            'kb_id': cls.KNOWLEDGE_BASE_ID,
            'llm_model': cls.LLM_MODEL,
            'num_results': cls.DEFAULT_NUM_RESULTS,
            'hybrid_alpha': cls.HYBRID_ALPHA
        }
