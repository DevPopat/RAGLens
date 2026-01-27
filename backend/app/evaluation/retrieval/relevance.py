"""Retrieval evaluation metrics for RAG systems.

Implements Precision@K, Recall@K, and relevance scoring.
"""
import logging
from typing import List, Dict, Any, Set, Optional

logger = logging.getLogger(__name__)


class RetrievalEvaluator:
    """Evaluator for retrieval quality in RAG systems."""

    def __init__(self, relevance_threshold: float = 0.5):
        """Initialize evaluator.

        Args:
            relevance_threshold: Score threshold for considering a document relevant
        """
        self.relevance_threshold = relevance_threshold

    def precision_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: Optional[int] = None
    ) -> float:
        """Calculate Precision@K.

        Precision@K = (# relevant docs in top K) / K

        Args:
            retrieved_ids: List of retrieved document IDs (in rank order)
            relevant_ids: Set of known relevant document IDs
            k: Top-K to evaluate (default: all retrieved)

        Returns:
            Precision score (0.0 to 1.0)
        """
        if not retrieved_ids:
            return 0.0

        k = k or len(retrieved_ids)
        top_k = retrieved_ids[:k]

        relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant_ids)

        return relevant_retrieved / k

    def recall_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: Optional[int] = None
    ) -> float:
        """Calculate Recall@K.

        Recall@K = (# relevant docs in top K) / (total # relevant docs)

        Args:
            retrieved_ids: List of retrieved document IDs (in rank order)
            relevant_ids: Set of known relevant document IDs
            k: Top-K to evaluate (default: all retrieved)

        Returns:
            Recall score (0.0 to 1.0)
        """
        if not relevant_ids:
            return 0.0

        if not retrieved_ids:
            return 0.0

        k = k or len(retrieved_ids)
        top_k = retrieved_ids[:k]

        relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant_ids)

        return relevant_retrieved / len(relevant_ids)

    def f1_score(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: Optional[int] = None
    ) -> float:
        """Calculate F1 score (harmonic mean of precision and recall).

        Args:
            retrieved_ids: List of retrieved document IDs
            relevant_ids: Set of known relevant document IDs
            k: Top-K to evaluate

        Returns:
            F1 score (0.0 to 1.0)
        """
        precision = self.precision_at_k(retrieved_ids, relevant_ids, k)
        recall = self.recall_at_k(retrieved_ids, relevant_ids, k)

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    def mean_reciprocal_rank(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str]
    ) -> float:
        """Calculate Mean Reciprocal Rank (MRR).

        MRR = 1 / (rank of first relevant document)

        Args:
            retrieved_ids: List of retrieved document IDs (in rank order)
            relevant_ids: Set of known relevant document IDs

        Returns:
            MRR score (0.0 to 1.0)
        """
        if not retrieved_ids or not relevant_ids:
            return 0.0

        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_ids:
                return 1.0 / rank

        return 0.0

    def average_precision(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str]
    ) -> float:
        """Calculate Average Precision (AP).

        AP = (sum of P@k for each relevant doc) / (total # relevant docs)

        Args:
            retrieved_ids: List of retrieved document IDs (in rank order)
            relevant_ids: Set of known relevant document IDs

        Returns:
            Average Precision (0.0 to 1.0)
        """
        if not relevant_ids or not retrieved_ids:
            return 0.0

        precision_sum = 0.0
        relevant_count = 0

        for k, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_ids:
                relevant_count += 1
                precision_sum += relevant_count / k

        if relevant_count == 0:
            return 0.0

        return precision_sum / len(relevant_ids)

    def evaluate_retrieval(
        self,
        retrieved_docs: List[Dict[str, Any]],
        relevant_doc_ids: Set[str],
        k_values: List[int] = [1, 3, 5, 10]
    ) -> Dict[str, Any]:
        """Comprehensive retrieval evaluation.

        Args:
            retrieved_docs: List of retrieved documents with 'id' and 'score'
            relevant_doc_ids: Set of ground-truth relevant document IDs
            k_values: List of K values to evaluate

        Returns:
            Dictionary with all metrics
        """
        # Extract IDs in rank order
        retrieved_ids = [doc.get("id") or doc.get("metadata", {}).get("source_id")
                        for doc in retrieved_docs]

        # Filter out None IDs
        retrieved_ids = [rid for rid in retrieved_ids if rid is not None]

        metrics = {
            "total_retrieved": len(retrieved_ids),
            "total_relevant": len(relevant_doc_ids),
            "retrieved_ids": retrieved_ids,
            "precision_at_k": {},
            "recall_at_k": {},
            "f1_at_k": {}
        }

        # Calculate metrics at different K values
        for k in k_values:
            if k <= len(retrieved_ids):
                metrics["precision_at_k"][f"p@{k}"] = round(
                    self.precision_at_k(retrieved_ids, relevant_doc_ids, k), 4
                )
                metrics["recall_at_k"][f"r@{k}"] = round(
                    self.recall_at_k(retrieved_ids, relevant_doc_ids, k), 4
                )
                metrics["f1_at_k"][f"f1@{k}"] = round(
                    self.f1_score(retrieved_ids, relevant_doc_ids, k), 4
                )

        # Overall metrics
        metrics["mean_reciprocal_rank"] = round(
            self.mean_reciprocal_rank(retrieved_ids, relevant_doc_ids), 4
        )
        metrics["average_precision"] = round(
            self.average_precision(retrieved_ids, relevant_doc_ids), 4
        )

        return metrics

    def evaluate_relevance_scores(
        self,
        retrieved_docs: List[Dict[str, Any]],
        score_key: str = "score"
    ) -> Dict[str, Any]:
        """Evaluate distribution of relevance scores.

        Args:
            retrieved_docs: List of retrieved documents with scores
            score_key: Key for relevance score in documents

        Returns:
            Score distribution statistics
        """
        if not retrieved_docs:
            return {
                "count": 0,
                "mean": None,
                "median": None,
                "min": None,
                "max": None
            }

        scores = [doc.get(score_key, 0.0) for doc in retrieved_docs]
        scores_sorted = sorted(scores)

        return {
            "count": len(scores),
            "mean": round(sum(scores) / len(scores), 4),
            "median": scores_sorted[len(scores) // 2],
            "min": scores_sorted[0],
            "max": scores_sorted[-1],
            "above_threshold": sum(1 for s in scores if s >= self.relevance_threshold)
        }

    def context_precision(
        self,
        retrieved_docs: List[Dict[str, Any]],
        relevant_doc_ids: Set[str]
    ) -> float:
        """Calculate context precision (how many retrieved are relevant).

        Args:
            retrieved_docs: Retrieved documents
            relevant_doc_ids: Ground truth relevant IDs

        Returns:
            Context precision (0.0 to 1.0)
        """
        if not retrieved_docs:
            return 0.0

        retrieved_ids = [
            doc.get("id") or doc.get("metadata", {}).get("source_id")
            for doc in retrieved_docs
        ]

        relevant_count = sum(1 for rid in retrieved_ids if rid in relevant_doc_ids)

        return relevant_count / len(retrieved_docs)


# Convenience function for quick evaluation
def evaluate_retrieval(
    retrieved_docs: List[Dict[str, Any]],
    relevant_doc_ids: Set[str],
    k_values: List[int] = [1, 3, 5, 10],
    relevance_threshold: float = 0.5
) -> Dict[str, Any]:
    """Quick retrieval evaluation helper.

    Args:
        retrieved_docs: List of retrieved documents
        relevant_doc_ids: Set of ground-truth relevant IDs
        k_values: K values to evaluate
        relevance_threshold: Relevance score threshold

    Returns:
        Evaluation metrics
    """
    evaluator = RetrievalEvaluator(relevance_threshold=relevance_threshold)
    return evaluator.evaluate_retrieval(retrieved_docs, relevant_doc_ids, k_values)
