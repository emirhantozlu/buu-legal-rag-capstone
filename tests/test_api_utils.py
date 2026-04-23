from __future__ import annotations

import unittest

from src.api.utils import build_sources, serialize_chunk


class ApiUtilsTests(unittest.TestCase):
    def test_serialize_chunk_uses_section_title_as_heading(self) -> None:
        chunk = {
            "score": 0.91,
            "metadata": {
                "id": "chunk-1",
                "doc_name": "Test Dokumani",
                "article_no": "MADDE 1",
                "section_title": "Amac",
                "text": "Ornek metin",
            },
        }

        result = serialize_chunk(chunk)

        self.assertEqual(result.heading, "Amac")
        self.assertEqual(result.chunk_id, "chunk-1")
        self.assertAlmostEqual(result.score, 0.91)

    def test_build_sources_deduplicates_same_document_and_article(self) -> None:
        raw_chunks = [
            {
                "score": 0.8,
                "metadata": {
                    "id": "a",
                    "doc_name": "Yonetmelik",
                    "article_no": "MADDE 12",
                },
            },
            {
                "score": 0.7,
                "metadata": {
                    "id": "b",
                    "doc_name": "Yonetmelik",
                    "article_no": "MADDE 12",
                },
            },
        ]

        result = build_sources(raw_chunks)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].chunk_id, "a")


if __name__ == "__main__":
    unittest.main()
