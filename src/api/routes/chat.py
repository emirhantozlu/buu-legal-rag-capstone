from __future__ import annotations

import json
from typing import Iterator

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_pipeline
from src.api.schemas import ChatRequest, ChatResponse
from src.api.utils import build_sources, serialize_chunks, to_chat_history
from src.rag.pipeline import PipelineContext, RAGPipeline

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _context_to_response(answer: str, context: PipelineContext) -> ChatResponse:
    sources = build_sources(context.retrieved_chunks)
    retrieved_chunks = serialize_chunks(context.retrieved_chunks)

    return ChatResponse(
        answer=answer,
        is_fallback=context.is_fallback,
        queries=context.queries,
        sources=sources,
        retrieved_chunks=retrieved_chunks,
    )


@router.post("/answer", response_model=ChatResponse)
async def create_answer(
    payload: ChatRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> ChatResponse:
    chat_history = to_chat_history(payload.chat_history)
    answer, context = await run_in_threadpool(
        pipeline.answer_with_context,
        payload.question,
        chat_history,
    )
    return _context_to_response(answer, context)


def _format_sse(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/stream")
async def stream_answer(
    payload: ChatRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    chat_history = to_chat_history(payload.chat_history)

    def event_stream() -> Iterator[str]:
        context, stream = pipeline.answer_stream_with_context(
            payload.question,
            chat_history=chat_history,
        )

        sources = build_sources(context.retrieved_chunks)
        retrieved_chunks = serialize_chunks(context.retrieved_chunks)
        context_payload = {
            "queries": context.queries,
            "sources": [src.model_dump() for src in sources],
            "retrieved_chunks": [chunk.model_dump() for chunk in retrieved_chunks],
            "is_fallback": context.is_fallback,
        }
        yield _format_sse("context", context_payload)

        for chunk in stream:
            yield _format_sse("chunk", {"delta": chunk})

        yield _format_sse("done", {"is_fallback": context.is_fallback})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
