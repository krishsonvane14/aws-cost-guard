# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 — Build
# Installs dependencies into a virtual-env so only the venv is copied forward.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-alpine AS builder

WORKDIR /app

# Install build-time OS deps if any compiled wheels are needed.
RUN apk add --no-cache gcc musl-dev

# Create a virtual environment and install Python deps.
COPY requirements.txt ./
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy source.
COPY src/ ./src/

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 — Production
# Minimal runtime image: only the venv + source, no compiler toolchain.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-alpine AS production

WORKDIR /app

# Create a non-root user and group before copying any files.
RUN addgroup --system appgroup && \
    adduser  --system --ingroup appgroup --no-create-home appuser

# Copy the pre-built virtual environment and source from the builder.
COPY --from=builder /app/.venv/ ./.venv/
COPY --from=builder /app/src/   ./src/

# Make sure the venv Python is on PATH.
ENV PATH="/app/.venv/bin:$PATH"

# Drop to the non-root user for all subsequent commands.
USER appuser

CMD ["python", "-m", "src.main"]
