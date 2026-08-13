"""tests/unit/knowledge_memory/ conftest.py · PR-4a 修复 kopf mock 污染。

test_main_memo.py 在 module-level 用 sys.modules["kopf"] = MagicMock() 防止
main.py 顶层 @kopf.on.* 装饰器在 collection 时触发 kopf 注册要求（names 不全
→ TypeError）。这个 mock 污染会让同进程后续加载的 test_admission_5step.py 和
test_admission_webhook.py 的 `import kopf` 拿到 MagicMock 而不是真实 kopf。

本 conftest.py 强制在每个 test 函数前重置 sys.modules["kopf"] 到真实 kopf 模块
（除 test_main_memo.py 自身的 test 函数），确保隔离。

PR-4a v0.2-draft 实装 · #111
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
        # 移除 mock 让 import 再次触发（无须保留 popped）
        sys.modules.pop("kopf", None)
        # 真实的 kopf 已被前面的 import 缓存（main.py 间接触发），但被 mock 覆盖
        # 强制重新 importlib.import_module
        _REAL_KOPF_MODULE = importlib.import_module("kopf")
    sys.modules["kopf"] = _REAL_KOPF_MODULE


@pytest.fixture(autouse=True)
def _restore_real_kopf(request: pytest.FixtureRequest) -> None:
    """autouse fixture：在每个 test 函数前恢复真实 kopf 到 sys.modules['kopf']。

    test_main_memo.py 自身测试需要 mock kopf（防止装饰器注册失败），所以本
    fixture 在 test_main_memo.py 内的 test 函数前主动重新 mock。其他测试文件
    的 test 函数前恢复真实 kopf。
    """
    test_module = request.node.fspath.basename
    if test_module == "test_main_memo.py":
        # test_main_memo.py 自身：保持 mock（test_main_memo.py module-level 已经在 setup 时 mock）
        return
    # 其他测试：恢复真实 kopf
    _fetch_real_kopf()
