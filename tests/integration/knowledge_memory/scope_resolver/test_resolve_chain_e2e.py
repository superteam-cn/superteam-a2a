"""PR-4c SCOPE-IT-001 · 4 级 scope chain E2E（system → workflow → agentset → agent）.

PR-4c plan §7 测试 ID 命名：
- SCOPE-IT-001 · 4 级 scope 继承 E2E
                    · 构造完整 4 级 chain 验证 traverse_scope_chain 返回正确顺序
                    · 验证 KNOWLEDGE_SCOPE_NOT_FOUND 触发（缺失 parent）
"""

from __future__ import annotations

import sys
from pathlib import Path

# 路径前置
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_PK_SRC = _REPO_ROOT / "packages" / "knowledge" / "src"

_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)
_PK_PATH = str(_PK_SRC)
if _PK_PATH not in sys.path:
    sys.path.insert(0, _PK_PATH)

import pytest  # noqa: E402
from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeScope  # noqa: E402
from superteam_a2a.knowledge.crd.scope_level import ScopeLevel  # noqa: E402
from superteam_a2a.knowledge.errors.codes import (  # noqa: E402
    KnowledgeContractError,
    KnowledgeErrorCode,
)
from superteam_a2a.knowledge_memory.scope_resolver import (  # noqa: E402
    InMemoryScopeCache,
    ScopeResolver,
)


# ============================================================================
# Helpers
# ============================================================================


def _make_scope_with_level(
    name: str,
    parent_name: str | None,
    *,
    level: ScopeLevel,
) -> KnowledgeScope:
    """构造 KnowledgeScope with level + spec.name."""
    scope_data: dict = {
        "scopeLevel": level,
        "name": name,
        "subjectRef": {"kind": "Agent", "name": "test"},
        "visibility": "scope-and-children",
    }
    if parent_name:
        scope_data["parent_ref"] = {"name": parent_name}

    return KnowledgeScope(spec=scope_data)


# ============================================================================
# SCOPE-IT-001 · 4 级 scope 继承 E2E
# ============================================================================


def test_scope_it_001_4_level_scope_chain_e2e() -> None:
    """SCOPE-IT-001 · 构造 4 级 scope chain（system → workflow → agentset → agent）.

    Chain 结构：
        system (root)
          └── workflow (parent=system)
                └── agentset (parent=workflow)
                      └── agent-1 (parent=agentset)
                      └── agent-2 (parent=agentset)

    验证 traverse_scope_chain 从 agent-1 出发返回完整 chain。
    """
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # 4 级 chain（depth=3）
    cache.add(
        _make_scope_with_level("system-root", None, level=ScopeLevel.SYSTEM)
    )
    cache.add(
        _make_scope_with_level(
            "wf-1", "system-root", level=ScopeLevel.WORKFLOW
        )
    )
    cache.add(
        _make_scope_with_level("as-1", "wf-1", level=ScopeLevel.AGENT_SET)
    )
    cache.add(
        _make_scope_with_level("agent-1", "as-1", level=ScopeLevel.AGENT)
    )
    cache.add(
        _make_scope_with_level("agent-2", "as-1", level=ScopeLevel.AGENT)
    )

    # 验证：从 agent-1 出发 → 完整 chain
    chain = resolver.resolve_chain("agent-1", max_depth=8)
    assert chain == ["agent-1", "as-1", "wf-1", "system-root"]


def test_scope_it_001_4_level_chain_validate_parent_all_strict() -> None:
    """SCOPE-IT-001 补充 · 4 级 chain 中每个 parent_ref 严格 1 级校验全 True."""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # 装入 chain
    cache.add(_make_scope_with_level("system", None, level=ScopeLevel.SYSTEM))
    cache.add(_make_scope_with_level("wf", "system", level=ScopeLevel.WORKFLOW))
    cache.add(_make_scope_with_level("as", "wf", level=ScopeLevel.AGENT_SET))
    cache.add(_make_scope_with_level("a", "as", level=ScopeLevel.AGENT))

    # 严格 1 级校验
    assert (
        resolver.validate_parent(ScopeLevel.WORKFLOW, ScopeLevel.SYSTEM) is True
    )
    assert (
        resolver.validate_parent(ScopeLevel.AGENT_SET, ScopeLevel.WORKFLOW) is True
    )
    assert (
        resolver.validate_parent(ScopeLevel.AGENT, ScopeLevel.AGENT_SET) is True
    )


def test_scope_it_001_missing_parent_triggers_scope_not_found() -> None:
    """SCOPE-IT-001 · 缺失 parent 触发 KNOWLEDGE_SCOPE_NOT_FOUND。"""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # chain 中间缺一级
    cache.add(
        _make_scope_with_level(
            "wf-x", "missing-system", level=ScopeLevel.WORKFLOW
        )
    )

    with pytest.raises(KnowledgeContractError) as exc_info:
        resolver.resolve_chain("wf-x")

    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND


def test_scope_it_001_missing_scope_triggers_scope_not_found() -> None:
    """SCOPE-IT-001 · 起点 scope 缺失触发 KNOWLEDGE_SCOPE_NOT_FOUND."""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    with pytest.raises(KnowledgeContractError) as exc_info:
        resolver.resolve_chain("nonexistent-scope")

    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND


def test_scope_it_001_chain_completeness_for_all_leaves() -> None:
    """SCOPE-IT-001 补充 · 同 agentset 下两个 agent 各自完整 chain 解析."""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    cache.add(_make_scope_with_level("system", None, level=ScopeLevel.SYSTEM))
    cache.add(_make_scope_with_level("wf", "system", level=ScopeLevel.WORKFLOW))
    cache.add(_make_scope_with_level("as", "wf", level=ScopeLevel.AGENT_SET))
    cache.add(_make_scope_with_level("agent-1", "as", level=ScopeLevel.AGENT))
    cache.add(_make_scope_with_level("agent-2", "as", level=ScopeLevel.AGENT))

    chain1 = resolver.resolve_chain("agent-1", max_depth=8)
    chain2 = resolver.resolve_chain("agent-2", max_depth=8)

    assert chain1 == ["agent-1", "as", "wf", "system"]
    assert chain2 == ["agent-2", "as", "wf", "system"]
    # 同一个父 chain 共享
    assert chain1[1:] == chain2[1:]
