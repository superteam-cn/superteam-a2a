"""SV-KT-UT-001 · KnowledgeType re-export."""

from __future__ import annotations

from superteam_a2a.knowledge.crd.knowledgeitem import KnowledgeType as OriginalKT
from superteam_a2a.shared.visibility.knowledge_type import KnowledgeType as ReKT


def test_sv_kt_ut_001_knowledge_type_reexport() -> None:
    """SV-KT-UT-001 · KnowledgeType re-export keeps the 4 enum members."""
    # re-export must be the same StrEnum class (single source of truth)
    assert ReKT is OriginalKT

    # 4 wire string values from ADR-0002 §3.2 + L2-4 Spec §3.3
    assert ReKT.PROCEDURAL == "procedural"
    assert ReKT.FACTUAL == "factual"
    assert ReKT.EPISODIC == "episodic"
    assert ReKT.CONCEPTUAL == "conceptual"
