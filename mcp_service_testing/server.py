"""MCP server `current_time` with tools for local time, date, and timezone."""

from __future__ import annotations

import argparse
from datetime import datetime

from mcp.server.fastmcp import FastMCP


def _now() -> datetime:
    return datetime.now().astimezone()


def build_app(*, host: str, port: int) -> FastMCP:
    """Create the FastMCP application (server name `current_time`)."""
    mcp = FastMCP(
        "current_time",
        instructions="Test MCP server exposing current local time, date, and timezone.",
        host=host,
        port=port,
    )

    @mcp.tool()
    def get_current_time() -> str:
        """Return the current local time (HH:MM:SS, 24h)."""
        return _now().strftime("%H:%M:%S")

    @mcp.tool()
    def get_current_date() -> str:
        """Return the current local calendar date (ISO YYYY-MM-DD)."""
        return _now().strftime("%Y-%m-%d")

    @mcp.tool()
    def get_current_timezone() -> str:
        """Return the current local timezone name (e.g. Europe/Berlin or UTC offset)."""
        tz = _now().tzinfo
        if tz is None:
            return "unknown"
        name = getattr(tz, "key", None)
        if name:
            return str(name)
        return tz.tzname(_now()) or str(tz)

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the `current_time` MCP test server.")
    parser.add_argument(
        "--transport",
        choices=("sse", "streamable-http"),
        default="streamable-http",
        help="Remote transport: legacy SSE or streamable HTTP (recommended MCP HTTP transport).",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind address for HTTP/SSE.")
    parser.add_argument("--port", type=int, default=8000, help="Listen port.")
    parser.add_argument(
        "--mount-path",
        default=None,
        help="Optional URL prefix for SSE routes (passed to FastMCP.run).",
    )
    args = parser.parse_args()

    app = build_app(host=args.host, port=args.port)
    if args.transport == "sse":
        app.run(transport="sse", mount_path=args.mount_path)
    else:
        app.run(transport="streamable-http")


if __name__ == "__main__":
    main()
