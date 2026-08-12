"""SV-INH-UT-001~002 · ScopeInherit Protocol + InheritRules re-export."""

from __future__ import annotations

from superteam_a2a.knowledge.crd.inherit_rules import InheritRules as OriginalIR
from superteam_a2a.knowledge.crd.scope_level import ScopeLevel
from superteam_a2a.shared.visibility.scope_inherit import InheritRules, ScopeInherit


def test_sv_inh_ut_001_scope_inherit_protocol() -> None:
    """SV-INH-UT-001 · ScopeInherit Protocol exists + duck-typing works."""
    assert ScopeInherit is not None

    class StubInherit:
        def filter_inherited_scopes(
            self,
            child_level: ScopeLevel,
            parent_scopes: list[ScopeLevel],
            rules: InheritRules,
        ) -> list[ScopeLevel]:
            return parent_scopes

    stub = StubInherit()
    assert isinstance(stub, ScopeInherit)


def test_sv_inh_ut_002_inherit_rules_reexport() -> None:
    """SV-INH-UT-002 · InheritRules re-export + field round-trip."""
    from superteam_a2a.shared.visibility.scope_inherit import InheritRules as ReIR

    assert ReIR is OriginalIR

    rules = InheritRules.model_validate({"maxDepth": 2, "allowedChildLevels": [ScopeLevel.AGENT]})
    assert rules.max_depth == 2
    assert ScopeLevel.AGENT in rules.allowed_child_levels
