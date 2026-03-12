# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 — builder
# Install runtime dependencies into a --prefix so they can be copied cleanly.
# Uses slim (Debian) for broad wheel compatibility during pip install.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /tmp/requirements.txt

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 — final
# Minimal Alpine runtime: no pip, setuptools, wheel, or build toolchain.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-alpine AS final

LABEL org.opencontainers.image.source="https://github.com/krishkumar/aws-cost-guard"
LABEL org.opencontainers.image.description="Zero-infrastructure AWS spend monitor with anomaly detection"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy installed packages from builder into the system site-packages.
COPY --from=builder /install /usr/local

# Copy only the application source.
COPY src/ /app/src/

# Create non-root user and switch to it.
RUN adduser -D -u 1001 appuser
USER appuser

ENTRYPOINT ["python", "-m", "src.main"]
