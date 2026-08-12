"""Scope resolver Protocol · L3-5 §4 引用 · 业务逻辑 PR-4+ 实装.

Re-export location for L3-5 §4 + L3-6 §4.5 shared definition.
PR-3 only exposes the Protocol interface; concrete implementations
(dependency-graph walker, cache layer) deferred to PR-4+.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from superteam_a2a.knowledge.crd.scope_level import ScopeLevel


class ScopeError(Exception):
    """Scope resolution error (PR-3 stub · PR-4+ adds error codes + detailed messages)."""

    def __init__(self, scope_name: str, reason: str) -> None:
        super().__init__(f"Scope '{scope_name}': {reason}")
        self.scope_name = scope_name
        self.reason = reason


@runtime_checkable
class ScopeResolver(Protocol):
    """4-level scope resolution protocol (PR-3 stub · business logic PR-4+).

    Implements L3-5 §4 + L3-6 §4.5 shared definition.
    """

    def resolve_chain(self, scope_name: str) -> list[str]:
        """Return the inheritance chain for ``scope_name``.

        Example:
            resolve_chain('agent-foo') -> ['system', 'workflow-bar', 'agentset-baz', 'agent-foo']
        """
        ...

    def validate_parent(self, child_level: ScopeLevel, parent_level: ScopeLevel) -> bool:
        """Validate that ``parent_level`` is exactly 1 step above ``child_level``.

        Strict monotonic ordering: system -> workflow -> agentset -> agent.
        Same-level or out-of-order parents are rejected.

        Returns:
            True if valid transition, False otherwise.
        """
        ...
