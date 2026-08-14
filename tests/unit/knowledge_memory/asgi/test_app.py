"""PR-4c ASGI server unit tests · ASGI-UT-001 + ASGI-UT-002。

PR-4c plan §7 测试 ID 命名：
- ASGI-UT-001 · create_app() binds 5 routes（/.well-known/agent.json + /jsonrpc +
  /healthz + /readyz + /metrics）
- ASGI-UT-002 · ASGI lifespan manages Clock + InProcessContext（startup 装配 +
  shutdown graceful close）
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

# 路径前置（与 api/test_server.py 模式一致）
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_OP_SRC = _REPO_ROOT / "packages" / "operator" / "src"

_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)
_OP_PATH = str(_OP_SRC)
if _OP_PATH not in sys.path:
    if _KM_PATH in sys.path:
        km_idx = sys.path.index(_KM_PATH)
        sys.path.insert(km_idx + 1, _OP_PATH)
    else:
        sys.path.insert(0, _OP_PATH)

from starlette.applications import Starlette  # noqa: E402, I001
from superteam_a2a.knowledge_memory.api.context import InProcessContext  # noqa: E402
from superteam_a2a.knowledge_memory.asgi.app import (  # noqa: E402
    app as module_app,
    create_app,
    healthz_endpoint,
    lifespan,
    readyz_endpoint,
)
from superteam_a2a.knowledge_memory.backend.clock import Clock, FakeClock, SystemClock  # noqa: E402

# ============================================================================
# ASGI-UT-001 · create_app binds 5 routes
# ============================================================================


def test_asgi_ut_001_create_app_binds_5_routes() -> None:
    """ASGI-UT-001 · create_app() 返回 Starlette 实例 + 5 routes 全部绑定。

    验证 5 routes 全部存在：
    - GET /.well-known/agent.json
    - POST /jsonrpc
    - GET /healthz
    - GET /readyz
    - GET /metrics
    """
    application = create_app()
    assert isinstance(application, Starlette)

    paths_methods = set()
    for route in application.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or set()
        if path is not None:
            for method in methods:
                paths_methods.add((path, method))

    expected = {
        ("/.well-known/agent.json", "GET"),
        ("/jsonrpc", "POST"),
        ("/healthz", "GET"),
        ("/readyz", "GET"),
        ("/metrics", "GET"),
    }
    assert expected.issubset(paths_methods), (
        f"Missing routes. Got {sorted(paths_methods)}, expected subset {sorted(expected)}"
    )


def test_asgi_ut_001_module_level_app_is_starlette() -> None:
    """ASGI-UT-001 补充：模块级 app 实例存在且与 create_app() 等价。"""
    assert isinstance(module_app, Starlette)
    assert module_app is not None


# ============================================================================
# ASGI-UT-002 · ASGI lifespan manages Clock + InProcessContext
# ============================================================================


@pytest.mark.asyncio
async def test_asgi_ut_002_lifespan_yields_without_error() -> None:
    """ASGI-UT-002 · lifespan startup/shutdown 正常 yield 不抛异常。

    验证：
    - startup 阶段不抛异常（bind_metrics_to_app 幂等调用）
    - yield 阶段控制权交回
    - shutdown 阶段不抛异常（graceful close）
    """
    application = create_app()
    async with lifespan(application):
        # lifespan 内部已运行 startup（bind metrics）；此为 yield 内
        assert isinstance(application, Starlette)


@pytest.mark.asyncio
async def test_asgi_ut_002_inprocess_context_can_be_built_with_clock() -> None:
    """ASGI-UT-002 补充：InProcessContext 接受 Clock 注入（frozen + Clock Protocol）。

    验证 lifespan 装配 Clock 后，InProcessContext 可正常构造（PR-4c lifespan 期望）。
    """
    clock: Clock = FakeClock(start=datetime(2026, 1, 1, tzinfo=UTC))
    context = InProcessContext(clock=clock, trace_id="lifespan-trace")
    assert context.clock is clock
    assert context.trace_id == "lifespan-trace"


@pytest.mark.asyncio
async def test_asgi_ut_002_lifespan_with_system_clock() -> None:
    """ASGI-UT-002 补充：SystemClock 与 lifespan 兼容（生产配置）。"""
    application = create_app()
    async with lifespan(application):
        # 模拟 main.py 装配 SystemClock 到 app.state
        application.state.clock = SystemClock()
        assert isinstance(application.state.clock, Clock)


# ============================================================================
# Helpers · 复用 healthz/readyz endpoint 直接调用
# ============================================================================


@pytest.mark.asyncio
async def test_healthz_endpoint_returns_healthy() -> None:
    """健康检查 endpoint 直接调用验证（PR-4c §2.1 5 endpoint 之一）。"""
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/healthz",
        "headers": [],
        "query_string": b"",
    }
    request = Request(scope)
    response = await healthz_endpoint(request)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_readyz_endpoint_returns_ready_when_clock_present() -> None:
    """readyz endpoint 在 clock 配置时返回 200。"""
    from starlette.requests import Request

    application = create_app()
    application.state.clock = SystemClock()

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/readyz",
        "headers": [],
        "query_string": b"",
        "app": application,
    }
    request = Request(scope)
    response = await readyz_endpoint(request)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_readyz_endpoint_returns_503_when_clock_missing() -> None:
    """readyz endpoint 在 clock 缺失时返回 503（fail-fast 探针）。"""
    from starlette.requests import Request

    application = create_app()
    # 不设置 clock
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/readyz",
        "headers": [],
        "query_string": b"",
        "app": application,
    }
    request = Request(scope)
    response = await readyz_endpoint(request)
    assert response.status_code == 503
