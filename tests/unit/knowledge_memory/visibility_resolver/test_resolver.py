"""PR-4c VIS-UT-002 + VIS-UT-003 · VisibilityResolver is_visible_to 矩阵策略.

PR-4c plan §7 测试 ID 命名：
- VIS-UT-002 · VisibilityResolver.is_visible_to 5 维 × 多 target_scope 组合
                    · PUBLIC_READABLE 包含 "*" 通配符
                    · AGENT_PRIVATE 只对 agent-self
- VIS-UT-003 · VISIBILITY_MATRIX 与 L3-5 §3.1 KnowledgeVisibility StrEnum 严格对应
                    · wire sync 静态断言（双向验证）
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

from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeVisibility  # noqa: E402
from superteam_a2a.knowledge_memory.visibility_resolver import (  # noqa: E402
    VISIBILITY_MATRIX,
    StaticVisibilityMatrix,
    VisibilityResolver,
)

# ============================================================================
# VIS-UT-002 · VisibilityResolver.is_visible_to 5 维组合
# ============================================================================


def test_vis_ut_002_scope_only_only_visible_to_scope_self() -> None:
    """VIS-UT-002 · SCOPE_ONLY 只对 scope-self 返回 True."""
    resolver = VisibilityResolver()

    assert resolver.is_visible_to(KnowledgeVisibility.SCOPE_ONLY, "scope-self") is True
    assert resolver.is_visible_to(KnowledgeVisibility.SCOPE_ONLY, "scope-children") is False
    assert resolver.is_visible_to(KnowledgeVisibility.SCOPE_ONLY, "scope-public") is False
    assert resolver.is_visible_to(KnowledgeVisibility.SCOPE_ONLY, "agent-self") is False


def test_vis_ut_002_scope_and_children_visible_to_self_and_children() -> None:
    """VIS-UT-002 · SCOPE_AND_CHILDREN 对 scope-self + scope-children 返回 True."""
    resolver = VisibilityResolver()

    assert resolver.is_visible_to(KnowledgeVisibility.SCOPE_AND_CHILDREN, "scope-self") is True
    assert resolver.is_visible_to(KnowledgeVisibility.SCOPE_AND_CHILDREN, "scope-children") is True
    assert resolver.is_visible_to(KnowledgeVisibility.SCOPE_AND_CHILDREN, "scope-public") is False
    assert resolver.is_visible_to(KnowledgeVisibility.SCOPE_AND_CHILDREN, "agent-self") is False


def test_vis_ut_002_public_readable_wildcard_visible_to_all() -> None:
    """VIS-UT-002 · PUBLIC_READABLE 包含 "*" 通配符 · 对任何 scope 都返回 True."""
    resolver = VisibilityResolver()

    assert resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, "scope-self") is True
    assert resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, "scope-children") is True
    assert resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, "scope-public") is True
    assert resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, "agent-self") is True
    # wildcard 测试
    assert resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, "any-scope-name") is True
    assert resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, "foobar") is True


def test_vis_ut_002_agent_private_only_visible_to_agent_self() -> None:
    """VIS-UT-002 · AGENT_PRIVATE 只对 agent-self 返回 True."""
    resolver = VisibilityResolver()

    assert resolver.is_visible_to(KnowledgeVisibility.AGENT_PRIVATE, "agent-self") is True
    assert resolver.is_visible_to(KnowledgeVisibility.AGENT_PRIVATE, "scope-self") is False
    assert resolver.is_visible_to(KnowledgeVisibility.AGENT_PRIVATE, "scope-children") is False
    assert resolver.is_visible_to(KnowledgeVisibility.AGENT_PRIVATE, "system-scope") is False


def test_vis_ut_002_system_readonly_only_visible_to_system_scope() -> None:
    """VIS-UT-002 · SYSTEM_READONLY 只对 system-scope 返回 True."""
    resolver = VisibilityResolver()

    assert resolver.is_visible_to(KnowledgeVisibility.SYSTEM_READONLY, "system-scope") is True
    assert resolver.is_visible_to(KnowledgeVisibility.SYSTEM_READONLY, "scope-self") is False
    assert resolver.is_visible_to(KnowledgeVisibility.SYSTEM_READONLY, "agent-self") is False


def test_vis_ut_002_resolver_accepts_custom_matrix() -> None:
    """VIS-UT-002 补充 · VisibilityResolver 接受 VisibilityMatrix 注入（OCP）。"""
    custom = StaticVisibilityMatrix()
    resolver = VisibilityResolver(matrix=custom)

    assert resolver.is_visible_to(KnowledgeVisibility.SCOPE_ONLY, "scope-self") is True


# ============================================================================
# VIS-UT-003 · wire sync 静态断言（双向验证）
# ============================================================================


def test_vis_ut_003_matrix_matches_l3_5_knowledge_visibility_strenum() -> None:
    """VIS-UT-003 · VISIBILITY_MATRIX 5 keys 严格对应 KnowledgeVisibility 5 values（wire sync）."""
    # 正向：matrix 覆盖 KnowledgeVisibility 所有成员（不能少）
    for k in KnowledgeVisibility:
        assert k in VISIBILITY_MATRIX, f"VISIBILITY_MATRIX missing {k}"

    # 反向：matrix 不能多（任何 matrix key 必须是 KnowledgeVisibility 成员 · 不允许新增同义）
    for k in VISIBILITY_MATRIX:
        assert k in KnowledgeVisibility, f"VISIBILITY_MATRIX has non-StrEnum key: {k}"

    # set equality · 严格双向一致（wire contract 零漂移）
    assert set(VISIBILITY_MATRIX.keys()) == set(KnowledgeVisibility)


def test_vis_ut_003_matrix_frozenset_size_invariant() -> None:
    """VIS-UT-003 补充 · 每个 visibility 至少 1 scope（不允许空 frozenset）。

    wire sync 不变量：每个 visibility 必须显式列出至少 1 个允许 scope。
    """
    for visibility, scopes in VISIBILITY_MATRIX.items():
        assert len(scopes) >= 1, f"{visibility} has empty scope set"
