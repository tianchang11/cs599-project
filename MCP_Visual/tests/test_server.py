from __future__ import annotations

import json
from pathlib import Path

import pytest

from multimodal_mcp.config import Settings
from multimodal_mcp.server import create_mcp


class FakeProvider:
    async def analyze_image(self, artifact, prompt, detail="auto"):  # type: ignore[no-untyped-def]
        return {
            "summary": "A test image.",
            "objects": ["test"],
            "visible_text": ["hello"],
            "safety_notes": [],
            "raw_answer": "ok",
            "text": "hello",
            "blocks": [],
            "language_guess": "en",
            "confidence_notes": [],
            "answer": "yes",
            "evidence": ["image"],
        }

    async def transcribe_audio(self, artifact, language=None, timestamps=False, diarize=False):  # type: ignore[no-untyped-def]
        return {"text": "hello audio", "language": language or "en", "segments": [], "speakers": []}

    async def summarize_text(self, transcript, summary_style, language=None):  # type: ignore[no-untyped-def]
        return {"summary": "short", "key_points": ["one"], "action_items": []}

    async def answer_text_question(self, context, question):  # type: ignore[no-untyped-def]
        return {"answer": "from audio", "evidence": ["transcript"], "intermediate_summary": "hello audio"}


def settings(tmp_path: Path) -> Settings:
    return Settings(
        openai_api_key="test",
        http_token="token",
        allowed_dirs=[tmp_path],
        max_file_mb=1,
        max_download_mb=1,
        request_timeout_seconds=1,
        openai_vision_model="vision",
        openai_summary_model="summary",
        openai_transcribe_model="transcribe",
        openai_diarize_model="diarize",
    )


@pytest.mark.asyncio
async def test_tools_are_registered(tmp_path: Path) -> None:
    mcp = create_mcp(settings(tmp_path), FakeProvider())
    tools = await mcp.list_tools()

    assert {tool.name for tool in tools} == {
        "vision_analyze",
        "ocr_image",
        "audio_transcribe",
        "audio_summarize",
        "media_qa",
    }


@pytest.mark.asyncio
async def test_vision_tool_returns_structured_json(tmp_path: Path) -> None:
    image = tmp_path / "photo.png"
    image.write_bytes(b"\x89PNG\r\n")
    mcp = create_mcp(settings(tmp_path), FakeProvider())

    result = await mcp.call_tool(
        "vision_analyze",
        {"source": {"type": "path", "value": str(image)}, "detail": "auto"},
    )
    content, structured_result = result
    payload = json.loads(content[0].text)

    assert payload["summary"] == "A test image."
    assert json.loads(structured_result["result"])["summary"] == "A test image."
