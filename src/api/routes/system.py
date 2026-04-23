from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool

from src.api.dependencies import get_pipeline
from src.api.schemas import (
    ChatRequest,
    ConfigResponse,
    HealthResponse,
    RetrievalDebugResponse,
)
from src.api.utils import serialize_chunks, to_chat_history
from src.config import (
    DEFAULT_TOP_K,
    EMBEDDING_MODEL_NAME,
    FAISS_INDEX_PATH,
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
)
from src.rag.pipeline import MIN_RELEVANCE_SCORE, RAGPipeline

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    pipeline_ready = getattr(request.app.state, "pipeline", None) is not None
    pipeline_error = getattr(request.app.state, "pipeline_error", None)
    checks = {
        "pipeline_loaded": pipeline_ready,
        "faiss_index_available": Path(FAISS_INDEX_PATH).exists(),
        "openai_api_key_present": bool(OPENAI_API_KEY),
    }
    status = "ok" if all(checks.values()) else "error"
    return HealthResponse(status=status, checks=checks, message=pipeline_error)


@router.get("/config/models", response_model=ConfigResponse)
async def model_config() -> ConfigResponse:
    return ConfigResponse(
        embedding_model=EMBEDDING_MODEL_NAME,
        llm_model=OPENAI_MODEL_NAME,
        default_top_k=DEFAULT_TOP_K,
        min_relevance_score=MIN_RELEVANCE_SCORE,
    )


@router.get("/system/info", response_model=ConfigResponse)
async def system_info() -> ConfigResponse:
    return await model_config()


@router.post("/retrieval/debug", response_model=RetrievalDebugResponse)
async def debug_retrieval(
    payload: ChatRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> RetrievalDebugResponse:
    chat_history = to_chat_history(payload.chat_history)
    context = await run_in_threadpool(
        pipeline.build_context,
        payload.question,
        chat_history,
    )

    return RetrievalDebugResponse(
        queries=context.queries,
        retrieved_chunks=serialize_chunks(context.retrieved_chunks),
        is_fallback=context.is_fallback,
    )
