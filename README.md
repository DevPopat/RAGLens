# RAGLens

RAG evaluation platform built around a customer service chatbot. Ingest a knowledge base, chat with the system, and get deep insight into why responses are good or bad — down to individual claims, retrieved chunks, and question components.

## Tech Stack

- **Backend**: FastAPI + PostgreSQL + ChromaDB
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **LLM Providers**: Anthropic Claude + OpenAI (configurable per request)
- **Evaluation**: RAGAS framework + LLM-as-judge analysis
- **Dataset**: [Bitext Customer Support](https://github.com/bitext/customer-support-llm-chatbot-training-dataset) — 26,872 Q&A pairs across 27 categories

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key
- OpenAI API key (used for embeddings)

### Setup

```bash
git clone <repo-url>
cd RAGLens
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
POSTGRES_PASSWORD=your_secure_password
```

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

Data ingestion runs automatically on first start if ChromaDB is empty.

---

## Evaluation System

RAGLens provides two evaluation paths: **inline evaluation** on live chat messages and **batch evaluation** against golden test sets. Both use the same underlying RAGAS metrics but serve different purposes.

### RAGAS Metrics

| Metric | Type | What it measures |
|---|---|---|
| **Context Precision** | Continuous (0–100%) | Are the retrieved chunks actually relevant to the query? Higher-ranked chunks should be more relevant than lower-ranked ones. |
| **Faithfulness** | Continuous (0–100%) | Are all claims in the response grounded in the retrieved context? Measures hallucination — statements the model invented rather than drew from sources. |
| **Answer Relevancy** | Pass / Fail | Did the response directly and completely answer the user's question? Evaluated by an LLM judge. Binary by design — a response either answers the question or it doesn't. |
| **Context Recall** | Continuous (0–100%) | Did the retrieved context contain all the information needed to produce the expected answer? Requires a ground truth answer. |
| **Answer Correctness** | Continuous (0–100%) | How closely does the generated answer match the expected ground truth in factual content? Requires a ground truth answer. |

**Why Answer Relevancy is pass/fail**: Most answer relevancy metrics use embedding similarity (generate reverse questions from the response, compare to original via cosine similarity). This approach is noisy for verbose customer support answers where step-by-step responses generate diffuse embeddings. RAGLens uses `AspectCritic` — an LLM judge that sees both the question and response and directly evaluates whether it was answered. Binary judgment from an LLM is significantly more reliable than numeric scoring on this task.

---

### Inline Chat Evaluation

Every chat response has a **Retrieved Sources** panel showing the chunks used to generate the answer. 10% of queries are automatically evaluated with RAGAS in the background; any message can also be manually evaluated with "Run Evaluation".

The evaluation panel shows:
- Overall weighted score
- Context Precision, Faithfulness scores with progress bars
- Answer Relevancy as a Relevant / Not Relevant badge

#### Load Detailed Analysis

Clicking **More Details → Load Detailed Analysis** triggers a single on-demand LLM call that breaks down the evaluation into three actionable sections:

**Faithfulness — Claim-Level Verdict**

Every factual claim in the generated response is extracted and individually checked against the retrieved context:

- `Supported` — the claim is directly backed by a retrieved chunk, with the exact source quote shown
- `Unsupported` — the claim has no basis in any retrieved context (hallucinated or assumed)
- `Contradicted` — the claim directly conflicts with what the context says

This turns a single 78% faithfulness score into a list like:
> ✓ "Returns are accepted within 30 days" — *supported by Context 2*
> ⚠ "You can return items purchased with gift cards" — *not found in any context*

**Answer Relevancy — Question Coverage Analysis**

The user's question is decomposed into its component sub-questions or intent parts. Each component is checked against the response:

- `Addressed` — the response directly answers this part, with the exact response quote
- `Partially addressed` — the response touches on it but incompletely
- `Not addressed` — the response ignores this part of the question entirely

This answers: *the response scored "Relevant" overall, but what exactly did it address and what did it miss?*

**Context Precision — Context Utilization Map**

For each retrieved chunk (ranked 1–N), the analysis determines whether the response actually drew from it:

- `Used` — the response clearly incorporates information from this chunk, with the quoted passage
- `Partially used` — the response tangentially draws from this chunk
- `Not used` — this chunk was retrieved but contributed nothing to the response

This reveals retrieval waste: if the top-ranked chunks aren't being used but lower-ranked ones are, it's a signal to tune retrieval parameters or the embedding model.

> **Message type awareness**: For conversational turns that aren't questions (acknowledgments like "thanks", greetings, closures), Question Coverage Analysis is skipped entirely — it's meaningless to ask "did the response answer the question?" when there was no question. Faithfulness and Context Utilization still run.

---

### Golden Set Evaluation Runs

Golden test sets are collections of query + expected answer pairs that represent your ground truth. Batch evaluation runs all cases through the full RAG pipeline and scores each one.

#### Creating a Golden Set

Navigate to **Golden Sets** → create a set → add test cases. Each case has:
- A query (the customer question)
- An expected answer (the ideal response)
- Optional category/intent labels

#### Running an Evaluation

From a golden set, click **Run Evaluation**. Configure:
- LLM provider for generation (Claude or OpenAI)
- LLM provider for evaluation (Claude or OpenAI)
- Top-K retrieved chunks

The run evaluates every test case and stores full results including per-case scores, generated answers, and retrieved sources.

#### Reading Run Results

The results table sorts cases by score ascending (worst first) to surface problems immediately.

**Summary panel** shows:
- Average overall score across all cases
- Pass rate (cases scoring above threshold)
- Total / completed / failed case counts
- Generator and evaluator provider used

**Per-case breakdown** (expand any row):
- Side-by-side expected vs. generated answer
- Context Precision, Faithfulness scores with progress bars
- Answer Relevancy as pass/fail badge — for a batch run with N cases, the displayed score is the fraction of cases where the LLM judge returned "relevant"
- Context Recall and Answer Correctness scores (when ground truth was used)
- **Compare Claims**: LLM-powered side-by-side comparison of expected vs. generated answer, marking each claim from the expected answer as covered, missing, or contradicted in the generated response — with the exact generated quote highlighted in the answer text
- **Show Retrieved Sources**: The actual chunks that were retrieved for this query, with relevance scores and metadata, with toggle to highlight which parts of the generated answer came from which source

---

## Project Structure

```
RAGLens/
├── backend/
│   └── app/
│       ├── api/routes/          # chat, evaluation, golden_set, diagnosis
│       ├── core/
│       │   ├── retrieval/       # RAGRetriever
│       │   ├── generation/      # Claude + OpenAI generators, prompt templates
│       │   ├── vectorstore/     # ChromaDB with OpenAI embeddings
│       │   └── conversation/    # Message type classifier
│       └── evaluation/
│           └── ragas/           # Metrics config, data adapter, evaluator
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── chat/            # ChatWindow, SourcesPanel
│       │   ├── evaluation/      # ScoreDetailModal, DetailedAnalysis
│       │   └── golden-set/      # RunResultsTable, TestCaseForm
│       └── pages/               # ChatPage, EvaluationsPage, GoldenSetsPage
└── docker-compose.yml
```

---

## Development

```bash
# Tail logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service
docker-compose restart backend

# Stop (keeps data)
docker-compose down

# Reset database (destructive)
docker-compose exec postgres psql -U raglens -c "DROP DATABASE raglens; CREATE DATABASE raglens;"
docker-compose restart backend

# Backup database
docker-compose exec postgres pg_dump -U raglens raglens > backup-$(date +%Y%m%d).sql
```

### Backend (local)
```bash
cd backend
uvicorn app.main:app --reload   # dev server on :8000
pytest                          # run tests
black . && flake8 .             # format + lint
```

### Frontend (local)
```bash
cd frontend
npm install
npm run dev    # dev server on :3000
npm run build  # production build
```

---

## License

MIT
