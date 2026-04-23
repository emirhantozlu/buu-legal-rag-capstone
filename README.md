# BUU Legal RAG

BUU Legal RAG, Bursa Uludag Universitesi mevzuat belgeleri uzerinde soru-cevap ve retrieval akisi sunan bir RAG projesidir. Backend tarafinda FastAPI, retrieval katmaninda FAISS, arayuz tarafinda React + Vite kullanir.

## Klasor Yapisi

```text
buu_llm_rag/
|- src/                     # Uygulama kaynak kodu
|  |- api/                  # FastAPI endpointleri
|  |- app/                  # Opsiyonel Streamlit arayuzu
|  |- embeddings/           # Embedding istemcileri ve uretim akisi
|  |- preprocessing/        # PDF temizleme ve chunking
|  |- rag/                  # Pipeline, query rewriting, answer generation
|  `- retriever/            # FAISS, reranker ve retrieval yardimcilari
|- frontend/                # React/Vite istemcisi
|- scripts/                 # Operasyonel ve smoke-test scriptleri
|- tests/                   # Otomatik testler
|  `- fixtures/             # Test verileri
|- notebooks/               # Arastirma ve analiz notebooklari
|  `- reports/              # Rapor notebooklari
|- .env.example
|- pyproject.toml
`- requirements.txt
```

## Kurulum

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

`requirements/base.txt` runtime bagimliliklarini, `requirements/dev.txt` ise notebook ve gelistirme araclarini tutar.

Backend'i calistirmak icin:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run typecheck
npm run build
npm run dev
```

## Veri ve Indeks Akisi

Buyuk veri ve index dosyalari repoya commit edilmez. Yeni veriyle calismak icin tipik akis:

```powershell
.\.venv\Scripts\python.exe scripts/rebuild_kanun_chunks.py
.\.venv\Scripts\python.exe -m src.embeddings.build_embeddings
.\.venv\Scripts\python.exe -m src.retriever.build_faiss_index
.\.venv\Scripts\python.exe scripts/run_retrieval_smoke.py
```

## API

- `GET /api/health`
- `GET /api/config/models`
- `GET /api/system/info`
- `POST /api/chat/answer`
- `POST /api/chat/stream`
- `POST /api/retrieval/debug`

## Test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

## Repo Kurallari

- `frontend/node_modules/`, `frontend/dist/`, `__pycache__` ve derleme artefaktlari takip edilmez.
- `.env` commit edilmez; sadece `.env.example` tutulur.
- `tests/` sadece otomatik test ve fixture dosyalari icindir.
- Notebook ve raporlar `notebooks/` altinda tutulur.
- GitHub Actions CI tanimi `.github/workflows/ci.yml` altinda tutulur.
