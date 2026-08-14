"""MemoryRecordService · 業務邏輯層 record 路徑。

PR-4b plan §2.2 Memory service 業務邏輯層 · 4 文件之一。
委託 `MemoryBackendInProcessServiceImpl.record_memory_async` (PR-4a 已實裝 5 步契約)。

5 步契約（§6.4）：
1. freeze input — memory.model_copy(deep=True)
2. 50ms validation — context.clock.monotonic() + 0.050 + asyncio.wait_for
3. admission validate — fail-closed 校驗
4. single handoff — 僅一次 backend.put + idempotency_key 防重
5. propagate/commit — 直接返回或拋權威異常

service 層職責（SRP）：
- 構造 InProcessContext（含 Clock 注入）
- 委託 InProcessService（5 步契約 + 50ms fail-closed 由 InProcessService 負責）
- 注入 Prometheus Counter MEMORY_IN_PROCESS_CALL_TOTAL

service 不重複 50ms fail-closed 邏輯（單一來源原則）。
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.api.results import MemoryRecordResult
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessService,
)
from superteam_a2a.knowledge_memory.backend.clock import Clock
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.observability.metrics import (
    MEMORY_IN_PROCESS_CALL_TOTAL,
)


class MemoryRecordService:
    """Memory record 路徑業務邏輯 · 委託 InProcessService.record_memory_async。

    構造注入：
    - in_process_service · MemoryBackendInProcessService（PR-4a 已實裝）
    - clock · Clock Protocol（L3-6 §5.1 · SystemClock/FakeClock）
    - trace_id · str | None（可選 · 用於 trace 標記）
    """

    def __init__(
        self,
        *,
        in_process_service: MemoryBackendInProcessService,
        clock: Clock,
        trace_id: str | None = None,
    ) -> None:
        self._in_process_service = in_process_service
        self._clock = clock
        self._trace_id = trace_id

    async def execute(self, memory: Memory) -> MemoryRecordResult:
        """執行 record_memory 業務邏輯 · 委託 InProcessService。

        參數：
        - memory · Memory 頂層 CRD（含 metadata + spec + status）

        返回：
        - MemoryRecordResult（frozen Pydantic · 含 phase + effective_confidence + resource_version）

        異常：
        - MemoryBackendError · 12 MEMORY_* 封閉錯誤碼（原樣透傳 · 不重映射）
        - KnowledgeContractError / KnowledgeError · 跨模塊校驗異常（InProcessService 透傳）
        """
        context = InProcessContext(clock=self._clock, trace_id=self._trace_id)
        result = await self._in_process_service.record_memory_async(memory, context=context)
        MEMORY_IN_PROCESS_CALL_TOTAL.labels(method="record", result="success").inc()
        return result


__all__ = ["MemoryRecordService"]
