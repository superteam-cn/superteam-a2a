"""L4-Phase3 PR-1 A2A HTTP JSON-RPC server · starlette + dispatcher。

依据 docs/phase3/l4-phase3-plan.md §3 PR-1 + L3-6 §6 in-process handler 契约：
- starlette App（§2.1 选项 C · 最小依赖 + 与 kopf event loop 集成可控）
- JSON-RPC 2.0 envelope（§2.2 · Google A2A 协议官方）
- 2 端点：/jsonrpc/record_memory + /jsonrpc/query_memory（method 编码在 URL）
- /healthz：kopf liveness_endpoint 替代（PR-4.1.1 #90 共用）
- 12 MEMORY_* 错误码 → JSON-RPC error.code 1:1 映射（§5.7 不变量 4 + L3-6 §8.1 权威表）

测试 ID 12 个（4 envelope + 4 round-trip + 4 error 传播）· TEST-A2A-001~012。
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessService,
)
from superteam_a2a.knowledge_memory.backend.clock import Clock
from superteam_a2a.knowledge_memory.backend.errors import MemoryBackendError
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.types import QueryMemoryRequest
from superteam_a2a.knowledge_memory.observability import bind_metrics_to_app

# ============================================================================
# JSON-RPC 2.0 协议常量
# ============================================================================

JSONRPC_VERSION = "2.0"

# JSON-RPC 2.0 预定义错误码（spec 固定 · 不可重映射）
ERR_PARSE_ERROR = -32700
ERR_INVALID_REQUEST = -32600
ERR_METHOD_NOT_FOUND = -32601
ERR_INVALID_PARAMS = -32602
ERR_INTERNAL_ERROR = -32603


# ============================================================================
# JSON-RPC envelope helpers
# ============================================================================


def _jsonrpc_error(
    *,
    code: int,
    message: str,
    request_id: Any = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构造 JSON-RPC 2.0 error response（§2.2 envelope 严格封闭）。"""
    error_obj: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error_obj["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "error": error_obj, "id": request_id}


def _jsonrpc_result(*, result: Any, request_id: Any) -> dict[str, Any]:
    """构造 JSON-RPC 2.0 success response（§2.2 envelope 严格封闭）。"""
    return {"jsonrpc": JSONRPC_VERSION, "result": result, "id": request_id}


def _parse_envelope(raw_body: bytes) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """解析 HTTP body 为 JSON-RPC 2.0 envelope。

    返回 (parsed_envelope, None) 或 (None, error_response) 互斥对。
    parse_error / invalid_request 在 envelope 阶段统一处理。
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
    return parsed, None


# ============================================================================
# Memory record / query dispatcher
# ============================================================================


async def _handle_record_memory(
    *,
    service: MemoryBackendInProcessService,
    clock: Clock,
    params: dict[str, Any],
    request_id: Any,
) -> dict[str, Any]:
    """record_memory 端点 dispatcher · 委托 MemoryBackendInProcessServiceImpl.record_memory_async。

    契约（L3-6 §6.1 line 953-954）：
    - 输入 params: K8s wire format dict（camelCase keys · scopeRef/agentRef/decayDays）
    - 输出 result: MemoryRecordResult.model_dump(by_alias=True, mode="json")
    - 异常：MemoryBackendError 原样透传（code 不重映射）
    - ValidationError → JSON-RPC -32602 invalid params
    """
    try:
        memory = Memory.model_validate(params)
    except ValidationError as exc:
        return _jsonrpc_error(
            code=ERR_INVALID_PARAMS,
            message=f"Invalid params: {exc.error_count()} validation error(s)",
            request_id=request_id,
            data={"errors": exc.errors(include_url=False)},
        )
    context = InProcessContext(clock=clock)
    try:
        record_result = await service.record_memory_async(memory, context=context)
    except MemoryBackendError as exc:
        return _memory_error_to_jsonrpc(exc, request_id=request_id)
    dumped = record_result.model_dump(by_alias=True, mode="json")
    return _jsonrpc_result(result=dumped, request_id=request_id)


async def _handle_query_memory(
    *,
    service: MemoryBackendInProcessService,
    clock: Clock,
    params: dict[str, Any],
    request_id: Any,
) -> dict[str, Any]:
    """query_memory 端点 dispatcher · 委托 MemoryBackendInProcessServiceImpl.query_memory_async。

    契约（L3-6 §6.1 line 957）：
    - 输入 params: QueryMemoryRequest wire dict（camelCase keys · scopeRef/agentRef/decayDays）
    - 输出 result: QueryMemoryResult.model_dump(by_alias=True, mode="json")
    - 异常：MemoryBackendError 原样透传（code 不重映射）
    - ValidationError → JSON-RPC -32602 invalid params
    """
    try:
        request = QueryMemoryRequest.model_validate(params)
    except ValidationError as exc:
        return _jsonrpc_error(
            code=ERR_INVALID_PARAMS,
            message=f"Invalid params: {exc.error_count()} validation error(s)",
            request_id=request_id,
            data={"errors": exc.errors(include_url=False)},
        )
    context = InProcessContext(clock=clock)
    try:
        query_result = await service.query_memory_async(request, context=context)
    except MemoryBackendError as exc:
        return _memory_error_to_jsonrpc(exc, request_id=request_id)
    dumped = query_result.model_dump(by_alias=True, mode="json")
    return _jsonrpc_result(result=dumped, request_id=request_id)


def _memory_error_to_jsonrpc(
    exc: MemoryBackendError,
    *,
    request_id: Any,
) -> dict[str, Any]:
    """MemoryBackendError → JSON-RPC error.code 1:1 映射（L3-6 §8.1 权威错误码表）。

    12 个 MEMORY_* 错误码（IntEnum）原样作 JSON-RPC error.code（-32101 ~ -32112）。
    data 字段携带 module + code_name + retryable + cause class name（脱敏）。
    """
    code_value = int(exc.code)
    data: dict[str, Any] = {
        "module": "memory",
        "code_name": exc.code.name,
        "retryable": exc.retryable,
    }
    if exc.cause is not None:
        data["cause_type"] = type(exc.cause).__name__
    return _jsonrpc_error(
        code=code_value,
        message=exc.message,
        request_id=request_id,
        data=data,
    )


# ============================================================================
# Starlette routes
# ============================================================================


async def healthz(request: Request) -> Response:
    """GET /healthz · kopf liveness_endpoint 替代（PR-4.1.1 #90 共用）。

    返回 200 + {"status": "healthy"} · Phase 2 e2e-envtest.yml 探针期望。
    """
    return JSONResponse({"status": "healthy"})


async def jsonrpc_record_memory(request: Request) -> Response:
    """POST /jsonrpc/record_memory · JSON-RPC 2.0 envelope → record_memory_async。"""
    service: MemoryBackendInProcessService | None = getattr(
        request.app.state, "memory_service", None
    )
    clock: Clock | None = getattr(request.app.state, "clock", None)
    if service is None or clock is None:
        return JSONResponse(
            _jsonrpc_error(
                code=ERR_INTERNAL_ERROR,
                message="Internal error: memory_service or clock not configured",
                request_id=None,
            ),
            status_code=500,
        )
    raw = await request.body()
    envelope, err = _parse_envelope(raw)
    if err is not None:
        return JSONResponse(err, status_code=200)  # JSON-RPC error responses are HTTP 200
    assert envelope is not None  # _parse_envelope returns (None, err) or (envelope, None)
    request_id = envelope["id"]
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
    response = await _handle_record_memory(
        service=service, clock=clock, params=params, request_id=request_id
    )
    return JSONResponse(response, status_code=200)


async def jsonrpc_query_memory(request: Request) -> Response:
    """POST /jsonrpc/query_memory · JSON-RPC 2.0 envelope → query_memory_async。"""
    service: MemoryBackendInProcessService | None = getattr(
        request.app.state, "memory_service", None
    )
    clock: Clock | None = getattr(request.app.state, "clock", None)
    if service is None or clock is None:
        return JSONResponse(
            _jsonrpc_error(
                code=ERR_INTERNAL_ERROR,
                message="Internal error: memory_service or clock not configured",
                request_id=None,
            ),
            status_code=500,
        )
    raw = await request.body()
    envelope, err = _parse_envelope(raw)
    if err is not None:
        return JSONResponse(err, status_code=200)
    assert envelope is not None  # _parse_envelope returns (None, err) or (envelope, None)
    request_id = envelope["id"]
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
    response = await _handle_query_memory(
        service=service, clock=clock, params=params, request_id=request_id
    )
    return JSONResponse(response, status_code=200)


# ============================================================================
# App factory
# ============================================================================


def create_app(*, service: MemoryBackendInProcessService, clock: Clock) -> Starlette:
    """构造 starlette App · service + clock 注入到 app.state。

    测试入口 + main.py 装配入口。Clock 与 L3-6 §M-1.5 三方共享单实例同源。
    """
    app = Starlette(
        debug=False,
        routes=[
            Route("/healthz", healthz, methods=["GET"]),
            Route("/jsonrpc/record_memory", jsonrpc_record_memory, methods=["POST"]),
            Route("/jsonrpc/query_memory", jsonrpc_query_memory, methods=["POST"]),
        ],
    )
    app.state.memory_service = service
    app.state.clock = clock
    # L4-Phase3 PR-3：注册 /metrics GET 路由（starlette 复用 8080 端口）
    bind_metrics_to_app(app)
    return app


__all__ = [
    "ERR_INTERNAL_ERROR",
    "ERR_INVALID_PARAMS",
    "ERR_INVALID_REQUEST",
    "ERR_METHOD_NOT_FOUND",
    "ERR_PARSE_ERROR",
    "JSONRPC_VERSION",
    "create_app",
    "jsonrpc_query_memory",
    "jsonrpc_record_memory",
]
