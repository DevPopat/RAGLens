# Metadata Enhancement Guide

## Overview

RAGLens now leverages the rich metadata from the Bitext dataset to improve both retrieval and LLM-as-judge evaluation.

## Enhanced Data Schema

### Input (Bitext CSV)
```csv
flags,instruction,category,intent,response
BQZ,i have a question about cancelling oorder {{Order Number}},ORDER,cancel_order,"..."
```

### Stored in ChromaDB
```python
{
    "text": "Q: <instruction>\nA: <response>",
    "metadata": {
        "flags": "BQZ",           # Variation flags
        "category": "ORDER",       # High-level category
        "intent": "cancel_order",  # Specific intent
        "question": "<instruction>",
        "token_count": 245
    }
}
```

## Flag System Explained

### Lexical Variations
- **M** - Morphological: "activate" vs "activated"
- **L** - Semantic: "billing date" vs "anniversary date"

### Syntactic Structure
- **B** - Basic: "activate my SIM"
- **I** - Interrogative: "how do I activate?"
- **C** - Coordinated: "I have a new SIM, how to activate?"
- **N** - Negation: "I don't want this"

### Language Register
- **P** - Polite: "could you please help"
- **Q** - Colloquial: "can u activ8"
- **W** - Offensive: contains profanity

### Stylistic
- **K** - Keyword: "activate SIM"
- **E** - Abbreviations: "I'm" vs "I am"
- **Z** - Errors/Typos: "activaet"

## Categories & Intents

### 11 Categories, 27 Intents

**ACCOUNT** (6 intents)
- create_account, delete_account, edit_account
- recover_password, registration_problems, switch_account

**CANCELLATION_FEE** (1 intent)
- check_cancellation_fee

**CONTACT** (2 intents)
- contact_customer_service, contact_human_agent

**DELIVERY** (2 intents)
- delivery_options, delivery_period

**FEEDBACK** (2 intents)
- complaint, review

**INVOICE** (2 intents)
- check_invoice, get_invoice

**ORDER** (4 intents)
- cancel_order, change_order, place_order, track_order

**PAYMENT** (2 intents)
- check_payment_methods, payment_issue

**REFUND** (3 intents)
- check_refund_policy, get_refund, track_refund

**SHIPPING_ADDRESS** (2 intents)
- change_shipping_address, set_up_shipping_address

**SUBSCRIPTION** (1 intent)
- newsletter_subscription

## Enhanced RAG Prompts

### Before (Basic)
```
[Context 1] (Category: ORDER, Intent: cancel_order, Relevance: 0.92)
Q: How do I cancel my order?
A: ...
```

### After (Enhanced with Flags)
```
[Context 1]
Category: ORDER
Intent: cancel_order
Query style: Basic syntactic structure, Colloquial language, Contains errors/typos
Relevance Score: 0.92

Q: How do I cancel my order?
A: ...
```

**Benefits:**
- LLM understands the variation type
- Can adapt response tone (formal for P flag, understanding for Z flag)
- Better context for evaluation

## LLM-as-Judge Enhancements

### Evaluation Criteria (Enhanced)

**1. Accuracy** (0-5)
- Verifies against retrieved context
- Checks category/intent alignment

**2. Completeness** (0-5)
- Addresses all aspects of query
- Considers intent-specific requirements

**3. Faithfulness** (0-5)
- Grounded in provided context
- No hallucinations

**4. Tone** (0-5)
- Appropriate for customer support
- **NEW**: Adapts based on query flags (P=formal, Q=friendly)

**5. Relevance** (0-5)
- **NEW**: Matches category and intent
- Retrieves correct information type

**6. Clarity** (0-5)
- Easy to understand
- Well-structured

### Evaluation Output

```json
{
    "scores": {
        "accuracy": 5,
        "completeness": 4,
        "faithfulness": 5,
        "tone": 5,
        "relevance": 5,
        "clarity": 4
    },
    "overall_score": 4.67,
    "explanation": "Response accurately addresses ORDER/cancel_order intent...",
    "strengths": [
        "Clearly outlines cancellation steps",
        "Professional and empathetic tone"
    ],
    "weaknesses": [
        "Could include refund timeline information"
    ],
    "suggested_improvement": "Add expected refund processing time"
}
```

## Golden Set Evaluation (Enhanced)

When evaluating against golden sets with expected answers:

```python
{
    "query": "i have a question about cancelling oorder {{Order Number}}",
    "expected_category": "ORDER",
    "expected_intent": "cancel_order",
    "expected_answer": "...",
    "flags": "BQZ"  # Basic + Colloquial + Typos
}
```

**Evaluation considers:**
1. **Semantic Similarity**: Same meaning as expected
2. **Information Coverage**: All key points included
3. **Accuracy**: Factually correct
4. **Tone Match**: Professional tone maintained
5. **Conciseness**: Not too verbose/brief

**Flag-aware scoring:**
- Queries with "Z" flag (typos): Don't penalize for understanding variations
- Queries with "Q" flag (colloquial): Expect friendly but professional tone
- Queries with "P" flag (polite): Expect formal, courteous response

## Usage Examples

### Filter by Category
```python
curl -X POST http://localhost:8000/api/chat/query \
  -d '{"query": "refund question", "filter_category": "REFUND"}'
```

### Filter by Intent
```python
curl -X POST http://localhost:8000/api/chat/query \
  -d '{"query": "track my refund", "filter_intent": "track_refund"}'
```

### Retrieve Flag Statistics
```python
# In Python
loader = BitetDatasetLoader(use_csv=True)
items = await loader.load_or_download()
stats = loader.get_dataset_stats(items)

print(stats["flags"]["tag_distribution"])
# Output: [('B', 15234), ('I', 8912), ('Q', 5432), ...]
```

## Impact on Metrics

### Retrieval Metrics
- **Precision@K**: Can measure category/intent accuracy
- **Recall@K**: Track if correct intent documents retrieved
- **Context Precision**: Improved with metadata filtering

### Generation Metrics (LLM-as-Judge)
- **Relevance Score**: Uses category/intent alignment
- **Tone Score**: Adapts based on query flags
- **Overall Quality**: More nuanced evaluation

### Example Diagnostic
```
Low scores detected for intent: "recover_password"
Flag distribution: 60% have "Z" flag (typos)
Suggestion: Improve typo-tolerant retrieval for this intent
```

## Week 2 Integration

These enhancements set the foundation for:

1. **Golden Set Creation**
   - Select diverse test cases across categories/intents/flags
   - Ensure coverage of all 27 intents
   - Include variation types (P, Q, Z, etc.)

2. **Batch Evaluation**
   - Evaluate retrieval: Does it retrieve correct category/intent?
   - Evaluate generation: Does it adapt tone based on flags?
   - Track per-category, per-intent, per-flag performance

3. **Diagnostic Insights** (Week 3)
   - "Intent 'recover_password' with flag 'Z' has 20% lower scores"
   - "Category 'REFUND' shows high retrieval precision but low generation scores"
   - "Queries with 'Q' flag (colloquial) score lower on tone - adjust system prompt"

## Migration Notes

**No database migration needed** - metadata already captured in:
- `Query.retrieval_config` (JSON field)
- `Response.sources_json` (includes metadata)
- `Evaluation.scores_json` (evaluation results)

**Updated files:**
- ✅ `loader.py` - CSV parsing with flags
- ✅ `chunker.py` - Preserves flags in metadata (already done)
- ✅ `prompt_templates.py` - Enhanced prompts with flag context
- ✅ `chromadb_store.py` - Stores rich metadata (already done)

## Testing

```bash
# 1. Download CSV dataset
docker-compose exec backend python -c "
from app.core.ingestion.loader import BitetDatasetLoader
import asyncio
loader = BitetDatasetLoader(use_csv=True)
asyncio.run(loader.download_dataset())
"

# 2. Check dataset stats
docker-compose exec backend python scripts/ingest_data.py

# 3. Test query with metadata
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "how do i canel my order", "llm_provider": "claude"}'

# Response should show flags in sources:
# "metadata": {"flags": "BZ", "category": "ORDER", "intent": "cancel_order"}
```

---

**Status**: Metadata enhancement complete! Ready for Week 2 golden set evaluation.
