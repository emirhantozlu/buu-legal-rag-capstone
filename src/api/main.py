from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from src.api.routes import chat, system
from src.rag.pipeline import RAGPipeline


def _format_startup_error(exc: Exception) -> str:
    message = str(exc).strip()
    if message:
        return f"{type(exc).__name__}: {message}"
    return type(exc).__name__


@asynccontextmanager
async def lifespan(app: FastAPI):
    pipeline: Optional[RAGPipeline] = None
    app.state.pipeline = None
    app.state.pipeline_error = None

    try:
        pipeline = RAGPipeline()
    except Exception as exc:  # pragma: no cover - exercised in startup tests
        app.state.pipeline_error = _format_startup_error(exc)
    else:
        app.state.pipeline = pipeline

    try:
        yield
    finally:
        app.state.pipeline = None
        app.state.pipeline_error = None


def create_app() -> FastAPI:
    app = FastAPI(
        title="BUU LLM RAG API",
        version="0.1.0",
        description="Legal RAG API for Bursa Uludag University documents.",
        lifespan=lifespan,
    )

    app.include_router(system.router)
    app.include_router(chat.router)
    return app


app = create_app()
