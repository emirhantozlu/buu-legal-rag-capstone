"""Doc-level lexical reranking helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from rank_bm25 import BM25Okapi
import re

TokenizeFn = Callable[[str], List[str]]
NormalizeDocFn = Callable[[Optional[str]], Optional[str]]

_TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)


def default_tokenizer(text: str) -> List[str]:
    """Lightweight tokenizer that is Turkish-aware via str.casefold."""
    if not isinstance(text, str):
        return []
    # casefold helps with dotted/dotless-I and other locale specific chars.
    return _TOKEN_PATTERN.findall(text.casefold())


def passthrough_normalizer(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.strip().lower() or None


@dataclass
class RerankStats:
    doc_count: int
    chunk_count: int
    target_docs: Optional[List[str]]


class BM25DocReranker:
    """Simple BM25 reranker that reorders chunk candidates per document."""

    def __init__(
        self,
        metadata: Sequence[Dict[str, object]],
        *,
        normalize_doc_fn: NormalizeDocFn | None = None,
        tokenize_fn: TokenizeFn | None = None,
        target_doc_ids: Optional[Iterable[str]] = None,
        score_saturation: float = 8.0,
    ) -> None:
        self._normalize_doc = normalize_doc_fn or passthrough_normalizer
        self._tokenize = tokenize_fn or default_tokenizer
        self._score_saturation = max(score_saturation, 1.0)

        target_set = (
            {self._normalize_doc(doc_id) for doc_id in target_doc_ids}
            if target_doc_ids is not None
            else None
        )
        if target_set is not None:
            target_set.discard(None)
        self._target_doc_ids = target_set

        self._doc_models: Dict[str, BM25Okapi] = {}
        self._doc_chunk_indices: Dict[str, List[int]] = {}
        self._chunk_token_cache: Dict[str, List[List[str]]] = {}

        self._build_models(metadata)

    def _build_models(self, metadata: Sequence[Dict[str, object]]) -> None:
        for idx, entry in enumerate(metadata):
            doc_raw = entry.get("doc_id") if isinstance(entry, dict) else None
            doc_id = self._normalize_doc(doc_raw) if doc_raw else None
            if not doc_id:
                continue
            if self._target_doc_ids is not None and doc_id not in self._target_doc_ids:
                continue

            text_value = entry.get("text") if isinstance(entry, dict) else None
            tokens = self._tokenize(text_value or "")
            if not tokens:
                continue

            chunk_list = self._chunk_token_cache.setdefault(doc_id, [])
            chunk_list.append(tokens)

            chunk_indices = self._doc_chunk_indices.setdefault(doc_id, [])
            chunk_indices.append(idx)

        for doc_id, corpus in self._chunk_token_cache.items():
            if corpus:
                self._doc_models[doc_id] = BM25Okapi(corpus)

    def describe(self) -> RerankStats:
        doc_ids = sorted(self._doc_models.keys()) or None
        total_chunks = sum(len(indices) for indices in self._doc_chunk_indices.values())
        return RerankStats(
            doc_count=len(self._doc_models),
            chunk_count=total_chunks,
            target_docs=doc_ids,
        )

    def supports(self, doc_id: Optional[str]) -> bool:
        normalized = self._normalize_doc(doc_id) if doc_id else None
        return bool(normalized and normalized in self._doc_models)

    def rerank(
        self,
        query: str,
        doc_id: str,
        candidate_indices: Sequence[int],
        *,
        embedding_scores: Optional[Sequence[float]] = None,
        alpha: float = 0.6,
    ) -> List[Tuple[int, float]]:
        """Rerank chunk indices for a single document."""
        normalized_doc_id = self._normalize_doc(doc_id)
        if not normalized_doc_id:
            return [(idx, float(embedding_scores[i]) if embedding_scores else 0.0) for i, idx in enumerate(candidate_indices)]

        model = self._doc_models.get(normalized_doc_id)
        if model is None:
            return [(idx, float(embedding_scores[i]) if embedding_scores else 0.0) for i, idx in enumerate(candidate_indices)]

        chunk_index_list = self._doc_chunk_indices.get(normalized_doc_id, [])
        position_by_chunk = {chunk_idx: pos for pos, chunk_idx in enumerate(chunk_index_list)}

        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return [(idx, float(embedding_scores[i]) if embedding_scores else 0.0) for i, idx in enumerate(candidate_indices)]

        bm25_scores = model.get_scores(tokenized_query)

        combined: List[Tuple[int, float]] = []
        for rank, chunk_idx in enumerate(candidate_indices):
            pos = position_by_chunk.get(chunk_idx)
            if pos is None:
                continue
            lexical_raw = float(bm25_scores[pos])
            lexical_norm = lexical_raw / (lexical_raw + self._score_saturation)
            dense_score = float(embedding_scores[rank]) if embedding_scores is not None and rank < len(embedding_scores) else 0.0
            hybrid_score = (alpha * lexical_norm) + ((1.0 - alpha) * dense_score)
            combined.append((chunk_idx, hybrid_score))

        combined.sort(key=lambda item: item[1], reverse=True)
        return combined


def rerank_or_default(
    reranker: Optional[BM25DocReranker],
    *,
    query: str,
    doc_id: str,
    candidate_indices: Sequence[int],
    embedding_scores: Sequence[float],
    alpha: float = 0.6,
) -> List[int]:
    if reranker is None or not reranker.supports(doc_id):
        return list(candidate_indices)

    reranked = reranker.rerank(
        query=query,
        doc_id=doc_id,
        candidate_indices=candidate_indices,
        embedding_scores=embedding_scores,
        alpha=alpha,
    )
    return [idx for idx, _ in reranked]
