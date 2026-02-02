"""Pydantic schemas for evaluation endpoints."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


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
