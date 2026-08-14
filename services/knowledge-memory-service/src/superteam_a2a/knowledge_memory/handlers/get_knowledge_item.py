"""JSON-RPC getKnowledgeItem handler · thin wrapper · superseded_by chain 接线（PR-4c 實装）。

PR-4b plan §2.1 + §2.4：

handler 職責（SRP）：
- 解析 request["params"]["item_ref"] dict → ItemReference
- 委託 item_service.get_item(item_ref, context) → KnowledgeItem | None
- 序列化（item=None 表示 not found）
- 錯誤碼映射（KnowledgeError → JSON-RPC error.code）

業務邏輯：
- superseded_by chain 遍歷（獲取當前最新版 KnowledgeItem）推 PR-4c 實装
- PR-4b KnowledgeItemService stub 返回 None（保持 service 接口可用）

PR-4c ASGI server 將 starlette Route handler 綁定到此函數：
    async def get_knowledge_item_route(request: Request) -> Response:
        body = await request.json()
        context = InProcessContext(clock=..., trace_id=...)
        result = await get_knowledge_item_handler(
            request=body,
            context=context,
            item_service=app.state.knowledge_item_service,
        )
        return JSONResponse(result)

憲法 §17 SOLID：
- SRP：handler 只做 JSON-RPC 序列化 + 錯誤碼映射
- DIP：依賴 Protocol（KnowledgeItemService）
- ISP：handler 接口最小化
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from superteam_a2a.knowledge.crd.item_reference import ItemReference
from superteam_a2a.knowledge.errors.codes import KnowledgeErrorCode
from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.services.knowledge.item import KnowledgeItemService
from superteam_a2a.knowledge_memory.services.shared.wire_sync import WireSyncService


def _build_error_response(
    code: int,
    message: str,
    *,
    module: str,
    code_name: str,
) -> dict[str, Any]:
    """構造 JSON-RPC 2.0 error response（無 envelope · PR-4c envelope 裝配）。"""
    return {
        "error": {
            "code": code,
            "message": message,
            "data": {"module": module, "code_name": code_name},
        },
    }


async def get_knowledge_item_handler(
    request: dict[str, Any],
    *,
    context: InProcessContext,
    item_service: KnowledgeItemService,
) -> dict[str, Any]:
    """JSON-RPC method: getKnowledgeItem · superseded_by chain（PR-4b stub）。

    流程：
    1. 解析 request["params"]["item_ref"] dict → ItemReference
       - ValidationError → JSON-RPC error.code KNOWLEDGE_INVALID_TYPE (-32010)
    2. 委託 item_service.get_item(item_ref, context) → KnowledgeItem | None
       - PR-4b stub 返回 None（not found 語義）
       - KnowledgeError → JSON-RPC error.code from KnowledgeErrorCode.value
    3. 序列化 → result.item（None 表示 not found）

    參數：
    - request · JSON-RPC request dict（含 params.item_ref）
    - context · InProcessContext · frozen
    - item_service · KnowledgeItemService · 構造注入

    返回：
    - dict · 成功路徑：{"item": KnowledgeItem | None}
    - dict · 失敗路徑：error dict

    不變量：
    - PR-4b stub 返回 None（not found 語義，與 HTTP 404 對齊）
    - superseded_by chain 推 PR-4c 實装
    - 不重映射錯誤碼（單一來源：WireSyncService.to_json_rpc_error_code）
    """
    # Step 1: 解析 request["params"]["item_ref"] → ItemReference
    params = request.get("params", {})
    item_ref_dict = params.get("item_ref", {})
    try:
        item_ref = ItemReference.model_validate(item_ref_dict)
    except ValidationError as exc:
        return _build_error_response(
            int(KnowledgeErrorCode.KNOWLEDGE_INVALID_TYPE.value),
            f"ItemReference validation failed: {exc}",
            module="knowledge",
            code_name=KnowledgeErrorCode.KNOWLEDGE_INVALID_TYPE.name,
        )

    # Step 2: 委託 item_service.get_item（stub 行為：返回 None）
    try:
        item = await item_service.get_item(item_ref)
    except Exception as exc:
        # KnowledgeError 統一映射；其他異常 → -32603 internal_error
        return _build_error_response(
            WireSyncService.to_json_rpc_error_code(exc),
            str(exc),
            module="knowledge",
            code_name=getattr(getattr(exc, "code", None), "name", "INTERNAL_ERROR"),
        )

    # Step 3: 序列化為 JSON-RPC result 格式（item=None 表示 not found）
    if item is None:
        return {"item": None, "found": False}
    # PR-4c 實装時：item.model_dump(by_alias=True, exclude_none=True)
    return {
        "item": getattr(item, "model_dump", lambda **_: item)(by_alias=True, exclude_none=True),
        "found": True,
    }


__all__ = ["get_knowledge_item_handler"]
