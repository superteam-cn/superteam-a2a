"""L3-6 kopf operator 入口 + starlette HTTP server（同 event loop · D 方案单进程）。

依据 ADR-0006 v1.0 Accepted + L4-Phase3 plan §3 PR-1：
- MemoryReconcilerService 60s timer（§4.1）
- MemoryBackendInProcessServiceImpl record/query（§6.1）
- @kopf.on.create / @kopf.on.update 接线（§6）
- @kopf.on.delete 接入 reconciler.finalize（§4.4）
- starlette ASGI app: /healthz + /jsonrpc/record_memory + /jsonrpc/query_memory

单进程架构：kopf + uvicorn 共享同一 asyncio event loop（§2.1 starlette 选项 C）；
不拆 deployment，livenessProbe/readinessProbe 路径统一指向 /healthz（PR-4.1.1 #90 共用）。

实际部署通过 Helm Chart + uv workspace；本入口仅供本地 kopf 启动与单元测试装配。
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from typing import Any

import kopf
import uvicorn
from starlette.applications import Starlette
from superteam_a2a.knowledge_memory.api.server import create_app
from superteam_a2a.knowledge_memory.api.service import (
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.backend.clock import SystemClock
from superteam_a2a.knowledge_memory.backend.in_memory import InMemoryBackend
from superteam_a2a.knowledge_memory.backend.k8s_backend import K8sBackend
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

# L4-Phase3 PR-1：HTTP server 端口（starlette · 替代 kopf liveness_endpoint）
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 8080

# L4-Phase3 PR-2：backend selection (helm values.yaml backend.type)
# - in_process (default): dict-backed (Phase 1 MVP core)
# - k8s: CustomObjectsApi-backed production backend
BACKEND_TYPE_ENV_VAR = "MEMORY_BACKEND_TYPE"
DEFAULT_BACKEND_TYPE = "in_process"
VALID_BACKEND_TYPES = frozenset({"in_process", "k8s"})


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


def _build_backend(
    *,
    backend_type: str | None = None,
    clock: SystemClock | None = None,
) -> Any:
    """根据 backend_type 选择 backend 实现（PR-2 helm values backend.type）。

    - in_process: InMemoryBackend（Phase 1 MVP core · 默认）
    - k8s: K8sBackend（CustomObjectsApi 生产实现）

    Args:
        backend_type: 显式指定 ("in_process" / "k8s")；None 时从 env var 读
        clock: 注入时钟（测试用 FakeClock；None 时 SystemClock）

    Returns:
        InMemoryBackend | K8sBackend 实例（满足 MemoryBackend Protocol）
    """
    if backend_type is None:
        backend_type = os.environ.get(BACKEND_TYPE_ENV_VAR, DEFAULT_BACKEND_TYPE)
    if backend_type not in VALID_BACKEND_TYPES:
        # 防御：未知 backend 类型 → 退化默认值 + log warning
        import warnings

        warnings.warn(
            f"Unknown backend_type {backend_type!r}; falling back to {DEFAULT_BACKEND_TYPE!r}",
            stacklevel=2,
        )
        backend_type = DEFAULT_BACKEND_TYPE
    shared_clock = clock or SystemClock()
    if backend_type == "k8s":
        return K8sBackend(clock=shared_clock)
    return InMemoryBackend(clock=shared_clock)


def _build_memo(backend_type: str | None = None) -> dict[str, Any]:
    """构造 kopf memo · 服务实例注册（Step 5 完整装配 + PR-2 backend 选择）。

    5 依赖单点注入：
    - clock: SystemClock（§M-1.5 单实例 · 三方共享）
    - backend: InMemoryBackend | K8sBackend（由 backend_type 选择）
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

    Args:
        backend_type: 显式指定 ("in_process" / "k8s")；None 时从 env var 读
    """
    clock = SystemClock()
    backend = _build_backend(backend_type=backend_type, clock=clock)
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


def _build_app(memo: dict[str, Any]) -> Starlette:
    """构造 starlette app · 注入 service + clock（L4-Phase3 PR-1）。

    Clock 与 L3-6 §M-1.5 三方共享同源（memo["clock"]）。
    """
    return create_app(
        service=memo["memory_in_process_service"],
        clock=memo["clock"],
    )


async def _run_uvicorn(app: Starlette) -> None:
    """uvicorn.Server 在当前 event loop 中运行（与 kopf 共享 · D 方案单进程）。

    lifespan="off"：starlette startup/shutdown 钩子不需要（service 已在 _build_memo 装配）。
    log_level="info"：生产等价；测试环境通过 TestClient 不经过 uvicorn。
    """
    config = uvicorn.Config(
        app=app,
        host=HTTP_HOST,
        port=HTTP_PORT,
        log_level="info",
        loop="asyncio",
        lifespan="off",
    )
    server = uvicorn.Server(config=config)
    await server.serve()


def main() -> None:
    """kopf operator + starlette HTTP server 同 event loop 启动入口。

    L4-Phase3 PR-1（D 方案单进程 · §2.1 starlette 选项 C）：
    - uvicorn 在 asyncio.create_task 中运行，与 kopf 共享 event loop
    - kopf.run() 完成（或 uvicorn 异常）后触发对方 graceful shutdown
    - /healthz 由 starlette 提供（替代 kopf 内置 liveness_endpoint）
    - Helm deployment livenessProbe/readinessProbe 路径无需变更（共用 /healthz · PR-4.1.1 #90）
    """
    memo = _build_memo()
    app = _build_app(memo)

    async def _amain() -> None:
        kopf_task = asyncio.create_task(kopf.run(memo=memo))
        server_task = asyncio.create_task(_run_uvicorn(app))
        # 等待任一完成 → 取消对方
        done, pending = await asyncio.wait(
            {kopf_task, server_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        for task in pending:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        # 让已完成 task 的异常正常冒泡（如有）
        for task in done:
            if not task.cancelled():
                exc = task.exception()
                if exc is not None:
                    raise exc

    asyncio.run(_amain())


if __name__ == "__main__":
    main()
