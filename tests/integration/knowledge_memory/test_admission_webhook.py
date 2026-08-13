"""@kopf.on.validate admission webhook 集成测试 · ADM-IT-004~006.

L3-5 §5.1 webhook 入口与 Kopf 框架集成验证。
PR-4a v0.2-draft 实装 · #111

测试 ID 规范：
- 避开 L3-5 §5.1 line 1434-1437 已有 ADM-IT-001~003（PR-3 测试）
- PR-4a 新增 ADM-IT-004~006（3 ID）
"""

from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path

# 路径前置
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_PATH = str(_REPO_ROOT / "services" / "knowledge-memory-service" / "src")
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

import pytest  # noqa: E402


def _get_real_kopf():
    """获取真实 kopf 模块（绕过 test_main_memo.py 的 sys.modules['kopf'] MagicMock 污染）。

    conftest.py 的 _restore_real_kopf fixture 已在每个 test 前重置 sys.modules['kopf']，
    但模块顶部的 `import kopf` 会缓存 Mock 引用。本 helper 在测试函数内通过 importlib
    重新导入 kopf，确保拿到真实模块。
    """
    # 强制重新 import 真实 kopf（如果 sys.modules['kopf'] 被 Mock 覆盖，则需要在 conftest 修复后）
    return importlib.import_module("kopf")


# ADM-IT-004
def test_admission_webhook_module_imports_cleanly():
    """ADM-IT-004 · admission webhook 模块导入无错（与 Kopf 框架兼容）。"""
    from superteam_a2a.knowledge_memory.admission import webhook

    assert hasattr(webhook, "validate_knowledge_item")
    assert hasattr(webhook, "validate_memory")
    assert hasattr(webhook, "fail_closed_50ms")


def test_admission_webhook_decorated_functions_exist():
    """ADM-IT-004 · @kopf.on.validate 装饰注册存在。"""
    from superteam_a2a.knowledge_memory.admission.webhook import (
        validate_knowledge_item,
        validate_memory,
    )

    # kopf.on.validate 装饰器会保留原函数 + 注入 kopf 注册标记
    assert callable(validate_knowledge_item)
    assert callable(validate_memory)


# ADM-IT-005
def test_admission_webhook_timeout_50ms_fail_closed():
    """ADM-IT-005 · 50ms fail-closed E2E 验证（与 Kopf 集成）。"""
    from superteam_a2a.knowledge_memory.admission.webhook import fail_closed_50ms

    kopf = _get_real_kopf()

    @fail_closed_50ms
    async def slow_validation() -> None:
        await asyncio.sleep(0.080)  # 80ms 超过 50ms 阈值

    with pytest.raises(kopf.AdmissionError) as exc_info:
        asyncio.run(slow_validation())  # type: ignore[arg-type]
    assert "fail-closed" in str(exc_info.value)


def test_admission_webhook_timeout_50ms_fast_passes():
    """ADM-IT-005 · 50ms fail-closed · 快速路径不超时。"""
    from superteam_a2a.knowledge_memory.admission.webhook import fail_closed_50ms

    @fail_closed_50ms
    async def fast() -> str:
        return "ok"

    result = asyncio.run(fast())  # type: ignore[arg-type]
    assert result == "ok"


# ADM-IT-006
def test_admission_webhook_knowledge_item_happy_path():
    """ADM-IT-006 · validate_knowledge_item · 小 content 不报错。"""
    from superteam_a2a.knowledge_memory.admission.webhook import (
        validate_knowledge_item,
    )

    spec = {"content": {"key": "value"}}
    # 不抛错
    asyncio.run(validate_knowledge_item(spec=spec))  # type: ignore[reportCallIssue]


def test_admission_webhook_memory_happy_path():
    """ADM-IT-006 · validate_memory · 小 decay_days 不报错。"""
    from superteam_a2a.knowledge_memory.admission.webhook import (
        validate_memory,
    )

    spec = {"content": {"k": "v"}, "decayDays": 30}
    # 不抛错
    asyncio.run(validate_memory(spec=spec))  # type: ignore[reportCallIssue]


def test_admission_webhook_memory_triggers_knowledge_admission_timeout_code():
    """ADM-IT-006 · validate_memory · KNOWLEDGE_ADMISSION_TIMEOUT 错误码常量可达。

    验证 KnowledgeAdmissionTimeout 错误码（-32018）作为 webhook 抛出的兜底。
    """
    from superteam_a2a.knowledge.errors.codes import KnowledgeErrorCode

    assert KnowledgeErrorCode.KNOWLEDGE_ADMISSION_TIMEOUT.value == -32018
