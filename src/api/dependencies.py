from __future__ import annotations

from fastapi import HTTPException, Request

from src.rag.pipeline import RAGPipeline


def get_pipeline(request: Request) -> RAGPipeline:
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        pipeline_error = getattr(request.app.state, "pipeline_error", None)
        detail = "RAG pipeline is not ready yet."
        if pipeline_error:
            detail = f"{detail} Startup error: {pipeline_error}"
        raise HTTPException(status_code=503, detail=detail)
    return pipeline
