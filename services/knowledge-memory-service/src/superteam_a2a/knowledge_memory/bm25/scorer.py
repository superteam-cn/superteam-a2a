"""BM25 TF-IDF scoring formula · L3-5 §4.4 + L3-6 §6.4.

§17 SOLID：
- SRP：纯函数 · 仅负责 BM25 公式计算 · 无副作用
- DIP：依赖 math + 算术 · 0 外部依赖
- ISP：仅暴露单一函数 bm25_score

性能门禁：p95<100ms @ 10K items (L3-5 §9.7 / L3-6 §9.7) · 在 BM25InvertedIndex.query 累计。
"""

from __future__ import annotations

import math

__all__ = ["bm25_score"]


def bm25_score(
    *,
    tf: int,
    df: int,
    doc_len: int,
    avg_doc_len: float,
    k1: float,
    b: float,
    N: int,  # noqa: N803 · BM25 文献标准参数命名（uppercase N）
) -> float:
    """BM25 TF-IDF scoring formula.

    公式：
        IDF = log((N - df + 0.5) / (df + 0.5) + 1)
        TF_normalized = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
        score = IDF * TF_normalized

    参数：
        tf: term frequency in document (≥ 1)
        df: document frequency (≥ 1, ≤ N)
        doc_len: document length in tokens (≥ 1)
        avg_doc_len: average document length (≥ 0)
        k1: BM25 k1 parameter (typical: 1.5)
        b: BM25 b parameter (typical: 0.75)
        N: total document count (≥ 1)

    返回：
        float: BM25 score · ≥ 0

    不变量：
        - IDF 平滑（+1）避免 log(0)
        - avg_doc_len == 0 时 TF_normalized 视为 0（避免除零）
        - 返回值 ≥ 0（IDF ≥ 0 · TF_normalized ≥ 0）
    """
    # Step 1: IDF 平滑（避免 log(0)）
    idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
    # Step 2: TF 归一化（文档长度归一化）
    if avg_doc_len == 0:
        tf_normalized = 0.0
    else:
        tf_normalized = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
    return idf * tf_normalized
