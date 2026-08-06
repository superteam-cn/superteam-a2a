"""L3-6 §6.3 BM25Index 内存 dict 实现 + 启动期懒加载。

Phase 1 MVP：
- 不实现 BM25 完整算法（TF-IDF/长度归一化）
- 仅维护 (namespace, name) → term frequency dict
- Protocol remove() idempotent：不存在时静默 return

完整 BM25 排序/搜索实装待 Phase 2。
"""

from __future__ import annotations


class BM25Index:
    """L3-6 §6.3 内存 BM25 index · startup lazy load。

    不变量：
    - remove() idempotent（namespace/name 不存在时静默 return）
    - 线程不安全（单进程 D 方案假设）
    - 启动期无任何 Memory 时 → 空 dict，正常运行
    """

    def __init__(self) -> None:
        self._docs: dict[tuple[str, str], dict[str, int]] = {}

    async def remove(self, namespace: str, name: str) -> None:
        """移除指定 (namespace, name) · 不存在时静默 return。"""
        self._docs.pop((namespace, name), None)

    # Phase 2 占位 API（仅 stub，不实装 search）
    async def upsert(self, namespace: str, name: str, terms: dict[str, int]) -> None:
        """Phase 2 占位 · 更新 (namespace, name) 的 term frequency。"""
        self._docs[(namespace, name)] = dict(terms)


__all__ = ["BM25Index"]
