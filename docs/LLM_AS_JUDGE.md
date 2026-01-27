# LLM-as-Judge Evaluation System

This document explains the LLM-as-judge evaluation system in RAGLens, which automatically evaluates chatbot responses using Claude or GPT-4 as an expert judge.

## Overview

LLM-as-judge is a powerful technique for evaluating RAG system outputs by using a large language model to score responses across multiple criteria. This provides more nuanced evaluation than simple keyword matching or embedding similarity.

## Evaluation Criteria

The system evaluates responses on 6 dimensions (each scored 0-5):

### 1. Accuracy (0-5)
**Question**: Is the information factually correct based on the provided context?

- **5**: Completely accurate, all facts verified against context
- **3**: Mostly accurate with minor issues
- **0**: Contains incorrect information

### 2. Completeness (0-5)
**Question**: Does it fully address the customer's question?

- **5**: Fully comprehensive, covers all aspects
- **3**: Addresses main points but misses some details
- **0**: Incomplete or missing key information

### 3. Faithfulness (0-5)
**Question**: Is the response grounded in the provided context?

- **5**: Entirely based on context, no hallucinations
- **3**: Mostly grounded with some unsupported statements
- **0**: Makes claims not supported by context

### 4. Tone (0-5)
**Question**: Is the tone appropriate for customer support?

- **5**: Professional, friendly, and empathetic
- **3**: Acceptable but could be warmer/more professional
- **0**: Inappropriate tone (too casual, rude, or cold)

### 5. Relevance (0-5)
**Question**: Is the response relevant to the query's category and intent?

- **5**: Perfect match for category/intent
- **3**: Related but may address wrong aspect
- **0**: Completely off-topic

### 6. Clarity (0-5)
**Question**: Is the response clear and easy to understand?

- **5**: Crystal clear, well-structured
- **3**: Understandable but could be clearer
- **0**: Confusing or poorly structured

## Overall Score

The overall score is the average of all 6 criteria scores.

## Evaluation Output

The LLM-as-judge returns structured JSON with:

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
  "explanation": "The response is highly accurate and faithful to the context...",
  "strengths": [
    "Clear step-by-step instructions",
    "Professional and friendly tone"
  ],
  "weaknesses": [
    "Could mention password requirements",
    "Slightly verbose"
  ],
  "suggested_improvement": "Consider adding information about password complexity requirements"
}
```

## How It Works

### 1. Prompt Construction

The system creates a detailed prompt that includes:
- The customer's original query
- The retrieved contexts with metadata (category, intent, flags, relevance scores)
- The chatbot's generated response
- Expected category/intent (if known from golden set)
- Detailed scoring rubric

Example prompt structure:
```
CUSTOMER QUERY:
How do I reset my password?

RETRIEVED CONTEXT PROVIDED TO CHATBOT:
[Context 1] (Category: ACCOUNT, Intent: password_reset, Flags: BI, Relevance: 0.92)
To reset your password: 1. Visit login page 2. Click 'Forgot Password'...

CHATBOT'S RESPONSE:
To reset your password, please follow these steps:
1. Go to the login page
2. Click on "Forgot Password"
...

Expected Classification:
- Category: ACCOUNT
- Intent: password_reset

Please evaluate the response on the following criteria (score each 0-5):
[detailed rubric]
```

### 2. LLM Evaluation

The prompt is sent to Claude or GPT-4 with:
- **Temperature**: 0.0 (deterministic for consistency)
- **Max tokens**: 2000
- **System prompt**: Expert evaluator role

### 3. Response Parsing

The LLM returns structured JSON, which is parsed and stored in the database.

## API Usage

### Evaluate Single Response

```bash
POST /api/evaluation/run
Content-Type: application/json

{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "evaluator_provider": "anthropic",
  "expected_category": "ACCOUNT",
  "expected_intent": "password_reset",
  "relevant_doc_ids": ["doc_123", "doc_456"]
}
```

### Batch Evaluation

```bash
POST /api/evaluation/batch
Content-Type: application/json

{
  "query_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ],
  "batch_name": "Golden Set v1",
  "evaluator_provider": "anthropic"
}
```

### Get Evaluation Results

```bash
GET /api/evaluation/{evaluation_id}
```

### List All Evaluations

```bash
GET /api/evaluation/?skip=0&limit=50&evaluation_type=llm_judge
```

## Python SDK Usage

```python
from app.evaluation.generation.llm_judge import LLMJudge

# Initialize judge
judge = LLMJudge(provider="anthropic")

# Evaluate a response
evaluation = await judge.evaluate_response(
    query="How do I reset my password?",
    response="To reset your password, follow these steps...",
    contexts=[
        {
            "text": "Password reset instructions...",
            "score": 0.92,
            "metadata": {
                "category": "ACCOUNT",
                "intent": "password_reset"
            }
        }
    ],
    expected_category="ACCOUNT",
    expected_intent="password_reset"
)

print(f"Overall Score: {evaluation['overall_score']}/5")
```

## Retrieval Metrics

In addition to generation quality, the system also evaluates retrieval performance:

### Precision@K
- **Definition**: Proportion of retrieved documents that are relevant
- **Formula**: `relevant_retrieved / k`
- **Example**: If top-5 contains 3 relevant docs, P@5 = 0.6

### Recall@K
- **Definition**: Proportion of relevant documents that were retrieved
- **Formula**: `relevant_retrieved / total_relevant`
- **Example**: If 3 out of 5 relevant docs retrieved, R@5 = 0.6

### F1 Score
- **Definition**: Harmonic mean of precision and recall
- **Formula**: `2 * (P * R) / (P + R)`

### Mean Reciprocal Rank (MRR)
- **Definition**: Reciprocal of rank of first relevant document
- **Formula**: `1 / rank_of_first_relevant`
- **Example**: If first relevant doc is at position 2, MRR = 0.5

### Average Precision (AP)
- **Definition**: Average of precision values at each relevant document position

## Testing

Run the evaluation test script:

```bash
cd scripts
python test_evaluation.py
```

This will:
1. Evaluate a good response (should get high scores)
2. Evaluate a poor response (should get low scores)
3. Calculate retrieval metrics
4. Show score distributions

## Golden Set Evaluation

For golden set testing (where you have expected answers), use the golden set evaluation:

```python
evaluation = await judge.evaluate_against_golden_set(
    query="How do I reset my password?",
    response="Generated response...",
    expected_answer="To reset your password: 1. Visit login...",
    contexts=contexts,
    category="ACCOUNT",
    intent="password_reset"
)
```

Golden set evaluation includes additional criteria:
- **Semantic Similarity**: Does it convey the same meaning?
- **Information Coverage**: Does it include all key information?
- **Tone Match**: Does it match the expected tone?
- **Conciseness**: Is it appropriately concise?

## Best Practices

### 1. Use Deterministic Settings
- Temperature = 0.0 for consistent evaluations
- Same model for baseline comparisons

### 2. Provide Rich Context
- Include all retrieved documents with metadata
- Provide expected category/intent when available
- Include relevance scores

### 3. Batch Evaluations
- Use batch API for golden sets (more efficient)
- Run periodic evaluations to detect regressions

### 4. Monitor Trends
- Track average scores over time
- Alert on score drops >10% from baseline
- Compare across different configurations

### 5. Combine Metrics
- Don't rely on overall score alone
- Look at individual criteria (faithfulness is critical)
- Check retrieval metrics (P@K, R@K)

## Cost Considerations

LLM-as-judge requires LLM API calls for each evaluation:

### Per Evaluation Cost (approximate)
- **Prompt tokens**: ~800-1500 (depending on context length)
- **Response tokens**: ~300-500
- **Total per evaluation**: ~$0.01-0.03 with Claude Sonnet

### Cost Optimization
- Use smaller model for initial screening (Claude Haiku)
- Use Opus/GPT-4 only for critical golden set evaluations
- Cache evaluation results to avoid re-running
- Batch evaluations for efficiency

## Limitations

1. **Subjectivity**: Even LLMs can have biases in scoring
2. **Cost**: Requires API calls (unlike automated metrics)
3. **Latency**: Takes 2-5 seconds per evaluation
4. **Context window**: Limited by model's max tokens

## Future Enhancements

- **Multi-judge consensus**: Use multiple LLMs and average scores
- **Human-in-the-loop**: Flag low-confidence evaluations for human review
- **Custom criteria**: Allow users to define domain-specific criteria
- **Calibration**: Tune scoring against human evaluations
- **Caching**: Cache evaluations for identical query/response pairs
