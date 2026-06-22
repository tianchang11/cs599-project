from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from multimodal_mcp.config import Settings, load_settings
from multimodal_mcp.errors import ToolError, error_payload, json_payload
from multimodal_mcp.media import MediaResolver, MediaSource
from multimodal_mcp.providers import OpenAIProvider

logger = logging.getLogger("multimodal_mcp")


class VisionAnalyzeInput(BaseModel):
    source: MediaSource
    prompt: str | None = None
    detail: Literal["low", "high", "auto"] = "auto"


class OcrImageInput(BaseModel):
    source: MediaSource
    languages: list[str] | None = None


class AudioTranscribeInput(BaseModel):
    source: MediaSource
    language: str | None = None
    timestamps: bool = False
    diarize: bool = False


class AudioSummarizeInput(BaseModel):
    source: MediaSource
    summary_style: str = Field(default="concise", min_length=1)
    language: str | None = None


class MediaQaInput(BaseModel):
    source: MediaSource
    media_type: Literal["image", "audio"]
    question: str = Field(min_length=1)


def create_mcp(settings: Settings | None = None, provider: OpenAIProvider | None = None) -> FastMCP:
    settings = settings or load_settings()
    resolver = MediaResolver(settings)
    provider = provider or OpenAIProvider(settings)
    mcp = FastMCP("multimodal-mcp", stateless_http=True, json_response=True)

    @mcp.tool()
    async def vision_analyze(source: dict[str, str], prompt: str | None = None, detail: str = "auto") -> str:
        """Analyze an image and return description, objects, visible text, and notes."""
        args = VisionAnalyzeInput(source=source, prompt=prompt, detail=detail)  # type: ignore[arg-type]

        async def run() -> dict[str, Any]:
            artifact = await resolver.resolve(args.source, expected="image")
            analysis_prompt = args.prompt or (
                "Analyze this image. Return JSON with keys summary, objects, visible_text, "
                "safety_notes, and raw_answer."
            )
            result = await provider.analyze_image(artifact, analysis_prompt, args.detail)
            return {
                "summary": result.get("summary", ""),
                "objects": result.get("objects", []),
                "visible_text": result.get("visible_text", result.get("ocr_text", [])),
                "safety_notes": result.get("safety_notes", []),
                "raw_answer": result.get("raw_answer", result),
            }

        return await _run_tool("vision_analyze", "image", run)

    @mcp.tool()
    async def ocr_image(source: dict[str, str], languages: list[str] | None = None) -> str:
        """Extract visible text from an image."""
        args = OcrImageInput(source=source, languages=languages)  # type: ignore[arg-type]

        async def run() -> dict[str, Any]:
            artifact = await resolver.resolve(args.source, expected="image")
            language_hint = f" Languages to prioritize: {', '.join(args.languages)}." if args.languages else ""
            result = await provider.analyze_image(
                artifact,
                "Perform OCR on this image. Return JSON with keys text, blocks, "
                f"language_guess, and confidence_notes.{language_hint}",
                "high",
            )
            return {
                "text": result.get("text", result.get("raw_answer", "")),
                "blocks": result.get("blocks", []),
                "language_guess": result.get("language_guess", ""),
                "confidence_notes": result.get("confidence_notes", []),
            }

        return await _run_tool("ocr_image", "image", run)

    @mcp.tool()
    async def audio_transcribe(
        source: dict[str, str],
        language: str | None = None,
        timestamps: bool = False,
        diarize: bool = False,
    ) -> str:
        """Transcribe audio, optionally with segment timestamps or speaker diarization."""
        args = AudioTranscribeInput(
            source=source, language=language, timestamps=timestamps, diarize=diarize  # type: ignore[arg-type]
        )

        async def run() -> dict[str, Any]:
            artifact = await resolver.resolve(args.source, expected="audio")
            result = await provider.transcribe_audio(
                artifact,
                language=args.language,
                timestamps=args.timestamps,
                diarize=args.diarize,
            )
            return {
                "text": result.get("text", ""),
                "language": result.get("language", args.language or ""),
                "segments": result.get("segments"),
                "speakers": result.get("speakers"),
            }

        return await _run_tool("audio_transcribe", "audio", run)

    @mcp.tool()
    async def audio_summarize(source: dict[str, str], summary_style: str = "concise", language: str | None = None) -> str:
        """Transcribe and summarize an audio file."""
        args = AudioSummarizeInput(source=source, summary_style=summary_style, language=language)  # type: ignore[arg-type]

        async def run() -> dict[str, Any]:
            artifact = await resolver.resolve(args.source, expected="audio")
            transcript = await provider.transcribe_audio(artifact, language=args.language)
            transcript_text = transcript.get("text", "")
            summary = await provider.summarize_text(transcript_text, args.summary_style, args.language)
            return {
                "transcript": transcript_text,
                "summary": summary.get("summary", ""),
                "key_points": summary.get("key_points", []),
                "action_items": summary.get("action_items", []),
            }

        return await _run_tool("audio_summarize", "audio", run)

    @mcp.tool()
    async def media_qa(source: dict[str, str], media_type: str, question: str) -> str:
        """Answer a question about an image or audio file."""
        args = MediaQaInput(source=source, media_type=media_type, question=question)  # type: ignore[arg-type]

        async def run() -> dict[str, Any]:
            artifact = await resolver.resolve(args.source, expected=args.media_type)
            if args.media_type == "image":
                result = await provider.analyze_image(
                    artifact,
                    f"Answer this question about the image. Return JSON with keys answer and evidence.\n\n{args.question}",
                    "auto",
                )
                return {
                    "answer": result.get("answer", result.get("raw_answer", "")),
                    "evidence": result.get("evidence", []),
                    "intermediate_summary": result.get("intermediate_summary"),
                }

            transcript = await provider.transcribe_audio(artifact)
            transcript_text = transcript.get("text", "")
            result = await provider.answer_text_question(transcript_text, args.question)
            return {
                "answer": result.get("answer", ""),
                "evidence": result.get("evidence", []),
                "intermediate_summary": result.get("intermediate_summary"),
            }

        return await _run_tool("media_qa", args.media_type, run)

    return mcp


async def _run_tool(
    tool_name: str,
    media_type: str,
    callback: Callable[[], Awaitable[dict[str, Any]]],
) -> str:
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    try:
        result = await callback()
        logger.info(
            "tool_complete request_id=%s tool=%s media_type=%s elapsed_ms=%.2f",
            request_id,
            tool_name,
            media_type,
            (time.perf_counter() - started) * 1000,
        )
        return json_payload(result)
    except ToolError as exc:
        logger.warning(
            "tool_error request_id=%s tool=%s media_type=%s code=%s elapsed_ms=%.2f",
            request_id,
            tool_name,
            media_type,
            exc.code,
            (time.perf_counter() - started) * 1000,
        )
        return error_payload(exc)
    except Exception as exc:
        logger.exception(
            "tool_exception request_id=%s tool=%s media_type=%s elapsed_ms=%.2f",
            request_id,
            tool_name,
            media_type,
            (time.perf_counter() - started) * 1000,
        )
        return error_payload(exc)

