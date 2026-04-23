from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROJECT_ROOT as CONFIG_PROJECT_ROOT, YOK_CHUNKS_PATH
from src.preprocessing.pdf_loader import load_pdf_pages
from src.preprocessing.chunker import build_chunks_from_pdf_pages, chunks_to_dicts

DOC_ID = "yuksek_ogretim_kanunu"
DOC_TYPE = "kanun"
DOC_NAME = "2547 Say\u0131l\u0131 Y\u00fcksek\u00f6\u011fretim Kanunu"


def main() -> None:
    pdf_path = CONFIG_PROJECT_ROOT / "data" / "raw" / "yuksek_ogretim_kanunu.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF bulunamad\u0131: {pdf_path}")

    print("PDF yükleniyor:", pdf_path)
    pages = load_pdf_pages(str(pdf_path))
    print(f"Toplam sayfa: {len(pages)}")

    chunks = build_chunks_from_pdf_pages(
        pages=pages,
        doc_id=DOC_ID,
        doc_type=DOC_TYPE,
        doc_name=DOC_NAME,
    )
    print(f"Oluşturulan chunk sayısı: {len(chunks)}")

    YOK_CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with YOK_CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for chunk_dict in chunks_to_dicts(chunks):
            f.write(json.dumps(chunk_dict, ensure_ascii=False) + "\n")

    print(f"Kaydedilen dosya: {YOK_CHUNKS_PATH}")


if __name__ == "__main__":
    main()
