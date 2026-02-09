"""ChromaDB vector store integration."""
import logging
from typing import List, Dict, Any, Optional
import chromadb

from app.config import settings
from app.core.embeddings.openai_embeddings import OpenAIEmbeddings

logger = logging.getLogger(__name__)


class ChromaDBStore:
    """ChromaDB vector store for RAG retrieval."""

    def __init__(
        self,
        collection_name: str = "customer_support_docs",
        persist_directory: str = None
    ):
        """Initialize ChromaDB store.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist ChromaDB data
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.chromadb_path

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Bitext customer support Q&A pairs"}
        )

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings()

        logger.info(f"Initialized ChromaDB collection '{self.collection_name}' at {self.persist_directory}")

    async def add_documents(
        self,
        chunks: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """Add document chunks to the vector store.

        Args:
            chunks: List of chunk dictionaries with 'text' and 'metadata'
            batch_size: Batch size for embedding generation

        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0

        logger.info(f"Adding {len(chunks)} chunks to ChromaDB...")

        # Extract texts for embedding
        texts = [chunk["text"] for chunk in chunks]

        # Generate embeddings in batches
        embeddings = await self.embeddings.embed_batch(texts, batch_size=batch_size)

        # Prepare data for ChromaDB
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [chunk["metadata"] for chunk in chunks]

        # Add to collection in batches
        for i in range(0, len(chunks), batch_size):
            end_idx = min(i + batch_size, len(chunks))

            self.collection.add(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )

            logger.info(f"Added batch {i // batch_size + 1}/{(len(chunks) - 1) // batch_size + 1}")

        logger.info(f"Successfully added {len(chunks)} chunks to ChromaDB")
        return len(chunks)

    async def query(
        self,
        query_text: str,
        top_k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Query the vector store for similar documents.

        Args:
            query_text: Query string
            top_k: Number of results to return (defaults to settings)
            filter_metadata: Optional metadata filter (e.g., {"category": "billing"})

        Returns:
            List of results with text, metadata, and scores
        """
        top_k = top_k or settings.top_k

        # Generate query embedding
        query_embedding = await self.embeddings.embed_text(query_text)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata  # Metadata filtering
        )

        # Format results
        formatted_results = []

        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1.0 - results["distances"][0][i],  # Convert distance to similarity
                "distance": results["distances"][0][i]
            })

        logger.info(f"Retrieved {len(formatted_results)} results for query")
        return formatted_results

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()

        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "persist_directory": self.persist_directory
        }

    def reset_collection(self):
        """Delete and recreate the collection. WARNING: Deletes all data!"""
        logger.warning(f"Resetting collection '{self.collection_name}'")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Bitext customer support Q&A pairs"}
        )
        logger.info("Collection reset complete")
