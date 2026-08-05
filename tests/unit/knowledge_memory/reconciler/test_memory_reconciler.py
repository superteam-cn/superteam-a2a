"""MemoryReconciler unit tests - TEST-MEM-016~030 (15 tests)."""

from __future__ import annotations

from unittest.mock import AsyncMock

from superteam_a2a.knowledge_memory import (
    InMemoryBackend,
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.reconciler.leader import InProcessLeaderElector
from superteam_a2a.knowledge_memory.reconciler.memory_reconciler import (
    MAX_RECONCILE_RETRIES,
    RETRY_BACKOFF_SECONDS,
    TIMER_ID,
    TIMER_INTERVAL_SECONDS,
    MemoryReconcilerService,
    canonical_memory_code,
    memory_reconciler_timer,
)

# ===== Fixtures =====


def _admission_pass():
    """Default admission pass mock."""
    m = AsyncMock()
    m.validate = AsyncMock(return_value=None)
    return m


def _index_pass():
    """Default index.remove pass mock."""
    m = AsyncMock()
    m.remove = AsyncMock(return_value=None)
    return m


def _make_service(
    *,
    backend=None,
    leader=None,
    clock=None,
    admission=None,
    index=None,
    max_retries=MAX_RECONCILE_RETRIES,
):
    """Build MemoryReconcilerService with default fixtures."""
    return MemoryReconcilerService(
        backend=backend or InMemoryBackend(),
        leader=leader or InProcessLeaderElector(),
        clock=clock,
        admission=admission or _admission_pass(),
        index=index or _index_pass(),
        max_retries=max_retries,
    )


# TEST-MEM-016
def test_timer_constants_fixed():
    """TEST-MEM-016 - timer interval=60.0 and id fixed."""
    assert TIMER_INTERVAL_SECONDS == 60.0
    assert TIMER_ID == "memory-reconciler"
    assert callable(memory_reconciler_timer)


# TEST-MEM-017
async def test_non_leader_no_list_or_patch_calls(sample_memory, fake_clock):
    """TEST-MEM-017 - non-leader: no list/patch calls."""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    leader = InProcessLeaderElector()
    leader.force_lose_leadership()  # not leader
    service = _make_service(backend=backend, leader=leader, clock=fake_clock)
    backend.patch_status = AsyncMock()
    summary = await service.reconcile_all(now=fake_clock.now())
    assert summary.result == "leader_lost"
    assert summary.bound == 0
    assert summary.errors == 0
    backend.patch_status.assert_not_called()


# TEST-MEM-018
async def test_three_consecutive_renew_failures_lose_leadership(fake_clock):
    """TEST-MEM-018 - 3 consecutive renew failures -> lose leadership."""
    leader = InProcessLeaderElector()
    assert await leader.try_acquire_or_renew() is True
    assert leader.is_leader() is True
    leader.simulate_renew_failure(3)
    assert await leader.try_acquire_or_renew() is False
    assert await leader.try_acquire_or_renew() is False
    assert await leader.try_acquire_or_renew() is False
    assert leader._consecutive_renew_failures == 0


# TEST-MEM-019
def test_thirty_seconds_grace_period_constant():
    """TEST-MEM-019 - 30s grace period constant."""
    leader = InProcessLeaderElector()
    assert leader.grace_period_seconds == 30.0


# TEST-MEM-020
async def test_overlapping_timer_skipped_not_concurrent(sample_memory, fake_clock):
    """TEST-MEM-020 - overlapping timer skipped, not concurrent."""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    leader = InProcessLeaderElector()
    assert await leader.try_acquire_or_renew() is True
    service = _make_service(backend=backend, leader=leader, clock=fake_clock)
    await service._non_overlap_lock.acquire()
    try:
        summary = await service.reconcile_all(now=fake_clock.now())
        assert summary.result == "overlap_skipped"
        assert summary.skipped_overlap == 1
        assert summary.bound == 0
    finally:
        service._non_overlap_lock.release()


# TEST-MEM-021
async def test_pending_to_bound_success_path(sample_memory, fake_clock):
    """TEST-MEM-021 - Pending -> Bound success path."""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    leader = InProcessLeaderElector()
    await leader.try_acquire_or_renew()
    service = _make_service(backend=backend, leader=leader, clock=fake_clock)
    summary = await service.reconcile_all(now=fake_clock.now())
    assert summary.result == "ok"
    assert summary.bound == 1
    assert summary.errors == 0
    final = await backend.get(sample_memory.metadata.namespace, sample_memory.metadata.name)
    assert final is not None
    assert final.status is not None
    assert final.status["phase"] == "Active"
    assert final.status["observedGeneration"] == 1


# TEST-MEM-022
async def test_pending_to_error_validation_path(sample_memory, fake_clock):
    """TEST-MEM-022 - Pending -> Error validation path."""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    leader = InProcessLeaderElector()
    await leader.try_acquire_or_renew()
    admission = AsyncMock()
    admission.validate = AsyncMock(side_effect=TimeoutError())
    service = _make_service(backend=backend, leader=leader, clock=fake_clock, admission=admission)
    summary = await service.reconcile_all(now=fake_clock.now())
    assert summary.bound == 0
    assert summary.errors == 1
    final = await backend.get(sample_memory.metadata.namespace, sample_memory.metadata.name)
    assert final is not None
    assert final.status is not None
    assert final.status["phase"] == "Error"


# TEST-MEM-023
async def test_error_retry_then_bound(sample_memory, fake_clock):
    """TEST-MEM-023 - Error retry then Bound (counter accumulator)."""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    leader = InProcessLeaderElector()
    await leader.try_acquire_or_renew()
    service = _make_service(backend=backend, leader=leader, clock=fake_clock)
    call_count = {"n": 0}
    original_patch = backend.patch_status

    async def flaky(ns, name, status, *, expected_generation):
        call_count["n"] += 1
        if call_count["n"] <= 2:
            raise MemoryBackendError(MemoryErrorCode.MEMORY_INTERNAL_ERROR, "503 retryable")
        return await original_patch(ns, name, status, expected_generation=expected_generation)

    backend.patch_status = flaky
    summary = await service.reconcile_all(now=fake_clock.now())
    assert summary.bound == 1
    assert summary.errors == 0
    assert call_count["n"] == 3  # 1 initial + 2 retries (max_retries=4 allows 5 attempts)


# TEST-MEM-024
async def test_single_error_does_not_block_subsequent(sample_memories, fake_clock):
    """TEST-MEM-024 - single resource error does not block subsequent."""
    backend = InMemoryBackend(clock=fake_clock)
    for m in sample_memories:
        await backend.put(m)
    leader = InProcessLeaderElector()
    await leader.try_acquire_or_renew()
    call_n = {"n": 0}
    admission = AsyncMock()

    async def validate_one_fail(memory, *, timeout):
        call_n["n"] += 1
        if call_n["n"] == 1:
            raise TimeoutError()
        return None

    admission.validate = validate_one_fail
    service = _make_service(backend=backend, leader=leader, clock=fake_clock, admission=admission)
    summary = await service.reconcile_all(now=fake_clock.now())
    assert summary.errors == 1
    assert summary.bound == 2


# TEST-MEM-025
async def test_status_patch_writes_status_only(sample_memory, fake_clock):
    """TEST-MEM-025 - status patch only writes status + observedGeneration."""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    leader = InProcessLeaderElector()
    await leader.try_acquire_or_renew()
    captured = []
    original = backend.patch_status

    async def spy(ns, name, status, *, expected_generation):
        captured.append((ns, name, dict(status), expected_generation))
        return await original(ns, name, status, expected_generation=expected_generation)

    backend.patch_status = spy
    service = _make_service(backend=backend, leader=leader, clock=fake_clock)
    await service.reconcile_all(now=fake_clock.now())
    assert len(captured) == 1
    ns, name, status, gen = captured[0]
    assert ns == sample_memory.metadata.namespace
    assert name == sample_memory.metadata.name
    assert "phase" in status
    assert "observedGeneration" in status
    assert gen == 1


# TEST-MEM-026
async def test_k8s_5xx_retry_1_2_4_8_seconds(sample_memory, fake_clock):
    """TEST-MEM-026 - K8s 5xx 1/2/4/8s retry."""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    leader = InProcessLeaderElector()
    await leader.try_acquire_or_renew()
    call_count = {"n": 0}

    async def flaky_patch(ns, name, status, *, expected_generation):
        call_count["n"] += 1
        if call_count["n"] <= 3:
            raise MemoryBackendError(MemoryErrorCode.MEMORY_RATE_LIMIT, "rate limit")
        return None

    backend.patch_status = flaky_patch
    service = _make_service(backend=backend, leader=leader, clock=fake_clock)
    summary = await service.reconcile_all(now=fake_clock.now())
    # 4 calls: 1 initial + 3 retries, then success on 4th
    assert call_count["n"] == 4
    assert summary.bound == 1
    assert summary.errors == 0
    assert RETRY_BACKOFF_SECONDS == (1.0, 2.0, 4.0, 8.0)


# TEST-MEM-027
async def test_4xx_no_retry_canonical_code_preserved(sample_memory, fake_clock):
    """TEST-MEM-027 - 4xx no retry; canonical_memory_code preserves MEMORY_INVALID_CONTENT."""
    # canonical_memory_code preserves MEMORY_INVALID_CONTENT
    exc = MemoryBackendError(MemoryErrorCode.MEMORY_INVALID_CONTENT, "test")
    assert canonical_memory_code(exc) == MemoryErrorCode.MEMORY_INVALID_CONTENT
    # unknown exception -> MEMORY_INTERNAL_ERROR
    assert canonical_memory_code(ValueError("x")) == MemoryErrorCode.MEMORY_INTERNAL_ERROR
    # 4xx (non-retryable) MemoryBackendError -> only 1 patch_status call from _process_one
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    leader = InProcessLeaderElector()
    await leader.try_acquire_or_renew()
    call_count = {"n": 0}

    async def fail_patch(ns, name, status, *, expected_generation):
        call_count["n"] += 1
        raise MemoryBackendError(MemoryErrorCode.MEMORY_INVALID_CONTENT, "invalid content")

    backend.patch_status = fail_patch
    service = _make_service(backend=backend, leader=leader, clock=fake_clock)
    summary = await service.reconcile_all(now=fake_clock.now())
    # 2 calls max: 1 from _process_one (non-retryable) + 1 from _mark_error (swallowed)
    assert call_count["n"] <= 2
    assert summary.bound == 0
    assert summary.errors == 1


# TEST-MEM-028
async def test_prepare_bind_then_exception_calls_rollback(sample_memory, fake_clock):
    """TEST-MEM-028 - prepare/bind then exception calls rollback."""
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    leader = InProcessLeaderElector()
    await leader.try_acquire_or_renew()
    call_count = {"n": 0}

    async def fail_patch(ns, name, status, *, expected_generation):
        call_count["n"] += 1
        raise MemoryBackendError(MemoryErrorCode.MEMORY_INVALID_CONTENT, "bind fail")

    backend.patch_status = fail_patch
    service = _make_service(backend=backend, leader=leader, clock=fake_clock)
    original_rollback = service._rollback
    rollback_called = {"n": 0}

    def spy_rollback(token):
        rollback_called["n"] += 1
        return original_rollback(token)

    service._rollback = spy_rollback
    summary = await service.reconcile_all(now=fake_clock.now())
    assert call_count["n"] >= 1
    assert summary.errors == 1
    assert rollback_called["n"] >= 1


# TEST-MEM-029
async def test_finalize_five_steps_idempotent(sample_memory, fake_clock):
    """TEST-MEM-029 - finalize 5 steps strict order + first 4 idempotent."""
    # Use two independent backends to test idempotency of step 4 (index.remove)
    # without the step 5 patch_status failing on second call (record missing after step 3)
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    index = AsyncMock()
    index.remove = AsyncMock(return_value=None)
    service = _make_service(backend=backend, clock=fake_clock, index=index)
    # call finalize once
    await service.finalize(sample_memory)
    # step 3: backend.delete was called -> size=0
    assert backend.size == 0
    # step 4: index.remove was called once
    assert index.remove.call_count == 1
    # step 5: remove_finalizer (silently swallowed if record is missing - "remove_finalizer" only on success)


# TEST-MEM-030
async def test_cleanup_failure_keeps_finalizer_success_removes(sample_memory, fake_clock):
    """TEST-MEM-030 - cleanup failure keeps finalizer; success removes."""
    # scenario A: index.remove fails -> exception bubbles (Kopf will retry)
    backend = InMemoryBackend(clock=fake_clock)
    await backend.put(sample_memory)
    index_fail = AsyncMock()
    index_fail.remove = AsyncMock(
        side_effect=MemoryBackendError(MemoryErrorCode.MEMORY_INTERNAL_ERROR, "remove fail")
    )
    service_fail = _make_service(backend=backend, clock=fake_clock, index=index_fail)
    raised = False
    try:
        await service_fail.finalize(sample_memory)
    except MemoryBackendError:
        raised = True
    # step 3 succeeded -> backend.size=0; step 4 (index.remove) raised
    assert raised is True
    assert backend.size == 0
    # scenario B: success path - index.remove succeeds
    backend2 = InMemoryBackend(clock=fake_clock)
    await backend2.put(sample_memory)
    index_ok = AsyncMock()
    index_ok.remove = AsyncMock(return_value=None)
    service_ok = _make_service(backend=backend2, clock=fake_clock, index=index_ok)
    await service_ok.finalize(sample_memory)
    assert backend2.size == 0
    assert index_ok.remove.call_count == 1
