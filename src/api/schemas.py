from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3)
    chat_history: Optional[List[ChatMessage]] = None


class SourceItem(BaseModel):
    chunk_id: Optional[str] = None
    doc_name: Optional[str] = None
    article_no: Optional[str] = None
    score: Optional[float] = None


class RetrievedChunk(BaseModel):
    chunk_id: Optional[str] = None
    doc_name: Optional[str] = None
    article_no: Optional[str] = None
    heading: Optional[str] = None
    text: Optional[str] = None
    score: float


class ChatResponse(BaseModel):
    answer: str
    is_fallback: bool
    queries: List[str]
    sources: List[SourceItem]
    retrieved_chunks: List[RetrievedChunk]


class RetrievalDebugResponse(BaseModel):
    queries: List[str]
    retrieved_chunks: List[RetrievedChunk]
    is_fallback: bool


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    checks: Dict[str, bool]
    message: Optional[str] = None


class ConfigResponse(BaseModel):
    embedding_model: str
    llm_model: str
    default_top_k: int
    min_relevance_score: float
