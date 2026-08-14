"""MemoryReinforceService · 業務邏輯層 reinforce 路徑。

PR-4b plan §2.2 Memory service 業務邏輯層 · 4 文件之三。
業務邏輯：通過 backend.patch_status CAS 提升 confidence。

CAS 規則（§4.3 + §5.7 不變量 2）：
- expected_generation 必須匹配 backend 當前 generation
- CAS 衝突顯式失敗 → MemoryBackendError(MEMORY_FORBIDDEN)
- 不允許 fail-open

service 職責：
- 構造 patch_status status payload（reinforced_count + last_reinforced_at + effective_confidence）
- 注入 Prometheus Counter MEMORY_REINFORCE_TOTAL
- CAS 失敗透傳 MEMORY_FORBIDDEN（不重映射）

LSP：service 依賴 MemoryBackend Protocol（L3-6 §5.7 6 抽象方法），mock backend 即可替換。
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.protocol import MemoryBackend
from superteam_a2a.knowledge_memory.observability.metrics import (
    MEMORY_REINFORCE_TOTAL,
)


class ReinforceStatus(BaseModel):
    """reinforce 操作 payload · patch_status 入參。

    字段含義（依據 L3-6 §3.5 MemoryStatus）：
    - reinforced_count · 強化計數（>= 0）
    - last_reinforced_at · 強化時間戳（UTC aware datetime）
    - effective_confidence · 強化後 confidence ∈ [0, 1]
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    reinforced_count: int = Field(ge=0)
    last_reinforced_at: AwareDatetime
    effective_confidence: float = Field(ge=0.0, le=1.0)


class MemoryReinforceService:
    """Memory reinforce 路�業務邏輯 · CAS 提升 confidence。

    構造注入：
    - backend · MemoryBackend Protocol（L3-6 §5.7 6 抽象方法）
    - context · InProcessContext（提供 Clock 用於 last_reinforced_at 時間戳）
    """

    def __init__(
        self,
        *,
        backend: MemoryBackend,
        context: InProcessContext,
    ) -> None:
        self._backend = backend
        self._context = context

    async def execute(
        self,
        memory: Memory,
        *,
        new_confidence: float,
    ) -> float:
        """執行 reinforce 業務邏輯 · CAS 提升 confidence。

        參數：
        - memory · Memory 頂層 CRD（含 metadata.generation）
        - new_confidence · 新 confidence ∈ [0, 1]

        返回：
        - float · 強化後的 confidence（== new_confidence）

        異常：
        - MemoryBackendError(MEMORY_FORBIDDEN) · CAS 衝突（透傳）
        - MemoryBackendError · 其他 backend 異常（原樣透傳）

        不變量：
        - new_confidence ∈ [0, 1]（輸入校驗）
        - patch_status 使用 expected_generation=memory.metadata.generation
        """
        if not 0.0 <= new_confidence <= 1.0:
            raise ValueError(f"new_confidence must be in [0, 1], got {new_confidence}")

        # 構造 ReinforceStatus payload
        now = datetime.now(UTC)
        existing_count = memory.spec.reinforced_count if memory.spec else 0
        status = ReinforceStatus(
            reinforced_count=existing_count + 1,
            last_reinforced_at=now,
            effective_confidence=new_confidence,
        )

        # CAS · generation 衝突顯式失敗
        try:
            await self._backend.patch_status(
                memory.metadata.namespace,
                memory.metadata.name,
                status.model_dump(by_alias=False),
                expected_generation=memory.metadata.generation,
            )
        except MemoryBackendError as exc:
            if exc.code == MemoryErrorCode.MEMORY_FORBIDDEN:
                MEMORY_REINFORCE_TOTAL.labels(result="forbidden").inc()
            else:
                MEMORY_REINFORCE_TOTAL.labels(result="error").inc()
            raise

        MEMORY_REINFORCE_TOTAL.labels(result="success").inc()
        return new_confidence


__all__ = [
    "MemoryReinforceService",
    "ReinforceStatus",
]
