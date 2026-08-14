"""tests/unit/knowledge_memory/services/ conftest.py · PR-4b 12 service tests fixtures。

複用 api/conftest.py 的 fixture 模式（sample_memory + fake_clock + make_service），
確保 services/ 子目錄的測試有完整的 fixture 訪問。

PR-4b 12 service UT 測試依賴：
- sample_memory · Memory 頂層 CRD（來自 operator 模型）
- fake_clock · FakeClock（可控時間源）
- in_process_context · InProcessContext（Clock + trace_id）
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

# ============================================================================
# 路径前置（namespace package 解析順序）
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

# ============================================================================
# Time fixtures
# ============================================================================


@pytest.fixture
def base_time() -> datetime:
    """測試基準時間 · 2026-08-01 12:00:00 UTC。"""
    return datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fake_clock(base_time: datetime) -> FakeClock:
    """FakeClock 實例 · 起始 base_time。"""
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
    """構造測試用 Memory 實例。"""
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
    """單個標準 Memory。"""
    return _make_memory()


# ============================================================================
# InProcessContext fixture
# ============================================================================


@pytest.fixture
def in_process_context(fake_clock: FakeClock) -> InProcessContext:
    """InProcessContext with FakeClock。"""
    return InProcessContext(clock=fake_clock, trace_id="test-pr4b")
