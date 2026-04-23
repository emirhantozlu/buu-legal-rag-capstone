from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.api.schemas import ChatMessage, RetrievedChunk, SourceItem


def serialize_chunk(raw_chunk: Dict[str, Any]) -> RetrievedChunk:
    metadata = raw_chunk.get("metadata", {}) or {}
    return RetrievedChunk(
        chunk_id=metadata.get("id"),
        doc_name=metadata.get("doc_name"),
        article_no=metadata.get("article_no"),
        heading=metadata.get("section_title") or metadata.get("heading"),
        text=metadata.get("text"),
        score=float(raw_chunk.get("score", 0.0)),
    )


def serialize_chunks(raw_chunks: Iterable[Dict[str, Any]]) -> List[RetrievedChunk]:
    return [serialize_chunk(chunk) for chunk in raw_chunks]


def build_sources(
    raw_chunks: Iterable[Dict[str, Any]],
    limit: Optional[int] = None,
) -> List[SourceItem]:
    sources: List[SourceItem] = []
    seen: set[Tuple[Optional[str], Optional[str]]] = set()

    for chunk in raw_chunks:
        metadata = chunk.get("metadata", {}) or {}
        key = (metadata.get("doc_name"), metadata.get("article_no"))
        if key in seen:
            continue
        seen.add(key)

        sources.append(
            SourceItem(
                chunk_id=metadata.get("id"),
                doc_name=metadata.get("doc_name"),
                article_no=metadata.get("article_no"),
                score=float(chunk.get("score", 0.0)),
            )
        )

        if limit is not None and len(sources) >= limit:
            break

    return sources


def to_chat_history(messages: Optional[List[ChatMessage]]):
    if not messages:
        return None
    return [msg.model_dump() for msg in messages]
