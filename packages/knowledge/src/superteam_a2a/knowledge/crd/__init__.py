"""Knowledge Service CRD types · L3-5 v0.2.0 §3.1-§3.3.

Re-exports for downstream packages. wire YAML contract 完全继承 L2-4 v0.2.0。
"""

from __future__ import annotations

from superteam_a2a.knowledge.crd.inherit_rules import InheritRules
from superteam_a2a.knowledge.crd.item_reference import ItemReference
from superteam_a2a.knowledge.crd.knowledgeitem import (
    DecayState,
    ItemPhase,
    KnowledgeItem,
    KnowledgeItemSpec,
    KnowledgeItemStatus,
    KnowledgeType,
)
from superteam_a2a.knowledge.crd.knowledgescope import (
    KnowledgeScope,
    KnowledgeScopeSpec,
    KnowledgeScopeStatus,
    KnowledgeVisibility,
    SubjectKind,
    SubjectReference,
)
from superteam_a2a.knowledge.crd.memory_schema import (
    GCState,
    Memory,
    MemoryPhase,
    MemorySpec,
    MemoryStatus,
)
from superteam_a2a.knowledge.crd.scope_level import ScopeLevel
from superteam_a2a.knowledge.crd.scope_phase import ScopePhase
from superteam_a2a.knowledge.crd.scope_reference import ScopeReference

__all__ = [
    # Auxiliary value objects
    "DecayState",
    "GCState",
    "InheritRules",
    "ItemPhase",
    "ItemReference",
    "KnowledgeItem",
    "KnowledgeItemSpec",
    "KnowledgeItemStatus",
    "KnowledgeScope",
    "KnowledgeScopeSpec",
    "KnowledgeScopeStatus",
    "KnowledgeType",
    "KnowledgeVisibility",
    "Memory",
    "MemoryPhase",
    "MemorySpec",
    "MemoryStatus",
    "ScopeLevel",
    "ScopePhase",
    "ScopeReference",
    "SubjectKind",
    "SubjectReference",
]
