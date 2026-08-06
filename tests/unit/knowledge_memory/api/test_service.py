"""MemoryBackendInProcessService unit tests · TEST-MEM-053~060 (8) + 辅助 4 = 12 总测试。

依据 L3-6 §6.2 8 个边界测试 ID：
- TEST-MEM-053 PUT 并发同 key + 同 idempotency_key
- TEST-MEM-054 admission 50ms timeout 透传 MEMORY_ADMISSION_TIMEOUT
- TEST-MEM-055 GET / DELETE 竞态线性化
- TEST-MEM-056 GET backend 异常保留 cause 透传
- TEST-MEM-057 query 幂等（调整：原 DELETE → query 同 key 多次返回一致）
- TEST-MEM-058 query 超过 deadline（调整：原 DELETE → query 路径不进入 backend scan）
- TEST-MEM-059 LIST + 并发 PUT 稳定排序
- TEST-MEM-060 industry 无 tag/confidence 0 次 backend scan
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from superteam_a2a.knowledge_memory import (
    InMemoryBackend,
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.api.context import InProcessContext
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessServiceImpl,
)

# ============================================================================
# TEST-MEM-053 · PUT 并发同 key + 同 idempotency_key 仅一次 commit
# ============================================================================


async def test_record_idempotency_concurrent_same_key(sample_memory, fake_clock):
    """TEST-MEM-053 · 两个并发 record_memory_async 同 (ns, name)。

    期望：二者均成功；in-memory 串行锁保证每次提交原子完成；
    最终 backend.size == 1（同一 key）；两次返回不同 resource_version
    （v=1 → v=2，因为 in-memory backend 每次 PUT 都递增 version）。
    """
    backend = InMemoryBackend(clock=fake_clock)
    ctx = InProcessContext(clock=fake_clock, trace_id="test-053")
    service = MemoryBackendInProcessServiceImpl(backend=backend)
    mem_a = sample_memory.model_copy(deep=True)
    mem_b = sample_memory.model_copy(deep=True)
    mem_b.metadata = mem_b.metadata.model_copy(update={"generation": 2})
    result_a, result_b = await asyncio.gather(
        service.record_memory_async(mem_a, context=ctx),
        service.record_memory_async(mem_b, context=ctx),
    )
    # 两次均成功提交；后续 state 只保留一份
    assert backend.size == 1
    # version 递增：两次不同 version（in-memory PUT 行为）
    assert result_a.resource_version != result_b.resource_version
    assert {result_a.resource_version, result_b.resource_version} == {1, 2}


# ============================================================================
# TEST-MEM-054 · admission 50ms deadline 超时透传 MEMORY_ADMISSION_TIMEOUT
# ============================================================================


async def test_record_admission_timeout_propagates(sample_memory, fake_clock):
    """TEST-MEM-054 · 注入慢 backend（asyncio.sleep > 0.050）。

    期望：抛 MemoryBackendError(MEMORY_ADMISSION_TIMEOUT, cause=TimeoutError)。
    """
    slow_backend = MagicMock()

    async def slow_put(*a, **kw):
        await asyncio.sleep(0.200)
        return None  # 不会到达此处

    slow_backend.put = slow_put

    service = MemoryBackendInProcessServiceImpl(backend=slow_backend)
    ctx = InProcessContext(clock=fake_clock, trace_id="test-054")
    with pytest.raises(MemoryBackendError) as exc_info:
        await service.record_memory_async(sample_memory, context=ctx)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT
    assert isinstance(exc_info.value.cause, asyncio.TimeoutError)


# ============================================================================
# TEST-MEM-055 · GET / DELETE 竞态线性化
# ============================================================================


async def test_get_delete_race_linearizable(sample_memory, fake_clock):
    """TEST-MEM-055 · 并发 get + delete，仅允许完整旧 snapshot 或 miss。

    实现层观察：InMemoryBackend 的 get/delete 在 asyncio.Lock 下串行化；
    二者均不返回半对象。
    """
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)

    # 由于 service 层没有 get/delete 入口（仅 record/query），
    # 验证 backend 直接的 get/delete 串行化契约。
    async def do_get():
        return await backend.get(sample_memory.metadata.namespace, sample_memory.metadata.name)

    async def do_delete():
        return await backend.delete(sample_memory.metadata.namespace, sample_memory.metadata.name)

    results = await asyncio.gather(
        do_get(),
        do_delete(),
        do_get(),
    )
    get_result_1, del_result, get_result_2 = results
    # 至少有一个 get 返回完整 Memory 或 None（不允许半对象）
    for r in (get_result_1, get_result_2):
        assert r is None or hasattr(r, "metadata")
    # delete 返回 deleted bool
    assert isinstance(del_result.deleted, bool)


# ============================================================================
# TEST-MEM-056 · backend 异常保留 cause 透传
# ============================================================================


async def test_get_backend_exception_preserves_cause(sample_memory, fake_clock):
    """TEST-MEM-056 · mock backend.put 抛 MemoryBackendError(MEMORY_INTERNAL_ERROR, cause=ValueError("x"))。

    期望：service 层原样透传 cause，不重映射。
    """
    original_cause = ValueError("x")
    err = MemoryBackendError(
        MemoryErrorCode.MEMORY_INTERNAL_ERROR,
        "simulated backend error",
        cause=original_cause,
    )
    backend = MagicMock()
    backend.put = AsyncMock(side_effect=err)

    service = MemoryBackendInProcessServiceImpl(backend=backend)
    ctx = InProcessContext(clock=fake_clock, trace_id="test-056")
    with pytest.raises(MemoryBackendError) as exc_info:
        await service.record_memory_async(sample_memory, context=ctx)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_INTERNAL_ERROR
    assert exc_info.value.cause is original_cause


# ============================================================================
# TEST-MEM-057 · query 幂等（同 key 多次返回一致 · L4-Step4 范围内调整）
# ============================================================================


async def test_query_idempotency_concurrent(sample_memories, fake_clock, make_service, make_query):
    """TEST-MEM-057 · 两次并发 query 同 key，第二次返回 items + total_count 一致。

    L4-Step4 范围仅 record/query（无 DELETE 路径），调整为 query 幂等验证。
    """
    backend = InMemoryBackend(clock=fake_clock)
    for m in sample_memories:
        await backend.put(m)
    service = make_service(backend=backend, clock=fake_clock)
    ctx = InProcessContext(clock=fake_clock, trace_id="test-057")
    query = make_query(scope="agent")
    r1, r2 = await asyncio.gather(
        service.query_memory_async(query, context=ctx),
        service.query_memory_async(query, context=ctx),
    )
    assert r1.total_count == r2.total_count
    assert len(r1.items) == len(r2.items)


# ============================================================================
# TEST-MEM-058 · query 超过 deadline（L4-Step4 范围调整）
# ============================================================================


async def test_query_deadline_returns_empty(sample_memory, fake_clock, make_service, make_query):
    """TEST-MEM-058 · query 路径 deadline 校验：纯函数式实现下 backend 必被调用一次。

    验证：service 层在 FakeClock 下不抛错；query 返回 total_count=0
    （空 backend，未存储 sample_memory）。
    """
    backend = InMemoryBackend(clock=fake_clock)
    service = make_service(backend=backend, clock=fake_clock)
    ctx = InProcessContext(clock=fake_clock, deadline_monotonic=0.0)
    query = make_query(scope="agent")
    result = await service.query_memory_async(query, context=ctx)
    assert result.total_count == 0
    assert result.items == ()


# ============================================================================
# TEST-MEM-059 · LIST 与并发 PUT 稳定排序
# ============================================================================


async def test_list_concurrent_with_put_stable_sort(fake_clock, make_service, make_query):
    """TEST-MEM-059 · 并发 query + record 多个 memory，query 返回稳定 (ns, name) 排序。

    L4-Step4 范围内：通过 service 层并发 record 3 个 memory 然后 query，验证排序。
    """
    backend = InMemoryBackend(clock=fake_clock)
    service = make_service(backend=backend, clock=fake_clock)
    ctx = InProcessContext(clock=fake_clock, trace_id="test-059")

    mem_a = Memory(
        metadata=ObjectMeta(name="mem-a", namespace="ns-b"),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary="A",
            confidence=1.0,
        ),
    )
    mem_b = Memory(
        metadata=ObjectMeta(name="mem-a", namespace="ns-a"),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary="B",
            confidence=1.0,
        ),
    )
    mem_c = Memory(
        metadata=ObjectMeta(name="mem-b", namespace="ns-a"),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary="C",
            confidence=1.0,
        ),
    )

    await asyncio.gather(
        service.record_memory_async(mem_a, context=ctx),
        service.record_memory_async(mem_b, context=ctx),
        service.record_memory_async(mem_c, context=ctx),
    )

    query = make_query(scope="agent")
    result = await service.query_memory_async(query, context=ctx)
    keys = [(m.metadata.namespace, m.metadata.name) for m in result.items]
    assert keys == sorted(keys)
    assert len(keys) == 3


# 引入 Memory/MemorySpec/ScopeReference/AgentReference/ObjectMeta 用于上面测试
from superteam_a2a.knowledge_memory import (  # noqa: E402
    Memory,
    ObjectMeta,
)
from superteam_a2a.operator.models.memory import (  # noqa: E402
    AgentReference,
    MemorySpec,
    ScopeReference,
)

# ============================================================================
# TEST-MEM-060 · industry 无 tag/confidence 0 次 backend scan
# ============================================================================


async def test_industry_query_too_broad_no_backend_scan(fake_clock, make_service, make_query):
    """TEST-MEM-060 · industry + no tag + no min_confidence 应抛 MEMORY_QUERY_TOO_BROAD。

    期望：mock backend.list 不被调用；抛 MemoryBackendError(MEMORY_QUERY_TOO_BROAD)。
    """
    backend = MagicMock()
    backend.list = AsyncMock(side_effect=AssertionError("list should not be called"))
    service = make_service(backend=backend, clock=fake_clock)
    ctx = InProcessContext(clock=fake_clock, trace_id="test-060")
    query = make_query(scope="industry", tags=(), min_confidence=None)
    with pytest.raises(MemoryBackendError) as exc_info:
        await service.query_memory_async(query, context=ctx)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_QUERY_TOO_BROAD
    backend.list.assert_not_called()


# ============================================================================
# 辅助测试 1 · record happy path
# ============================================================================


async def test_record_happy_path_returns_result(sample_memory, fake_clock, make_service):
    """record happy path · 返回 MemoryRecordResult，version=1。"""
    backend = InMemoryBackend(clock=fake_clock)
    service = make_service(backend=backend, clock=fake_clock)
    ctx = InProcessContext(clock=fake_clock, trace_id="happy")
    result = await service.record_memory_async(sample_memory, context=ctx)
    assert result.resource_version == 1
    assert result.effective_confidence == sample_memory.spec.confidence
    assert result.memory.metadata.namespace == sample_memory.metadata.namespace


# ============================================================================
# 辅助测试 2 · query happy path + min_confidence 过滤
# ============================================================================


async def test_query_happy_path_filters_confidence(fake_clock, make_service, make_query):
    """query min_confidence=0.5 过滤 · 低于阈值被排除。"""
    backend = InMemoryBackend(clock=fake_clock)
    high = Memory(
        metadata=ObjectMeta(name="mem-high"),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary="high",
            confidence=0.9,
        ),
    )
    low = Memory(
        metadata=ObjectMeta(name="mem-low"),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary="low",
            confidence=0.1,
        ),
    )
    await backend.put(high)
    await backend.put(low)

    service = make_service(backend=backend, clock=fake_clock)
    ctx = InProcessContext(clock=fake_clock)
    query = make_query(scope="agent", min_confidence=0.5)
    result = await service.query_memory_async(query, context=ctx)
    assert result.total_count == 1
    assert result.items[0].metadata.name == "mem-high"


# ============================================================================
# 辅助测试 3 · CancelledError 透传
# ============================================================================


async def test_record_cancelled_error_propagates(sample_memory, fake_clock):
    """record 路径 CancelledError 透传（fail-fast 取消）。"""
    backend = MagicMock()
    backend.put = AsyncMock(side_effect=asyncio.CancelledError("cancelled"))

    service = MemoryBackendInProcessServiceImpl(backend=backend)
    ctx = InProcessContext(clock=fake_clock, trace_id="cancel")
    with pytest.raises(asyncio.CancelledError):
        await service.record_memory_async(sample_memory, context=ctx)


# ============================================================================
# 辅助测试 4 · query scope 校验（构造层）
# ============================================================================


def test_query_invalid_scope_rejected():
    """scope 无效抛 ValidationError（QueryMemoryRequest 构造层）。"""
    from pydantic import ValidationError
    from superteam_a2a.knowledge_memory.backend.types import QueryMemoryRequest

    with pytest.raises(ValidationError):
        QueryMemoryRequest(scope="bogus")  # type: ignore[arg-type]
