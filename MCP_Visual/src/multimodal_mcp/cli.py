from __future__ import annotations

import argparse
import logging

import uvicorn

from multimodal_mcp.config import load_settings
from multimodal_mcp.http_app import create_app
from multimodal_mcp.server import create_mcp


def main() -> None:
    parser = argparse.ArgumentParser(prog="multimodal-mcp")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("stdio", help="Run as a local stdio MCP server.")

    http_parser = subparsers.add_parser("http", help="Run as a Streamable HTTP MCP server.")
    http_parser.add_argument("--host", default="127.0.0.1")
    http_parser.add_argument("--port", default=8765, type=int)

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    settings = load_settings()
    if args.command == "stdio":
        create_mcp(settings).run()
        return

    if args.command == "http":
        uvicorn.run(create_app(settings), host=args.host, port=args.port, log_level=args.log_level)
        return

    parser.error(f"Unsupported command: {args.command}")

