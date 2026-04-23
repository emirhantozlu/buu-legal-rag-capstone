"""Heuristic article-level prefiltering for targeted retrieval."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence
import re


def _normalize_doc_id(value: Optional[str]) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    return normalized or None


def _normalize_article_label(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value_str = str(value).strip()
    digits = "".join(ch for ch in value_str if ch.isdigit())
    return digits or None


@dataclass(frozen=True)
class ArticleHint:
    doc_id: str
    article_no: str


class ArticleHintPrefilter:
    """Detects article references in the query and returns matching chunks."""

    def __init__(
        self,
        metadata: Sequence[Dict[str, object]],
        *,
        target_doc_ids: Optional[Iterable[str]] = None,
        doc_keyword_map: Optional[Dict[str, str]] = None,
        max_results: int = 3,
        max_per_article: int = 2,
    ) -> None:
        self._max_results = max(1, max_results)
        self._max_per_article = max(1, max_per_article)
        self._doc_keyword_map = {
            keyword.casefold(): _normalize_doc_id(doc_id)
            for keyword, doc_id in (doc_keyword_map or {}).items()
        }
        connector = r"(?:,|ve|veya|/|-)"
        number_sequence = rf"((?:\d{{1,3}})(?:\s*{connector}\s*\d{{1,3}})*)"
        self._article_patterns = [
            re.compile(
                rf"(?:ek\s+)?madde(?:si|sinin|de|den|ye|yi|nin|ne|ler|leri)?\s*(?:no|numarası|num|\.)?\s*[-:.']?\s*{number_sequence}",
                flags=re.IGNORECASE,
            ),
            re.compile(
                rf"{number_sequence}\s*(?:\.|'|)\s*(?:madde|maddesi|maddeler|md)\b",
                flags=re.IGNORECASE,
            ),
            re.compile(
                rf"madde(?:ler|leri)?\s*(?:arasında|aralık)?\s*{number_sequence}",
                flags=re.IGNORECASE,
            ),
        ]

        target_set = (
            {_normalize_doc_id(doc_id) for doc_id in target_doc_ids}
            if target_doc_ids is not None
            else None
        )
        if target_set is not None:
            target_set.discard(None)
        self._target_doc_ids = target_set

        self._doc_article_index: Dict[str, Dict[str, List[Dict[str, object]]]] = {}
        self._available_doc_ids: List[str] = []
        self._build_index(metadata)

    def _build_index(self, metadata: Sequence[Dict[str, object]]) -> None:
        for entry in metadata:
            if not isinstance(entry, dict):
                continue
            doc_raw = entry.get("doc_id")
            doc_id = _normalize_doc_id(doc_raw)
            if not doc_id:
                continue
            if self._target_doc_ids is not None and doc_id not in self._target_doc_ids:
                continue

            article_norm = _normalize_article_label(entry.get("article_no"))
            if not article_norm:
                continue

            article_map = self._doc_article_index.setdefault(doc_id, {})
            chunk_list = article_map.setdefault(article_norm, [])
            chunk_list.append(entry)

        self._available_doc_ids = sorted(self._doc_article_index.keys())

    def _guess_doc_id(self, question: str) -> Optional[str]:
        text = question.casefold()
        for keyword, doc_id in self._doc_keyword_map.items():
            if keyword in text and doc_id:
                return doc_id
        return None

    def _extract_article_numbers(self, question: str) -> List[str]:
        matches: List[str] = []
        seen = set()
        number_finder = re.compile(r"\d{1,3}")
        for pattern in self._article_patterns:
            for match in pattern.finditer(question):
                span_text = match.group(1) or ""
                if not span_text:
                    continue
                raw_numbers = number_finder.findall(span_text)
                if "/" in span_text and raw_numbers:
                    raw_numbers = raw_numbers[:1]
                for digits in raw_numbers:
                    normalized = digits.lstrip("0") or digits
                    if normalized in seen:
                        continue
                    seen.add(normalized)
                    matches.append(normalized)
        return matches

    def find_candidates(self, question: str) -> List[Dict[str, object]]:
        if not question:
            return []

        doc_hint = self._guess_doc_id(question)
        if doc_hint is None and len(self._available_doc_ids) == 1:
            doc_hint = self._available_doc_ids[0]
        if doc_hint is None:
            return []

        article_numbers = self._extract_article_numbers(question)
        if not article_numbers:
            return []

        doc_index = self._doc_article_index.get(doc_hint)
        if not doc_index:
            return []

        results: List[Dict[str, object]] = []
        for article_no in article_numbers:
            chunks = doc_index.get(article_no)
            if not chunks:
                continue
            results.extend(chunks[: self._max_per_article])
            if len(results) >= self._max_results:
                break
        return results[: self._max_results]

    def describe(self) -> Dict[str, object]:
        return {
            "doc_ids": list(self._doc_article_index.keys()),
            "indexed_articles": {
                doc_id: len(article_map)
                for doc_id, article_map in self._doc_article_index.items()
            },
        }
