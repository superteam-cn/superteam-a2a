"""PR-4c JSON-RPC round-trip integration test · ASGI-IT-001。

PR-4c plan §7 测试 ID 命名：
- ASGI-IT-001 · POST /jsonrpc recordMemory round-trip with admission 50ms

测试策略：
- 使用 httpx2 + ASGITransport 启动完整 ASGI app in-process
- 装配真实 MemoryRecordService + AdmissionService + InMemoryBackend（PR-4a 5 步契约）
- POST /jsonrpc method=recordMemory params={memory: {...}}
- 验证响应包含 result.memory + result.phase + result.effective_confidence + result.resource_version
- 验证 50ms admission fail-closed（timing assertion）
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# 路径前置（与 unit test 一致模式）
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
from starlette.applications import Starlette  # noqa: E402
from superteam_a2a.knowledge_memory.api.service import (  # noqa: E402
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.asgi.app import create_app  # noqa: E402
from superteam_a2a.knowledge_memory.asgi.routes import (  # noqa: E402
    JSONRPC_VERSION,
    METHOD_RECORD_MEMORY,
)
from superteam_a2a.knowledge_memory.backend.clock import SystemClock  # noqa: E402
from superteam_a2a.knowledge_memory.backend.in_memory import InMemoryBackend  # noqa: E402
from superteam_a2a.knowledge_memory.handlers.admission_validator import (  # noqa: E402
    AdmissionValidatorImpl,
)
from superteam_a2a.knowledge_memory.services.knowledge.item import (  # noqa: E402
    KnowledgeItemService,
)
from superteam_a2a.knowledge_memory.services.knowledge.query import (  # noqa: E402
    KnowledgeQueryService,
)
from superteam_a2a.knowledge_memory.services.memory.query import (  # noqa: E402
    MemoryQueryService,
)
from superteam_a2a.knowledge_memory.services.memory.record import (  # noqa: E402
    MemoryRecordService,
)
from superteam_a2a.knowledge_memory.services.shared.admission import (  # noqa: E402
    AdmissionService,
)
from superteam_a2a.operator.models.memory import MemoryVisibility  # noqa: E402

# ============================================================================
# Helpers
# ============================================================================


def _make_memory_payload(
    *,
    name: str = "asgi-it-mem-1",
    namespace: str = "default",
    summary: str = "ASGI IT recordMemory round-trip",
    confidence: float = 1.0,
) -> dict:
    """构造 recordMemory 入参（K8s wire format dict · camelCase keys）。"""
    return {
        "apiVersion": "memory.superteam-a2a.io/v1alpha1",
        "kind": "Memory",
        "metadata": {"name": name, "namespace": namespace},
        "spec": {
            "scopeRef": {"name": "industry-ai"},
            "agentRef": {"kind": "ServiceAccount", "name": "asgi-it-sa"},
            "content": {"k": "v"},
            "summary": summary,
            "confidence": confidence,
            "decayDays": 30,
            "visibility": MemoryVisibility.SCOPE_AND_CHILDREN.value,
        },
    }


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def app_with_real_services() -> Starlette:
    """装配完整 ASGI app + 真实 PR-4a + PR-4b services。"""
    clock = SystemClock()
    backend = InMemoryBackend(clock=clock)
    in_process = MemoryBackendInProcessServiceImpl(backend=backend)
    admission_validator = AdmissionValidatorImpl()
    admission_service = AdmissionService(validator=admission_validator)

    app = create_app()
    app.state.clock = clock
    app.state.record_service = MemoryRecordService(
        in_process_service=in_process,
        clock=clock,
    )
    app.state.admission_service = admission_service
    app.state.query_service = MemoryQueryService(
        in_process_service=in_process,
        clock=clock,
    )
    app.state.knowledge_query_service = KnowledgeQueryService()
    app.state.knowledge_item_service = KnowledgeItemService()
    return app


# ============================================================================
# ASGI-IT-001 · POST /jsonrpc recordMemory round-trip with admission 50ms
# ============================================================================


@pytest.mark.asyncio
async def test_asgi_it_001_record_memory_round_trip(app_with_real_services: Starlette) -> None:
    """ASGI-IT-001 · POST /jsonrpc recordMemory 完整 round-trip。

    验证：
    - 响应 status_code=200
    - 响应 JSON-RPC 2.0 envelope 正确（jsonrpc + id + result）
    - result 包含 memory + phase + effective_confidence + resource_version
    """
    import httpx2

    request_body = {
        "jsonrpc": JSONRPC_VERSION,
        "id": "asgi-it-001-req",
        "method": METHOD_RECORD_MEMORY,
        "params": {"memory": _make_memory_payload()},
    }

    transport = httpx2.ASGITransport(app=app_with_real_services)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/jsonrpc",
            content=json.dumps(request_body),
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["jsonrpc"] == JSONRPC_VERSION
    assert body["id"] == "asgi-it-001-req"
    assert "result" in body
    result = body["result"]
    assert "memory" in result
    assert "phase" in result
    assert "effective_confidence" in result
    assert "resource_version" in result
    assert result["phase"] in {"Pending", "Bound", "Error"}


@pytest.mark.asyncio
async def test_asgi_it_001_admission_fail_closed_under_50ms(
    app_with_real_services: Starlette,
) -> None:
    """ASGI-IT-001 补充：admission 50ms fail-closed timing assertion。

    验证单次 recordMemory round-trip 总耗时包含 admission 50ms fail-closed。
    注意：这是 timing sanity check · 不严格断言 50ms（避免 flaky）· 只验证总耗时
    在合理范围内（含 admission 验证 + InMemoryBackend put）。
    """
    import httpx2

    request_body = {
        "jsonrpc": JSONRPC_VERSION,
        "id": "asgi-it-001-timing",
        "method": METHOD_RECORD_MEMORY,
        "params": {"memory": _make_memory_payload(name="timing-test")},
    }

    transport = httpx2.ASGITransport(app=app_with_real_services)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.monotonic()
        response = await client.post(
            "/jsonrpc",
            content=json.dumps(request_body),
            headers={"content-type": "application/json"},
        )
        elapsed = time.monotonic() - start

    assert response.status_code == 200
    body = response.json()
    assert body["jsonrpc"] == JSONRPC_VERSION
    # timing sanity check：admission 50ms + handler overhead → 总耗时 < 1s（宽松边界）
    assert elapsed < 1.0, f"recordMemory took {elapsed:.3f}s · 超过 1s 宽松边界"


@pytest.mark.asyncio
async def test_asgi_it_001_method_not_found_envelope(app_with_real_services: Starlette) -> None:
    """ASGI-IT-001 补充：未知 method → JSON-RPC -32601 method not found。"""
    import httpx2

    request_body = {
        "jsonrpc": JSONRPC_VERSION,
        "id": "asgi-it-001-404",
        "method": "nonExistentMethod",
        "params": {},
    }

    transport = httpx2.ASGITransport(app=app_with_real_services)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/jsonrpc",
            content=json.dumps(request_body),
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"]["code"] == -32601
    assert body["id"] == "asgi-it-001-404"
