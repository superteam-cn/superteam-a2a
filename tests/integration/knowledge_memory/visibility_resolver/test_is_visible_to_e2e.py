"""PR-4c VIS-IT-001 · 5 维 visibility E2E（5 种 visibility × 多 target_scope）.

PR-4c plan §7 测试 ID 命名：
- VIS-IT-001 · 5 维 visibility 端到端
                    · 构造 5 类 KnowledgeItem（5 种 visibility）
                    · 对每类用不同 target_scope 查询 → 验证 is_visible_to 正确
                    · 包含通配符 "*" 的 PUBLIC_READABLE 测试
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
    VisibilityMatrix,
    VisibilityResolver,
)


# ============================================================================
# Custom matrix (PR-5 + 测试场景扩展使用 · OCP 验证)
# ============================================================================


class MockWorkflowVisibilityMatrix(VisibilityMatrix):
    """工作流测试用自定义 matrix · 替换 PUBLIC_READABLE 集合。

    OCP 验证：PR-5 可注入自定义矩阵（如 industry-scope-only）。
    """

    def __init__(self) -> None:
        self._custom = {
            KnowledgeVisibility.PUBLIC_READABLE: frozenset({"scope-public", "*"}),
            KnowledgeVisibility.SCOPE_ONLY: frozenset({"scope-self"}),
            KnowledgeVisibility.SCOPE_AND_CHILDREN: frozenset({"scope-self", "scope-children"}),
            KnowledgeVisibility.AGENT_PRIVATE: frozenset({"agent-self"}),
            KnowledgeVisibility.SYSTEM_READONLY: frozenset({"system-scope"}),
        }

    def allowed_scopes(self, visibility: KnowledgeVisibility) -> frozenset[str]:
        return self._custom.get(visibility, frozenset())


# ============================================================================
# VIS-IT-001 · 5 维 visibility E2E
# ============================================================================


def test_vis_it_001_5_dimension_visibility_e2e() -> None:
    """VIS-IT-001 · 端到端：构造 5 类 KnowledgeItem（5 种 visibility）.

    对每类 item 用不同 target_scope 查询 is_visible_to，验证全部组合正确。
    """
    resolver = VisibilityResolver(matrix=StaticVisibilityMatrix())

    # 模拟 5 类 item（每类一种 visibility）
    items_visibilities = [
        ("scope-only-item", KnowledgeVisibility.SCOPE_ONLY),
        ("scope-and-children-item", KnowledgeVisibility.SCOPE_AND_CHILDREN),
        ("public-readable-item", KnowledgeVisibility.PUBLIC_READABLE),
        ("agent-private-item", KnowledgeVisibility.AGENT_PRIVATE),
        ("system-readonly-item", KnowledgeVisibility.SYSTEM_READONLY),
    ]

    # 对每类 item 验证 is_visible_to 在 5 种 target_scope 下
    target_scopes = ["scope-self", "scope-children", "scope-public", "agent-self", "system-scope"]

    for item_name, visibility in items_visibilities:
        allowed = VISIBILITY_MATRIX[visibility]
        for target in target_scopes:
            expected = target in allowed or "*" in allowed
            actual = resolver.is_visible_to(visibility, target)
            assert actual == expected, (
                f"item={item_name} visibility={visibility} target={target}: "
                f"expected={expected} actual={actual}"
            )


def test_vis_it_001_public_readable_wildcard_e2e() -> None:
    """VIS-IT-001 补充 · PUBLIC_READABLE 包含 "*" 通配符 · 对任何 scope 都返回 True."""
    resolver = VisibilityResolver()

    # 测试 10 种任意 scope 名
    arbitrary_scopes = [
        "scope-self",
        "scope-children",
        "scope-public",
        "agent-self",
        "system-scope",
        "random-scope-1",
        "any-other-scope",
        "test-foobar",
        "wf-123",
        "industry-xyz",
    ]

    for scope in arbitrary_scopes:
        assert (
            resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, scope) is True
        ), f"PUBLIC_READABLE should be visible to {scope}"


def test_vis_it_001_agent_private_e2e() -> None:
    """VIS-IT-001 补充 · AGENT_PRIVATE 只对 agent-self 返回 True."""
    resolver = VisibilityResolver()

    # AGENT_PRIVATE 验证 5 种 target 组合
    assert resolver.is_visible_to(KnowledgeVisibility.AGENT_PRIVATE, "agent-self") is True
    assert resolver.is_visible_to(KnowledgeVisibility.AGENT_PRIVATE, "scope-self") is False
    assert resolver.is_visible_to(KnowledgeVisibility.AGENT_PRIVATE, "scope-children") is False
    assert resolver.is_visible_to(KnowledgeVisibility.AGENT_PRIVATE, "scope-public") is False
    assert resolver.is_visible_to(KnowledgeVisibility.AGENT_PRIVATE, "system-scope") is False


def test_vis_it_001_system_readonly_e2e() -> None:
    """VIS-IT-001 补充 · SYSTEM_READONLY 只对 system-scope 返回 True."""
    resolver = VisibilityResolver()

    assert resolver.is_visible_to(KnowledgeVisibility.SYSTEM_READONLY, "system-scope") is True
    assert resolver.is_visible_to(KnowledgeVisibility.SYSTEM_READONLY, "scope-self") is False
    assert resolver.is_visible_to(KnowledgeVisibility.SYSTEM_READONLY, "scope-children") is False
    assert resolver.is_visible_to(KnowledgeVisibility.SYSTEM_READONLY, "scope-public") is False
    assert resolver.is_visible_to(KnowledgeVisibility.SYSTEM_READONLY, "agent-self") is False


def test_vis_it_001_custom_matrix_via_ocp() -> None:
    """VIS-IT-001 补充 · OCP 验证：注入自定义 matrix 替换 PUBLIC_READABLE 集合."""
    custom_resolver = VisibilityResolver(matrix=MockWorkflowVisibilityMatrix())

    # 验证自定义 PUBLIC_READABLE（去除 scope-self + scope-children + 添加 scope-public 显式存在）
    assert (
        custom_resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, "scope-self")
        is False
    )
    assert (
        custom_resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, "scope-public")
        is True
    )
    # 通配符仍生效
    assert (
        custom_resolver.is_visible_to(KnowledgeVisibility.PUBLIC_READABLE, "any-scope")
        is True
    )

    # SCOPE_ONLY 不受影响
    assert (
        custom_resolver.is_visible_to(KnowledgeVisibility.SCOPE_ONLY, "scope-self") is True
    )
