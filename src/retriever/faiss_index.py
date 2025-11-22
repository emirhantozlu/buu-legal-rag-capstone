# src/retriever/faiss_index.py

from __future__ import annotations

from typing import List, Dict, Any, Tuple
from pathlib import Path

import numpy as np
import faiss
import json


def load_embeddings(embeddings_path: str | Path) -> np.ndarray:
    """
    .npy dosyasından embedding matrisini yükler.
    """
    embeddings_path = Path(embeddings_path)
    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings dosyası bulunamadı: {embeddings_path}")
    embeddings = np.load(embeddings_path)
    return embeddings.astype("float32")  # faiss float32 bekler


def load_metadata(metadata_path: str | Path) -> List[Dict[str, Any]]:
    """
    JSONL metadata dosyasını yükler.
    """
    metadata_path = Path(metadata_path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata dosyası bulunamadı: {metadata_path}")

    metadata: List[Dict[str, Any]] = []
    with metadata_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            metadata.append(obj)
    return metadata


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Normalleştirilmiş embedding'ler için (cosine similarity) FAISS index oluşturur.

    Biz embedding'leri zaten normalize ettiğimiz için (||v||=1),
    inner product (dot product) = cosine similarity olur.

    Bu yüzden IndexFlatIP kullanıyoruz.
    """
    if embeddings.dtype != np.float32:
        embeddings = embeddings.astype("float32")

    n, d = embeddings.shape
    index = faiss.IndexFlatIP(d)  # Inner Product index
    index.add(embeddings)
    return index


def save_faiss_index(index: faiss.Index, index_path: str | Path) -> None:
    """
    FAISS index'i diske kaydeder.
    """
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))


def load_faiss_index(index_path: str | Path) -> faiss.Index:
    """
    Diske kaydedilmiş FAISS index'i yükler.
    """
    index_path = Path(index_path)
    if not index_path.exists():
        raise FileNotFoundError(f"FAISS index dosyası bulunamadı: {index_path}")
    index = faiss.read_index(str(index_path))
    return index


def search_index(
    index: faiss.Index,
    query_embeddings: np.ndarray,
    top_k: int = 5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Verilen query embedding(ler)i için FAISS index üzerinde arama yapar.

    Args:
        index: FAISS Index
        query_embeddings: (Q, D) boyutunda NumPy array
        top_k: Her query için dönecek sonuç sayısı

    Returns:
        distances: (Q, top_k) benzerlik skorları
        indices:   (Q, top_k) doküman indeksleri
    """
    if query_embeddings.dtype != np.float32:
        query_embeddings = query_embeddings.astype("float32")

    distances, indices = index.search(query_embeddings, top_k)
    return distances, indices


def get_top_k_results(
    distances: np.ndarray,
    indices: np.ndarray,
    metadata: List[Dict[str, Any]],
    top_k: int = 5
) -> List[List[Dict[str, Any]]]:
    """
    FAISS'ten dönen indices + distances çıktılarını,
    metadata listesiyle birleştirip okunabilir yapıya çevirir.

    Returns:
        results[q] = [
            {"score": float, "metadata": {...}},
            ...
        ]
    """
    all_results: List[List[Dict[str, Any]]] = []

    num_queries = indices.shape[0]
    for qi in range(num_queries):
        query_results: List[Dict[str, Any]] = []
        for rank in range(top_k):
            idx = indices[qi, rank]
            if idx < 0:
                continue  # FAISS -1 dönerse geçersiz
            score = float(distances[qi, rank])
            meta = metadata[idx]
            query_results.append(
                {
                    "score": score,
                    "metadata": meta,
                }
            )
        all_results.append(query_results)

    return all_results
