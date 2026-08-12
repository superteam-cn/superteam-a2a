"""SV-VIS-UT-001~002 · VisibilityMatrix Protocol + KnowledgeVisibility re-export."""

from __future__ import annotations

from superteam_a2a.knowledge.crd.knowledgescope import KnowledgeVisibility
from superteam_a2a.shared.visibility.visibility_matrix import (
    VISIBILITY_MATRIX_PLACEHOLDER,
    VisibilityMatrix,
)
from superteam_a2a.shared.visibility.visibility_matrix import (
    KnowledgeVisibility as ReExportedKV,
)


def test_sv_vis_ut_001_visibility_matrix_protocol() -> None:
    """SV-VIS-UT-001 · VisibilityMatrix Protocol exists + duck-typing works."""
    assert VisibilityMatrix is not None

    class StubMatrix:
        def is_visible_to(
            self,
            visibility: KnowledgeVisibility,
            source_scope: str,
            target_scope: str,
        ) -> bool:
            return True

        def allowed_scopes(self, visibility: KnowledgeVisibility) -> frozenset[str]:
            return frozenset({"all"})

    stub = StubMatrix()
    assert isinstance(stub, VisibilityMatrix)


def test_sv_vis_ut_002_knowledge_visibility_reexport() -> None:
    """SV-VIS-UT-002 · KnowledgeVisibility re-export + 5-dim placeholder table."""
    # re-export must be the same StrEnum class (single source of truth)
    assert ReExportedKV is KnowledgeVisibility

    # placeholder table must cover all 5 dimensions
    assert len(VISIBILITY_MATRIX_PLACEHOLDER) == 5
    for kv in KnowledgeVisibility:
        assert kv in VISIBILITY_MATRIX_PLACEHOLDER

    # PUBLIC_READABLE carries the cross-scope wildcard marker
    assert "scope-children" in VISIBILITY_MATRIX_PLACEHOLDER[KnowledgeVisibility.PUBLIC_READABLE]
