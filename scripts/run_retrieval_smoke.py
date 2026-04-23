from __future__ import annotations

import numpy as np

from src.config import (
    DEFAULT_TOP_K,
    EMBEDDING_BACKEND,
    EMBEDDING_MODEL_NAME,
    FAISS_INDEX_PATH,
    METADATA_PATH,
)
from src.embeddings.providers import BaseEmbeddingClient, create_embedding_client
from src.retriever.faiss_index import (
    get_top_k_results,
    load_faiss_index,
    load_metadata,
    search_index,
)


def embed_query(client: BaseEmbeddingClient, query: str) -> np.ndarray:
    vec = client.embed_one(query)
    return vec.astype("float32")


def pretty_print_results(results) -> None:
    for i, res in enumerate(results[0], start=1):
        meta = res["metadata"]
        score = res["score"]
        doc_name = meta.get("doc_name", "N/A")
        article_no = meta.get("article_no", "N/A")
        snippet = meta.get("text", "")[:200].replace("\n", " ")

        print(f"[{i}] Skor: {score:.3f}")
        print(f"    Kaynak: {doc_name} - {article_no}")
        print(f"    Ozet  : {snippet}...")
        print("")


def main() -> None:
    print("Embedding modeli yukleniyor...")
    client = create_embedding_client(
        backend=EMBEDDING_BACKEND,
        model_name=EMBEDDING_MODEL_NAME,
    )

    print("FAISS index yukleniyor...")
    index = load_faiss_index(FAISS_INDEX_PATH)

    print("Metadata yukleniyor...")
    metadata = load_metadata(METADATA_PATH)

    test_queries = [
        "Lisansustu programlarin amaci nedir?",
        "Lisansustu egitimde harc iadesi hangi durumlarda yapilir?",
        "Yuksekogretim kurumlarinin tanimi nedir?",
        "Enstitulerin akademik takvimi kim tarafindan belirlenir?",
    ]

    for query in test_queries:
        print("=" * 80)
        print("Soru:", query)
        print("-" * 80)

        query_embedding = embed_query(client, query)
        distances, indices = search_index(index, query_embedding, top_k=DEFAULT_TOP_K)
        results = get_top_k_results(distances, indices, metadata, top_k=DEFAULT_TOP_K)

        pretty_print_results(results)


if __name__ == "__main__":
    main()
