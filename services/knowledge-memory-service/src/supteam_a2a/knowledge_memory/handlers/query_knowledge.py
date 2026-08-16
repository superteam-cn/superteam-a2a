"""JSON-RPC queryKnowledge handler · thin wrapper · BM25 stub 接线（PR-4c 實装 BM25）。

PR-4b plan §2.1 + §2.4：

handler 職責（SRP）：
- 解析 request["params"]["query"] dict（PR-4c 升級為 BM25QueryRequest）
- 委託 knowledge_service.execute(query_dict, context) → list[KnowledgeItem]
- 序列化為 JSON-RPC result.items + total_count
- 錯誤碼映射（KnowledgeError → JSON-RPC error.code）

業務邏輯：
- BM25 倒排索引 + tokenization + TF-IDF 評分 推 PR-4c 實装
- PR-4b KnowledgeQueryService stub 返回空列表（保持 service 接口可用）

PR-4c ASGI server 將 starlette Route handler 綁定到此函數：
    async def query_knowledge_route(request: Request) -> Response:
        body = await request.json()
        context = InProcessContext(clock=..., trace_id=...)
        result = await query_knowledge_handler(
            request=body,
            context=context,
            knowledge_service=app.state.knowledge_query_service,
        )
        return JSONResponse(result)

憲法 §17 SOLID：
- SRP：handler 只做 JSON-RPC 序列化 + 錯誤碼映射
- DIP：依賴 Protocol（KnowledgeQueryService）
- ISP：handler 接口最小化
"""

from __future__ import annotations

from typing import Any

from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.services.knowledge.query import (
    KnowledgeQueryService,
)
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


async def query_knowledge_handler(
    request: dict[str, Any],
    *,
    context: InProcessContext,
    knowledge_service: KnowledgeQueryService,
) -> dict[str, Any]:
    """JSON-RPC method: queryKnowledge · BM25 scope filter（PR-4b stub）。

    流程：
    1. 提取 request["params"]["query"] dict（PR-4b 階段無 BM25 schema 強校驗）
    2. 委託 knowledge_service.execute(query_dict, context) → list[Any]
       - PR-4b stub 返回空列表
       - KnowledgeError → JSON-RPC error.code from KnowledgeErrorCode.value
    3. 序列化 → result.items + result.total_count

    參數：
    - request · JSON-RPC request dict（含 params.query）
    - context · InProcessContext · frozen
    - knowledge_service · KnowledgeQueryService · 構造注入

    返回：
    - dict · 成功路徑：{"items": [...], "total_count": N}
    - dict · 失敗路徑：error dict

    不變量：
    - PR-4b stub 返回空列表（BM25 推 PR-4c）
    - 不重映射錯誤碼（單一來源：WireSyncService.to_json_rpc_error_code）
    """
    # Step 1: 提取 query dict（PR-4b 階段不強校驗 schema · PR-4c BM25QueryRequest）
    params = request.get("params", {})
    query_dict = params.get("query", {})

    # Step 2: 委託 knowledge_service.execute（stub 行為：返回空列表）
    try:
        items = await knowledge_service.execute(query_dict)
    except Exception as exc:
        # KnowledgeError 統一映射；其他異常 → -32603 internal_error
        return _build_error_response(
            WireSyncService.to_json_rpc_error_code(exc),
            str(exc),
            module="knowledge",
            code_name=getattr(getattr(exc, "code", None), "name", "INTERNAL_ERROR"),
        )

    # Step 3: 序列化為 JSON-RPC result 格式
    return {
        "items": list(items),
        "total_count": len(items),
    }


__all__ = ["query_knowledge_handler"]
