"""Shared visibility package · 4 shared modules (Protocol interfaces only).

PR-3 surface — business logic deferred to PR-4+.
"""

from superteam_a2a.shared.visibility.knowledge_type import KnowledgeType
from superteam_a2a.shared.visibility.scope_inherit import InheritRules, ScopeInherit
from superteam_a2a.shared.visibility.scope_resolver import ScopeError, ScopeResolver
from superteam_a2a.shared.visibility.visibility_matrix import (
    VISIBILITY_MATRIX_PLACEHOLDER,
    KnowledgeVisibility,
    VisibilityMatrix,
)

__all__ = [
    "VISIBILITY_MATRIX_PLACEHOLDER",
    "InheritRules",
    "KnowledgeType",
    "KnowledgeVisibility",
    "ScopeError",
    "ScopeInherit",
    "ScopeResolver",
    "VisibilityMatrix",
]
