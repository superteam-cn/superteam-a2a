"""Handler 测试 fixtures · sample_memory + fake_memo。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

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
    Memory,
    ObjectMeta,
)
from superteam_a2a.operator.models.memory import (  # noqa: E402
    AgentReference,
    MemorySpec,
    ScopeReference,
)


@pytest.fixture
def sample_memory() -> Memory:
    """单个标准 Memory（handler body 验证用）。"""
    from superteam_a2a.operator.models.memory import MemoryVisibility

    return Memory(
        metadata=ObjectMeta(name="mem-handler", namespace="default"),
        spec=MemorySpec(
            scope_ref=ScopeReference(name="industry-ai"),
            agent_ref=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary="handler test",
            confidence=1.0,
            visibility=MemoryVisibility.SCOPE_AND_CHILDREN,
        ),
    )


@pytest.fixture
def fake_memo() -> dict:
    """空 memo dict（handler 缺失 service 时静默 return 测试用）。"""
    return {}


@pytest.fixture
def sample_body(sample_memory: Memory) -> dict:
    """Memory 序列化为 dict（kopf body 格式）。"""
    return sample_memory.model_dump(by_alias=True, exclude_none=True)


@pytest.fixture
def sample_meta() -> dict:
    """kopf meta dict（uid 提取用）。"""
    return {"uid": "test-uid-12345"}
