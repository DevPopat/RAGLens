"""Evaluation module for RAG system.

This module provides RAGAS-based evaluation for RAG responses.
The legacy LLMJudge and RetrievalEvaluator are deprecated.
"""
from .ragas import RAGASEvaluator, RAGASMetricConfig, compute_overall_score

__all__ = [
    "RAGASEvaluator",
    "RAGASMetricConfig",
    "compute_overall_score",
]
