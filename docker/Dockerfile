# Reusable image for the MCP `current_time` server and the HTTP/SSE test client.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mcp_service_testing ./mcp_service_testing

RUN pip install --no-cache-dir .

# Override CMD per service in docker-compose.yml
CMD ["python", "-m", "mcp_service_testing.server", "--help"]
