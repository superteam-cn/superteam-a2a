"""Memory finalizer kopf.on.delete handler - L3-6 -4.4.

Invoked by kopf on Memory CR delete; delegates to MemoryReconcilerService.finalize.
The actual logic lives in MemoryReconcilerService.finalize (5-step cleanup).
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.reconciler.memory_reconciler import MemoryReconcilerService

MEMORY_FINALIZER = "memory.superteam-a2a.io/cleanup"


async def finalize_memory(*, body: dict[str, object], memo: dict[str, object], **_: object) -> None:
    """-4.4 @kopf.on.delete entry - delegates to service.finalize."""
    service = memo.get("memory_reconciler")
    if not isinstance(service, MemoryReconcilerService):
        return
    memory = Memory.model_validate(body)
    await service.finalize(memory)


__all__ = ["MEMORY_FINALIZER", "finalize_memory"]
