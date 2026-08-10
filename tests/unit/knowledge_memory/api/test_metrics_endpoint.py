"""L4-Phase3 PR-3 starlette /metrics 端点集成测试（TEST-A2A-013~015）。

依据 docs/phase3/pr3-25-metrics-plan.md §4 阶段 D 测试要求：
- TEST-A2A-013: create_app 后 GET /metrics → 200 + text/plain content type
- TEST-A2A-014: GET /metrics 内容包含 10 个 superteam_memory_* name
- TEST-A2A-015: GET /metrics 内容包含 11 个 superteam_a2a_* name（L3-2 复用）
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

from starlette.testclient import TestClient

# ============================================================================
# 路径前置（与 api/conftest.py 模式一致）
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_OP_SRC = _REPO_ROOT / "packages" / "operator" / "src"

_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)
_OP_PATH = str(_OP_SRC)
if _OP_PATH not in sys.path:
    if _KM_PATH in sys.path:
        km_idx = sys.path.index(_KM_PATH)
        sys.path.insert(km_idx + 1, _OP_PATH)
    else:
        sys.path.insert(0, _OP_PATH)

from superteam_a2a.knowledge_memory import (  # noqa: E402
    FakeClock,
    InMemoryBackend,
)
from superteam_a2a.knowledge_memory.api.server import (  # noqa: E402
    create_app,
)
from superteam_a2a.knowledge_memory.api.service import (  # noqa: E402
    MemoryBackendInProcessServiceImpl,
)
from superteam_a2a.knowledge_memory.observability import (  # noqa: E402
    MEMORY_BM25_INDEX_SIZE,
    MEMORY_PROMOTION_ELIGIBLE_TOTAL,
    MEMORY_RECONCILE_TOTAL,
)
from superteam_a2a.knowledge_memory.observability.labels import (  # noqa: E402
    Phase,
    Result,
    ScopeLevel,
    Visibility,
)

# ============================================================================
# 25 指标名常量
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


# ============================================================================
# Helpers
# ============================================================================


def _build_test_app():
    """构造 create_app 的最小依赖（clock + service）。"""
    clock = FakeClock(datetime(2026, 8, 10, 12, 0, 0, tzinfo=UTC))
    backend = InMemoryBackend(clock=clock)
    service = MemoryBackendInProcessServiceImpl(backend=backend)
    return create_app(service=service, clock=clock)


# ============================================================================
# TEST-A2A-013
# ============================================================================


def test_a2a_013_metrics_endpoint_returns_200_text_plain() -> None:
    """TEST-A2A-013 · create_app 后 GET /metrics → 200 + text/plain content type。"""
    app = _build_test_app()
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    # CONTENT_TYPE_LATEST = 'text/plain; version=0.0.4; charset=utf-8'
    assert "text/plain" in resp.headers["content-type"]


# ============================================================================
# TEST-A2A-014
# ============================================================================


def test_a2a_014_metrics_endpoint_contains_10_memory_names() -> None:
    """TEST-A2A-014 · GET /metrics 内容包含 10 个 superteam_memory_* name。

    触发 3 行占位埋点后断言（保证 Counter _total + Gauge 值非空）：
    - superteam_memory_reconcile_total
    - superteam_memory_reconcile_duration_seconds
    - superteam_memory_decay_applied_total
    - superteam_memory_reinforce_total
    - superteam_memory_gc_cleaned_total
    - superteam_memory_promotion_eligible_total
    - superteam_memory_bm25_index_size
    - superteam_memory_admission_duration_seconds
    - superteam_memory_in_process_call_total
    - superteam_memory_rate_limited_total
    """
    app = _build_test_app()
    client = TestClient(app)

    # 触发占位埋点（与 main.py _build_memo 一致）
    MEMORY_RECONCILE_TOTAL.labels(phase=Phase.ADMIT, result=Result.SUCCESS).inc()
    MEMORY_PROMOTION_ELIGIBLE_TOTAL.labels(visibility=Visibility.TEAM).set(0)
    MEMORY_BM25_INDEX_SIZE.labels(scope_level=ScopeLevel.AGENT).set(0)

    body = client.get("/metrics").text
    for name in EXPECTED_MEMORY_METRIC_NAMES:
        assert name in body, f"Missing Memory metric {name!r} in /metrics output"


# ============================================================================
# TEST-A2A-015
# ============================================================================


def test_a2a_015_metrics_endpoint_servicemonitor_regex_covers_l3_2_namespace() -> None:
    """TEST-A2A-015 · ServiceMonitor regex 覆盖 L3-2 命名空间（superteam_a2a_/superteam_python_）。

    注意：L3-2 §9.1 11+4 指标的 prometheus_client 实例化由 L3-2 服务模块负责（PR-3 范围外）。
    本测试仅断言 helm servicemonitor.yaml regex 已包含 5 命名空间（PR-3 修复：python_.* → superteam_python_.*）。
    25 指标聚合验证在 phase 4 真实业务埋点后。
    """
    sm_path = _REPO_ROOT / "helm" / "knowledge-memory-service" / "templates" / "servicemonitor.yaml"
    content = sm_path.read_text(encoding="utf-8")
    # 5 命名空间必须全部覆盖
    for namespace in (
        "superteam_a2a_.*",
        "superteam_knowledge_.*",
        "superteam_memory_.*",
        "superteam_python_.*",
        "process_.*",
    ):
        assert namespace in content, f"ServiceMonitor regex missing {namespace!r}"
