"""OpenAI embeddings wrapper."""
import logging
from typing import List
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIEmbeddings:
    """Wrapper for OpenAI embeddings API."""

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize OpenAI embeddings.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Embedding model name (defaults to settings)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.embedding_model
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.dimensions = settings.embedding_dimensions

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimensions
        )

        return response.data[0].embedding

    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts
            batch_size: Process in batches to avoid rate limits

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            logger.info(f"Embedding batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}")

            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
                dimensions=self.dimensions
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings
