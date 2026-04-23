from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import create_app


class AppStartupTests(unittest.TestCase):
    def test_health_endpoint_reports_startup_error(self) -> None:
        with patch("src.api.main.RAGPipeline", side_effect=RuntimeError("missing index")):
            app = create_app()
            with TestClient(app) as client:
                response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertFalse(payload["checks"]["pipeline_loaded"])
        self.assertIn("missing index", payload["message"])

    def test_chat_endpoint_returns_503_when_pipeline_is_unavailable(self) -> None:
        with patch("src.api.main.RAGPipeline", side_effect=RuntimeError("startup failed")):
            app = create_app()
            with TestClient(app) as client:
                response = client.post(
                    "/api/chat/answer",
                    json={"question": "Bu soru neden calismiyor?"},
                )

        self.assertEqual(response.status_code, 503)
        self.assertIn("startup failed", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
