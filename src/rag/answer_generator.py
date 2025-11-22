# src/rag/answer_generator.py

from __future__ import annotations

from typing import List, Dict, Any
from openai import OpenAI

from src.config import OPENAI_MODEL_NAME

client = OpenAI()

# Sistem seviyesinde daha katı bir rol tanımı
SYSTEM_MESSAGE = """
Sen bir RAG tabanlı üniversite mevzuatı asistanısın.

Yalnızca şu iki kaynağa dayanarak yanıt vereceksin:
1) 2547 Sayılı Yükseköğretim Kanunu
2) Bursa Uludağ Üniversitesi Lisansüstü Eğitim-Öğretim Yönetmeliği

Kurallar:
- Yanıtını sadece sana verilen mevzuat metinlerine dayanarak üret.
- Türkiye'deki başka hiçbir kanun, yönetmelik veya mevzuat ismini ANMA (Vergi Usul Kanunu, TCK, vb. kesinlikle geçmeyecek).
- Bağlamda yer almayan hüküm veya bilgiyi uydurma.
- Emin olmadığın konularda tahmin yürütme; bunun yerine mevzuatta açık hüküm olmadığını söyle.
- Metinlerdeki ifadeleri mümkün oldukça özetleyerek, anlaşılır ve akademik bir Türkçe ile açıkla.
- Aşağıda belirtilen çıktı formatına KESİNLİKLE UY.
"""


def _build_prompt(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> str:
    """
    Hem normal hem de streaming cevap için ortak prompt'u hazırlar.
    Burada sadece soru + ilgili maddeler + çok net format talimatı var.
    """

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
            f"[{idx}] Kaynak: {doc_name} – {article_no}\n"
            f"{chunk_text}\n"
        )

    context = "\n".join(context_parts)
    doc_name_list = ", ".join(sorted(doc_names))

    prompt = f"""
Aşağıda üniversite mevzuatından alınmış ilgili maddeler bulunmaktadır.

Kullanılabilecek doküman adları YALNIZCA şunlardır:
{doc_name_list}

Bu listenin DIŞINDA hiçbir kanun veya yönetmelik adı kullanma.

İLGİLİ MEVZUAT METİNLERİ:
{context}

Kullanıcı sorusu:
"{question}"

Şimdi aşağıdaki formatta yanıt üret (biçimi birebir koru):

YANIT:
(buraya sorunun cevabını, sadece yukarıdaki metinlere dayanarak,
özetleyici ve açıklayıcı bir şekilde yaz. Metni kopyalama, özetle.)

KAYNAKLAR:
- Doküman adı – Madde N
- Doküman adı – Madde N

Ek kurallar:
- "YANIT:" ve "KAYNAKLAR:" başlıklarını sadece birer kez kullan.
- KAYNAKLAR kısmında sadece yukarıda listelenen doküman adlarını ve ilgili madde numaralarını yaz.
- Yeni kanun isimleri uydurma; sadece bağlamda geçen doc_name bilgilerini kullan.
- Eğer verilen metinler soruyu doğrudan karşılamıyorsa, YANIT kısmında
  "Soruyla ilgili mevzuatta açık bir hüküm bulunmamaktadır." de
  ve KAYNAKLAR kısmına en ilgili gördüğün 1-2 maddeyi yaz.
"""

    return prompt


def generate_answer(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> str:
    """
    LLM'e kullanıcı sorusunu + chunk metinlerini vererek
    hukuki ve akademik formatta yanıt üretir (non-streaming).
    """

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
        temperature=0.0,  # halüsinasyonu azaltmak için deterministik cevap
    )

    return response.choices[0].message.content


def generate_answer_stream(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
):
    """
    Aynı cevabı bu sefer streaming olarak üretir.
    Streamlit arayüzü, bu fonksiyondan gelen parçaları sırayla yazacaktır.
    """

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
