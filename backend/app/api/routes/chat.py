"""Chat API endpoints."""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chat import ChatRequest, ChatResponse, RetrievedSource, ErrorResponse
from app.core.retrieval.retriever import RAGRetriever
from app.db.database import get_db
from app.db.models import Query, Response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Process a chat query using RAG pipeline.

    This endpoint:
    1. Retrieves relevant documents from ChromaDB
    2. Generates a response using the specified LLM
    3. Stores the query and response in the database
    4. Returns the response with sources and metadata
    """
    try:
        # Initialize RAG retriever
        retriever = RAGRetriever()

        # Build metadata filter if specified
        filter_metadata = None
        if request.filter_category or request.filter_intent:
            filter_metadata = {}
            if request.filter_category:
                filter_metadata["category"] = request.filter_category
            if request.filter_intent:
                filter_metadata["intent"] = request.filter_intent

        # Execute RAG pipeline
        rag_result = await retriever.query(
            query_text=request.query,
            top_k=request.top_k,
            llm_provider=request.llm_provider,
            filter_metadata=filter_metadata
        )

        # Store query in database
        query_id = uuid.uuid4()
        db_query = Query(
            id=query_id,
            query_text=request.query,
            llm_provider=request.llm_provider,
            retrieval_config={
                "top_k": request.top_k,
                "filter_category": request.filter_category,
                "filter_intent": request.filter_intent
            }
        )
        db.add(db_query)

        # Store response in database
        db_response = Response(
            query_id=query_id,
            response_text=rag_result["response"],
            sources_json=[
                {
                    "id": src["id"],
                    "text": src["text"],
                    "score": src["score"],
                    "metadata": src["metadata"]
                }
                for src in rag_result["sources"]
            ],
            latency_ms=rag_result["latency_ms"],
            token_usage=rag_result["token_usage"],
            cost=rag_result["cost"]
        )
        db.add(db_response)

        await db.commit()

        logger.info(f"Query {query_id} processed successfully")

        # Format response
        return ChatResponse(
            query_id=str(query_id),
            query=rag_result["query"],
            response=rag_result["response"],
            sources=[
                RetrievedSource(
                    id=src["id"],
                    text=src["text"],
                    score=src["score"],
                    metadata=src["metadata"]
                )
                for src in rag_result["sources"]
            ],
            llm_provider=rag_result["llm_provider"],
            model=rag_result["model"],
            token_usage=rag_result["token_usage"],
            latency_ms=rag_result["latency_ms"],
            cost=rag_result["cost"]
        )

    except Exception as e:
        logger.error(f"Error processing chat query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
