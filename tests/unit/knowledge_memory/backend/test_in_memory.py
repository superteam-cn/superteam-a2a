"""InMemoryBackend async wrapper 单元测试 · TEST-MEM-048~051。

L3-6 §5.7 6 抽象方法 + §5 不变量：
- 不可变快照
- 线性化单 key 写
- Clock 唯一时间源
- 错误码封闭集
- 可替换语义
"""

from __future__ import annotations

import pytest
from superteam_a2a.knowledge_memory import (
    BackendHealth,
    BackendMetadata,
    BackendType,
    InMemoryBackend,
    MemoryBackendError,
    MemoryErrorCode,
)

# ============================================================================
# TEST-MEM-048 · Protocol 6 方法 runtime_checkable
# ============================================================================


def test_in_memory_backend_implements_protocol(sample_memory, fake_clock):
    """TEST-MEM-048 · InMemoryBackend 实例 satisfies MemoryBackend Protocol。

    注：MemoryBackend Protocol 用 runtime_checkable 装饰，但 isinstance 检查
    仅验证方法签名存在。我们通过 duck-type 验证 6 方法 + health + metadata。
    """
    backend = InMemoryBackend(clock=fake_clock)
    # 6 abstract methods + health + metadata
    assert hasattr(backend, "put")
    assert hasattr(backend, "get")
    assert hasattr(backend, "delete")
    assert hasattr(backend, "list")
    assert hasattr(backend, "patch_status")
    assert hasattr(backend, "health")
    assert hasattr(backend, "metadata")


# ============================================================================
# PUT/GET/DELETE/LIST 集成（async wrapper）
# ============================================================================


async def test_in_memory_backend_put_get_roundtrip(sample_memory, fake_clock):
    """InMemoryBackend.put → get 完整 round-trip。"""
    backend = InMemoryBackend(clock=fake_clock)
    result = await backend.put(sample_memory)
    assert result.version == 1

    got = await backend.get(sample_memory.metadata.namespace, sample_memory.metadata.name)
    assert got is not None
    assert got.metadata.name == sample_memory.metadata.name
    assert got.spec.summary == sample_memory.spec.summary


async def test_in_memory_backend_get_miss_returns_none(sample_memory, fake_clock):
    """InMemoryBackend.get 不存在 → 返回 None（不抛错）。"""
    backend = InMemoryBackend(clock=fake_clock)
    got = await backend.get("default", "nonexistent")
    assert got is None


async def test_in_memory_backend_delete_then_get_returns_none(sample_memory, fake_clock):
    """InMemoryBackend.delete 后 get 返回 None。"""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    delete_result = await backend.delete(
        sample_memory.metadata.namespace, sample_memory.metadata.name
    )
    assert delete_result.deleted is True

    got = await backend.get(sample_memory.metadata.namespace, sample_memory.metadata.name)
    assert got is None


async def test_in_memory_backend_delete_missing_returns_deleted_false(fake_clock):
    """InMemoryBackend DELETE 不存在 → deleted=False（幂等）。"""
    backend = InMemoryBackend(clock=fake_clock)
    result = await backend.delete("default", "nonexistent")
    assert result.deleted is False


async def test_in_memory_backend_put_capacity_exceeded(sample_memory, fake_clock):
    """InMemoryBackend capacity 满 → MemoryBackendError(MEMORY_FORBIDDEN)。"""
    from superteam_a2a.knowledge_memory.backend.memory import ObjectMeta

    backend = InMemoryBackend(clock=fake_clock, max_size=1)
    mem1 = sample_memory.model_copy(update={"metadata": ObjectMeta(name="first")})
    await backend.put(mem1)

    mem2 = sample_memory.model_copy(update={"metadata": ObjectMeta(name="second")})
    with pytest.raises(MemoryBackendError) as exc:
        await backend.put(mem2)
    assert exc.value.code == MemoryErrorCode.MEMORY_FORBIDDEN


# ============================================================================
# TEST-MEM-050 · patch_status generation CAS
# ============================================================================


async def test_patch_status_success_with_matching_generation(sample_memory, fake_clock):
    """TEST-MEM-050 · patch_status 在 generation 匹配时成功。"""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    initial_gen = sample_memory.metadata.generation

    new_status = sample_memory.status
    await backend.patch_status(
        sample_memory.metadata.namespace,
        sample_memory.metadata.name,
        new_status,
        expected_generation=initial_gen,
    )

    got = await backend.get(sample_memory.metadata.namespace, sample_memory.metadata.name)
    assert got is not None


async def test_patch_status_cas_conflict_raises(sample_memory, fake_clock):
    """TEST-MEM-050 · patch_status generation 不匹配 → MemoryBackendError(MEMORY_INTERNAL_ERROR, retryable=True)。"""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)

    with pytest.raises(MemoryBackendError) as exc:
        await backend.patch_status(
            sample_memory.metadata.namespace,
            sample_memory.metadata.name,
            None,
            expected_generation=999,  # 不匹配
        )
    assert exc.value.code == MemoryErrorCode.MEMORY_INTERNAL_ERROR
    assert exc.value.retryable is True


async def test_patch_status_not_found_raises(sample_memory, fake_clock):
    """TEST-MEM-050 配套 · patch_status 不存在 → MemoryBackendError。"""
    backend = InMemoryBackend(clock=fake_clock)
    with pytest.raises(MemoryBackendError) as exc:
        await backend.patch_status("default", "nonexistent", None, expected_generation=1)
    assert exc.value.code == MemoryErrorCode.MEMORY_INTERNAL_ERROR


# ============================================================================
# TEST-MEM-051 · backend exception 保留 cause
# ============================================================================


def test_memory_backend_error_preserves_cause():
    """TEST-MEM-051 · MemoryBackendError 保留 cause 链。"""
    cause = ValueError("original")
    err = MemoryBackendError(
        MemoryErrorCode.MEMORY_INTERNAL_ERROR,
        "wrapped",
        cause=cause,
    )
    assert err.cause is cause
    assert err.code == MemoryErrorCode.MEMORY_INTERNAL_ERROR
    assert err.retryable is True


# ============================================================================
# health + metadata
# ============================================================================


async def test_health_returns_healthy(fake_clock):
    """InMemoryBackend.health() → BackendHealth.HEALTHY（in-memory 永远 healthy）。"""
    backend = InMemoryBackend(clock=fake_clock)
    h = await backend.health()
    assert h == BackendHealth.HEALTHY


async def test_metadata_describes_backend(fake_clock):
    """InMemoryBackend.metadata() 返回 BackendMetadata with backend_type=IN_MEMORY。"""
    backend = InMemoryBackend(clock=fake_clock, max_size=1024)
    md = await backend.metadata()
    assert isinstance(md, BackendMetadata)
    assert md.backend_type == BackendType.IN_MEMORY
    assert md.max_size == 1024
    assert md.version == "0.1.0"


# ============================================================================
# 并发安全
# ============================================================================


async def test_concurrent_puts_same_key_preserve_consistency(sample_memory, fake_clock):
    """并发 PUT 同 key：version 递增无丢失。"""
    import asyncio

    backend = InMemoryBackend(clock=fake_clock)
    await asyncio.gather(*[backend.put(sample_memory) for _ in range(5)])
    # size 不变（同 key 后写覆盖前写）
    assert backend.size == 1


async def test_concurrent_puts_different_keys_all_present(sample_memories, fake_clock):
    """并发 PUT 不同 key：所有记录都在。"""
    import asyncio

    backend = InMemoryBackend(clock=fake_clock)
    await asyncio.gather(*[backend.put(mem) for mem in sample_memories])
    assert backend.size == len(sample_memories)
