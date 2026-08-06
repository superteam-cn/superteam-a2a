"""API 测试 fixtures · InProcessContext / MemoryBackendInProcessServiceImpl / samples。

复用 backend/conftest.py 的 inline fixtures 模式（pytest 不会把 tests/ 当 namespace package）。
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

# ============================================================================
# 路径前置（namespace package 解析顺序）
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
    FakeClock,
    InMemoryBackend,
    Memory,
    ObjectMeta,
)
from superteam_a2a.knowledge_memory.api.service import (  # noqa: E402
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.backend.types import (  # noqa: E402
    MemoryScope,
    QueryMemoryRequest,
)
from superteam_a2a.operator.models.memory import (  # noqa: E402
    AgentReference,
    MemorySpec,
    ScopeReference,
)

# ============================================================================
# Time fixtures
# ============================================================================


@pytest.fixture
def base_time() -> datetime:
    """测试基准时间 · 2026-08-01 12:00:00 UTC。"""
    return datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fake_clock(base_time: datetime) -> FakeClock:
    """FakeClock 实例 · 起始 base_time。"""
    return FakeClock(base_time)


# ============================================================================
# Memory fixtures
# ============================================================================


def _make_memory(
    *,
    name: str = "mem-1",
    namespace: str = "default",
    summary: str = "Test memory",
    confidence: float = 1.0,
    decay_days: int = 30,
    tags: list[str] | None = None,
    visibility: str = "scope-and-children",
) -> Memory:
    """构造测试用 Memory 实例。"""
    from superteam_a2a.operator.models.memory import MemoryVisibility

    return Memory(
        metadata=ObjectMeta(name=name, namespace=namespace),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary=summary,
            confidence=confidence,
            decayDays=decay_days,
            tags=tags,
            visibility=MemoryVisibility(visibility),
        ),
    )


@pytest.fixture
def sample_memory() -> Memory:
    """单个标准 Memory。"""
    return _make_memory()


@pytest.fixture
def sample_memories() -> list[Memory]:
    """3 个不同 key 的 Memory（用于 list 排序）。"""
    return [
        _make_memory(name="mem-b", namespace="ns-a"),
        _make_memory(name="mem-a", namespace="ns-a"),
        _make_memory(name="mem-c", namespace="ns-b"),
    ]


# ============================================================================
# Service helper
# ============================================================================


def _make_service(*, backend=None, clock=None):
    """构造 MemoryBackendInProcessServiceImpl。"""
    if backend is None:
        backend = InMemoryBackend(clock=clock) if clock else InMemoryBackend()
    return MemoryBackendInProcessServiceImpl(backend=backend)


@pytest.fixture
def make_service():
    """返回 _make_service helper（参数化 backend / clock）。"""
    return _make_service


# ============================================================================
# Query helpers
# ============================================================================


@pytest.fixture
def make_query():
    """返回 QueryMemoryRequest 构造 helper。"""

    def _factory(
        *,
        scope: str = "agent",
        namespace: str | None = None,
        tags: tuple[str, ...] = (),
        min_confidence: float | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> QueryMemoryRequest:
        return QueryMemoryRequest(
            scope=MemoryScope(scope),
            namespace=namespace,
            tags=tags,
            min_confidence=min_confidence,
            limit=limit,
            offset=offset,
        )

    return _factory
