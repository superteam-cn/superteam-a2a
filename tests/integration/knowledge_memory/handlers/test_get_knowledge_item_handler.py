"""H-GKI-IT-001 · getKnowledgeItem handler 端到端 IT 測試。

PR-4b plan §7 IT 增量：H-GKI-IT-001 · getKnowledgeItem 端到端（JSON-RPC round-trip + superseded_by chain stub not found）。

驗證：
1. JSON-RPC request["params"]["item_ref"] dict → ItemReference 解析
2. KnowledgeItemService.get_item stub 返回 None（PR-4b stub 行為）
3. handler 序列化 → {"item": None, "found": False}
4. 不拋 NotImplementedError（保持 service 接口可用 · PR-4c 替換實裝）
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

# 路径前置
_REPO_ROOT = Path(__file__).resolve().parents[5]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory.handlers.get_knowledge_item import (  # noqa: E402
    get_knowledge_item_handler,
)
from superteam_a2a.knowledge_memory.services.knowledge.item import (  # noqa: E402
    KnowledgeItemService,
)


# H-GKI-IT-001
async def test_get_knowledge_item_round_trip_with_not_found(
    sample_request_get_item,
    in_process_context,
):
    """H-GKI-IT-001 · getKnowledgeItem 端到端 · stub 返回 not found。

    驗證：
    1. request["params"]["item_ref"] dict → ItemReference 解析（name + version）
    2. KnowledgeItemService.get_item stub 返回 None（PR-4b stub 行為）
    3. handler 序列化 → {"item": None, "found": False}
    4. 不拋 NotImplementedError（保持 service 接口可用）
    """
    # arrange · KnowledgeItemService stub 返回 None（not found 語義）
    item_service = AsyncMock(spec=KnowledgeItemService)
    item_service.get_item.return_value = None

    # act
    response = await get_knowledge_item_handler(
        sample_request_get_item,
        context=in_process_context,
        item_service=item_service,
    )

    # assert · service.get_item 被呼叫一次 + 傳入 ItemReference
    item_service.get_item.assert_awaited_once()
    item_ref_passed = item_service.get_item.await_args.args[0]
    assert item_ref_passed.name == "ki-stub"
    assert item_ref_passed.version == 1

    # assert · response 是 result dict（非 error）· 404-like 語義
    assert "item" in response
    assert response["item"] is None
    assert response["found"] is False
    assert "error" not in response


__all__ = [
    "test_get_knowledge_item_round_trip_with_not_found",
]
