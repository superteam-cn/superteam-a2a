"""L3-6 §6 kopf on.create / on.update entry · 接线 record_memory_async。

依据 §6.3 协调点拓扑 D 方案：
- kopf @kopf.on.create → on_memory_create → record_memory_async
- kopf @kopf.on.update → on_memory_update → record_memory_async（覆盖更新）

通过 kopf memo 注入 MemoryBackendInProcessServiceImpl 单例；
缺失或类型不匹配时静默 return（operator 启动期 / 单元测试期可调用）。
"""

from __future__ import annotations

from typing import Any

from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.backend.clock import SystemClock
from superteam_a2a.knowledge_memory.backend.memory import Memory


async def on_memory_create(
    *,
    body: dict[str, Any],
    meta: dict[str, Any],
    memo: dict[str, Any],
    **_: Any,
) -> None:
    """kopf @kopf.on.create entry · §6 接线 record 路径。

    将 K8s body 反序列化为 Memory → 构造 InProcessContext →
    委托 record_memory_async。
    """
    service = memo.get("memory_in_process_service")
    if not isinstance(service, MemoryBackendInProcessServiceImpl):
        return
    memory = Memory.model_validate(body)
    context = InProcessContext(
        clock=SystemClock(),
        trace_id=str(meta.get("uid", "")),
    )
    await service.record_memory_async(memory, context=context)


async def on_memory_update(
    *,
    body: dict[str, Any],
    meta: dict[str, Any],
    memo: dict[str, Any],
    **_: Any,
) -> None:
    """kopf @kopf.on.update entry · §6 接线 record 路径（覆盖更新）。

    generation 变更由 backend.patch_status CAS 保证（§4.3 CAS 规则）。
    """
    service = memo.get("memory_in_process_service")
    if not isinstance(service, MemoryBackendInProcessServiceImpl):
        return
    memory = Memory.model_validate(body)
    context = InProcessContext(
        clock=SystemClock(),
        trace_id=str(meta.get("uid", "")),
    )
    await service.record_memory_async(memory, context=context)


__all__ = ["on_memory_create", "on_memory_update"]
