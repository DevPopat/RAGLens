"""Pydantic schemas for evaluation endpoints."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.api.schemas.chat import ConversationMessage


class EvaluationRequest(BaseModel):
    """Request to evaluate a query/response pair using RAGAS."""

    query_id: UUID = Field(..., description="ID of the query to evaluate")
    evaluator_provider: Optional[str] = Field(
        "anthropic",
        description="LLM provider for evaluation (anthropic or openai)"
    )
    expected_category: Optional[str] = Field(
        None,
        description="Expected category (for metadata only)"
    )
    expected_intent: Optional[str] = Field(
        None,
        description="Expected intent (for metadata only)"
    )
    conversation_history: Optional[List[ConversationMessage]] = Field(
        None,
        description="Previous messages for multi-turn conversation context"
    )


class EvaluationResponse(BaseModel):
    """Evaluation result."""

    id: UUID
    query_id: UUID
    evaluation_type: str
    scores: Dict[str, Any] = Field(
        ...,
        description="Evaluation scores (generation + retrieval metrics)"
    )
    evaluator: str = Field(..., description="Evaluator identifier (e.g., anthropic/claude-3-5-sonnet)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional evaluation metadata")
    timestamp: datetime
    latency_ms: Optional[float] = Field(None, description="Evaluation latency in milliseconds")

    class Config:
        from_attributes = True


class BatchEvaluationRequest(BaseModel):
    """Request to evaluate multiple queries in batch."""

    query_ids: List[UUID] = Field(..., description="List of query IDs to evaluate")
    batch_name: Optional[str] = Field(None, description="Name for this batch evaluation")
    evaluator_provider: Optional[str] = Field("anthropic", description="LLM provider")


class BatchEvaluationResponse(BaseModel):
    """Batch evaluation results."""

    batch_name: Optional[str]
    total_queries: int
    successful: int
    failed: int
    results: List[Dict[str, Any]] = Field(..., description="List of evaluation results")
    errors: List[Dict[str, Any]] = Field(..., description="List of errors")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")


class EvaluationListResponse(BaseModel):
    """Paginated list of evaluations."""

    evaluations: List[EvaluationResponse]
    total: int
    skip: int
    limit: int


class ClaimCompareRequest(BaseModel):
    """Request to compare expected vs generated answers at claim level."""

    expected_answer: str = Field(..., description="Ground truth / expected answer")
    generated_answer: str = Field(..., description="LLM-generated answer")


class Claim(BaseModel):
    """A single factual claim extracted from the expected answer."""

    claim: str = Field(..., description="The factual claim")
    status: str = Field(..., description="covered, missing, or contradicted")
    detail: str = Field(..., description="Explanation of the status")
    generated_quote: Optional[str] = Field(
        None,
        description="The relevant quote from the generated answer, if any"
    )


class ClaimCompareResponse(BaseModel):
    """Claim-level comparison between expected and generated answers."""

    claims: List[Claim]


# --- Detailed Analysis Schemas ---


class FaithfulnessClaim(BaseModel):
    """A single factual claim from the response, verified against contexts."""

    statement: str = Field(..., description="The factual claim from the response")
    verdict: str = Field(..., description="supported, unsupported, or contradicted")
    reason: str = Field(..., description="Why this verdict was reached")
    source_quote: Optional[str] = Field(
        None,
        description="Supporting/contradicting quote from context"
    )
    context_index: Optional[int] = Field(
        None,
        description="0-based index of the relevant context"
    )


class FaithfulnessDetail(BaseModel):
    """Detailed faithfulness breakdown with per-claim verdicts."""

    summary: str = Field(..., description="One-sentence summary of faithfulness issues")
    claims: List[FaithfulnessClaim]


class QuestionComponent(BaseModel):
    """A sub-question or intent component of the user's question."""

    component: str = Field(..., description="The sub-question or intent")
    verdict: str = Field(..., description="addressed, partially_addressed, or not_addressed")
    response_quote: Optional[str] = Field(
        None,
        description="Exact substring of response where this was addressed"
    )
    reason: str = Field(..., description="Explanation of the verdict")


class QuestionCoverageDetail(BaseModel):
    """Detailed question coverage analysis."""

    summary: str = Field(..., description="One-sentence summary of question coverage")
    components: List[QuestionComponent]


class ContextUtilization(BaseModel):
    """Assessment of whether a retrieved context was used in the response."""

    context_index: int = Field(..., description="0-based index in the contexts list")
    verdict: str = Field(..., description="used, partially_used, or not_used")
    used_in_response: Optional[str] = Field(
        None,
        description="Quote from response that draws on this context"
    )
    reason: str = Field(..., description="Explanation of the verdict")


class ContextUtilizationDetail(BaseModel):
    """Detailed context utilization map."""

    summary: str = Field(..., description="One-sentence summary of context utilization")
    contexts: List[ContextUtilization]


class DetailedAnalysisRequest(BaseModel):
    """Request for detailed, actionable analysis of a RAG evaluation."""

    query: str = Field(..., description="The user's original question")
    response: str = Field(..., description="The generated answer")
    contexts: List[str] = Field(..., description="List of retrieved context texts")
    scores: Dict[str, float] = Field(
        ..., description="RAGAS metric scores (e.g. faithfulness=0.62)"
    )
    message_type: Optional[str] = Field(
        None,
        description="Message type (question, follow_up, acknowledgment, greeting, closure)"
    )


class DetailedAnalysisResponse(BaseModel):
    """Complete detailed analysis across all metrics."""

    faithfulness: Optional[FaithfulnessDetail] = None
    answer_relevancy: Optional[QuestionCoverageDetail] = None
    context_precision: Optional[ContextUtilizationDetail] = None
