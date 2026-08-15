"""L3-6 §6.3 BM25 索引子包 · Phase 1 最小集（startup lazy load）。

Phase 1 MVP 占位：
- BM25Index 仅维护 (namespace, name) → term frequency dict
- 不实现完整 BM25 算法（TF-IDF/长度归一化）
- Protocol remove() idempotent：不存在时静默 return

完整 BM25 算法（TF-IDF/长度归一化/排序）待 Phase 2 实装。
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.index.bm25_index import BM25Index

__all__ = ["BM25Index"]
