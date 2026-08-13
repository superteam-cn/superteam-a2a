"""L3-5 §5.2 5 步算法 + §5.3 4 步 scope_ref 检测 · ADM-UT-006~009.

L3-5 §5.2 5 步算法 + §5.3 4 步算法单元测试。
PR-4a v0.2-draft 实装 · #111

测试 ID 规范：
- 避开 L3-5 §5.1 line 1428-1437 已有 ADMISSION-UT-001/002/003（PR-3 测试）
- PR-4a 新增 ADM-UT-006~009（4 ID）
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import sys
from pathlib import Path

# 路径前置
_REPO_ROOT = Path(__file__).resolve().parents[4]
_PK_PATH = str(_REPO_ROOT / "packages" / "knowledge" / "src")
_KM_PATH = str(_REPO_ROOT / "services" / "knowledge-memory-service" / "src")
for p in (_PK_PATH, _KM_PATH):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402
from superteam_a2a.knowledge.errors.codes import (  # noqa: E402
    KnowledgeContractError,
    KnowledgeErrorCode,
)
from superteam_a2a.knowledge_memory.handlers.admission_validator import (  # noqa: E402
    KnowledgeMemoryMutexValidator,
)


def _get_real_kopf():
    """获取真实 kopf 模块（绕过 test_main_memo.py 的 sys.modules['kopf'] MagicMock 污染）。

    tests/unit/knowledge_memory/conftest.py 的 _restore_real_kopf fixture 已在每个 test 前
    重置 sys.modules['kopf']，但模块顶部的 `import kopf` 会缓存 Mock 引用。本 helper 在测试
    函数内通过 importlib 重新导入 kopf，确保拿到真实模块。
    """
    return importlib.import_module("kopf")


# ============================================================================
# Mock fixtures
# ============================================================================


class _MockMeta:
    def __init__(self, name: str, labels: dict[str, str] | None = None) -> None:
        self.name = name
        self.labels = labels or {}


class _MockScopeRef:
    def __init__(self, name: str) -> None:
        self.name = name


class _MockSpec:
    def __init__(
        self,
        content: str = "",
        scope_ref: _MockScopeRef | None = None,
        parent_ref: _MockScopeRef | None = None,
    ) -> None:
        self.content = content
        self.scope_ref = scope_ref
        self.parent_ref = parent_ref


class _MockKn:
    def __init__(self, content: str, agent: str = "agent-1") -> None:
        self.metadata = _MockMeta(name="ki-1", labels={"superteam-a2a.io/agent": agent})
        self.spec = _MockSpec(content=content)


class _MockScope:
    def __init__(self, name: str, parent_name: str | None = None) -> None:
        self.metadata = _MockMeta(name=name)
        self.spec = _MockSpec(parent_ref=_MockScopeRef(name=parent_name) if parent_name else None)


# ADM-UT-006
async def test_admission_5step_no_matching_memory_allows():
    """ADM-UT-006 · 5 步算法 · 不存在同 content_hash Memory → 允许。"""
    validator = KnowledgeMemoryMutexValidator()
    ki = _MockKn(content="hello world")
    # memories=[] 无匹配 → 允许
    await validator.validate_ki_memory_mutex(ki, memories=[])


async def test_admission_5step_same_agent_supersede_allows():
    """ADM-UT-006 · 5 步算法 · 同 agent Memory 存在 → supersede 允许。"""
    validator = KnowledgeMemoryMutexValidator()
    ki = _MockKn(content="hello world", agent="agent-1")
    content_hash = hashlib.sha256(b"hello world").hexdigest()[:16]
    memories = [
        {
            "metadata": {
                "labels": {
                    "superteam-a2a.io/contentHash": content_hash,
                    "superteam-a2a.io/agent": "agent-1",
                }
            },
            "spec": {"subject": "agent-1"},
        }
    ]
    # 同 agent → return None（允许）
    await validator.validate_ki_memory_mutex(ki, memories=memories)


async def test_admission_5step_different_agent_rejects():
    """ADM-UT-006 · 5 步算法 · 不同 agent Memory 存在 → 拒绝。"""
    validator = KnowledgeMemoryMutexValidator()
    ki = _MockKn(content="hello world", agent="agent-1")
    content_hash = hashlib.sha256(b"hello world").hexdigest()[:16]
    memories = [
        {
            "metadata": {
                "labels": {
                    "superteam-a2a.io/contentHash": content_hash,
                    "superteam-a2a.io/agent": "agent-2",
                }
            },
            "spec": {"subject": "agent-2"},
        }
    ]
    with pytest.raises(KnowledgeContractError) as exc_info:
        await validator.validate_ki_memory_mutex(ki, memories=memories)
    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_ITEM_NOT_FOUND


# ADM-UT-007
async def test_admission_scope_ref_cycle_detected():
    """ADM-UT-007 · 4 步 scope_ref 检测 · 环 → KNOWLEDGE_OWNER_KIND_FORBIDDEN."""
    validator = KnowledgeMemoryMutexValidator(max_scope_depth=8)
    # scope A 的 parent 是 B，B 的 parent 是 A（环）
    scope_a = _MockScope("scope-a", parent_name="scope-b")
    scope_b = _MockScope("scope-b", parent_name="scope-a")
    scope_lookup = {"scope-a": scope_a, "scope-b": scope_b}
    with pytest.raises(KnowledgeContractError) as exc_info:
        await validator.detect_scope_ref_cycle(scope_a, scope_lookup=scope_lookup)
    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN


async def test_admission_scope_ref_depth_exceeded():
    """ADM-UT-007 · 4 步 scope_ref 检测 · 深度 > 8 → 拒绝。"""
    validator = KnowledgeMemoryMutexValidator(max_scope_depth=3)
    # 4 层嵌套
    s1 = _MockScope("s1", parent_name="s2")
    s2 = _MockScope("s2", parent_name="s3")
    s3 = _MockScope("s3", parent_name="s4")
    s4 = _MockScope("s4", parent_name="s5")
    s5 = _MockScope("s5", parent_name=None)
    scope_lookup = {"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5}
    with pytest.raises(KnowledgeContractError) as exc_info:
        await validator.detect_scope_ref_cycle(s1, scope_lookup=scope_lookup)
    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN


async def test_admission_scope_ref_no_cycle_allows():
    """ADM-UT-007 · 4 步 scope_ref 检测 · 无环 → 允许。"""
    validator = KnowledgeMemoryMutexValidator(max_scope_depth=8)
    s1 = _MockScope("s1", parent_name="s2")
    s2 = _MockScope("s2", parent_name=None)
    scope_lookup = {"s1": s1, "s2": s2}
    # 无环 → 不抛错
    await validator.detect_scope_ref_cycle(s1, scope_lookup=scope_lookup)


# ADM-UT-008
async def test_admission_fail_closed_50ms_timeout():
    """ADM-UT-008 · fail_closed_50ms 装饰器 · 内部 sleep > 50ms → kopf.AdmissionError."""
    from superteam_a2a.knowledge_memory.admission.webhook import fail_closed_50ms

    kopf = _get_real_kopf()

    @fail_closed_50ms
    async def slow_coro() -> None:
        await asyncio.sleep(0.080)  # > 50ms

    with pytest.raises(kopf.AdmissionError, match="fail-closed"):
        await slow_coro()


async def test_admission_fail_closed_50ms_fast_passes():
    """ADM-UT-008 · fail_closed_50ms 装饰器 · 内部快速完成 → 返回结果。"""
    from superteam_a2a.knowledge_memory.admission.webhook import fail_closed_50ms

    @fail_closed_50ms
    async def fast_coro() -> str:
        return "ok"

    result = await fast_coro()
    assert result == "ok"


# ADM-UT-009
async def test_admission_webhook_knowledge_item_rejects_large_content():
    """ADM-UT-009 · validate_knowledge_item webhook · content > 20 keys → kopf.AdmissionError."""
    from superteam_a2a.knowledge_memory.admission.webhook import (
        validate_knowledge_item,
    )

    kopf = _get_real_kopf()

    spec = {"content": {f"k{i}": "v" for i in range(21)}}
    with pytest.raises(kopf.AdmissionError, match="content keys > 20"):
        await validate_knowledge_item(spec=spec)  # type: ignore[reportCallIssue]


async def test_admission_webhook_memory_rejects_large_decay_days():
    """ADM-UT-009 · validate_memory webhook · decay_days > 3650 → kopf.AdmissionError."""
    from superteam_a2a.knowledge_memory.admission.webhook import (
        validate_memory,
    )

    kopf = _get_real_kopf()

    spec = {"content": {"k": "v"}, "decayDays": 3651}
    with pytest.raises(kopf.AdmissionError, match="decay_days > 3650"):
        await validate_memory(spec=spec)  # type: ignore[reportCallIssue]
