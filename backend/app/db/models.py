"""SQLAlchemy database models for RAGLens."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.database import Base


class Query(Base):
    """User query model."""
    __tablename__ = "queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    llm_provider = Column(String(50), nullable=False)  # claude or openai
    retrieval_config = Column(JSON, nullable=True)  # Store retrieval params

    # Relationships
    responses = relationship("Response", back_populates="query", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="query", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Query(id={self.id}, query_text='{self.query_text[:50]}...')>"


class Response(Base):
    """LLM response model."""
    __tablename__ = "responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id"), nullable=False)
    response_text = Column(Text, nullable=False)
    sources_json = Column(JSON, nullable=False)  # List of retrieved chunks with scores
    latency_ms = Column(Float, nullable=False)
    token_usage = Column(JSON, nullable=False)  # {prompt_tokens, completion_tokens, total_tokens}
    cost = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    query = relationship("Query", back_populates="responses")

    def __repr__(self):
        return f"<Response(id={self.id}, query_id={self.query_id})>"


class Evaluation(Base):
    """Evaluation results model."""
    __tablename__ = "evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id"), nullable=False)
    evaluation_type = Column(String(50), nullable=False)  # retrieval, generation, combined
    scores_json = Column(JSON, nullable=False)  # Dictionary of metric scores
    evaluator = Column(String(100), nullable=False)  # Which LLM evaluated
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSON, nullable=True)  # Additional evaluation metadata

    # Relationships
    query = relationship("Query", back_populates="evaluations")

    def __repr__(self):
        return f"<Evaluation(id={self.id}, type={self.evaluation_type})>"


class GoldenTestSet(Base):
    """Golden test set model."""
    __tablename__ = "golden_test_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_cases = relationship("GoldenTestCase", back_populates="test_set", cascade="all, delete-orphan")
    evaluation_runs = relationship("EvaluationRun", back_populates="test_set")

    def __repr__(self):
        return f"<GoldenTestSet(id={self.id}, name='{self.name}')>"


class GoldenTestCase(Base):
    """Individual test case in a golden set."""
    __tablename__ = "golden_test_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_set_id = Column(UUID(as_uuid=True), ForeignKey("golden_test_sets.id"), nullable=False)
    query = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=False)
    relevant_doc_ids = Column(ARRAY(String), nullable=True)  # List of relevant chunk IDs
    category = Column(String(100), nullable=True)
    intent = Column(String(100), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    test_set = relationship("GoldenTestSet", back_populates="test_cases")

    def __repr__(self):
        return f"<GoldenTestCase(id={self.id}, category='{self.category}')>"


class EvaluationRun(Base):
    """Batch evaluation run model."""
    __tablename__ = "evaluation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_set_id = Column(UUID(as_uuid=True), ForeignKey("golden_test_sets.id"), nullable=False)
    config_snapshot = Column(JSON, nullable=False)  # Store config used for this run
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed
    results_json = Column(JSON, nullable=True)  # Aggregated results
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    test_set = relationship("GoldenTestSet", back_populates="evaluation_runs")
    metrics = relationship("Metric", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EvaluationRun(id={self.id}, status='{self.status}')>"


class Metric(Base):
    """Metrics model for time-series tracking."""
    __tablename__ = "metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=True)
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id"), nullable=True)
    metric_type = Column(String(100), nullable=False)  # latency, cost, retrieval_score, generation_score
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    tags = Column(JSON, nullable=True)  # Additional metadata for filtering

    # Relationships
    run = relationship("EvaluationRun", back_populates="metrics")

    def __repr__(self):
        return f"<Metric(id={self.id}, type='{self.metric_type}', value={self.value})>"
