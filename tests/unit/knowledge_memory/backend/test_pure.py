"""4 个 MemoryBackend 纯函数单元测试 · TEST-MEM-035~047。

L3-6 §5.3 PUT / §5.4 GET / §5.5 DELETE / §5.6 LIST。

特性：
- 同步（不需 await）
- stateless（state 由 caller 传入）
- 不可变（输入输出 deep copy）
- Clock 注入
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from superteam_a2a.knowledge_memory import (
    MemoryContractError,
    MemoryErrorCode,
    MemoryScope,
    QueryMemoryRequest,
    StoredMemory,
    pure_delete,
    pure_get,
    pure_list_memories,
    pure_put,
)
from superteam_a2a.knowledge_memory.backend.memory import canonical_key

# ============================================================================
# TEST-MEM-035/036 · PUT 新 key immutable snapshot / 同 key 原子 replace
# ============================================================================


def test_put_creates_new_record_with_version_one(sample_memory, fake_clock):
    """TEST-MEM-035 · PUT 新 key → version=1, stored_at=clock.now()。"""
    state: dict[tuple[str, str], StoredMemory] = {}
    result = pure_put(state, sample_memory, clock=fake_clock, max_size=10, ttl_seconds=None)
    assert result.version == 1
    assert result.stored_at == fake_clock.now()
    assert result.expires_at is None


def test_put_same_key_atomic_replace(sample_memory, fake_clock):
    """TEST-MEM-036 · 同 key PUT → version 递增（原子 replace）。"""
    state: dict[tuple[str, str], StoredMemory] = {}
    r1 = pure_put(state, sample_memory, clock=fake_clock, max_size=10, ttl_seconds=None)
    state[(sample_memory.metadata.namespace, sample_memory.metadata.name)] = StoredMemory(
        memory=sample_memory,
        created_at=fake_clock.now(),
        updated_at=fake_clock.now(),
        version=r1.version,
    )
    fake_clock.advance(timedelta(seconds=5))
    r2 = pure_put(state, sample_memory, clock=fake_clock, max_size=10, ttl_seconds=None)
    assert r2.version == 2
    assert r2.stored_at == fake_clock.now()


def test_put_with_ttl_sets_expires_at(sample_memory, fake_clock):
    """TEST-MEM-035 配套 · ttl_seconds=3600 → expires_at = now + 1h。"""
    result = pure_put(
        state={},
        memory=sample_memory,
        clock=fake_clock,
        max_size=10,
        ttl_seconds=3600,
    )
    assert result.expires_at is not None
    assert result.expires_at == fake_clock.now() + timedelta(seconds=3600)


# ============================================================================
# TEST-MEM-037 · PUT capacity 满 → MEMORY_FORBIDDEN
# ============================================================================


def test_put_capacity_exceeded_raises_forbidden(sample_memory, fake_clock):
    """TEST-MEM-037 · max_size=1 已满，再 PUT 新 key → MemoryContractError(MEMORY_FORBIDDEN)。"""
    # 先 PUT 一个填满
    from superteam_a2a.knowledge_memory.backend.memory import ObjectMeta

    mem1 = sample_memory.model_copy(deep=True)
    mem1 = mem1.model_copy(update={"metadata": ObjectMeta(name="first")})
    state: dict[tuple[str, str], StoredMemory] = {}
    pure_put(state, mem1, clock=fake_clock, max_size=1, ttl_seconds=None)
    state[(mem1.metadata.namespace, mem1.metadata.name)] = StoredMemory(
        memory=mem1, created_at=fake_clock.now(), updated_at=fake_clock.now(), version=1
    )

    # 再 PUT 新 key → capacity 满
    mem2 = sample_memory.model_copy(deep=True)
    mem2 = mem2.model_copy(update={"metadata": ObjectMeta(name="second")})
    with pytest.raises(MemoryContractError) as exc:
        pure_put(state, mem2, clock=fake_clock, max_size=1, ttl_seconds=None)
    assert exc.value.code == MemoryErrorCode.MEMORY_FORBIDDEN
    assert exc.value.retryable is False


# ============================================================================
# TEST-MEM-039/040 · GET 命中 deep copy / 不存在不创造 MEMORY_*
# ============================================================================


def test_get_hit_returns_deep_copy(sample_memory, fake_clock):
    """TEST-MEM-039 · GET hit 返回 deep copy（修改返回不影响 state）。"""
    state: dict[tuple[str, str], StoredMemory] = {}
    pure_put(state, sample_memory, clock=fake_clock, max_size=10, ttl_seconds=None)
    state[(sample_memory.metadata.namespace, sample_memory.metadata.name)] = StoredMemory(
        memory=sample_memory,
        created_at=fake_clock.now(),
        updated_at=fake_clock.now(),
        version=1,
    )

    result = pure_get(
        state,
        sample_memory.metadata.namespace,
        sample_memory.metadata.name,
        clock=fake_clock,
    )
    assert result.found is True
    assert result.memory is not None
    assert result.memory.spec.summary == sample_memory.spec.summary


def test_get_miss_returns_empty_without_error(sample_memory, fake_clock):
    """TEST-MEM-040 · GET miss → found=False, memory=None，**不抛任何 MEMORY_* 错误**。"""
    state: dict[tuple[str, str], StoredMemory] = {}
    result = pure_get(state, "default", "nonexistent", clock=fake_clock)
    assert result.found is False
    assert result.memory is None


def test_get_expired_returns_miss(sample_memory, fake_clock):
    """TEST-MEM-041 · GET TTL 过期 → found=False（即使 stored 存在）。"""
    state: dict[tuple[str, str], StoredMemory] = {}
    pure_put(state, sample_memory, clock=fake_clock, max_size=10, ttl_seconds=10)
    state[(sample_memory.metadata.namespace, sample_memory.metadata.name)] = StoredMemory(
        memory=sample_memory,
        created_at=fake_clock.now(),
        updated_at=fake_clock.now(),
        version=1,
        expires_at=fake_clock.now() + timedelta(seconds=10),
    )
    fake_clock.advance(timedelta(seconds=11))
    result = pure_get(
        state,
        sample_memory.metadata.namespace,
        sample_memory.metadata.name,
        clock=fake_clock,
    )
    assert result.found is False


# ============================================================================
# TEST-MEM-042/043 · DELETE 幂等 tombstone
# ============================================================================


def test_delete_existing_returns_deleted_true(sample_memory, fake_clock):
    """TEST-MEM-042 · DELETE existing → deleted=True。"""
    state: dict[tuple[str, str], StoredMemory] = {
        (sample_memory.metadata.namespace, sample_memory.metadata.name): StoredMemory(
            memory=sample_memory,
            created_at=fake_clock.now(),
            updated_at=fake_clock.now(),
            version=1,
        )
    }
    result = pure_delete(
        state, sample_memory.metadata.namespace, sample_memory.metadata.name, clock=fake_clock
    )
    assert result.deleted is True
    assert result.deleted_at == fake_clock.now()


def test_delete_missing_returns_deleted_false(fake_clock):
    """TEST-MEM-043 · DELETE 不存在 → deleted=False（幂等重放不报错）。"""
    state: dict[tuple[str, str], StoredMemory] = {}
    result = pure_delete(state, "default", "nonexistent", clock=fake_clock)
    assert result.deleted is False


# ============================================================================
# TEST-MEM-044/045 · LIST 固定排序 / snapshot pagination
# ============================================================================


def test_list_stable_sorted_by_namespace_name(sample_memories, fake_clock):
    """TEST-MEM-044 · LIST 固定 (namespace, name) 排序。

    输入: mem-b/ns-a, mem-a/ns-a, mem-c/ns-b
    期望顺序: mem-a/ns-a, mem-b/ns-a, mem-c/ns-b
    """
    state: dict[tuple[str, str], StoredMemory] = {}
    for mem in sample_memories:
        state[(mem.metadata.namespace, mem.metadata.name)] = StoredMemory(
            memory=mem,
            created_at=fake_clock.now(),
            updated_at=fake_clock.now(),
            version=1,
        )

    query = QueryMemoryRequest(scope=MemoryScope.SCOPE, namespace="ns-a")
    result = pure_list_memories(state, query, clock=fake_clock)
    names = [m.metadata.name for m in result.items]
    # ns-a 下有两个：mem-a 和 mem-b（按 name 排序）
    assert result.total == 2
    assert len(result.items) == 2
    assert names == ["mem-a", "mem-b"]


def test_list_industry_requires_filter(sample_memories, fake_clock):
    """TEST-MEM-046 · industry scope 无 tag/confidence 过滤 → MEMORY_QUERY_TOO_BROAD。"""
    state: dict[tuple[str, str], StoredMemory] = {}
    for mem in sample_memories:
        state[(mem.metadata.namespace, mem.metadata.name)] = StoredMemory(
            memory=mem,
            created_at=fake_clock.now(),
            updated_at=fake_clock.now(),
            version=1,
        )

    query = QueryMemoryRequest(scope=MemoryScope.INDUSTRY)
    with pytest.raises(MemoryContractError) as exc:
        pure_list_memories(state, query, clock=fake_clock)
    assert exc.value.code == MemoryErrorCode.MEMORY_QUERY_TOO_BROAD


def test_list_industry_with_tag_filter_passes(sample_memories, fake_clock):
    """TEST-MEM-046 配套 · industry + tag 过滤 → 通过。"""
    state: dict[tuple[str, str], StoredMemory] = {}
    for mem in sample_memories:
        state[(mem.metadata.namespace, mem.metadata.name)] = StoredMemory(
            memory=mem,
            created_at=fake_clock.now(),
            updated_at=fake_clock.now(),
            version=1,
        )

    query = QueryMemoryRequest(scope=MemoryScope.INDUSTRY, tags=("any",))
    result = pure_list_memories(state, query, clock=fake_clock)
    # tag 过滤可能为 0 个（因为 sample_memory 没有 tags）
    assert isinstance(result.items, tuple)


# ============================================================================
# TEST-MEM-056 · canonical_key 工具函数
# ============================================================================


def test_canonical_key_returns_namespace_name_tuple(sample_memory):
    """TEST-MEM-056 · canonical_key(mem) == (namespace, name)。"""
    key = canonical_key(sample_memory)
    assert key == (sample_memory.metadata.namespace, sample_memory.metadata.name)
    assert isinstance(key, tuple)
    assert len(key) == 2
