"""ScopePhase StrEnum · L3-5 §3.1 status.phase 状态机."""

from __future__ import annotations

from enum import StrEnum


class ScopePhase(StrEnum):
    """KnowledgeScope status.phase 3 态（Pending/Active/Archived）。"""

    PENDING = "Pending"
    ACTIVE = "Active"
    ARCHIVED = "Archived"
