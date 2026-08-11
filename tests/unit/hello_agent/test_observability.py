"""Hello Agent · observability.py 测试 · HELLO-OBS-001~003（3 UT）。

L3-4 §9.7 锁定 4 Python runtime 指标（PR-1 验证）：
- python_gc_objects_collected_total
- process_cpu_seconds_total
- process_resident_memory_bytes
- process_open_fds
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

# ============================================================================
# 路径前置
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HA_SRC = _REPO_ROOT / "services" / "hello-agent" / "src"
_HA_PATH = str(_HA_SRC)
if _HA_PATH not in sys.path:
    sys.path.insert(0, _HA_PATH)

from superteam_a2a.hello_agent import create_app  # noqa: E402
from superteam_a2a.hello_agent.observability import (  # noqa: E402
    STRUCTLOG_KEYS,
    configure_structlog,
    get_logger,
)


@pytest.fixture
def client():
    """TestClient 实例（构造一次 · 复用）。"""
    return TestClient(create_app())


# ============================================================================
# HELLO-OBS-001 · /healthz + /readyz 返回 healthy/ready
# ============================================================================


def test_healthz_and_readyz_return_healthy_ready(client):
    """HELLO-OBS-001: GET /healthz 返回 {"status": "healthy"} · GET /readyz 返回 {"status": "ready"}。

    双探针 liveness + readiness 共享 8080 端口（L3-4 §9.7 不变量 5）。
    """
    h = client.get("/healthz")
    assert h.status_code == 200
    assert h.json() == {"status": "healthy"}

    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


# ============================================================================
# HELLO-OBS-002 · /metrics 返回 4 Python runtime 指标
# ============================================================================


def test_metrics_endpoint_returns_4_python_runtime_metrics(client):
    """HELLO-OBS-002: GET /metrics 返回 Prometheus 格式 + 4 Python runtime 指标。

    4 指标（L3-4 §9.7 锁定）：
    - python_gc_objects_collected_total（prometheus_client GCCollector 跨平台）
    - process_cpu_seconds_total（ProcessCollector · psutil 跨平台）
    - process_resident_memory_bytes（ProcessCollector · psutil 跨平台）
    - process_open_fds（ProcessCollector · psutil 跨平台）

    dev dep 声明 `psutil>=5.9,<7` 确保 Windows/Linux/macOS 跨平台可见。
    """
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    # 4 Python runtime 指标（prometheus_client 默认 + ProcessCollector + psutil）
    assert "python_gc_objects_collected_total" in body
    assert "process_cpu_seconds_total" in body
    assert "process_resident_memory_bytes" in body
    assert "process_open_fds" in body


# ============================================================================
# HELLO-OBS-003 · structlog 8 字段配置 + get_logger
# ============================================================================


def test_structlog_8_keys_and_get_logger():
    """HELLO-OBS-003: STRUCTLOG_KEYS 含 8 字段 + configure_structlog 幂等 + get_logger 返回 logger。

    8 字段：timestamp + level + event + logger + service + request_id + method + status。
    """
    assert len(STRUCTLOG_KEYS) == 8
    assert "timestamp" in STRUCTLOG_KEYS
    assert "level" in STRUCTLOG_KEYS
    assert "event" in STRUCTLOG_KEYS
    assert "logger" in STRUCTLOG_KEYS
    assert "service" in STRUCTLOG_KEYS
    assert "request_id" in STRUCTLOG_KEYS
    assert "method" in STRUCTLOG_KEYS
    assert "status" in STRUCTLOG_KEYS

    # configure_structlog 幂等（多次调用不抛异常）
    configure_structlog()
    configure_structlog(service_name="custom-name")

    # get_logger 返回 structlog BoundLogger
    logger = get_logger()
    assert logger is not None

    custom_logger = get_logger("custom_logger_name")
    assert custom_logger is not None
