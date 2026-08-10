"""Hello Agent · observability 子模块（4 Python runtime 指标 + structlog 8 字段 + /metrics）。

L3-4 §9.7 锁定 4 指标（与 L3-5 25 Memory 指标命名空间独立 · 避免冲突）：
- python_gc_objects_collected_total（prometheus_client 默认 · 跨平台）
- process_cpu_seconds_total
- process_resident_memory_bytes
- process_open_fds

Windows 兼容策略：prometheus_client 默认 ProcessCollector 仅在 Linux /proc 可用，
本模块提供 psutil-based fallback（_PsutilProcessCollector）· 自动注册替换默认。
Linux/macOS 系统走默认 /proc 路径 · Windows 走 psutil 路径。

8 字段结构化日志（structlog）：timestamp + level + event + logger + service + request_id +
method + status。

/metrics 路由通过 bind_metrics_to_app(app) 注册到 starlette app（与 healthz 同端口 8080）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from prometheus_client.metrics_core import CounterMetricFamily, GaugeMetricFamily
from prometheus_client.registry import Collector
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

if TYPE_CHECKING:

    class _PsutilProcessLike:
        """psutil.Process 的最小接口（避免 pyright 在 None context 报错）。"""

        def oneshot(self) -> Any: ...
        def cpu_times(self) -> Any: ...
        def memory_info(self) -> Any: ...
        def create_time(self) -> float: ...
        def num_fds(self) -> int: ...
        def num_handles(self) -> int: ...
else:
    _PsutilProcessLike = object  # runtime fallback

# ============================================================================
# Structlog 配置（8 字段结构化日志）
# ============================================================================

STRUCTLOG_KEYS: tuple[str, ...] = (
    "timestamp",
    "level",
    "event",
    "logger",
    "service",
    "request_id",
    "method",
    "status",
)


def configure_structlog(*, service_name: str = "hello-agent") -> None:
    """配置 structlog · 8 字段固定 + 服务名注入。

    幂等：多次调用安全（structlog.configure_reset + configure）。
    """
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.dict_tracebacks,
            _inject_service(service_name=service_name),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _inject_service(*, service_name: str) -> Any:
    """structlog processor · 注入 service 字段。"""

    def _processor(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        event_dict.setdefault("service", service_name)
        return event_dict

    return _processor


def get_logger(name: str = "hello_agent") -> Any:
    """获取 structlog logger（统一入口）。"""
    return structlog.get_logger(name)


# ============================================================================
# Windows 兼容 · psutil-based ProcessCollector
# ============================================================================


class _PsutilProcessCollector(Collector):
    """Windows/macOS 兼容的 ProcessCollector（prometheus_client 默认仅 Linux）。

    4 个 process_* 指标与默认 ProcessCollector 同 schema：
    - process_cpu_seconds_total（Counter）
    - process_resident_memory_bytes（Gauge）
    - process_virtual_memory_bytes（Gauge）
    - process_start_time_seconds（Gauge）
    - process_open_fds（Gauge · 跨平台 · Windows 退化为 -1）
    """

    def __init__(self) -> None:
        self._process: Any = None
        self._import_psutil()

    def _import_psutil(self) -> None:
        try:
            import psutil  # type: ignore[import-not-found]

            self._process = psutil.Process()
        except ImportError:
            self._process = None

    def collect(self) -> Any:  # type: ignore[override]
        proc = self._process
        if proc is None:
            return []
        try:
            with proc.oneshot():
                cpu_times = proc.cpu_times()
                mem_info = proc.memory_info()
                # 累计 CPU 时间 = user + system
                cpu_total = float(cpu_times.user + cpu_times.system)
                rss = float(mem_info.rss)
                vms = float(mem_info.vms)

                # 进程启动时间
                start_time = float(proc.create_time())

                # process_open_fds（Unix num_fds） · Windows num_handles 退化
                num_fds: float
                num_fds_attr = getattr(proc, "num_fds", None)
                if callable(num_fds_attr):
                    try:
                        num_fds = float(num_fds_attr())  # type: ignore[arg-type]
                    except (AttributeError, OSError):
                        num_fds = -1.0
                else:
                    num_handles_attr = getattr(proc, "num_handles", None)
                    if callable(num_handles_attr):
                        try:
                            num_fds = float(num_handles_attr())  # type: ignore[arg-type]
                        except (AttributeError, OSError):
                            num_fds = -1.0
                    else:
                        num_fds = -1.0
        except OSError:
            return []

        metrics: list[Any] = [
            CounterMetricFamily(
                "process_cpu_seconds_total",
                "Total user and system CPU time spent in seconds.",
                value=cpu_total,
            ),
            GaugeMetricFamily(
                "process_resident_memory_bytes",
                "Resident memory size in bytes.",
                value=rss,
            ),
            GaugeMetricFamily(
                "process_virtual_memory_bytes",
                "Virtual memory size in bytes.",
                value=vms,
            ),
            GaugeMetricFamily(
                "process_start_time_seconds",
                "Start time of the process since unix epoch in seconds.",
                value=start_time,
            ),
        ]
        if num_fds >= 0.0:
            metrics.append(
                GaugeMetricFamily(
                    "process_open_fds",
                    "Number of open file descriptors (Unix) or handles (Windows).",
                    value=num_fds,
                )
            )
        return metrics


# ============================================================================
# /metrics 路由 + 4 Python runtime 指标注册
# ============================================================================


def _register_default_metrics() -> None:
    """注册 prometheus_client 默认 collector + Windows-compatible ProcessCollector fallback。

    默认 Linux /proc-based ProcessCollector 保留；Windows 上若默认未产出 4 指标，
    自动 unregister + 注册 _PsutilProcessCollector。
    """
    from prometheus_client import (  # noqa: F401
        GC_COLLECTOR,
        PLATFORM_COLLECTOR,
        PROCESS_COLLECTOR,
    )

    # 检测默认 ProcessCollector 是否产出 process_cpu_seconds_total（Linux 才有）
    sample = generate_latest(REGISTRY).decode("utf-8", errors="ignore")
    if "process_cpu_seconds_total" not in sample:
        # Windows/macOS fallback：unregister 默认 ProcessCollector + 注册 psutil 版
        from prometheus_client.process_collector import ProcessCollector

        for collector in list(REGISTRY._collector_to_names.keys()):  # type: ignore[attr-defined]
            if isinstance(collector, ProcessCollector):
                REGISTRY.unregister(collector)
        REGISTRY.register(_PsutilProcessCollector())


async def metrics_endpoint(request: Request) -> Response:
    """GET /metrics · prometheus text format 0.0.4 输出（4 指标聚合）。"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


async def healthz(request: Request) -> JSONResponse:
    """GET /healthz · liveness probe。"""
    return JSONResponse({"status": "healthy"})


async def readyz(request: Request) -> JSONResponse:
    """GET /readyz · readiness probe。"""
    return JSONResponse({"status": "ready"})


def bind_metrics_to_app(app: Any) -> None:
    """注册 GET /metrics + /healthz + /readyz route 到 starlette app（端口 8080 共享）。

    与 agent.py 已注册的 /.well-known/agent.json + /a2a/sendMessage 端点互补。
    """
    _register_default_metrics()
    app.routes.append(  # type: ignore[attr-defined]
        Route("/metrics", metrics_endpoint, methods=["GET"])
    )
    app.routes.append(  # type: ignore[attr-defined]
        Route("/healthz", healthz, methods=["GET"])
    )
    app.routes.append(  # type: ignore[attr-defined]
        Route("/readyz", readyz, methods=["GET"])
    )


__all__ = [
    "STRUCTLOG_KEYS",
    "bind_metrics_to_app",
    "configure_structlog",
    "get_logger",
]
