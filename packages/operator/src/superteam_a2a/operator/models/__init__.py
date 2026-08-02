"""superteam-a2a Operator CRD models (Pydantic v2).

依据 L3-1 Spec §2.3.4 + L3-1 §6.2 + L1 §2-§4。
- Agent / AgentSet / Workflow Pydantic 在 L1 Spec §2-§4 定义（待 L4 #75+ 落地）
- Memory Pydantic v2 完整实现在 L3-1 Spec §6.2.1-§6.2.5（L4 Step 1 落地）
"""

from __future__ import annotations

from superteam_a2a.operator.models.memory import (
    MemoryCondition,
    MemoryConditionType,
    MemoryPhase,
    MemorySpec,
    MemoryStatus,
    MemoryVisibility,
)

__all__ = [
    # Memory CRD（L3-1 §6.2 · L4 Step 1）
    "MemoryCondition",
    "MemoryConditionType",
    "MemoryPhase",
    "MemorySpec",
    "MemoryStatus",
    "MemoryVisibility",
]
