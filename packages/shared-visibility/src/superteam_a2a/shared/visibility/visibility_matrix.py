"""Visibility matrix Protocol · L3-5 §5 5-dimensional strategy placeholder.

PR-3 only exposes:
  * ``VisibilityMatrix`` runtime-checkable Protocol
  * re-export of ``KnowledgeVisibility`` StrEnum (single source of truth)
  * 5-dimension strategy placeholder table for early consumers / tests

Business logic (cache + audit + cardinality policy) deferred to PR-4+.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeVisibility

__all__ = ["VISIBILITY_MATRIX_PLACEHOLDER", "KnowledgeVisibility", "VisibilityMatrix"]


# 5-dimension visibility strategy table placeholder (PR-3 stub · business logic PR-4+).
# Wildcard ``*`` denotes cross-scope access for PUBLIC; the other four restrict
# the visible set to same-scope, sibling, or higher-level peers.
VISIBILITY_MATRIX_PLACEHOLDER: dict[KnowledgeVisibility, frozenset[str]] = {
    KnowledgeVisibility.SCOPE_ONLY: frozenset({"scope-self"}),
    KnowledgeVisibility.SCOPE_AND_CHILDREN: frozenset({"scope-self", "scope-children"}),
    KnowledgeVisibility.PUBLIC_READABLE: frozenset(
        {"scope-self", "scope-children", "public-readers"}
    ),
    KnowledgeVisibility.AGENT_PRIVATE: frozenset({"agent-self"}),
    KnowledgeVisibility.SYSTEM_READONLY: frozenset({"system-readers"}),
}


@runtime_checkable
class VisibilityMatrix(Protocol):
    """5-dimension visibility matrix protocol (PR-3 stub · business logic PR-4+)."""

    def is_visible_to(
        self,
        visibility: KnowledgeVisibility,
        source_scope: str,
        target_scope: str,
    ) -> bool:
        """Return True iff ``source_scope`` at ``visibility`` is visible to ``target_scope``."""
        ...

    def allowed_scopes(self, visibility: KnowledgeVisibility) -> frozenset[str]:
        """Return the set of scope keys permitted at the given ``visibility`` dimension."""
        ...
