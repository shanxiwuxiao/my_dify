# syntax=docker/dockerfile:1

FROM node:22-slim AS frontend
WORKDIR /app/web
RUN corepack enable
COPY web/package.json web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY web/ ./
RUN pnpm build

FROM python:3.10-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/api

RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY api/ ./api/
COPY migrations/ ./migrations/
COPY --from=frontend /app/web/dist ./web/dist/

EXPOSE 10000
CMD ["sh", "-c", "flask --app my_dify:create_app db upgrade && gunicorn 'my_dify:create_app()' --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 --timeout 120"]
