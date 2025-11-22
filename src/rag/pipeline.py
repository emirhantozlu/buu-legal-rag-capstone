# src/rag/pipeline.py

from __future__ import annotations

from typing import Dict, Any, List, Optional, Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import (
    EMBEDDING_MODEL_NAME,
    FAISS_INDEX_PATH,
    METADATA_PATH,
    DEFAULT_TOP_K,
)

from src.retriever.faiss_index import (
    load_faiss_index,
    load_metadata,
    search_index,
    get_top_k_results,
)

from src.rag.query_rewriter import rewrite_query
from src.rag.answer_generator import generate_answer, generate_answer_stream

# Basit bir güven eşiği (cosine similarity). İstersen sonra ayarlarız.
MIN_RELEVANCE_SCORE = 0.62


class RAGPipeline:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.index = load_faiss_index(FAISS_INDEX_PATH)
        self.metadata = load_metadata(METADATA_PATH)

    def embed_query(self, text: str) -> np.ndarray:
        vec = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return vec.astype("float32")

    def retrieve(self, queries: List[str], top_k: int = DEFAULT_TOP_K):
        all_results: List[Dict[str, Any]] = []

        for q in queries:
            q_emb = self.embed_query(q)
            distances, indices = search_index(self.index, q_emb, top_k=top_k)
            results = get_top_k_results(distances, indices, self.metadata, top_k)
            all_results.extend(results[0])

        # Duplicate temizleme
        unique = {}
        for r in all_results:
            chunk_id = r["metadata"]["id"]
            if chunk_id not in unique:
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

    def answer(
        self,
        question: str,
        chat_history: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> str:
        """
        Non-streaming cevap (örneğin CLI testi için).
        Burada chat_history sadece query rewriter için kullanılıyor.
        """
        rewritten = rewrite_query(question, chat_history=chat_history)
        queries = [rewritten.original] + rewritten.rewritten

        retrieved = self.retrieve(queries, top_k=DEFAULT_TOP_K)

        if not retrieved:
            return self._fallback_message()

        max_score = max(r["score"] for r in retrieved)
        if max_score < MIN_RELEVANCE_SCORE:
            return self._fallback_message()

        answer_text = generate_answer(
            question,
            retrieved,
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
        rewritten = rewrite_query(question, chat_history=chat_history)
        queries = [rewritten.original] + rewritten.rewritten

        retrieved = self.retrieve(queries, top_k=DEFAULT_TOP_K)

        # Hiç sonuç yoksa ya da en iyi skor düşükse, LLM'e gitmeden sabit mesaj stream edelim
        if not retrieved:
            yield self._fallback_message()
            return

        max_score = max(r["score"] for r in retrieved)
        if max_score < MIN_RELEVANCE_SCORE:
            yield self._fallback_message()
            return

        # Yeterli güven varsa normal streaming cevabı üret
        stream = generate_answer_stream(
            question,
            retrieved,
        )
        for chunk in stream:
            yield chunk
