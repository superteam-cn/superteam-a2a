"""K8sBackend unit tests - TEST-K8S-BE-001~012 (12 tests).

L4-Phase3 PR-2 K8sBackend 完整实装 testsuite.
Mock CustomObjectsApi + 验证 12 MEMORY_* 错误码 1:1 映射 K8s API 异常.

3 test groups (per plan v0.1-draft §4 阶段 D):
- Mock K8s API IT (4): TEST-K8S-BE-001~004
- Wire 一致性 (4): TEST-K8S-BE-005~008
- Round-trip (4): TEST-K8S-BE-009~012

作者: #94 主 Agent (PR-2 完整实装)
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# ============================================================================
# 路径前置 (与 conftest.py 一致 · 测试独立可执行)
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory import (  # noqa: E402
    BackendType,
    K8sBackend,
    Memory,
    MemoryBackendError,
    MemoryErrorCode,
    MemoryScope,
    ObjectMeta,
    QueryMemoryRequest,
)
from superteam_a2a.knowledge_memory.backend.memory import canonical_key  # noqa: E402
from superteam_a2a.operator.models.memory import (  # noqa: E402
    AgentReference,
    MemorySpec,
    ScopeReference,
)

# ============================================================================
# Mock helpers (modeled after test_k8s_lease_leader_elector.py)
# ============================================================================


def _resolve_real_api_exception() -> type[Exception]:
    """Lazy resolve kubernetes_asyncio.client.ApiException.

    若导入失败则 fallback Exception 基类, 测试代码应能容忍.
    """
    try:
        from kubernetes_asyncio.client import ApiException as _K8sApiException
    except ImportError:
        return Exception
    return _K8sApiException


_REAL_API_EXCEPTION_BASE: type[Exception] = _resolve_real_api_exception()


class _FakeApiException(_REAL_API_EXCEPTION_BASE):
    """模拟 kubernetes_asyncio.client.ApiException · 与 leader_elector 测试一致."""

    def __init__(self, status: int, reason: str = "", headers: dict | None = None) -> None:
        super().__init__(status=status, reason=reason)  # type: ignore[call-arg]
        self.status = status
        self.reason = reason
        self.headers = headers or {}


def _make_kube_client(
    *,
    create: object | Exception | list | None = None,
    replace: object | Exception | list | None = None,
    get: object | Exception | list | None = None,
    delete: object | Exception | list | None = None,
    list_response: object | Exception | list | None = None,
    patch_status: object | Exception | list | None = None,
) -> MagicMock:
    """构造 CustomObjectsApi MagicMock with 6 async methods.

    setup 规则 (与 K8sLeaseLeaderElector 测试 helper 一致):
    - Exception instance / class → side_effect = raise 每次
    - list / tuple → side_effect = queue (按序消费)
    - None → return_value = None
    - 其他 → return_value = value (单次固定返回值)

    注：使用 list_response 而非 list 避免与 builtin list shadow 问题.
    """
    client = MagicMock()

    def _setup(attr_name: str, value: object | Exception | list | None) -> None:
        if value is None:
            setattr(client, attr_name, AsyncMock(return_value=None))
            return
        if isinstance(value, BaseException) or (
            isinstance(value, type) and issubclass(value, BaseException)
        ):
            setattr(client, attr_name, AsyncMock(side_effect=value))
            return
        if isinstance(value, (list, tuple)):
            setattr(client, attr_name, AsyncMock(side_effect=list(value)))
            return
        setattr(client, attr_name, AsyncMock(return_value=value))

    _setup("create_namespaced_custom_object", create)
    _setup("replace_namespaced_custom_object", replace)
    _setup("get_namespaced_custom_object", get)
    _setup("delete_namespaced_custom_object", delete)
    _setup("list_namespaced_custom_object", list_response)
    _setup("patch_namespaced_custom_object_status", patch_status)
    return client


class _MockK8sBody(dict[str, Any]):
    """Mock K8s CustomObject response wrapper.

    包装一个纯 dict（兼容 Memory.model_validate）但额外支持：
    - resource_version (属性): mock seam 给 K8sBackend.patch_status 读

    Memory.model_validate 要求 dict[Unknown, Any] 无多余 top-level 字段；
    通过 dict 行为绕过 __setattr__ 污染。
    """

    def __init__(self, data: dict[str, Any], *, resource_version: str = "1") -> None:
        super().__init__(data)
        self._mock_resource_version: str = resource_version


def _extract_resource_version(raw: object) -> str:
    """从 mock 响应提取 resourceVersion (兼容 K8sBackend & mock seam)."""
    if isinstance(raw, _MockK8sBody):
        return raw._mock_resource_version
    if isinstance(raw, dict):
        meta = raw.get("metadata") or {}
        if isinstance(meta, dict):
            rv = meta.get("resourceVersion")
            if rv:
                return str(rv)
    return "1"


def _memory_to_mock_body(memory: Memory, *, resource_version: str = "1") -> _MockK8sBody:
    """构造 mock CustomObjectsApi 返回的 K8s CR body（_MockK8sBody 包装）.

    关键约束：
    - Memory ObjectMeta 是 extra='forbid' → 不能在 dict 顶层加 resourceVersion
    - Memory ObjectMeta.creationTimestamp 需 AwareDatetime (tz-aware)
    - Memory labels 用 K8s label_key regex 必须 prefix/name 形式
    - resourceVersion 用 _MockK8sBody 顶层属性存储 → 兼容测试断言
      K8sBackend 通过 metadata.resourceVersion / _mock_resource_version 读取.
    """
    body = memory.model_dump(by_alias=True, mode="json", exclude_none=False)
    if "metadata" not in body or body["metadata"] is None:
        body["metadata"] = {}
    meta = body["metadata"]
    if "labels" not in meta or meta["labels"] is None:
        meta["labels"] = {}
    spec = body.get("spec") or {}
    if isinstance(spec, dict):
        scope_ref = spec.get("scopeRef", {})
        if isinstance(scope_ref, dict) and scope_ref.get("name"):
            meta["labels"]["superteam-a2a.io/scope"] = str(scope_ref["name"]).replace(".", "-")
        agent_ref = spec.get("agentRef", {})
        if isinstance(agent_ref, dict) and agent_ref.get("name"):
            meta["labels"]["superteam-a2a.io/agent"] = str(agent_ref["name"]).replace(".", "-")
    if "creationTimestamp" not in meta:
        from datetime import UTC

        meta["creationTimestamp"] = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC).isoformat()
    meta.setdefault("generation", 1)
    return _MockK8sBody(body, resource_version=resource_version)


def _make_memory(
    *,
    name: str = "mem-test",
    namespace: str = "default",
    summary: str = "Test memory",
    confidence: float = 1.0,
    visibility: str = "scope-and-children",
) -> Memory:
    """构造测试用 Memory 实例."""
    from superteam_a2a.operator.models.memory import MemoryVisibility

    return Memory(
        metadata=ObjectMeta(name=name, namespace=namespace),
        spec=MemorySpec(
            scopeRef=ScopeReference(name="industry-ai"),
            agentRef=AgentReference(name="hello-agent-sa"),
            content={"k": "v"},
            summary=summary,
            confidence=confidence,
            decayDays=30,
            visibility=MemoryVisibility(visibility),
        ),
    )


# ============================================================================
# Mock K8s API IT (4 tests: TEST-K8S-BE-001~004)
# ============================================================================


# -------- TEST-K8S-BE-001: PUT 创建 (201 → success) + 不重复创建 --------


async def test_k8s_be_001_put_create_new_memory_calls_create_not_replace() -> None:
    """TEST-K8S-BE-001 · 首次 PUT (local_meta 无 key) → create_namespaced_custom_object
    返回 Mock 201 success body. replace 不应被调用.
    """
    mem = _make_memory(name="mem-create-001")
    create_response = _memory_to_mock_body(mem, resource_version="10")
    client = _make_kube_client(create=create_response)

    backend = K8sBackend(kube_client=client)
    result = await backend.put(mem)

    # 验证 create 被调用
    client.create_namespaced_custom_object.assert_awaited_once()
    # 验证 replace 不应被调用 (首次创建路径)
    client.replace_namespaced_custom_object.assert_not_awaited()
    # 验证 version 从 1 开始
    assert result.version == 1
    assert result.stored_at is not None


# -------- TEST-K8S-BE-002: PUT 更新 (200 → version 递增) --------


async def test_k8s_be_002_put_existing_uses_replace_with_resource_version() -> None:
    """TEST-K8S-BE-002 · 第二次 PUT 同 (namespace, name) → replace_namespaced_custom_object
    带 resourceVersion CAS · 版本递增到 2.
    """
    mem = _make_memory(name="mem-update-002")
    create_response = _memory_to_mock_body(mem, resource_version="10")
    replace_response = _memory_to_mock_body(mem, resource_version="11")
    client = _make_kube_client(create=create_response, replace=replace_response)

    backend = K8sBackend(kube_client=client)
    # 1st put: create
    r1 = await backend.put(mem)
    assert r1.version == 1
    # 2nd put: replace (local_meta 已有该 key)
    r2 = await backend.put(mem)
    assert r2.version == 2

    client.create_namespaced_custom_object.assert_awaited_once()
    client.replace_namespaced_custom_object.assert_awaited_once()
    # replace body 应携带 resourceVersion (来自 create response "10")
    replace_call = client.replace_namespaced_custom_object.await_args
    assert replace_call is not None
    replace_body = replace_call.kwargs["body"]
    assert replace_body["metadata"]["resourceVersion"] == "10"


# -------- TEST-K8S-BE-003: GET 命中 (200 → 返回 Memory) --------


async def test_k8s_be_003_get_existing_returns_memory() -> None:
    """TEST-K8S-BE-003 · GET 命中 → 反序列化为 Memory. summary + spec 内容一致."""
    mem = _make_memory(name="mem-get-003", summary="hello world")
    get_response = _memory_to_mock_body(mem, resource_version="42")
    client = _make_kube_client(get=get_response)

    backend = K8sBackend(kube_client=client)
    got = await backend.get(mem.metadata.namespace, mem.metadata.name)

    assert got is not None
    assert isinstance(got, Memory)
    assert got.metadata.name == "mem-get-003"
    assert got.spec.summary == "hello world"
    client.get_namespaced_custom_object.assert_awaited_once()


# -------- TEST-K8S-BE-004: GET 未命中 (404 → 返回 None) --------


async def test_k8s_be_004_get_not_found_returns_none_no_error() -> None:
    """TEST-K8S-BE-004 · GET 返回 404 → K8sBackend 返回 None (不抛 MEMORY_*).
    重要 wire contract: 404 不算 MEMORY_* 错误, 由 handler 决定空集合.
    """
    client = _make_kube_client(get=_FakeApiException(404, "not found"))

    backend = K8sBackend(kube_client=client)
    got = await backend.get("default", "nonexistent")

    assert got is None
    # 不应抛任何 MemoryBackendError
    client.get_namespaced_custom_object.assert_awaited_once()


# ============================================================================
# Wire 一致性 (4 tests: TEST-K8S-BE-005~008)
# ============================================================================


# -------- TEST-K8S-BE-005: 422 → MEMORY_INVALID_CONTENT --------


async def test_k8s_be_005_422_maps_to_memory_invalid_content() -> None:
    """TEST-K8S-BE-005 · K8s 422 Unprocessable Entity (validation 失败)
    → MemoryBackendError(MEMORY_INVALID_CONTENT, retryable=False).
    """
    mem = _make_memory(name="mem-422-005")
    client = _make_kube_client(
        create=_FakeApiException(422, "spec validation failed"),
    )
    backend = K8sBackend(kube_client=client)

    with pytest.raises(MemoryBackendError) as exc_info:
        await backend.put(mem)

    assert exc_info.value.code == MemoryErrorCode.MEMORY_INVALID_CONTENT
    assert exc_info.value.retryable is False
    assert "422" in str(exc_info.value)


# -------- TEST-K8S-BE-006: 403 → MEMORY_FORBIDDEN --------


async def test_k8s_be_006_403_maps_to_memory_forbidden() -> None:
    """TEST-K8S-BE-006 · K8s 403 Forbidden (RBAC 拒绝)
    → MemoryBackendError(MEMORY_FORBIDDEN, retryable=False).
    """
    mem = _make_memory(name="mem-403-006")
    client = _make_kube_client(
        create=_FakeApiException(403, "forbidden"),
    )
    backend = K8sBackend(kube_client=client)

    with pytest.raises(MemoryBackendError) as exc_info:
        await backend.put(mem)

    assert exc_info.value.code == MemoryErrorCode.MEMORY_FORBIDDEN
    assert exc_info.value.retryable is False


# -------- TEST-K8S-BE-007: 429 → MEMORY_RATE_LIMIT (retryable=True) --------


async def test_k8s_be_007_429_maps_to_memory_rate_limit_retryable() -> None:
    """TEST-K8S-BE-007 · K8s 429 Too Many Requests (rate limit)
    → MemoryBackendError(MEMORY_RATE_LIMIT, retryable=True).
    """
    mem = _make_memory(name="mem-429-007")
    client = _make_kube_client(
        create=_FakeApiException(429, "too many requests"),
    )
    backend = K8sBackend(kube_client=client)

    with pytest.raises(MemoryBackendError) as exc_info:
        await backend.put(mem)

    assert exc_info.value.code == MemoryErrorCode.MEMORY_RATE_LIMIT
    assert exc_info.value.retryable is True


# -------- TEST-K8S-BE-008: 5xx → MEMORY_INTERNAL_ERROR (retryable=True) --------


async def test_k8s_be_008_5xx_maps_to_memory_internal_error_retryable() -> None:
    """TEST-K8S-BE-008 · K8s 500 Internal Server Error
    → MemoryBackendError(MEMORY_INTERNAL_ERROR, retryable=True).
    """
    mem = _make_memory(name="mem-500-008")
    client = _make_kube_client(
        create=_FakeApiException(500, "internal server error"),
    )
    backend = K8sBackend(kube_client=client)

    with pytest.raises(MemoryBackendError) as exc_info:
        await backend.put(mem)

    assert exc_info.value.code == MemoryErrorCode.MEMORY_INTERNAL_ERROR
    assert exc_info.value.retryable is True


# ============================================================================
# Round-trip (4 tests: TEST-K8S-BE-009~012)
# ============================================================================


# -------- TEST-K8S-BE-009: put → get round-trip --------


async def test_k8s_be_009_put_then_get_roundtrip() -> None:
    """TEST-K8S-BE-009 · put → get 完整 round-trip 数据一致.
    验证 contract 不变量 5 (可替换语义): 与 InMemoryBackend 行为等价.
    """
    mem = _make_memory(name="mem-roundtrip-009")
    create_response = _memory_to_mock_body(mem, resource_version="1")
    get_response = _memory_to_mock_body(mem, resource_version="1")
    client = _make_kube_client(create=create_response, get=get_response)

    backend = K8sBackend(kube_client=client)
    put_result = await backend.put(mem)
    assert put_result.version == 1

    got = await backend.get(mem.metadata.namespace, mem.metadata.name)
    assert got is not None
    assert got.metadata.name == mem.metadata.name
    assert got.spec.summary == mem.spec.summary


# -------- TEST-K8S-BE-010: put → list 命中 --------


async def test_k8s_be_010_put_then_list_finds_memory() -> None:
    """TEST-K8S-BE-010 · put 后 list (industry scope + tag filter)
    → 返回包含该 Memory. 验证 list label_selector 路径与 client-side 过滤.
    """
    mem = _make_memory(name="mem-list-010")
    create_response = _memory_to_mock_body(mem, resource_version="1")
    list_response = {
        "apiVersion": "memory.superteam-a2a.io/v1alpha1",
        "kind": "MemoryList",
        "metadata": {"resourceVersion": "100"},
        "items": [_memory_to_mock_body(mem, resource_version="1")],
    }
    client = _make_kube_client(create=create_response, list_response=list_response)
    backend = K8sBackend(kube_client=client)
    await backend.put(mem)

    # 用 industry scope + tag 必须过滤 (避免 MEMORY_QUERY_TOO_BROAD)
    query = QueryMemoryRequest(
        scope=MemoryScope.INDUSTRY,
        tags=(),
    )
    # industry + no tag + no min_confidence → MEMORY_QUERY_TOO_BROAD
    with pytest.raises(MemoryBackendError) as exc_info:
        await backend.list(query)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_QUERY_TOO_BROAD

    # 添加 tag 后正常 list
    query_with_filter = QueryMemoryRequest(
        scope=MemoryScope.INDUSTRY,
        min_confidence=0.5,
    )
    list_result = await backend.list(query_with_filter)
    assert list_result.total >= 1
    assert any(m.metadata.name == "mem-list-010" for m in list_result.items)
    client.list_namespaced_custom_object.assert_awaited_once()


# -------- TEST-K8S-BE-011: put → patch_status CAS 成功 --------


async def test_k8s_be_011_patch_status_generation_matches_succeeds() -> None:
    """TEST-K8S-BE-011 · patch_status generation 匹配 → 成功 (无 MemoryBackendError).
    Mock 返回 current generation == expected_generation.
    """
    mem = _make_memory(name="mem-patch-011")
    create_response = _memory_to_mock_body(mem, resource_version="1")
    # get (patch 前查询) 返回 metadata.generation = 1 (matches expected)
    get_response = _memory_to_mock_body(mem, resource_version="1")
    get_response["metadata"]["generation"] = 1
    client = _make_kube_client(
        create=create_response,
        get=get_response,
        patch_status={"metadata": {}},  # patch 成功
    )
    backend = K8sBackend(kube_client=client)
    await backend.put(mem)

    # patch_status with expected_generation=1 (match)
    new_status = {"phase": "Bound"}
    await backend.patch_status(
        mem.metadata.namespace,
        mem.metadata.name,
        new_status,
        expected_generation=1,
    )
    client.patch_namespaced_custom_object_status.assert_awaited_once()


# -------- TEST-K8S-BE-012: put → patch_status generation 不匹配 → MEMORY_INTERNAL_ERROR --------


async def test_k8s_be_012_patch_status_generation_mismatch_raises() -> None:
    """TEST-K8S-BE-012 · patch_status generation 不匹配
    → MemoryBackendError(MEMORY_INTERNAL_ERROR, retryable=True).
    """
    mem = _make_memory(name="mem-cas-012")
    create_response = _memory_to_mock_body(mem, resource_version="1")
    # mock get 返回 generation=2 (但 caller expected_generation=1)
    get_response = _memory_to_mock_body(mem, resource_version="2")
    get_response["metadata"]["generation"] = 2
    client = _make_kube_client(
        create=create_response,
        get=get_response,
    )
    backend = K8sBackend(kube_client=client)
    await backend.put(mem)

    # patch_status with expected_generation=1 (mismatch with actual=2)
    with pytest.raises(MemoryBackendError) as exc_info:
        await backend.patch_status(
            mem.metadata.namespace,
            mem.metadata.name,
            {"phase": "Bound"},
            expected_generation=1,
        )
    assert exc_info.value.code == MemoryErrorCode.MEMORY_INTERNAL_ERROR
    assert exc_info.value.retryable is True
    # patch_status 不应被调用 (generation check 失败提前抛)
    client.patch_namespaced_custom_object_status.assert_not_awaited()


# ============================================================================
# 额外 smoke tests: Protocol + capacity + BackendType
# ============================================================================


def test_k8s_backend_implements_protocol() -> None:
    """K8sBackend 必须实现 MemoryBackend Protocol 6 抽象方法 (duck-typed).

    验证 §5.7 不变量 5: 可替换语义.
    """
    backend = K8sBackend()
    for method in ("put", "get", "delete", "list", "patch_status", "health", "metadata"):
        assert hasattr(backend, method), f"K8sBackend missing method {method}"


async def test_k8s_backend_metadata_returns_k8s_backend_type() -> None:
    """K8sBackend.metadata() → backend_type=K8S (BackendType.K8S)."""
    backend = K8sBackend(max_size=2048)
    md = await backend.metadata()
    assert md.backend_type == BackendType.K8S
    assert md.max_size == 2048
    assert md.version == "0.1.0"


async def test_k8s_backend_put_capacity_exceeded_raises_memory_forbidden() -> None:
    """K8sBackend.put capacity 满 → MemoryBackendError(MEMORY_FORBIDDEN)."""
    from unittest.mock import MagicMock  # noqa: F401

    create_response_1 = _memory_to_mock_body(_make_memory(name="only-one"), resource_version="1")
    # Create always succeeds so local_meta fills
    client = _make_kube_client(create=create_response_1)
    backend = K8sBackend(kube_client=client, max_size=1)
    mem1 = _make_memory(name="only-one")
    await backend.put(mem1)
    assert backend.size == 1

    # 现在 size=1, max=1, 新 key 应抛 MEMORY_FORBIDDEN (pure.put check)
    mem2 = _make_memory(name="second")
    with pytest.raises(MemoryBackendError) as exc_info:
        await backend.put(mem2)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_FORBIDDEN


# canonical_key 静默引用 (避免 lint 警告 - 已使用)
_ = canonical_key
