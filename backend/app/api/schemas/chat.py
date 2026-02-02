"""Pydantic schemas for chat API."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """A message in the conversation history."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat query request with multi-turn conversation support."""
    query: str = Field(..., description="User's question", min_length=1)
    llm_provider: Optional[str] = Field("anthropic", description="LLM provider: anthropic or openai")
    top_k: Optional[int] = Field(5, description="Number of documents to retrieve", ge=1, le=20)
    filter_category: Optional[str] = Field(None, description="Filter by category")
    filter_intent: Optional[str] = Field(None, description="Filter by intent")
    conversation_history: Optional[List[ConversationMessage]] = Field(
        None,
        description="Previous messages in the conversation for context"
    )


class RetrievedSource(BaseModel):
    """Retrieved source document."""
    id: str
    text: str
    score: float = Field(..., description="Relevance score (0-1)")
    metadata: Dict[str, Any]


class ChatResponse(BaseModel):
    """Chat query response with message classification."""
    query_id: str = Field(..., description="Unique query ID")
    query: str
    response: str
    sources: List[RetrievedSource]
    llm_provider: str
    model: str
    token_usage: Dict[str, int]
    latency_ms: float
    cost: float
    message_type: Optional[str] = Field(
        None,
        description="Classified message type (question, follow_up, acknowledgment, etc.)"
    )


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
