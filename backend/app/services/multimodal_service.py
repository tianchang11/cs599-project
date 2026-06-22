import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.pdf_service import MediaType, pdf_service

logger = logging.getLogger(__name__)


class MultimodalAnalysisService:
    def build_uploaded_context(
        self,
        file_id: str,
        api_key: str | None = None,
        provider: str | None = None,
    ) -> str:
        media_type = pdf_service.get_media_type(file_id)
        if not media_type:
            raise FileNotFoundError(f"File {file_id} not found")

        if media_type == "pdf":
            raw_text = pdf_service.extract_text(file_id)
            return f"\n\n[上传的PDF文档内容]:\n{raw_text[:4000]}"

        return ""

    async def build_uploaded_context_async(
        self,
        file_id: str,
        api_key: str | None = None,
        provider: str | None = None,
    ) -> str:
        media_type = pdf_service.get_media_type(file_id)
        if not media_type:
            raise FileNotFoundError(f"File {file_id} not found")

        if media_type == "pdf":
            return self.build_uploaded_context(file_id, api_key=api_key, provider=provider)

        path = pdf_service.get_path(file_id)
        if not path:
            raise FileNotFoundError(f"File {file_id} not found")

        mcp_api_key = self._resolve_openai_api_key(api_key=api_key, provider=provider)
        if not mcp_api_key:
            logger.warning("[MCP_Visual] OPENAI_API_KEY is not configured; skipping %s analysis", media_type)
            return ""

        try:
            if media_type == "image":
                payload = await self.analyze_image(path, mcp_api_key)
                return self._format_image_context(path, payload)
            if media_type == "audio":
                payload = await self.analyze_audio(path, mcp_api_key)
                return self._format_audio_context(path, payload)
        except Exception as exc:
            logger.warning("[MCP_Visual] Failed to analyze %s file %s: %s", media_type, file_id, exc)
            return ""

        return ""

    async def analyze_image(self, path: Path, api_key: str) -> dict[str, Any]:
        resolver, provider = self._create_mcp_components(api_key)
        source = self._media_source(path)
        artifact = await resolver.resolve(source, expected="image")
        prompt = (
            "Analyze this image for deep research. Return JSON with keys summary, objects, "
            "visible_text, safety_notes, and raw_answer. Focus on facts that could support a research report."
        )
        vision = await provider.analyze_image(artifact, prompt, "auto")
        ocr = await provider.analyze_image(
            artifact,
            "Perform OCR on this image. Return JSON with keys text, blocks, language_guess, and confidence_notes.",
            "high",
        )
        return {"vision_analyze": vision, "ocr_image": ocr}

    async def analyze_audio(self, path: Path, api_key: str) -> dict[str, Any]:
        resolver, provider = self._create_mcp_components(api_key)
        source = self._media_source(path)
        artifact = await resolver.resolve(source, expected="audio")
        transcript = await provider.transcribe_audio(artifact)
        transcript_text = transcript.get("text", "")
        summary = await provider.summarize_text(transcript_text, "research-oriented concise")
        return {"audio_transcribe": transcript, "audio_summarize": summary}

    async def run_visual_tool(
        self,
        tool_name: str,
        source: dict[str, str],
        api_key: str | None = None,
        provider: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        mcp_api_key = self._resolve_openai_api_key(api_key=api_key, provider=provider)
        if not mcp_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for MCP_Visual tools")

        resolver, mcp_provider = self._create_mcp_components(mcp_api_key)
        media_source = self._media_source_from_dict(source)

        if tool_name == "vision_analyze":
            artifact = await resolver.resolve(media_source, expected="image")
            prompt = kwargs.get("prompt") or (
                "Analyze this image. Return JSON with keys summary, objects, visible_text, safety_notes, and raw_answer."
            )
            detail = kwargs.get("detail", "auto")
            return await mcp_provider.analyze_image(artifact, prompt, detail)

        if tool_name == "ocr_image":
            artifact = await resolver.resolve(media_source, expected="image")
            languages = kwargs.get("languages") or []
            language_hint = f" Languages to prioritize: {', '.join(languages)}." if languages else ""
            return await mcp_provider.analyze_image(
                artifact,
                "Perform OCR on this image. Return JSON with keys text, blocks, "
                f"language_guess, and confidence_notes.{language_hint}",
                "high",
            )

        if tool_name == "audio_transcribe":
            artifact = await resolver.resolve(media_source, expected="audio")
            return await mcp_provider.transcribe_audio(
                artifact,
                language=kwargs.get("language"),
                timestamps=bool(kwargs.get("timestamps", False)),
                diarize=bool(kwargs.get("diarize", False)),
            )

        if tool_name == "audio_summarize":
            artifact = await resolver.resolve(media_source, expected="audio")
            transcript = await mcp_provider.transcribe_audio(artifact, language=kwargs.get("language"))
            summary = await mcp_provider.summarize_text(
                transcript.get("text", ""),
                kwargs.get("summary_style", "concise"),
                kwargs.get("language"),
            )
            return {"transcript": transcript.get("text", ""), **summary}

        if tool_name == "media_qa":
            media_type = kwargs.get("media_type")
            question = kwargs.get("question")
            if media_type not in {"image", "audio"}:
                raise ValueError("media_type must be 'image' or 'audio'")
            if not question:
                raise ValueError("question is required")
            artifact = await resolver.resolve(media_source, expected=media_type)
            if media_type == "image":
                return await mcp_provider.analyze_image(
                    artifact,
                    f"Answer this question about the image. Return JSON with keys answer and evidence.\n\n{question}",
                    "auto",
                )
            transcript = await mcp_provider.transcribe_audio(artifact)
            return await mcp_provider.answer_text_question(transcript.get("text", ""), question)

        raise ValueError(f"Unsupported MCP_Visual tool: {tool_name}")

    def _resolve_openai_api_key(self, api_key: str | None, provider: str | None) -> str:
        if settings.openai_api_key:
            return settings.openai_api_key
        if provider == "openai" and api_key:
            return api_key
        return ""

    def _create_mcp_components(self, api_key: str):  # type: ignore[no-untyped-def]
        from multimodal_mcp.config import Settings as MCPVisualSettings
        from multimodal_mcp.media import MediaResolver
        from multimodal_mcp.providers import OpenAIProvider

        mcp_settings = MCPVisualSettings(
            openai_api_key=api_key,
            http_token=None,
            allowed_dirs=settings.mcp_visual_allowed_dirs,
            max_file_mb=settings.mcp_visual_max_file_mb,
            max_download_mb=settings.mcp_visual_max_download_mb,
            request_timeout_seconds=settings.mcp_visual_request_timeout_seconds,
            openai_vision_model=settings.openai_vision_model,
            openai_summary_model=settings.openai_summary_model,
            openai_transcribe_model=settings.openai_transcribe_model,
            openai_diarize_model=settings.openai_diarize_model,
        )
        return MediaResolver(mcp_settings), OpenAIProvider(mcp_settings)

    def _media_source(self, path: Path):  # type: ignore[no-untyped-def]
        return self._media_source_from_dict({"type": "path", "value": str(path)})

    def _media_source_from_dict(self, source: dict[str, str]):  # type: ignore[no-untyped-def]
        from multimodal_mcp.media import MediaSource

        return MediaSource(**source)

    def _format_image_context(self, path: Path, payload: dict[str, Any]) -> str:
        vision = payload.get("vision_analyze", {})
        ocr = payload.get("ocr_image", {})
        return (
            f"\n\n[上传图片分析: {path.name}]\n"
            f"视觉摘要: {vision.get('summary') or vision.get('raw_answer') or json.dumps(vision, ensure_ascii=False)[:1200]}\n"
            f"识别对象: {json.dumps(vision.get('objects', []), ensure_ascii=False)}\n"
            f"可见文字: {ocr.get('text') or json.dumps(vision.get('visible_text', []), ensure_ascii=False)}\n"
            f"安全/置信说明: {json.dumps(vision.get('safety_notes') or ocr.get('confidence_notes', []), ensure_ascii=False)}"
        )

    def _format_audio_context(self, path: Path, payload: dict[str, Any]) -> str:
        transcript = payload.get("audio_transcribe", {})
        summary = payload.get("audio_summarize", {})
        transcript_text = transcript.get("text", "")
        return (
            f"\n\n[上传音频分析: {path.name}]\n"
            f"音频摘要: {summary.get('summary') or json.dumps(summary, ensure_ascii=False)[:1200]}\n"
            f"关键要点: {json.dumps(summary.get('key_points', []), ensure_ascii=False)}\n"
            f"转写文本: {transcript_text[:3000]}"
        )


multimodal_analysis_service = MultimodalAnalysisService()
