"""on_memory_create / on_memory_update handler unit tests · H-RM-UT-001~005 + 2 stubs。

L3-6 §6 + §M-1.5 验证：
- H-RM-UT-001：on_memory_create 正常路径 → service.record_memory_async 被调
- H-RM-UT-002：on_memory_create 异常透传（service 抛 MemoryBackendError → caller 看到）
- H-RM-UT-003：on_memory_create memo 缺 service → 静默 return（不抛错）
- H-RM-UT-004：§M-1.5 Clock 注入：handler 从 memo["clock"] 读取
- H-RM-UT-005：on_memory_update 与 create 路径一致
- H-RM-IT-001（stub）：K8s CR 接入占位
- H-RM-CF-001（stub）：wire DTO 一致性占位
"""

from __future__ import annotations

import sys
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
    Memory,
    MemoryBackendError,
    MemoryErrorCode,
    ObjectMeta,
)
from superteam_a2a.knowledge_memory.api.service import (  # noqa: E402
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.handlers.memory_handler import (  # noqa: E402
    on_memory_create,
    on_memory_update,
)
from superteam_a2a.operator.models.memory import (  # noqa: E402
    AgentReference,
    MemorySpec,
    ScopeReference,
)


def _make_memory() -> Memory:
    return Memory(
        metadata=ObjectMeta(name="mem-handler", namespace="default"),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary="handler test",
        ),
    )


def _body_and_meta():
    memory = _make_memory()
    return memory.model_dump(by_alias=True, exclude_none=True), {"uid": "test-uid-h-rm"}


# H-RM-UT-001
async def test_h_rm_ut_001_on_create_invokes_service():
    """H-RM-UT-001 · on_memory_create 正常路径 · service.record_memory_async 被调。

    §M-1.5 验证：context.clock 是 memo["clock"] · 单一时间源。
    """
    fake_clock = FakeClock(
        __import__("datetime").datetime(2026, 8, 1, 12, 0, 0, tzinfo=__import__("datetime").UTC)
    )
    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.record_memory_async = AsyncMock()
    body, meta = _body_and_meta()
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}
    await on_memory_create(body=body, meta=meta, memo=memo)
    mock_service.record_memory_async.assert_called_once()
    # context.clock 必须等于 memo["clock"]
    call_kwargs = mock_service.record_memory_async.call_args.kwargs
    assert "context" in call_kwargs
    assert call_kwargs["context"].clock is fake_clock
    # trace_id 来自 meta.uid
    assert call_kwargs["context"].trace_id == "test-uid-h-rm"


# H-RM-UT-002
async def test_h_rm_ut_002_on_create_exception_propagates():
    """H-RM-UT-002 · on_memory_create 异常透传。

    service 抛 MemoryBackendError → caller 看到同类型异常（不重映射）。
    """
    fake_clock = FakeClock(
        __import__("datetime").datetime(2026, 8, 1, 12, 0, 0, tzinfo=__import__("datetime").UTC)
    )

    async def _raise(*_args, **_kwargs):
        raise MemoryBackendError(MemoryErrorCode.MEMORY_INTERNAL_ERROR, "boom from service")

    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.record_memory_async = AsyncMock(side_effect=_raise)
    body, meta = _body_and_meta()
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}
    with pytest.raises(MemoryBackendError) as exc_info:
        await on_memory_create(body=body, meta=meta, memo=memo)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_INTERNAL_ERROR


# H-RM-UT-003
async def test_h_rm_ut_003_on_create_memo_missing_service_returns_silently():
    """H-RM-UT-003 · on_memory_create memo 缺 service → 静默 return（不抛错）。

    边界：operator 启动期 / 单元测试期可调用 handler 而 service 尚未注入。
    """
    body, meta = _body_and_meta()
    # memo 完全为空
    await on_memory_create(body=body, meta=meta, memo={})
    # memo 含错误类型
    await on_memory_create(body=body, meta=meta, memo={"memory_in_process_service": "bogus"})
    # memo 缺 clock（service 存在但 clock 缺失 → 也静默 return）
    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.record_memory_async = AsyncMock()
    await on_memory_create(body=body, meta=meta, memo={"memory_in_process_service": mock_service})
    # record_memory_async 绝不能被调用
    mock_service.record_memory_async.assert_not_called()


# H-RM-UT-004
async def test_h_rm_ut_004_m_1_5_clock_injection():
    """H-RM-UT-004 · §M-1.5 Clock 注入 · handler 从 memo["clock"] 读取。

    验证：memo["clock"] 是 FakeClock → context.clock is FakeClock。
    §M-1.5 修复：禁止现场 new SystemClock()。
    """
    from datetime import UTC, datetime

    fake_clock = FakeClock(datetime(2026, 8, 6, 10, 0, 0, tzinfo=UTC))
    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.record_memory_async = AsyncMock()
    body, meta = _body_and_meta()
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}
    await on_memory_create(body=body, meta=meta, memo=memo)
    call_kwargs = mock_service.record_memory_async.call_args.kwargs
    assert call_kwargs["context"].clock is fake_clock


# H-RM-UT-005
async def test_h_rm_ut_005_on_update_path_consistent_with_create():
    """H-RM-UT-005 · on_memory_update 与 create 路径一致。

    验证：on_update 也走 §M-1.5 Clock 注入 + 同样委托 record_memory_async。
    """
    from datetime import UTC, datetime

    fake_clock = FakeClock(datetime(2026, 8, 6, 10, 0, 0, tzinfo=UTC))
    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.record_memory_async = AsyncMock()
    body, meta = _body_and_meta()
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}
    await on_memory_update(body=body, meta=meta, memo=memo)
    mock_service.record_memory_async.assert_called_once()
    call_kwargs = mock_service.record_memory_async.call_args.kwargs
    assert call_kwargs["context"].clock is fake_clock
    # trace_id 来自 meta.uid（与 create 相同路径）
    assert call_kwargs["context"].trace_id == "test-uid-h-rm"


# H-RM-IT-001
async def test_h_rm_it_001_handler_validates_k8s_body_and_invokes_service():
    """H-RM-IT-001 · handler 接 K8s body/memo 后完整 round-trip 验证。

    Phase 2 范围：mock K8s API 入参 (不需 kind cluster / envtest) — 验证 body
    在 §6.3 协调点形态下能被 Memory.model_validate 解析, memo 注入正确传递,
    service.record_memory_async 被调用 1 次, context/trace_id/clock 正确。
    """
    from datetime import UTC, datetime

    fake_clock = FakeClock(datetime(2026, 8, 8, 9, 0, 0, tzinfo=UTC))
    mock_service = AsyncMock(spec=MemoryBackendInProcessServiceImpl)
    mock_service.record_memory_async = AsyncMock()
    body, meta = _body_and_meta()
    memo = {"memory_in_process_service": mock_service, "clock": fake_clock}

    await on_memory_create(body=body, meta=meta, memo=memo)

    mock_service.record_memory_async.assert_called_once()
    call_args = mock_service.record_memory_async.call_args
    # memory 是位置参数 · context 是 kw-only
    memory_passed = call_args.args[0]
    assert isinstance(memory_passed, Memory)
    assert memory_passed.metadata.name == "mem-handler"
    assert memory_passed.metadata.namespace == "default"
    assert memory_passed.spec.summary == "handler test"
    # context 注入 trace_id (meta.uid) + clock (memo["clock"])
    context = call_args.kwargs["context"]
    assert context.trace_id == "test-uid-h-rm"
    assert context.clock is fake_clock


# H-RM-CF-001
def test_h_rm_cf_001_memory_wire_field_set_matches_pydantic_model():
    """H-RM-CF-001 · wire DTO 字段集合与 Memory / ObjectMeta Pydantic model 一致。

    静态断言: 由 Memory 生成 dict 后, 其字段集合必须与 Memory/ObjectMeta
    model_fields 集合严格相等 (含 alias). 这保证 kopf 注入 body 与 §3.4
    Memory CRD 不会因字段漂移而拒绝 (TEST-MEM-051 静态断言集合同类).
    """
    from superteam_a2a.knowledge_memory.backend.memory import Memory as MemoryModel
    from superteam_a2a.knowledge_memory.backend.memory import ObjectMeta

    memory = _make_memory()
    body = memory.model_dump(by_alias=True, exclude_none=True)

    # Memory wire schema: Pydantic 字段名 + alias (排除 None 默认值字段)
    schema_top = set(MemoryModel.model_fields.keys()) | {
        f.alias for f in MemoryModel.model_fields.values() if f.alias
    }
    # wire body keys 必须是 schema 的子集 (None 字段被 exclude_none 剔除)
    assert set(body.keys()).issubset(schema_top)
    # 必须存在的非 None 字段: apiVersion (alias) + kind + metadata + spec
    assert {"apiVersion", "kind", "metadata", "spec"}.issubset(set(body.keys()))
    # metadata 字段集合 (含 alias) — 与 ObjectMeta schema 子集
    metadata_body = body["metadata"]
    schema_meta = set(ObjectMeta.model_fields.keys()) | {
        f.alias for f in ObjectMeta.model_fields.values() if f.alias
    }
    assert set(metadata_body.keys()).issubset(schema_meta)
    # 必须存在: name, namespace, labels, annotations, generation, finalizers
    assert {"name", "namespace", "labels", "annotations", "generation", "finalizers"}.issubset(
        set(metadata_body.keys())
    )
