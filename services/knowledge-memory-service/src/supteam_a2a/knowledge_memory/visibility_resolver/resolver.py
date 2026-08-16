"""5 维 visibility resolver 主类.

PR-4c plan §2.4 · L3-5 §3.1 + L3-6 §3 + ADR-0002 §4。

is_visible_to algorithm:
1. matrix.allowed_scopes(visibility) -> frozenset[str]
2. target_scope in allowed -> True
3. "*" in allowed -> True (PUBLIC_READABLE wildcard)
4. otherwise -> False
"""

from __future__ import annotations

from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeVisibility
from superteam_a2a.knowledge_memory.visibility_resolver.matrix import (
    StaticVisibilityMatrix,
    VisibilityMatrix,
)


class VisibilityResolver:
    """5-dim visibility resolver main class.

    Single public method: is_visible_to(visibility, target_scope) -> bool.
    """

    def __init__(self, matrix: VisibilityMatrix | None = None) -> None:
        """Constructor with optional matrix injection (DIP)."""
        self._matrix = matrix if matrix is not None else StaticVisibilityMatrix()

    def is_visible_to(
        self,
        visibility: KnowledgeVisibility,
        target_scope: str,
    ) -> bool:
        """Determine whether visibility allows the target_scope.

        Returns True if target_scope is in the visibility's allowed set,
        or the allowed set contains "*" wildcard.
        """
        allowed = self._matrix.allowed_scopes(visibility)
        return target_scope in allowed or "*" in allowed


__all__ = [
    "VisibilityResolver",
]
