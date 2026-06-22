from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _split_dirs(value: str | None) -> list[Path]:
    if not value:
        return []
    return [Path(part).expanduser().resolve() for part in value.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    http_token: str | None
    allowed_dirs: list[Path]
    max_file_mb: int
    max_download_mb: int
    request_timeout_seconds: float
    openai_vision_model: str
    openai_summary_model: str
    openai_transcribe_model: str
    openai_diarize_model: str

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024

    @property
    def max_download_bytes(self) -> int:
        return self.max_download_mb * 1024 * 1024


def load_settings(require_openai_key: bool = True) -> Settings:
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if require_openai_key and not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    return Settings(
        openai_api_key=openai_api_key,
        http_token=os.getenv("MCP_VISUAL_HTTP_TOKEN"),
        allowed_dirs=_split_dirs(os.getenv("MCP_VISUAL_ALLOWED_DIRS")),
        max_file_mb=int(os.getenv("MCP_VISUAL_MAX_FILE_MB", "25")),
        max_download_mb=int(os.getenv("MCP_VISUAL_MAX_DOWNLOAD_MB", "25")),
        request_timeout_seconds=float(os.getenv("MCP_VISUAL_REQUEST_TIMEOUT_SECONDS", "60")),
        openai_vision_model=os.getenv("OPENAI_VISION_MODEL", "gpt-5.4-mini"),
        openai_summary_model=os.getenv("OPENAI_SUMMARY_MODEL", "gpt-5.4-mini"),
        openai_transcribe_model=os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"),
        openai_diarize_model=os.getenv("OPENAI_DIARIZE_MODEL", "gpt-4o-transcribe-diarize"),
    )

