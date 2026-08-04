"""共享 fixtures · Memory / FakeClock / sample state。

TDD 测试基础设施（l4-tdd-methodology.md）：每个测试用例应使用 FakeClock
显式控制时间；不得依赖 datetime.now()。

注意：superteam_a2a 是 PEP 420 namespace package（5 个 workspace 成员合并）。
为确保 knowledge_memory 子包可导入，必须把 services/knowledge-memory-service/src
放到 sys.path 最前（先于其他 superteam_a2a 路径）。
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
# 顺序很关键：knowledge-memory-service 必须在 operator 之前
# 否则 Python 先找到 operator/src/supteam_a2a/__init__.py，就找不到 knowledge_memory 子包
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)
_OP_PATH = str(_OP_SRC)
if _OP_PATH not in sys.path:
    # 把 operator 放到 services 后面
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
    """测试基准时间 · 2026-08-01 12:00:00 UTC（tz-aware）。"""
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
            scope_ref=ScopeReference(name="industry-ai"),
            agent_ref=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary=summary,
            confidence=confidence,
            decay_days=decay_days,
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
    """3 个不同 key 的 Memory 用于 LIST 排序测试。"""
    return [
        _make_memory(name="mem-b", namespace="ns-a"),
        _make_memory(name="mem-a", namespace="ns-a"),
        _make_memory(name="mem-c", namespace="ns-b"),
    ]


@pytest.fixture
def sample_state(
    sample_memories: list[Memory], fake_clock: FakeClock
) -> dict[tuple[str, str], object]:
    """预填充 state（3 个 StoredMemory 记录）。

    返回 dict 兼容 pure.py 的 state 入参类型。
    """
    from superteam_a2a.knowledge_memory import StoredMemory

    state: dict[tuple[str, str], StoredMemory] = {}
    for mem in sample_memories:
        key = (mem.metadata.namespace, mem.metadata.name)
        state[key] = StoredMemory(
            memory=mem,
            created_at=fake_clock.now(),
            updated_at=fake_clock.now(),
            version=1,
        )
    return state
