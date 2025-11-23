# ===============================
# Stage 1 — Dependency installer
# ===============================
FROM python:3.13-slim AS uvbuilder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# ===============================
# Stage 2 — Final runtime image
# ===============================
FROM python:3.13-slim AS runtime
RUN useradd -m appuser
WORKDIR /app
COPY --from=uvbuilder /app/.venv ./.venv
COPY app ./app
COPY settings.py ./
COPY utils ./utils
RUN mkdir -p storage/datasets storage/models storage/macro_cache logs && \
    chown -R appuser:appuser storage logs

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
