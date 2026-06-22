from __future__ import annotations

from pathlib import Path

import pytest

from multimodal_mcp.config import Settings
from multimodal_mcp.errors import ToolError
from multimodal_mcp.media import MediaResolver, MediaSource


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
async def test_path_inside_allowed_dir_passes(tmp_path: Path) -> None:
    image = tmp_path / "photo.png"
    image.write_bytes(b"\x89PNG\r\n")

    artifact = await MediaResolver(settings(tmp_path)).resolve(MediaSource(type="path", value=str(image)), "image")

    assert artifact.path == image.resolve()
    assert artifact.mime_type == "image/png"


@pytest.mark.asyncio
async def test_path_outside_allowed_dir_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.png"
    outside.write_bytes(b"\x89PNG\r\n")

    with pytest.raises(ToolError) as exc:
        await MediaResolver(settings(tmp_path)).resolve(MediaSource(type="path", value=str(outside)), "image")

    assert exc.value.code == "invalid_source"


@pytest.mark.asyncio
async def test_expected_media_type_is_enforced(tmp_path: Path) -> None:
    audio = tmp_path / "clip.mp3"
    audio.write_bytes(b"ID3")

    with pytest.raises(ToolError) as exc:
        await MediaResolver(settings(tmp_path)).resolve(MediaSource(type="path", value=str(audio)), "image")

    assert exc.value.code == "unsupported_media_type"


@pytest.mark.asyncio
async def test_file_size_limit_is_enforced(tmp_path: Path) -> None:
    image = tmp_path / "large.png"
    image.write_bytes(b"0" * (1024 * 1024 + 1))

    with pytest.raises(ToolError) as exc:
        await MediaResolver(settings(tmp_path)).resolve(MediaSource(type="path", value=str(image)), "image")

    assert exc.value.code == "file_too_large"


@pytest.mark.asyncio
async def test_localhost_url_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ToolError) as exc:
        await MediaResolver(settings(tmp_path)).resolve(MediaSource(type="url", value="http://localhost/photo.png"), "image")

    assert exc.value.code == "invalid_source"

