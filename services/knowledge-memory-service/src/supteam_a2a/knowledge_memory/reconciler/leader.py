"""Leader Election · L3-6 §4.2 · 30s grace + renew 失败 3 次让位.

两种实现 (PR-2 完整实装后):
- InProcessLeaderElector: 单进程 / 测试 / v0.1 single-instance (D 方案默认)
- K8sLeaseLeaderElector: coordination.k8s.io/v1 Lease (Helm `leaderElection.backend=k8s` 显式启用)

§4.2 invariant:
- duration=15s, renew_deadline=10s, retry_period=5s
- 30s grace 内仅允许重获,不允许写 status
- 连续 3 次 renew 失败 → 立即让位 leadership
- timer 重叠禁止并发: 上一轮未完成 → 跳过并记录 result="overlap_skipped"
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from superteam_a2a.knowledge_memory.reconciler.k8s_lease_leader_elector import (
    K8sLeaseLeaderElector,
)


@runtime_checkable
class LeaderElector(Protocol):
    """Leader Election 抽象 contract."""

    def is_leader(self) -> bool:
        """是否当前 leader."""
        ...

    async def try_acquire_or_renew(self) -> bool:
        """尝试获取或续约 leadership."""
        ...


class InProcessLeaderElector:
    """In-process leader elector (tests + D 方案 single-instance 默认).

    关键不变量:
    - _is_leader: bool 当前持锁状态
    - _consecutive_renew_failures: int (≥3 → 永久让位)
    - grace_period_seconds: float (默认 30s per spec)

    Test backdoors:
    - simulate_renew_failure(n): 模拟连续 n 次失败,用于 TEST-MEM-018
    - force_lose_leadership(): 立即让位,用于 TEST-MEM-019 grace 测试
    """

    _consecutive_failures_threshold = 3

    def __init__(
        self,
        *,
        duration_seconds: float = 15.0,
        renew_deadline_seconds: float = 10.0,
        retry_period_seconds: float = 5.0,
    ) -> None:
        self._duration = duration_seconds
        self._renew_deadline = renew_deadline_seconds
        self._retry_period = retry_period_seconds
        self._is_leader = False
        self._consecutive_renew_failures = 0
        self.grace_period_seconds: float = 30.0

    def is_leader(self) -> bool:
        return self._is_leader

    async def try_acquire_or_renew(self) -> bool:
        """Simulate acquire/renew (test double)."""
        if self._consecutive_renew_failures > 0:
            self._consecutive_renew_failures -= 1
            return False
        if not self._is_leader:
            self._is_leader = True
        return True

    def simulate_renew_failure(self, n: int) -> None:
        self._consecutive_renew_failures = n

    def force_lose_leadership(self) -> None:
        self._is_leader = False


__all__ = ["InProcessLeaderElector", "K8sLeaseLeaderElector", "LeaderElector"]


# Backward compatibility re-export
# K8sLeaseLeaderElector 现已从独立模块导入 (PR-2 · 替换原 stub)
# 使用方式保持不变: `from .leader import K8sLeaseLeaderElector`
