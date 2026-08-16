"""L3-6 §6.1 InProcessContext · frozen Pydantic + Clock 唯一时间源。

in-process call context 在 record_memory_async / query_memory_async handler 入口构造；
Clock 必须与 L3-6 §5.1 Clock 协议同源（SystemClock/FakeClock）。
deadline_monotonic 由 caller 基于 context.clock.monotonic() 计算。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from superteam_a2a.knowledge_memory.backend.clock import Clock


class InProcessContext(BaseModel):
    """in-process call context · frozen + Clock 注入。

    §6.1 line 960: clock 必须与 L3-6 §5.1 Clock 协议同源。
    §6.1 line 943: immutable 传递；deadline_monotonic 由 caller 计算。
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,  # Clock 是 Protocol，Pydantic 无 schema
    )
    clock: Clock
    trace_id: str | None = Field(default=None, max_length=64)
    deadline_monotonic: float | None = Field(default=None, ge=0.0)


__all__ = ["InProcessContext"]
