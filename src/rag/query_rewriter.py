# src/rag/query_rewriter.py

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from openai import OpenAI
from src.config import OPENAI_API_KEY, OPENAI_MODEL_NAME


client = OpenAI(api_key=OPENAI_API_KEY)


@dataclass
class RewrittenQuery:
    original: str
    rewritten: List[str]  # 2–3 alternatif query


def rewrite_query(question: str, num_alternatives: int = 2) -> RewrittenQuery:
    """
    Kullanıcı sorusunu daha akademik, hukuki ve açık hale getirir.
    Ayrıca birkaç alternatif sorgu üretir (multi-query RAG için).
    """

    prompt = f"""
Kullanıcı sorusunu daha anlaşılır, hukuki ve akademik bir dile dönüştür.

Soru: "{question}"

Ayrıca {num_alternatives} tane alternatif sorgu üret.
Bu alternatifler:
- Daha genel
- Daha detaylı
- Veya daha resmi bir dilde olabilir.

Cevabı şu formatta döndür:
REWRITTEN:
1) ...
2) ...
3) ...
"""

    response = client.chat.completions.create(
    model=OPENAI_MODEL_NAME,
    messages=[
        {"role": "system", "content": "Sadece yeniden yazılmış sorular döndür."},
        {"role": "user", "content": prompt}
    ]
    )

    text = response.choices[0].message.content


    rewritten = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(("1)", "2)", "3)", "- ")):
            q = line.split(")", 1)[-1].strip()
            rewritten.append(q)

    if not rewritten:
        rewritten = [question]

    return RewrittenQuery(original=question, rewritten=rewritten)
