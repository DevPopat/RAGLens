"""LLM-as-Judge evaluation for generated responses.

Uses Claude or OpenAI to score chatbot responses on multiple criteria.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import settings
from app.core.generation.prompt_templates import (
    EVALUATION_SYSTEM_PROMPT,
    create_evaluation_prompt,
    create_golden_set_evaluation_prompt
)

logger = logging.getLogger(__name__)


class LLMJudge:
    """LLM-as-Judge evaluator for RAG responses."""

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None
    ):
        """Initialize LLM judge.

        Args:
            provider: "anthropic" or "openai"
            model: Optional model override
        """
        self.provider = provider.lower()

        if self.provider == "anthropic":
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = model or settings.ANTHROPIC_MODEL
        elif self.provider == "openai":
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = model or settings.OPENAI_MODEL
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info(f"Initialized LLM Judge with {self.provider} ({self.model})")

    async def evaluate_response(
        self,
        query: str,
        response: str,
        contexts: List[Dict[str, Any]],
        expected_category: Optional[str] = None,
        expected_intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate a chatbot response using LLM-as-judge.

        Args:
            query: Original customer query
            response: Chatbot's generated response
            contexts: Retrieved contexts with metadata and scores
            expected_category: Expected category (optional)
            expected_intent: Expected intent (optional)

        Returns:
            Evaluation results with scores and explanation
        """
        # Create evaluation prompt
        eval_prompt = create_evaluation_prompt(
            query=query,
            response=response,
            contexts=contexts,
            expected_category=expected_category,
            expected_intent=expected_intent
        )

        logger.debug(f"Evaluating response with {self.provider}")

        # Call LLM
        try:
            evaluation_text = await self._call_llm(eval_prompt)

            # Parse JSON response
            evaluation = self._parse_evaluation_response(evaluation_text)

            # Add metadata
            evaluation["evaluator"] = f"{self.provider}/{self.model}"
            evaluation["query"] = query
            evaluation["response"] = response

            return evaluation

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {
                "error": str(e),
                "evaluator": f"{self.provider}/{self.model}",
                "query": query,
                "response": response
            }

    async def evaluate_against_golden_set(
        self,
        query: str,
        response: str,
        expected_answer: str,
        contexts: List[Dict[str, Any]],
        category: str,
        intent: str
    ) -> Dict[str, Any]:
        """Evaluate response against expected answer from golden set.

        Args:
            query: Customer query
            response: Chatbot's response
            expected_answer: Expected/ideal answer
            contexts: Retrieved contexts
            category: Expected category
            intent: Expected intent

        Returns:
            Evaluation with comparison to expected answer
        """
        # Create golden set evaluation prompt
        eval_prompt = create_golden_set_evaluation_prompt(
            query=query,
            response=response,
            expected_answer=expected_answer,
            contexts=contexts,
            category=category,
            intent=intent
        )

        logger.debug(f"Evaluating against golden set with {self.provider}")

        try:
            evaluation_text = await self._call_llm(eval_prompt)

            # Parse JSON response
            evaluation = self._parse_evaluation_response(evaluation_text)

            # Add metadata
            evaluation["evaluator"] = f"{self.provider}/{self.model}"
            evaluation["evaluation_type"] = "golden_set"
            evaluation["query"] = query
            evaluation["response"] = response
            evaluation["expected_answer"] = expected_answer

            return evaluation

        except Exception as e:
            logger.error(f"Golden set evaluation failed: {e}")
            return {
                "error": str(e),
                "evaluator": f"{self.provider}/{self.model}",
                "evaluation_type": "golden_set",
                "query": query,
                "response": response
            }

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM with evaluation prompt.

        Args:
            prompt: Evaluation prompt

        Returns:
            LLM response text
        """
        if self.provider == "anthropic":
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.0,  # Deterministic for evaluation
                system=EVALUATION_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        elif self.provider == "openai":
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=2000
            )
            return response.choices[0].message.content

    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON evaluation response from LLM.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed evaluation dict
        """
        # Try to extract JSON from response
        # LLMs sometimes wrap JSON in markdown code blocks
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            evaluation = json.loads(text)
            return evaluation
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation JSON: {e}")
            logger.error(f"Response text: {response_text}")

            # Return fallback structure
            return {
                "error": "Failed to parse evaluation",
                "raw_response": response_text,
                "scores": {},
                "overall_score": None
            }

    async def batch_evaluate(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple responses in batch.

        Args:
            evaluations: List of evaluation requests, each with:
                - query: str
                - response: str
                - contexts: List[Dict]
                - expected_category: Optional[str]
                - expected_intent: Optional[str]

        Returns:
            List of evaluation results
        """
        results = []

        for eval_request in evaluations:
            result = await self.evaluate_response(
                query=eval_request["query"],
                response=eval_request["response"],
                contexts=eval_request["contexts"],
                expected_category=eval_request.get("expected_category"),
                expected_intent=eval_request.get("expected_intent")
            )
            results.append(result)

        return results


# Convenience function for quick evaluation
async def evaluate_with_llm(
    query: str,
    response: str,
    contexts: List[Dict[str, Any]],
    provider: str = "anthropic",
    expected_category: Optional[str] = None,
    expected_intent: Optional[str] = None
) -> Dict[str, Any]:
    """Quick evaluation helper function.

    Args:
        query: Customer query
        response: Chatbot response
        contexts: Retrieved contexts
        provider: "anthropic" or "openai"
        expected_category: Expected category
        expected_intent: Expected intent

    Returns:
        Evaluation results
    """
    judge = LLMJudge(provider=provider)
    return await judge.evaluate_response(
        query=query,
        response=response,
        contexts=contexts,
        expected_category=expected_category,
        expected_intent=expected_intent
    )
