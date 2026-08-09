"""L4-Phase3 PR-1 A2A HTTP JSON-RPC server 测试 · TEST-A2A-001~012（12 个）。

依据 docs/phase3/l4-phase3-plan.md §3 PR-1 + L3-6 §6 in-process handler 契约：
- 4 envelope 验证（TEST-A2A-001~004）：jsonrpc version / id 必填 / params 类型 / parse error
- 4 round-trip（TEST-A2A-005~008）：record happy / query happy / record→query / empty query
- 4 error 传播（TEST-A2A-009~012）：wire 12 错误码 1:1 映射 + ValidationError → -32602
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

# ============================================================================
# 路径前置（与 api/conftest.py 一致）
# ============================================================================

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

from superteam_a2a.knowledge_memory import (  # noqa: E402
    InMemoryBackend,
    MemoryBackendError,
    MemoryBackendInProcessServiceImpl,
    MemoryErrorCode,
    SystemClock,
)
from superteam_a2a.knowledge_memory.api.server import (  # noqa: E402
    ERR_INVALID_PARAMS,
    ERR_INVALID_REQUEST,
    ERR_PARSE_ERROR,
    JSONRPC_VERSION,
    create_app,
)
from superteam_a2a.operator.models.memory import (  # noqa: E402
    MemoryVisibility,
)

# ============================================================================
# Fixtures
# ============================================================================


def _make_memory_payload(
    *,
    name: str = "mem-1",
    namespace: str = "default",
    summary: str = "Test memory",
    confidence: float = 1.0,
    decay_days: int = 30,
) -> dict:
    """构造 K8s wire format dict（camelCase keys）。"""
    return {
        "apiVersion": "memory.superteam-a2a.io/v1alpha1",
        "kind": "Memory",
        "metadata": {"name": name, "namespace": namespace},
        "spec": {
            "scopeRef": {"name": "industry-ai"},
            "agentRef": {"kind": "ServiceAccount", "name": "hello-agent-sa"},
            "content": {"k": "v"},
            "summary": summary,
            "confidence": confidence,
            "decayDays": decay_days,
            "visibility": MemoryVisibility.SCOPE_AND_CHILDREN.value,
        },
    }


@pytest.fixture
def fake_clock():
    """测试用 Clock（SystemClock 单例 · 与 backend 默认兼容）。"""
    return SystemClock()


@pytest.fixture
def make_service(fake_clock):
    """构造 MemoryBackendInProcessServiceImpl + 后端 InMemoryBackend。"""

    def _factory():
        backend = InMemoryBackend(clock=fake_clock)
        return MemoryBackendInProcessServiceImpl(backend=backend)

    return _factory


@pytest.fixture
def client(make_service):
    """starlette TestClient · service + clock 注入 app.state。"""
    service = make_service()
    app = create_app(service=service, clock=SystemClock())
    return TestClient(app)


# ============================================================================
# TEST-A2A-001~004 · Envelope 验证
# ============================================================================


def test_a2a_001_envelope_missing_id_returns_invalid_request(client):
    """TEST-A2A-001 · envelope 缺 id 字段 → JSON-RPC -32600 invalid request。"""
    resp = client.post(
        "/jsonrpc/record_memory",
        json={"jsonrpc": JSONRPC_VERSION, "params": _make_memory_payload()},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["jsonrpc"] == JSONRPC_VERSION
    assert body["id"] is None  # spec: missing id → null in response
    assert body["error"]["code"] == ERR_INVALID_REQUEST


def test_a2a_002_envelope_wrong_jsonrpc_version_returns_invalid_request(client):
    """TEST-A2A-002 · jsonrpc != "2.0" → JSON-RPC -32600 invalid request。"""
    resp = client.post(
        "/jsonrpc/record_memory",
        json={"jsonrpc": "1.0", "id": 1, "params": _make_memory_payload()},
    )
    body = resp.json()
    assert body["error"]["code"] == ERR_INVALID_REQUEST
    assert "2.0" in body["error"]["message"]


def test_a2a_003_envelope_parse_error_returns_parse_error_code(client):
    """TEST-A2A-003 · 非 JSON body → JSON-RPC -32700 parse error。"""
    resp = client.post(
        "/jsonrpc/record_memory",
        content=b"not a json object",
        headers={"content-type": "application/json"},
    )
    body = resp.json()
    assert body["error"]["code"] == ERR_PARSE_ERROR
    assert body["id"] is None


def test_a2a_004_envelope_params_not_object_returns_invalid_params(client):
    """TEST-A2A-004 · params 不是 object → JSON-RPC -32602 invalid params。"""
    resp = client.post(
        "/jsonrpc/record_memory",
        json={"jsonrpc": JSONRPC_VERSION, "id": 1, "params": "not an object"},
    )
    body = resp.json()
    assert body["error"]["code"] == ERR_INVALID_PARAMS
    assert body["id"] == 1


# ============================================================================
# TEST-A2A-005~008 · Round-trip（业务 happy path）
# ============================================================================


def test_a2a_005_record_memory_happy_path_returns_result(client):
    """TEST-A2A-005 · record_memory 成功路径：返回 MemoryRecordResult + resource_version=1。

    注意：MemoryRecordResult 字段无 alias（Python snake_case wire）；
    Memory 字段有 alias（K8s camelCase wire）。
    """
    payload = _make_memory_payload(name="happy-005")
    resp = client.post(
        "/jsonrpc/record_memory",
        json={"jsonrpc": JSONRPC_VERSION, "id": "req-005", "params": payload},
    )
    body = resp.json()
    assert "result" in body
    assert body["id"] == "req-005"
    assert body["result"]["resource_version"] == 1
    assert body["result"]["memory"]["metadata"]["name"] == "happy-005"


def test_a2a_006_query_memory_happy_path_returns_items(client):
    """TEST-A2A-006 · query_memory happy path：先 record 再 query → items 包含。"""
    payload = _make_memory_payload(name="mem-q1")
    client.post(
        "/jsonrpc/record_memory",
        json={"jsonrpc": JSONRPC_VERSION, "id": 1, "params": payload},
    )
    resp = client.post(
        "/jsonrpc/query_memory",
        json={
            "jsonrpc": JSONRPC_VERSION,
            "id": "q-006",
            "params": {"scope": "agent"},
        },
    )
    body = resp.json()
    assert "result" in body
    assert body["id"] == "q-006"
    names = [m["metadata"]["name"] for m in body["result"]["items"]]
    assert "mem-q1" in names


def test_a2a_007_record_then_query_round_trip(client):
    """TEST-A2A-007 · record + query 完整 round-trip：跨端点状态共享。"""
    # Record 3 个不同 memory
    for i in range(3):
        client.post(
            "/jsonrpc/record_memory",
            json={
                "jsonrpc": JSONRPC_VERSION,
                "id": f"rec-{i}",
                "params": _make_memory_payload(name=f"mem-rt-{i}"),
            },
        )
    # Query
    resp = client.post(
        "/jsonrpc/query_memory",
        json={
            "jsonrpc": JSONRPC_VERSION,
            "id": "q-rt",
            "params": {"scope": "agent"},
        },
    )
    body = resp.json()
    assert body["result"]["total_count"] >= 3


def test_a2a_008_healthz_returns_healthy(client):
    """TEST-A2A-008 · GET /healthz 返回 {"status": "healthy"} · Helm 探针期望。"""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


# ============================================================================
# TEST-A2A-009~012 · Error 传播（12 错误码 → JSON-RPC error.code 1:1）
# ============================================================================


def test_a2a_009_validation_error_returns_invalid_params_code(client):
    """TEST-A2A-009 · params 违反 Pydantic 约束（content 空）→ JSON-RPC -32602 invalid params。"""
    bad_payload = _make_memory_payload()
    bad_payload["spec"]["content"] = {}  # min_length=1 violation
    resp = client.post(
        "/jsonrpc/record_memory",
        json={"jsonrpc": JSONRPC_VERSION, "id": 9, "params": bad_payload},
    )
    body = resp.json()
    assert body["error"]["code"] == ERR_INVALID_PARAMS
    assert "errors" in body["error"]["data"]


def test_a2a_010_memory_backend_error_propagates_wire_code(client, make_service):
    """TEST-A2A-010 · record 抛 MemoryBackendError(MEMORY_INVALID_CONTENT) →
    JSON-RPC error.code = -32102（wire contract 1:1 映射）。"""
    service = make_service()

    # 替换 backend.put 抛 wire 错误码
    async def boom(memory, *, idempotency_key=None):
        raise MemoryBackendError(
            MemoryErrorCode.MEMORY_INVALID_CONTENT,
            "wire contract test",
        )

    service._backend.put = boom  # type: ignore[method-assign]

    app = create_app(service=service, clock=SystemClock())
    test_client = TestClient(app)
    payload = _make_memory_payload(name="boom-010")
    resp = test_client.post(
        "/jsonrpc/record_memory",
        json={"jsonrpc": JSONRPC_VERSION, "id": 10, "params": payload},
    )
    body = resp.json()
    assert body["error"]["code"] == int(MemoryErrorCode.MEMORY_INVALID_CONTENT)
    assert body["error"]["code"] == -32102
    assert body["error"]["data"]["code_name"] == "MEMORY_INVALID_CONTENT"


def test_a2a_011_query_too_broad_propagates_wire_code(client, make_service):
    """TEST-A2A-011 · query industry + no tag + no min_confidence 抛 MEMORY_QUERY_TOO_BROAD →
    JSON-RPC error.code = -32106。"""
    service = make_service()
    app = create_app(service=service, clock=SystemClock())
    test_client = TestClient(app)
    resp = test_client.post(
        "/jsonrpc/query_memory",
        json={
            "jsonrpc": JSONRPC_VERSION,
            "id": 11,
            "params": {"scope": "industry"},  # 无 tag + 无 min_confidence
        },
    )
    body = resp.json()
    assert body["error"]["code"] == -32106
    assert body["error"]["data"]["code_name"] == "MEMORY_QUERY_TOO_BROAD"
    assert body["error"]["data"]["module"] == "memory"


def test_a2a_012_error_data_includes_retryable_and_module(client, make_service):
    """TEST-A2A-012 · wire error response 的 data 字段携带 module + code_name + retryable。

    验证 MEMORY_RATE_LIMIT（-32104 · retryable=true）映射完整性。
    """
    service = make_service()

    async def rate_limit(*a, **kw):
        raise MemoryBackendError(
            MemoryErrorCode.MEMORY_RATE_LIMIT,
            "rate limited",
        )

    service._backend.put = rate_limit  # type: ignore[method-assign]

    app = create_app(service=service, clock=SystemClock())
    test_client = TestClient(app)
    payload = _make_memory_payload(name="rate-012")
    resp = test_client.post(
        "/jsonrpc/record_memory",
        json={"jsonrpc": JSONRPC_VERSION, "id": 12, "params": payload},
    )
    body = resp.json()
    assert body["error"]["code"] == -32104
    data = body["error"]["data"]
    assert data["module"] == "memory"
    assert data["code_name"] == "MEMORY_RATE_LIMIT"
    assert data["retryable"] is True
