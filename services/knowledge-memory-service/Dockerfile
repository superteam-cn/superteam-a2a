# syntax=docker/dockerfile:1.7
#
# Knowledge Memory Service Dockerfile · Phase 4 PR-5
# 依据 docs/phase4/pr5-knowledge-service-step3-plan.md §2.5
#
# 5 项关键不变量（PR-5 验证）：
# 1. Card-driven 单实例（replicaCount=1 · Helm values.schema.json enum 强约束）
# 2. Python-first 边界（base image = python:3.12-slim · 0 系统级依赖）
# 3. SOLID §17 + wire contract 23 错误码（PR-4a/b/c 实装）
# 4. ASGI server（PR-4c 实装 · starlette 1.4.1 + uvicorn --factory）
# 5. single-process 8080 + 8443 端口（port 8080 A2A + /healthz + /readyz + /metrics · 8443 mTLS tls.enabled）

# ===== Stage 1: builder =====
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install uv (Astral official image · multi-arch · zero install footprint)
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy entire workspace for `uv sync --all-packages --all-extras`
# 注意：必须复制整个 workspace（packages/ + services/）因为 knowledge-memory-service 依赖
# workspace 内部包 superteam_a2a.knowledge_memory（PR-4c ASGI + handlers）
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY services/knowledge-memory-service/ ./services/knowledge-memory-service/

# Install runtime deps only (no dev · §13.6 依赖锁定)
RUN uv sync --frozen --all-packages --all-extras --no-dev

# ===== Stage 2: runtime =====
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install curl for HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user (UID 1000 · matches podSecurityContext runAsUser)
RUN useradd --create-home --shell /bin/bash --uid 1000 kmm

# Copy .venv from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/packages /app/packages
COPY --from=builder /app/services /app/services

# Set PATH to use .venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Switch to non-root user
USER 1000

# Expose ports (8080 A2A HTTP JSON-RPC + 8443 mTLS when tls.enabled)
EXPOSE 8080 8443

# Health check (matches deployment.yaml livenessProbe/readinessProbe)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/healthz || exit 1

# Run uvicorn with ASGI factory (PR-4c 实装 · superteam_a2a.knowledge_memory.asgi.app:app)
CMD ["uvicorn", \
     "superteam_a2a.knowledge_memory.asgi.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--factory"]
