"""H-RM-E2E-001: A2A recordMemory end-to-end via kind cluster.

Reference: Phase 2 plan §3.4 + L3-5 §4.3 line 1178 + L2-4 §6.4 wire contract.

Phase 3 PR-4 (#96) 实装：
- 上游 PR-1 (A2A HTTP JSON-RPC server · starlette) 已 merged
- 上游 PR-2 (K8sBackend) 已 merged
- 上游 PR-3 (25 metrics ServiceMonitor) 已 merged
- 本测试 unskip + 真实实装 apply Memory CR + POST /jsonrpc/record_memory round-trip

JSON-RPC 2.0 envelope（PR-1 server.py 严格遵循）：
- request:  {"jsonrpc": "2.0", "id": "<uuid>", "params": {...}}
- response: {"jsonrpc": "2.0", "result": {...}, "id": ...}  或 error envelope
- 成功路径：response["error"] is None + response["result"] 含 record_memory_result
- 12 MEMORY_* 错误码 → JSON-RPC error.code 1:1 映射

跳过条件：chart 不完整（e2e-envtest workflow 真验证 · 本地不可用）
"""

from __future__ import annotations

import contextlib
import json
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

import pytest

# Path setup for service imports (matches tests/unit/knowledge_memory pattern)
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Phase 2 PR-4.1.1 共享常量 + L4-Phase3 PR-1 port-forward 端口
NAMESPACE = "superteam-a2a-system"
RELEASE_NAME = "kmem-lifecycle-test"
SELECTOR = "app.kubernetes.io/name=knowledge-memory-service"
WAIT_BOUND_TIMEOUT = "120s"  # 60s timer + buffer
SERVICE_PORT = 8080
LOCAL_PORT = 8080


# ============================================================================
# Helpers · 复用 LIFECYCLE-E2E-001 模式 + 新增 port-forward helper
# ============================================================================


def _ensure_helm_install(
    kind_cluster: str,
    chart_status: tuple[bool, list[str]],
) -> None:
    """Ensure helm chart is installed and pods are ready (idempotent across tests).

    与 test_memory_lifecycle.py 完全一致的复用模式（chart 共享 release）。
    LEADER-E2E-002 用独立 release "kmem-leader-test"；本测试与 LIFECYCLE 共享。
    """
    if not chart_status[0]:
        pytest.skip(
            f"Helm chart incomplete (missing: {chart_status[1]})",
            allow_module_level=False,
        )

    # Lazy import (避免 tests/__init__.py 不存在的 collection 错误)
    from tests.e2e.conftest import CHART_PATH  # type: ignore[import-not-found]

    list_result = subprocess.run(
        [
            "helm",
            "list",
            "--kubeconfig",
            kind_cluster,
            "-n",
            NAMESPACE,
            "--short",
            "-f",
            RELEASE_NAME,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if RELEASE_NAME in list_result.stdout:
        return  # 已部署

    install_result = subprocess.run(
        [
            "helm",
            "install",
            RELEASE_NAME,
            str(CHART_PATH),
            "--kubeconfig",
            kind_cluster,
            "--namespace",
            NAMESPACE,
            "--create-namespace",
            "--set",
            "image.pullPolicy=Never",
            "--wait",
            "--timeout",
            "120s",
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert install_result.returncode == 0, f"helm install failed: {install_result.stderr}"

    wait_result = subprocess.run(
        [
            "kubectl",
            "wait",
            "--for=condition=ready",
            "pod",
            "-l",
            SELECTOR,
            "-n",
            NAMESPACE,
            "--kubeconfig",
            kind_cluster,
            "--timeout",
            "120s",
        ],
        capture_output=True,
        text=True,
        timeout=150,
    )
    assert wait_result.returncode == 0, f"kubectl wait failed: {wait_result.stderr}"


def _port_forward_service(
    *,
    kind_cluster: str,
    service_name: str,
    local_port: int,
    remote_port: int,
) -> subprocess.Popen[bytes]:
    """启动 kubectl port-forward · 返回 subprocess.Popen。"""
    service_resource = f"svc/{service_name}"
    proc = subprocess.Popen(
        [
            "kubectl",
            "port-forward",
            service_resource,
            f"{local_port}:{remote_port}",
            "--kubeconfig",
            kind_cluster,
            "-n",
            NAMESPACE,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def _wait_port_listening(local_port: int, timeout_seconds: float = 15.0) -> bool:
    """socket 探测 localhost:local_port 直到端口可连接（避免 port-forward 启动 race）。"""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", local_port), timeout=1.0):
                return True
        except (TimeoutError, OSError):
            time.sleep(0.2)
    return False


def _cleanup_port_forward(proc: subprocess.Popen[bytes] | None) -> None:
    """严格清理 port-forward subprocess：terminate → wait 5s → kill -9 fallback."""
    if proc is None:
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=2)
    except OSError:
        pass


def _post_jsonrpc(
    *,
    url: str,
    payload: dict[str, Any],
    timeout: float = 10.0,
) -> dict[str, Any]:
    """POST JSON-RPC 2.0 envelope via urllib (no extra deps)."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
    except urllib_error.HTTPError as exc:
        raw_bytes = exc.read()
    return json.loads(raw_bytes.decode("utf-8"))


def _memory_cr_yaml(
    *,
    name: str,
    namespace: str,
    scope_ref: str = "default-scope",
    agent_ref: str = "default-agent",
    industry: str = "tech",
    content: dict[str, Any] | None = None,
    summary: str = "E2E test memory",
    confidence: float = 0.85,
    decay_days: int = 30,
) -> str:
    """构造 K8s Memory CR apply YAML（camelCase wire format，与 LIFECYCLE 一致）。"""
    if content is None:
        content = {"key1": "value1"}
    return (
        f"---\n"
        f"apiVersion: memory.superteam-a2a.io/v1alpha1\n"
        f"kind: Memory\n"
        f"metadata:\n"
        f"  name: {name}\n"
        f"  namespace: {namespace}\n"
        f"spec:\n"
        f"  scopeRef:\n"
        f"    name: {scope_ref}\n"
        f"  agentRef:\n"
        f"    name: {agent_ref}\n"
        f"  industry: {industry}\n"
        f"  content:\n"
        f"    key1: {content['key1']}\n"
        f"  summary: {summary}\n"
        f"  confidence: {confidence}\n"
        f"  decayDays: {decay_days}\n"
    )


def _service_name() -> str:
    """读取 helm chart 全限定 service name（template 渲染）。"""
    from tests.e2e.conftest import CHART_PATH  # type: ignore[import-not-found]

    result = subprocess.run(
        [
            "helm",
            "template",
            RELEASE_NAME,
            str(CHART_PATH),
            "--namespace",
            NAMESPACE,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"helm template failed: {result.stderr}"
    # 提取 Service.metadata.name（位于 "kind: Service" 之后）
    lines = result.stdout.splitlines()
    in_service = False
    for line in lines:
        if line.strip() == "kind: Service":
            in_service = True
            continue
        if in_service and line.strip().startswith("name:") and line.startswith("  name:"):
            return line.split(":", 1)[1].strip()
    # Fallback: helm chart fullname default
    return "knowledge-memory-service"


def _wait_observed_generation(
    *,
    kind_cluster: str,
    name: str,
    namespace: str,
    timeout_seconds: int = 120,
) -> int:
    """kubectl wait observedGeneration >= 1 with timeout · 60s timer + buffer."""
    result = subprocess.run(
        [
            "kubectl",
            "wait",
            "--for=jsonpath={.status.observedGeneration}",
            "memory",
            name,
            "-n",
            namespace,
            "--kubeconfig",
            kind_cluster,
            f"--timeout={timeout_seconds}s",
        ],
        capture_output=True,
        text=True,
        timeout=timeout_seconds + 10,
    )
    if result.returncode != 0:
        # jsonpath wait for integer >= 1 not directly supported by kubectl wait;
        # fallback: read observedGeneration and check >= 1
        gen_result = subprocess.run(
            [
                "kubectl",
                "get",
                "memory",
                name,
                "-n",
                namespace,
                "--kubeconfig",
                kind_cluster,
                "-o",
                "jsonpath={.status.observedGeneration}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return int(gen_result.stdout.strip() or "0")
    # 若 jsonpath wait 成功（observedGeneration 存在），读取实际值
    gen_result = subprocess.run(
        [
            "kubectl",
            "get",
            "memory",
            name,
            "-n",
            namespace,
            "--kubeconfig",
            kind_cluster,
            "-o",
            "jsonpath={.status.observedGeneration}",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return int(gen_result.stdout.strip() or "0")


# ============================================================================
# H-RM-E2E-001
# ============================================================================


@pytest.mark.e2e
def test_h_rm_e2e_001_a2a_record_memory_via_a2a_call(
    kind_cluster: str,
    chart_status: tuple[bool, list[str]],
    helm_client: str,
) -> None:
    """H-RM-E2E-001 · A2A recordMemory → POST /jsonrpc/record_memory 完整 round-trip。

    完整 E2E 验证：
    1. helm install（in_process backend · rc=1 · image.pullPolicy=Never）
    2. kubectl create namespace e2e-h-rm-001
    3. kubectl apply Memory CR（含 scopeRef/agentRef/content/summary/confidence）
    4. kubectl wait observedGeneration >= 1 (timeout 120s · 60s timer + buffer)
    5. kubectl port-forward service 8080:8080
    6. POST http://localhost:8080/jsonrpc/record_memory · JSON-RPC envelope
    7. 断言 response["jsonrpc"] == "2.0" + response["error"] is None +
       response["result"] 含有效 record_memory_result 字段

    跳过条件：chart 不完整（e2e-envtest workflow 真验证）
    """
    _ensure_helm_install(kind_cluster, chart_status)

    test_namespace = "e2e-h-rm-001"
    mem_name = "e2e-rm-mem-001"
    request_id = f"h-rm-{uuid.uuid4().hex[:8]}"

    # 创建测试 namespace
    subprocess.run(
        [
            "kubectl",
            "create",
            "namespace",
            test_namespace,
            "--kubeconfig",
            kind_cluster,
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )

    service_name = _service_name()
    pf_proc: subprocess.Popen[bytes] | None = None
    try:
        # 1. apply Memory CR
        cr_yaml = _memory_cr_yaml(
            name=mem_name,
            namespace=test_namespace,
            scope_ref="rm-scope",
            agent_ref="rm-agent",
            industry="tech",
            summary="H-RM-E2E-001 A2A recordMemory round-trip test",
            confidence=0.92,
        )
        apply_result = subprocess.run(
            ["kubectl", "apply", "-f", "-", "--kubeconfig", kind_cluster],
            input=cr_yaml,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert apply_result.returncode == 0, f"kubectl apply failed: {apply_result.stderr}"

        # 2. 等待 60s timer + kopf reconcile → observedGeneration >= 1
        observed_gen = _wait_observed_generation(
            kind_cluster=kind_cluster,
            name=mem_name,
            namespace=test_namespace,
            timeout_seconds=120,
        )
        assert observed_gen >= 1, f"Memory CR apply 后 observedGeneration 未递增: {observed_gen}"

        # 3. kubectl port-forward service 8080:8080 + socket 探测
        pf_proc = _port_forward_service(
            kind_cluster=kind_cluster,
            service_name=service_name,
            local_port=LOCAL_PORT,
            remote_port=SERVICE_PORT,
        )
        port_ready = _wait_port_listening(LOCAL_PORT, timeout_seconds=15.0)
        assert port_ready, f"port-forward to {service_name}:{SERVICE_PORT} not ready in 15s"

        # 4. POST /jsonrpc/record_memory (K8s wire format)
        params = {
            "apiVersion": "memory.superteam-a2a.io/v1alpha1",
            "kind": "Memory",
            "metadata": {
                "name": f"{mem_name}-via-a2a",
                "namespace": test_namespace,
            },
            "spec": {
                "scopeRef": {"name": "rm-scope-via-a2a"},
                "agentRef": {"name": "rm-agent-via-a2a"},
                "content": {"key": "value"},
                "summary": "Created via A2A HTTP JSON-RPC record_memory",
                "confidence": 0.88,
                "decayDays": 30,
            },
        }
        envelope = {"jsonrpc": "2.0", "id": request_id, "params": params}
        response = _post_jsonrpc(
            url=f"http://localhost:{LOCAL_PORT}/jsonrpc/record_memory",
            payload=envelope,
            timeout=10.0,
        )

        # 5. 断言 JSON-RPC 2.0 envelope
        assert response.get("jsonrpc") == "2.0", f"response.jsonrpc != '2.0': {response}"
        assert response.get("id") == request_id, (
            f"response.id mismatch: expected={request_id} got={response.get('id')}"
        )
        assert response.get("error") is None, (
            f"response.error expected None · got: {response.get('error')}"
        )
        result = response.get("result")
        assert isinstance(result, dict), f"response.result must be object: {result!r}"
        # MemoryRecordResult 字段（pyright: MemoryRecordResult model_dump snake_case wire）
        assert "resource_version" in result, f"response.result 缺 resource_version: {result}"
        assert result["resource_version"] >= 1, (
            f"resource_version must be >= 1: {result['resource_version']}"
        )
        assert "memory" in result, f"response.result 缺 memory: {result}"
        assert result["memory"]["metadata"]["name"] == f"{mem_name}-via-a2a"
        assert result["memory"]["metadata"]["namespace"] == test_namespace

    finally:
        # Cleanup: port-forward + namespace
        _cleanup_port_forward(pf_proc)
        subprocess.run(
            [
                "kubectl",
                "delete",
                "namespace",
                test_namespace,
                "--ignore-not-found",
                "--wait=false",
                "--kubeconfig",
                kind_cluster,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
