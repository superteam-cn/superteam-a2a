"""PR-4c Agent Card endpoint integration test · CARD-IT-001。

PR-4c plan §7 测试 ID 命名：
- CARD-IT-001 · GET /.well-known/agent.json returns 4 skills + 5 endpoint 描述

测试策略：
- 使用 httpx2 + ASGITransport 启动 ASGI app in-process（subprocess-free）
- 与 Phase 3 PR-1 测试模式一致（httpx2 替代 starlette TestClient · httpx2 0.27+）
"""

from __future__ import annotations

import sys
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
from superteam_a2a.knowledge_memory.asgi.app import create_app  # noqa: E402
from superteam_a2a.knowledge_memory.backend.clock import SystemClock  # noqa: E402
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


class _StubAdmissionValidator:
    async def validate(self, memory: object, *, timeout: float) -> None:
        return None


# ============================================================================
# Fixtures
# ============================================================================


class _NoopRecordService:
    async def execute(self, memory: object) -> object:
        raise NotImplementedError


class _NoopQueryService:
    async def execute(self, query: object) -> object:
        raise NotImplementedError


@pytest.fixture
def app_with_services() -> Starlette:
    """装配完整 ASGI app + 6 services（stub · 满足 isinstance 验证即可）。"""
    app = create_app()
    app.state.clock = SystemClock()
    app.state.record_service = MemoryRecordService(  # type: ignore[abstract]
        in_process_service=None,  # type: ignore[arg-type]
        clock=SystemClock(),
    )
    app.state.admission_service = AdmissionService(validator=_StubAdmissionValidator())  # type: ignore[arg-type]
    app.state.query_service = MemoryQueryService(  # type: ignore[abstract]
        in_process_service=None,  # type: ignore[arg-type]
        clock=SystemClock(),
    )
    app.state.knowledge_query_service = KnowledgeQueryService()
    app.state.knowledge_item_service = KnowledgeItemService()
    return app


# ============================================================================
# CARD-IT-001 · GET /.well-known/agent.json
# ============================================================================


@pytest.mark.asyncio
async def test_card_it_001_get_well_known_agent_json(app_with_services: Starlette) -> None:
    """CARD-IT-001 · GET /.well-known/agent.json 返回 200 + 4 skills + 5 endpoint 描述。"""
    import httpx2

    transport = httpx2.ASGITransport(app=app_with_services)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/.well-known/agent.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    body = response.json()
    # 4 skills
    skills = body["skills"]
    assert len(skills) == 4
    skill_ids = {skill["id"] for skill in skills}
    assert skill_ids == {
        "queryKnowledge",
        "getKnowledgeItem",
        "recordMemory",
        "queryMemory",
    }

    # 5 endpoint 描述
    endpoints = body["endpoints"]
    assert len(endpoints) == 5
    paths = {endpoint["path"] for endpoint in endpoints}
    assert paths == {
        "/.well-known/agent.json",
        "/jsonrpc",
        "/healthz",
        "/readyz",
        "/metrics",
    }


@pytest.mark.asyncio
async def test_card_it_001_healthz_returns_healthy(app_with_services: Starlette) -> None:
    """CARD-IT-001 补充：/healthz 端点 in-process 测试。"""
    import httpx2

    transport = httpx2.ASGITransport(app=app_with_services)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_card_it_001_readyz_returns_ready(app_with_services: Starlette) -> None:
    """CARD-IT-001 补充：/readyz 端点 in-process 测试（clock 已注入 → 200 ready）。"""
    import httpx2

    transport = httpx2.ASGITransport(app=app_with_services)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
