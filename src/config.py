# src/config.py

from __future__ import annotations

from pathlib import Path
import os
from dotenv import load_dotenv  

# .env dosyasını yükle
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# Proje kök dizini (rag_legal_buu)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "indexes"

# Chunk korpusu için sabit yollar
YOK_CHUNKS_PATH = PROCESSED_DIR / "yuksek_ogretim_kanunu_chunks.jsonl"
BUU_CHUNKS_PATH = PROCESSED_DIR / "buu_yonetmelik_chunks.jsonl"

EMBEDDINGS_PATH = INDEX_DIR / "buu_legal_corpus_embeddings.npy"
METADATA_PATH = INDEX_DIR / "buu_legal_corpus_metadata.jsonl"
FAISS_INDEX_PATH = INDEX_DIR / "buu_legal_corpus_faiss.index"

# Embedding modeli (TR için iyi, çok dilli)
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Retrieval ayarları
DEFAULT_TOP_K = 5
MIN_RELEVANCE_SCORE = 0.25  # çok alakasız sonuçları elemek için eşik

# OpenAI ayarları (LLM tarafı için)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = "gpt-4.1-mini"  # ileride istersen değiştirirsin
