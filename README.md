# MCP service testing tools

Python helpers for exercising the [Model Context Protocol](https://modelcontextprotocol.io/) over the network using the official `mcp` SDK.

## What is included

- **`current_time` MCP server** — three tools:
  - `get_current_time` — local time (`HH:MM:SS`)
  - `get_current_date` — local date (`YYYY-MM-DD`)
  - `get_current_timezone` — timezone name or offset
- **MCP test client** — reads configuration from a `.env` file, connects with either:
  - **Streamable HTTP** (`MCP_TRANSPORT=http` or `streamable-http`) — the current MCP HTTP transport
  - **Legacy SSE** (`MCP_TRANSPORT=sse`) — older remote transport still useful for compatibility tests

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run the HTTP (streamable) server

```bash
mcp-current-time-server --transport streamable-http --host 127.0.0.1 --port 8000
# MCP endpoint: http://127.0.0.1:8000/mcp
```

### Run the legacy SSE server

```bash
mcp-current-time-server --transport sse --host 127.0.0.1 --port 8001
# SSE endpoint: http://127.0.0.1:8001/sse
```

### Run the client

Copy `.env.example` to `.env` and adjust URLs, then:

```bash
mcp-test-client
# or
python -m mcp_service_testing.client --env-file /path/to/.env
```

The client prints connection status, initialization details, and the list of tools exposed by the server.

## Docker Compose

Build and start both transports (HTTP on `8000`, SSE on `8001`):

```bash
docker compose up --build
```

Run the bundled client against the HTTP server (Compose profile `client`):

```bash
docker compose --profile client up --build mcp-test-client
```

Inside the Compose network the client defaults to `http://current-time-http:8000/mcp`. Override by providing your own `.env` (not committed) and mounting it, for example:

```yaml
mcp-test-client:
  env_file: .env
```

## Environment variables

| Variable | Purpose |
| --- | --- |
| `MCP_SERVER_URL` | Full URL to the MCP endpoint (`/mcp` for streamable HTTP, `/sse` for legacy SSE with this server). |
| `MCP_TRANSPORT` | `http`, `streamable-http`, or `sse`. |
| `MCP_HTTP_HEADERS` | Optional JSON object of string HTTP headers. |
| `MCP_HTTP_TERMINATE_ON_CLOSE` | `true`/`false` — whether the HTTP client sends session teardown on exit. |
| `MCP_CLIENT_LOG_LEVEL` | Python logging level for SDK messages (default `WARNING`). |

## Notes

- **HTTP vs SSE**: In the MCP Python SDK, remote **HTTP** uses the **streamable HTTP** transport (`/mcp` in FastMCP). **SSE** is the older split-endpoint transport (`GET /sse` + `POST /messages/?session_id=...`).
- **DNS rebinding protection**: FastMCP enables extra checks for localhost binds. This project binds Docker services to `0.0.0.0`, which keeps those defaults relaxed; when you bind to `127.0.0.1` locally, keep the documented FastMCP behavior in mind.
