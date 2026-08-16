"""BM25 倒排索引单元测试 · BM25-UT-001/002/003。

PR-4c plan §2.5 测试策略 · L3-5 §4.4 + L3-6 §6.4 契约验证。

测试 ID：
- BM25-UT-001 · tokenize 小写 + 停用词过滤
- BM25-UT-002 · upsert/delete 维护倒排索引 + set 去重
- BM25-UT-003 · bm25_score 公式正确性（数值断言）

§17 SOLID：测试层只依赖 BM25InvertedIndex + bm25_score 公共 API。
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

from superteam_a2a.knowledge_memory.bm25 import (  # noqa: E402
    STOP_WORDS,
    BM25InvertedIndex,
    bm25_score,
)


def test_bm25_ut_001_tokenize_lowercase_and_filters_stop_words():
    """BM25-UT-001 · tokenize 小写 + split + STOP_WORDS filter。

    验证：
        - lowercase：'The' / 'Quick' / 'Brown' / 'Fox' → 'the' / 'quick' / 'brown' / 'fox'
        - split：按空格分割
        - STOP_WORDS filter：'the' 被过滤掉
    """
    index = BM25InvertedIndex()
    # 基本用例：包含停用词 the
    tokens = index.tokenize("The Quick Brown Fox")
    assert tokens == ["quick", "brown", "fox"], (
        f"BM25-UT-001 期望 ['quick', 'brown', 'fox'] 实际 {tokens}"
    )

    # 多个停用词 + 重复 term
    tokens_multi = index.tokenize("the cat and the dog and the bird")
    # 停用词全部过滤 → 只剩 cat / dog / bird
    assert tokens_multi == ["cat", "dog", "bird"], (
        f"BM25-UT-001 多停用词期望 ['cat', 'dog', 'bird'] 实际 {tokens_multi}"
    )

    # 验证 STOP_WORDS 是 frozenset（O(1) 查找 · immutable）
    assert isinstance(STOP_WORDS, frozenset), (
        f"BM25-UT-001 STOP_WORDS 期望 frozenset 实际 {type(STOP_WORDS)}"
    )

    # 验证 'the' 在 STOP_WORDS 中
    assert "the" in STOP_WORDS, "BM25-UT-001 'the' 应在 STOP_WORDS 中"

    # 空字符串过滤
    tokens_empty = index.tokenize("  hello   world  ")
    assert tokens_empty == ["hello", "world"], (
        f"BM25-UT-001 空白期望 ['hello', 'world'] 实际 {tokens_empty}"
    )


def test_bm25_ut_002_upsert_and_delete_maintains_inverted_index():
    """BM25-UT-002 · upsert + delete 维护倒排索引 + set 去重。

    验证：
        - mock 100 个小文档 → upsert 写入 _index + _doc_lens + _doc_count + _avg_doc_len
        - set(tokens) 去重（同一 term 只出现一次 per doc · 仅 1 个 postings 记录）
        - delete 清理 _index + _doc_lens + _avg_doc_len 更新
        - 多次 delete idempotent
    """
    index = BM25InvertedIndex()

    # Step 1: upsert 100 个小文档（each ~10 tokens）
    for doc_id in range(100):
        # 确定性文本：避免 flakiness
        text = f"document {doc_id} token {doc_id} common common common"
        index.upsert(doc_id, text)

    # Step 2: 验证 _doc_count = 100
    assert len(index) == 100, f"BM25-UT-002 _doc_count 期望 100 实际 {len(index)}"
    assert index._doc_count == 100

    # Step 3: 验证 _doc_lens 完整
    assert len(index._doc_lens) == 100

    # Step 4: 验证 _avg_doc_len > 0
    assert index._avg_doc_len > 0.0

    # Step 5: 验证 set(tokens) 去重（'common' 在 doc 0 中出现 3 次 → postings 只有 1 条）
    common_postings = index._index.get("common", [])
    # 100 个 doc 每个都包含 'common' → 100 条 postings
    assert len(common_postings) == 100, (
        f"BM25-UT-002 'common' postings 期望 100 实际 {len(common_postings)}"
    )
    # doc 0 的 'common' tf 应为 3（同一 doc 中 'common' 出现 3 次 · 但 postings 只 1 条）
    doc0_tf = next(tf for d, tf in common_postings if d == 0)
    assert doc0_tf == 3, f"BM25-UT-002 doc 0 'common' tf 期望 3 实际 {doc0_tf}"

    # Step 6: query 验证（query 'common' 返回 100 个 doc · 按 score 降序）
    results = index.query("common", top_k=10)
    assert len(results) == 10, f"BM25-UT-002 query top_k=10 期望 10 结果 实际 {len(results)}"
    # score 降序
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True), "BM25-UT-002 query 结果应按 score 降序"

    # Step 7: delete 部分 doc
    index.delete(0)
    index.delete(50)
    index.delete(99)
    assert len(index) == 97, f"BM25-UT-002 delete 3 doc 后 _doc_count 期望 97 实际 {len(index)}"
    assert 0 not in index._doc_lens
    assert 50 not in index._doc_lens
    assert 99 not in index._doc_lens

    # Step 8: 验证 'common' postings 不再含 deleted doc
    common_postings_after = index._index.get("common", [])
    for d, _tf in common_postings_after:
        assert d not in {0, 50, 99}, f"BM25-UT-002 deleted doc {d} 不应在 'common' postings 中"

    # Step 9: delete idempotent（不存在 doc 静默 return）
    index.delete(999)  # 不存在
    index.delete(999)  # 多次 idempotent
    assert len(index) == 97


def test_bm25_ut_003_score_formula_correctness():
    """BM25-UT-003 · bm25_score 公式正确性。

    验证：
        tf=2, df=1, doc_len=10, avg_doc_len=10.0, k1=1.5, b=0.75, N=1
        IDF = log((1 - 1 + 0.5) / (1 + 0.5) + 1) = log(1/1.5 + 1) ≈ 0.2877
        TF_normalized = (2 * 2.5) / (2 + 1.5 * (1 - 0.75 + 0.75 * 10/10))
                      = 5 / (2 + 1.5 * 1.0) = 5/3.5 ≈ 1.4286
        score ≈ 0.4110
    """
    score = bm25_score(
        tf=2,
        df=1,
        doc_len=10,
        avg_doc_len=10.0,
        k1=1.5,
        b=0.75,
        N=1,
    )
    # 期望 score ≈ 0.4110（允许 1e-6 浮点误差）
    expected = 0.41097438921682977
    assert abs(score - expected) < 1e-6, (
        f"BM25-UT-003 bm25_score 期望 {expected} 实际 {score} 差值 {abs(score - expected)}"
    )

    # 验证 score 非负
    assert score >= 0.0, f"BM25-UT-003 score 应 ≥ 0 实际 {score}"

    # 边界测试 1：avg_doc_len=0 → tf_normalized=0 → score=0
    score_zero_avg = bm25_score(tf=2, df=1, doc_len=10, avg_doc_len=0.0, k1=1.5, b=0.75, N=1)
    assert score_zero_avg == 0.0, f"BM25-UT-003 avg_doc_len=0 期望 0 实际 {score_zero_avg}"

    # 边界测试 2：tf 越高 → score 越高（饱和曲线）
    score_tf1 = bm25_score(tf=1, df=1, doc_len=10, avg_doc_len=10.0, k1=1.5, b=0.75, N=1)
    score_tf2 = bm25_score(tf=2, df=1, doc_len=10, avg_doc_len=10.0, k1=1.5, b=0.75, N=1)
    score_tf10 = bm25_score(tf=10, df=1, doc_len=10, avg_doc_len=10.0, k1=1.5, b=0.75, N=1)
    assert score_tf1 < score_tf2 < score_tf10, (
        f"BM25-UT-003 TF 饱和曲线 score_tf1={score_tf1} < score_tf2={score_tf2} < "
        f"score_tf10={score_tf10} 不成立"
    )
