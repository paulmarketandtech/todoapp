# Dockerfile

# ── Use the official uv image (Python 3.12, Debian slim) ──
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Don't buffer Python output, keeps logs real-time
ENV PYTHONUNBUFFERED=1

# uv settings for Docker
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# ── Install dependencies first (cached layer) ──
# Only copy what uv needs so this layer stays cached
# unless pyproject.toml / uv.lock actually change
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# ── Copy the rest of the application ──
COPY . .

# ── Install the project itself ──
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ── Create non-root user ──
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && mkdir -p /app/instance \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# ── Health check ──
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# ── Run with gunicorn (production WSGI server) ──
# 4 workers is a good default for a small app; tune to your server's CPU cores
CMD ["uv", "run", "gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
