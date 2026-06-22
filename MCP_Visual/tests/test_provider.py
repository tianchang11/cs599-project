from __future__ import annotations

from pathlib import Path

import pytest

from multimodal_mcp.config import Settings
from multimodal_mcp.media import MediaArtifact
from multimodal_mcp.providers import OpenAIProvider


class FakeTranscriptions:
    def __init__(self) -> None:
        self.kwargs = None

    async def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.kwargs = kwargs
        return {"text": "hello", "language": "en"}


class FakeAudio:
    def __init__(self) -> None:
        self.transcriptions = FakeTranscriptions()


class FakeClient:
    def __init__(self) -> None:
        self.audio = FakeAudio()


def settings() -> Settings:
    return Settings(
        openai_api_key="test",
        http_token="token",
        allowed_dirs=[],
        max_file_mb=1,
        max_download_mb=1,
        request_timeout_seconds=1,
        openai_vision_model="vision",
        openai_summary_model="summary",
        openai_transcribe_model="transcribe",
        openai_diarize_model="diarize",
    )


@pytest.mark.asyncio
async def test_diarize_uses_diarize_model(tmp_path: Path) -> None:
    audio = tmp_path / "clip.mp3"
    audio.write_bytes(b"ID3")
    artifact = MediaArtifact(audio, "audio/mpeg", 3, "path", "clip.mp3")
    client = FakeClient()

    await OpenAIProvider(settings(), client=client).transcribe_audio(artifact, diarize=True)

    assert client.audio.transcriptions.kwargs["model"] == "diarize"

