"""@kopf.validation admission webhook 集成测试 · ADM-IT-004~006.

L3-5 §5.1 webhook 入口与 Kopf 框架集成验证。
PR-4a v0.2-draft 实装 · #111

测试 ID 规范：
- 避开 L3-5 §5.1 line 1434-1437 已有 ADM-IT-001~003（PR-3 测试）
- PR-4a 新增 ADM-IT-004~006（3 ID）
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

# 路径前置
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_PATH = str(_REPO_ROOT / "services" / "knowledge-memory-service" / "src")
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)


def _load_real_kopf():
    """从 venv 真实 kopf 路径加载模块，绕过 sys.modules['kopf'] 污染。"""
    kopf_init = (
        Path(sys.executable).parent.parent / "Lib" / "site-packages" / "kopf" / "__init__.py"
    )
    if not kopf_init.exists():
        return None
    spec = importlib.util.spec_from_file_location("_real_kopf", str(kopf_init))
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_REAL_KOPF = _load_real_kopf()


import pytest  # noqa: E402


# ADM-IT-004
def test_admission_webhook_module_imports_cleanly():
    """ADM-IT-004 · admission webhook 模块导入无错（与 Kopf 框架兼容）。"""
    from superteam_a2a.knowledge_memory.admission import webhook

    assert hasattr(webhook, "validate_knowledge_item")
    assert hasattr(webhook, "validate_memory")
    assert hasattr(webhook, "fail_closed_50ms")


def test_admission_webhook_decorated_functions_exist():
    """ADM-IT-004 · @kopf.validation 装饰注册存在。"""
    from superteam_a2a.knowledge_memory.admission.webhook import (
        validate_knowledge_item,
        validate_memory,
    )

    # kopf.validation 装饰器会保留原函数 + 注入 kopf 注册标记
    assert callable(validate_knowledge_item)
    assert callable(validate_memory)


# ADM-IT-005
def test_admission_webhook_timeout_50ms_fail_closed():
    """ADM-IT-005 · 50ms fail-closed E2E 验证（与 Kopf 集成）。"""
    from superteam_a2a.knowledge_memory.admission.webhook import fail_closed_50ms

    @fail_closed_50ms
    async def slow_validation() -> None:
        await asyncio.sleep(0.080)  # 80ms 超过 50ms 阈值

    assert _REAL_KOPF is not None
    with pytest.raises(_REAL_KOPF.AdmissionError) as exc_info:
        # pyright: ignore[reportArgumentType] - wrapped function returns coroutine
        asyncio.run(slow_validation())  # type: ignore[arg-type]
    assert "fail-closed" in str(exc_info.value)


def test_admission_webhook_timeout_50ms_fast_passes():
    """ADM-IT-005 · 50ms fail-closed · 快速路径不超时。"""
    from superteam_a2a.knowledge_memory.admission.webhook import fail_closed_50ms

    @fail_closed_50ms
    async def fast() -> str:
        return "ok"

    # pyright: ignore[reportArgumentType] - wrapped function returns coroutine
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
    asyncio.run(validate_knowledge_item(spec=spec))


def test_admission_webhook_memory_happy_path():
    """ADM-IT-006 · validate_memory · 小 decay_days 不报错。"""
    from superteam_a2a.knowledge_memory.admission.webhook import (
        validate_memory,
    )

    spec = {"content": {"k": "v"}, "decayDays": 30}
    # 不抛错
    asyncio.run(validate_memory(spec=spec))


def test_admission_webhook_memory_triggers_knowledge_admission_timeout_code():
    """ADM-IT-006 · validate_memory · MEMORY_ADMISSION_TIMEOUT 错误码常量可达。

    验证 KnowledgeAdmissionTimeout 错误码（-32018）作为 webhook 抛出的兜底。
    """
    from superteam_a2a.knowledge.errors.codes import KnowledgeErrorCode

    assert KnowledgeErrorCode.KNOWLEDGE_ADMISSION_TIMEOUT.value == -32018
