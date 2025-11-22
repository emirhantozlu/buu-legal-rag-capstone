# src/rag/pipeline.py

from __future__ import annotations

from typing import Dict, Any, List

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
from src.rag.answer_generator import generate_answer


class RAGPipeline:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.index = load_faiss_index(FAISS_INDEX_PATH)
        self.metadata = load_metadata(METADATA_PATH)

    def embed_query(self, text: str) -> np.ndarray:
        vec = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return vec.astype("float32")

    def retrieve(self, queries: List[str], top_k: int = DEFAULT_TOP_K):
        all_results = []

        for q in queries:
            q_emb = self.embed_query(q)
            distances, indices = search_index(self.index, q_emb, top_k=top_k)
            results = get_top_k_results(distances, indices, self.metadata, top_k)
            all_results.extend(results[0])

        # Duplicate chunk'ları kaldır (id'ye göre)
        unique = {}
        for r in all_results:
            chunk_id = r["metadata"]["id"]
            if chunk_id not in unique:
                unique[chunk_id] = r

        # Skor sırasına göre sırala
        sorted_chunks = sorted(unique.values(), key=lambda x: x["score"], reverse=True)

        return sorted_chunks[:top_k]

    def answer(self, question: str) -> str:
        rewritten = rewrite_query(question)
        queries = [rewritten.original] + rewritten.rewritten

        retrieved = self.retrieve(queries, top_k=5)
        answer = generate_answer(question, retrieved)
        return answer
