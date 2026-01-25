# RAGLens Setup Guide

Complete setup instructions for RAGLens - Customer Service RAG Evaluation Platform.

## Prerequisites

- Docker and Docker Compose installed
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Quick Start (5 minutes)

### Step 1: Clone and Setup Environment

```bash
# Navigate to project directory
cd RAGLens

# Create .env file from template
cp .env.example .env
```

### Step 2: Add API Keys

Edit `.env` and add your API keys:

```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
OPENAI_API_KEY=sk-your-actual-key-here
POSTGRES_PASSWORD=your_secure_password_here
```

### Step 3: Start Services

```bash
# Build and start all services (PostgreSQL + Backend)
docker-compose up --build
```

Wait for:
- ✅ `raglens-postgres` - PostgreSQL ready
- ✅ `raglens-backend` - FastAPI server running on port 8000

### Step 4: Verify Installation

Open http://localhost:8000/docs in your browser to see the API documentation.

Test health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "raglens-api",
  "version": "0.1.0"
}
```

## Data Ingestion (One-time setup)

### Step 5: Ingest Bitext Dataset

This downloads the customer support dataset and indexes it in ChromaDB:

```bash
# Enter the backend container
docker-compose exec backend bash

# Run the ingestion script
python scripts/ingest_data.py
```

The script will:
1. Download 26,872 customer support Q&A pairs from Bitext GitHub
2. Chunk the documents (preserving metadata)
3. Generate embeddings using OpenAI
4. Index in ChromaDB

**Expected output:**
```
[1/4] Loading Bitext dataset...
Dataset loaded: 26872 Q&A pairs
Categories: 10, Intents: 27

[2/4] Chunking documents...
Created 26872 chunks from 26872 Q&A pairs

[3/4] Initializing ChromaDB...
Initialized ChromaDB collection 'customer_support_docs'

[4/4] Adding chunks to ChromaDB (this may take a while)...
✓ Ingestion complete!
Total chunks in collection: 26872
```

**Time:** ~15-20 minutes depending on API rate limits
**Cost:** ~$0.10-0.20 in OpenAI embedding costs

## Testing the RAG Pipeline

### Test Query via API

```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my password?",
    "llm_provider": "claude",
    "top_k": 5
  }'
```

**Expected response:**
```json
{
  "query_id": "uuid-here",
  "query": "How do I reset my password?",
  "response": "To reset your password, follow these steps: ...",
  "sources": [
    {
      "id": "chunk_123",
      "text": "Q: How to reset password?\nA: Click 'Forgot Password'...",
      "score": 0.92,
      "metadata": {
        "category": "account_management",
        "intent": "password_reset"
      }
    }
  ],
  "llm_provider": "claude",
  "model": "claude-3-5-sonnet-20241022",
  "token_usage": {...},
  "latency_ms": 1523.4,
  "cost": 0.0042
}
```

### Test with OpenAI Instead

```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I cancel my subscription?",
    "llm_provider": "openai",
    "top_k": 3
  }'
```

### Test with Category Filtering

```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do refunds work?",
    "filter_category": "billing",
    "llm_provider": "claude"
  }'
```

## API Endpoints

### Available Now ✅

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `POST /api/chat/query` - Query the RAG chatbot

### Coming in Week 2

- `POST /api/evaluation/run` - Evaluate a query
- `POST /api/evaluation/batch` - Batch evaluation on golden set
- `POST /api/golden-set/` - Create golden test sets
- `GET /api/metrics/summary` - Get metrics summary

## Development Workflow

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# PostgreSQL only
docker-compose logs -f postgres
```

### Restart a Service

```bash
docker-compose restart backend
```

### Access Backend Container

```bash
docker-compose exec backend bash
```

### Access PostgreSQL

```bash
docker-compose exec postgres psql -U raglens -d raglens
```

Example queries:
```sql
-- Count queries
SELECT COUNT(*) FROM queries;

-- View recent queries
SELECT id, query_text, llm_provider, timestamp
FROM queries
ORDER BY timestamp DESC
LIMIT 5;

-- View responses with costs
SELECT r.id, q.query_text, r.cost, r.latency_ms
FROM responses r
JOIN queries q ON r.query_id = q.id
ORDER BY r.timestamp DESC
LIMIT 5;
```

### Stop Services

```bash
# Stop but keep data
docker-compose down

# Stop and remove volumes (DESTRUCTIVE!)
docker-compose down -v
```

### Rebuild After Code Changes

```bash
# Rebuild backend only
docker-compose up --build backend

# Rebuild everything
docker-compose up --build
```

## Data Management

### Backup Database

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U raglens raglens > backup-$(date +%Y%m%d).sql

# Backup ChromaDB and datasets
tar -czf data-backup-$(date +%Y%m%d).tar.gz backend/data/
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U raglens raglens < backup-20260123.sql
```

### Reset Database (DESTRUCTIVE)

```bash
docker-compose exec postgres psql -U raglens -c "DROP DATABASE raglens; CREATE DATABASE raglens;"
docker-compose restart backend
```

### Reset ChromaDB (DESTRUCTIVE)

```bash
# Delete ChromaDB data
rm -rf backend/data/chromadb/*

# Re-run ingestion
docker-compose exec backend python scripts/ingest_data.py
```

## Project Structure

```
RAGLens/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app ✅
│   │   ├── config.py            # Configuration ✅
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   └── chat.py      # Chat endpoint ✅
│   │   │   └── schemas/
│   │   │       └── chat.py      # Pydantic models ✅
│   │   ├── core/
│   │   │   ├── ingestion/
│   │   │   │   ├── loader.py    # Dataset loader ✅
│   │   │   │   └── chunker.py   # Chunking logic ✅
│   │   │   ├── embeddings/
│   │   │   │   └── openai_embeddings.py ✅
│   │   │   ├── vectorstore/
│   │   │   │   └── chromadb_store.py ✅
│   │   │   ├── retrieval/
│   │   │   │   └── retriever.py # RAG pipeline ✅
│   │   │   └── generation/
│   │   │       ├── claude.py    # Claude LLM ✅
│   │   │       ├── openai_gen.py # OpenAI LLM ✅
│   │   │       └── prompt_templates.py ✅
│   │   └── db/
│   │       ├── database.py      # DB connection ✅
│   │       └── models.py        # SQLAlchemy models ✅
│   ├── data/                    # Persistent data
│   │   ├── chromadb/           # Vector store
│   │   ├── raw/                # Bitext dataset
│   │   └── golden_sets/        # Test sets
│   ├── Dockerfile              ✅
│   └── requirements.txt        ✅
├── scripts/
│   └── ingest_data.py          # Ingestion script ✅
├── docker-compose.yml          ✅
├── .env.example                ✅
├── README.md                   ✅
└── SETUP.md                    ✅ (this file)
```

## Troubleshooting

### Issue: "Connection refused" to PostgreSQL

**Solution:** Wait for PostgreSQL to be ready. Check health:
```bash
docker-compose logs postgres | grep "ready to accept connections"
```

### Issue: "OpenAI API key not found"

**Solution:** Verify `.env` file has correct keys:
```bash
cat .env | grep OPENAI_API_KEY
```

### Issue: "ChromaDB collection empty"

**Solution:** Run ingestion script:
```bash
docker-compose exec backend python scripts/ingest_data.py
```

### Issue: "Module not found" errors

**Solution:** Rebuild backend container:
```bash
docker-compose up --build backend
```

### Issue: High embedding costs

**Solution:** The dataset has 26k pairs. To test with fewer:
1. Edit `scripts/ingest_data.py`
2. Slice the dataset: `qa_items = qa_items[:100]  # First 100 only`
3. Re-run ingestion

## Next Steps

- **Week 2**: Golden set management + React dashboard
- **Week 3**: Metrics tracking + Regression detection + A/B testing

## Need Help?

- API Docs: http://localhost:8000/docs
- Check logs: `docker-compose logs -f backend`
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)

---

**Phase 1 Complete!** ✅ You now have a working RAG chatbot with retrieval + generation.
