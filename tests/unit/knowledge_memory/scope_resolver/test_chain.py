"""PR-4c SCOPE-UT-002 + SCOPE-UT-003 · scope chain 遍历测试.

PR-4c plan §7 测试 ID 命名：
- SCOPE-UT-002 · traverse_scope_chain 检测 cycle（A → B → A）
- SCOPE-UT-003 · traverse_scope_chain 强制 max_depth 限制（max_depth=3 + depth=5）
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
    traverse_scope_chain,
)


# ============================================================================
# Helpers
# ============================================================================


def _make_scope(name: str, parent_name: str | None) -> KnowledgeScope:
    """构造 KnowledgeScope with spec.parent_ref.name fallback chain.

    name · spec.name 用于 _scope_name fallback。
    实际 K8s object 通过 metadata.name 暴露，单元测试用 spec.name 替代。
    """
    scope_data: dict = {
        "scopeLevel": ScopeLevel.AGENT,
        "name": name,
        "subjectRef": {"kind": "Agent", "name": "test"},
        "visibility": "scope-and-children",
    }
    if parent_name:
        scope_data["parent_ref"] = {"name": parent_name}

    return KnowledgeScope(spec=scope_data)


# ============================================================================
# SCOPE-UT-002 · traverse_scope_chain 检测 cycle
# ============================================================================


def test_scope_ut_002_traverse_scope_chain_detects_self_reference() -> None:
    """SCOPE-UT-002 · 构造循环 scope（A → B → A）→ traverse_scope_chain raise KNOWLEDGE_OWNER_KIND_FORBIDDEN."""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # 构造 A → B → A 循环
    scope_a = _make_scope("A", parent_name="B")
    scope_b = _make_scope("B", parent_name="A")
    cache.add(scope_a)
    cache.add(scope_b)

    # 解析 A 的 chain → 命中 cycle → raise KNOWLEDGE_OWNER_KIND_FORBIDDEN
    with pytest.raises(KnowledgeContractError) as exc_info:
        resolver.resolve_chain("A", max_depth=8)

    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN


def test_scope_ut_002_traverse_scope_chain_detects_self_loop() -> None:
    """SCOPE-UT-002 补充 · A 自循环（A → A）→ 直接 raise cycle。"""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # A → A 自循环
    scope_a = _make_scope("A", parent_name="A")
    cache.add(scope_a)

    with pytest.raises(KnowledgeContractError) as exc_info:
        resolver.resolve_chain("A", max_depth=8)

    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN


# ============================================================================
# SCOPE-UT-003 · traverse_scope_chain 强制 max_depth
# ============================================================================


def test_scope_ut_003_traverse_scope_chain_enforces_max_depth() -> None:
    """SCOPE-UT-003 · 构造深度 5 chain → max_depth=3 抛 KNOWLEDGE_OWNER_KIND_FORBIDDEN.

    构造 5 级 chain：A → B → C → D → E → F（6 节点 · depth=5）。
    traverse_scope_chain(max_depth=3) 在第 4 步尝试下探时 raise。
    """
    cache = InMemoryScopeCache()

    # 构造 5 级 chain（A 是叶子 · F 是 root）
    for parent_child in [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F")]:
        child_name, parent_name = parent_child
        cache.add(_make_scope(child_name, parent_name=parent_name))
    cache.add(_make_scope("F", parent_name=None))  # root 无 parent

    resolver = ScopeResolver(cache)

    # max_depth=3 → depth >= 3 时 raise → chain 长度最多 = max_depth + 1 = 4
    with pytest.raises(KnowledgeContractError) as exc_info:
        resolver.resolve_chain("A", max_depth=3)

    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN


def test_scope_ut_003_traverse_scope_chain_max_depth_8_allows_4_level() -> None:
    """SCOPE-UT-003 补充 · max_depth=8 允许完整 4 级 scope chain。

    4 级 chain：A → B → C → D → root（D 无 parent）。
    节点个数 5 · depth 序列 0, 1, 2, 3, 4 → max_depth=8 充裕。
    """
    cache = InMemoryScopeCache()

    # 4 级 chain（A 叶子 · root 无 parent）
    cache.add(_make_scope("A", parent_name="B"))
    cache.add(_make_scope("B", parent_name="C"))
    cache.add(_make_scope("C", parent_name="D"))
    cache.add(_make_scope("D", parent_name="root"))
    cache.add(_make_scope("root", parent_name=None))

    resolver = ScopeResolver(cache)

    chain = resolver.resolve_chain("A", max_depth=8)
    assert chain == ["A", "B", "C", "D", "root"]


def test_scope_ut_003_traverse_scope_chain_block_self_reference_false() -> None:
    """SCOPE-UT-003 补充 · block_self_reference=False 允许重用（B → A 内部引用 · Cycle 视情）。"""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    # Cycle 但 block_self_reference=False
    cache.add(_make_scope("A", parent_name="B"))
    cache.add(_make_scope("B", parent_name=None))  # B 是 root，链路终止

    # 解析 A → B → stop · 不命中 cycle
    chain = resolver.resolve_chain("A", max_depth=8, block_self_reference=False)
    assert chain == ["A", "B"]


# ============================================================================
# Scope not found 测试
# ============================================================================


def test_scope_chain_scope_not_found() -> None:
    """SCOPE chain 测试 · 不存在 scope raise KNOWLEDGE_SCOPE_NOT_FOUND."""
    cache = InMemoryScopeCache()
    resolver = ScopeResolver(cache)

    with pytest.raises(KnowledgeContractError) as exc_info:
        resolver.resolve_chain("nonexistent")

    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND


def test_scope_chain_parent_not_found() -> None:
    """SCOPE chain 测试 · parent 不存在 raise KNOWLEDGE_SCOPE_NOT_FOUND."""
    cache = InMemoryScopeCache()
    cache.add(_make_scope("A", parent_name="missing-parent"))

    resolver = ScopeResolver(cache)

    with pytest.raises(KnowledgeContractError) as exc_info:
        resolver.resolve_chain("A")

    assert exc_info.value.code == KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND


def test_scope_chain_simple_chain_no_parent() -> None:
    """SCOPE chain 测试 · 无 parent 单一 scope 返回 [self]."""
    cache = InMemoryScopeCache()
    cache.add(_make_scope("lonely", parent_name=None))
    resolver = ScopeResolver(cache)

    chain = resolver.resolve_chain("lonely")
    assert chain == ["lonely"]
