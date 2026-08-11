# syntax=docker/dockerfile:1.7
#
# Hello Agent Dockerfile · Phase 4 PR-2
# 依据 docs/phase4/pr2-hello-agent-helm-plan.md §2.1（multi-stage）+ L3-4 v0.2.0 §9（容器化契约）
#
# 5 项关键不变量（PR-1 验证 + PR-2 保持）：
# 1. Card-driven 单实例（replicaCount=1 · Helm values.schema.json enum 强约束）
# 2. Python-first 边界（base image = python:3.12-slim · 0 系统级依赖）
# 3. observability 4 指标（uvicorn 启动时自动加载 observability.py）
# 4. wire contract（Hello Agent 不涉及 MEMORY_* · 0 错误码定义）
# 5. 单进程 8080 端口（EXPOSE 8080 + uvicorn --port 8080 + --factory）

# ===== Stage 1: builder =====
# 隔离编译工具（uv + 完整 Python 工具链）· 镜像体积最小化
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install uv (Astral official image · multi-arch · zero install footprint)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy entire workspace for `uv sync --all-packages --all-extras`
# 注意：必须复制整个 workspace（packages/ + services/）因为 hello-agent 依赖
# workspace 内部包 superteam-a2a-a2a-core（PR-2 §5 风险 #7 缓解）
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY services/ ./services/

# Install runtime deps only (no dev · §13.6 依赖锁定)
# --frozen: 严格使用 uv.lock 不更新 · --no-dev: 排除 pytest/ruff/pyright 等开发依赖
# --all-packages: workspace 跨包依赖 · --all-extras: 含可选依赖
RUN uv sync --frozen --all-packages --all-extras --no-dev

# ===== Stage 2: runtime =====
# 仅含 .venv + 源码 + 必要 system libs · 不含 uv/builder 工具链
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:${PATH}"

# Create non-root user (UID 1000 · Pod Security Standards restricted profile)
RUN groupadd --system --gid 1000 hello && \
    useradd --system --uid 1000 --gid 1000 --no-create-home --shell /bin/false hello

WORKDIR /app

# Copy venv + workspace sources from builder
COPY --from=builder --chown=hello:hello /app/.venv /app/.venv
COPY --from=builder --chown=hello:hello /app/packages /app/packages
COPY --from=builder --chown=hello:hello /app/services /app/services

# 切换到 non-root user 执行后续命令（含 ENTRYPOINT）
USER hello:hello

# 单进程 8080 端口（关键不变量 #5 · 与 deployment.yaml containerPort 对齐）
EXPOSE 8080

# HEALTHCHECK: 引用 /healthz 路由（L3-4 §6 契约 + observability.py healthz 实现）
# --start-period=10s 等待 uvicorn 启动 + starlette 路由注册
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')"]

# ENTRYPOINT: exec form（避免 shell 形式 signal propagation 问题）
# --factory: 因为 create_app 是 factory function（agent.py line 81）
# --host 0.0.0.0: 容器内监听所有接口（K8s service 转发）
# --port 8080: 与 EXPOSE + deployment.yaml containerPort 严格对齐
ENTRYPOINT ["python", "-m", "uvicorn", "superteam_a2a.hello_agent.agent:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
