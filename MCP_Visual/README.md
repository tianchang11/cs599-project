# multimodal-mcp

A Python MCP server that gives text-only MCP clients multimodal tools for images and audio through OpenAI-backed providers.

## Features

- `vision_analyze`: image description, objects, visible text, and safety notes.
- `ocr_image`: OCR-focused image analysis.
- `audio_transcribe`: audio transcription with optional timestamps or diarization model selection.
- `audio_summarize`: transcription plus structured summary.
- `media_qa`: question answering over image or audio sources.

The first version accepts only local paths and URLs. Base64, multipart uploads, video, streaming audio, queues, and caching are intentionally out of scope.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Configuration

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:MCP_VISUAL_ALLOWED_DIRS = "D:\media,D:\HSource\MCP_Visual\examples"
$env:MCP_VISUAL_HTTP_TOKEN = "replace-with-a-long-random-token"
```

Optional defaults:

```powershell
$env:MCP_VISUAL_MAX_FILE_MB = "25"
$env:MCP_VISUAL_MAX_DOWNLOAD_MB = "25"
$env:MCP_VISUAL_REQUEST_TIMEOUT_SECONDS = "60"
$env:OPENAI_VISION_MODEL = "gpt-5.4-mini"
$env:OPENAI_SUMMARY_MODEL = "gpt-5.4-mini"
$env:OPENAI_TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"
$env:OPENAI_DIARIZE_MODEL = "gpt-4o-transcribe-diarize"
```

## Run

Local stdio:

```powershell
multimodal-mcp stdio
```

HTTP:

```powershell
multimodal-mcp http --host 127.0.0.1 --port 8765
```

Health check:

```powershell
curl http://127.0.0.1:8765/health
```

The MCP endpoint is mounted at:

```text
http://127.0.0.1:8765/mcp
```

HTTP MCP requests require:

```text
Authorization: Bearer <MCP_VISUAL_HTTP_TOKEN>
```

## MCP Client Examples

Claude Desktop or Cursor-style stdio configuration:

```json
{
  "mcpServers": {
    "multimodal-mcp": {
      "command": "multimodal-mcp",
      "args": ["stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "MCP_VISUAL_ALLOWED_DIRS": "D:/media"
      }
    }
  }
}
```

Codex-style stdio configuration:

```toml
[mcp_servers.multimodal-mcp]
command = "multimodal-mcp"
args = ["stdio"]

[mcp_servers.multimodal-mcp.env]
OPENAI_API_KEY = "sk-..."
MCP_VISUAL_ALLOWED_DIRS = "D:/media"
```

## Source Shape

All tools accept a source object:

```json
{
  "type": "path",
  "value": "D:/media/photo.jpg"
}
```

or:

```json
{
  "type": "url",
  "value": "https://example.com/audio.mp3"
}
```

Local paths must be inside `MCP_VISUAL_ALLOWED_DIRS`. URLs must be public `http` or `https` URLs and pass size and MIME checks.

## Tests

```powershell
pytest
```

