"""Test script for LLM-as-judge evaluation system.

This script demonstrates:
1. Running a query through the RAG system
2. Evaluating the response with LLM-as-judge
3. Checking retrieval metrics
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.evaluation.generation.llm_judge import LLMJudge
from app.evaluation.retrieval.relevance import RetrievalEvaluator


async def test_llm_judge():
    """Test LLM-as-judge evaluation."""
    print("=" * 80)
    print("Testing LLM-as-Judge Evaluation")
    print("=" * 80)

    # Sample query and response
    query = "How do I reset my password?"

    response = """To reset your password, please follow these steps:

1. Go to the login page
2. Click on "Forgot Password"
3. Enter your email address
4. Check your email for a reset link
5. Click the link and create a new password

If you don't receive the email within 5 minutes, please check your spam folder. If you still have issues, contact our support team at support@example.com."""

    # Sample contexts (retrieved documents)
    contexts = [
        {
            "text": "To reset your password: 1. Visit login page 2. Click 'Forgot Password' 3. Enter email 4. Follow email link",
            "score": 0.92,
            "metadata": {
                "category": "ACCOUNT",
                "intent": "password_reset",
                "flags": "BI",
                "source_id": "doc_123"
            }
        },
        {
            "text": "If you don't receive the password reset email, check your spam folder or contact support.",
            "score": 0.78,
            "metadata": {
                "category": "ACCOUNT",
                "intent": "password_reset",
                "flags": "BN",
                "source_id": "doc_456"
            }
        },
        {
            "text": "Our support team is available at support@example.com or call 1-800-SUPPORT.",
            "score": 0.65,
            "metadata": {
                "category": "CONTACT",
                "intent": "contact_support",
                "flags": "B",
                "source_id": "doc_789"
            }
        }
    ]

    # Test with Anthropic (Claude)
    print("\n1. Testing with Anthropic Claude...")
    print("-" * 80)

    try:
        judge = LLMJudge(provider="anthropic")

        evaluation = await judge.evaluate_response(
            query=query,
            response=response,
            contexts=contexts,
            expected_category="ACCOUNT",
            expected_intent="password_reset"
        )

        print(f"Evaluator: {evaluation.get('evaluator')}")
        print(f"\nScores:")
        scores = evaluation.get("scores", {})
        for metric, score in scores.items():
            print(f"  {metric}: {score}/5")

        print(f"\nOverall Score: {evaluation.get('overall_score')}/5")
        print(f"\nExplanation: {evaluation.get('explanation')}")

        if evaluation.get("strengths"):
            print(f"\nStrengths:")
            for strength in evaluation["strengths"]:
                print(f"  - {strength}")

        if evaluation.get("weaknesses"):
            print(f"\nWeaknesses:")
            for weakness in evaluation["weaknesses"]:
                print(f"  - {weakness}")

        if evaluation.get("suggested_improvement"):
            print(f"\nSuggested Improvement:")
            print(f"  {evaluation['suggested_improvement']}")

    except Exception as e:
        print(f"Error with Anthropic: {e}")

    # Test retrieval metrics
    print("\n\n2. Testing Retrieval Metrics...")
    print("-" * 80)

    retrieval_evaluator = RetrievalEvaluator()

    # Simulate ground truth: doc_123 and doc_456 are relevant
    relevant_doc_ids = {"doc_123", "doc_456"}

    retrieval_metrics = retrieval_evaluator.evaluate_retrieval(
        retrieved_docs=contexts,
        relevant_doc_ids=relevant_doc_ids,
        k_values=[1, 3, 5]
    )

    print(f"Total Retrieved: {retrieval_metrics['total_retrieved']}")
    print(f"Total Relevant: {retrieval_metrics['total_relevant']}")

    print(f"\nPrecision@K:")
    for k, score in retrieval_metrics["precision_at_k"].items():
        print(f"  {k}: {score}")

    print(f"\nRecall@K:")
    for k, score in retrieval_metrics["recall_at_k"].items():
        print(f"  {k}: {score}")

    print(f"\nF1@K:")
    for k, score in retrieval_metrics["f1_at_k"].items():
        print(f"  {k}: {score}")

    print(f"\nMean Reciprocal Rank: {retrieval_metrics['mean_reciprocal_rank']}")
    print(f"Average Precision: {retrieval_metrics['average_precision']}")

    # Test score distribution
    print("\n\n3. Testing Score Distribution...")
    print("-" * 80)

    score_stats = retrieval_evaluator.evaluate_relevance_scores(
        retrieved_docs=contexts,
        score_key="score"
    )

    print(f"Count: {score_stats['count']}")
    print(f"Mean: {score_stats['mean']}")
    print(f"Median: {score_stats['median']}")
    print(f"Min: {score_stats['min']}")
    print(f"Max: {score_stats['max']}")
    print(f"Above Threshold (0.5): {score_stats['above_threshold']}")


async def test_poor_response():
    """Test evaluation of a poor response (should get low scores)."""
    print("\n\n" + "=" * 80)
    print("Testing Poor Response Evaluation")
    print("=" * 80)

    query = "How do I reset my password?"
    poor_response = "You need to contact IT department."

    contexts = [
        {
            "text": "To reset your password: 1. Visit login page 2. Click 'Forgot Password' 3. Enter email 4. Follow email link",
            "score": 0.92,
            "metadata": {
                "category": "ACCOUNT",
                "intent": "password_reset",
                "flags": "BI",
                "source_id": "doc_123"
            }
        }
    ]

    try:
        judge = LLMJudge(provider="anthropic")

        evaluation = await judge.evaluate_response(
            query=query,
            response=poor_response,
            contexts=contexts,
            expected_category="ACCOUNT",
            expected_intent="password_reset"
        )

        print(f"\nScores:")
        scores = evaluation.get("scores", {})
        for metric, score in scores.items():
            print(f"  {metric}: {score}/5")

        print(f"\nOverall Score: {evaluation.get('overall_score')}/5")
        print(f"\nExplanation: {evaluation.get('explanation')}")

        if evaluation.get("weaknesses"):
            print(f"\nWeaknesses:")
            for weakness in evaluation["weaknesses"]:
                print(f"  - {weakness}")

    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all tests."""
    await test_llm_judge()
    await test_poor_response()

    print("\n" + "=" * 80)
    print("Evaluation Tests Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
