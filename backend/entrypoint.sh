#!/bin/bash
set -e

echo "Starting RAGLens backend..."

# Check if ChromaDB has data and run ingestion if needed
python -c "
from app.core.vectorstore.chromadb_store import ChromaDBStore
store = ChromaDBStore()
stats = store.get_collection_stats()
exit(0 if stats['total_chunks'] > 0 else 1)
" && echo "ChromaDB already has data, skipping ingestion." || {
    echo "ChromaDB is empty, running ingestion..."
    python scripts/ingest_data.py
}

# Start the server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
