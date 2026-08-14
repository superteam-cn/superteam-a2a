"""H-QK-UT-003 + H-GKI-UT-001 · KnowledgeItemService stub + Protocol runtime_checkable。

驗證：
1. H-QK-UT-003 · KnowledgeItemService.get_item(item_ref) 返回 None
2. H-GKI-UT-001 · KnowledgeItemService Protocol 暴露 get_item 方法
3. KnowledgeItemRecordService.derive_from_memory 拋 NotImplementedError

依據 PR-4b plan §7 H-QK-UT-003 + H-GKI-UT-001 + Protocol stub 模式。
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.services.knowledge.item import (
    KnowledgeItemService,
    KnowledgeItemServiceProtocol,
)
from superteam_a2a.knowledge_memory.services.knowledge.record import (
    KnowledgeItemRecordService,
)


async def test_knowledge_item_service_stub_returns_none() -> None:
    """H-QK-UT-003 · KnowledgeItemService.get_item(item_ref) 返回 None。

    期望：
    1. KnowledgeItemService().get_item(item_ref) 返回 None
    2. superseded_by chain 推 PR-4c
    """
    service = KnowledgeItemService()
    result = await service.get_item(item_ref={"name": "item-1", "namespace": "default"})

    assert result is None


def test_knowledge_item_service_protocol_exists() -> None:
    """H-GKI-UT-001 · KnowledgeItemServiceProtocol 暴露 get_item 方法 + runtime_checkable。

    期望：
    1. KnowledgeItemServiceProtocol 有 get_item 方法
    2. KnowledgeItemService 實例通過 isinstance 檢查
    """
    service = KnowledgeItemService()
    # runtime_checkable 允許 isinstance 檢查
    assert isinstance(service, KnowledgeItemServiceProtocol)


async def test_knowledge_item_record_service_raises_not_implemented() -> None:
    """H-GKI-UT 補充 · KnowledgeItemRecordService.derive_from_memory 拋 NotImplementedError。

    期望：
    1. KnowledgeItemRecordService().derive_from_memory(memory_ref) 拋 NotImplementedError
    2. 錯誤訊息提及 PR-4c scope
    """
    service = KnowledgeItemRecordService()
    import pytest

    with pytest.raises(NotImplementedError) as exc_info:
        await service.derive_from_memory(memory_ref={"name": "mem-1", "namespace": "default"})
    assert "PR-4c scope" in str(exc_info.value)


__all__ = [
    "test_knowledge_item_record_service_raises_not_implemented",
    "test_knowledge_item_service_protocol_exists",
    "test_knowledge_item_service_stub_returns_none",
]
