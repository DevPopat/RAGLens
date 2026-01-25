"""Claude (Anthropic) LLM integration."""
import logging
import time
from typing import List, Dict, Any
from anthropic import AsyncAnthropic

from app.config import settings
from app.core.generation.prompt_templates import CUSTOMER_SUPPORT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ClaudeGenerator:
    """Claude LLM wrapper for RAG generation."""

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to settings)
            model: Model name (defaults to settings)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """Generate response using Claude.

        Args:
            prompt: User prompt
            system_prompt: System prompt (defaults to customer support prompt)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary with response text, token usage, and latency
        """
        system_prompt = system_prompt or CUSTOMER_SUPPORT_SYSTEM_PROMPT
        temperature = temperature if temperature is not None else settings.temperature
        max_tokens = max_tokens or settings.max_tokens

        start_time = time.time()

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract response text
            response_text = response.content[0].text

            # Token usage
            token_usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }

            # Calculate cost (approximate pricing for Claude 3.5 Sonnet)
            # Input: $3/million tokens, Output: $15/million tokens
            input_cost = (token_usage["input_tokens"] / 1_000_000) * 3.0
            output_cost = (token_usage["output_tokens"] / 1_000_000) * 15.0
            total_cost = input_cost + output_cost

            logger.info(
                f"Claude generation: {token_usage['total_tokens']} tokens, "
                f"{latency_ms:.0f}ms, ${total_cost:.4f}"
            )

            return {
                "text": response_text,
                "model": self.model,
                "token_usage": token_usage,
                "latency_ms": latency_ms,
                "cost": total_cost
            }

        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise
