"""PR-4c SCOPE-UT-001 · 4 级 scope resolver validate_parent 严格 1 级校验.

PR-4c plan §7 测试 ID 命名：
- SCOPE-UT-001 · validate_parent() 验证严格 1 级递增 + SYSTEM 顶层例外 +
  反向/跨级/同级 失败
"""

from __future__ import annotations

import sys
from pathlib import Path

# 路径前置（与 test_app.py 模式一致）
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_PK_SRC = _REPO_ROOT / "packages" / "knowledge" / "src"

_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

_PK_PATH = str(_PK_SRC)
if _PK_PATH not in sys.path:
    sys.path.insert(0, _PK_PATH)

from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeScope  # noqa: E402
from superteam_a2a.knowledge.crd.scope_level import ScopeLevel  # noqa: E402
from superteam_a2a.knowledge_memory.scope_resolver import (  # noqa: E402
    InMemoryScopeCache,
    ScopeResolver,
)


# ============================================================================
# SCOPE-UT-001 · validate_parent 严格 1 级校验
# ============================================================================


def test_scope_ut_001_validate_parent_valid_increment() -> None:
    """SCOPE-UT-001 · system→workflow, workflow→agentset, agentset→agent 严格 1 级."""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # 正向严格 1 级 → True
    assert resolver.validate_parent(ScopeLevel.WORKFLOW, ScopeLevel.SYSTEM) is True
    assert resolver.validate_parent(ScopeLevel.AGENT_SET, ScopeLevel.WORKFLOW) is True
    assert resolver.validate_parent(ScopeLevel.AGENT, ScopeLevel.AGENT_SET) is True


def test_scope_ut_001_validate_parent_system_top_level_none() -> None:
    """SCOPE-UT-001 · SYSTEM 顶层 parent_ref=None → True（合法）。"""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # SYSTEM 顶层 → parent_ref=None 合法
    assert resolver.validate_parent(ScopeLevel.SYSTEM, None) is True


def test_scope_ut_001_validate_parent_cross_level_fails() -> None:
    """SCOPE-UT-001 · system→agent 跨级失败（违反严格 1 级）。"""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # system → agent（跨级 · 期望 False）
    assert resolver.validate_parent(ScopeLevel.WORKFLOW, ScopeLevel.AGENT) is False
    # workflow → agent（跨级 · 期望 False）
    assert resolver.validate_parent(ScopeLevel.AGENT_SET, ScopeLevel.AGENT) is False


def test_scope_ut_001_validate_parent_same_level_fails() -> None:
    """SCOPE-UT-001 · 同级（system→system）失败（不允许同级引用）。"""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # system → system（同级 · 期望 False）
    assert resolver.validate_parent(ScopeLevel.SYSTEM, ScopeLevel.SYSTEM) is False
    # workflow → workflow（同级 · 期望 False）
    assert resolver.validate_parent(ScopeLevel.WORKFLOW, ScopeLevel.WORKFLOW) is False
    assert resolver.validate_parent(ScopeLevel.AGENT_SET, ScopeLevel.AGENT_SET) is False
    assert resolver.validate_parent(ScopeLevel.AGENT, ScopeLevel.AGENT) is False


def test_scope_ut_001_validate_parent_reverse_fails() -> None:
    """SCOPE-UT-001 · 反向（workflow→system）失败（不允许子指向父）。"""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # workflow → system（反向 · 期望 False · 子不应指向顶层）
    assert resolver.validate_parent(ScopeLevel.AGENT_SET, ScopeLevel.SYSTEM) is False
    # agent → workflow（反向跨级 · 期望 False）
    assert resolver.validate_parent(ScopeLevel.AGENT, ScopeLevel.WORKFLOW) is False
    # agent → system（反向跨级 · 期望 False）
    assert resolver.validate_parent(ScopeLevel.AGENT, ScopeLevel.SYSTEM) is False


def test_scope_ut_001_validate_parent_non_system_with_none_fails() -> None:
    """SCOPE-UT-001 · 非 SYSTEM 层级 parent_ref=None 失败（必须严格 1 级递增）。"""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # 非 SYSTEM + parent=None → False（必须严格 1 级）
    assert resolver.validate_parent(ScopeLevel.WORKFLOW, None) is False
    assert resolver.validate_parent(ScopeLevel.AGENT_SET, None) is False
    assert resolver.validate_parent(ScopeLevel.AGENT, None) is False


def test_scope_ut_001_in_memory_scope_cache_lookup_roundtrip() -> None:
    """SCOPE-UT-001 补充 · InMemoryScopeCache add + get roundtrip + 未命中 None。"""
    cache = InMemoryScopeCache()
    # 未命中 → None
    assert cache.get("nonexistent") is None

    # 装入一个 scope（mock metadata via Pydantic 包装）
    scope = KnowledgeScope(
        spec={
            "scopeLevel": ScopeLevel.AGENT,
            "name": "agent-1",
            "subjectRef": {"kind": "Agent", "name": "a1"},
            "visibility": "scope-only",
        },
    )
    # Pydantic 模型没有 metadata，需要 Pydantic v2 + 直接注入或测试防御式访问
    # 因 KnowledgeScope 不存 metadata，但 resolver._scope_name 接受 spec.name fallback
    cache.add(scope)

    # 命中
    retrieved = cache.get("agent-1")
    assert retrieved is scope
