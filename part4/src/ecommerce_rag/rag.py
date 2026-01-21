"""
RAG pipeline implementation with LLM generation and conversation memory.
"""

from typing import List, Dict, Optional
from datetime import datetime
from openai import OpenAI

from .config import Config
from .retrieval import VectorRetriever, BM25Retriever, HybridRetriever


class RAGPipeline:
    """Basic RAG pipeline for question answering."""

    def __init__(self, retrieval_method: str = 'hybrid', **kwargs):
        """
        Initialize RAG pipeline.

        Args:
            retrieval_method: 'vector', 'bm25', or 'hybrid'
            **kwargs: Additional arguments for retriever
        """
        # Initialize retriever
        if retrieval_method == 'vector':
            self.retriever = VectorRetriever()
        elif retrieval_method == 'bm25':
            self.retriever = BM25Retriever(**kwargs)
        else:
            self.retriever = HybridRetriever(**kwargs)

        # Initialize LLM client
        self.llm_client = OpenAI(
            base_url=Config.LLM_BASE_URL,
            api_key=Config.LLM_API_KEY
        )

        self.retrieval_method = retrieval_method

    def answer(self, query: str, num_results: int = None, include_sources: bool = True) -> Dict:
        """
        Generate answer for a query.

        Args:
            query: User question
            num_results: Number of documents to retrieve
            include_sources: Whether to include source citations

        Returns:
            Dict with answer, sources, and metadata
        """
        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(query, num_results)

        # Generate answer
        return self._generate_answer(query, retrieved_docs, include_sources)

    def _generate_answer(self, query: str, retrieved_docs: List[Dict], include_sources: bool) -> Dict:
        """Generate answer using LLM with retrieved context."""
        # Build context from retrieved documents
        context_parts = []
        sources = []

        for idx, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"[Document {idx}]\n{doc['text']}")
            sources.append({
                'index': idx,
                'source': doc['source'],
                'score': doc['score']
            })

        context = "\n\n".join(context_parts)

        # Create prompt
        system_prompt = """You are a helpful customer service assistant for an e-commerce platform.
Answer questions based on the provided context. Be concise, accurate, and friendly.

Guidelines:
- Only use information from the provided context
- If the context doesn't contain the answer, say so politely
- Cite document numbers when referencing specific information
- Keep answers clear and actionable"""

        user_prompt = f"""Context:
{context}

Question: {query}

Answer:"""

        # Generate response
        response = self.llm_client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )

        answer = response.choices[0].message.content

        return {
            'query': query,
            'answer': answer,
            'sources': sources if include_sources else [],
            'num_sources': len(sources),
            'retrieval_method': self.retrieval_method,
            'model': Config.LLM_MODEL,
            'timestamp': datetime.now().isoformat()
        }


class ConversationalRAG:
    """RAG system with conversation memory."""

    def __init__(self, retrieval_method: str = 'hybrid', **kwargs):
        """
        Initialize conversational RAG.

        Args:
            retrieval_method: 'vector', 'bm25', or 'hybrid'
            **kwargs: Additional arguments for retriever
        """
        # Initialize retriever
        if retrieval_method == 'vector':
            self.retriever = VectorRetriever()
        elif retrieval_method == 'bm25':
            self.retriever = BM25Retriever(**kwargs)
        else:
            self.retriever = HybridRetriever(**kwargs)

        # Initialize LLM client
        self.llm_client = OpenAI(
            base_url=Config.LLM_BASE_URL,
            api_key=Config.LLM_API_KEY
        )

        self.retrieval_method = retrieval_method
        self.conversation_history = []
        self.user_context = {}  # Store user information separately

    def chat(self, user_message: str, num_results: int = None) -> Dict:
        """
        Process user message with conversation context.

        Args:
            user_message: User's message
            num_results: Number of documents to retrieve

        Returns:
            Dict with answer, sources, and metadata
        """
        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(user_message, num_results)

        # Build context from retrieved docs
        context_parts = []
        sources = []

        for idx, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"[Document {idx}]\n{doc['text']}")
            sources.append({
                'index': idx,
                'source': doc['source'],
                'score': doc['score']
            })

        context = "\n\n".join(context_parts)

        # Build user context summary
        user_context_str = ""
        if self.user_context:
            user_context_str = "\n\nUser Information (from previous conversation):\n"
            for key, value in self.user_context.items():
                user_context_str += f"- {key}: {value}\n"

        # Build messages with conversation history
        system_content = """You are a helpful customer service assistant for an e-commerce platform.
Answer questions based on the provided context and conversation history.
Be concise, accurate, and friendly.

IMPORTANT: Remember information the user shares about themselves (name, order details, preferences, etc.)
and use it naturally in the conversation. This information is preserved across messages."""

        messages = [
            {
                "role": "system",
                "content": system_content
            }
        ]

        # Add conversation history (keep last N exchanges)
        # Include both user and assistant messages to maintain full context
        for msg in self.conversation_history[-Config.MAX_HISTORY_LENGTH:]:
            # Add user message (keep it simple, the context is in the current retrieval)
            messages.append({
                "role": "user",
                "content": msg['user']
            })
            # Add assistant response
            messages.append({
                "role": "assistant",
                "content": msg['assistant']
            })

        # Add current message with context and user info
        current_content = f"""Retrieved Knowledge Base Context:
{context}{user_context_str}

Current Question: {user_message}

Please answer the question using the retrieved context and conversation history. Remember any personal information shared."""

        messages.append({
            "role": "user",
            "content": current_content
        })

        # Generate response
        response = self.llm_client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=messages,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )

        answer = response.choices[0].message.content

        # Extract and store user information from the conversation
        self._extract_user_context(user_message, answer)

        # Update conversation history
        self.conversation_history.append({
            'user': user_message,
            'assistant': answer,
            'sources': sources,
            'timestamp': datetime.now().isoformat()
        })

        return {
            'answer': answer,
            'sources': sources,
            'retrieval_method': self.retrieval_method,
            'conversation_length': len(self.conversation_history)
        }

    def _extract_user_context(self, user_message: str, assistant_response: str):
        """
        Extract user information from conversation to maintain context.
        Simple pattern matching for common information.
        """
        import re

        # Extract name patterns
        name_patterns = [
            r"my name is (\w+)",
            r"I'm (\w+)",
            r"I am (\w+)",
            r"call me (\w+)",
            r"this is (\w+)"
        ]

        for pattern in name_patterns:
            match = re.search(pattern, user_message.lower())
            if match:
                self.user_context['name'] = match.group(1).capitalize()
                break

        # Extract order number patterns
        order_patterns = [
            r"order[# ]+([A-Z0-9-]+)",
            r"order number[: ]+([A-Z0-9-]+)",
        ]

        for pattern in order_patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                self.user_context['order_number'] = match.group(1).upper()
                break

        # Extract email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, user_message)
        if match:
            self.user_context['email'] = match.group(0)

    def get_history(self) -> List[Dict]:
        """Get conversation history."""
        return self.conversation_history

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def export_conversation(self) -> Dict:
        """Export conversation for analysis or saving."""
        return {
            'retrieval_method': self.retrieval_method,
            'total_exchanges': len(self.conversation_history),
            'conversation': self.conversation_history,
            'exported_at': datetime.now().isoformat()
        }
