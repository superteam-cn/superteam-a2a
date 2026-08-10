"""Hello Agent · 内部 helpers（仅包内 import · 不导出到 __all__）。

L3-4 §5 文件级契约：
- _task_store: dict 单例 + _MAX_STORED_TASKS = 1024 FIFO 轮转（单进程）
- handle_send_message(payload) → Task dict 核心业务逻辑
- 异常类型 + 校验 helper（仅包内）

5 项不变量：
1. _task_store 单进程（replicaCount=1 强约束 · PR-2 Helm schema enum）
2. 无 LLM 依赖（v0.1 仅 echo · "pong" 字面量）
3. 无 framework 依赖（不 import langchain/autogen/crewai）
4. 单实例 ASGI（uvicorn 端口 8080 · 单进程）
5. 4 指标独立命名空间（与 Memory 25 指标不冲突）
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

# ============================================================================
# 单进程 _task_store（单例 dict + FIFO 轮转）
# ============================================================================

_MAX_STORED_TASKS = 1024

_task_store: dict[str, dict[str, Any]] = {}


def _store_task(task_id: str, task: dict[str, Any]) -> None:
    """存储 task 到单例 dict（FIFO 轮转超过 _MAX_STORED_TASKS）。

    单进程架构下无需 Redis（OPEN-HELLO-002 已登记 v0.5+ 演进）。
    """
    if len(_task_store) >= _MAX_STORED_TASKS:
        # FIFO：pop oldest key
        oldest_key = next(iter(_task_store))
        _task_store.pop(oldest_key)
    _task_store[task_id] = task


def get_stored_task(task_id: str) -> dict[str, Any] | None:
    """查询 task（仅测试 + E2E 用 · 不进 public API）。"""
    return _task_store.get(task_id)


def reset_task_store() -> None:
    """测试辅助：清空单例 dict。"""
    _task_store.clear()


def stored_task_count() -> int:
    """查询 _task_store 当前大小（仅测试用）。"""
    return len(_task_store)


# ============================================================================
# Wire format Pydantic models（请求 schema 校验）
# ============================================================================


class MessagePart(BaseModel):
    """A2A message part（v0.1 仅 text 类型）。"""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(default="text", description="part 类型 (v0.1 仅 text)")
    text: str = Field(..., description="part 文本内容")


class A2AMessage(BaseModel):
    """A2A message envelope。"""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(default="user", description="message role")
    parts: list[MessagePart] = Field(..., min_length=1, description="message parts")


class SendMessagePayload(BaseModel):
    """POST /a2a/sendMessage request body（顶层 envelope）。"""

    model_config = ConfigDict(extra="forbid")

    message: A2AMessage = Field(..., description="A2A message")


class Artifact(BaseModel):
    """A2A Task artifact（v0.1 仅 1 text part · "pong"）。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parts: list[MessagePart] = Field(..., min_length=1)


class TaskStatus(BaseModel):
    """A2A Task status（v0.1 仅 completed）。"""

    model_config = ConfigDict(extra="forbid")

    state: str = Field(default="completed")


class Task(BaseModel):
    """A2A Task envelope（GET /a2a/getTask 复用 · v0.1 必返 completed）。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = Field(default_factory=TaskStatus)
    artifacts: list[Artifact] = Field(default_factory=list)


# ============================================================================
# 业务核心 · handle_send_message（test fixture + agent.py 共用）
# ============================================================================


def handle_send_message(payload: dict[str, Any]) -> dict[str, Any]:
    """处理 sendMessage 请求 · 返回 Task dict（含 "pong" artifact）。

    5 步契约（L3-4 §6）：
    1. 校验 payload schema（SendMessagePayload Pydantic）
    2. 生成 task_id + context_id（uuid4）
    3. 构造 Artifact (parts: [{kind: text, text: "pong"}])
    4. Task(status: completed) → store_task → return model_dump(mode="json")
    5. 异常：ValidationError → 抛 InvalidParamsError

    Args:
        payload: HTTP request body dict（顶层 message 字段）

    Returns:
        Task.model_dump(mode="json") dict

    Raises:
        InvalidParamsError: payload schema 校验失败
    """
    try:
        SendMessagePayload.model_validate(payload)
    except ValidationError as exc:
        raise InvalidParamsError(
            f"Invalid sendMessage payload: {exc.error_count()} validation error(s)"
        ) from exc

    task = Task(
        status=TaskStatus(state="completed"),
        artifacts=[
            Artifact(parts=[MessagePart(kind="text", text="pong")]),
        ],
    )
    dumped = task.model_dump(mode="json")
    _store_task(task_id=dumped["id"], task=dumped)
    return dumped


# ============================================================================
# 异常类型（仅包内）
# ============================================================================


class InvalidParamsError(Exception):
    """sendMessage payload 校验失败（HTTP 400）。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def is_valid_message_payload(payload: Any) -> bool:
    """快速校验：payload 是否符合 SendMessagePayload schema（test fixture 用）。

    不抛异常 · 仅返回 bool。
    """
    if not isinstance(payload, dict):
        return False
    try:
        SendMessagePayload.model_validate(payload)
    except ValidationError:
        return False
    return True
