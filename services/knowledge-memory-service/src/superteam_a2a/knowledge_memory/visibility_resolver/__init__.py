"""Visibility resolver 业务逻辑层 · 5 维 visibility 矩阵 + scope/scope 过滤.

PR-4c plan §2.4 · L3-5 §3.1 + L3-6 §3 + ADR-0002 §3。
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.visibility_resolver.matrix import (
    VISIBILITY_MATRIX,
    StaticVisibilityMatrix,
    VisibilityMatrix,
)
from superteam_a2a.knowledge_memory.visibility_resolver.resolver import VisibilityResolver

__all__ = [
    "VISIBILITY_MATRIX",
    "StaticVisibilityMatrix",
    "VisibilityMatrix",
    "VisibilityResolver",
]
