"""Hello Agent · _internals.py 测试 · HELLO-INT-001~002（2 UT）。

L3-4 §5 文件级契约：
- _task_store 单例 dict + _MAX_STORED_TASKS = 1024 FIFO 轮转
- handle_send_message 业务核心 5 步契约
- InvalidParamsError / is_valid_message_payload 异常与校验
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ============================================================================
# 路径前置
# ============================================================================

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HA_SRC = _REPO_ROOT / "services" / "hello-agent" / "src"
_HA_PATH = str(_HA_SRC)
if _HA_PATH not in sys.path:
    sys.path.insert(0, _HA_PATH)

from superteam_a2a.hello_agent._internals import (  # noqa: E402
    _MAX_STORED_TASKS,
    InvalidParamsError,
    get_stored_task,
    handle_send_message,
    is_valid_message_payload,
    reset_task_store,
    stored_task_count,
)


@pytest.fixture(autouse=True)
def _clear_store():
    """autouse fixture: 每个测试前清 _task_store（隔离单例状态）。"""
    reset_task_store()
    yield
    reset_task_store()


# ============================================================================
# HELLO-INT-001 · handle_send_message 业务核心 + _task_store FIFO
# ============================================================================


def test_handle_send_message_returns_pong_task_and_stores():
    """HELLO-INT-001: handle_send_message 返回 Task(artifacts: "pong") + _task_store 存储。

    5 步契约验证：
    1. payload schema 校验通过
    2. task_id + context_id（uuid4 格式）
    3. artifacts[0].parts[0].text == "pong"
    4. status.state == "completed"
    5. _task_store 含此 task_id
    """
    payload = {"message": {"role": "user", "parts": [{"kind": "text", "text": "ping"}]}}
    task = handle_send_message(payload=payload)

    # 3 步契约
    assert "id" in task
    assert "context_id" in task
    assert task["status"]["state"] == "completed"
    assert task["artifacts"][0]["parts"][0]["text"] == "pong"

    # 5 步：_task_store 存储
    assert stored_task_count() == 1
    stored = get_stored_task(task["id"])
    assert stored is not None
    assert stored["status"]["state"] == "completed"


def test_task_store_fifo_eviction_at_max():
    """HELLO-INT-001 补充：_task_store 超过 _MAX_STORED_TASKS → FIFO 轮转。

    单进程架构下无需 Redis（OPEN-HELLO-002 已登记 v0.5+ 演进）。
    """
    assert _MAX_STORED_TASKS == 1024  # L3-4 §5 锁定

    payload = {"message": {"role": "user", "parts": [{"kind": "text", "text": "x"}]}}
    first_task = handle_send_message(payload=payload)

    # 填满到 _MAX_STORED_TASKS
    for _ in range(_MAX_STORED_TASKS - 1):
        handle_send_message(payload=payload)
    assert stored_task_count() == _MAX_STORED_TASKS

    # 再添加 1 个 → FIFO 弹出第一个
    new_task = handle_send_message(payload=payload)
    assert stored_task_count() == _MAX_STORED_TASKS
    assert get_stored_task(first_task["id"]) is None  # 已被弹出
    assert get_stored_task(new_task["id"]) is not None


# ============================================================================
# HELLO-INT-002 · InvalidParamsError + is_valid_message_payload 校验
# ============================================================================


def test_handle_send_message_invalid_payload_raises_invalid_params():
    """HELLO-INT-002: payload schema 校验失败 → InvalidParamsError 抛出。

    验证：min_length=1 违反 + missing message field 都正确抛 InvalidParamsError。
    """
    # 空 parts 违反 min_length=1
    with pytest.raises(InvalidParamsError) as exc_info:
        handle_send_message(payload={"message": {"role": "user", "parts": []}})
    assert "validation error" in str(exc_info.value.message).lower()

    # 缺 message 字段
    with pytest.raises(InvalidParamsError):
        handle_send_message(payload={"foo": "bar"})


def test_is_valid_message_payload_quick_check():
    """HELLO-INT-002 补充：is_valid_message_payload 快速校验返回 bool · 不抛异常。

    验证：合法 payload → True · 非法 payload → False。
    """
    valid = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": "ping"}],
        },
    }
    assert is_valid_message_payload(valid) is True

    # 非法：非 dict
    assert is_valid_message_payload("string") is False
    assert is_valid_message_payload(None) is False
    assert is_valid_message_payload(123) is False

    # 非法：空 parts
    assert is_valid_message_payload({"message": {"role": "user", "parts": []}}) is False

    # 非法：缺 message
    assert is_valid_message_payload({"foo": "bar"}) is False
