"""RAGAS metric configuration and scoring utilities."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ragas.metrics import (
    LLMContextPrecisionWithoutReference,
    LLMContextRecall,
    Faithfulness,
    AspectCritic,
    FactualCorrectness,
)


@dataclass
class RAGASMetricConfig:
    """Configuration for RAGAS metrics and weights.

    Weights are used to compute a single overall score from individual metrics.
    """

    # Metric weights when ground_truth (expected answer) is available
    weights_with_ground_truth: Dict[str, float] = field(
        default_factory=lambda: {
            "context_precision": 0.15,
            "context_recall": 0.15,
            "faithfulness": 0.25,
            "answer_relevancy": 0.20,
            "answer_correctness": 0.25,
        }
    )

    # Metric weights when no ground_truth available (inline evaluation)
    # answer_relevancy uses AspectCritic (binary 0/1), so weighted lower than continuous metrics
    weights_without_ground_truth: Dict[str, float] = field(
        default_factory=lambda: {
            "context_precision": 0.30,
            "faithfulness": 0.45,
            "answer_relevancy": 0.25,
        }
    )


def get_answer_metrics(has_ground_truth: bool) -> List:
    """Get answer-level RAGAS metrics (LLM-as-judge on generated answers).

    Args:
        has_ground_truth: Whether expected answer is available

    Returns:
        List of RAGAS metric instances for answer evaluation
    """
    metrics = [AspectCritic(name="answer_relevancy", definition="Does the response directly and completely answer the user's question?")]
    if has_ground_truth:
        metrics.append(FactualCorrectness())
    return metrics


def get_context_metrics(has_ground_truth: bool) -> List:
    """Get context/retrieval RAGAS metrics.

    Args:
        has_ground_truth: Whether expected answer is available

    Returns:
        List of RAGAS metric instances for retrieval evaluation
    """
    metrics = [LLMContextPrecisionWithoutReference(), Faithfulness()]
    if has_ground_truth:
        metrics.append(LLMContextRecall())
    return metrics


def get_metrics_for_evaluation(has_ground_truth: bool) -> List:
    """Get appropriate RAGAS metrics based on data availability.

    Args:
        has_ground_truth: Whether expected answer is available

    Returns:
        List of RAGAS metric instances
    """
    # Base metrics that don't require ground truth
    base_metrics = [
        LLMContextPrecisionWithoutReference(),
        Faithfulness(),
        AspectCritic(name="answer_relevancy", definition="Does the response directly and completely answer the user's question?"),
    ]

    if has_ground_truth:
        # Add metrics that compare against expected answer
        base_metrics.extend(
            [
                LLMContextRecall(),
                FactualCorrectness(),
            ]
        )

    return base_metrics


def compute_overall_score(
    scores: Dict[str, float],
    has_ground_truth: bool,
    config: Optional[RAGASMetricConfig] = None,
) -> Optional[float]:
    """Compute weighted overall score from RAGAS metrics.

    Args:
        scores: Dict of metric_name -> score (0-1 scale from RAGAS)
        has_ground_truth: Whether ground_truth was available
        config: Optional custom weights

    Returns:
        Overall score in 0-1 range. Returns None if no valid scores.
    """
    config = config or RAGASMetricConfig()
    weights = (
        config.weights_with_ground_truth
        if has_ground_truth
        else config.weights_without_ground_truth
    )

    weighted_sum = 0.0
    total_weight = 0.0

    for metric_name, weight in weights.items():
        if metric_name in scores and scores[metric_name] is not None:
            weighted_sum += scores[metric_name] * weight
            total_weight += weight

    if total_weight == 0:
        return None

    normalized_score = weighted_sum / total_weight
    return round(normalized_score, 4)


# Mapping from RAGAS internal metric names to our standardized names
METRIC_NAME_MAP = {
    "llm_context_precision_without_reference": "context_precision",
    "context_precision": "context_precision",
    "llm_context_recall": "context_recall",
    "context_recall": "context_recall",
    "faithfulness": "faithfulness",
    "response_relevancy": "answer_relevancy",
    "answer_relevancy": "answer_relevancy",
    "aspect_critic": "answer_relevancy",
    "factual_correctness": "answer_correctness",
    "answer_correctness": "answer_correctness",
}


def normalize_metric_name(name: str) -> str:
    """Normalize RAGAS metric names to our standardized format.

    Args:
        name: Raw metric name from RAGAS

    Returns:
        Standardized metric name
    """
    return METRIC_NAME_MAP.get(name.lower(), name.lower())
