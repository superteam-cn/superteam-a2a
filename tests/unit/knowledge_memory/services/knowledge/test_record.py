"""KnowledgeItemRecordService 補充測試（PR-4b plan 未明確編號，補充覆蓋）。

驗證：
1. KnowledgeItemRecordService.derive_from_memory 拋 NotImplementedError

依據 PR-4b plan §2.2 KnowledgeItemRecordService 職責。
"""

from __future__ import annotations

import pytest
from superteam_a2a.knowledge_memory.services.knowledge.record import (
    KnowledgeItemRecordService,
)


async def test_knowledge_item_record_service_derive_stub_raises() -> None:
    """KnowledgeItemRecordService.derive_from_memory stub 拋 NotImplementedError。

    期望：
    1. KnowledgeItemRecordService().derive_from_memory(memory_ref) 拋 NotImplementedError
    2. 錯誤訊息提及 PR-4a KnowledgeMemoryMutexValidator 5 步算法是實裝基礎
    """
    service = KnowledgeItemRecordService()
    with pytest.raises(NotImplementedError) as exc_info:
        await service.derive_from_memory(memory_ref={"namespace": "default", "name": "mem-1"})
    msg = str(exc_info.value)
    assert "PR-4c" in msg
    assert "KnowledgeMemoryMutexValidator" in msg


__all__ = ["test_knowledge_item_record_service_derive_stub_raises"]
