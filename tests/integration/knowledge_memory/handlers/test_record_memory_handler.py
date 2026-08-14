"""H-RM-IT-001 · recordMemory handler 端到端 IT 測試。

PR-4b plan §7 IT 增量：H-RM-IT-001 · recordMemory 端到端（JSON-RPC round-trip + admission pass + record_service mock）。

驗證：
1. JSON-RPC request["params"]["memory"] dict → Memory CRD model 解析
2. AdmissionService.execute 被呼叫（admission 50ms fail-closed 鏈路）
3. MemoryRecordService.execute 被呼叫並傳入正確 context
4. MemoryRecordResult 序列化為 JSON-RPC result dict
5. response 含 memory + phase + effective_confidence + resource_version
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

from superteam_a2a.knowledge_memory.api.results import MemoryRecordResult  # noqa: E402
from superteam_a2a.knowledge_memory.backend.errors import (  # noqa: E402
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.handlers.record_memory import (  # noqa: E402
    record_memory_handler,
)
from superteam_a2a.knowledge_memory.services.memory.record import (  # noqa: E402
    MemoryRecordService,
)
from superteam_a2a.knowledge_memory.services.shared.admission import (  # noqa: E402
    AdmissionService,
)


# H-RM-IT-001
async def test_record_memory_round_trip_with_admission_pass(
    sample_request_memory,
    sample_memory,
    in_process_context,
):
    """H-RM-IT-001 · recordMemory 端到端 · admission pass + record_service 委託。

    驗證：
    1. JSON-RPC request["params"]["memory"] → Memory CRD 解析（by_alias=True）
    2. AdmissionService.execute 被呼叫一次
    3. MemoryRecordService.execute 被呼叫一次 + 傳入 memory + context
    4. 返回 dict 含 memory + phase + effective_confidence + resource_version
    """
    # arrange
    expected_result = MemoryRecordResult(
        memory=sample_memory,
        phase="Active",
        effective_confidence=1.0,
        resource_version=42,
    )
    record_service = AsyncMock(spec=MemoryRecordService)
    record_service.execute.return_value = expected_result

    admission_service = AsyncMock(spec=AdmissionService)
    admission_service.execute.return_value = None  # admission pass

    # act
    response = await record_memory_handler(
        sample_request_memory,
        context=in_process_context,
        record_service=record_service,
        admission_service=admission_service,
    )

    # assert · AdmissionService.execute 被呼叫一次（含原始 memory）
    admission_service.execute.assert_awaited_once()
    admission_call_arg = admission_service.execute.await_args.args[0]
    assert admission_call_arg.metadata.name == "mem-pr4b-handler"
    assert admission_call_arg.metadata.namespace == "default"

    # assert · MemoryRecordService.execute 被呼叫一次（含 memory + context）
    record_service.execute.assert_awaited_once()
    record_call = record_service.execute.await_args
    record_call_arg = record_call.args[0]
    assert record_call_arg.metadata.name == "mem-pr4b-handler"
    record_call_ctx = record_call.kwargs.get("context")
    # execute(memory) 位置參數 · 不含 context kwarg（service.execute 構造 context 自身）
    assert record_call_ctx is None

    # assert · response 含完整 recordMemory 結果
    assert "memory" in response
    assert response["phase"] == "Active"
    assert response["effective_confidence"] == 1.0
    assert response["resource_version"] == 42
    assert response["memory"]["metadata"]["name"] == "mem-pr4b-handler"


# H-RM-IT-001a · admission 失敗路徑
async def test_record_memory_admission_failure_maps_to_error(
    sample_request_memory,
    in_process_context,
):
    """H-RM-IT-001a · recordMemory admission 失敗 → JSON-RPC error dict。

    驗證：
    1. AdmissionService.execute 拋 MemoryBackendError(MEMORY_ADMISSION_TIMEOUT)
    2. handler 捕獲異常 → 返回 error dict（非重拋）
    3. error.code = -32112（MEMORY_ADMISSION_TIMEOUT）
    4. error.data.module = "memory"
    5. error.data.code_name = "MEMORY_ADMISSION_TIMEOUT"
    """
    # arrange
    admission_service = AsyncMock(spec=AdmissionService)
    admission_service.execute.side_effect = MemoryBackendError(
        MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT,
        "admission exceeded 50ms",
    )
    record_service = AsyncMock(spec=MemoryRecordService)

    # act
    response = await record_memory_handler(
        sample_request_memory,
        context=in_process_context,
        record_service=record_service,
        admission_service=admission_service,
    )

    # assert · admission 失敗觸發
    admission_service.execute.assert_awaited_once()
    # record_service.execute 永遠不被呼叫（admission fail-closed）
    record_service.execute.assert_not_called()

    # assert · response 是 error dict
    assert "error" in response
    assert response["error"]["code"] == -32112
    assert response["error"]["data"]["module"] == "memory"
    assert response["error"]["data"]["code_name"] == "MEMORY_ADMISSION_TIMEOUT"


__all__ = [
    "test_record_memory_admission_failure_maps_to_error",
    "test_record_memory_round_trip_with_admission_pass",
]
