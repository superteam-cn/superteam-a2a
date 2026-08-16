"""BM25 倒排索引业务逻辑 · PR-4c plan §2.2.

§16.1 + 宪法 §17 SOLID 6 原则：
- SRP：scorer.py 只负责 BM25 公式计算；index.py 只负责索引管理
- OCP：通过 k1 + b 参数扩展（不修改算法核心）
- LSP：BM25InvertedIndex 类支持任意 tokenization（不变性保持）
- DIP：依赖 math + 标准库（无外部依赖）
- ISP：scorer.py 暴露单一函数 bm25_score
- CRP：构造参数注入（k1 + b）

依赖：stdlib only（math + 内置 dict/list/tuple/set）
性能门禁：p95<100ms @ 10K items (L3-5 §9.7 / L3-6 §9.7)
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.bm25.index import (
    STOP_WORDS,
    BM25InvertedIndex,
)
from superteam_a2a.knowledge_memory.bm25.scorer import bm25_score

__all__ = [
    "STOP_WORDS",
    "BM25InvertedIndex",
    "bm25_score",
]
