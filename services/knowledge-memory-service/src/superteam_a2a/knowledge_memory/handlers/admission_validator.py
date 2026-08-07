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
from typing import Any

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


__all__ = ["AdmissionValidatorImpl"]
