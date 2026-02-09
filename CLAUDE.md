# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAGLens is a RAG (Retrieval-Augmented Generation) evaluation platform built around a customer service chatbot. It ingests the Bitext customer support dataset, serves a chat interface, and evaluates response quality using the RAGAS framework. A diagnosis agent analyzes evaluation results and suggests improvements.

## Development Commands

### Docker (full stack)
```bash
docker-compose up --build          # Start all services (postgres, backend, frontend)
docker-compose logs -f backend     # Tail backend logs
docker-compose logs -f frontend    # Tail frontend logs
```

### Backend (FastAPI, Python 3.11)
```bash
cd backend
uvicorn app.main:app --reload      # Dev server on :8000
pytest                             # Run all tests
pytest tests/test_foo.py::test_bar # Run single test
black .                            # Format
flake8 .                           # Lint
mypy .                             # Type check
```

### Frontend (React 18 + Vite + TypeScript)
```bash
cd frontend
npm install                        # Install deps
npm run dev                        # Dev server on :3000 (HMR enabled)
npm run build                      # Production build (tsc + vite)
npm run lint                       # ESLint
```

### Data Ingestion
```bash
python scripts/ingest_data.py      # Load Bitext dataset into ChromaDB
```
The Docker entrypoint auto-runs ingestion if ChromaDB is empty.

## Architecture

### Backend (`backend/app/`)

**Entry point**: `main.py` — FastAPI app with CORS, request logging, and exception handling middleware. Database tables are created on startup.

**Config**: `config.py` — Pydantic Settings loaded from environment variables. Controls LLM provider choice (Anthropic/OpenAI), model names, retrieval parameters (top_k, chunk_size), and paths.

**API routes** (`api/routes/`):
- `chat.py` — `POST /api/chat/query`. Classifies the message type (question, follow_up, acknowledgment, greeting, closure), then routes to either the RAG pipeline or a direct response. 10% of queries are evaluated in the background asynchronously.
- `evaluation.py` — Single query evaluation and batch runs against golden sets.
- `golden_set.py` — CRUD for golden test sets and test cases.
- `diagnosis.py` — `GET /api/diagnosis/report`, `/summary`, `/alerts`.

**Core pipeline** (`core/`):
- `ingestion/` — BitetDatasetLoader (80/20 train/test split), BitetChunker (chunks with category/intent metadata)
- `vectorstore/chromadb_store.py` — ChromaDB PersistentClient with OpenAI embeddings (text-embedding-3-small)
- `retrieval/retriever.py` — RAGRetriever orchestrates retrieve → generate
- `generation/` — Dual LLM support: `claude.py` (AsyncAnthropic) and `openai_gen.py` (AsyncOpenAI). Prompt templates in `prompt_templates.py`
- `conversation/classifier.py` — MessageClassifier detects message types to skip retrieval for non-questions
- `embeddings/` — OpenAI embeddings wrapper

**Evaluation** (`evaluation/`):
- `ragas/` — RAGAS evaluator with metrics: context precision, faithfulness, answer relevancy (without ground truth) or context recall, answer correctness (with ground truth)
- `diagnosis/agent.py` — DiagnosisAgent analyzes evaluation patterns and suggests improvements

**Database** (`db/`): PostgreSQL via async SQLAlchemy. Models: Query, Response, Evaluation, GoldenTestSet, GoldenTestCase, EvaluationRun, Metric.

### Frontend (`frontend/src/`)

**Routing** (`App.tsx`): `/` (Dashboard), `/chat` (Chat), `/evaluations`, `/golden-sets`, `/golden-sets/:id`

**State management**: Custom hooks pattern — no Redux/Zustand. Each domain has a hook (`useChat`, `useEvaluations`, `useDiagnosis`). `AppContext` handles global notifications and loading state. Chat state persists to localStorage.

**API layer** (`api/`): Axios client configured to `VITE_API_BASE_URL` (default `http://localhost:8000/api`). Service files per domain: `chat.ts`, `evaluation.ts`, `goldenSet.ts`, `diagnosis.ts`.

### Key Data Flow
1. User sends message → frontend `POST /api/chat/query` with conversation history
2. Backend classifies message type → routes to RAG pipeline or direct response
3. RAG: query ChromaDB → retrieve top-k chunks → generate with LLM → return response with sources, token usage, cost
4. Frontend stores in localStorage, displays sources panel
5. Background: 10% sample evaluated with RAGAS metrics

## Environment Variables

Required in `.env` (see `.env.example`):
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` — LLM API keys
- `DATABASE_URL` — PostgreSQL connection string
- `POSTGRES_PASSWORD` — Database password
- `VITE_API_BASE_URL` — Frontend API target (default `http://localhost:8000/api`)

## Docker Services

Three services on `raglens_network` bridge:
- **postgres** (15-alpine) on :5432 with health check
- **backend** on :8000, depends on postgres healthy, mounts `data/` volume for ChromaDB
- **frontend** on :3000, depends on backend
