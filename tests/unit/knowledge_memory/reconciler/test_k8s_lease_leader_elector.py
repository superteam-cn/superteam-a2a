"""K8sLeaseLeaderElector unit tests - K8S-LE-UT-001~008 (8 tests).

PR-2 L4-Phase2 K8sLeaseLeaderElector 完整实装 testsuite.
Mock coordination.k8s.io/v1 ApiException + CoordinationV1Api client.

Per plan v1.0 §2.9 + Phase 2 测试策略 (plan §4):
- New module k8s_lease_leader_elector 需 ≥ 92% 覆盖率 (v0.2 微调 vs 95% 基线 3pp 差距)
- 5-8 个 UT 已实装 (K8S-LE-UT-001~008)

作者: #85 主 Agent (Subagent 受 Write 权限拒绝,沿 #81 #82 主 Agent 直接执行模式)
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# ============================================================================
# 路径前置 (与 conftest.py 一致 · 测试独立可执行)
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory import (  # noqa: E402
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.reconciler.k8s_lease_leader_elector import (  # noqa: E402
    K8sLeaseLeaderElector,
)
from superteam_a2a.knowledge_memory.reconciler.leader import LeaderElector  # noqa: E402

# ============================================================================
# Mock helpers
# ============================================================================


def _resolve_real_api_exception() -> type[Exception]:
    """Lazy resolve kubernetes_asyncio.client.ApiException (顶层 import 会被 mock 误判).

    若导入失败则 fallback Exception 基类, 测试代码应能容忍.
    """
    try:
        from kubernetes_asyncio.client import ApiException as _K8sApiException
    except ImportError:
        return Exception
    return _K8sApiException


# Module-load resolution (above function must be defined before this use)
_REAL_API_EXCEPTION_BASE: type[Exception] = _resolve_real_api_exception()


class _FakeApiException(_REAL_API_EXCEPTION_BASE):
    """模拟 kubernetes_asyncio.client.ApiException · lazy 解析子类化实现.

    严格匹配真实 ApiException 接口 (status + reason + headers),
    使生产代码 `except ApiException` 能捕获此 fake.
    """

    def __init__(self, status: int, reason: str = "", headers: dict | None = None) -> None:
        # Kubernetes Async ApiException signature: (self, status=None, reason=None, http_resp=None)
        # pyright 没有 stubs → 不能验证 call-arg
        super().__init__(status=status, reason=reason)  # type: ignore[call-arg]
        self.status = status
        self.reason = reason
        self.headers = headers or {}


def _make_kube_client(
    *,
    read: object | Exception | list | None = None,
    create: object | Exception | list | None = None,
    replace: object | Exception | list | None = None,
) -> MagicMock:
    """构造 CoordinationV1Api MagicMock with 3 async methods.

    setup 规则:
    - Exception instance / class → side_effect = raise 每次
    - list / tuple → side_effect = queue (按序消费)
    - None → return_value = None
    - 其他 → return_value = value (单次固定返回值)
    """
    client = MagicMock()

    def _setup(attr_name: str, value: object | Exception | list | None) -> None:
        if value is None:
            setattr(client, attr_name, AsyncMock(return_value=None))
            return
        # Exception instance / class
        if isinstance(value, BaseException) or (
            isinstance(value, type) and issubclass(value, BaseException)
        ):
            setattr(client, attr_name, AsyncMock(side_effect=value))
            return
        # iterable
        if isinstance(value, (list, tuple)):
            setattr(client, attr_name, AsyncMock(side_effect=list(value)))
            return
        # 普通 return value
        setattr(client, attr_name, AsyncMock(return_value=value))

    _setup("read_namespaced_lease", read)
    _setup("create_namespaced_lease", create)
    _setup("replace_namespaced_lease", replace)
    return client


def _make_lease(*, holder: str, resource_version: str = "1") -> MagicMock:
    """构造假 V1Lease object (annotations) with holder + resource_version."""
    lease = MagicMock()
    lease.annotations = {"superteam-a2a.io/holder-id": holder}
    lease.resource_version = resource_version
    lease.spec = MagicMock()
    lease.spec.holder_identity = holder
    return lease


# ============================================================================
# K8S-LE-UT-001: is_leader 同步返回缓存
# ============================================================================


def test_k8s_le_ut_001_is_leader_returns_cache() -> None:
    """K8S-LE-UT-001 · 同步 is_leader 直接返回 _is_holder · 无 I/O."""
    elector = K8sLeaseLeaderElector(holder_id="pod-test-001")
    assert elector.is_leader() is False, "初始默认 False"
    # 直接修改内部状态模拟已持有
    elector._is_holder = True
    assert elector.is_leader() is True
    # force_lose_leadership 模拟被抢占
    elector.force_lose_leadership()
    assert elector.is_leader() is False


# ============================================================================
# K8S-LE-UT-002: 首次 acquire: read 404 → create 200
# ============================================================================


async def test_k8s_le_ut_002_first_acquire_404_then_create_200() -> None:
    """K8S-LE-UT-002 · 首次获取: read 404 → create 200 → is_leader True → return True."""
    created_lease = _make_lease(holder="pod-acquire-002")
    client = _make_kube_client(
        read=_FakeApiException(404, "not found"),  # read → 404 → None
        create=created_lease,  # create → 200
    )
    elector = K8sLeaseLeaderElector(holder_id="pod-acquire-002", kube_client=client)

    result = await elector.try_acquire_or_renew()

    assert result is True
    assert elector.is_leader() is True
    assert elector._consecutive_renew_failures == 0
    client.read_namespaced_lease.assert_awaited_once_with(
        name="memory-reconciler-leader",
        namespace="superteam-a2a-system",
    )
    client.create_namespaced_lease.assert_awaited_once()


# ============================================================================
# K8S-LE-UT-003: 已持有续约: CAS success
# ============================================================================


async def test_k8s_le_ut_003_renew_cas_success() -> None:
    """K8S-LE-UT-003 · 已持有 Lease: read 返回自己 → replace success → return True."""
    self_lease = _make_lease(holder="pod-renew-003", resource_version="42")
    client = _make_kube_client(
        read=self_lease,
        replace=MagicMock(),  # replace_namespaced_lease success
    )
    elector = K8sLeaseLeaderElector(holder_id="pod-renew-003", kube_client=client)

    result = await elector.try_acquire_or_renew()

    assert result is True
    assert elector.is_leader() is True
    client.read_namespaced_lease.assert_awaited_once()
    client.replace_namespaced_lease.assert_awaited_once()
    # CAS key 已被 read 提取
    assert elector._lease_resource_version == "42"


# ============================================================================
# K8S-LE-UT-004: 抢占检测: read 返回其他 holder_id
# ============================================================================


async def test_k8s_le_ut_004_preempted_by_other_holder() -> None:
    """K8S-LE-UT-004 · read 返回其他 holder_id → 被抢占 · _is_holder=False → return False."""
    other_lease = _make_lease(holder="pod-other-004", resource_version="100")
    client = _make_kube_client(read=other_lease)
    elector = K8sLeaseLeaderElector(holder_id="pod-self-004", kube_client=client)
    elector._is_holder = True  # 模拟原本持有

    result = await elector.try_acquire_or_renew()

    assert result is False
    assert elector.is_leader() is False, "被抢占后 is_leader 立即 False"
    assert elector._consecutive_renew_failures == 0  # 抢占不计入 renew 失败
    # 不应调用 replace (CAS 没机会)
    client.replace_namespaced_lease.assert_not_awaited()


# ============================================================================
# K8S-LE-UT-005: 5xx backoff 1/2/4/8s sequence
# ============================================================================


async def test_k8s_le_ut_005_5xx_backoff_1_2_4_8_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """K8S-LE-UT-005 · 5xx 错误: 4 次 backoff 1s/2s/4s/8s 后返回 False (不抛).

    通过 monkeypatch asyncio.sleep 拦截真实睡眠,验证 backoff 序列 + 最终 surrender.
    """
    # 4 次 read 都抛 500 → 触发 backoff 1/2/4/8s
    client = _make_kube_client(
        read=_FakeApiException(500, "internal error"),
    )
    elector = K8sLeaseLeaderElector(
        holder_id="pod-backoff-005", kube_client=client, duration_seconds=15.0
    )

    sleep_calls: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    result = await elector.try_acquire_or_renew()

    # 4 次 read 全部 fail → 第 4 次失败后 _handle_terminal_failure → _consecutive_renew_failures = 4 ≥ 3 → surrender
    # backoff 序列应该调用 4 次睡眠: 1, 2, 4, 8 (MAX_BACKOFF_SECONDS)
    assert sleep_calls == [1.0, 2.0, 4.0, 8.0], (
        f"expected backoff sequence [1,2,4,8], got {sleep_calls}"
    )
    assert result is False, "5xx 用完 attempts 应返回 False"
    assert elector.is_leader() is False
    assert client.read_namespaced_lease.await_count == 5, (
        "读 lease 5 次: 4 次 backoff + 第 5 次 (用完 attempts)"
    )


# ============================================================================
# K8S-LE-UT-006: 3 次连续 renew 失败 → 永久让位
# ============================================================================


async def test_k8s_le_ut_006_three_consecutive_renew_failures_surrender() -> None:
    """K8S-LE-UT-006 · 持锁方是自己 → replace 阶段 5xx → 连续 3 次后永久让位 (3 独立 call).

    这里简化: 3 次独立 try_acquire_or_renew 调用,每次 replace 5xx,
    第 3 次后 _is_holder 应该永久 False.
    """
    self_lease = _make_lease(holder="pod-consec-006", resource_version="50")

    # 构造一个每次调用都返 5xx 的 client
    client = MagicMock()
    client.read_namespaced_lease = AsyncMock(return_value=self_lease)
    client.replace_namespaced_lease = AsyncMock(side_effect=_FakeApiException(500, "internal"))
    elector = K8sLeaseLeaderElector(holder_id="pod-consec-006", kube_client=client)
    elector._is_holder = True  # 初始持有

    # 第 1 次: _consecutive_renew_failures → 1
    r1 = await elector.try_acquire_or_renew()
    # 第 2 次: 2
    r2 = await elector.try_acquire_or_renew()
    # 第 3 次: 3 ≥ MAX → surrender
    r3 = await elector.try_acquire_or_renew()

    assert r1 is False
    assert r2 is False
    assert r3 is False
    assert elector._consecutive_renew_failures >= 3
    assert elector.is_leader() is False, "3 次连续后永久让位"


# ============================================================================
# K8S-LE-UT-007: 4xx (except 404/409) 透传 MemoryBackendError
# ============================================================================


async def test_k8s_le_ut_007_4xx_raises_memory_backend_error() -> None:
    """K8S-LE-UT-007 · read 403 → raise MemoryBackendError(MEMORY_INTERNAL_ERROR)."""
    client = _make_kube_client(
        read=_FakeApiException(403, "forbidden"),
    )
    elector = K8sLeaseLeaderElector(holder_id="pod-403-007", kube_client=client)

    with pytest.raises(MemoryBackendError) as exc_info:
        await elector.try_acquire_or_renew()

    assert exc_info.value.code == MemoryErrorCode.MEMORY_INTERNAL_ERROR
    assert "403" in str(exc_info.value) or "forbidden" in str(exc_info.value)


# ============================================================================
# K8S-LE-UT-008: CancelledError 透传
# ============================================================================


async def test_k8s_le_ut_008_cancelled_error_propagates() -> None:
    """K8S-LE-UT-008 · kopf 取消 tick 时 CancelledError 透传,不转为 False."""
    client = MagicMock()

    async def cancel_on_read(*args: object, **kwargs: object) -> None:
        raise asyncio.CancelledError

    client.read_namespaced_lease = AsyncMock(side_effect=cancel_on_read)
    elector = K8sLeaseLeaderElector(holder_id="pod-cancel-008", kube_client=client)

    with pytest.raises(asyncio.CancelledError):
        await elector.try_acquire_or_renew()


# ============================================================================
# 额外 smoke: Protocol isinstance · 替换 stub 后保持兼容
# ============================================================================


def test_k8s_lease_leader_elector_is_leader_elector() -> None:
    """Protocol isinstance · K8sLeaseLeaderElector 必须 runtime_checkable 通过."""
    elector = K8sLeaseLeaderElector(holder_id="pod-iso")
    assert isinstance(elector, LeaderElector), (
        f"K8sLeaseLeaderElector must satisfy LeaderElector Protocol; got {type(elector)}"
    )


def test_k8s_lease_leader_elector_constructor_validates_params() -> None:
    """构造参数验证: 负数或 0 应抛 ValueError."""
    with pytest.raises(ValueError, match="duration_seconds"):
        K8sLeaseLeaderElector(duration_seconds=0)
    with pytest.raises(ValueError, match="renew_deadline_seconds"):
        K8sLeaseLeaderElector(renew_deadline_seconds=-1)
    with pytest.raises(ValueError, match="retry_period_seconds"):
        K8sLeaseLeaderElector(retry_period_seconds=0)


def test_k8s_lease_leader_elector_auto_generates_holder_id() -> None:
    """holder_id 默认生成 `pod-{uuid4().hex[:8]}`."""
    e1 = K8sLeaseLeaderElector()
    e2 = K8sLeaseLeaderElector()
    assert e1._holder_id.startswith("pod-")
    assert e2._holder_id.startswith("pod-")
    assert e1._holder_id != e2._holder_id  # uuid 唯一


def test_k8s_lease_leader_elector_lease_body_includes_holder() -> None:
    """_build_lease_body 必须包含 holderIdentity + annotations + duration."""
    elector = K8sLeaseLeaderElector(holder_id="pod-body-test", duration_seconds=15.0)
    body = elector._build_lease_body(holder_only=True)
    assert body["apiVersion"] == "coordination.k8s.io/v1"
    assert body["kind"] == "Lease"
    assert body["metadata"]["name"] == "memory-reconciler-leader"
    assert body["metadata"]["namespace"] == "superteam-a2a-system"
    assert body["metadata"]["annotations"]["superteam-a2a.io/holder-id"] == "pod-body-test"
    assert body["spec"]["holderIdentity"] == "pod-body-test"
    assert body["spec"]["leaseDurationSeconds"] == 15
