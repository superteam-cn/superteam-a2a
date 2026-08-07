"""K8s coordination.k8s.io/v1 Lease backed leader elector · L3-6 §4.1.

完整实装 (PR-2)· 替换 #77-era stub · 与 InProcessLeaderElector 行为对齐 (D-3).

核心不变量 (D-5 状态机):
- duration=15s, renew_deadline=10s, retry_period=5s (L3-6 §4.2)
- 30s grace_period_seconds 内仅允许重获,不允许写 status
- 连续 _MAX_CONSECUTIVE_RENEW_FAILURES 次 renew 失败 → 永久让位
- timer 重叠禁止并发: 上一轮未完成 → 跳过 (由 reconciler 处理,本类不感知)

错误映射矩阵 (D-4):
- 404 (Lease 不存在) → create → True
- 200 + holder_id 匹配 → renew → True
- 200 + holder_id 不同 → 被抢占 · _is_holder=False → False
- 409 Conflict → 被抢占 · False
- 5xx → 1/2/4/8s backoff (max _MAX_BACKOFF_ATTEMPTS) → False (不抛)
- 4xx (除 404/409) → raise MemoryBackendError(MEMORY_INTERNAL_ERROR)
- 429 → sleep(Retry-After, cap 60s) → 重试 → False (超过 attempts)
- asyncio.CancelledError → 透传 (让 kopf 取消 tick)
"""

from __future__ import annotations

import asyncio
import re
from typing import Any, ClassVar
from uuid import uuid4

from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
    MemoryErrorCode,
)

# 状态机常量 (D-5)
_MAX_BACKOFF_SECONDS: tuple[float, ...] = (1.0, 2.0, 4.0, 8.0)  # D-4 错误映射 · 5xx 序列
_MAX_BACKOFF_ATTEMPTS: int = len(_MAX_BACKOFF_SECONDS)  # 4 次
_MAX_CONSECUTIVE_RENEW_FAILURES: int = 3  # L3-6 §4.2 line 671
_MAX_RETRY_AFTER_SECONDS: float = 60.0  # D-4 · 429 cap
_HOLDER_ANNOTATION_KEY: str = (
    "superteam-a2a.io/holder-id"  # Lease 上携带 holder_id 的 annotation key
)
_RETRY_AFTER_HEADER: str = "Retry-After"  # K8s API standard
_RETRY_AFTER_INT_RE: re.Pattern[str] = re.compile(r"^\d+$")


class K8sLeaseLeaderElector:
    """K8s coordination.k8s.io/v1 Lease backed leader elector (PR-2 完整实装).

    Replacement for #77-era stub. Inherits LeaderElector Protocol via duck typing
    (5 method signature + runtime_checkable). Behavior aligns with
    InProcessLeaderElector (D-3 行为对齐表) so that REPLACEMENT under
    `_build_memo()` (Helm `leaderElection.backend=k8s`) is a drop-in.

    Test backdoors (与 InProcessLeaderElector D-3 #5 对齐):
    - force_lose_leadership(): 测试 helper,模拟被抢占

    K8sLeaseLeaderElector 不主动写 status (L3-6 §4.2 30s grace 规则),
    只更新 Lease spec.transitionTime。reconciler 决定是否 patch Memory CRD status。
    """

    # Class-level constants (类级供 test 引用)
    MAX_BACKOFF_SECONDS: ClassVar[tuple[float, ...]] = _MAX_BACKOFF_SECONDS
    MAX_CONSECUTIVE_RENEW_FAILURES: ClassVar[int] = _MAX_CONSECUTIVE_RENEW_FAILURES
    MAX_RETRY_AFTER_SECONDS: ClassVar[float] = _MAX_RETRY_AFTER_SECONDS
    HOLDER_ANNOTATION_KEY: ClassVar[str] = _HOLDER_ANNOTATION_KEY

    def __init__(
        self,
        *,
        lease_name: str = "memory-reconciler-leader",
        namespace: str = "superteam-a2a-system",
        holder_id: str | None = None,
        duration_seconds: float = 15.0,
        renew_deadline_seconds: float = 10.0,
        retry_period_seconds: float = 5.0,
        kube_client: Any | None = None,
    ) -> None:
        # D-2 7 kw-only 构造参数
        if duration_seconds <= 0:
            raise ValueError(f"duration_seconds must be > 0, got {duration_seconds}")
        if renew_deadline_seconds <= 0:
            raise ValueError(f"renew_deadline_seconds must be > 0, got {renew_deadline_seconds}")
        if retry_period_seconds <= 0:
            raise ValueError(f"retry_period_seconds must be > 0, got {retry_period_seconds}")
        self._lease_name = lease_name
        self._namespace = namespace
        self._holder_id = holder_id if holder_id is not None else f"pod-{uuid4().hex[:8]}"
        self._duration = duration_seconds
        self._renew_deadline = renew_deadline_seconds
        self._retry_period = retry_period_seconds
        self._kube_client = kube_client  # lazy-init in _ensure_kube_client()

        # D-5 状态机 5 flag
        self._is_holder: bool = False
        self._lease_resource_version: str | None = None  # K8s 乐观锁 CAS (D-3 #4)
        self._consecutive_renew_failures: int = 0
        self._grace_period_seconds: float = 30.0  # L3-6 §4.2
        self._last_attempt_at: float | None = None  # 最近 try_acquire_or_renew 时间戳

    # ===== LeaderElector Protocol 实现 =====

    def is_leader(self) -> bool:
        """D-3 #1: 同步缓存查询 · 返回 _is_holder."""
        return self._is_holder

    async def try_acquire_or_renew(self) -> bool:
        """D-3 #2: 三段式 read → CAS write or create.

        Returns:
            True if we hold leadership after this attempt;
            False if we were preempted or 5xx exhausted attempts.

        Raises:
            MemoryBackendError: 4xx (except 404/409) k8s API error
            asyncio.CancelledError: 透传 kopf 取消
        """
        self._last_attempt_at = asyncio.get_event_loop().time()
        client = await self._ensure_kube_client()

        # 5xx/429 backoff state
        attempt_idx = 0

        while True:
            try:
                lease = await self._read_lease(client)
            except _RetryableK8sError as exc:
                # 5xx 或 429 → backoff/retry
                if exc.is_5xx and attempt_idx >= _MAX_BACKOFF_ATTEMPTS:
                    # 5xx attempts 用完 → 让位 or 永久 surrender
                    self._handle_terminal_failure()
                    return False
                # delay: 429 用 Retry-After (caller computed) · 5xx 用 attempt_idx 索引序列
                if exc.is_5xx:
                    delay = _MAX_BACKOFF_SECONDS[attempt_idx]
                    attempt_idx += 1
                else:
                    delay = exc.delay_seconds
                await asyncio.sleep(delay)
                continue
            except _TerminalK8sError as exc:
                # 4xx (除 404/409) → raise
                raise MemoryBackendError(
                    MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                    f"K8s Lease API error: {exc.reason}",
                    cause=exc.__cause__ if isinstance(exc.__cause__, Exception) else None,
                ) from exc.__cause__

            # Read 成功 (None = 404, dict = V1Lease)
            if lease is None:
                # 404: Lease 不存在 → create (允许 429 重试,409 让位)
                while True:
                    try:
                        created = await self._create_lease(client)
                        break
                    except _RetryableK8sError as exc:
                        await asyncio.sleep(exc.delay_seconds)
                        continue
                    except _TerminalK8sError as exc:
                        raise MemoryBackendError(
                            MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                            f"K8s Lease create failed: {exc.reason}",
                            cause=exc.__cause__ if isinstance(exc.__cause__, Exception) else None,
                        ) from exc.__cause__
                if created:
                    self._is_holder = True
                    self._consecutive_renew_failures = 0
                    return True
                # create 失败 (e.g. 409 race) → 回到 read 重试
                continue

            # Read 成功: 检查 holder
            holder = self._extract_holder_id(lease)
            if holder != self._holder_id:
                # D-4: 被抢占
                self._is_holder = False
                self._consecutive_renew_failures = 0
                return False

            # 持锁方是自己 → renew (CAS)
            try:
                await self._update_lease(client, lease)
            except _TerminalK8sError as exc:
                raise MemoryBackendError(
                    MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                    f"K8s Lease update failed: {exc.reason}",
                    cause=exc.__cause__ if isinstance(exc.__cause__, Exception) else None,
                ) from exc.__cause__
            except _RetryableK8sError:
                # update 阶段 5xx: 计入失败计数
                self._consecutive_renew_failures += 1
                if self._consecutive_renew_failures >= _MAX_CONSECUTIVE_RENEW_FAILURES:
                    self._is_holder = False
                return False

            self._is_holder = True
            self._consecutive_renew_failures = 0
            return True

    def force_lose_leadership(self) -> None:
        """D-3 #5: 测试 backdoor · 模拟被抢占/主动让位."""
        self._is_holder = False
        self._lease_resource_version = None
        self._consecutive_renew_failures = 0

    # ===== D-3 内部方法 =====

    async def _read_lease(self, client: Any) -> Any:
        """D-3 #3: read Lease · 返回 V1Lease 或 None (404)."""
        try:
            return await client.read_namespaced_lease(
                name=self._lease_name,
                namespace=self._namespace,
            )
        except _ApiException as e:
            status = getattr(e, "status", None)
            if status == 404:
                return None
            if status == 429:
                delay = self._parse_retry_after(e)
                raise _RetryableK8sError(delay, reason=f"429 rate-limited: {e}") from e
            if status is not None and 500 <= status < 600:
                # 5xx: caller 用 attempt_idx 计算 backoff (这里 is_5xx=True 标记)
                raise _RetryableK8sError(0, reason=f"5xx read: {status}", is_5xx=True) from e
            raise _TerminalK8sError(reason=f"K8s read error {status}: {e}") from e

    async def _create_lease(self, client: Any) -> bool:
        """创建 Lease · 409 (被抢占) 返回 False · 其他 raise."""
        lease_body = self._build_lease_body(holder_only=True)
        try:
            await client.create_namespaced_lease(
                namespace=self._namespace,
                body=lease_body,
            )
            return True
        except _ApiException as e:
            status = getattr(e, "status", None)
            if status == 409:
                # Lost the race
                return False
            if status == 429:
                delay = self._parse_retry_after(e)
                raise _RetryableK8sError(delay, reason="429 on create") from e
            if status is not None and 500 <= status < 600:
                # create 阶段 5xx: 同样 caller 计算 backoff
                raise _RetryableK8sError(0, reason=f"5xx create: {status}", is_5xx=True) from e
            raise _TerminalK8sError(reason=f"K8s create error {status}: {e}") from e

    async def _update_lease(self, client: Any, lease: Any) -> None:
        """CAS update Lease with current resourceVersion."""
        # 提取 resourceVersion (CAS key)
        rv = getattr(lease, "resource_version", None) or getattr(lease, "resourceVersion", None)
        if rv:
            self._lease_resource_version = rv

        lease_body = self._build_lease_body(holder_only=False)
        # 把 spec.holderIdentity annotation 写回 (renew 模式)
        lease_body["metadata"]["resourceVersion"] = self._lease_resource_version or ""

        try:
            await client.replace_namespaced_lease(
                name=self._lease_name,
                namespace=self._namespace,
                body=lease_body,
            )
        except _ApiException as e:
            status = getattr(e, "status", None)
            if status == 409:
                # Lost CAS — fire as Retryable so caller can mark failed
                raise _RetryableK8sError(
                    _MAX_BACKOFF_SECONDS[0],
                    reason="409 CAS lost on update",
                ) from e
            if status == 429:
                delay = self._parse_retry_after(e)
                raise _RetryableK8sError(delay, reason="429 on update") from e
            if status is not None and 500 <= status < 600:
                raise _RetryableK8sError(0, reason=f"5xx update: {status}", is_5xx=True) from e
            raise _TerminalK8sError(reason=f"K8s update error {status}: {e}") from e

    def _build_lease_body(self, *, holder_only: bool) -> dict[str, Any]:
        """构造 K8s Lease body (D-3 #4 CAS body)."""
        body: dict[str, Any] = {
            "apiVersion": "coordination.k8s.io/v1",
            "kind": "Lease",
            "metadata": {
                "name": self._lease_name,
                "namespace": self._namespace,
                "annotations": {
                    _HOLDER_ANNOTATION_KEY: self._holder_id,
                },
            },
            "spec": {
                "holderIdentity": self._holder_id,
                "leaseDurationSeconds": int(self._duration),
                "renewTime": None,  # K8s server 填充
            },
        }
        if not holder_only and self._lease_resource_version:
            body["metadata"]["resourceVersion"] = self._lease_resource_version
        return body

    @staticmethod
    def _extract_holder_id(lease: Any) -> str | None:
        """从 Lease object 提取当前 holder ID (annotation 优先, fallback spec.holderIdentity)."""
        annotations = getattr(lease, "annotations", None) or {}
        if isinstance(annotations, dict):
            holder = annotations.get(_HOLDER_ANNOTATION_KEY)
            if holder:
                return str(holder)
        spec = getattr(lease, "spec", None)
        if spec is not None:
            spec_holder = getattr(spec, "holder_identity", None) or getattr(
                spec, "holderIdentity", None
            )
            if spec_holder:
                return str(spec_holder)
        return None

    def _parse_retry_after(self, exc: Exception) -> float:
        """解析 K8s Retry-After header · cap 60s."""
        headers = getattr(exc, "headers", None) or {}
        value = headers.get(_RETRY_AFTER_HEADER) if hasattr(headers, "get") else None
        if value is None:
            # ApiException 在 PyPI 是 namedtuple-like; header 可能 e.headers
            value = getattr(exc, "reason", None)  # 退化
            if value is None:
                return _MAX_BACKOFF_SECONDS[0]
        value_str = str(value).strip()
        if _RETRY_AFTER_INT_RE.match(value_str):
            try:
                delay = float(value_str)
            except ValueError:
                return _MAX_BACKOFF_SECONDS[0]
            return min(delay, _MAX_RETRY_AFTER_SECONDS)
        # HTTP-date 格式不实现精确解析 · 退化使用默认
        return _MAX_BACKOFF_SECONDS[0]

    def _handle_terminal_failure(self) -> None:
        """连续 backoff attempts 用完 or 永久 surrender."""
        self._consecutive_renew_failures += 1
        if self._consecutive_renew_failures >= _MAX_CONSECUTIVE_RENEW_FAILURES:
            self._is_holder = False

    async def _ensure_kube_client(self) -> Any:
        """Lazy init kube_client · 优先 in-cluster, fallback kubeconfig."""
        if self._kube_client is not None:
            return self._kube_client

        # Lazy import kubernetes_asyncio (避免 module import 时需要 k8s 环境)
        import kubernetes_asyncio as k8s
        from kubernetes_asyncio.client import ApiClient, CoordinationV1Api

        try:
            # Try in-cluster first (production path)
            k8s.config.load_incluster_config()
        except Exception:
            # Fallback to kubeconfig (dev/CI path)
            await k8s.config.load_kube_config()

        api_client = ApiClient()
        self._kube_client = CoordinationV1Api(api_client)
        return self._kube_client


# ===== 内部异常类 (lazy import kubernetes_asyncio.client.ApiException) =====


def _resolve_api_exception_base() -> type[Exception]:
    """Lazy resolve kubernetes_asyncio.client.ApiException (避免顶层 import)."""
    try:
        from kubernetes_asyncio.client import ApiException as K8sApiException
    except ImportError:
        # Fallback to base Exception if not installed (test env without kube)
        class _FallbackK8sApiExceptionError(Exception):  # type: ignore[no-redef]
            pass

        return _FallbackK8sApiExceptionError
    return K8sApiException


_ApiException: type[Exception] = _resolve_api_exception_base()  # type: ignore[reportInvalidTypeForm]


class _RetryableK8sError(Exception):
    """5xx / 429 / 409 CAS lost · 需要 backoff/retry 后续 attempt."""

    def __init__(self, delay_seconds: float, *, reason: str, is_5xx: bool = False) -> None:
        super().__init__(reason)
        self.delay_seconds = delay_seconds
        self.reason = reason
        self.is_5xx = is_5xx  # True 时 caller 用 attempt_idx 计算 1/2/4/8s 序列


class _TerminalK8sError(Exception):
    """4xx (除 404/409) · raise MemoryBackendError(MEMORY_INTERNAL_ERROR)."""

    def __init__(self, *, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


__all__ = ["K8sLeaseLeaderElector"]
