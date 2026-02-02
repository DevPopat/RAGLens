"""Convert RAGLens data formats to RAGAS format.

RAGAS expects a specific data format for evaluation. This module handles
the conversion from our internal formats.
"""
from typing import List, Dict, Any, Optional

from ragas import EvaluationDataset, SingleTurnSample


def convert_contexts_from_sources(sources_json: List[Dict[str, Any]]) -> List[str]:
    """Extract context texts from Response.sources_json format.

    Our sources_json format:
    [{"id": "...", "text": "...", "score": 0.85, "metadata": {...}}, ...]

    RAGAS expects:
    ["context text 1", "context text 2", ...]

    Args:
        sources_json: List of source documents with text, score, metadata

    Returns:
        List of context text strings
    """
    return [src.get("text", "") for src in sources_json if src.get("text")]


def convert_to_ragas_sample(
    query: str,
    response: str,
    contexts: List[Dict[str, Any]],
    ground_truth: Optional[str] = None,
) -> SingleTurnSample:
    """Convert single evaluation data to RAGAS SingleTurnSample.

    Args:
        query: User question
        response: Generated answer
        contexts: Retrieved documents (our format with text, score, metadata)
        ground_truth: Expected answer (optional, from GoldenTestCase)

    Returns:
        RAGAS SingleTurnSample for evaluation
    """
    # Extract context texts from our sources format
    context_texts = convert_contexts_from_sources(contexts)

    sample = SingleTurnSample(
        user_input=query,
        response=response,
        retrieved_contexts=context_texts,
    )

    if ground_truth:
        sample.reference = ground_truth

    return sample


def create_ragas_dataset(
    samples: List[Dict[str, Any]],
) -> EvaluationDataset:
    """Create RAGAS EvaluationDataset from list of sample dicts.

    Args:
        samples: List of dicts with keys:
            - query: str
            - response: str
            - contexts: List[Dict] (our format)
            - expected_answer: Optional[str]

    Returns:
        RAGAS EvaluationDataset
    """
    ragas_samples = []

    for s in samples:
        sample = convert_to_ragas_sample(
            query=s["query"],
            response=s["response"],
            contexts=s.get("contexts", []),
            ground_truth=s.get("expected_answer"),
        )
        ragas_samples.append(sample)

    return EvaluationDataset(samples=ragas_samples)
