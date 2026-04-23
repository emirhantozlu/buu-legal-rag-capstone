from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "indexes"

YOK_CHUNKS_PATH = PROCESSED_DIR / "yuksek_ogretim_kanunu_chunks.jsonl"
BUU_CHUNKS_PATH = PROCESSED_DIR / "buu_yonetmelik_chunks.jsonl"

EMBEDDINGS_PATH = INDEX_DIR / "buu_legal_corpus_embeddings.npy"
METADATA_PATH = INDEX_DIR / "buu_legal_corpus_metadata.jsonl"
FAISS_INDEX_PATH = INDEX_DIR / "buu_legal_corpus_faiss.index"

CHUNKING_PARAMS: Dict[str, Dict[str, Any]] = {
    "default": {
        "max_chars": 1500,
        "propagate_section_title": False,
        "chunk_overlap_chars": 0,
        "prepend_metadata_header": False,
        "force_single_chunk": False,
    },
    "kanun": {
        "max_chars": 900,
        "propagate_section_title": True,
        "chunk_overlap_chars": 120,
        "prepend_metadata_header": True,
        "force_single_chunk": True,
    },
}


def resolve_chunking_params(doc_type: str) -> Dict[str, Any]:
    merged = dict(CHUNKING_PARAMS["default"])
    merged.update(CHUNKING_PARAMS.get(doc_type, {}))
    return merged


EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "openai").strip().lower()
SENTENCE_TRANSFORMER_MODEL = os.getenv(
    "SENTENCE_TRANSFORMER_MODEL",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
)
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

if EMBEDDING_BACKEND not in {"openai", "sentence_transformers"}:
    raise ValueError(
        "EMBEDDING_BACKEND sadece 'openai' veya 'sentence_transformers' olabilir."
    )

EMBEDDING_MODEL_NAME = (
    OPENAI_EMBEDDING_MODEL
    if EMBEDDING_BACKEND == "openai"
    else SENTENCE_TRANSFORMER_MODEL
)

DEFAULT_TOP_K = 5
MIN_RELEVANCE_SCORE = 0.50

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini")
OPENAI_EMBEDDING_MAX_TOKENS = int(os.getenv("OPENAI_EMBEDDING_MAX_TOKENS", "8000"))
