from __future__ import annotations

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from multimodal_mcp.config import Settings, load_settings
from multimodal_mcp.server import create_mcp


class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str | None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path == "/health":
            return await call_next(request)
        if not self._token:
            return JSONResponse({"error": {"code": "auth_required", "message": "HTTP token is not configured."}}, 401)
        expected = f"Bearer {self._token}"
        if request.headers.get("authorization") != expected:
            return JSONResponse({"error": {"code": "auth_required", "message": "Invalid or missing bearer token."}}, 401)
        return await call_next(request)


async def health(_: Request) -> Response:
    return JSONResponse({"status": "ok", "service": "multimodal-mcp"})


def create_app(settings: Settings | None = None) -> Starlette:
    settings = settings or load_settings()
    mcp = create_mcp(settings)
    app = Starlette(routes=[Route("/health", health), Mount("/", app=mcp.streamable_http_app())])
    app.add_middleware(BearerAuthMiddleware, token=settings.http_token)
    return app
