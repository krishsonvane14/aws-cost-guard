# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 — Build
# Compiles TypeScript to JavaScript and prunes dev dependencies.
# ──────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy manifests first to maximise layer cache reuse.
COPY package.json package-lock.json tsconfig.json ./

# Install all dependencies (including devDependencies needed for tsc).
RUN npm ci

# Copy source and compile.
COPY src/ ./src/
RUN npm run build

# Produce a clean production-only node_modules.
RUN npm ci --omit=dev

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 — Production
# Minimal runtime image: only compiled output + production modules.
# ──────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS production

ENV NODE_ENV=production

WORKDIR /app

# Create a non-root user and group before copying any files.
RUN addgroup --system appgroup && \
    adduser  --system --ingroup appgroup --no-create-home appuser

# Copy only what the app needs to run.
COPY --from=builder /app/dist/         ./dist/
COPY --from=builder /app/node_modules/ ./node_modules/
COPY --from=builder /app/package.json  ./package.json

# Drop to the non-root user for all subsequent commands.
USER appuser

CMD ["node", "dist/index.js"]
