from __future__ import annotations

import ipaddress
import mimetypes
import socket
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field

from multimodal_mcp.config import Settings
from multimodal_mcp.errors import ToolError

IMAGE_MIME_PREFIX = "image/"
AUDIO_MIME_PREFIX = "audio/"
SUPPORTED_MIME_PREFIXES = (IMAGE_MIME_PREFIX, AUDIO_MIME_PREFIX)


class MediaSource(BaseModel):
    type: Literal["path", "url"]
    value: str = Field(min_length=1)


@dataclass
class MediaArtifact:
    path: Path
    mime_type: str
    size_bytes: int
    source_type: Literal["path", "url"]
    display_name: str


class MediaResolver:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def resolve(self, source: MediaSource, expected: Literal["image", "audio"] | None = None) -> MediaArtifact:
        if source.type == "path":
            artifact = self._resolve_path(source.value)
        elif source.type == "url":
            artifact = await self._resolve_url(source.value)
        else:
            raise ToolError("invalid_source", "Source type must be 'path' or 'url'.")

        self._validate_expected_type(artifact.mime_type, expected)
        return artifact

    def _resolve_path(self, value: str) -> MediaArtifact:
        path = Path(value).expanduser().resolve()
        if not self._is_allowed_path(path):
            raise ToolError("invalid_source", "Local path is outside MCP_VISUAL_ALLOWED_DIRS.")
        if not path.is_file():
            raise ToolError("invalid_source", "Local path does not exist or is not a file.")

        size = path.stat().st_size
        if size > self._settings.max_file_bytes:
            raise ToolError("file_too_large", "Local file exceeds MCP_VISUAL_MAX_FILE_MB.")

        mime_type = self._guess_mime(path)
        self._validate_supported_mime(mime_type)
        return MediaArtifact(
            path=path,
            mime_type=mime_type,
            size_bytes=size,
            source_type="path",
            display_name=path.name,
        )

    async def _resolve_url(self, value: str) -> MediaArtifact:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ToolError("invalid_source", "URL source must use http or https.")
        if self._is_private_hostname(parsed.hostname):
            raise ToolError("invalid_source", "URL source must not target localhost or private networks.")

        timeout = httpx.Timeout(self._settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            try:
                async with client.stream("GET", value) as response:
                    response.raise_for_status()
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > self._settings.max_download_bytes:
                        raise ToolError("file_too_large", "Remote file exceeds MCP_VISUAL_MAX_DOWNLOAD_MB.")

                    mime_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                    if not mime_type:
                        mime_type = self._guess_mime(Path(parsed.path))
                    self._validate_supported_mime(mime_type)

                    suffix = mimetypes.guess_extension(mime_type) or Path(parsed.path).suffix or ".bin"
                    temp = tempfile.NamedTemporaryFile(prefix="multimodal-mcp-", suffix=suffix, delete=False)
                    total = 0
                    with temp:
                        async for chunk in response.aiter_bytes():
                            total += len(chunk)
                            if total > self._settings.max_download_bytes:
                                raise ToolError("file_too_large", "Remote file exceeds MCP_VISUAL_MAX_DOWNLOAD_MB.")
                            temp.write(chunk)
            except ToolError:
                raise
            except httpx.TimeoutException as exc:
                raise ToolError("timeout", "Timed out while downloading remote media.") from exc
            except httpx.HTTPError as exc:
                raise ToolError("invalid_source", "Could not download remote media.") from exc

        return MediaArtifact(
            path=Path(temp.name),
            mime_type=mime_type,
            size_bytes=total,
            source_type="url",
            display_name=Path(parsed.path).name or "downloaded-media",
        )

    def _is_allowed_path(self, path: Path) -> bool:
        if not self._settings.allowed_dirs:
            return False
        return any(path == root or root in path.parents for root in self._settings.allowed_dirs)

    def _guess_mime(self, path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(path.name)
        if not mime_type:
            raise ToolError("unsupported_media_type", "Could not determine media MIME type.")
        return mime_type.lower()

    def _validate_supported_mime(self, mime_type: str) -> None:
        if not mime_type.startswith(SUPPORTED_MIME_PREFIXES):
            raise ToolError("unsupported_media_type", "Only image and audio media are supported.")

    def _validate_expected_type(self, mime_type: str, expected: Literal["image", "audio"] | None) -> None:
        if expected == "image" and not mime_type.startswith(IMAGE_MIME_PREFIX):
            raise ToolError("unsupported_media_type", "Expected an image source.")
        if expected == "audio" and not mime_type.startswith(AUDIO_MIME_PREFIX):
            raise ToolError("unsupported_media_type", "Expected an audio source.")

    def _is_private_hostname(self, hostname: str) -> bool:
        if hostname.lower() in {"localhost"}:
            return True
        try:
            addresses = socket.getaddrinfo(hostname, None)
        except socket.gaierror as exc:
            raise ToolError("invalid_source", "Could not resolve URL hostname.") from exc

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
        return False

