"""Message classifier for multi-turn conversations.

Classifies user messages to determine:
1. Message type (question, follow_up, acknowledgment, closure)
2. Whether RAG retrieval is needed
"""
import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of user messages in a conversation."""
    QUESTION = "question"           # New question requiring retrieval
    FOLLOW_UP = "follow_up"         # Follow-up to previous context
    CLARIFICATION = "clarification"  # Asking for more detail
    ACKNOWLEDGMENT = "acknowledgment"  # Ok, thanks, got it
    CLOSURE = "closure"             # Bye, that's all
    GREETING = "greeting"           # Hi, hello
    OTHER = "other"                 # Anything else


@dataclass
class ClassificationResult:
    """Result from message classification."""
    message_type: MessageType
    needs_retrieval: bool
    confidence: float
    reasoning: Optional[str] = None


CLASSIFICATION_PROMPT = """You are a message classifier for a customer support chatbot.

Given a conversation history and the user's latest message, classify the message.

CONVERSATION HISTORY:
{history}

LATEST USER MESSAGE:
{message}

Classify the message into one of these types:
- question: A new question that requires looking up information
- follow_up: A follow-up question related to the previous topic (may need retrieval)
- clarification: User asking for more details on something already discussed
- acknowledgment: User acknowledging (ok, thanks, got it, I understand)
- closure: User ending the conversation (bye, that's all, no more questions)
- greeting: User greeting (hi, hello)
- other: Anything that doesn't fit above

Also determine if RAG retrieval is needed:
- TRUE for: question, follow_up (usually), clarification (sometimes)
- FALSE for: acknowledgment, closure, greeting, simple confirmations

Respond in JSON format:
{{
    "message_type": "<type>",
    "needs_retrieval": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}
"""


class MessageClassifier:
    """Classifies messages to route them appropriately."""

    def __init__(self, provider: str = "anthropic", model: Optional[str] = None):
        """Initialize classifier.

        Args:
            provider: "anthropic" or "openai"
            model: Optional model override (defaults to fast/cheap model)
        """
        self.provider = provider.lower()

        if self.provider == "anthropic":
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            # Use Haiku for fast, cheap classification
            self.model = model or "claude-3-haiku-20240307"
        elif self.provider == "openai":
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = model or "gpt-3.5-turbo"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def classify(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> ClassificationResult:
        """Classify a user message.

        Args:
            message: The user's latest message
            history: Conversation history [{role: "user"|"assistant", content: "..."}]

        Returns:
            ClassificationResult with type and retrieval flag
        """
        # Try rule-based classification first (fast, free)
        rule_result = self._rule_based_classify(message, history)
        if rule_result and rule_result.confidence >= 0.9:
            logger.debug(f"Rule-based classification: {rule_result.message_type}")
            return rule_result

        # Fall back to LLM classification
        return await self._llm_classify(message, history)

    def _rule_based_classify(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[ClassificationResult]:
        """Fast rule-based classification for common patterns.

        Returns None if uncertain, letting LLM handle it.
        """
        msg_lower = message.lower().strip()

        # Greetings
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        if msg_lower in greetings or any(msg_lower.startswith(g + " ") for g in greetings):
            return ClassificationResult(
                message_type=MessageType.GREETING,
                needs_retrieval=False,
                confidence=0.95,
                reasoning="Detected greeting pattern"
            )

        # Closures
        closures = [
            "bye", "goodbye", "thanks bye", "thank you bye", "that's all",
            "thats all", "no more questions", "nothing else", "i'm done",
            "im done", "that will be all", "have a good day"
        ]
        if msg_lower in closures or any(msg_lower.startswith(c) for c in closures):
            return ClassificationResult(
                message_type=MessageType.CLOSURE,
                needs_retrieval=False,
                confidence=0.95,
                reasoning="Detected closure pattern"
            )

        # Acknowledgments
        acknowledgments = [
            "ok", "okay", "got it", "i see", "understood", "i understand",
            "makes sense", "thanks", "thank you", "perfect", "great",
            "awesome", "cool", "alright", "all right", "sure", "yes",
            "yep", "yeah", "no", "nope"
        ]
        # Only pure acknowledgments (short messages)
        if msg_lower in acknowledgments and len(msg_lower.split()) <= 3:
            return ClassificationResult(
                message_type=MessageType.ACKNOWLEDGMENT,
                needs_retrieval=False,
                confidence=0.9,
                reasoning="Detected acknowledgment pattern"
            )

        # Questions (contains question mark or starts with question word)
        question_starters = ["how", "what", "where", "when", "why", "who", "which", "can", "could", "would", "is", "are", "do", "does", "will"]
        if "?" in message or any(msg_lower.startswith(q + " ") for q in question_starters):
            # Check if it's a follow-up (references previous context)
            if history and len(history) > 0:
                follow_up_indicators = ["it", "that", "this", "the same", "also", "and", "what about", "how about"]
                if any(indicator in msg_lower for indicator in follow_up_indicators):
                    return ClassificationResult(
                        message_type=MessageType.FOLLOW_UP,
                        needs_retrieval=True,
                        confidence=0.8,
                        reasoning="Question with context reference"
                    )

            return ClassificationResult(
                message_type=MessageType.QUESTION,
                needs_retrieval=True,
                confidence=0.85,
                reasoning="Detected question pattern"
            )

        # If we have history and message is short, might be follow-up or clarification
        if history and len(history) > 0 and len(msg_lower.split()) < 10:
            return ClassificationResult(
                message_type=MessageType.FOLLOW_UP,
                needs_retrieval=True,
                confidence=0.7,
                reasoning="Short message with conversation context"
            )

        # Uncertain - let LLM decide
        return None

    async def _llm_classify(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> ClassificationResult:
        """Use LLM for classification when rules are uncertain."""
        # Format history
        history_text = "No previous messages."
        if history:
            history_lines = []
            for msg in history[-5:]:  # Last 5 messages for context
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")[:200]  # Truncate long messages
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)

        prompt = CLASSIFICATION_PROMPT.format(
            history=history_text,
            message=message
        )

        try:
            if self.provider == "anthropic":
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=200,
                    temperature=0.0,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text

            elif self.provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=200
                )
                result_text = response.choices[0].message.content

            # Parse JSON response
            result = self._parse_response(result_text)
            return result

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Default to question with retrieval on error
            return ClassificationResult(
                message_type=MessageType.QUESTION,
                needs_retrieval=True,
                confidence=0.5,
                reasoning=f"LLM classification failed: {str(e)}"
            )

    def _parse_response(self, response_text: str) -> ClassificationResult:
        """Parse LLM response into ClassificationResult."""
        try:
            # Clean up response (remove markdown code blocks if present)
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())

            message_type = MessageType(data.get("message_type", "question"))
            needs_retrieval = data.get("needs_retrieval", True)
            confidence = float(data.get("confidence", 0.8))
            reasoning = data.get("reasoning")

            return ClassificationResult(
                message_type=message_type,
                needs_retrieval=needs_retrieval,
                confidence=confidence,
                reasoning=reasoning
            )

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse classification response: {e}")
            return ClassificationResult(
                message_type=MessageType.QUESTION,
                needs_retrieval=True,
                confidence=0.5,
                reasoning="Failed to parse LLM response"
            )


# Evaluation criteria per message type
EVALUATION_CRITERIA = {
    MessageType.QUESTION: {
        "criteria": ["accuracy", "completeness", "faithfulness", "tone", "relevance", "clarity"],
        "weights": {"accuracy": 0.25, "completeness": 0.2, "faithfulness": 0.2, "tone": 0.1, "relevance": 0.15, "clarity": 0.1}
    },
    MessageType.FOLLOW_UP: {
        "criteria": ["context_awareness", "accuracy", "relevance", "tone"],
        "weights": {"context_awareness": 0.3, "accuracy": 0.3, "relevance": 0.25, "tone": 0.15}
    },
    MessageType.CLARIFICATION: {
        "criteria": ["clarity", "completeness", "tone"],
        "weights": {"clarity": 0.4, "completeness": 0.35, "tone": 0.25}
    },
    MessageType.ACKNOWLEDGMENT: {
        "criteria": ["appropriateness", "tone"],
        "weights": {"appropriateness": 0.5, "tone": 0.5}
    },
    MessageType.CLOSURE: {
        "criteria": ["appropriateness", "tone"],
        "weights": {"appropriateness": 0.5, "tone": 0.5}
    },
    MessageType.GREETING: {
        "criteria": ["appropriateness", "tone"],
        "weights": {"appropriateness": 0.5, "tone": 0.5}
    },
    MessageType.OTHER: {
        "criteria": ["relevance", "tone"],
        "weights": {"relevance": 0.5, "tone": 0.5}
    }
}


def get_evaluation_criteria(message_type: MessageType) -> Dict[str, Any]:
    """Get evaluation criteria for a message type.

    Args:
        message_type: The type of message

    Returns:
        Dictionary with criteria list and weights
    """
    return EVALUATION_CRITERIA.get(message_type, EVALUATION_CRITERIA[MessageType.QUESTION])
