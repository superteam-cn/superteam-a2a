"""tests/integration/knowledge_memory/handlers/ conftest.py · 4 handler IT fixtures。

提供：
- fake_clock · FakeClock（可控時間源）
- in_process_context · InProcessContext 含 clock + trace_id
- sample_memory_dict · Memory CRD model_dump(by_alias=True) 序列化結果
- sample_query_dict · QueryMemoryRequest model_dump(by_alias=True) 序列化結果

父目錄 conftest.py 已 autouse 恢復真實 kopf 模組（避免 MagicMock 污染）。
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

# 路径前置（namespace package 解析順序）
_REPO_ROOT = Path(__file__).resolve().parents[5]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KN_SRC = _REPO_ROOT / "packages" / "knowledge" / "src"
_OP_SRC = _REPO_ROOT / "packages" / "operator" / "src"

_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)
_KN_PATH = str(_KN_SRC)
if _KN_PATH not in sys.path:
    sys.path.insert(0, _KN_PATH)
_OP_PATH = str(_OP_SRC)
if _OP_PATH not in sys.path:
    sys.path.insert(0, _OP_PATH)

from superteam_a2a.knowledge_memory import (  # noqa: E402
    FakeClock,
    Memory,
    ObjectMeta,
)
from superteam_a2a.knowledge_memory.api.context import InProcessContext  # noqa: E402
from superteam_a2a.operator.models.memory import (  # noqa: E402
    AgentReference,
    MemorySpec,
    MemoryVisibility,
    ScopeReference,
)


@pytest.fixture
def base_time() -> datetime:
    """測試基準時間 · 2026-08-14 10:00:00 UTC（#113 PR-4b Phase B 啟動時間）。"""
    return datetime(2026, 8, 14, 10, 0, 0, tzinfo=UTC)


@pytest.fixture
def fake_clock(base_time: datetime) -> FakeClock:
    """FakeClock 實例 · 起始 base_time。"""
    return FakeClock(base_time)


@pytest.fixture
def in_process_context(fake_clock: FakeClock) -> InProcessContext:
    """InProcessContext with FakeClock + trace_id=test-pr4b-handler。"""
    return InProcessContext(clock=fake_clock, trace_id="test-pr4b-handler")


@pytest.fixture
def sample_memory() -> Memory:
    """標準 Memory 實例（用於 handler round-trip 測試）。"""
    return Memory(
        metadata=ObjectMeta(name="mem-pr4b-handler", namespace="default"),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary="PR-4b handler IT",
            confidence=1.0,
            decayDays=30,
            visibility=MemoryVisibility.SCOPE_AND_CHILDREN,
        ),
    )


@pytest.fixture
def sample_memory_dict(sample_memory: Memory) -> dict:
    """Memory CRD 序列化為 dict（by_alias=True, exclude_none=True）。

    用於構造 JSON-RPC request["params"]["memory"]。
    """
    return sample_memory.model_dump(by_alias=True, exclude_none=True)


@pytest.fixture
def sample_query_dict() -> dict:
    """QueryMemoryRequest 序列化為 dict（用於 queryMemory handler）。

    使用 industry scope + tags 觸發合法路徑（不觸發 MEMORY_QUERY_TOO_BROAD）。
    QueryMemoryRequest 不帶 populate_by_name · 使用 snake_case 字段名。
    """
    return {
        "scope": "industry",
        "namespace": "default",
        "agent_ref": "hello-agent-sa",
        "tags": ["ai", "ml"],
        "min_confidence": 0.5,
        "limit": 10,
        "offset": 0,
    }


@pytest.fixture
def sample_query_broad_dict() -> dict:
    """industry scope 無 tags/confidence → 觸發 MEMORY_QUERY_TOO_BROAD。

    QueryMemoryRequest 不帶 populate_by_name · 使用 snake_case 字段名。
    """
    return {
        "scope": "industry",
        "namespace": "default",
        "tags": [],
        "limit": 10,
        "offset": 0,
    }


@pytest.fixture
def sample_request_memory(sample_memory_dict: dict) -> dict:
    """JSON-RPC request dict（recordMemory 輸入）。"""
    return {
        "jsonrpc": "2.0",
        "id": "test-rm-1",
        "method": "recordMemory",
        "params": {"memory": sample_memory_dict},
    }


@pytest.fixture
def sample_request_query(sample_query_dict: dict) -> dict:
    """JSON-RPC request dict（queryMemory 輸入 · 合法）。"""
    return {
        "jsonrpc": "2.0",
        "id": "test-qm-1",
        "method": "queryMemory",
        "params": {"query": sample_query_dict},
    }


@pytest.fixture
def sample_request_query_broad(sample_query_broad_dict: dict) -> dict:
    """JSON-RPC request dict（queryMemory 輸入 · 觸發 MEMORY_QUERY_TOO_BROAD）。"""
    return {
        "jsonrpc": "2.0",
        "id": "test-qm-broad",
        "method": "queryMemory",
        "params": {"query": sample_query_broad_dict},
    }


@pytest.fixture
def sample_request_query_knowledge() -> dict:
    """JSON-RPC request dict（queryKnowledge 輸入 · stub 返回空列表）。"""
    return {
        "jsonrpc": "2.0",
        "id": "test-qk-1",
        "method": "queryKnowledge",
        "params": {"query": {"queryText": "BM25 stub", "scopeRef": "industry-ai"}},
    }


@pytest.fixture
def sample_request_get_item() -> dict:
    """JSON-RPC request dict（getKnowledgeItem 輸入 · stub 返回 None）。"""
    return {
        "jsonrpc": "2.0",
        "id": "test-gki-1",
        "method": "getKnowledgeItem",
        "params": {"item_ref": {"name": "ki-stub", "version": 1}},
    }
