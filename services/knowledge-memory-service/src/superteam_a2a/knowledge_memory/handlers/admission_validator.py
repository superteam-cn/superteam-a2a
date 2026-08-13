"""L3-6 §6.4 step 3 admission_validator · 与 Protocol 零漂移。

实现 AdmissionValidatorProtocol 的最小集（Phase 1 MVP）：
- 仅做 schema 校验（content keys 数量 + decay_days 范围）
- 完整 L3-5 §5.2 5 步 + §5.3 4 步算法待 Phase 2 实装（需 Phase 2 引入 K8s client）

关键不变量：
- validate() 异常原样透传给 caller；不允许内部 catch 重映射
- timeout 内未完成 → 抛 MemoryBackendError(MEMORY_ADMISSION_TIMEOUT)
- content keys > 20 → MemoryContractError(MEMORY_INVALID_CONTENT)
- decay_days > 3650 → MemoryContractError(MEMORY_DECAY_DAYS_EXCEEDED)
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any

from superteam_a2a.knowledge.errors.codes import (
    KnowledgeContractError,
    KnowledgeErrorCode,
)
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
    MemoryContractError,
    MemoryErrorCode,
)


class AdmissionValidatorImpl:
    """L3-6 §6.4 step 3 mutex lookup · Phase 1 最小集实现。

    关键不变量：
    - validate() 异常原样透传给 caller；不允许内部 catch 重映射
    - timeout 内未完成 → 抛 MemoryBackendError(MEMORY_ADMISSION_TIMEOUT)
    """

    def __init__(self, *, default_timeout_seconds: float = 0.050) -> None:
        self._default_timeout = default_timeout_seconds

    async def validate(self, memory: Any, *, timeout: float = 0.050) -> None:
        """执行 admission 互斥校验（§5.2 5 步 + §5.3 4 步）。

        异常透传规则（§6.4 step 5）：
        - caller 的 K8s API 异常 / MemoryBackendError / MemoryContractError → 直接 raise，不重映射
        - admission 内部 timeout → raise MemoryBackendError(MEMORY_ADMISSION_TIMEOUT)
        """
        try:
            await asyncio.wait_for(
                self._validate_inner(memory),
                timeout=timeout,
            )
        except TimeoutError as exc:
            raise MemoryBackendError(
                MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT,
                f"admission.validate exceeded {timeout * 1000:.1f}ms",
                cause=exc,
            ) from exc
        # §6.4 step 5：MemoryBackendError / MemoryContractError 原样透传
        # MemoryContractError is-a MemoryBackendError，二者一并 raise 不重映射

    async def _validate_inner(self, memory: Any) -> None:
        """§5.2 5 步 + §5.3 4 步算法 stub（Phase 1 最小集）。

        检查项：
        1. content keys ≤ 20（> 20 → MEMORY_INVALID_CONTENT）
        2. decay_days ≤ 3650（> 3650 → MEMORY_DECAY_DAYS_EXCEEDED）

        完整算法待 Phase 2 实装（需 Phase 2 引入 K8s client）。
        Phase 1 最小集仅做 schema 校验。
        """
        # Phase 1 最小集：仅 schema 校验
        spec = getattr(memory, "spec", None)
        if spec is None:
            return  # Memory model 不是必须有 spec（顶层 Memory + ObjectMeta）

        # content 数量校验 → MEMORY_INVALID_CONTENT
        content = getattr(spec, "content", None)
        if content is not None and isinstance(content, dict) and len(content) > 20:
            raise MemoryContractError(
                MemoryErrorCode.MEMORY_INVALID_CONTENT,
                f"content keys > 20 (got {len(content)})",
            )

        # decay_days 范围校验 → MEMORY_DECAY_DAYS_EXCEEDED
        decay_days = getattr(spec, "decay_days", 30)
        if decay_days > 3650:
            raise MemoryContractError(
                MemoryErrorCode.MEMORY_DECAY_DAYS_EXCEEDED,
                f"decay_days > 3650 (got {decay_days})",
            )


# ============================================================================
# PR-4a v0.2-draft 增量 · L3-5 §5.2 5 步算法 + §5.3 4 步 scope_ref 检测
# ============================================================================


class KnowledgeMemoryMutexValidator:
    """L3-5 §5.2 5 步算法 + §5.3 4 步 scope_ref 父子循环检测。

    关键不变量（§5.2 + §5.3）：
    - 5 步：content_hash 计算 → K8s 查询同 hash Memory → 不存在 → 允许 / 存在同 agent → supersede 允许 / 存在不同 agent → 拒绝
    - 4 步：parent_ref BFS → max_depth=8 → 命中自身 → KNOWLEDGE_OWNER_KIND_FORBIDDEN / 命中 > 8 → 拒绝
    - 拒绝时抛出 KnowledgeContractError(KNOWLEDGE_ITEM_NOT_FOUND, ...) 或 KNOWLEDGE_OWNER_KIND_FORBIDDEN
    - 与 AdmissionValidatorImpl 互不影响（关注点分离）
    """

    # 5 步算法 —— 5 步名称 + 目的必须严格对应 L3-5 §5.2 line 1445-1491
    CONTENT_HASH_LENGTH = 16  # sha256 前 16 hex chars（64 bit）

    def __init__(self, *, max_scope_depth: int = 8) -> None:
        self._max_scope_depth = max_scope_depth

    async def validate_ki_memory_mutex(
        self,
        ki: Any,
        *,
        memories: list[dict[str, Any]] | None = None,
    ) -> None:
        """L3-5 §5.2 5 步算法。

        参数 memories: 模拟 K8s 列表查询（list_namespaced_custom_object 返回 dict）；
        生产环境由 kopf.admission 注入 K8s client 调用 list_namespaced_custom_object。

        5 步：
        1. 计算 content_hash（sha256 前 16 hex chars · 与 wire 名一致）
        2. K8s 查询同 content_hash Memory（已模型化为 memories 参数）
        3. 不存在 → 允许（短路）
        4. 存在 + 同 agent_ref → supersede 允许
        5. 存在 + 不同 agent → 拒绝（KNOWLEDGE_ITEM_NOT_FOUND -32012）
        """
        # 1. 计算 content_hash
        content = getattr(ki.spec, "content", "") or ""
        if not isinstance(content, str):
            content = str(content)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[
            : self.CONTENT_HASH_LENGTH
        ]

        # 2. K8s 查询（已模型化）
        if memories is None:
            memories = []
        matching = [
            m
            for m in memories
            if m.get("metadata", {}).get("labels", {}).get("superteam-a2a.io/contentHash")
            == content_hash
        ]

        # 3. 不存在 → 允许
        if not matching:
            return

        # 4. 存在 + 同 agent → supersede 允许
        agent_label = (
            ki.metadata.labels.get("superteam-a2a.io/agent") if hasattr(ki, "metadata") else None
        )
        for mem in matching:
            mem_agent = mem.get("spec", {}).get("subject") or mem.get("metadata", {}).get(
                "labels", {}
            ).get("superteam-a2a.io/agent")
            if mem_agent and agent_label and mem_agent == agent_label:
                return  # 同 agent supersede 允许

        # 5. 存在 + 不同 agent → 拒绝
        raise KnowledgeContractError(
            KnowledgeErrorCode.KNOWLEDGE_ITEM_NOT_FOUND,
            f"Knowledge content already exists with different agent (contentHash={content_hash})",
        )

    async def detect_scope_ref_cycle(
        self,
        scope: Any,
        *,
        scope_lookup: dict[str, Any] | None = None,
    ) -> None:
        """L3-5 §5.3 4 步 scope_ref 父子循环检测。

        参数 scope_lookup: dict[name, scope] 模拟 K8s 查询；生产环境由 K8s client 注入。

        4 步：
        1. 从 scope.parent_ref 开始 BFS
        2. 命中 scope 自身 → KNOWLEDGE_OWNER_KIND_FORBIDDEN（环）
        3. BFS 深度 > 8 → 拒绝
        4. 命中不存在的 parent → 拒绝（KNOWLEDGE_SCOPE_NOT_FOUND）
        """
        if scope_lookup is None:
            scope_lookup = {}

        visited: set[str] = set()
        current_name = getattr(scope.metadata, "name", None) if hasattr(scope, "metadata") else None
        if current_name is None:
            return

        current: Any = scope
        depth = 0
        while True:
            # 4. 命中不存在的 parent → 拒绝
            if current is None:
                raise KnowledgeContractError(
                    KnowledgeErrorCode.KNOWLEDGE_SCOPE_NOT_FOUND,
                    "scope parent not found",
                )

            current_name = (
                getattr(current.metadata, "name", None) if hasattr(current, "metadata") else None
            )

            # 2. 环检测
            if current_name is not None and current_name in visited:
                raise KnowledgeContractError(
                    KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN,
                    f"scope_ref cycle detected at depth {depth}",
                )
            if current_name is not None:
                visited.add(current_name)

            # 3. 深度限制
            if depth >= self._max_scope_depth:
                raise KnowledgeContractError(
                    KnowledgeErrorCode.KNOWLEDGE_OWNER_KIND_FORBIDDEN,
                    f"scope_ref depth > {self._max_scope_depth}",
                )

            # 1. BFS 下一步
            parent_ref = (
                getattr(current.spec, "parent_ref", None) if hasattr(current, "spec") else None
            )
            if parent_ref is None:
                return  # 到达根

            parent_name = getattr(parent_ref, "name", None)
            if parent_name is None:
                return

            current = scope_lookup.get(parent_name)
            depth += 1


__all__ = [
    "AdmissionValidatorImpl",
    "KnowledgeMemoryMutexValidator",
]
