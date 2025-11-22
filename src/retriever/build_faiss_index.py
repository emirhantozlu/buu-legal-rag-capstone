# src/retriever/build_faiss_index.py

"""
Embedding dosyalarından FAISS index oluşturur ve kaydeder.

Terminalden çalıştırmak için:
    python -m src.retriever.build_faiss_index
"""

from pathlib import Path
from src.retriever.faiss_index import (
    load_embeddings,
    load_metadata,
    build_faiss_index,
    save_faiss_index,
)


def main():
    project_root = Path(__file__).resolve().parents[2]  # rag_legal_buu/

    embeddings_path = project_root / "data" / "indexes" / "buu_legal_corpus_embeddings.npy"
    metadata_path = project_root / "data" / "indexes" / "buu_legal_corpus_metadata.jsonl"
    index_path = project_root / "data" / "indexes" / "buu_legal_corpus_faiss.index"

    print("=== BUÜ Legal Corpus FAISS Index Script ===")
    print("Embeddings:", embeddings_path)
    print("Metadata:  ", metadata_path)
    print("Index out: ", index_path)
    print("------------------------------------------")

    embeddings = load_embeddings(embeddings_path)
    print("Embeddings shape:", embeddings.shape)

    metadata = load_metadata(metadata_path)
    print("Metadata entries:", len(metadata))

    if embeddings.shape[0] != len(metadata):
        raise ValueError("Embeddings sayısı ile metadata satır sayısı uyuşmuyor!")

    index = build_faiss_index(embeddings)
    save_faiss_index(index, index_path)

    print("\nFAISS index oluşturuldu ve kaydedildi!")


if __name__ == "__main__":
    main()
