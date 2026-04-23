from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL_NAME

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


@dataclass
class RewrittenQuery:
    original: str
    rewritten: List[str]


def _history_to_text(
    chat_history: Optional[Sequence[Dict[str, Any]]],
    max_turns: int = 4,
) -> str:
    if not chat_history:
        return ""

    recent = chat_history[-(max_turns * 2) :]
    lines = []
    for msg in recent:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            lines.append(f"KULLANICI: {content}")
        elif role == "assistant":
            lines.append(f"ASISTAN: {content}")
    return "\n".join(lines)


def rewrite_query(
    question: str,
    chat_history: Optional[Sequence[Dict[str, Any]]] = None,
    num_alternatives: int = 2,
) -> RewrittenQuery:
    if not OPENAI_API_KEY or client is None:
        return RewrittenQuery(original=question, rewritten=[])

    history_text = _history_to_text(chat_history)

    if history_text:
        prompt = f"""
Asagida kullanici ile bir mevzuat asistani arasindaki son konusma gecmisi verilmistir:

{history_text}

Simdi kullanici asagidaki son soruyu soruyor:
"{question}"

Gorevlerin:
1) Bu son soruyu, konusma gecmisinden bagimsiz, tek basina anlasilir bir hukuki/akademik soru haline donustur.
2) Ayrica bu soruya yakin {num_alternatives} tane alternatif sorgu uret.
   - Biri daha genel olabilir
   - Biri daha spesifik veya detayli olabilir.

Cevabi su formatta dondur:
REWRITTEN:
1) ...
2) ...
3) ...
"""
    else:
        prompt = f"""
Kullanici sorusunu hukuki ve akademik bir dile donustur ve
{num_alternatives} alternatif sorgu uret.

Soru: "{question}"

Cevabi su formatta dondur:
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
                "content": "Gorevin, mevzuat tabanli bir RAG sistemine uygun net ve bagimsiz arama sorgulari uretmektir.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    text = response.choices[0].message.content or ""

    rewritten: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0] in ("1", "2", "3", "-") and ")" in line:
            parts = line.split(")", 1)
            candidate = parts[1].strip() if len(parts) == 2 else line
            if candidate:
                rewritten.append(candidate)

    return RewrittenQuery(
        original=question,
        rewritten=rewritten[: max(0, num_alternatives)],
    )
