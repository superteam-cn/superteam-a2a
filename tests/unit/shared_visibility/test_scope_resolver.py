"""SV-SCOPE-UT-001~002 · ScopeResolver Protocol + ScopeError exception."""

from __future__ import annotations

import pytest
from superteam_a2a.knowledge.crd.scope_level import ScopeLevel
from superteam_a2a.shared.visibility.scope_resolver import ScopeError, ScopeResolver


def test_sv_scope_ut_001_scope_resolver_protocol_exists() -> None:
    """SV-SCOPE-UT-001 · ScopeResolver Protocol exists + runtime_checkable."""
    # Protocol symbol itself
    assert ScopeResolver is not None
    # runtime_checkable decorator enables isinstance() on duck-typed classes.
    assert hasattr(ScopeResolver, "_is_protocol") or hasattr(ScopeResolver, "__protocol_attrs__")

    # Duck-typed stub class instances must be recognized as ScopeResolver
    class StubResolver:
        def resolve_chain(self, scope_name: str) -> list[str]:
            return [scope_name]

        def validate_parent(self, child_level: ScopeLevel, parent_level: ScopeLevel) -> bool:
            return True

    stub = StubResolver()
    assert isinstance(stub, ScopeResolver)


def test_sv_scope_ut_002_scope_error_exception() -> None:
    """SV-SCOPE-UT-002 · ScopeError exception can be raised + fields accessible."""
    with pytest.raises(ScopeError) as exc_info:
        raise ScopeError("agent-foo", "parent not found")

    assert exc_info.value.scope_name == "agent-foo"
    assert exc_info.value.reason == "parent not found"
    assert "agent-foo" in str(exc_info.value)
    assert "parent not found" in str(exc_info.value)
