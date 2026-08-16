"""ASGI Application · starlette + uvicorn + 5 endpoint + 4 JSON-RPC handler binding。

PR-4c plan §2.1 · 单进程 D 方案（uvicorn worker=1 · 与 ADR-0006 D 方案一致）。

5 endpoint 暴露（A2A spec + kopf 探针 + Prometheus）：
- GET  /.well-known/agent.json · Agent Card discovery (A2A spec §5.1)
- POST /jsonrpc                · JSON-RPC 2.0 dispatcher (4 methods)
- GET  /healthz                · kopf liveness
- GET  /readyz                 · kopf readiness
- GET  /metrics                · Prometheus metrics

不变量（PR-4c §6）：
- 4 handler 全部通过 starlette Route 绑定（PR-4b 复用）
- lifespan 管理 observability + backend 资源（startup/shutdown 优雅管理）
- ASGI 单进程（uvicorn worker=1 · 与 D 方案一致）
- Clock 与 L3-6 §M-1.5 三方共享单实例同源（memo["clock"]）

宪法 §17 SOLID：
- SRP：create_app 只做 Starlette 装配 + Route 绑定
- OCP：通过 app.state 注入扩展（不修改 PR-4b handler）
- LSP：JSON-RPC envelope 结构稳定
- DIP：依赖 starlette Request + PR-4b handler Protocol
- ISP：create_app 接口最小化（无强制参数 · app.state 注入）
- CRP：构造注入 handler（组合而非继承）
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from superteam_a2a.knowledge_memory.asgi.card import agent_card_endpoint
from superteam_a2a.knowledge_memory.asgi.routes import jsonrpc_dispatch
from superteam_a2a.knowledge_memory.observability import bind_metrics_to_app

# ============================================================================
# Health endpoints（PR-4.1.1 #90 共用 · kopf liveness/readiness 替代）
# ============================================================================


async def healthz_endpoint(request: Request) -> Response:
    """GET /healthz · kopf liveness_endpoint 替代（PR-4.1.1 #90 共用）。

    返回 200 + {"status": "healthy"} · Phase 2 e2e-envtest.yml 探针期望。
    """
    return JSONResponse({"status": "healthy"})


async def readyz_endpoint(request: Request) -> Response:
    """GET /readyz · kopf readiness_endpoint 替代（PR-4.1.1 #90 共用）。

    返回 200 + {"status": "ready"} · Phase 2 e2e-envtest.yml 探针期望。
    与 healthz 的区别：readyz 显式检查 service 是否装配（app.state 有 clock 即视为 ready）。
    """
    clock = getattr(request.app.state, "clock", None)
    if clock is None:
        return JSONResponse(
            {"status": "not_ready", "reason": "clock not configured"},
            status_code=503,
        )
    return JSONResponse({"status": "ready"})


# ============================================================================
# lifespan · startup/shutdown 优雅管理（observability + backend 资源）
# ============================================================================


@asynccontextmanager
async def lifespan(app: Starlette):
    """ASGI lifespan · observability binding + backend 资源生命周期。

    Startup：
    - bind Prometheus /metrics（PR-4.3 25 指标已绑定 · Phase 4 PR-3 已实装）

    Shutdown：
    - graceful close：starlette 不持有 backend 资源（PR-4a/b InMemoryBackend 无 close）
    - 扩展点：PR-5 K8sBackend 接入后可在此显式 close

    Yield：
    - 控制权交回 starlette · server 进入正常 request 处理
    """
    # Startup: bind_metrics_to_app 幂等（多次调用安全）· 与 main.py 装配一致
    bind_metrics_to_app(app)
    try:
        yield
    finally:
        # Shutdown: 预留扩展点（PR-5 K8sBackend close 接入）
        pass


# ============================================================================
# create_app · Starlette Application 工厂
# ============================================================================


def create_app() -> Starlette:
    """Create ASGI application · 4 JSON-RPC method + Agent Card endpoint + healthz/readyz/metrics。

    Returns:
        Starlette instance with 5 routes bound + lifespan configured.

    app.state 注入契约（PR-4b 业务逻辑层 · 由 main.py / tests 装配）：
    - record_service · MemoryRecordService（必需 · recordMemory）
    - admission_service · AdmissionService（必需 · recordMemory 含 admission 50ms）
    - query_service · MemoryQueryService（必需 · queryMemory）
    - knowledge_query_service · KnowledgeQueryService（必需 · queryKnowledge）
    - knowledge_item_service · KnowledgeItemService（必需 · getKnowledgeItem）
    - clock · Clock（必需 · InProcessContext 注入）

    不变量：
    - 5 routes 全部绑定（/.well-known/agent.json + /jsonrpc + /healthz + /readyz + /metrics）
    - /metrics 通过 bind_metrics_to_app 在 lifespan startup 绑定（幂等）
    - 单进程架构（uvicorn worker=1 · 与 ADR-0006 D 方案一致）
    """
    app = Starlette(
        debug=False,
        lifespan=lifespan,
        routes=[
            Route(
                "/.well-known/agent.json",
                agent_card_endpoint,
                methods=["GET"],
            ),
            Route("/jsonrpc", jsonrpc_dispatch, methods=["POST"]),
            Route("/healthz", healthz_endpoint, methods=["GET"]),
            Route("/readyz", readyz_endpoint, methods=["GET"]),
        ],
    )
    # 立即绑定 /metrics（lifespan startup 也会再调一次 · 幂等）
    bind_metrics_to_app(app)
    return app


# uvicorn entrypoint: uvicorn superteam_a2a.knowledge_memory.asgi.app:app
# 模块级 app 实例（PR-5 Helm main.py 可直接复用或重新 create_app）
app: Starlette = create_app()


# ============================================================================
# 工厂函数（测试装配入口 · app.state 注入）
# ============================================================================


def attach_services(app: Starlette, **services: Any) -> Starlette:
    """app.state 注入 6 service（PR-4b + Clock）。

    Args:
        app: starlette instance from create_app()
        **services: 关键字参数 · 必须包含以下 key：
            - record_service · MemoryRecordService
            - admission_service · AdmissionService
            - query_service · MemoryQueryService
            - knowledge_query_service · KnowledgeQueryService
            - knowledge_item_service · KnowledgeItemService
            - clock · Clock

    Returns:
        同一 app 实例（链式调用友好）

    Raises:
        ValueError: 缺少必需 key（fail-fast · 防止启动后才发现配置缺失）
    """
    required = frozenset(
        {
            "record_service",
            "admission_service",
            "query_service",
            "knowledge_query_service",
            "knowledge_item_service",
            "clock",
        }
    )
    missing = required - services.keys()
    if missing:
        raise ValueError(f"attach_services missing required keys: {sorted(missing)}")
    for key, value in services.items():
        setattr(app.state, key, value)
    return app


__all__ = [
    "app",
    "attach_services",
    "create_app",
    "healthz_endpoint",
    "lifespan",
    "readyz_endpoint",
]
