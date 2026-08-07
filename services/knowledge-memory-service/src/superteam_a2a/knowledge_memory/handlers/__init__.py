"""L3-6 §6 kopf handler 接线 · D 方案单进程架构。

- memory_handler: @kopf.on.create / @kopf.on.update + a2a.queryMemory
- admission_validator: AdmissionValidatorImpl（§6.4 step 3 mutex lookup）
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.handlers.admission_validator import (
    AdmissionValidatorImpl,
)
from superteam_a2a.knowledge_memory.handlers.memory_handler import (
    handle_query_memory,
    on_memory_create,
    on_memory_update,
)
from superteam_a2a.knowledge_memory.reconciler.memory_reconciler import (
    AdmissionValidatorProtocol,
)

__all__ = [
    "AdmissionValidatorImpl",
    "AdmissionValidatorProtocol",
    "handle_query_memory",
    "on_memory_create",
    "on_memory_update",
]
