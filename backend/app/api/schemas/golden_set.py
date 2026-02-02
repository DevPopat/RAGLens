"""Pydantic schemas for Golden Set endpoints."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


# ============== Test Case Schemas ==============

class TestCaseCreate(BaseModel):
    """Schema for creating a single test case."""
    query: str = Field(..., description="The customer query/question")
    expected_answer: str = Field(..., description="The expected/ideal answer")
    category: Optional[str] = Field(None, description="Category (e.g., ACCOUNT, ORDER)")
    intent: Optional[str] = Field(None, description="Intent (e.g., password_reset, track_order)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata (flags, etc.)")


class TestCaseResponse(BaseModel):
    """Schema for test case response."""
    id: UUID
    test_set_id: UUID
    query: str
    expected_answer: str
    category: Optional[str]
    intent: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class TestCaseUpdate(BaseModel):
    """Schema for updating a test case."""
    query: Optional[str] = None
    expected_answer: Optional[str] = None
    category: Optional[str] = None
    intent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============== Golden Set Schemas ==============

class GoldenSetCreate(BaseModel):
    """Schema for creating a golden test set."""
    name: str = Field(..., description="Unique name for the test set")
    description: Optional[str] = Field(None, description="Description of the test set")


class GoldenSetResponse(BaseModel):
    """Schema for golden set response."""
    id: UUID
    name: str
    description: Optional[str]
    version: int
    created_at: datetime
    updated_at: Optional[datetime]
    test_case_count: int = Field(0, description="Number of test cases in this set")

    class Config:
        from_attributes = True


class GoldenSetDetail(BaseModel):
    """Schema for golden set with all test cases."""
    id: UUID
    name: str
    description: Optional[str]
    version: int
    created_at: datetime
    updated_at: Optional[datetime]
    test_cases: List[TestCaseResponse]

    class Config:
        from_attributes = True


class GoldenSetUpdate(BaseModel):
    """Schema for updating a golden set."""
    name: Optional[str] = None
    description: Optional[str] = None


class GoldenSetListResponse(BaseModel):
    """Paginated list of golden sets."""
    golden_sets: List[GoldenSetResponse]
    total: int
    skip: int
    limit: int


# ============== Bulk Import Schemas ==============

class BulkImportRequest(BaseModel):
    """Schema for bulk importing test cases from CSV."""
    test_set_id: UUID = Field(..., description="Target golden set ID")
    csv_path: Optional[str] = Field(None, description="Path to CSV file (server-side)")
    max_cases: Optional[int] = Field(None, description="Max cases to import (for sampling)")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    intents: Optional[List[str]] = Field(None, description="Filter by intents")


class BulkImportResponse(BaseModel):
    """Response from bulk import."""
    test_set_id: UUID
    imported_count: int
    skipped_count: int
    errors: List[str]


# ============== Evaluation Run Schemas ==============

class RunTestSetRequest(BaseModel):
    """Schema for running evaluation on a golden set."""
    llm_provider: str = Field("anthropic", description="LLM provider (anthropic or openai)")
    evaluator_provider: str = Field("anthropic", description="Evaluator LLM provider")
    top_k: int = Field(5, description="Number of documents to retrieve")
    run_name: Optional[str] = Field(None, description="Optional name for this run")


class TestCaseResult(BaseModel):
    """Result for a single test case."""
    test_case_id: UUID
    query: str
    expected_answer: str
    generated_answer: str
    scores: Dict[str, Any]
    overall_score: Optional[float]
    retrieval_metrics: Optional[Dict[str, Any]]
    latency_ms: float
    status: str  # success, error


class RunTestSetResponse(BaseModel):
    """Response from running a golden set evaluation."""
    run_id: UUID
    test_set_id: UUID
    test_set_name: str
    status: str  # pending, running, completed, failed
    total_cases: int
    completed_cases: int
    failed_cases: int
    results: Optional[List[TestCaseResult]]
    summary: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]


class EvaluationRunResponse(BaseModel):
    """Schema for evaluation run details."""
    id: UUID
    test_set_id: UUID
    status: str
    config_snapshot: Dict[str, Any]
    results_json: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class EvaluationRunListResponse(BaseModel):
    """List of evaluation runs."""
    runs: List[EvaluationRunResponse]
    total: int
