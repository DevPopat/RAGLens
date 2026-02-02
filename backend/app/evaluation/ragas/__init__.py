"""RAGAS-based evaluation module for RAG systems.

This module replaces the custom LLMJudge and RetrievalEvaluator with
industry-standard RAGAS metrics that use LLM-as-judge methodology.
"""
from .evaluator import RAGASEvaluator
from .metrics import RAGASMetricConfig, compute_overall_score
from .data_adapter import convert_to_ragas_sample, convert_contexts_from_sources

__all__ = [
    "RAGASEvaluator",
    "RAGASMetricConfig",
    "compute_overall_score",
    "convert_to_ragas_sample",
    "convert_contexts_from_sources",
]
