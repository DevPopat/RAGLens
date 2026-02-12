"""Main RAGAS evaluator class.

Provides a unified interface for evaluating RAG responses using RAGAS metrics.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional

from ragas import evaluate, EvaluationDataset

from .llm_providers import get_ragas_llm, get_ragas_embeddings
from .metrics import (
    get_metrics_for_evaluation,
    compute_overall_score,
    normalize_metric_name,
    RAGASMetricConfig,
)
from .data_adapter import convert_to_ragas_sample, create_ragas_dataset

logger = logging.getLogger(__name__)


def _run_ragas_evaluate(**kwargs):
    """Run RAGAS evaluate with standard asyncio policy to avoid uvloop conflicts."""
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    return evaluate(**kwargs)


class RAGASEvaluator:
    """RAGAS-based evaluator for RAG systems.

    Replaces the custom LLMJudge and RetrievalEvaluator with industry-standard
    RAGAS metrics. Uses LLM-as-judge methodology for both generation and
    retrieval evaluation.

    Metrics evaluated:
    - context_precision: Are retrieved docs relevant to the query?
    - context_recall: Can expected answer be derived from contexts? (requires ground_truth)
    - faithfulness: Is response grounded in retrieved contexts?
    - answer_relevancy: Is the answer relevant to the question?
    - answer_correctness: Does generated match expected? (requires ground_truth)
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        metric_config: Optional[RAGASMetricConfig] = None,
    ):
        """Initialize RAGAS evaluator.

        Args:
            provider: LLM provider ("anthropic" or "openai")
            model: Optional model override
            metric_config: Optional custom metric weights
        """
        self.provider = provider
        self.model = model
        self.llm = get_ragas_llm(provider, model)
        self.embeddings = get_ragas_embeddings()
        self.metric_config = metric_config or RAGASMetricConfig()

        logger.info(f"Initialized RAGASEvaluator with {provider}")

    async def evaluate_response(
        self,
        query: str,
        response: str,
        contexts: List[Dict[str, Any]],
        expected_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate a single RAG response using RAGAS metrics.

        Args:
            query: User question
            response: Generated answer
            contexts: Retrieved contexts (from Response.sources_json format)
            expected_answer: Ground truth answer (optional, from GoldenTestCase)

        Returns:
            Evaluation results with scores and overall_score
        """
        has_ground_truth = expected_answer is not None

        # Convert to RAGAS format
        sample = convert_to_ragas_sample(
            query=query,
            response=response,
            contexts=contexts,
            ground_truth=expected_answer,
        )

        # Get appropriate metrics
        metrics = get_metrics_for_evaluation(has_ground_truth)

        try:
            # Run RAGAS evaluation in a separate thread to avoid
            # nested event loop conflicts with uvloop
            result = await asyncio.to_thread(
                _run_ragas_evaluate,
                dataset=EvaluationDataset(samples=[sample]),
                metrics=metrics,
                llm=self.llm,
                embeddings=self.embeddings,
            )

            # Extract and normalize scores
            scores = self._extract_scores(result)
            overall = compute_overall_score(
                scores, has_ground_truth, self.metric_config
            )

            return {
                "scores": {
                    **scores,
                    "overall_score": overall,
                },
                "overall_score": overall,
                "evaluator": f"ragas/{self.provider}",
                "evaluation_type": "ragas",
                "has_ground_truth": has_ground_truth,
                "metrics_used": [m.__class__.__name__ for m in metrics],
            }

        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "evaluator": f"ragas/{self.provider}",
                "evaluation_type": "ragas",
                "scores": {"ragas": {}, "overall_score": None},
                "overall_score": None,
            }

    async def evaluate_batch(
        self,
        samples: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple samples in batch.

        More efficient than calling evaluate_response multiple times as it
        batches LLM calls.

        Args:
            samples: List of dicts with keys:
                - query: str
                - response: str
                - contexts: List[Dict]
                - expected_answer: Optional[str]

        Returns:
            List of evaluation results
        """
        if not samples:
            return []

        # Track ground truth availability per sample
        has_ground_truth_list = [
            s.get("expected_answer") is not None for s in samples
        ]

        # For batch, use metrics for the minimum common denominator
        all_have_ground_truth = all(has_ground_truth_list)

        # Create RAGAS dataset
        dataset = create_ragas_dataset(samples)
        metrics = get_metrics_for_evaluation(all_have_ground_truth)

        try:
            # Run RAGAS evaluation on full batch in a separate thread
            # to avoid nested event loop conflicts with uvloop
            result = await asyncio.to_thread(
                _run_ragas_evaluate,
                dataset=dataset,
                metrics=metrics,
                llm=self.llm,
                embeddings=self.embeddings,
            )

            # Process results for each sample
            results = []
            for i, sample in enumerate(samples):
                scores = self._extract_scores_for_index(result, i)
                has_gt = has_ground_truth_list[i]
                overall = compute_overall_score(scores, has_gt, self.metric_config)

                results.append(
                    {
                        "scores": {
                            **scores,
                            "overall_score": overall,
                        },
                        "overall_score": overall,
                        "evaluator": f"ragas/{self.provider}",
                        "evaluation_type": "ragas_batch",
                        "has_ground_truth": has_gt,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Batch RAGAS evaluation failed: {e}", exc_info=True)
            return [
                {
                    "error": str(e),
                    "evaluator": f"ragas/{self.provider}",
                    "scores": {"ragas": {}, "overall_score": None},
                    "overall_score": None,
                }
                for _ in samples
            ]

    def _extract_scores(self, result) -> Dict[str, float]:
        """Extract scores from RAGAS evaluation result.

        Args:
            result: RAGAS EvaluationResult object

        Returns:
            Dict of normalized metric names to scores
        """
        scores = {}

        # RAGAS returns a pandas DataFrame-like result
        # Access scores via the result object
        if hasattr(result, "scores"):
            for row in result.scores:
                for metric_name, value in row.items():
                    if metric_name not in ("user_input", "response", "retrieved_contexts", "reference"):
                        normalized = normalize_metric_name(metric_name)
                        # Handle potential list values
                        if isinstance(value, (list, tuple)):
                            scores[normalized] = value[0] if value else None
                        else:
                            scores[normalized] = value
        elif hasattr(result, "to_pandas"):
            # Alternative: convert to pandas and iterate
            df = result.to_pandas()
            if len(df) > 0:
                row = df.iloc[0]
                for col in df.columns:
                    if col not in ("user_input", "response", "retrieved_contexts", "reference"):
                        normalized = normalize_metric_name(col)
                        scores[normalized] = row[col]

        return scores

    def _extract_scores_for_index(self, result, index: int) -> Dict[str, float]:
        """Extract scores for a specific sample index from batch result.

        Args:
            result: RAGAS EvaluationResult object
            index: Index of sample in batch

        Returns:
            Dict of normalized metric names to scores for that sample
        """
        scores = {}

        if hasattr(result, "to_pandas"):
            df = result.to_pandas()
            if len(df) > index:
                row = df.iloc[index]
                for col in df.columns:
                    if col not in ("user_input", "response", "retrieved_contexts", "reference"):
                        normalized = normalize_metric_name(col)
                        scores[normalized] = row[col]

        return scores
