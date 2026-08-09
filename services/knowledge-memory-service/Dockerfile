# syntax=docker/dockerfile:1.7
# Knowledge Memory Service — multi-stage Dockerfile
# 参考:
# - docs/spec/L3-file-specs/L3-memory-backend.md §11.4 (line 1689-1695)
# - helm/knowledge-memory-service/values.yaml (image.repository, image.tag)
# - pyproject.toml (uv workspace)
#
# Build context: monorepo root (必须包含 pyproject.toml + uv.lock + 5 workspace members)
#   docker build -f services/knowledge-memory-service/Dockerfile -t <tag> .
#
# 多阶段构建:
# - builder: ghcr.io/astral-sh/uv:python3.12-bookworm-slim + uv sync --no-dev
# - runtime: python:3.12-slim-bookworm + non-root user + readOnlyRootFilesystem 兼容

# ============================================================================
# Stage 1: Builder（uv sync 安装所有依赖 + workspace 内部包）
# ============================================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# uv 容器内 PATH（用户安装方式：python -m uv · Windows quirk 不影响容器）
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /build

# 先复制锁文件 + workspace 配置以最大化 Docker layer 缓存
COPY pyproject.toml uv.lock ./
COPY packages/a2a-core/pyproject.toml packages/a2a-core/pyproject.toml
COPY packages/adapter-sdk/pyproject.toml packages/adapter-sdk/pyproject.toml
COPY packages/operator/pyproject.toml packages/operator/pyproject.toml
COPY services/knowledge-memory-service/pyproject.toml services/knowledge-memory-service/pyproject.toml
COPY agents/hello/pyproject.toml agents/hello/pyproject.toml

# 安装所有依赖（包含工作区内部包）—— 不安装 dev group 减小镜像体积
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project --frozen

# 再复制项目源代码
COPY packages/a2a-core/src packages/a2a-core/src
COPY packages/adapter-sdk/src packages/adapter-sdk/src
COPY packages/operator/src packages/operator/src
COPY services/knowledge-memory-service/src services/knowledge-memory-service/src
COPY agents/hello/src agents/hello/src

# sync 项目本身（包含本服务的 console scripts / __main__.py）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen

# ============================================================================
# Stage 2: Runtime（最小化镜像 + non-root + restricted）
# ============================================================================
FROM python:3.12-slim-bookworm AS runtime

# 元数据
LABEL org.opencontainers.image.title="knowledge-memory-service" \
      org.opencontainers.image.description="superteam-a2a Knowledge-Memory Service (D 方案单进程合并, ADR-0006 v1.0 Accepted)" \
      org.opencontainers.image.source="https://github.com/superteam-cn/superteam-a2a" \
      org.opencontainers.image.licenses="Apache-2.0"

# 安全：禁用 pip cache + 升级关键包 + 创建 non-root user（UID 1000）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

# 仅安装 CA certificates + curl（健康检查备用）+ tini（PID 1 信号转发 · kopf 优雅关闭）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        tini && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --system --gid 1000 kms && \
    useradd --system --uid 1000 --gid kms --no-create-home --shell /sbin/nologin kms

# 从 builder 拷贝已安装的 venv
COPY --from=builder /opt/venv /opt/venv

# 复制运行时必需的源代码（read-only root fs 兼容）
COPY --from=builder /build/packages/a2a-core/src /app/packages/a2a-core/src
COPY --from=builder /build/packages/adapter-sdk/src /app/packages/adapter-sdk/src
COPY --from=builder /build/packages/operator/src /app/packages/operator/src
COPY --from=builder /build/services/knowledge-memory-service/src /app/services/knowledge-memory-service/src
COPY --from=builder /build/agents/hello/src /app/agents/hello/src

WORKDIR /app

# kopf 需要写入 in-memory state · 使用 emptyDir 兼容 readOnlyRootFilesystem
# (K8s deployment.yaml 中安全上下文 readOnlyRootFilesystem=true)
RUN mkdir -p /tmp/kopf && chown -R kms:kms /tmp/kopf

USER kms

# 单端口 8080（A2A + /healthz + /readyz + /metrics）· tls.enabled=true 时另开 8443
EXPOSE 8080

# 健康检查（容器内本地，K8s 仍用 deployment.yaml 的 livenessProbe/readinessProbe）
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/healthz', timeout=3).status == 200 else 1)"

# kopf operator 入口（D 方案单进程：MemoryReconciler 60s timer + on.create/on.update/on.delete）
# tini 作为 PID 1 转发信号 · kopf 收到 SIGTERM 优雅关闭
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "superteam_a2a.knowledge_memory.main"]