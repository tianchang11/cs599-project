from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolError(Exception):
    code: str
    message: str
    details: dict[str, Any] | None = None


def error_payload(error: ToolError | Exception) -> str:
    if isinstance(error, ToolError):
        body: dict[str, Any] = {
            "error": {
                "code": error.code,
                "message": error.message,
            }
        }
        if error.details:
            body["error"]["details"] = error.details
    else:
        body = {
            "error": {
                "code": "internal_error",
                "message": "Unexpected server error.",
            }
        }
    return json.dumps(body, ensure_ascii=False)


def json_payload(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)

