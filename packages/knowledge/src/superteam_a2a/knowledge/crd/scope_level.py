"""ScopeLevel StrEnum · L3-5 §3.1 / ADR-0002 §3.1."""

from __future__ import annotations

from enum import StrEnum


class ScopeLevel(StrEnum):
    """4 级 scope 枚举（agent/agentset/workflow/system）。"""

    AGENT = "agent"
    AGENT_SET = "agentset"
    WORKFLOW = "workflow"
    SYSTEM = "system"
