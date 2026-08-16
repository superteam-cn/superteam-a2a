"""MemoryQueryService · 業務邏輯層 query 路徑。

PR-4b plan §2.2 Memory service 業務邏輯層 · 4 文件之二。
委託 `MemoryBackendInProcessServiceImpl.query_memory_async` (PR-4a 已實裝)。

InProcessService 職責（§6.4 step 5）：
- industry scope 預檢（無 tag/confidence 立即拋 MEMORY_QUERY_TOO_BROAD）
- 後置 confidence 過濾
- 異常原樣透傳（不重映射）

service 層職責（SRP）：
- 構造 InProcessContext（含 Clock 注入）
- 委託 InProcessService（scope 預檢 + confidence 過濾由 InProcessService 負責）
- 注入 Prometheus Counter MEMORY_IN_PROCESS_CALL_TOTAL
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.api.results import QueryMemoryResult
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessService,
)
from superteam_a2a.knowledge_memory.backend.clock import Clock
from superteam_a2a.knowledge_memory.backend.types import QueryMemoryRequest
from superteam_a2a.knowledge_memory.observability.metrics import (
    MEMORY_IN_PROCESS_CALL_TOTAL,
)


class MemoryQueryService:
    """Memory query 路徑業務邏輯 · 委託 InProcessService.query_memory_async。

    構造注入：
    - in_process_service · MemoryBackendInProcessService（PR-4a 已實裝）
    - clock · Clock Protocol（L3-6 §5.1）
    - trace_id · str | None（可選）
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

    async def execute(self, request: QueryMemoryRequest) -> QueryMemoryResult:
        """執行 query_memory 業務邏輯 · 委託 InProcessService。

        參數：
        - request · QueryMemoryRequest（frozen Pydantic · §5.6 字段）

        返回：
        - QueryMemoryResult（frozen Pydantic · 含 items + total_count）

        異常：
        - MemoryBackendError · 12 MEMORY_* 封閉錯誤碼（原樣透傳 · 不重映射）
        """
        context = InProcessContext(clock=self._clock, trace_id=self._trace_id)
        result = await self._in_process_service.query_memory_async(request, context=context)
        MEMORY_IN_PROCESS_CALL_TOTAL.labels(method="query", result="success").inc()
        return result


__all__ = ["MemoryQueryService"]
