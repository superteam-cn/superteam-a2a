"""BM25Index unit tests · BM25-UT-001/002。

Phase 1 MVP 占位实装的最小集验证：
- remove() idempotent（存在/不存在均静默 return）
- upsert + remove 集成
- 启动期空状态正常

不在范围：BM25 搜索算法、TF-IDF 排序（待 Phase 2）。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 路径前置（namespace package 解析顺序）
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory import BM25Index  # noqa: E402


async def test_bm25_ut_001_remove_idempotent():
    """BM25-UT-001 · remove() 不存在 key 时静默 return（不抛错）。

    §4.4 finalize step 4 不变量：idempotent。
    """
    index = BM25Index()
    # 移除空 index 中的 key → 静默 return
    await index.remove("ns-a", "mem-x")
    # upsert 后再次 remove
    await index.upsert("ns-a", "mem-1", {"foo": 2, "bar": 1})
    await index.remove("ns-a", "mem-1")
    # 第二次 remove 同一 key → 静默 return
    await index.remove("ns-a", "mem-1")
    # 不同 ns/name 仍可静默 return
    await index.remove("ns-b", "mem-2")


async def test_bm25_ut_002_upsert_remove_integration():
    """BM25-UT-002 · upsert + remove 集成 + 覆盖语义。

    验证：upsert 可创建 + 覆盖；remove 后 dict 不留痕迹。
    """
    index = BM25Index()
    # upsert 初始项
    await index.upsert("ns-a", "mem-1", {"foo": 1})
    assert ("ns-a", "mem-1") in index._docs
    assert index._docs[("ns-a", "mem-1")] == {"foo": 1}
    # upsert 覆盖语义
    await index.upsert("ns-a", "mem-1", {"foo": 5, "bar": 3})
    assert index._docs[("ns-a", "mem-1")] == {"foo": 5, "bar": 3}
    # remove 后清除
    await index.remove("ns-a", "mem-1")
    assert ("ns-a", "mem-1") not in index._docs
    # 多 key 独立
    await index.upsert("ns-a", "mem-2", {"baz": 7})
    await index.upsert("ns-b", "mem-3", {"qux": 9})
    assert len(index._docs) == 2
    await index.remove("ns-a", "mem-2")
    assert ("ns-a", "mem-2") not in index._docs
    assert ("ns-b", "mem-3") in index._docs


def test_bm25_init_empty():
    """BM25Index 构造为空 dict · 启动期无任何 Memory 时正常运行。"""
    index = BM25Index()
    assert index._docs == {}
