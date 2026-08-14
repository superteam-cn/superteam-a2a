"""tests/integration/knowledge_memory/ conftest.py · PR-4b 修复 kopf mock 跨目录污染。

#111 PR-4a 修复了 tests/unit/knowledge_memory/ 的 kopf mock 污染（test_main_memo.py
在 module-level 用 sys.modules["kopf"] = MagicMock() 防止装饰器注册失败）。但
tests/integration/knowledge_memory/ 没有对应的 conftest.py，导致污染跨目录传播：

  pytest collection order:
    tests/unit/knowledge_memory/handlers/test_main_memo.py  → sys.modules["kopf"] = MagicMock
    tests/integration/knowledge_memory/test_admission_webhook.py
      → importlib.import_module("kopf") 拿到 MagicMock
      → kopf.AdmissionError = MagicMock 而非真实异常类
      → pytest.raises(kopf.AdmissionError) → TypeError: Expected BaseException, got MagicMock

本 conftest.py 在每个 integration test 前恢复真实 kopf 到 sys.modules["kopf"]。
与 unit/knowledge_memory/conftest.py 完全镜像（同样的 fixture 实现）。

PR-4b 启动前置修复 · #113 · 修复 6 个 PR-4a 遗留失败 admission 测试。
"""

from __future__ import annotations

import importlib
import sys

import pytest

# 缓存"真实 kopf"模块引用（首次访问时记录）
_REAL_KOPF_MODULE = None


def _fetch_real_kopf() -> None:
    """恢复真实 kopf 模块到 sys.modules。

    策略：
    1. 移除 sys.modules['kopf'] 使 Python 重新 import
    2. import kopf 会触发真实 kopf 加载（importlib 缓存）
    3. 如果 kopf 已经原 import 过则 import kopf 直接拿到原缓存
    """
    global _REAL_KOPF_MODULE
    # 第一次删除 mock 重新 import，缓存真实版
    if _REAL_KOPF_MODULE is None:
        # 移除 mock 让 import 再次触发
        sys.modules.pop("kopf", None)
        # 真实的 kopf 已被前面的 import 缓存（main.py 间接触发），但被 mock 覆盖
        # 强制重新 importlib.import_module
        _REAL_KOPF_MODULE = importlib.import_module("kopf")
    sys.modules["kopf"] = _REAL_KOPF_MODULE


@pytest.fixture(autouse=True)
def _restore_real_kopf(request: pytest.FixtureRequest) -> None:
    """autouse fixture：在每个 integration test 函数前恢复真实 kopf 到 sys.modules['kopf']。

    镜像 tests/unit/knowledge_memory/conftest.py 的 _restore_real_kopf。
    """
    _fetch_real_kopf()
