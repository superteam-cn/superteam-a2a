"""PR-4c VIS-UT-001 · 5 维 visibility matrix 静态断言.

PR-4c plan §7 测试 ID 命名：
- VIS-UT-001 · VISIBILITY_MATRIX 包含 5 个 KnowledgeVisibility 值（不能多也不能少）
                    · 静态断言（wire contract 零漂移）
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
)

# ============================================================================
# VIS-UT-001 · VISIBILITY_MATRIX 包含 5 个 KnowledgeVisibility 值
# ============================================================================


def test_vis_ut_001_visibility_matrix_covers_5_dimensions() -> None:
    """VIS-UT-001 · VISIBILITY_MATRIX 包含 5 个 KnowledgeVisibility 值（恰好 5 · 零漂移）."""
    # static assertion: set equality (wire contract 零漂移)
    expected_keys = {
        KnowledgeVisibility.SCOPE_ONLY,
        KnowledgeVisibility.SCOPE_AND_CHILDREN,
        KnowledgeVisibility.PUBLIC_READABLE,
        KnowledgeVisibility.AGENT_PRIVATE,
        KnowledgeVisibility.SYSTEM_READONLY,
    }
    assert set(VISIBILITY_MATRIX.keys()) == expected_keys
    assert len(VISIBILITY_MATRIX) == 5


def test_vis_ut_001_visibility_matrix_values_are_frozensets() -> None:
    """VIS-UT-001 补充 · 所有 value 都是 frozenset[str]（不可变 · wire 防腐）."""
    for visibility, scopes in VISIBILITY_MATRIX.items():
        assert isinstance(scopes, frozenset), f"{visibility}: not frozenset"
        for scope in scopes:
            assert isinstance(scope, str), f"{visibility} contains non-str: {scope}"


def test_vis_ut_001_public_readable_contains_wildcard() -> None:
    """VIS-UT-001 补充 · PUBLIC_READABLE 必须包含 "*" 通配符（公开可见所有 scope）."""
    public_scopes = VISIBILITY_MATRIX[KnowledgeVisibility.PUBLIC_READABLE]
    assert "*" in public_scopes


def test_vis_ut_001_scope_only_only_scope_self() -> None:
    """VIS-UT-001 补充 · SCOPE_ONLY 只允许 scope-self（不含 children / public / wildcard）."""
    scopes = VISIBILITY_MATRIX[KnowledgeVisibility.SCOPE_ONLY]
    assert "scope-self" in scopes
    assert "scope-children" not in scopes
    assert "scope-public" not in scopes
    assert "*" not in scopes


def test_vis_ut_001_scope_and_children_includes_self_and_children() -> None:
    """VIS-UT-001 补充 · SCOPE_AND_CHILDREN 包含 scope-self + scope-children（不含 wildcard）."""
    scopes = VISIBILITY_MATRIX[KnowledgeVisibility.SCOPE_AND_CHILDREN]
    assert "scope-self" in scopes
    assert "scope-children" in scopes
    assert "*" not in scopes


def test_vis_ut_001_agent_private_only_agent_self() -> None:
    """VIS-UT-001 补充 · AGENT_PRIVATE 只允许 agent-self（不含其他 scope）."""
    scopes = VISIBILITY_MATRIX[KnowledgeVisibility.AGENT_PRIVATE]
    assert "agent-self" in scopes
    assert "scope-self" not in scopes
    assert "*" not in scopes


def test_vis_ut_001_system_readonly_only_system_scope() -> None:
    """VIS-UT-001 补充 · SYSTEM_READONLY 只允许 system-scope."""
    scopes = VISIBILITY_MATRIX[KnowledgeVisibility.SYSTEM_READONLY]
    assert "system-scope" in scopes
    assert "scope-self" not in scopes
    assert "*" not in scopes


# ============================================================================
# VisibilityMatrix Protocol 注入测试
# ============================================================================


def test_static_visibility_matrix_dict_lookup() -> None:
    """StaticVisibilityMatrix 默认实现 · dict lookup 返回正确 scope 集合."""
    matrix = StaticVisibilityMatrix()

    public_scopes = matrix.allowed_scopes(KnowledgeVisibility.PUBLIC_READABLE)
    assert "*" in public_scopes
    assert "scope-self" in public_scopes


def test_static_visibility_matrix_returns_frozenset() -> None:
    """StaticVisibilityMatrix 返回 frozenset（不可变）."""
    matrix = StaticVisibilityMatrix()
    scopes = matrix.allowed_scopes(KnowledgeVisibility.SCOPE_ONLY)
    assert isinstance(scopes, frozenset)


def test_visibility_matrix_protocol_inheritance() -> None:
    """StaticVisibilityMatrix 继承 VisibilityMatrix · LSP 验证 · 可替换为 K8s 实现."""
    matrix = StaticVisibilityMatrix()
    assert isinstance(matrix, VisibilityMatrix)
