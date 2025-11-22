# src/rag/answer_generator.py

from __future__ import annotations

from typing import List, Dict, Any
from urllib import response
from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL_NAME


client = OpenAI(api_key=OPENAI_API_KEY)


def generate_answer(question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    LLM'e kullanıcı sorusunu + chunk metinlerini vererek
    hukuki ve akademik formatta yanıt üretir.
    """

    context = ""
    sources_info = []

    for idx, item in enumerate(retrieved_chunks, start=1):
        meta = item["metadata"]
        chunk_text = meta.get("text", "")
        doc_name = meta.get("doc_name", "")
        article_no = meta.get("article_no", "")

        context += (
         f"[{idx}] Kaynak: {doc_name} – {article_no}\n"
            f"{chunk_text}\n\n"
        )

        sources_info.append(f"{doc_name} – {article_no}")

    sources_text = "\n".join(f"- {s}" for s in sources_info)

    prompt = f"""
Aşağıda mevzuattan alınmış ilgili maddeler bulunmaktadır:

{context}

Kullanıcı sorusu: "{question}"

Görev:
- Yalnızca yukarıdaki bağlama dayanarak bir akademik yanıt üret.
- Cevapta keyfi yorum yapma, uydurma bilgi verme.
- Eğer cevap yukarıdaki metinlerde yoksa "Bu soruyla ilgili kesin bir hüküm bulunmamaktadır" de.
- Cevabın sonunda kullanılan maddeleri listele:

Format:
YANIT:
...
KAYNAKLAR:
- Kanun/Yönetmelik – Madde N

"""

    response = client.chat.completions.create(
    model=OPENAI_MODEL_NAME,
    messages=[
        {"role": "system", "content": "Hukuki metinleri özetleyen bir akademik yardımcı asistansın."},
        {"role": "user", "content": prompt}
    ]
    )

    return response.choices[0].message.content

