"""5 维 visibility matrix 策略表 · L3-5 §3.1 + L3-6 §3 + ADR-0002 §4.

wire sync invariants (VIS-UT-001 / VIS-UT-003 static assertions):
1. All 5 KnowledgeVisibility values are covered (no more, no less)
2. Strategy sets match L3-5 §3.1 line 360-470 strictly (wire contract zero-drift)
3. PUBLIC_READABLE must include "*" wildcard (public-visible to all scopes)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeVisibility

# ============================================================================
# 5-dim visibility strategy table (L3-5 §3.1 + L3-6 §3 + ADR-0002 §4 · WireContract)
# ============================================================================

VISIBILITY_MATRIX: dict[KnowledgeVisibility, frozenset[str]] = {
    KnowledgeVisibility.SCOPE_ONLY: frozenset({"scope-self"}),
    KnowledgeVisibility.SCOPE_AND_CHILDREN: frozenset({"scope-self", "scope-children"}),
    KnowledgeVisibility.PUBLIC_READABLE: frozenset(
        {"scope-self", "scope-children", "scope-public", "*"},
    ),
    KnowledgeVisibility.AGENT_PRIVATE: frozenset({"agent-self"}),
    KnowledgeVisibility.SYSTEM_READONLY: frozenset({"system-scope"}),
}


@runtime_checkable
class VisibilityMatrix(Protocol):
    """5-dim visibility matrix Protocol interface.

    使用 typing.Protocol 而非 ABC，单元测试可用任意 duck-typed 实现。
    """

    def allowed_scopes(self, visibility: KnowledgeVisibility) -> frozenset[str]:
        """Return the set of scopes allowed for the given visibility."""
        ...


class StaticVisibilityMatrix:
    """默认静态实现 · 直接代理 VISIBILITY_MATRIX dict lookup.

    LSP：满足 VisibilityMatrix Protocol · 可替换为 K8s 自定义实现。
    """

    def allowed_scopes(self, visibility: KnowledgeVisibility) -> frozenset[str]:
        """Dict lookup · returns empty frozenset on miss (defensive)."""
        return VISIBILITY_MATRIX.get(visibility, frozenset())


__all__ = [
    "VISIBILITY_MATRIX",
    "StaticVisibilityMatrix",
    "VisibilityMatrix",
]
