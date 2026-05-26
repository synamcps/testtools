"""MCP client that connects over SSE or streamable HTTP using `.env` configuration."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any

import anyio
from dotenv import load_dotenv

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client


def _load_headers() -> dict[str, str] | None:
    raw = os.environ.get("MCP_HTTP_HEADERS")
    if not raw:
        return None
    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"MCP_HTTP_HEADERS must be valid JSON object: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit("MCP_HTTP_HEADERS must be a JSON object of string keys to string values.")
    out: dict[str, str] = {}
    for key, value in parsed.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise SystemExit("MCP_HTTP_HEADERS keys and values must be strings.")
        out[key] = value
    return out


def _normalize_transport(raw: str) -> str:
    value = raw.strip().lower()
    aliases = {
        "http": "streamable-http",
        "streamable": "streamable-http",
        "streamable_http": "streamable-http",
        "streamable-http": "streamable-http",
        "sse": "sse",
    }
    if value not in aliases:
        allowed = ", ".join(sorted(set(aliases)))
        raise SystemExit(f"Unsupported MCP_TRANSPORT={raw!r}. Use one of: {allowed}.")
    return aliases[value]


async def _run_client(url: str, transport: str, terminate_on_close: bool) -> int:
    headers = _load_headers()

    print(f"Target URL: {url}")
    print(f"Transport: {transport}")

    if transport == "streamable-http":
        http_client = create_mcp_http_client(headers=headers)
        try:
            async with http_client:
                async with streamable_http_client(
                    url,
                    http_client=http_client,
                    terminate_on_close=terminate_on_close,
                ) as (read_stream, write_stream, _get_session_id):
                    return await _mcp_session(read_stream, write_stream)
        except Exception as exc:
            print(f"Connection: FAILED ({exc!r})")
            return 1

    # Legacy SSE transport
    try:
        async with sse_client(url, headers=headers) as (read_stream, write_stream):
            return await _mcp_session(read_stream, write_stream)
    except Exception as exc:
        print(f"Connection: FAILED ({exc!r})")
        return 1


async def _mcp_session(read_stream, write_stream) -> int:
    print("Connection: OPEN")
    try:
        async with ClientSession(read_stream, write_stream) as session:
            init = await session.initialize()
            server = init.serverInfo
            print("MCP initialize: OK")
            if server:
                print(f"Server implementation: {server.name} {server.version or ''}".strip())
            caps = session.get_server_capabilities()
            if caps and caps.tools:
                print(f"Server tools capability: listChanged={caps.tools.listChanged}")

            listed = await session.list_tools()
            tools = listed.tools
            print(f"Available tools ({len(tools)}):")
            for tool in tools:
                desc = (tool.description or "").strip().replace("\n", " ")
                suffix = f" — {desc}" if desc else ""
                print(f"  - {tool.name}{suffix}")
        print("Connection: CLOSED (clean)")
        return 0
    except Exception as exc:
        print(f"MCP session failed: {exc!r}")
        return 1


def main() -> None:
    logging.basicConfig(level=os.environ.get("MCP_CLIENT_LOG_LEVEL", "WARNING"))

    parser = argparse.ArgumentParser(
        description="Connect to a remote MCP server via SSE or streamable HTTP.",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Optional path to a .env file (defaults to python-dotenv discovery).",
    )
    args = parser.parse_args()

    if args.env_file:
        load_dotenv(args.env_file)
    else:
        load_dotenv()

    url = os.environ.get("MCP_SERVER_URL", "").strip()
    if not url:
        print(
            "Missing MCP_SERVER_URL. Set it in your environment or .env file "
            "(see .env.example).",
            file=sys.stderr,
        )
        raise SystemExit(2)

    transport_raw = os.environ.get("MCP_TRANSPORT", "http").strip()
    transport = _normalize_transport(transport_raw)

    terminate = os.environ.get("MCP_HTTP_TERMINATE_ON_CLOSE", "true").strip().lower() not in (
        "0",
        "false",
        "no",
    )

    exit_code = anyio.run(_run_client, url, transport, terminate)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
