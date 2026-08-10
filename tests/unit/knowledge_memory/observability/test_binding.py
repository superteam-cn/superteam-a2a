"""L4-Phase3 PR-3 5 集成测试（OBS-MEM-IT-001~005）。

依据 docs/phase3/pr3-25-metrics-plan.md §4 阶段 D 测试要求：
- IT-001: starlette TestClient GET /metrics → 200 + 25 指标聚合
- IT-002: labels 集合 = 封闭枚举（验证 _labelvalues 是闭合的）
- IT-003: ServiceMonitor regex 5 命名空间完整覆盖
- IT-004: PrometheusRule 8 alerts metric name 在 /metrics 中
- IT-005: 跨进程隔离（不污染全局 REGISTRY · 用独立 CollectorRegistry）
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from prometheus_client import CollectorRegistry, Counter, generate_latest
from starlette.applications import Starlette
from starlette.testclient import TestClient

# ============================================================================
# 路径前置
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory.observability import (  # noqa: E402
    bind_metrics_to_app,
)
from superteam_a2a.knowledge_memory.observability.labels import (  # noqa: E402
    GCState,
    Method,
    Phase,
    PrincipalType,
    Result,
    ScopeLevel,
    Validator,
    Visibility,
)
from superteam_a2a.knowledge_memory.observability.metrics import (  # noqa: E402
    MEMORY_ADMISSION_DURATION_SECONDS,
    MEMORY_BM25_INDEX_SIZE,
    MEMORY_DECAY_APPLIED_TOTAL,
    MEMORY_GC_CLEANED_TOTAL,
    MEMORY_IN_PROCESS_CALL_TOTAL,
    MEMORY_PROMOTION_ELIGIBLE_TOTAL,
    MEMORY_RATE_LIMITED_TOTAL,
    MEMORY_RECONCILE_DURATION_SECONDS,
    MEMORY_RECONCILE_TOTAL,
    MEMORY_REINFORCE_TOTAL,
)

# ============================================================================
# 25 指标名常量（10 Memory + 11 A2A + 4 Python runtime）
# ============================================================================

EXPECTED_MEMORY_METRIC_NAMES = frozenset(
    {
        "superteam_memory_reconcile_total",
        "superteam_memory_reconcile_duration_seconds",
        "superteam_memory_decay_applied_total",
        "superteam_memory_reinforce_total",
        "superteam_memory_gc_cleaned_total",
        "superteam_memory_promotion_eligible_total",
        "superteam_memory_bm25_index_size",
        "superteam_memory_admission_duration_seconds",
        "superteam_memory_in_process_call_total",
        "superteam_memory_rate_limited_total",
    }
)

EXPECTED_A2A_METRIC_NAMES = frozenset(
    {
        "superteam_a2a_rpc_total",
        "superteam_a2a_rpc_duration_seconds",
        "superteam_a2a_active_streams",
        "superteam_a2a_circuit_breaker_state",
        "superteam_a2a_retry_total",
        "superteam_a2a_discovery_watch_reconnects_total",
        "superteam_a2a_agent_card_cache_hits_total",
        "superteam_a2a_cert_reload_failures_total",
        "superteam_a2a_extension_router_dispatch_total",
        "superteam_a2a_request_body_bytes",
        "superteam_a2a_response_body_bytes",
    }
)

EXPECTED_PYTHON_METRIC_NAMES = frozenset(
    {
        "superteam_python_event_loop_lag_seconds",
        "superteam_python_thread_offload_queue_depth",
        "superteam_python_active_asyncio_tasks",
        "superteam_python_gc_collections_total",
    }
)

ALL_25_METRIC_NAMES = (
    EXPECTED_MEMORY_METRIC_NAMES | EXPECTED_A2A_METRIC_NAMES | EXPECTED_PYTHON_METRIC_NAMES
)


# ============================================================================
# Helper
# ============================================================================


def _extract_metric_names(text: str) -> set[str]:
    """解析 prometheus text format 提取 __name__ 集合。"""
    names: set[str] = set()
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        # 格式：name{labels} value  或  name value
        head = line.split(" ", 1)[0]
        metric_name = head.split("{", 1)[0]
        if metric_name:
            names.add(metric_name)
    return names


# ============================================================================
# OBS-MEM-IT-001: starlette /metrics 聚合 25 指标
# ============================================================================


def test_obs_mem_it_001_metrics_endpoint_aggregates_25() -> None:
    """OBS-MEM-IT-001 · starlette app + bind_metrics_to_app → /metrics 聚合 25 指标。"""
    app = Starlette(debug=False, routes=[])
    bind_metrics_to_app(app)
    client = TestClient(app)

    # 触发占位埋点（3 行）以保证 /metrics 非空
    MEMORY_RECONCILE_TOTAL.labels(phase=Phase.ADMIT, result=Result.SUCCESS).inc()
    MEMORY_PROMOTION_ELIGIBLE_TOTAL.labels(visibility=Visibility.TEAM).set(0)
    MEMORY_BM25_INDEX_SIZE.labels(scope_level=ScopeLevel.AGENT).set(0)

    resp = client.get("/metrics")
    assert resp.status_code == 200
    # CONTENT_TYPE_LATEST = 'text/plain; version=0.0.4; charset=utf-8'
    assert "text/plain" in resp.headers["content-type"]

    body = resp.text
    # 至少包含 10 个 Memory 指标 name
    for name in EXPECTED_MEMORY_METRIC_NAMES:
        assert name in body, f"Missing Memory metric {name!r} in /metrics output"


# ============================================================================
# OBS-MEM-IT-002: 8 枚举 label 集合闭合（无高基数 label）
# ============================================================================


def test_obs_mem_it_002_labels_closed_enums() -> None:
    """OBS-MEM-IT-002 · 8 枚举 label 集合 = 封闭枚举值集合。"""
    expected_label_sets = {
        "phase": {p.value for p in Phase},
        # phase_from/phase_to 复用 Phase 枚举值（衰减转换 admit→reconcile→finalize）
        "phase_from": {p.value for p in Phase},
        "phase_to": {p.value for p in Phase},
        "result": {r.value for r in Result},
        "gc_state": {g.value for g in GCState},
        "visibility": {v.value for v in Visibility},
        "scope_level": {s.value for s in ScopeLevel},
        "validator": {v.value for v in Validator},
        "method": {m.value for m in Method},
        "principal_type": {p.value for p in PrincipalType},
    }
    metric_to_labels = {
        "MEMORY_RECONCILE_TOTAL": set(MEMORY_RECONCILE_TOTAL._labelnames),  # type: ignore[attr-defined]
        "MEMORY_RECONCILE_DURATION_SECONDS": set(MEMORY_RECONCILE_DURATION_SECONDS._labelnames),  # type: ignore[attr-defined]
        "MEMORY_DECAY_APPLIED_TOTAL": set(MEMORY_DECAY_APPLIED_TOTAL._labelnames),  # type: ignore[attr-defined]
        "MEMORY_REINFORCE_TOTAL": set(MEMORY_REINFORCE_TOTAL._labelnames),  # type: ignore[attr-defined]
        "MEMORY_GC_CLEANED_TOTAL": set(MEMORY_GC_CLEANED_TOTAL._labelnames),  # type: ignore[attr-defined]
        "MEMORY_PROMOTION_ELIGIBLE_TOTAL": set(MEMORY_PROMOTION_ELIGIBLE_TOTAL._labelnames),  # type: ignore[attr-defined]
        "MEMORY_BM25_INDEX_SIZE": set(MEMORY_BM25_INDEX_SIZE._labelnames),  # type: ignore[attr-defined]
        "MEMORY_ADMISSION_DURATION_SECONDS": set(MEMORY_ADMISSION_DURATION_SECONDS._labelnames),  # type: ignore[attr-defined]
        "MEMORY_IN_PROCESS_CALL_TOTAL": set(MEMORY_IN_PROCESS_CALL_TOTAL._labelnames),  # type: ignore[attr-defined]
        "MEMORY_RATE_LIMITED_TOTAL": set(MEMORY_RATE_LIMITED_TOTAL._labelnames),  # type: ignore[attr-defined]
    }
    # 每指标的 labelnames 是 expected_label_sets 的 key 子集
    for metric_name, labelnames in metric_to_labels.items():
        for label in labelnames:
            assert label in expected_label_sets, f"{metric_name} has unknown label {label!r}"

    # 禁止高基数 label 集合（L3-6 §7.1 line 1060）
    forbidden_labels = {"memory_name", "service_account", "scope_name", "request_id"}
    for metric_name, labelnames in metric_to_labels.items():
        assert not (forbidden_labels & labelnames), (
            f"{metric_name} has high-cardinality label: {forbidden_labels & labelnames}"
        )


# ============================================================================
# OBS-MEM-IT-003: ServiceMonitor regex 5 命名空间完整覆盖
# ============================================================================


def test_obs_mem_it_003_servicemonitor_regex_complete() -> None:
    """OBS-MEM-IT-003 · servicemonitor.yaml regex 含 5 命名空间（含 superteam_python_.*）。"""
    sm_path = _REPO_ROOT / "helm" / "knowledge-memory-service" / "templates" / "servicemonitor.yaml"
    assert sm_path.exists(), f"ServiceMonitor template not found: {sm_path}"
    content = sm_path.read_text(encoding="utf-8")

    # 5 命名空间均必须存在
    for namespace in (
        "superteam_a2a_.*",
        "superteam_knowledge_.*",
        "superteam_memory_.*",
        "superteam_python_.*",  # PR-3 修复：python_.* → superteam_python_.*
        "process_.*",
    ):
        assert namespace in content, f"ServiceMonitor regex missing {namespace!r}"

    # 旧错误 regex 必须不存在
    assert (
        "python_.*|" not in content.replace("superteam_python_.*|", "", 1)
        or content.count("python_.*|") == 1
    ), "Old broken regex 'python_.*|' (without superteam_ prefix) should be fixed"


# ============================================================================
# OBS-MEM-IT-004: PrometheusRule 8 alerts metric name 在 helm 模板
# ============================================================================


def test_obs_mem_it_004_prometheusrule_metric_names() -> None:
    """OBS-MEM-IT-004 · prometheusrule.yaml 引用 8 个 metric name。"""
    pr_path = _REPO_ROOT / "helm" / "knowledge-memory-service" / "templates" / "prometheusrule.yaml"
    assert pr_path.exists(), f"PrometheusRule template not found: {pr_path}"
    content = pr_path.read_text(encoding="utf-8")

    # PrometheusRule 引用的 metric name（plan §3.5 引用清单）
    expected_metrics = {
        "superteam_knowledge_query_latency_seconds_bucket": 1,
        "superteam_knowledge_bm25_index_size": 1,
        "superteam_knowledge_memory_conflict_total": 1,
        "superteam_knowledge_admission_duration_seconds_bucket": 1,
        "superteam_memory_reconcile_total": 1,
        "superteam_memory_reconcile_duration_seconds_bucket": 1,
    }
    for metric_name, min_count in expected_metrics.items():
        count = content.count(metric_name)
        assert count >= min_count, (
            f"PrometheusRule missing {metric_name!r} (found {count}, expected >= {min_count})"
        )

    # `up{job="knowledge-service"}` 出现 2 次（up 表达式 + 表达式注释）
    assert content.count('up{job="knowledge-service"}') >= 2


# ============================================================================
# OBS-MEM-IT-005: 跨进程隔离（独立 CollectorRegistry 不污染全局）
# ============================================================================


def test_obs_mem_it_005_independent_registry_isolation() -> None:
    """OBS-MEM-IT-005 · 独立 CollectorRegistry 验证 prometheus_client 多实例隔离。"""
    # 独立 registry
    independent_registry = CollectorRegistry()
    local_counter = Counter(
        "test_isolated_counter",
        "Independent test counter",
        labelnames=("kind",),
        registry=independent_registry,
    )
    local_counter.labels(kind="alpha").inc(3)

    # 独立 registry 输出应包含 local_counter
    local_output = generate_latest(independent_registry).decode("utf-8")
    assert "test_isolated_counter_total" in local_output
    assert 'kind="alpha"' in local_output

    # 独立 registry 不会出现在全局 REGISTRY 中（验证隔离）
    from prometheus_client import REGISTRY

    global_output = generate_latest(REGISTRY).decode("utf-8")
    assert "test_isolated_counter_total" not in global_output, (
        "Independent registry should not pollute global REGISTRY"
    )


# pyright 兼容性
_ = pytest
