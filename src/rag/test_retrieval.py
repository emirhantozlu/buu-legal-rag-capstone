# src/rag/test_retrieval.py

"""
Bu script, FAISS index ve metadata kullanarak
komut satırından basit retrieval testi yapar.

Çalıştırmak için:
    python -m src.rag.test_retrieval
"""

from pathlib import Path

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


def embed_query(model: SentenceTransformer, query: str) -> np.ndarray:
    """
    Kullanıcı sorgusunu embedding'e çevirir.
    """
    vec = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vec.astype("float32")


def pretty_print_results(results):
    """
    Top-k sonuçlarını terminalde okunabilir şekilde yazar.
    """
    for i, res in enumerate(results[0], start=1):
        meta = res["metadata"]
        score = res["score"]
        doc_name = meta.get("doc_name", "N/A")
        article_no = meta.get("article_no", "N/A")
        snippet = meta.get("text", "")[:200].replace("\n", " ")

        print(f"[{i}] Skor: {score:.3f}")
        print(f"    Kaynak: {doc_name} - {article_no}")
        print(f"    Özet  : {snippet}...")
        print("")


def main():
    # 1) Model, index ve metadata'yı yükle
    print("Embedding modeli yükleniyor...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("FAISS index yükleniyor...")
    index = load_faiss_index(FAISS_INDEX_PATH)

    print("Metadata yükleniyor...")
    metadata = load_metadata(METADATA_PATH)

    # 2) Test için birkaç örnek soru
    test_queries = [
        "Lisansüstü programların amacı nedir?",
        "Lisansüstü eğitimde harç iadesi hangi durumlarda yapılır?",
        "Yükseköğretim kurumlarının tanımı nedir?",
        "Enstitülerin akademik takvimi kim tarafından belirlenir?",
    ]

    for q in test_queries:
        print("=" * 80)
        print("Soru:", q)
        print("-" * 80)

        q_emb = embed_query(model, q)
        distances, indices = search_index(index, q_emb, top_k=DEFAULT_TOP_K)
        results = get_top_k_results(distances, indices, metadata, top_k=DEFAULT_TOP_K)

        pretty_print_results(results)


if __name__ == "__main__":
    main()
