"""Reconciler 公共类型 · L3-6 §4.3 + §4.4 + §5.7 错误码封闭集.

- ReconcileSummary: Pydantic frozen BaseModel;reconcile_all 返回值.
- MemoryReconcilerError: MemoryBackendError 子类;仅 reconciler 内部抛出.
"""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict
from superteam_a2a.knowledge_memory.backend.errors import (
    MemoryBackendError,
)


class ReconcileSummary(BaseModel):
    """§4.3 reconcile_all 返回值.

    所有字段都有默认;允许增量更新(注意 Pydantic v2 BaseModel 默认 mutable,
    但本类只作为 reconciler 内部累加器使用,不跨边界暴露 mutation).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    bound: int = 0
    errors: int = 0
    skipped_overlap: int = 0
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    result: Literal["ok", "overlap_skipped", "leader_lost", "error"] = "ok"


class MemoryReconcilerError(MemoryBackendError):
    """Reconciler 内部错误基类 · code 必须是 L2-4 §9.1 权威枚举成员.

    用于 §4.3 三类异常之外的 reconciler 自身失败(例如 lock acquire 失败等).
    实际 §4.3 pseudocode 三类异常(AdmissionTimeoutError / BackendUnavailable /
    其他)直接使用 backend.errors.MemoryBackendError;本类保留为 reconciler
    边界专用入口.
    """


__all__ = ["MemoryReconcilerError", "ReconcileSummary"]
