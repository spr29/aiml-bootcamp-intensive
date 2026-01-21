"""
Retrieval strategies for RAG system.
"""

import json
import re
import boto3
import numpy as np
from typing import List, Dict
from rank_bm25 import BM25Okapi

from .config import Config


class BaseRetriever:
    """Base class for retrievers."""

    def retrieve(self, query: str, num_results: int = None) -> List[Dict]:
        """Retrieve relevant documents for a query."""
        raise NotImplementedError


class VectorRetriever(BaseRetriever):
    """Vector similarity retriever using Bedrock Knowledge Base."""

    def __init__(self):
        self.client = boto3.client(
            'bedrock-agent-runtime',
            region_name=Config.AWS_REGION
        )
        self.kb_id = Config.KNOWLEDGE_BASE_ID

    def retrieve(self, query: str, num_results: int = None) -> List[Dict]:
        """
        Retrieve documents using vector similarity search.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of documents with text, score, and source
        """
        if num_results is None:
            num_results = Config.DEFAULT_NUM_RESULTS

        response = self.client.retrieve(
            knowledgeBaseId=self.kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': num_results
                }
            }
        )

        results = []
        for result in response.get('retrievalResults', []):
            results.append({
                'text': result['content']['text'],
                'score': result['score'],
                'source': result['location']['s3Location']['uri'],
                'method': 'vector'
            })

        return results


class BM25Retriever(BaseRetriever):
    """BM25 keyword-based retriever."""

    def __init__(self, chunks_file: str = None):
        """
        Initialize BM25 retriever.

        Args:
            chunks_file: Path to chunks JSON file
        """
        if chunks_file is None:
            chunks_file = Config.CHUNKS_FILE

        # Load chunks
        with open(chunks_file, 'r') as f:
            self.chunks = json.load(f)

        # Build BM25 index
        self.corpus = [chunk['text'] for chunk in self.chunks]
        tokenized_corpus = [self._tokenize(doc) for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize text into words."""
        return re.findall(r'\w+', text.lower())

    def retrieve(self, query: str, num_results: int = None) -> List[Dict]:
        """
        Retrieve documents using BM25 keyword search.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of documents with text, score, and source
        """
        if num_results is None:
            num_results = Config.DEFAULT_NUM_RESULTS

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Get top K indices
        top_indices = np.argsort(scores)[::-1][:num_results]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    'text': self.chunks[idx]['text'],
                    'score': float(scores[idx]),
                    'source': self.chunks[idx]['chunk_id'],
                    'method': 'bm25'
                })

        return results


class HybridRetriever(BaseRetriever):
    """Hybrid retriever combining vector and BM25 search."""

    def __init__(self, chunks_file: str = None, alpha: float = None):
        """
        Initialize hybrid retriever.

        Args:
            chunks_file: Path to chunks JSON file
            alpha: Weight for vector search (0-1). Default from config.
                   alpha=1.0: pure vector, alpha=0.0: pure BM25
        """
        self.vector_retriever = VectorRetriever()
        self.bm25_retriever = BM25Retriever(chunks_file)
        self.alpha = alpha if alpha is not None else Config.HYBRID_ALPHA

    @staticmethod
    def _normalize_scores(results: List[Dict]) -> List[Dict]:
        """Normalize scores to 0-1 range."""
        if not results:
            return results

        scores = [r['score'] for r in results]
        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            for r in results:
                r['normalized_score'] = 1.0
        else:
            for r in results:
                r['normalized_score'] = (r['score'] - min_score) / (max_score - min_score)

        return results

    def retrieve(self, query: str, num_results: int = None) -> List[Dict]:
        """
        Retrieve documents using hybrid search.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of documents with combined scores
        """
        if num_results is None:
            num_results = Config.DEFAULT_NUM_RESULTS

        # Get results from both methods (fetch more to ensure good coverage)
        vector_results = self.vector_retriever.retrieve(query, num_results * 2)
        bm25_results = self.bm25_retriever.retrieve(query, num_results * 2)

        # Normalize scores
        vector_results = self._normalize_scores(vector_results)
        bm25_results = self._normalize_scores(bm25_results)

        # Combine results
        combined = {}

        for result in vector_results:
            text = result['text']
            combined[text] = {
                'text': text,
                'source': result['source'],
                'vector_score': result['normalized_score'],
                'bm25_score': 0.0,
                'method': 'hybrid'
            }

        for result in bm25_results:
            text = result['text']
            if text in combined:
                combined[text]['bm25_score'] = result['normalized_score']
            else:
                combined[text] = {
                    'text': text,
                    'source': result['source'],
                    'vector_score': 0.0,
                    'bm25_score': result['normalized_score'],
                    'method': 'hybrid'
                }

        # Calculate hybrid scores
        for text in combined:
            combined[text]['score'] = (
                self.alpha * combined[text]['vector_score'] +
                (1 - self.alpha) * combined[text]['bm25_score']
            )

        # Sort by hybrid score and return top K
        sorted_results = sorted(combined.values(), key=lambda x: x['score'], reverse=True)
        return sorted_results[:num_results]
