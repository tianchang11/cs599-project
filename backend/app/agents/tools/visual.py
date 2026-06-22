import logging
from typing import Any

from app.agents.tools.base import BaseTool, ToolResult
from app.agents.tools.registry import register_tool
from app.services.multimodal_service import multimodal_analysis_service

logger = logging.getLogger(__name__)


class MCPVisualTool(BaseTool):
    mcp_tool_name: str = ""

    async def execute(self, **kwargs: Any) -> ToolResult:
        source = kwargs.pop("source", None)
        if not source:
            return ToolResult(success=False, error="source is required")

        try:
            data = await multimodal_analysis_service.run_visual_tool(
                self.mcp_tool_name,
                source=source,
                **kwargs,
            )
            return ToolResult(success=True, data=data)
        except Exception as exc:
            logger.warning("[MCP_Visual] Tool %s failed: %s", self.mcp_tool_name, exc)
            return ToolResult(success=False, error=str(exc))

    def _source_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["path", "url"],
                    "description": "Media source type. Local paths must be under MCP_VISUAL_ALLOWED_DIRS.",
                },
                "value": {"type": "string", "description": "Local file path or public media URL."},
            },
            "required": ["type", "value"],
        }


@register_tool("vision_analyze")
class VisionAnalyzeTool(MCPVisualTool):
    name = "vision_analyze"
    mcp_tool_name = "vision_analyze"
    description = "Analyze an image and return summary, objects, visible text, safety notes, and raw answer."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "source": self._source_schema(),
                "prompt": {"type": "string", "description": "Optional analysis prompt."},
                "detail": {"type": "string", "enum": ["low", "high", "auto"], "default": "auto"},
            },
            "required": ["source"],
        }


@register_tool("ocr_image")
class OcrImageTool(MCPVisualTool):
    name = "ocr_image"
    mcp_tool_name = "ocr_image"
    description = "Extract visible text from an image."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "source": self._source_schema(),
                "languages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional language hints for OCR.",
                },
            },
            "required": ["source"],
        }


@register_tool("audio_transcribe")
class AudioTranscribeTool(MCPVisualTool):
    name = "audio_transcribe"
    mcp_tool_name = "audio_transcribe"
    description = "Transcribe an audio file, optionally with timestamps or diarization."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "source": self._source_schema(),
                "language": {"type": "string", "description": "Optional language code."},
                "timestamps": {"type": "boolean", "default": False},
                "diarize": {"type": "boolean", "default": False},
            },
            "required": ["source"],
        }


@register_tool("audio_summarize")
class AudioSummarizeTool(MCPVisualTool):
    name = "audio_summarize"
    mcp_tool_name = "audio_summarize"
    description = "Transcribe and summarize an audio file."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "source": self._source_schema(),
                "summary_style": {"type": "string", "default": "concise"},
                "language": {"type": "string", "description": "Optional language code."},
            },
            "required": ["source"],
        }


@register_tool("media_qa")
class MediaQaTool(MCPVisualTool):
    name = "media_qa"
    mcp_tool_name = "media_qa"
    description = "Answer a question about an image or audio file."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "source": self._source_schema(),
                "media_type": {"type": "string", "enum": ["image", "audio"]},
                "question": {"type": "string", "description": "Question to answer from the media."},
            },
            "required": ["source", "media_type", "question"],
        }
