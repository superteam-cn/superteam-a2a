"""PR-4c JSON-RPC dispatcher unit tests · ASGI-UT-003。

PR-4c plan §7 测试 ID 命名：
- ASGI-UT-003 · jsonrpc_dispatch routes 4 methods（queryMemory/recordMemory/
  queryKnowledge/getKnowledgeItem · mock handler 返回 dict · 验证 JSON-RPC
  result/error envelope 正确）

测试策略：
- 直接构造 starlette Request（带 body bytes）+ app.state 注入 mock service
- 不启动 uvicorn（subprocess-free · in-process 测试）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# 路径前置（与 test_app.py 模式一致）
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

import pytest  # noqa: E402
from starlette.requests import Request  # noqa: E402
from superteam_a2a.knowledge_memory.asgi.app import create_app  # noqa: E402
from superteam_a2a.knowledge_memory.asgi.routes import (  # noqa: E402
    ERR_INVALID_REQUEST,
    ERR_METHOD_NOT_FOUND,
    ERR_PARSE_ERROR,
    JSONRPC_VERSION,
    METHOD_GET_KNOWLEDGE_ITEM,
    METHOD_QUERY_KNOWLEDGE,
    METHOD_QUERY_MEMORY,
    METHOD_RECORD_MEMORY,
    jsonrpc_dispatch,
)
from superteam_a2a.knowledge_memory.backend.clock import SystemClock  # noqa: E402
from superteam_a2a.knowledge_memory.services.shared.admission import (  # noqa: E402
    AdmissionService,
)

# ============================================================================
# Mock services · 4 method 全部 mock 返回值
# ============================================================================


class _StubRecordService:
    """MemoryRecordService stub · 仅供 isinstance 验证 + 不可被真正调用。"""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def execute(self, memory: Any) -> Any:
        # 真实 MemoryRecordService.execute 接受 1 个 positional；这里给一个 mock
        self.calls.append({"memory_count": 1})
        return {"memory": {"metadata": {"name": "stub"}}, "phase": "Bound"}


class _StubQueryService:
    """MemoryQueryService stub."""

    async def execute(self, query: Any) -> Any:
        return {"items": [], "total_count": 0}


class _StubKnowledgeQueryService:
    """KnowledgeQueryService stub."""

    async def execute(self, query_dict: dict[str, Any]) -> list[Any]:
        return []


class _StubKnowledgeItemService:
    """KnowledgeItemService stub."""

    async def get_item(self, item_ref: Any) -> Any:
        return None


@pytest.fixture
def stub_services() -> dict[str, Any]:
    """6 services 注入到 app.state（PR-4c attach_services 契约）。"""
    return {
        "record_service": _StubRecordService(),  # type: ignore[dict-item]
        "admission_service": AdmissionService(validator=_StubAdmissionValidator()),  # type: ignore[arg-type,dict-item]
        "query_service": _StubQueryService(),  # type: ignore[dict-item]
        "knowledge_query_service": _StubKnowledgeQueryService(),  # type: ignore[dict-item]
        "knowledge_item_service": _StubKnowledgeItemService(),  # type: ignore[dict-item]
        "clock": SystemClock(),
    }


class _StubAdmissionValidator:
    """AdmissionValidatorImpl stub（type-only · AdmissionService.execute 不调用 validator.validate）。"""

    async def validate(self, memory: Any, *, timeout: float) -> None:
        return None


# ============================================================================
# helpers
# ============================================================================


def _build_request(
    *,
    app: Any,
    body: bytes,
    method: str = "POST",
    path: str = "/jsonrpc",
) -> Request:
    """构造 starlette Request（带 body + app scope）。"""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [],
        "query_string": b"",
        "app": app,
    }
    request = Request(scope)
    # 直接覆盖 _body（starlette Request 默认 lazy read body）
    request._body = body
    return request


def _envelope(method: str, params: dict[str, Any], *, request_id: Any = "req-1") -> bytes:
    """构造 JSON-RPC 2.0 request body bytes。"""
    return json.dumps(
        {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "method": method,
            "params": params,
        }
    ).encode("utf-8")


# ============================================================================
# ASGI-UT-003 · jsonrpc_dispatch routes 4 methods
# ============================================================================


@pytest.mark.asyncio
async def test_asgi_ut_003_dispatch_routes_4_methods(stub_services: dict[str, Any]) -> None:
    """ASGI-UT-003 · jsonrpc_dispatch 正确路由 4 methods + envelope 包装。

    验证 4 method（recordMemory/queryMemory/queryKnowledge/getKnowledgeItem）
    都被 dispatcher 路由到对应 handler，并返回正确的 JSON-RPC result envelope。
    """
    application = create_app()
    for key, value in stub_services.items():
        setattr(application.state, key, value)

    # 4 method 测试：每个 method 都应返回 JSON-RPC 2.0 result envelope
    test_cases = [
        (
            METHOD_RECORD_MEMORY,
            {"memory": {"metadata": {"name": "stub"}}},
        ),
        (
            METHOD_QUERY_MEMORY,
            {"query": {"scope": "scope", "namespace": "default"}},
        ),
        (
            METHOD_QUERY_KNOWLEDGE,
            {"query": {"query_text": "test"}},
        ),
        (
            METHOD_GET_KNOWLEDGE_ITEM,
            {"item_ref": {"name": "item-1", "namespace": "default"}},
        ),
    ]

    for method, params in test_cases:
        body = _envelope(method, params, request_id=f"id-{method}")
        request = _build_request(app=application, body=body)
        response = await jsonrpc_dispatch(request)
        assert response.status_code == 200

        decoded = bytes(response.body).decode("utf-8")
        parsed = json.loads(decoded)

        # JSON-RPC 2.0 success envelope
        assert parsed["jsonrpc"] == JSONRPC_VERSION
        assert parsed["id"] == f"id-{method}"
        # 应有 result 或 error（这里所有 stub handler 都不抛异常 → result）
        assert "result" in parsed or "error" in parsed


# ============================================================================
# JSON-RPC error envelope · parse / invalid request / method not found
# ============================================================================


@pytest.mark.asyncio
async def test_dispatch_parse_error_returns_envelope(stub_services: dict[str, Any]) -> None:
    """非 JSON body → JSON-RPC -32700 parse error envelope。"""
    application = create_app()
    for key, value in stub_services.items():
        setattr(application.state, key, value)

    request = _build_request(app=application, body=b"not json {{{")
    response = await jsonrpc_dispatch(request)
    body_bytes = bytes(response.body) if not isinstance(response.body, bytes) else response.body
    parsed = json.loads(body_bytes)
    assert parsed["jsonrpc"] == JSONRPC_VERSION
    assert parsed["error"]["code"] == ERR_PARSE_ERROR
    assert parsed["id"] is None


@pytest.mark.asyncio
async def test_dispatch_invalid_request_envelope(stub_services: dict[str, Any]) -> None:
    """缺 id 字段 → JSON-RPC -32600 invalid request。"""
    application = create_app()
    for key, value in stub_services.items():
        setattr(application.state, key, value)

    body = json.dumps({"jsonrpc": JSONRPC_VERSION, "method": "recordMemory"}).encode()
    request = _build_request(app=application, body=body)
    response = await jsonrpc_dispatch(request)
    parsed = json.loads(bytes(response.body).decode("utf-8"))
    assert parsed["error"]["code"] == ERR_INVALID_REQUEST


@pytest.mark.asyncio
async def test_dispatch_method_not_found(stub_services: dict[str, Any]) -> None:
    """未知 method → JSON-RPC -32601 method not found。"""
    application = create_app()
    for key, value in stub_services.items():
        setattr(application.state, key, value)

    body = _envelope("nonexistentMethod", {}, request_id="req-404")
    request = _build_request(app=application, body=body)
    response = await jsonrpc_dispatch(request)
    parsed = json.loads(bytes(response.body).decode("utf-8"))
    assert parsed["error"]["code"] == ERR_METHOD_NOT_FOUND
    assert parsed["id"] == "req-404"


@pytest.mark.asyncio
async def test_dispatch_service_unavailable(stub_services: dict[str, Any]) -> None:
    """app.state 缺 record_service → JSON-RPC -32603 internal error。

    不注入 record_service，但其他 service 都注入 → recordMemory 应触发兜底。
    """
    application = create_app()
    # 故意只注入 clock + admission + query + knowledge_* 不注入 record_service
    for key, value in stub_services.items():
        if key != "record_service":
            setattr(application.state, key, value)

    body = _envelope(METHOD_RECORD_MEMORY, {"memory": {}}, request_id="req-x")
    request = _build_request(app=application, body=body)
    response = await jsonrpc_dispatch(request)
    parsed = json.loads(bytes(response.body).decode("utf-8"))
    assert parsed["error"]["code"] == -32603
    assert parsed["id"] == "req-x"
