"""Chat API endpoints with multi-turn conversation support."""
import uuid
import logging
import random
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    RetrievedSource,
    ConversationMessage
)
from app.core.retrieval.retriever import RAGRetriever
from app.core.conversation.classifier import (
    MessageClassifier,
    MessageType,
    ClassificationResult,
    get_evaluation_criteria
)
from app.db.database import get_db
from app.db.models import Query, Response
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Evaluation sample rate (10% by default)
EVALUATION_SAMPLE_RATE = 0.1


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Process a chat query with multi-turn conversation support.

    This endpoint:
    1. Classifies the message type (question, follow_up, acknowledgment, etc.)
    2. Routes based on type (skip retrieval for acknowledgments)
    3. Retrieves relevant documents if needed
    4. Generates a response using the specified LLM
    5. Stores the query and response in the database
    6. Queues async evaluation in background (sampled)
    7. Returns the response with sources and metadata
    """
    try:
        # Step 1: Classify the message
        classifier = MessageClassifier(provider=request.llm_provider)
        classification = await classifier.classify(
            message=request.query,
            history=_convert_history(request.conversation_history)
        )

        logger.info(
            f"Message classified as {classification.message_type.value} "
            f"(needs_retrieval={classification.needs_retrieval})"
        )

        # Step 2: Route based on classification
        if classification.needs_retrieval:
            # Full RAG pipeline
            rag_result = await _run_rag_pipeline(request, classification)
        else:
            # Direct response (no retrieval)
            rag_result = await _generate_direct_response(request, classification)

        # Step 3: Store in database
        query_id = uuid.uuid4()
        db_query = Query(
            id=query_id,
            query_text=request.query,
            llm_provider=request.llm_provider,
            retrieval_config={
                "top_k": request.top_k,
                "filter_category": request.filter_category,
                "filter_intent": request.filter_intent,
                "message_type": classification.message_type.value,
                "needs_retrieval": classification.needs_retrieval
            }
        )
        db.add(db_query)

        db_response = Response(
            query_id=query_id,
            response_text=rag_result["response"],
            sources_json=rag_result.get("sources_json", []),
            latency_ms=rag_result["latency_ms"],
            token_usage=rag_result["token_usage"],
            cost=rag_result["cost"]
        )
        db.add(db_response)

        await db.commit()

        logger.info(f"Query {query_id} processed successfully")

        # Step 4: Queue async evaluation (sampled)
        if _should_evaluate():
            background_tasks.add_task(
                _evaluate_response_async,
                query_id=query_id,
                message_type=classification.message_type,
                conversation_history=request.conversation_history
            )

        # Step 5: Format and return response
        return ChatResponse(
            query_id=str(query_id),
            query=request.query,
            response=rag_result["response"],
            sources=[
                RetrievedSource(
                    id=src["id"],
                    text=src["text"],
                    score=src["score"],
                    metadata=src["metadata"]
                )
                for src in rag_result.get("sources", [])
            ],
            llm_provider=rag_result["llm_provider"],
            model=rag_result["model"],
            token_usage=rag_result["token_usage"],
            latency_ms=rag_result["latency_ms"],
            cost=rag_result["cost"],
            message_type=classification.message_type.value
        )

    except Exception as e:
        logger.error(f"Error processing chat query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _convert_history(
    history: Optional[List[ConversationMessage]]
) -> Optional[List[Dict[str, str]]]:
    """Convert ConversationMessage list to simple dict format."""
    if not history:
        return None
    return [{"role": msg.role, "content": msg.content} for msg in history]


async def _run_rag_pipeline(
    request: ChatRequest,
    classification: ClassificationResult
) -> Dict[str, Any]:
    """Run full RAG pipeline with retrieval."""
    retriever = RAGRetriever()

    # Build metadata filter
    filter_metadata = None
    if request.filter_category or request.filter_intent:
        filter_metadata = {}
        if request.filter_category:
            filter_metadata["category"] = request.filter_category
        if request.filter_intent:
            filter_metadata["intent"] = request.filter_intent

    # Build context from conversation history for follow-ups
    context_query = request.query
    if classification.message_type == MessageType.FOLLOW_UP and request.conversation_history:
        # Append recent context to query for better retrieval
        recent_context = _get_recent_context(request.conversation_history)
        if recent_context:
            context_query = f"{recent_context}\n\nCurrent question: {request.query}"

    # Execute RAG pipeline
    rag_result = await retriever.query(
        query_text=context_query,
        top_k=request.top_k,
        llm_provider=request.llm_provider,
        filter_metadata=filter_metadata
    )

    # Format sources for storage
    sources_json = [
        {
            "id": src["id"],
            "text": src["text"],
            "score": src["score"],
            "metadata": src["metadata"]
        }
        for src in rag_result["sources"]
    ]

    return {
        "response": rag_result["response"],
        "sources": rag_result["sources"],
        "sources_json": sources_json,
        "llm_provider": rag_result["llm_provider"],
        "model": rag_result["model"],
        "token_usage": rag_result["token_usage"],
        "latency_ms": rag_result["latency_ms"],
        "cost": rag_result["cost"]
    }


async def _generate_direct_response(
    request: ChatRequest,
    classification: ClassificationResult
) -> Dict[str, Any]:
    """Generate direct response without RAG retrieval.

    Used for acknowledgments, closures, greetings, etc.
    """
    import time
    from anthropic import AsyncAnthropic
    from openai import AsyncOpenAI

    start_time = time.time()

    # Generate appropriate response based on message type
    if classification.message_type == MessageType.ACKNOWLEDGMENT:
        prompts = [
            "You're welcome! Is there anything else I can help you with?",
            "Glad I could help! Let me know if you have any other questions.",
            "Happy to help! Feel free to ask if you need anything else."
        ]
        response_text = random.choice(prompts)

    elif classification.message_type == MessageType.CLOSURE:
        prompts = [
            "Thank you for contacting us! Have a great day!",
            "Goodbye! Don't hesitate to reach out if you need help in the future.",
            "Take care! We're always here if you need assistance."
        ]
        response_text = random.choice(prompts)

    elif classification.message_type == MessageType.GREETING:
        prompts = [
            "Hello! How can I help you today?",
            "Hi there! What can I assist you with?",
            "Welcome! How may I help you?"
        ]
        response_text = random.choice(prompts)

    else:
        # For other types, use LLM but without retrieval
        if request.llm_provider == "anthropic":
            client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            response = await client.messages.create(
                model=settings.claude_model,
                max_tokens=500,
                temperature=0.7,
                system="You are a helpful customer support assistant. Respond naturally to the user.",
                messages=[{"role": "user", "content": request.query}]
            )
            response_text = response.content[0].text
        else:
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful customer support assistant."},
                    {"role": "user", "content": request.query}
                ],
                temperature=0.7,
                max_tokens=500
            )
            response_text = response.choices[0].message.content

    latency_ms = (time.time() - start_time) * 1000

    return {
        "response": response_text,
        "sources": [],
        "sources_json": [],
        "llm_provider": request.llm_provider,
        "model": settings.claude_model if request.llm_provider == "anthropic" else settings.openai_model,
        "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "latency_ms": latency_ms,
        "cost": 0.0  # Minimal cost for canned responses
    }


def _get_recent_context(
    history: Optional[List[ConversationMessage]],
    max_turns: int = 2
) -> Optional[str]:
    """Extract recent conversation context for follow-up queries."""
    if not history:
        return None

    recent = history[-max_turns * 2:]  # Last N turns (user + assistant)
    context_parts = []

    for msg in recent:
        role = "Customer" if msg.role == "user" else "Assistant"
        content = msg.content[:200]  # Truncate long messages
        context_parts.append(f"{role}: {content}")

    return "\n".join(context_parts) if context_parts else None


def _should_evaluate() -> bool:
    """Determine if this response should be evaluated (sampling)."""
    return random.random() < EVALUATION_SAMPLE_RATE


def _format_history_for_evaluation(
    history: Optional[List[ConversationMessage]],
    max_turns: int = 3
) -> Optional[str]:
    """Format conversation history for RAGAS evaluation context.

    Similar to _get_recent_context but for evaluation purposes.
    Includes more context to help RAGAS understand follow-up queries.
    """
    if not history:
        return None

    recent = history[-max_turns * 2:]  # Last N turns (user + assistant pairs)
    context_parts = []

    for msg in recent:
        role = "User" if msg.role == "user" else "Assistant"
        # Allow longer content for evaluation context
        content = msg.content[:500] if len(msg.content) > 500 else msg.content
        context_parts.append(f"{role}: {content}")

    return "\n".join(context_parts) if context_parts else None


async def _evaluate_response_async(
    query_id: uuid.UUID,
    message_type: MessageType,
    conversation_history: Optional[List[ConversationMessage]] = None
):
    """Async background task to evaluate a response with RAGAS.

    Runs RAGAS evaluation metrics on sampled responses.
    For multi-turn conversations, includes conversation history in the
    evaluation query to properly assess follow-up responses.
    """
    from app.db.database import async_session_maker
    from app.evaluation.ragas import RAGASEvaluator
    from app.db.models import Evaluation

    try:
        async with async_session_maker() as db:
            # Get query and response
            query_obj = await db.get(Query, query_id)
            if not query_obj:
                return

            # Get response
            from sqlalchemy import select
            stmt = select(Response).where(Response.query_id == query_id)
            result = await db.execute(stmt)
            response_obj = result.scalar_one_or_none()

            if not response_obj:
                return

            # Get evaluation criteria for message type (for metadata)
            criteria = get_evaluation_criteria(message_type)

            # Build evaluation query with conversation context for follow-ups
            eval_query = query_obj.query_text
            has_context = False

            if message_type == MessageType.FOLLOW_UP and conversation_history:
                # Include conversation history so RAGAS can properly evaluate
                # follow-up responses that depend on prior context
                history_context = _format_history_for_evaluation(conversation_history)
                if history_context:
                    eval_query = f"Conversation context:\n{history_context}\n\nCurrent question: {query_obj.query_text}"
                    has_context = True

            # Run RAGAS evaluation (no ground truth for live queries)
            evaluator = RAGASEvaluator(provider="anthropic")
            evaluation_result = await evaluator.evaluate_response(
                query=eval_query,
                response=response_obj.response_text,
                contexts=response_obj.sources_json or [],
                expected_answer=None
            )

            # Store evaluation
            evaluation = Evaluation(
                id=uuid.uuid4(),
                query_id=query_id,
                evaluation_type=f"ragas_{message_type.value}",
                scores_json=evaluation_result.get("scores", {}),
                evaluator=evaluation_result.get("evaluator", "ragas/anthropic"),
                metadata={
                    "message_type": message_type.value,
                    "async_evaluation": True,
                    "sample_rate": EVALUATION_SAMPLE_RATE,
                    "criteria_context": criteria["criteria"],
                    "has_ground_truth": False,
                    "has_conversation_context": has_context
                }
            )

            db.add(evaluation)
            await db.commit()

            logger.info(f"Async RAGAS evaluation completed for query {query_id} (with_context={has_context})")

    except Exception as e:
        logger.error(f"Async RAGAS evaluation failed for query {query_id}: {e}")


@router.get("/history")
async def get_chat_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent chat history.

    Args:
        limit: Number of recent queries to return

    Returns:
        List of recent queries with responses
    """
    # This will be implemented with proper query logic
    # For now, return placeholder
    return {
        "message": "Chat history endpoint - to be implemented",
        "limit": limit
    }
