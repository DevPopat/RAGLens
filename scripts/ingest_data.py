#!/usr/bin/env python3
"""Script to ingest Bitext dataset into ChromaDB."""
import asyncio
import os
import sys
from pathlib import Path

# Add correct path for both local and Docker environments
script_dir = Path(__file__).parent.parent
if (script_dir / "backend").exists():
    # Local: /project/backend
    sys.path.insert(0, str(script_dir / "backend"))
else:
    # Docker: /app (app module is directly here)
    sys.path.insert(0, str(script_dir))

from app.core.ingestion.loader import BitetDatasetLoader
from app.core.ingestion.chunker import BitetChunker
from app.core.vectorstore.chromadb_store import ChromaDBStore
from app.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main ingestion pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Bitext dataset ingestion")
    logger.info("=" * 60)

    # Step 1: Load dataset and create 80/20 train/test split
    logger.info("\n[1/4] Loading Bitext dataset and creating train/test split...")
    loader = BitetDatasetLoader(raw_data_path=settings.raw_data_path)
    train_items, test_items = loader.load_and_split(test_size=0.2, random_seed=42)

    # Only index training data; test set is held out for evaluation
    qa_items = train_items

    # Get stats
    stats = loader.get_dataset_stats(qa_items)
    logger.info(f"Training set: {stats['total']} Q&A pairs")
    logger.info(f"Test holdout: {len(test_items)} Q&A pairs (saved to bitext_test_holdout.json)")
    logger.info(f"Categories: {stats['categories']['count']}, Intents: {stats['intents']['count']}")
    logger.info(f"Top categories: {stats['categories']['breakdown'][:5]}")

    # Step 2: Chunk documents
    logger.info("\n[2/4] Chunking documents...")
    chunker = BitetChunker(
        max_tokens=settings.chunk_size,
        overlap=settings.chunk_overlap
    )
    chunks = chunker.chunk_batch(qa_items)
    logger.info(f"Created {len(chunks)} chunks from {len(qa_items)} Q&A pairs")

    # Sample chunk info
    if chunks:
        sample = chunks[0]
        logger.info(f"Sample chunk metadata: {sample['metadata']}")
        logger.info(f"Sample text preview: {sample['text'][:200]}...")

    # Step 3: Initialize ChromaDB
    logger.info("\n[3/4] Initializing ChromaDB...")
    vector_store = ChromaDBStore()

    # Check if collection already has data
    existing_stats = vector_store.get_collection_stats()
    if existing_stats["total_chunks"] > 0:
        logger.warning(f"Collection already contains {existing_stats['total_chunks']} chunks. Resetting...")
        vector_store.reset_collection()

    # Step 4: Add to vector store
    logger.info("\n[4/4] Adding chunks to ChromaDB (this may take a while)...")
    added_count = await vector_store.add_documents(chunks, batch_size=50)

    # Final stats
    logger.info("\n" + "=" * 60)
    logger.info("Ingestion complete!")
    logger.info("=" * 60)
    logger.info(f"Added {added_count} chunks")
    final_stats = vector_store.get_collection_stats()
    logger.info(f"Total chunks in collection: {final_stats['total_chunks']}")
    logger.info(f"Collection: {final_stats['collection_name']}")
    logger.info(f"Location: {final_stats['persist_directory']}")

    # Test query
    logger.info("\n" + "=" * 60)
    logger.info("Testing retrieval...")
    logger.info("=" * 60)
    test_query = "How do I reset my password?"
    results = await vector_store.query(test_query, top_k=3)

    logger.info(f"\nTest query: '{test_query}'")
    logger.info(f"Retrieved {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        logger.info(f"Result {i}:")
        logger.info(f"  Score: {result['score']:.4f}")
        logger.info(f"  Category: {result['metadata'].get('category')}")
        logger.info(f"  Intent: {result['metadata'].get('intent')}")
        logger.info(f"  Text: {result['text'][:150]}...")
        logger.info("")

    logger.info("Ingestion and testing successful! ✓")


if __name__ == "__main__":
    asyncio.run(main())
