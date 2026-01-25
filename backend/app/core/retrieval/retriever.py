"""Retrieval system with scoring."""
import logging
from typing import List, Dict, Any, Optional

from app.core.vectorstore.chromadb_store import ChromaDBStore
from app.core.generation.claude import ClaudeGenerator
from app.core.generation.openai_gen import OpenAIGenerator
from app.core.generation.prompt_templates import create_rag_prompt
from app.config import settings

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Complete RAG pipeline: Retrieval + Generation."""

    def __init__(self):
        """Initialize RAG retriever."""
        self.vector_store = ChromaDBStore()
        self.claude_generator = ClaudeGenerator()
        self.openai_generator = OpenAIGenerator()

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: Query string
            top_k: Number of results
            filter_metadata: Optional metadata filter

        Returns:
            List of retrieved documents with scores
        """
        top_k = top_k or settings.top_k

        results = await self.vector_store.query(
            query_text=query,
            top_k=top_k,
            filter_metadata=filter_metadata
        )

        logger.info(f"Retrieved {len(results)} documents for query")
        return results

    async def generate_response(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        llm_provider: str = None
    ) -> Dict[str, Any]:
        """Generate response using LLM with retrieved contexts.

        Args:
            query: User query
            contexts: Retrieved context documents
            llm_provider: "claude" or "openai" (defaults to settings)

        Returns:
            Generation result with text, tokens, cost, latency
        """
        llm_provider = llm_provider or settings.default_llm_provider

        # Create RAG prompt
        rag_prompt = create_rag_prompt(query, contexts)

        # Select generator
        if llm_provider == "claude":
            result = await self.claude_generator.generate(rag_prompt)
        elif llm_provider == "openai":
            result = await self.openai_generator.generate(rag_prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {llm_provider}")

        return result

    async def query(
        self,
        query_text: str,
        top_k: int = None,
        llm_provider: str = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Complete RAG pipeline: retrieve + generate.

        Args:
            query_text: User's question
            top_k: Number of documents to retrieve
            llm_provider: LLM to use for generation
            filter_metadata: Optional metadata filter

        Returns:
            Complete RAG result with response, sources, and metadata
        """
        logger.info(f"Processing RAG query: '{query_text}'")

        # Step 1: Retrieve relevant documents
        sources = await self.retrieve(
            query=query_text,
            top_k=top_k,
            filter_metadata=filter_metadata
        )

        if not sources:
            logger.warning("No sources retrieved for query")
            return {
                "query": query_text,
                "response": "I couldn't find relevant information to answer your question. Please contact support for assistance.",
                "sources": [],
                "llm_provider": llm_provider or settings.default_llm_provider,
                "token_usage": {},
                "latency_ms": 0,
                "cost": 0.0
            }

        # Step 2: Generate response
        generation_result = await self.generate_response(
            query=query_text,
            contexts=sources,
            llm_provider=llm_provider
        )

        # Step 3: Combine results
        result = {
            "query": query_text,
            "response": generation_result["text"],
            "sources": sources,
            "llm_provider": llm_provider or settings.default_llm_provider,
            "model": generation_result["model"],
            "token_usage": generation_result["token_usage"],
            "latency_ms": generation_result["latency_ms"],
            "cost": generation_result["cost"]
        }

        logger.info(f"RAG query complete: {len(sources)} sources, {result['latency_ms']:.0f}ms")
        return result
