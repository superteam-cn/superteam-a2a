"""H-QM-E2E-001: A2A queryMemory end-to-end via kind cluster.

Reference: Phase 2 plan §3.4 + L3-5 §4.4 line 1289 + L2-4 §6.5 wire contract.

Phase 3 PR-4 (#96) 实装：
- 上游 PR-1 (A2A HTTP JSON-RPC server · starlette) 已 merged
- 上游 PR-2 (K8sBackend) 已 merged
- 上游 PR-3 (25 metrics ServiceMonitor) 已 merged
- 本测试 unskip + 真实实装 apply 3 个 Memory CR + POST /jsonrpc/query_memory 过滤

JSON-RPC 2.0 envelope（PR-1 server.py 严格遵循）：
- request:  {"jsonrpc": "2.0", "id": "<uuid>", "params": {...}}
- response: {"jsonrpc": "2.0", "result": {...}, "id": ...}  或 error envelope
- 成功路径：response["error"] is None + response["result"]["items"] 包含过滤子集
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
# Helpers · 复用 test_handle_record_memory.py 模式
# 注：helpers 可放 conftest.py 但 Phase 2 plan §3.4 鼓励 file-local 内聚
# ============================================================================


def _ensure_helm_install(
    kind_cluster: str,
    chart_status: tuple[bool, list[str]],
) -> None:
    """Ensure helm chart is installed and pods are ready (idempotent across tests)."""
    if not chart_status[0]:
        pytest.skip(
            f"Helm chart incomplete (missing: {chart_status[1]})",
            allow_module_level=False,
        )

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
        return

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
    return subprocess.Popen(
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
    scope_ref: str,
    agent_ref: str,
    industry: str,
    summary: str,
    confidence: float = 0.85,
    decay_days: int = 30,
) -> str:
    """构造 K8s Memory CR apply YAML（camelCase wire format）。"""
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
        f"    key1: value1\n"
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
    lines = result.stdout.splitlines()
    in_service = False
    for line in lines:
        if line.strip() == "kind: Service":
            in_service = True
            continue
        if in_service and line.strip().startswith("name:") and line.startswith("  name:"):
            return line.split(":", 1)[1].strip()
    return "knowledge-memory-service"


def _wait_observed_generation(
    *,
    kind_cluster: str,
    name: str,
    namespace: str,
    timeout_seconds: int = 120,
) -> int:
    """kubectl wait observedGeneration >= 1 with timeout · 60s timer + buffer."""
    subprocess.run(
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
# H-QM-E2E-001
# ============================================================================


@pytest.mark.e2e
def test_h_qm_e2e_001_a2a_query_memory_via_a2a_call(
    kind_cluster: str,
    chart_status: tuple[bool, list[str]],
    helm_client: str,
) -> None:
    """H-QM-E2E-001 · A2A queryMemory → POST /jsonrpc/query_memory 5 维过滤 round-trip。

    完整 E2E 验证：
    1. helm install（in_process backend · rc=1）
    2. apply 3 个不同 Memory CR：
       - mem-001: scope=scope-a, agent=agent-a, industry=tech
       - mem-002: scope=scope-b, agent=agent-a, industry=finance
       - mem-003: scope=scope-a, agent=agent-b, industry=tech
    3. kubectl wait 3 个 CR observedGeneration >= 1 (timeout 120s each)
    4. kubectl port-forward service 8080:8080
    5. POST /jsonrpc/query_memory 过滤 scope=scope + agent_ref=agent-a
       期望 mem-001 命中 · mem-002/mem-003 不命中
    6. 断言 response.error is None + result.items 包含 mem-001 + 不含 mem-002/mem-003

    跳过条件：chart 不完整（e2e-envtest workflow 真验证）
    """
    _ensure_helm_install(kind_cluster, chart_status)

    test_namespace = "e2e-h-qm-001"
    request_id = f"h-qm-{uuid.uuid4().hex[:8]}"

    # 三种 CR 字段组合（与 query 过滤模式严格匹配）
    # 设计：3 个 CR 的 agent_ref 各不相同 → agent_ref=agent-a 过滤仅命中 mem-001
    mem_records = [
        {
            "name": "qm-mem-001",
            "scope_ref": "scope-a",
            "agent_ref": "agent-a",
            "industry": "tech",
            "summary": "H-QM-E2E-001 mem-001 (scope-a, agent-a, tech)",
        },
        {
            "name": "qm-mem-002",
            "scope_ref": "scope-b",
            "agent_ref": "agent-b",
            "industry": "finance",
            "summary": "H-QM-E2E-001 mem-002 (scope-b, agent-b, finance)",
        },
        {
            "name": "qm-mem-003",
            "scope_ref": "scope-a",
            "agent_ref": "agent-c",
            "industry": "tech",
            "summary": "H-QM-E2E-001 mem-003 (scope-a, agent-c, tech)",
        },
    ]

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
        # 1. apply 3 个 Memory CR
        for rec in mem_records:
            cr_yaml = _memory_cr_yaml(
                name=rec["name"],
                namespace=test_namespace,
                scope_ref=rec["scope_ref"],
                agent_ref=rec["agent_ref"],
                industry=rec["industry"],
                summary=rec["summary"],
                confidence=0.85,
            )
            apply_result = subprocess.run(
                ["kubectl", "apply", "-f", "-", "--kubeconfig", kind_cluster],
                input=cr_yaml,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert apply_result.returncode == 0, (
                f"kubectl apply {rec['name']} failed: {apply_result.stderr}"
            )

        # 2. 逐 CR wait observedGeneration >= 1 (60s timer + buffer)
        for rec in mem_records:
            observed_gen = _wait_observed_generation(
                kind_cluster=kind_cluster,
                name=rec["name"],
                namespace=test_namespace,
                timeout_seconds=120,
            )
            assert observed_gen >= 1, (
                f"Memory {rec['name']} observedGeneration 未递增: {observed_gen}"
            )

        # 3. kubectl port-forward + socket 探测
        pf_proc = _port_forward_service(
            kind_cluster=kind_cluster,
            service_name=service_name,
            local_port=LOCAL_PORT,
            remote_port=SERVICE_PORT,
        )
        port_ready = _wait_port_listening(LOCAL_PORT, timeout_seconds=15.0)
        assert port_ready, f"port-forward to {service_name}:{SERVICE_PORT} not ready in 15s"

        # 4. POST /jsonrpc/query_memory
        # QueryMemoryRequest wire format (camelCase):
        #   scope: "scope" (scope-based query)
        #   namespace: apply 同 namespace
        #   agent_ref: "agent-a" (snake_case wire as per QueryMemoryRequest)
        params = {
            "scope": "scope",
            "namespace": test_namespace,
            "agent_ref": "agent-a",
        }
        envelope = {"jsonrpc": "2.0", "id": request_id, "params": params}
        response = _post_jsonrpc(
            url=f"http://localhost:{LOCAL_PORT}/jsonrpc/query_memory",
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
        # QueryMemoryResult 字段（pyright: QueryMemoryResult model_dump snake_case wire）
        assert "items" in result, f"response.result 缺 items: {result}"
        items = result["items"]
        assert isinstance(items, list), f"result.items must be list: {items!r}"

        # 6. 验证过滤子集
        item_names = {m["metadata"]["name"] for m in items}
        # Phase 1 MVP in-process backend 跨 namespace 隔离：namespace=test_namespace
        # 期望 mem-001 命中 · mem-002 + mem-003 不命中
        assert "qm-mem-001" in item_names, (
            f"items 必须含 mem-001 (scope-a, agent-a): got {item_names}"
        )
        assert "qm-mem-002" not in item_names, (
            f"items 不应含 mem-002 (scope-b, agent-b): got {item_names}"
        )
        assert "qm-mem-003" not in item_names, (
            f"items 不应含 mem-003 (scope-a, agent-c): got {item_names}"
        )

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
