"""L3-6 kopf operator 入口 · 装配 timer + on.create + on.update + on.delete。

D 方案单进程架构（ADR-0006 v1.0 Accepted）：
- MemoryReconcilerService 60s timer（§4.1）
- MemoryBackendInProcessServiceImpl record/query（§6.1）
- @kopf.on.create / @kopf.on.update 接线（§6）
- @kopf.on.delete 接入 reconciler.finalize（§4.4）

实际部署通过 Helm Chart + uv workspace；本入口仅供本地 kopf 启动与单元测试装配。
"""

from __future__ import annotations

from typing import Any

import kopf
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.backend.clock import SystemClock
from superteam_a2a.knowledge_memory.backend.in_memory import InMemoryBackend
from superteam_a2a.knowledge_memory.handlers.admission_validator import (
    AdmissionValidatorImpl,
)
from superteam_a2a.knowledge_memory.handlers.memory_handler import (
    on_memory_create,
    on_memory_update,
)
from superteam_a2a.knowledge_memory.index.bm25_index import BM25Index
from superteam_a2a.knowledge_memory.reconciler.finalize import finalize_memory
from superteam_a2a.knowledge_memory.reconciler.leader import InProcessLeaderElector
from superteam_a2a.knowledge_memory.reconciler.memory_reconciler import (
    MemoryReconcilerService,
    memory_reconciler_timer,
)

API_GROUP = "memory.superteam-a2a.io"
API_VERSION = "v1alpha1"
KIND = "memory"


@kopf.on.create(API_GROUP, API_VERSION, KIND, id="memory-create")
async def _on_create(*, body: Any, meta: Any, memo: Any, **_: Any) -> None:
    await on_memory_create(body=body, meta=meta, memo=memo)


@kopf.on.update(API_GROUP, API_VERSION, KIND, id="memory-update")
async def _on_update(*, body: Any, meta: Any, memo: Any, **_: Any) -> None:
    await on_memory_update(body=body, meta=meta, memo=memo)


@kopf.on.delete(API_GROUP, API_VERSION, KIND, id="memory-finalize")
async def _on_delete(*, body: Any, meta: Any, memo: Any, **_: Any) -> None:
    await finalize_memory(body=body, memo=memo)


@kopf.timer(interval=60.0, id="memory-reconciler")
async def _timer(
    *,
    memo: dict[str, Any],
    **_: Any,
) -> None:
    await memory_reconciler_timer(memo=memo)


def _build_memo() -> dict[str, Any]:
    """构造 kopf memo · 服务实例注册（Step 5 完整装配）。

    5 依赖单点注入：
    - clock: SystemClock（§M-1.5 单实例 · 三方共享）
    - backend: InMemoryBackend
    - leader: InProcessLeaderElector
    - admission: AdmissionValidatorImpl
    - index: BM25Index

    6 memo key 注册：
    - clock
    - memory_backend（测试入口）
    - memory_admission_validator（测试入口）
    - memory_index（测试入口）
    - memory_in_process_service（handler record/query 路径）
    - memory_reconciler（timer/finalize 路径）
    """
    clock = SystemClock()
    backend = InMemoryBackend()
    leader = InProcessLeaderElector()
    admission = AdmissionValidatorImpl()
    index = BM25Index()

    in_process_service = MemoryBackendInProcessServiceImpl(
        backend=backend,
        admission=admission,
    )
    reconciler_service = MemoryReconcilerService(
        backend=backend,
        leader=leader,
        clock=clock,
        admission=admission,
        index=index,
    )

    return {
        "clock": clock,
        "memory_backend": backend,
        "memory_admission_validator": admission,
        "memory_index": index,
        "memory_in_process_service": in_process_service,
        "memory_reconciler": reconciler_service,
    }


def main() -> None:
    """kopf operator 启动入口。"""
    kopf.run(memo=_build_memo())


if __name__ == "__main__":
    main()
