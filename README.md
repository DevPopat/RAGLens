# RAGLens

Customer service chatbot RAG evaluation platform with comprehensive metrics, LLM-as-judge, golden set testing, and interactive dashboard.

## Tech Stack

- **Backend**: FastAPI + PostgreSQL + ChromaDB
- **Frontend**: React + TypeScript + Tailwind CSS + Recharts
- **LLM Providers**: Anthropic Claude + OpenAI (configurable)
- **Dataset**: [Bitext Customer Support](https://github.com/bitext/customer-support-llm-chatbot-training-dataset) - 26,872 Q&A pairs

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key
- OpenAI API key

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd RAGLens
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and add your API keys**:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   OPENAI_API_KEY=sk-your-key-here
   POSTGRES_PASSWORD=your_secure_password
   ```

4. **Start the services**:
   ```bash
   docker-compose up --build
   ```

5. **Access the application**:
   - **Backend API**: http://localhost:8000
   - **API Docs (Swagger)**: http://localhost:8000/docs
   - **Frontend Dashboard**: http://localhost:3000 (coming in Week 2)
   - **Health Check**: http://localhost:8000/health

## Project Structure

```
RAGLens/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry
│   │   ├── config.py        # Configuration
│   │   ├── db/              # Database models
│   │   ├── api/             # API routes
│   │   ├── core/            # RAG pipeline
│   │   └── evaluation/      # Evaluation system
│   ├── data/                # Persistent data (mounted)
│   └── requirements.txt
├── frontend/                 # React frontend (coming soon)
├── docker-compose.yml       # Docker setup
└── .env                     # Environment variables
```

## Development

### View logs:
```bash
docker-compose logs -f backend
docker-compose logs -f postgres
```

### Restart a service:
```bash
docker-compose restart backend
```

### Stop services (keeps data):
```bash
docker-compose down
```

### Reset database (DESTRUCTIVE):
```bash
docker-compose exec postgres psql -U raglens -c "DROP DATABASE raglens; CREATE DATABASE raglens;"
docker-compose restart backend
```

### Backup database:
```bash
docker-compose exec postgres pg_dump -U raglens raglens > backup-$(date +%Y%m%d).sql
```

## Implementation Roadmap

### Week 1: Basic RAG + Simple Evals ✅ (In Progress)
- [x] Docker setup with PostgreSQL
- [x] FastAPI backend structure
- [x] Database models
- [ ] Bitext dataset ingestion
- [ ] ChromaDB integration
- [ ] RAG pipeline (retrieval + generation)
- [ ] Basic evaluation (retrieval metrics + LLM-as-judge)

### Week 2: Golden Set & Dashboard
- [ ] Golden set management
- [ ] Batch evaluation runner
- [ ] React dashboard
- [ ] Chat interface with source inspection
- [ ] Metrics visualization

### Week 3: Improvement Loop
- [ ] Time-series metrics tracking
- [ ] Regression detection
- [ ] Diagnostic insights
- [ ] A/B testing
- [ ] Production deployment

## API Endpoints (Planned)

- `GET /health` - Health check ✅
- `POST /api/chat/query` - Query chatbot with RAG
- `POST /api/evaluation/run` - Evaluate a query
- `POST /api/evaluation/batch` - Batch evaluation
- `GET /api/metrics/summary` - Get metrics summary
- `POST /api/golden-set/` - Create golden test set
- `GET /api/golden-set/` - List golden sets

## License

MIT
