"""JSON-RPC queryMemory handler · thin wrapper · scope/visibility filter 接线。

PR-4b plan §2.1 + §2.4：

handler 職責（SRP）：
- 解析 request["params"]["query"] dict → QueryMemoryRequest
- 委託 query_service.execute(query, context) → QueryMemoryResult
- 序列化 QueryMemoryResult.model_dump(by_alias=True, exclude_none=True)
- 錯誤碼映射（MemoryBackendError → JSON-RPC error.code）

業務邏輯（industry 預檢 / confidence 後置過濾）全部在 InProcessService.query_memory_async
（PR-4a 已實裝），service 層僅負責構造 InProcessContext 與 Prometheus Counter 注入。

PR-4c ASGI server 將 starlette Route handler 綁定到此函數：
    async def query_memory_route(request: Request) -> Response:
        body = await request.json()
        context = InProcessContext(clock=..., trace_id=...)
        result = await query_memory_handler(
            request=body,
            context=context,
            query_service=app.state.query_service,
        )
        return JSONResponse(result)

憲法 §17 SOLID：
- SRP：handler 只做 JSON-RPC 序列化 + 錯誤碼映射
- DIP：依賴 Protocol（MemoryQueryService）+ 抽象（WireSyncService）
- ISP：handler 接口最小化
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
    MemoryContractError,
)
from superteam_a2a.knowledge_memory.backend.types import QueryMemoryRequest
from superteam_a2a.knowledge_memory.services.memory.query import MemoryQueryService
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


async def query_memory_handler(
    request: dict[str, Any],
    *,
    context: InProcessContext,
    query_service: MemoryQueryService,
) -> dict[str, Any]:
    """JSON-RPC method: queryMemory · scope/visibility filter。

    流程：
    1. 解析 request["params"]["query"] dict → QueryMemoryRequest
       - ValidationError → JSON-RPC error.code MEMORY_INVALID_CONTENT (-32102)
    2. 委託 query_service.execute(query, context) → QueryMemoryResult
       - MemoryBackendError(MEMORY_QUERY_TOO_BROAD) → JSON-RPC error.code -32106
       - 其他 MemoryBackendError → JSON-RPC error.code from MemoryErrorCode.value
    3. 序列化 QueryMemoryResult.model_dump(by_alias=True, exclude_none=True)

    參數：
    - request · JSON-RPC request dict（含 params.query）
    - context · InProcessContext · frozen
    - query_service · MemoryQueryService · 構造注入

    返回：
    - dict · 成功路徑：result dict（items + total_count）
    - dict · 失敗路徑：error dict

    不變量：
    - 不重映射錯誤碼（單一來源：WireSyncService.to_json_rpc_error_code）
    - service 異常原樣透傳到 handler 邊界後由 handler 映射
    """
    # Step 1: 解析 request["params"]["query"] → QueryMemoryRequest
    params = request.get("params", {})
    query_dict = params.get("query", {})
    try:
        query = QueryMemoryRequest.model_validate(query_dict)
    except ValidationError as exc:
        from superteam_a2a.knowledge_memory.backend.errors import MemoryErrorCode

        return _build_error_response(
            int(MemoryErrorCode.MEMORY_INVALID_CONTENT.value),
            f"QueryMemoryRequest validation failed: {exc}",
            module="memory",
            code_name=MemoryErrorCode.MEMORY_INVALID_CONTENT.name,
        )

    # Step 2: 委託 query_service.execute
    try:
        result = await query_service.execute(query)
    except (MemoryBackendError, MemoryContractError) as exc:
        return _build_error_response(
            WireSyncService.to_json_rpc_error_code(exc),
            exc.message,
            module=exc.data.get("module", "memory"),
            code_name=exc.data.get("code_name", exc.code.name),
        )

    # Step 3: 序列化 QueryMemoryResult
    return result.model_dump(by_alias=True, exclude_none=True)


__all__ = ["query_memory_handler"]
