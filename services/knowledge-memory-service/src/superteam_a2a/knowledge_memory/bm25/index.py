"""BM25 倒排索引 · tokenization + inverted index + scoring.

PR-4c plan §2.2 · L3-5 §4.4 + L3-6 §6.4 + 性能门禁 p95<100ms @ 10K items。

参数（BM25 经典）：
    k1 = 1.5（词频饱和参数）
    b = 0.75（文档长度归一化参数）

数据结构：
    _index: dict[term, list[(doc_id, tf)]] · 倒排索引（term → postings list）
    _doc_lens: dict[doc_id, int] · 文档长度（tokens 数）
    _avg_doc_len: float · 平均文档长度
    _doc_count: int · 文档总数

不变量：
    - text tokenization：lowercase + split + stop words filter（STOP_WORDS frozenset）
    - upsert：原子 add/update · set(tokens) 去重
    - query：返回 top_k (doc_id, score) sorted by score desc · BM25 TF-IDF scoring
    - 性能门禁：p95<100ms @ 10K items (L3-5 §9.7 / L3-6 §9.7)

§17 SOLID 6 原则：
    - SRP：仅负责索引管理 + tokenization · 评分由 scorer.py 负责
    - OCP：k1 + b 构造参数扩展（不修改算法核心）
    - LSP：支持任意 tokenization（不变性保持 · 下游可替换 STOP_WORDS）
    - DIP：依赖 math + stdlib
    - CRP：构造参数注入（k1 + b）+ 内部数据结构封装
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.bm25.scorer import bm25_score

# 经典英文停用词（lowercase frozenset · O(1) 查找）
# 不依赖 NLTK · stdlib only · 性能 + 可移植性权衡
STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "should",
        "could",
        "may",
        "might",
        "must",
        "shall",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "can",
        "just",
        "don",
        "now",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "its",
        "our",
        "their",
        "this",
        "that",
        "these",
        "those",
    }
)


class BM25InvertedIndex:
    """BM25 倒排索引 · tokenization + inverted index + scoring (L3-5 §4.4)."""

    def __init__(self, *, k1: float = 1.5, b: float = 0.75) -> None:
        """构造 BM25 倒排索引。

        参数：
            k1: BM25 k1 参数（典型 1.5 · 词频饱和）
            b: BM25 b 参数（典型 0.75 · 文档长度归一化）
        """
        self.k1 = k1
        self.b = b
        self._index: dict[str, list[tuple[int, int]]] = {}
        self._doc_lens: dict[int, int] = {}
        self._avg_doc_len: float = 0.0
        self._doc_count: int = 0

    def tokenize(self, text: str) -> list[str]:
        """Text tokenization · lowercase + split + stop words filter.

        参数：
            text: 原始文本

        返回：
            list[str]: 过滤后的 token 列表（不含空字符串和停用词）
        """
        return [t for t in text.lower().split() if t and t not in STOP_WORDS]

    def upsert(self, doc_id: int, text: str) -> None:
        """Add/update document in index · atomic.

        算法：
            1. tokenize(text)
            2. delete(doc_id) · 清除旧 doc（如果存在）
            3. 写入新 doc · set(tokens) 去重
            4. 更新 _doc_count + _avg_doc_len

        参数：
            doc_id: 文档 ID（≥ 0）
            text: 文档文本
        """
        # Step 1: tokenize + 计算 tf
        tokens = self.tokenize(text)
        # Step 2: 清除旧 doc（如果存在）
        self.delete(doc_id)
        # Step 3: 写入新 doc · set 去重
        self._doc_lens[doc_id] = len(tokens)
        for term in set(tokens):
            tf = tokens.count(term)
            self._index.setdefault(term, []).append((doc_id, tf))
        # Step 4: 更新 _doc_count + _avg_doc_len
        self._doc_count = len(self._doc_lens)
        self._avg_doc_len = (
            sum(self._doc_lens.values()) / self._doc_count if self._doc_count > 0 else 0.0
        )

    def delete(self, doc_id: int) -> None:
        """Remove document from index.

        参数：
            doc_id: 文档 ID · 不存在时静默 return（idempotent）
        """
        if doc_id not in self._doc_lens:
            return
        del self._doc_lens[doc_id]
        for term, postings in self._index.items():
            self._index[term] = [(d, tf) for d, tf in postings if d != doc_id]
        self._doc_count = len(self._doc_lens)
        self._avg_doc_len = (
            sum(self._doc_lens.values()) / self._doc_count if self._doc_count > 0 else 0.0
        )

    def query(self, text: str, *, top_k: int = 10) -> list[tuple[int, float]]:
        """BM25 scoring · 返回 top_k (doc_id, score) sorted by score desc.

        算法：
            1. tokenize(query)
            2. 对每个 query term：计算 BM25 score 每个 doc
            3. 累加每个 doc 的总分
            4. 排序返回 top_k

        参数：
            text: 查询文本
            top_k: 返回前 k 个结果（默认 10）

        返回：
            list[tuple[int, float]]: (doc_id, score) 列表 · 按 score 降序

        不变量：
            - 空 query 或空索引 → 返回空列表
            - score ≥ 0（IDF 平滑 + TF 非负）
        """
        # Step 1: tokenize query
        query_tokens = self.tokenize(text)
        if not query_tokens or self._doc_count == 0:
            return []

        # Step 2-3: 计算每个 doc 的累计 BM25 score
        scores: dict[int, float] = {}
        for term in set(query_tokens):
            postings = self._index.get(term, [])
            if not postings:
                continue
            df = len(postings)  # document frequency
            for doc_id, tf in postings:
                doc_len = self._doc_lens.get(doc_id, 0)
                score = bm25_score(
                    tf=tf,
                    df=df,
                    doc_len=doc_len,
                    avg_doc_len=self._avg_doc_len,
                    k1=self.k1,
                    b=self.b,
                    N=self._doc_count,
                )
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        # Step 4: 排序返回 top_k
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(doc_id, score) for doc_id, score in sorted_scores[:top_k]]

    def __len__(self) -> int:
        """当前索引文档数。"""
        return self._doc_count
