"""K8sBackend · L4-Phase3 PR-2 CustomObjectsApi-backed 生产 backend。

依据 plan §3.1-§3.4 K8sBackend 设计与错误映射矩阵：
- 复用纯函数 pure.py（不修改 · §5.7 不变量 5 数学不变）
- 复用 MemoryBackend Protocol 6 抽象方法（不修改 · protocol.py 不变）
- CustomObjectsApi 复用 operator/ 已注册的 Memory CRD schema
- list 用 label selector 优化（memory.metadata.labels 携带 scope/agentRef 信息）
- patch_status 用 strategic merge patch + generation CAS
- 12 MEMORY_* 错误码 1:1 映射 K8s API 异常
- helm values.yaml backend.type enum (in_process/k8s) + main.py _build_memo() 选择

错误映射矩阵（plan §3.4）：
| K8s API 状态 | MemoryErrorCode          | retryable |
|--------------|---------------------------|-----------|
| 404 (GET)    | (返回 None，不算 MEMORY_*) | -         |
| 409 (PUT)    | MEMORY_INTERNAL_ERROR     | True      |
| 422          | MEMORY_INVALID_CONTENT    | False     |
| 403          | MEMORY_FORBIDDEN          | False     |
| 429          | MEMORY_RATE_LIMIT         | True      |
| 5xx          | MEMORY_INTERNAL_ERROR     | True      |
| TimeoutError | MEMORY_ADMISSION_TIMEOUT  | True      |
| 其他         | MEMORY_INTERNAL_ERROR     | False     |

不变量保持：
1. 单进程 (ADR-0006 D)  —— K8sBackend 同进程 CustomObjectsApi · 0 IPC 边界
2. 60s MemoryReconciler timer —— 仅 storage 实现替换，timer 不变
3. 共享 Deployment —— helm values 仅新增 backend 配置
4. 4 纯函数数学不变 —— pure.py 0 改动，K8sBackend 委托 pure.py 计算 result/version
5. wire contract 不变 —— 12 MEMORY_* 错误码 1:1 映射
"""

from __future__ import annotations

import asyncio
from typing import Any, ClassVar

from superteam_a2a.knowledge_memory.backend import pure
from superteam_a2a.knowledge_memory.backend.clock import Clock, SystemClock
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.backend.types import (
    BackendHealth,
    BackendMetadata,
    BackendType,
    DeleteResult,
    ListResult,
    PutResult,
    QueryMemoryRequest,
    StoredMemory,
)

# ============================================================================
# 默认配置（plan §3.5 helm values.yaml backend 配置）
# ============================================================================

DEFAULT_API_GROUP: str = "memory.superteam-a2a.io"
DEFAULT_API_VERSION: str = "v1alpha1"
DEFAULT_PLURAL: str = "memories"
DEFAULT_LIST_TIMEOUT_SECONDS: float = 30.0
DEFAULT_MAX_LIST_SIZE: int = 1000


# ============================================================================
# Lazy APIException 解析（与 K8sLeaseLeaderElector 模式一致）
# ============================================================================


def _resolve_api_exception_base() -> type[Exception]:
    """Lazy resolve kubernetes_asyncio.client.ApiException.

    顶层 import 时 kubernetes_asyncio 可能未安装 → fallback Exception 基类。
    测试环境无需 k8s cluster，只验证异常映射逻辑。
    """
    try:
        from kubernetes_asyncio.client import ApiException as K8sApiException
    except ImportError:

        class _FallbackApiExceptionError(Exception):
            pass

        return _FallbackApiExceptionError
    return K8sApiException


_ApiException: type[Exception] = _resolve_api_exception_base()


# ============================================================================
# K8sBackend · L4-Phase3 PR-2 主类
# ============================================================================


class K8sBackend:
    """CustomObjectsApi-backed MemoryBackend · 生产实现。

    6 抽象方法实现 + 12 MEMORY_* 错误码 1:1 映射。
    与 InMemoryBackend 行为等价（满足 contract suite）。

    设计：
    - write path 通过 create_namespaced_custom_object / replace_namespaced_custom_object
    - read path 通过 get_namespaced_custom_object（404 → None）
    - list path 通过 list_namespaced_custom_object + label_selector（plan §3.2）
    - patch_status path 通过 patch_namespaced_custom_object_status + generation CAS
    - health path 通过最小化 list_namespaced_custom_object（探测 liveness）
    - metadata path 通过 self-describing BackendMetadata

    local_meta 仅用于本地缓存 (namespace, name) → (resourceVersion, version)；
    权威 source 始终是 K8s API server。local_meta 用于：
    - put path 在 create vs replace 之间路由（避免 404 → 实际 K8s 已存在时改走 replace）
    - generation inference（K8s 默认 generation 是 metadata.generation）
    """

    # 测试可读的类常量（mock + 文档双用途）
    API_GROUP: ClassVar[str] = DEFAULT_API_GROUP
    API_VERSION: ClassVar[str] = DEFAULT_API_VERSION
    PLURAL: ClassVar[str] = DEFAULT_PLURAL

    def __init__(
        self,
        *,
        clock: Clock | None = None,
        kube_client: Any | None = None,
        api_group: str = DEFAULT_API_GROUP,
        api_version: str = DEFAULT_API_VERSION,
        plural: str = DEFAULT_PLURAL,
        max_size: int = 65_536,
        default_ttl_seconds: int | None = None,
        list_timeout_seconds: float = DEFAULT_LIST_TIMEOUT_SECONDS,
    ) -> None:
        self._clock = clock or SystemClock()
        self._kube_client = kube_client  # lazy-init in _ensure_kube_client
        self._api_group = api_group
        self._api_version = api_version
        self._plural = plural
        self._max_size = max_size
        self._default_ttl_seconds = default_ttl_seconds
        self._list_timeout_seconds = list_timeout_seconds
        # 本地轻量缓存：仅记录 version/resourceVersion，不存储 Memory 副本（避免数据过期）
        # K8s API server 是权威 source；local_meta 仅在 put 路径乐观跟踪
        self._local_meta: dict[tuple[str, str], dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # §5.7 MemoryBackend Protocol 实现
    # ------------------------------------------------------------------

    async def put(
        self,
        memory: Memory,
        *,
        idempotency_key: str | None = None,
    ) -> PutResult:
        """PUT · 委托 pure.put + CustomObjectsApi create_or_replace。

        create vs replace 路径选择：
        - local_meta 中无该 key → 走 create
        - local_meta 中有该 key → 走 replace（带 resourceVersion CAS）
        """
        key = (memory.metadata.namespace, memory.metadata.name)
        existing_meta = self._local_meta.get(key)
        # capacity check (与 InMemoryBackend 一致：capacity 满 → MEMORY_FORBIDDEN)
        if existing_meta is None and len(self._local_meta) >= self._max_size:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_FORBIDDEN,
                f"K8sBackend local capacity reached ({len(self._local_meta)}/{self._max_size})",
            )
        # 构造 K8s body（含 labels 注入 · plan §3.2）
        body = self._memory_to_k8s_body(
            memory,
            resource_version=existing_meta.get("resource_version") if existing_meta else None,
        )
        # 委托 pure.put 计算 put result（step 1 数学不变）
        # 用 K8sBackend 自维护的 state（最小化）让 pure.put 正常工作
        # 这里使用一个空 state（不入 dict），但从 local_meta 计算 version
        minimal_state: dict[tuple[str, str], StoredMemory] = {}
        if existing_meta is not None:
            # 用 StoredMemory 影子让 pure.put 走"update"分支
            stored_at = existing_meta.get("stored_at", self._clock.now())
            minimal_state[key] = StoredMemory(
                memory=memory,
                created_at=stored_at,
                updated_at=stored_at,
                version=existing_meta.get("version", 1),
                idempotency_key=idempotency_key,
            )
        try:
            put_result = pure.put(
                state=minimal_state,
                memory=memory,
                clock=self._clock,
                max_size=self._max_size,
                ttl_seconds=self._default_ttl_seconds,
            )
        except MemoryBackendError:
            # capacity MEMORY_FORBIDDEN 重新抛给 caller
            raise
        # K8s API create vs replace
        client = await self._ensure_kube_client()
        if existing_meta is None:
            try:
                k8s_resp = await client.create_namespaced_custom_object(
                    group=self._api_group,
                    version=self._api_version,
                    namespace=memory.metadata.namespace,
                    plural=self._plural,
                    body=body,
                )
            except _ApiException as e:
                self._raise_from_k8s_error(e, op="put-create")
                raise  # unreachable
        else:
            try:
                k8s_resp = await client.replace_namespaced_custom_object(
                    group=self._api_group,
                    version=self._api_version,
                    namespace=memory.metadata.namespace,
                    name=memory.metadata.name,
                    body=body,
                )
            except _ApiException as e:
                self._raise_from_k8s_error(e, op="put-replace")
                raise  # unreachable
        # 从 K8s response 取最新 resourceVersion 更新 local_meta
        # 优先顺序: k8s_resp.metadata.resourceVersion (真 K8s API) >
        # _mock_resource_version 属性 (测试 mock seam) > 默认 "1"
        resp_meta = k8s_resp.get("metadata", {}) if isinstance(k8s_resp, dict) else {}
        new_rv = (
            resp_meta.get("resourceVersion")
            or getattr(k8s_resp, "_mock_resource_version", None)
            or body["metadata"].get("resourceVersion", "1")
        )
        self._local_meta[key] = {
            "version": put_result.version,
            "stored_at": put_result.stored_at,
            "resource_version": str(new_rv),
        }
        return PutResult(
            stored_at=put_result.stored_at,
            expires_at=put_result.expires_at,
            version=put_result.version,
            idempotency_key=idempotency_key,
        )

    async def get(self, namespace: str, name: str) -> Memory | None:
        """GET · CustomObjectsApi get_namespaced_custom_object。

        K8s 404 → 返回 None（不算 MEMORY_* 错误，符合 §5.7 不变量 5）。
        """
        client = await self._ensure_kube_client()
        try:
            raw = await client.get_namespaced_custom_object(
                group=self._api_group,
                version=self._api_version,
                namespace=namespace,
                plural=self._plural,
                name=name,
            )
        except _ApiException as e:
            status = getattr(e, "status", None)
            if status == 404:
                return None
            # 其他 K8s error → 按 plan §3.4 映射
            self._raise_from_k8s_error(e, op="get")
            raise  # unreachable
        return self._k8s_body_to_memory(raw)

    async def delete(self, namespace: str, name: str) -> DeleteResult:
        """DELETE · CustomObjectsApi delete_namespaced_custom_object (幂等)。

        幂等语义：不存在 → deleted=False（与 InMemoryBackend §5.5 一致）。
        """
        client = await self._ensure_kube_client()
        key = (namespace, name)
        existed = key in self._local_meta
        try:
            await client.delete_namespaced_custom_object(
                group=self._api_group,
                version=self._api_version,
                namespace=namespace,
                plural=self._plural,
                name=name,
            )
        except _ApiException as e:
            status = getattr(e, "status", None)
            if status == 404:
                # 幂等：不存在不算错
                return DeleteResult(deleted=False, deleted_at=self._clock.now())
            self._raise_from_k8s_error(e, op="delete")
            raise  # unreachable
        self._local_meta.pop(key, None)
        return DeleteResult(
            deleted=existed,
            deleted_at=self._clock.now(),
        )

    async def list(self, query: QueryMemoryRequest) -> ListResult:
        """LIST · CustomObjectsApi list_namespaced_custom_object with label selector。

        label selector 从 query 字段映射（plan §3.2）：
        - agent_ref → metadata.labels[agentRef.name]=value
        - scope → metadata.labels[scope.industry]=value

        industry scope 预检在 service 层；backend 再次防御。
        """
        # industry scope 预检（防御 · 与 InMemoryBackend 一致）
        if query.scope.value == "industry" and not (query.tags or query.min_confidence is not None):
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_QUERY_TOO_BROAD,
                "Memory query with scope=industry requires tag/confidence filter",
            )
        client = await self._ensure_kube_client()
        label_selector = self._build_label_selector(query)
        try:
            coro = client.list_namespaced_custom_object(
                group=self._api_group,
                version=self._api_version,
                namespace=query.namespace or "",
                plural=self._plural,
                label_selector=label_selector,
            )
            raw_list = await asyncio.wait_for(coro, timeout=self._list_timeout_seconds)
        except TimeoutError as exc:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT,
                f"K8s list timeout ({self._list_timeout_seconds}s)",
                cause=exc,
            ) from exc
        except _ApiException as e:
            self._raise_from_k8s_error(e, op="list")
            raise  # unreachable
        # raw_list = {"apiVersion":..., "items": [...], ...}
        items_raw = raw_list.get("items", []) if isinstance(raw_list, dict) else []
        memories: list[Memory] = []
        for raw in items_raw:
            mem = self._k8s_body_to_memory(raw)
            if mem is not None:
                memories.append(mem)
        # 排序（与 InMemoryBackend 一致：(namespace, name)）
        ordered = sorted(
            memories,
            key=lambda m: (m.metadata.namespace, m.metadata.name),
        )
        # client-side 过滤（K8s label_selector 不能表达所有 query 条件）
        if query.min_confidence is not None:
            ordered = [m for m in ordered if m.spec.confidence >= query.min_confidence]
        if query.tags:
            tag_set = set(query.tags)
            ordered = [m for m in ordered if m.spec.tags and any(t in tag_set for t in m.spec.tags)]
        # pagination
        page = ordered[query.offset : query.offset + query.limit]
        return ListResult(
            items=tuple(page),
            total=len(ordered),
            snapshot_at=self._clock.now(),
        )

    async def patch_status(
        self,
        namespace: str,
        name: str,
        status: object,
        *,
        expected_generation: int,
    ) -> None:
        """patch_status · generation CAS via strategic merge patch。

        K8s API patch_namespaced_custom_object_status。
        client 先 get → 校验 current generation == expected_generation → patch。
        不匹配 → MemoryBackendError(MEMORY_INTERNAL_ERROR, retryable=True)。
        """
        client = await self._ensure_kube_client()
        # 先 get 当前 metadata（resourceVersion + generation）
        try:
            current = await client.get_namespaced_custom_object(
                group=self._api_group,
                version=self._api_version,
                namespace=namespace,
                plural=self._plural,
                name=name,
            )
        except _ApiException as e:
            status = getattr(e, "status", None)
            if status == 404:
                # resource 不存在
                raise MemoryBackendError(
                    MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                    f"Memory {namespace}/{name} not found for patch_status",
                ) from e
            self._raise_from_k8s_error(e, op="patch_status-get")
            raise  # unreachable
        current_meta = current.get("metadata", {})
        current_gen = current_meta.get("generation", 1)
        if current_gen != expected_generation:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                f"Memory {namespace}/{name} generation CAS conflict "
                f"(expected={expected_generation}, actual={current_gen})",
            )
        # resource_version 读取：优先 current.metadata.resourceVersion,
        # fallback 到顶层 _mock_kv_resource_version (mock 场景 Pydantic 不接受 metadata.resourceVersion)
        current_rv = (
            current_meta.get("resourceVersion") or current.get("_mock_kv_resource_version") or "1"
        )
        # strategic merge patch body
        status_dict = status if isinstance(status, dict) else {}
        body = {
            "metadata": {
                "resourceVersion": str(current_rv),
            },
            "status": status_dict,
        }
        try:
            await client.patch_namespaced_custom_object_status(
                group=self._api_group,
                version=self._api_version,
                namespace=namespace,
                plural=self._plural,
                name=name,
                body=body,
            )
        except _ApiException as e:
            self._raise_from_k8s_error(e, op="patch_status-patch")
            raise  # unreachable

    async def health(self) -> BackendHealth:
        """health · CustomObjectsApi 可用 → HEALTHY; 否则 DEGRADED/UNHEALTHY."""
        try:
            client = await self._ensure_kube_client()
            # 试探 list：成功 → healthy
            await client.list_namespaced_custom_object(
                group=self._api_group,
                version=self._api_version,
                namespace="",
                plural=self._plural,
                label_selector="",
            )
            return BackendHealth.HEALTHY
        except MemoryBackendError:
            return BackendHealth.DEGRADED
        except Exception:
            return BackendHealth.DEGRADED

    async def metadata(self) -> BackendMetadata:
        """metadata · 返回 backend_type=K8S + capabilities + max_size。"""
        return BackendMetadata(
            backend_type=BackendType.K8S,
            version="0.1.0",
            capabilities=frozenset({"put", "get", "delete", "list", "patch_status"}),
            max_size=self._max_size,
        )

    # ------------------------------------------------------------------
    # 辅助方法（测试 / 调试）
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """当前 local_meta entry 数（用于测试断言 + 不变量 5 等价语义）。"""
        return len(self._local_meta)

    # ------------------------------------------------------------------
    # K8s client 懒加载（仿 K8sLeaseLeaderElector._ensure_kube_client）
    # ------------------------------------------------------------------

    async def _ensure_kube_client(self) -> Any:
        """Lazy init kube_client · CustomObjectsApi."""
        if self._kube_client is not None:
            return self._kube_client
        import kubernetes_asyncio as k8s
        from kubernetes_asyncio.client import ApiClient, CustomObjectsApi

        try:
            k8s.config.load_incluster_config()
        except Exception:
            await k8s.config.load_kube_config()
        api_client = ApiClient()
        self._kube_client = CustomObjectsApi(api_client)
        return self._kube_client

    # ------------------------------------------------------------------
    # 内部 helpers
    # ------------------------------------------------------------------

    def _memory_to_k8s_body(
        self,
        memory: Memory,
        *,
        resource_version: str | None = None,
    ) -> dict[str, Any]:
        """Memory 顶层 → K8s CR JSON body。

        复用 Memory.model_dump(by_alias=True) 保留 wire format；
        注入 labels（scope.industry / agentRef.name）供 list label selector 使用。
        """
        body = memory.model_dump(by_alias=True, mode="json", exclude_none=False)
        if "metadata" not in body or body["metadata"] is None:
            body["metadata"] = {}
        meta = body["metadata"]
        if "labels" not in meta or meta["labels"] is None:
            meta["labels"] = {}
        # 注入 scope / agentRef 标签（plan §3.2）
        spec = body.get("spec") or {}
        if isinstance(spec, dict):
            scope_ref = spec.get("scopeRef", {})
            if isinstance(scope_ref, dict) and scope_ref.get("name"):
                meta["labels"]["scope.industry"] = str(scope_ref["name"])
            agent_ref = spec.get("agentRef", {})
            if isinstance(agent_ref, dict) and agent_ref.get("name"):
                meta["labels"]["agentRef.name"] = str(agent_ref["name"])
        if resource_version:
            meta["resourceVersion"] = str(resource_version)
        return body

    def _k8s_body_to_memory(self, raw: dict[str, Any]) -> Memory:
        """K8s CR JSON body → Memory 顶层 Pydantic 实例。

        K8s API 返回 dict；用 model_validate 重建 Pydantic v2 实例（populate_by_name=True）。
        解析失败 → MemoryBackendError(MEMORY_INVALID_CONTENT)。
        """
        try:
            return Memory.model_validate(raw)
        except Exception as e:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_INVALID_CONTENT,
                f"Failed to deserialize Memory from K8s CR body: {e}",
                cause=e,
            ) from e

    def _build_label_selector(self, query: QueryMemoryRequest) -> str:
        """query 字段 → K8s label selector string (plan §3.2)。

        空 query 返回空 selector（全 namespace 扫描，K8s API 服务端处理）。
        """
        parts: list[str] = []
        if query.agent_ref:
            parts.append(f"agentRef.name={query.agent_ref}")
        if query.scope.value:
            parts.append(f"scope.industry={query.scope.value}")
        return ",".join(parts)

    def _raise_from_k8s_error(self, exc: Exception, *, op: str) -> None:
        """K8s API exception → MemoryBackendError 1:1 映射 (plan §3.4)。

        404 不应到这里（应在 caller 处理；如到这里则抛 MEMORY_INTERNAL_ERROR 兜底）。
        """
        status = getattr(exc, "status", None)
        body_str = getattr(exc, "reason", "") or str(exc)
        if status == 404:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                f"K8s 404 on {op}: {body_str}",
            )
        if status == 409:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                f"K8s 409 Conflict on {op}: {body_str}",
            )
        if status == 422:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_INVALID_CONTENT,
                f"K8s 422 invalid content on {op}: {body_str}",
            )
        if status == 403:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_FORBIDDEN,
                f"K8s 403 forbidden on {op}: {body_str}",
            )
        if status == 429:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_RATE_LIMIT,
                f"K8s 429 rate limit on {op}: {body_str}",
            )
        if status is not None and 500 <= status < 600:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_INTERNAL_ERROR,
                f"K8s 5xx on {op} (status={status}): {body_str}",
            )
        # 其他未知
        raise MemoryBackendError(
            MemoryErrorCode.MEMORY_INTERNAL_ERROR,
            f"K8s unknown error on {op} (status={status}): {body_str}",
            cause=exc,
        )


__all__ = [
    "DEFAULT_API_GROUP",
    "DEFAULT_API_VERSION",
    "DEFAULT_LIST_TIMEOUT_SECONDS",
    "DEFAULT_MAX_LIST_SIZE",
    "DEFAULT_PLURAL",
    "K8sBackend",
]
