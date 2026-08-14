"""JSON-RPC 2.0 dispatcher · 4 method 路由 + envelope 包装 + error handling。

PR-4c plan §2.1 + §2.5 · A2A spec §3.2 JSON-RPC 2.0 + PR-4b 4 handler 复用：

4 JSON-RPC methods（method 编码在 body.method 字段）：
- recordMemory       → handlers/record_memory.py:record_memory_handler（含 admission 50ms）
- queryMemory        → handlers/query_memory.py:query_memory_handler
- queryKnowledge     → handlers/query_knowledge.py:query_knowledge_handler（PR-4b stub）
- getKnowledgeItem   → handlers/get_knowledge_item.py:get_knowledge_item_handler（PR-4b stub）

JSON-RPC 2.0 envelope（A2A spec §3.2）：
- Request:    {jsonrpc: "2.0", method: <name>, params: <object>, id: <string|int|null>}
- Response:   {jsonrpc: "2.0", result: <object>, id: <same>}  (success)
- Error:      {jsonrpc: "2.0", error: {code, message, data}, id: <same>}  (error)

JSON-RPC 2.0 standard error codes：
- -32700 Parse error (invalid JSON)
- -32600 Invalid Request
- -32601 Method not found
- -32602 Invalid params
- -32603 Internal error
- -32000 to -32099 Server error (application-defined) → 23 应用错误码（PR-4a）

不变量（PR-4c §6）：
- 23 错误码范围 -32008~-32018 + -32101~-32112 通过 WireSyncService.to_json_rpc_error_code 映射
- JSON-RPC 2.0 envelope 严格（A2A spec §3.2）
- id 透传（request.id → response.id · 不重写）
- 不暴露 handler 内部异常细节（error.data 只含 module + code_name）
"""

from __future__ import annotations

import json
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse
from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.backend.clock import Clock
from superteam_a2a.knowledge_memory.handlers.get_knowledge_item import (
    get_knowledge_item_handler,
)
from superteam_a2a.knowledge_memory.handlers.query_knowledge import (
    query_knowledge_handler,
)
from superteam_a2a.knowledge_memory.handlers.query_memory import (
    query_memory_handler,
)
from superteam_a2a.knowledge_memory.handlers.record_memory import (
    record_memory_handler,
)
from superteam_a2a.knowledge_memory.services.knowledge.item import KnowledgeItemService
from superteam_a2a.knowledge_memory.services.knowledge.query import (
    KnowledgeQueryService,
)
from superteam_a2a.knowledge_memory.services.memory.query import MemoryQueryService
from superteam_a2a.knowledge_memory.services.memory.record import MemoryRecordService
from superteam_a2a.knowledge_memory.services.shared.admission import AdmissionService
from superteam_a2a.knowledge_memory.services.shared.wire_sync import WireSyncService

# ============================================================================
# JSON-RPC 2.0 协议常量（A2A spec §3.2）
# ============================================================================

JSONRPC_VERSION = "2.0"

# JSON-RPC 2.0 预定义错误码（spec 固定 · 不可重映射）
ERR_PARSE_ERROR = -32700
ERR_INVALID_REQUEST = -32600
ERR_METHOD_NOT_FOUND = -32601
ERR_INVALID_PARAMS = -32602
ERR_INTERNAL_ERROR = -32603

# 4 method 名称常量（wire JSON · 与 A2A spec §5.1 skill 一致）
METHOD_RECORD_MEMORY = "recordMemory"
METHOD_QUERY_MEMORY = "queryMemory"
METHOD_QUERY_KNOWLEDGE = "queryKnowledge"
METHOD_GET_KNOWLEDGE_ITEM = "getKnowledgeItem"

# 4 method → handler 路由表（构造注入 · 不修改 PR-4b handler）
_VALID_METHODS: frozenset[str] = frozenset(
    {
        METHOD_RECORD_MEMORY,
        METHOD_QUERY_MEMORY,
        METHOD_QUERY_KNOWLEDGE,
        METHOD_GET_KNOWLEDGE_ITEM,
    }
)


# ============================================================================
# JSON-RPC envelope helpers（A2A spec §3.2 严格）
# ============================================================================


def _jsonrpc_error(
    *,
    code: int,
    message: str,
    request_id: Any = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构造 JSON-RPC 2.0 error response（A2A spec §3.2 envelope 严格封闭）。

    Returns:
        dict with shape {"jsonrpc": "2.0", "error": {"code", "message", "data?"}, "id": request_id}
    """
    error_obj: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error_obj["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "error": error_obj, "id": request_id}


def _jsonrpc_result(*, result: Any, request_id: Any) -> dict[str, Any]:
    """构造 JSON-RPC 2.0 success response（A2A spec §3.2 envelope 严格封闭）。

    Returns:
        dict with shape {"jsonrpc": "2.0", "result": ..., "id": request_id}
    """
    return {"jsonrpc": JSONRPC_VERSION, "result": result, "id": request_id}


def _parse_envelope(
    raw_body: bytes,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """解析 HTTP body 为 JSON-RPC 2.0 envelope。

    Returns:
        (parsed_envelope, None)  成功路径
        (None, error_response)    失败路径（parse_error / invalid_request）
    """
    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        return None, _jsonrpc_error(
            code=ERR_PARSE_ERROR,
            message=f"Parse error: {exc.msg}",
            request_id=None,
        )
    if not isinstance(parsed, dict):
        return None, _jsonrpc_error(
            code=ERR_INVALID_REQUEST,
            message="Invalid Request: top-level JSON must be an object",
            request_id=None,
        )
    if parsed.get("jsonrpc") != JSONRPC_VERSION:
        return None, _jsonrpc_error(
            code=ERR_INVALID_REQUEST,
            message=f"Invalid Request: jsonrpc must be {JSONRPC_VERSION!r}",
            request_id=None,
        )
    if "id" not in parsed:
        return None, _jsonrpc_error(
            code=ERR_INVALID_REQUEST,
            message="Invalid Request: missing 'id' field",
            request_id=None,
        )
    method = parsed.get("method")
    if not isinstance(method, str):
        return None, _jsonrpc_error(
            code=ERR_INVALID_REQUEST,
            message="Invalid Request: 'method' must be a string",
            request_id=parsed.get("id"),
        )
    if method not in _VALID_METHODS:
        # method not found（spec 标准错误码 -32601）
        return None, _jsonrpc_error(
            code=ERR_METHOD_NOT_FOUND,
            message=f"Method not found: {method!r}",
            request_id=parsed.get("id"),
            data={"method": method},
        )
    return parsed, None


# ============================================================================
# 4 method dispatcher（PR-4b handler 复用 + InProcessContext 注入）
# ============================================================================


def _build_context(
    clock: Clock,
    *,
    request_id: Any,
) -> InProcessContext:
    """构造 InProcessContext（frozen · clock + trace_id）。

    trace_id 用 JSON-RPC request_id 字符串化（透传 · 便于 trace）。
    """
    trace_id = str(request_id) if request_id is not None else ""
    return InProcessContext(clock=clock, trace_id=trace_id)


def _envelope_service_unavailable(request_id: Any) -> dict[str, Any]:
    """app.state 缺 service/clock → JSON-RPC -32603 internal_error。"""
    return _jsonrpc_error(
        code=ERR_INTERNAL_ERROR,
        message="Internal error: required service or clock not configured on app.state",
        request_id=request_id,
    )


async def _dispatch_record_memory(
    *,
    request: dict[str, Any],
    record_service: MemoryRecordService,
    admission_service: AdmissionService,
    clock: Clock,
    request_id: Any,
) -> dict[str, Any]:
    """recordMemory dispatcher · 50ms admission fail-closed 透传。"""
    context = _build_context(clock, request_id=request_id)
    return await record_memory_handler(
        request=request,
        context=context,
        record_service=record_service,
        admission_service=admission_service,
    )


async def _dispatch_query_memory(
    *,
    request: dict[str, Any],
    query_service: MemoryQueryService,
    clock: Clock,
    request_id: Any,
) -> dict[str, Any]:
    """queryMemory dispatcher · scope/visibility filter。"""
    context = _build_context(clock, request_id=request_id)
    return await query_memory_handler(
        request=request,
        context=context,
        query_service=query_service,
    )


async def _dispatch_query_knowledge(
    *,
    request: dict[str, Any],
    knowledge_service: KnowledgeQueryService,
    clock: Clock,
    request_id: Any,
) -> dict[str, Any]:
    """queryKnowledge dispatcher · PR-4b stub（PR-4c BM25 替换）。"""
    context = _build_context(clock, request_id=request_id)
    return await query_knowledge_handler(
        request=request,
        context=context,
        knowledge_service=knowledge_service,
    )


async def _dispatch_get_knowledge_item(
    *,
    request: dict[str, Any],
    item_service: KnowledgeItemService,
    clock: Clock,
    request_id: Any,
) -> dict[str, Any]:
    """getKnowledgeItem dispatcher · superseded_by chain（PR-4b stub）。"""
    context = _build_context(clock, request_id=request_id)
    return await get_knowledge_item_handler(
        request=request,
        context=context,
        item_service=item_service,
    )


# ============================================================================
# POST /jsonrpc · starlette Request handler
# ============================================================================


async def jsonrpc_dispatch(request: Request) -> JSONResponse:
    """POST /jsonrpc · JSON-RPC 2.0 dispatcher。

    路由表：
    - recordMemory       → record_memory_handler（PR-4b + admission 50ms fail-closed）
    - queryMemory        → query_memory_handler（PR-4b）
    - queryKnowledge     → query_knowledge_handler（PR-4b stub · PR-4c BM25）
    - getKnowledgeItem   → get_knowledge_item_handler（PR-4b stub · PR-4c chain）

    Required app.state keys（PR-4b 装配）：
    - record_service · MemoryRecordService
    - admission_service · AdmissionService（含 AdmissionValidatorImpl）
    - query_service · MemoryQueryService
    - knowledge_query_service · KnowledgeQueryService
    - knowledge_item_service · KnowledgeItemService
    - clock · Clock

    不变量：
    - JSON-RPC error responses are HTTP 200（spec · error 通过 envelope 编码）
    - 23 错误码范围由 WireSyncService.assert_json_rpc_code_range 守卫
    - handler 异常映射通过 WireSyncService.to_json_rpc_error_code 统一（PR-4b §2.4）
    """
    raw = await request.body()
    envelope, err = _parse_envelope(raw)
    if err is not None:
        return JSONResponse(err, status_code=200)
    assert envelope is not None  # _parse_envelope returns (None, err) or (envelope, None)

    request_id = envelope["id"]
    method = envelope["method"]
    params = envelope.get("params", {})
    if not isinstance(params, dict):
        return JSONResponse(
            _jsonrpc_error(
                code=ERR_INVALID_PARAMS,
                message="Invalid params: 'params' must be a JSON object",
                request_id=request_id,
            ),
            status_code=200,
        )

    # 构造 envelope-style request dict（PR-4b handler 期望 request["params"]["..."]）
    handler_request: dict[str, Any] = {"params": params}

    clock: Clock | None = getattr(request.app.state, "clock", None)

    if method == METHOD_RECORD_MEMORY:
        record_service = getattr(request.app.state, "record_service", None)
        admission_service = getattr(request.app.state, "admission_service", None)
        if (
            record_service is None
            or admission_service is None
            or clock is None
            or not isinstance(record_service, MemoryRecordService)
            or not isinstance(admission_service, AdmissionService)
            or not isinstance(clock, Clock)
        ):
            return JSONResponse(_envelope_service_unavailable(request_id), status_code=200)
        handler_result = await _dispatch_record_memory(
            request=handler_request,
            record_service=record_service,
            admission_service=admission_service,
            clock=clock,
            request_id=request_id,
        )
    elif method == METHOD_QUERY_MEMORY:
        query_service = getattr(request.app.state, "query_service", None)
        if (
            query_service is None
            or clock is None
            or not isinstance(query_service, MemoryQueryService)
            or not isinstance(clock, Clock)
        ):
            return JSONResponse(_envelope_service_unavailable(request_id), status_code=200)
        handler_result = await _dispatch_query_memory(
            request=handler_request,
            query_service=query_service,
            clock=clock,
            request_id=request_id,
        )
    elif method == METHOD_QUERY_KNOWLEDGE:
        knowledge_service = getattr(request.app.state, "knowledge_query_service", None)
        if (
            knowledge_service is None
            or clock is None
            or not isinstance(knowledge_service, KnowledgeQueryService)
            or not isinstance(clock, Clock)
        ):
            return JSONResponse(_envelope_service_unavailable(request_id), status_code=200)
        handler_result = await _dispatch_query_knowledge(
            request=handler_request,
            knowledge_service=knowledge_service,
            clock=clock,
            request_id=request_id,
        )
    elif method == METHOD_GET_KNOWLEDGE_ITEM:
        item_service = getattr(request.app.state, "knowledge_item_service", None)
        if (
            item_service is None
            or clock is None
            or not isinstance(item_service, KnowledgeItemService)
            or not isinstance(clock, Clock)
        ):
            return JSONResponse(_envelope_service_unavailable(request_id), status_code=200)
        handler_result = await _dispatch_get_knowledge_item(
            request=handler_request,
            item_service=item_service,
            clock=clock,
            request_id=request_id,
        )
    else:
        # _parse_envelope 已守卫 method ∈ _VALID_METHODS（defensive：不应到达）
        return JSONResponse(
            _jsonrpc_error(
                code=ERR_METHOD_NOT_FOUND,
                message=f"Method not found: {method!r}",
                request_id=request_id,
            ),
            status_code=200,
        )

    # handler 返回 dict：成功路径 = result dict / 失败路径 = error dict
    if isinstance(handler_result, dict) and "error" in handler_result:
        # PR-4b handler 返回 error dict（构造失败）→ 包装 JSON-RPC envelope
        err_data = handler_result["error"]
        try:
            WireSyncService.assert_json_rpc_code_range(int(err_data["code"]))
        except Exception:
            # 不在 23 错误码范围（如 -32102 等在范围内）→ -32603 兜底
            err_data = {
                "code": ERR_INTERNAL_ERROR,
                "message": err_data.get("message", "internal error"),
                "data": err_data.get("data", {}),
            }
        return JSONResponse(
            _jsonrpc_error(
                code=int(err_data["code"]),
                message=str(err_data["message"]),
                request_id=request_id,
                data=err_data.get("data"),
            ),
            status_code=200,
        )

    return JSONResponse(
        _jsonrpc_result(result=handler_result, request_id=request_id),
        status_code=200,
    )


__all__ = [
    "ERR_INTERNAL_ERROR",
    "ERR_INVALID_PARAMS",
    "ERR_INVALID_REQUEST",
    "ERR_METHOD_NOT_FOUND",
    "ERR_PARSE_ERROR",
    "JSONRPC_VERSION",
    "METHOD_GET_KNOWLEDGE_ITEM",
    "METHOD_QUERY_KNOWLEDGE",
    "METHOD_QUERY_MEMORY",
    "METHOD_RECORD_MEMORY",
    "jsonrpc_dispatch",
]
