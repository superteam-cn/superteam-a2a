"""MemoryReconciler · L3-6 §4 · 60s kopf.timer + Leader Election + finalize 5-step.

ADR-0006 v1.0 Accepted D 方案 · 单进程 · MemoryBackend 抽象层（PR #17 merged at bf1ca4b）。

公开 API（19 符号）:
- types: ReconcileSummary, MemoryReconcilerError
- leader: LeaderElector (Protocol), InProcessLeaderElector, K8sLeaseLeaderElector
- timer constants: TIMER_INTERVAL_SECONDS=60.0, TIMER_ID="memory-reconciler"
- finalize: MEMORY_FINALIZER, finalize_memory (kopf.on.delete decorator)
- entry: MemoryReconcilerService, memory_reconciler_timer (kopf.timer decorator)

L4-Step3 Path 1 微同步: §4.3 pseudocode 用的 prepare/bind/commit/rollback 不扩展 MemoryBackend
Protocol（保持 5 项不变量）；reconciler 内 `async with _tx_lock` + try/except 实现事务语义。
§M-followup: v0.2.2 ADR-0007 微同步（若 spec 收紧要 2-phase commit）。

WIP #79: MemoryReconcilerService + memory_reconciler_timer + finalize_memory 留 #79 Subagent.
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.reconciler.leader import (
    InProcessLeaderElector,
    K8sLeaseLeaderElector,
    LeaderElector,
)

# Re-exports placeholder for full implementation in #79
__all__ = [
    "InProcessLeaderElector",
    "K8sLeaseLeaderElector",
    "LeaderElector",
    # MemoryReconcilerService + memory_reconciler_timer + finalize_memory
    # + ReconcileSummary + MEMORY_FINALIZER + TIMER_ID + TIMER_INTERVAL_SECONDS
    # 由 #79 Subagent 在 memory_reconciler.py + finalize.py 模块实装后追加导出
]
