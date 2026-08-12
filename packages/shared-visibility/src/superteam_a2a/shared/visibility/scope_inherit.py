"""ScopeInherit Protocol · L3-5 §3.1 inheritRules 4-level inheritance interface.

PR-3 only exposes:
  * ``ScopeInherit`` runtime-checkable Protocol
  * re-export of ``InheritRules`` Pydantic model

Business logic (filter evaluation + cache) deferred to PR-4+.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from superteam_a2a.knowledge.crd.inherit_rules import InheritRules
from superteam_a2a.knowledge.crd.scope_level import ScopeLevel

__all__ = ["InheritRules", "ScopeInherit"]


@runtime_checkable
class ScopeInherit(Protocol):
    """4-level scope inheritance filtering protocol (PR-3 stub · business logic PR-4+)."""

    def filter_inherited_scopes(
        self,
        child_level: ScopeLevel,
        parent_scopes: list[ScopeLevel],
        rules: InheritRules,
    ) -> list[ScopeLevel]:
        """Filter ``parent_scopes`` according to ``rules`` for ``child_level``.

        Applies ``include_types`` / ``exclude_types`` / ``allowed_child_levels``
        and enforces ``max_depth`` + ``block_self_reference`` constraints.
        """
        ...
