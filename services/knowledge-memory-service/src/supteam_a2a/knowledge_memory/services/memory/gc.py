"""MemoryGCService · 業務邏輯層 gc 路徑。

PR-4b plan §2.2 Memory service 業務�輯層 · 4 文件之四。
業務邏輯：mark/archive/delete 狀態轉換。

MemoryPhase 狀態機（依據 L3-1 §6.2.5 line 1827-1833）：
- Pending → Bound → Reinforced → Archived → Deleted

GC 合法轉換：
- ACTIVE → ARCHIVED → DELETED（標記 → 刪除）
- DECAYING → ARCHIVED → DELETED
- EXPIRED → DELETED（直接刪除）

service 職責：
- 驗證目標 phase 是當前 phase 的合法後繼
- 通過 backend.patch_status 標記 archived（如需）
- 通過 backend.delete 最終刪除
- 注入 Prometheus Counter MEMORY_GC_CLEANED_TOTAL

依據 L3-1 §6.2.5 狀態機 + L3-6 §5.5 DELETE 冪等規則。
"""

from __future__ import annotations

from enum import StrEnum

from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.protocol import MemoryBackend
from superteam_a2a.knowledge_memory.observability.metrics import (
    MEMORY_GC_CLEANED_TOTAL,
)


class GCState(StrEnum):
    """Memory GC 狀態（labels gc_state）。

    - MARKED · 已標記為 Archived（等待清理）
    - DELETED · 已從 backend 刪除
    - SKIPPED · 不合法轉換跳過
    """

    MARKED = "marked"
    DELETED = "deleted"
    SKIPPED = "skipped"


# GC 合法後繼 phase
_GC_LEGAL_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("Active", "Archived"),
        ("Decaying", "Archived"),
        ("Expired", "Deleted"),
        ("Archived", "Deleted"),
    }
)


class MemoryGCService:
    """Memory gc 路徑業務邏輯 · 標記 → 刪除兩步。

    構造注入：
    - backend · MemoryBackend Protocol（L3-6 §5.7）
    - context · InProcessContext（含 Clock + trace_id）
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
        target_phase: str,
    ) -> str:
        """執行 gc 業務邏輯 · 標記 + 刪除。

        參數：
        - memory · Memory 頂層 CRD
        - target_phase · 目標 phase（"Archived" 或 "Deleted"）

        返回：
        - str · 最終 phase（"Archived" 或 "Deleted"）

        異常：
        - ValueError · 不合法 phase 轉換
        - MemoryBackendError · backend 異常（原樣透傳）

        行為：
        - target_phase=Archived → patch_status 標記 archived
        - target_phase=Deleted → patch_status（如需） + delete
        """
        current_phase = memory.status.phase.value if memory.status and memory.status.phase else None

        if (current_phase, target_phase) not in _GC_LEGAL_TRANSITIONS:
            MEMORY_GC_CLEANED_TOTAL.labels(gc_state="skipped").inc()
            raise ValueError(
                f"Illegal GC transition: {current_phase} → {target_phase} "
                f"(allowed: {sorted(_GC_LEGAL_TRANSITIONS)})"
            )

        if target_phase == "Deleted":
            # 直接刪除（冪等：deleted=False 表示 key 不存在）
            await self._backend.delete(memory.metadata.namespace, memory.metadata.name)
            MEMORY_GC_CLEANED_TOTAL.labels(gc_state="deleted").inc()
            return "Deleted"

        # 標記 Archived（不刪除）
        archived_status: dict[str, str] = {"phase": "Archived"}
        await self._backend.patch_status(
            memory.metadata.namespace,
            memory.metadata.name,
            archived_status,
            expected_generation=memory.metadata.generation,
        )
        MEMORY_GC_CLEANED_TOTAL.labels(gc_state="marked").inc()
        return "Archived"


__all__ = [
    "GCState",
    "MemoryGCService",
]
