# KittenTTS Web Interface Dockerfile
# Hardened for smaller runtime image, safer execution, and faster rebuilds

FROM python:3.12-slim AS builder

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=1000 \
    PIP_RETRIES=5 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Build-only packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment used by final image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install gunicorn

# Install local kittentts package
COPY pyproject.toml setup.py MANIFEST.in README.md ./
COPY kittentts/ kittentts/
RUN pip install .


FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HOME=/app \
    XDG_CACHE_HOME=/app/.cache \
    HF_HOME=/app/.cache/huggingface \
    PATH="/opt/venv/bin:$PATH" \
    PORT=5000

# Runtime-only packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    libespeak-ng1 \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Non-root execution
RUN groupadd -r app && useradd -r -g app app

# Copy installed Python environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY app.py .
COPY entrypoint.sh .
COPY templates/ templates/
COPY static/ static/

# Create writable output directory with non-root ownership
RUN mkdir -p /app/generated_audio && \
    mkdir -p /app/.cache/huggingface && \
    chown -R app:app /app && \
    chmod +x /app/entrypoint.sh

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/').read()" || exit 1

USER app

ENTRYPOINT ["/usr/bin/tini", "--", "./entrypoint.sh"]
