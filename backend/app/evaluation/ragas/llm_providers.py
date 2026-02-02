"""LLM provider setup for RAGAS evaluation.

RAGAS uses LangChain-style LLM wrappers for evaluation.
"""
import logging
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from app.config import settings

logger = logging.getLogger(__name__)


def get_ragas_llm(provider: str = "anthropic", model: Optional[str] = None):
    """Get RAGAS-compatible LLM wrapper for evaluation.

    Args:
        provider: "anthropic" or "openai"
        model: Optional model override

    Returns:
        LangchainLLMWrapper for RAGAS
    """
    if provider == "anthropic":
        model = model or settings.claude_eval_model
        llm = ChatAnthropic(
            model=model,
            api_key=settings.anthropic_api_key,
            temperature=0.0,  # Deterministic for evaluation
            max_tokens=2000,
        )
        logger.info(f"Initialized RAGAS LLM with Anthropic ({model})")
    elif provider == "openai":
        model = model or settings.openai_model
        llm = ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            temperature=0.0,
            max_tokens=2000,
        )
        logger.info(f"Initialized RAGAS LLM with OpenAI ({model})")
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return LangchainLLMWrapper(llm)


def get_ragas_embeddings():
    """Get RAGAS-compatible embeddings wrapper.

    Uses OpenAI embeddings as that's what's configured for the vector store.

    Returns:
        LangchainEmbeddingsWrapper for RAGAS
    """
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
    return LangchainEmbeddingsWrapper(embeddings)
