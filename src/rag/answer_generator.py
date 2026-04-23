from __future__ import annotations

from typing import Any, Dict, List

from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL_NAME

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_MESSAGE = """
Sen bir RAG tabanli universite mevzuati asistansin.

Yalnizca su iki kaynaga dayanarak yanit vereceksin:
1) 2547 Sayili Yuksekogretim Kanunu
2) Bursa Uludag Universitesi Lisansustu Egitim-Ogretim Yonetmeligi

Kurallar:
- Yanitini sadece sana verilen mevzuat metinlerine dayanarak uret.
- Baglamda yer almayan hukum veya bilgiyi uydurma.
- Emin olmadigin konularda tahmin yurutme; bunun yerine mevzuatta acik hukum olmadigini soyle.
- Metinlerdeki ifadeleri ozetleyerek, anlasilir ve akademik bir Turkce ile acikla.
- Asagidaki cikti formatina kesinlikle uy.
"""


def _build_sources_list(retrieved_chunks: List[Dict[str, Any]]) -> str:
    seen = set()
    lines: List[str] = []

    for item in retrieved_chunks:
        metadata = item.get("metadata", {}) or {}
        doc_name = metadata.get("doc_name") or "Bilinmeyen dokuman"
        article_no = metadata.get("article_no") or "Madde belirtilmedi"
        label = f"- {doc_name} - {article_no}"
        if label in seen:
            continue
        seen.add(label)
        lines.append(label)

    return "\n".join(lines) if lines else "- Kaynak bulunamadi"


def _build_local_fallback_answer(retrieved_chunks: List[Dict[str, Any]]) -> str:
    if not retrieved_chunks:
        return (
            "YANIT:\n"
            "OpenAI API anahtari tanimli olmadigi icin dil modeli cevabi uretilemiyor.\n\n"
            "KAYNAKLAR:\n"
            "- Kaynak bulunamadi"
        )

    primary_text = (retrieved_chunks[0].get("metadata", {}) or {}).get("text", "").strip()
    if len(primary_text) > 900:
        primary_text = primary_text[:900].rsplit(" ", 1)[0].rstrip() + "..."

    excerpt = primary_text or "Ilgili metin parcasi bos geldi."
    sources_text = _build_sources_list(retrieved_chunks)

    return (
        "YANIT:\n"
        "OpenAI API anahtari tanimli olmadigi icin cevap yerel ozet modunda gosteriliyor. "
        "En ilgili mevzuat parcasi asagidadir:\n"
        f"{excerpt}\n\n"
        "KAYNAKLAR:\n"
        f"{sources_text}"
    )


def _build_prompt(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> str:
    context_parts = []
    doc_names = set()

    for idx, item in enumerate(retrieved_chunks, start=1):
        meta = item["metadata"]
        chunk_text = meta.get("text", "")
        doc_name = meta.get("doc_name", "")
        article_no = meta.get("article_no", "")

        if doc_name:
            doc_names.add(doc_name)

        context_parts.append(
            f"[{idx}] Kaynak: {doc_name} - {article_no}\n"
            f"{chunk_text}\n"
        )

    context = "\n".join(context_parts)
    doc_name_list = ", ".join(sorted(doc_names))

    return f"""
Asagida universite mevzuatindan alinmis ilgili maddeler bulunmaktadir.

Kullanilabilecek dokuman adlari yalnizca sunlardir:
{doc_name_list}

Ilgili mevzuat metinleri:
{context}

Kullanici sorusu:
"{question}"

Simdi asagidaki formatta yanit uret:

YANIT:
(Buraya sorunun cevabini sadece yukaridaki metinlere dayanarak, ozetleyici ve aciklayici bir sekilde yaz.)

KAYNAKLAR:
- Dokuman adi - Madde N
- Dokuman adi - Madde N
"""


def generate_answer(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> str:
    if not OPENAI_API_KEY or client is None:
        return _build_local_fallback_answer(retrieved_chunks)

    prompt = _build_prompt(question, retrieved_chunks)

    response = client.chat.completions.create(
        model=OPENAI_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_MESSAGE,
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    return response.choices[0].message.content or _build_local_fallback_answer(retrieved_chunks)


def generate_answer_stream(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
):
    if not OPENAI_API_KEY or client is None:
        yield _build_local_fallback_answer(retrieved_chunks)
        return

    prompt = _build_prompt(question, retrieved_chunks)

    stream = client.chat.completions.create(
        model=OPENAI_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_MESSAGE,
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
