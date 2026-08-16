"""JSON-RPC recordMemory handler · thin wrapper · 含 admission 50ms fail-closed 接线。

PR-4b plan §2.1 + §2.3 + §2.4：

handler 職責（SRP）：
- 解析 request["params"]["memory"] dict → Memory CRD model
- 委託 admission_service.execute(memory) · 50ms fail-closed（PR-4a AdmissionValidatorImpl）
- 委託 record_service.execute(memory, context) → MemoryRecordResult
- 序列化 MemoryRecordResult.model_dump(by_alias=True, exclude_none=True)
- 錯誤碼映射（MemoryBackendError/KnowledgeError → JSON-RPC error.code）

業務邏輯（凍結 / 5 步契約 / 並行控制）全部在 service 層（Subagent 1 實裝）。
handler 不持有業務狀態、不引入新 timeout 邏輯、不重映射錯誤碼（單一來源原則）。

PR-4c ASGI server 將 starlette Route handler 綁定到此函數：
    async def record_memory_route(request: Request) -> Response:
        body = await request.json()
        context = InProcessContext(clock=..., trace_id=...)
        result = await record_memory_handler(
            request=body,
            context=context,
            record_service=app.state.record_service,
            admission_service=app.state.admission_service,
        )
        return JSONResponse(result)

憲法 §17 SOLID：
- SRP：handler 只做 JSON-RPC 序列化 + 錯誤碼映射
- DIP：依賴 Protocol（MemoryRecordService）+ 抽象（WireSyncService）
- ISP：handler 接口最小化（request + context + service → response）
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
    MemoryContractError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.services.memory.record import MemoryRecordService
from superteam_a2a.knowledge_memory.services.shared.admission import AdmissionService
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


async def record_memory_handler(
    request: dict[str, Any],
    *,
    context: InProcessContext,
    record_service: MemoryRecordService,
    admission_service: AdmissionService,
) -> dict[str, Any]:
    """JSON-RPC method: recordMemory · 含 admission 50ms fail-closed。

    流程：
    1. 解析 request["params"]["memory"] dict → Memory CRD model
       - ValidationError → JSON-RPC error.code MEMORY_INVALID_CONTENT (-32102)
    2. 委託 admission_service.execute(memory) · 50ms fail-closed
       - MemoryBackendError(MEMORY_ADMISSION_TIMEOUT) → JSON-RPC error.code -32112
       - KnowledgeError → JSON-RPC error.code from KnowledgeErrorCode.value
    3. 委託 record_service.execute(memory, context) → MemoryRecordResult
       - MemoryBackendError → JSON-RPC error.code from MemoryErrorCode.value
    4. 序列化 MemoryRecordResult.model_dump(by_alias=True, exclude_none=True)

    參數：
    - request · JSON-RPC request dict（含 params.memory）
    - context · InProcessContext · frozen 含 clock + trace_id
    - record_service · MemoryRecordService · 構造注入
    - admission_service · AdmissionService · 構造注入（含 AdmissionValidatorImpl）

    返回：
    - dict · 成功路徑：result dict（memory + phase + effective_confidence + resource_version）
    - dict · 失敗路徑：error dict（code + message + data.module + data.code_name）

    異常：
    - 不主動重拋異常；所有 service 異常都被捕獲並映射到 error dict

    不變量：
    - 50ms fail-closed 單一來源在 AdmissionValidatorImpl（service.execute 內）
    - handler 不引入新 timeout 邏輯（單一職責）
    - 錯誤碼通過 WireSyncService.to_json_rpc_error_code 統一映射
    """
    # Step 1: 解析 request["params"]["memory"] → Memory CRD
    params = request.get("params", {})
    memory_dict = params.get("memory", {})
    try:
        memory = Memory.model_validate(memory_dict)
    except ValidationError as exc:
        # 入參校驗失敗 → MEMORY_INVALID_CONTENT (-32102)
        return _build_error_response(
            int(MemoryErrorCode.MEMORY_INVALID_CONTENT.value),
            f"Memory model validation failed: {exc}",
            module="memory",
            code_name=MemoryErrorCode.MEMORY_INVALID_CONTENT.name,
        )

    # Step 2: admission 校驗（50ms fail-closed · 委託 AdmissionValidatorImpl）
    try:
        await admission_service.execute(memory)
    except MemoryBackendError as exc:
        return _build_error_response(
            int(exc.code.value),
            exc.message,
            module=exc.data.get("module", "memory"),
            code_name=exc.data.get("code_name", exc.code.name),
        )

    # Step 3: 委託 record_service.execute（含 5 步契約）
    try:
        result = await record_service.execute(memory)
    except (MemoryBackendError, MemoryContractError) as exc:
        return _build_error_response(
            WireSyncService.to_json_rpc_error_code(exc),
            exc.message,
            module=exc.data.get("module", "memory"),
            code_name=exc.data.get("code_name", exc.code.name),
        )

    # Step 4: 序列化 MemoryRecordResult
    return result.model_dump(by_alias=True, exclude_none=True)


__all__ = ["record_memory_handler"]
