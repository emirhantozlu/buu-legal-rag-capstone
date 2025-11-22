from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Dict, Any

from openai import OpenAI
from src.config import OPENAI_MODEL_NAME

client = OpenAI()



@dataclass
class RewrittenQuery:
    original: str
    rewritten: List[str]  # 2–3 alternatif query


def _history_to_text(chat_history: Optional[Sequence[Dict[str, Any]]], max_turns: int = 4) -> str:
    """
    Streamlit'ten gelen chat_history yapısını (role, content)
    düz bir metne çevirir. Son max_turns turu kullanıyoruz.
    """
    if not chat_history:
        return ""

    # Sadece son max_turns adet user+assistant mesaj çiftini alalım
    recent = chat_history[-(max_turns * 2) :]
    lines = []
    for msg in recent:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            lines.append(f"KULLANICI: {content}")
        elif role == "assistant":
            lines.append(f"ASİSTAN: {content}")
    return "\n".join(lines)


def rewrite_query(
    question: str,
    chat_history: Optional[Sequence[Dict[str, Any]]] = None,
    num_alternatives: int = 2,
) -> RewrittenQuery:
    """
    Kullanıcı sorusunu daha akademik, hukuki ve açık hale getirir.
    Konuşma geçmişini kullanarak son soruyu bağlamdan bağımsız,
    tek başına anlaşılır bir sorguya dönüştürür.
    """

    history_text = _history_to_text(chat_history)

    if history_text:
        prompt = f"""
Aşağıda kullanıcı ile bir mevzuat asistanı arasındaki son konuşma geçmişi verilmiştir:

{history_text}

Şimdi kullanıcı aşağıdaki son soruyu soruyor:
"{question}"

Görevlerin:
1) Bu son soruyu, konuşma geçmişinden bağımsız, tek başına anlaşılır bir hukuki/akademik soru haline dönüştür.
2) Ayrıca bu soruya yakın {num_alternatives} tane alternatif sorgu üret.
   - Biri daha genel olabilir
   - Biri daha spesifik veya detaylı olabilir.

Cevabı şu formatta döndür:
REWRITTEN:
1) ...
2) ...
3) ...
"""
    else:
        prompt = f"""
Kullanıcı sorusunu hukuki ve akademik bir dile dönüştür ve
{num_alternatives} alternatif sorgu üret.

Soru: "{question}"

Cevabı şu formatta döndür:
REWRITTEN:
1) ...
2) ...
3) ...
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "Görevin, mevzuat tabanlı bir RAG sistemine uygun net ve bağımsız arama sorguları üretmektir.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    text = response.choices[0].message.content

    rewritten: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0] in ("1", "2", "3", "-") and ")" in line:
            # '1) ....', '2) ....' gibi satırlar
            parts = line.split(")", 1)
            if len(parts) == 2:
                candidate = parts[1].strip()
            else:
                candidate = line
            if candidate:
                rewritten.append(candidate)

    if not rewritten:
        rewritten = [question]

    return RewrittenQuery(original=question, rewritten=rewritten)

