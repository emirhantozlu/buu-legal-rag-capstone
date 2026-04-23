# src/rag/pipeline.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Sequence

import numpy as np
from src.config import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_BACKEND,
    FAISS_INDEX_PATH,
    METADATA_PATH,
    DEFAULT_TOP_K,
    MIN_RELEVANCE_SCORE,
)
from src.embeddings.providers import create_embedding_client

from src.retriever.faiss_index import (
    load_faiss_index,
    load_metadata,
    search_index,
    get_top_k_results,
)
from src.retriever.article_prefilter import ArticleHintPrefilter

from src.rag.query_rewriter import rewrite_query
from src.rag.answer_generator import generate_answer, generate_answer_stream

ARTICLE_PREFILTER_SCORE = 1.15


@dataclass
class PipelineContext:
    question: str
    queries: List[str]
    retrieved_chunks: List[Dict[str, Any]]
    fallback_message: Optional[str] = None

    @property
    def is_fallback(self) -> bool:
        return self.fallback_message is not None


class RAGPipeline:
    def __init__(self):
        self.embed_client = create_embedding_client(
            backend=EMBEDDING_BACKEND,
            model_name=EMBEDDING_MODEL_NAME,
        )
        self.index = load_faiss_index(FAISS_INDEX_PATH)
        self.metadata = load_metadata(METADATA_PATH)
        self.article_prefilter = ArticleHintPrefilter(
            self.metadata,
            target_doc_ids={"yuksek_ogretim_kanunu"},
            doc_keyword_map={
                "kanun": "yuksek_ogretim_kanunu",
                "2547": "yuksek_ogretim_kanunu",
                "yükseköğretim": "yuksek_ogretim_kanunu",
                "yuksek ogretim": "yuksek_ogretim_kanunu",
            },
            max_results=2,
            max_per_article=1,
        )

    def embed_query(self, text: str) -> np.ndarray:
        vec = self.embed_client.embed_one(text)
        return vec.astype("float32")

    def retrieve(self, queries: List[str], top_k: int = DEFAULT_TOP_K):
        all_results: List[Dict[str, Any]] = []

        for q in queries:
            prefilter_hits = self.article_prefilter.find_candidates(q)
            for meta in prefilter_hits:
                all_results.append({
                    "score": ARTICLE_PREFILTER_SCORE,
                    "metadata": meta,
                })

            q_emb = self.embed_query(q)
            distances, indices = search_index(self.index, q_emb, top_k=top_k)
            results = get_top_k_results(distances, indices, self.metadata, top_k)
            all_results.extend(results[0])

        # Duplicate temizleme
        unique = {}
        for r in all_results:
            chunk_id = r["metadata"]["id"]
            if chunk_id not in unique or r["score"] > unique[chunk_id]["score"]:
                unique[chunk_id] = r

        sorted_chunks = sorted(unique.values(), key=lambda x: x["score"], reverse=True)
        return sorted_chunks[:top_k]

    def _fallback_message(self) -> str:
        return (
            "YANIT:\n"
            "Bu soruyla ilgili mevzuatta güvenilir biçimde eşleşen bir hüküm "
            "bulunamadı veya sistem ilgili maddeyi yeterli güvenle tespit edemedi.\n\n"
            "KAYNAKLAR:\n"
            "- (İlgili madde bulunamadı)"
        )

    def build_context(
        self,
        question: str,
        chat_history: Optional[Sequence[Dict[str, Any]]] = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> PipelineContext:
        rewritten = rewrite_query(question, chat_history=chat_history)
        queries = [rewritten.original] + rewritten.rewritten

        retrieved = self.retrieve(queries, top_k=top_k)
        fallback_message: Optional[str] = None

        if not retrieved:
            fallback_message = self._fallback_message()
        else:
            max_score = max(r["score"] for r in retrieved)
            if max_score < MIN_RELEVANCE_SCORE:
                fallback_message = self._fallback_message()

        return PipelineContext(
            question=question,
            queries=queries,
            retrieved_chunks=retrieved,
            fallback_message=fallback_message,
        )

    def answer_with_context(
        self,
        question: str,
        chat_history: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> tuple[str, PipelineContext]:
        context = self.build_context(question, chat_history=chat_history)

        if context.is_fallback:
            # fallback_message asla None olmayacak ama type checker için
            return context.fallback_message or self._fallback_message(), context

        answer_text = generate_answer(
            question,
            context.retrieved_chunks,
        )
        return answer_text, context

    def answer(
        self,
        question: str,
        chat_history: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> str:
        """
        Non-streaming cevap (örneğin CLI testi için).
        Burada chat_history sadece query rewriter için kullanılıyor.
        """
        answer_text, _ = self.answer_with_context(
            question,
            chat_history=chat_history,
        )
        return answer_text

    def answer_stream(
        self,
        question: str,
        chat_history: Optional[Sequence[Dict[str, Any]]] = None,
    ):
        """
        Streaming cevap. Generator döndürür; Streamlit bu generator'dan
        gelen parçaları sırayla ekrana yazabilir.
        chat_history yine sadece rewrite_query için kullanılıyor.
        """
        _, stream = self.answer_stream_with_context(
            question,
            chat_history=chat_history,
        )
        for chunk in stream:
            yield chunk

    def answer_stream_with_context(
        self,
        question: str,
        chat_history: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> tuple[PipelineContext, Any]:
        context = self.build_context(question, chat_history=chat_history)

        if context.is_fallback:
            def _fallback_stream():
                yield context.fallback_message or self._fallback_message()

            return context, _fallback_stream()

        stream = generate_answer_stream(
            question,
            context.retrieved_chunks,
        )
        return context, stream
