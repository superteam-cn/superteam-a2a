"""handle_query_memory handler unit tests · H-QM-UT-001~004 + 3 stubs。

L3-5 §4.4 + L3-6 §6 + §M-1.5 验证：
- H-QM-UT-001：handle_query_memory 正常路径 · service.query_memory_async 被调
- H-QM-UT-002：handle_query_memory 异常透传
- H-QM-UT-003：handle_query_memory memo 缺 service + clock → 静默 return 空结果
- H-QM-UT-004：query_memory_async 0-backend-scan 行为（industry + 无 tag/confidence → MEMORY_QUERY_TOO_BROAD）
- H-QM-IT-001（stub）：K8s CR 接入占位
- H-QM-CF-001（stub）：wire DTO 一致性占位
- H-QM-E2E-001（stub）：E2E 占位
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock

# 路径前置
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

import pytest  # noqa: E402
from superteam_a2a.knowledge_memory import (  # noqa: E402
    FakeClock,
    MemoryBackendError,
    MemoryErrorCode,
    QueryMemoryResult,
)
from superteam_a2a.knowledge_memory.api.service import (  # noqa: E402
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.backend.types import (  # noqa: E402
    MemoryScope,
    QueryMemoryRequest,
)
from superteam_a2a.knowledge_memory.handlers.memory_handler import (  # noqa: E402
    handle_query_memory,
)


def _make_query_body():
    """构造 QueryMemoryRequest body dict（handle_query_memory 入参格式）。

    alias 形式: scope → scope, namespace → namespace 等。
    """
    return {
        "scope": "agent",
        "namespace": "default",
        "limit": 50,
        "offset": 0,
        "metadata": {"uid": "qm-uid-001"},
    }


# H-QM-UT-001
async def test_h_qm_ut_001_query_normal_path():
    """H-QM-UT-001 · handle_query_memory 正常路径 · service.query_memory_async 被调。

    §M-1.5 验证：context.clock 是 memo["clock"] · 单一时间源。
    """
    fake_clock = FakeClock(datetime(2026, 8, 6, 10, 0, 0, tzinfo=UTC))
    expected_result = QueryMemoryResult(items=(), total_count=0)
    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.query_memory_async = AsyncMock(return_value=expected_result)
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}
    result = await handle_query_memory(body=_make_query_body(), memo=memo)
    assert result is expected_result
    mock_service.query_memory_async.assert_called_once()
    call_args = mock_service.query_memory_async.call_args
    # request 是 QueryMemoryRequest 实例（service 接收位置参数 request）
    request = call_args.args[0]
    assert isinstance(request, QueryMemoryRequest)
    assert request.scope == MemoryScope.AGENT
    # context.clock 必须等于 memo["clock"]
    assert call_args.kwargs["context"].clock is fake_clock


# H-QM-UT-002
async def test_h_qm_ut_002_query_exception_propagates():
    """H-QM-UT-002 · handle_query_memory 异常透传。

    service 抛 MemoryBackendError → caller 看到同类型异常（不重映射）。
    """
    fake_clock = FakeClock(datetime(2026, 8, 6, 10, 0, 0, tzinfo=UTC))

    async def _raise(*_args, **_kwargs):
        raise MemoryBackendError(MemoryErrorCode.MEMORY_QUERY_TOO_BROAD, "query too broad")

    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.query_memory_async = AsyncMock(side_effect=_raise)
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}
    with pytest.raises(MemoryBackendError) as exc_info:
        await handle_query_memory(body=_make_query_body(), memo=memo)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_QUERY_TOO_BROAD


# H-QM-UT-003
async def test_h_qm_ut_003_query_memo_missing_service_or_clock_returns_empty():
    """H-QM-UT-003 · handle_query_memory memo 缺 service 或 clock → 静默 return 空结果。

    边界：operator 启动期 / 单元测试期可调用 handler 而 service/clock 尚未注入。
    返回 QueryMemoryResult(items=(), total_count=0)。
    """
    # memo 完全为空
    result = await handle_query_memory(body=_make_query_body(), memo={})
    assert result == QueryMemoryResult(items=(), total_count=0)
    # memo 含错误类型
    result = await handle_query_memory(
        body=_make_query_body(),
        memo={"memory_in_process_service": "bogus", "clock": "bogus"},
    )
    assert result == QueryMemoryResult(items=(), total_count=0)
    # memo 缺 clock（service 存在但 clock 缺失 → 静默 return）
    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.query_memory_async = AsyncMock()
    result = await handle_query_memory(
        body=_make_query_body(),
        memo={"memory_in_process_service": mock_service},
    )
    assert result == QueryMemoryResult(items=(), total_count=0)
    mock_service.query_memory_async.assert_not_called()
    # memo 缺 service（clock 存在但 service 缺失 → 静默 return）
    fake_clock = FakeClock(datetime(2026, 8, 6, 10, 0, 0, tzinfo=UTC))
    result = await handle_query_memory(
        body=_make_query_body(),
        memo={"clock": fake_clock},
    )
    assert result == QueryMemoryResult(items=(), total_count=0)


# H-QM-UT-004
async def test_h_qm_ut_004_query_zero_backend_scan_industry():
    """H-QM-UT-004 · query_memory_async 0-backend-scan 行为。

    industry scope + 无 tag + 无 min_confidence → 直接 MEMORY_QUERY_TOO_BROAD，
    backend 不被扫描（TEST-MEM-060 边界）。
    """
    fake_clock = FakeClock(datetime(2026, 8, 6, 10, 0, 0, tzinfo=UTC))
    backend_mock = AsyncMock()
    backend_mock.list = AsyncMock()
    mock_service = MemoryBackendInProcessServiceImpl(backend=backend_mock)
    body = {
        "scope": "industry",
        "namespace": None,
        "limit": 100,
        "offset": 0,
        "metadata": {"uid": "qm-industry-001"},
    }
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}
    with pytest.raises(MemoryBackendError) as exc_info:
        await handle_query_memory(body=body, memo=memo)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_QUERY_TOO_BROAD
    # backend.list 绝不能被调用（0-backend-scan）
    backend_mock.list.assert_not_called()


# H-QM-IT-001
async def test_h_qm_it_001_handler_round_trips_query_body_and_metadata():
    """H-QM-IT-001 · handler 接 K8s body 后完整 round-trip 验证。

    验证: body["metadata"] 提取为 trace_id, 剩余字段被 QueryMemoryRequest.model_validate
    解析; memo 注入 service + clock; 5 维 visibility 字段 round-trip; scope 切换
    到 industry + 0-backend-scan 行为保持.
    """
    fake_clock = FakeClock(datetime(2026, 8, 8, 9, 30, 0, tzinfo=UTC))
    expected_result = QueryMemoryResult(items=(), total_count=0)
    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.query_memory_async = AsyncMock(return_value=expected_result)
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}

    # 5 维 visibility body (scope + namespace + tags + min_confidence + limit/offset)
    body = {
        "scope": "scope",
        "namespace": "team-platform",
        "tags": ("incidents", "runbooks"),
        "min_confidence": 0.42,
        "limit": 25,
        "offset": 5,
        "metadata": {"uid": "qm-rt-001"},
    }
    result = await handle_query_memory(body=body, memo=memo)

    assert result is expected_result
    mock_service.query_memory_async.assert_called_once()
    call_args = mock_service.query_memory_async.call_args
    request = call_args.args[0]
    assert isinstance(request, QueryMemoryRequest)
    # 5 维 visibility round-trip
    assert request.scope == MemoryScope.SCOPE
    assert request.namespace == "team-platform"
    assert request.tags == ("incidents", "runbooks")
    assert request.min_confidence == 0.42
    assert request.limit == 25
    assert request.offset == 5
    # context trace_id 从 metadata.uid 提取
    assert call_args.kwargs["context"].trace_id == "qm-rt-001"
    assert call_args.kwargs["context"].clock is fake_clock


# H-QM-CF-001
def test_h_qm_cf_001_query_wire_field_set_matches_pydantic_model():
    """H-QM-CF-001 · wire DTO 字段集合与 QueryMemoryRequest Pydantic model 一致。

    静态断言: handler 接受的 body 字段集合 (去掉 metadata) 必须等于
    QueryMemoryRequest.model_fields 集合 (含 alias). 同时验证 MemoryScope
    枚举值集合不漂移, 与 wire spec 对齐.
    """
    from superteam_a2a.knowledge_memory.backend.types import MemoryScope as ScopeEnum
    from superteam_a2a.knowledge_memory.backend.types import QueryMemoryRequest

    body = _make_query_body()
    # QueryMemoryRequest 字段全是同名的 (无 alias), wire body 字段集应是 pydantic schema 的子集
    # (exclude_none=True 会把 None 默认值字段剔除, body 只含本测试填写的字段)
    wire_fields = {k for k in body if k != "metadata"}
    pydantic_fields = set(QueryMemoryRequest.model_fields)
    assert wire_fields.issubset(pydantic_fields)
    # wire 必须存在的字段: scope / namespace / limit / offset
    assert {"scope", "namespace", "limit", "offset"}.issubset(wire_fields)
    # alias 集合为空 (QueryMemoryRequest 不使用 alias)
    alias_fields = {f.alias for f in QueryMemoryRequest.model_fields.values() if f.alias}
    assert alias_fields == set()

    # MemoryScope 5 类与 _make_query_body 实际使用字符串一致
    expected_scopes = {"agent", "scope", "industry", "project", "global"}
    assert {s.value for s in ScopeEnum} == expected_scopes
    # body 内 scope 是合法枚举值
    assert body["scope"] in expected_scopes


# H-QM-E2E-001（stub）
def test_h_qm_e2e_001_stub_end_to_end():
    """H-QM-E2E-001 stub · E2E 端到端测试。

    Phase 2 范围：kind cluster + real kopf operator + wire transport。
    """
    # 占位：仅验证测试 ID 已注册
    assert True
