from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from multimodal_mcp.config import Settings
from multimodal_mcp.http_app import create_app


def settings(tmp_path: Path) -> Settings:
    return Settings(
        openai_api_key="test",
        http_token="secret",
        allowed_dirs=[tmp_path],
        max_file_mb=1,
        max_download_mb=1,
        request_timeout_seconds=1,
        openai_vision_model="vision",
        openai_summary_model="summary",
        openai_transcribe_model="transcribe",
        openai_diarize_model="diarize",
    )


def test_health_does_not_require_auth(tmp_path: Path) -> None:
    client = TestClient(create_app(settings(tmp_path)))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_mcp_requires_auth(tmp_path: Path) -> None:
    client = TestClient(create_app(settings(tmp_path)))

    response = client.post("/mcp", json={})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_required"

