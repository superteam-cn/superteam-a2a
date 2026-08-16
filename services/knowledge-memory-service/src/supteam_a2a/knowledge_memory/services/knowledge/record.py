"""KnowledgeItemRecordService · Protocol stub · KnowledgeItem 派生實裝推 PR-4c。

依據 PR-4b plan §1 明確剔除：
- ❌ KnowledgeItem 派生業務邏輯（從 Memory 派生 KnowledgeItem）→ PR-4c

PR-4a 已實裝 KnowledgeMemoryMutexValidator 5 步算法（內容哈希 + agent 互斥）
是 KnowledgeItem 派生的實裝基礎，PR-4c 將基於該算法完成 KnowledgeItem 派生。

ISP：Protocol 僅暴露 derive_from_memory 方法。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class KnowledgeItemRecordServiceProtocol(Protocol):
    """KnowledgeItem 派生 Protocol · ISP 最小接口。"""

    async def derive_from_memory(
        self,
        memory_ref: Any,
    ) -> Any:  # KnowledgeItem
        ...


class KnowledgeItemRecordService:
    """KnowledgeItemRecordService stub · PR-4b 階段實裝。

    行為：
    - derive_from_memory 接收 memory_ref（Memory 引用）
    - 拋 NotImplementedError（PR-4b 明確剔除 · PR-4c 實裝派生邏輯）

    PR-4c 實裝要點：
    1. 通過 memory_ref 從 backend 獲取 Memory 頂層 CRD
    2. 調用 KnowledgeMemoryMutexValidator.validate_ki_memory_mutex（PR-4a 已實裝 5 步算法）
    3. 構造 KnowledgeItem（從 Memory.spec.content + summary + scope_ref）
    4. 寫入 BM25 索引
    """

    async def derive_from_memory(
        self,
        memory_ref: Any,
    ) -> Any:
        """從 Memory 派生 KnowledgeItem · PR-4b stub 拋 NotImplementedError。

        參數：
        - memory_ref · Memory 引用（含 namespace / name）

        返回：
        - Any · KnowledgeItem（PR-4c 實裝）

        異常：
        - NotImplementedError · PR-4b 明確剔除業務邏輯

        PR-4a 已實裝的 KnowledgeMemoryMutexValidator 5 步算法（位於
        handlers/admission_validator.py）是本 service PR-4c 實裝的基礎。
        """
        raise NotImplementedError(
            "KnowledgeItemRecordService.derive_from_memory is PR-4c scope "
            "(PR-4a KnowledgeMemoryMutexValidator 5 步算法是實裝基礎)"
        )


__all__ = [
    "KnowledgeItemRecordService",
    "KnowledgeItemRecordServiceProtocol",
]
