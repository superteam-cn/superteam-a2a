"""L3-6 §6 kopf on.create / on.update / query handler 入口 · 接线 record_memory_async + query_memory_async。

依据 §6.3 协调点拓扑 D 方案：
- kopf @kopf.on.create → on_memory_create → record_memory_async
- kopf @kopf.on.update → on_memory_update → record_memory_async（覆盖更新）
- a2a.queryMemory → handle_query_memory → query_memory_async

通过 kopf memo 注入 MemoryBackendInProcessServiceImpl 单例；
缺失或类型不匹配时静默 return（operator 启动期 / 单元测试期可调用）。

§M-1.5 修复：Clock 必须从 memo["clock"] 读取，禁止现场 new SystemClock() / FakeClock()。
"""

from __future__ import annotations

from typing import Any

from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.api.results import QueryMemoryResult
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.backend.clock import Clock
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.types import QueryMemoryRequest


async def _build_context(memo: dict[str, Any], meta: dict[str, Any]) -> InProcessContext | None:
    """§M-1.5 Clock 注入：从 memo["clock"] 读取 + isinstance guard。

    任一缺失/类型不匹配 → 返回 None，调用者静默 return。
    """
    clock = memo.get("clock")
    if not isinstance(clock, Clock):
        return None
    return InProcessContext(
        clock=clock,
        trace_id=str(meta.get("uid", "")),
    )


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
    context = await _build_context(memo, meta)
    if context is None:
        return
    memory = Memory.model_validate(body)
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
    context = await _build_context(memo, meta)
    if context is None:
        return
    memory = Memory.model_validate(body)
    await service.record_memory_async(memory, context=context)


async def handle_query_memory(
    *,
    body: dict[str, Any],
    memo: dict[str, Any],
    **_: Any,
) -> QueryMemoryResult:
    """L3-5 §4.4 a2a.queryMemory handler · 接线 query_memory_async。

    流程（L3-5 §4.4 line 1241）：
    1. 提取 body["metadata"] → trace_id（QueryMemoryRequest 不允许 metadata 字段）
    2. 反序列化剩余 body → QueryMemoryRequest（已在 backend/types.py 实装）
    3. 取 memo["clock"] 构造 InProcessContext（§M-1.5）
    4. 委托 service.query_memory_async(req, context=...)
    5. 异常原样透传（L3-6 §6.2 调用契约 3 项规则 2）

    边界：
    - memo 缺 memory_in_process_service 或 clock → 静默 return 空 QueryMemoryResult
    - body 验证失败 → 原样透传 ValidationError
    - service 抛 MemoryBackendError → 原样透传
    """
    service = memo.get("memory_in_process_service")
    clock = memo.get("clock")
    if not isinstance(service, MemoryBackendInProcessServiceImpl) or not isinstance(clock, Clock):
        return QueryMemoryResult(items=(), total_count=0)
    # 提取 K8s metadata.uid 作为 trace_id（QueryMemoryRequest 字段外）
    metadata_obj = body.get("metadata", {})
    trace_id = str(metadata_obj.get("uid", "")) if isinstance(metadata_obj, dict) else ""
    # 反序列化剩余 body → QueryMemoryRequest（去掉 metadata 字段避免 extra="forbid" 拒绝）
    query_body = {k: v for k, v in body.items() if k != "metadata"}
    request = QueryMemoryRequest.model_validate(query_body)
    context = InProcessContext(clock=clock, trace_id=trace_id)
    return await service.query_memory_async(request, context=context)


__all__ = [
    "handle_query_memory",
    "on_memory_create",
    "on_memory_update",
]
