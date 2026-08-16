"""BM25 性能门禁集成测试 · BM25-IT-001。

PR-4c plan §2.5 + §5 风险 #1 缓解：
    - 本地 p95<100ms @ 10K items
    - CI 环境阈值放宽到 p95<150ms（env=SUPERTEAM_BM25_CI_RELAX=1）
    - 用确定性文本避免 flakiness
    - 测量方式：time.perf_counter() · 100 次 query · 排序取 p95

§17 SOLID：性能门禁仅依赖 BM25InvertedIndex 公共 API。
§11.5 event-loop lag < 100ms：10K items BM25 query p95 必须 < 100ms。
"""

from __future__ import annotations

import os
import statistics
import sys
import time
from pathlib import Path

import pytest

# 路径前置（namespace package 解析顺序）
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)

from superteam_a2a.knowledge_memory.bm25 import BM25InvertedIndex  # noqa: E402

# 性能门禁阈值
_LOCAL_THRESHOLD_MS = 100.0  # 本地 p95 < 100ms
_CI_THRESHOLD_MS = 150.0  # CI p95 < 150ms（plan §5 风险 #1 缓解）
_NUM_DOCS = 10_000  # 10K 文档
_TOKENS_PER_DOC = 100  # 每个 doc 100 tokens
_QUERY_ITERATIONS = 100  # 100 次 query 取 p95


@pytest.mark.integration
def test_bm25_query_p95_under_100ms_at_10k_items():
    """BM25-IT-001 · 10K items BM25 query p95 < 100ms（本地）/ < 150ms（CI）。

    算法：
        1. 构造 10K 文档（each ~100 tokens · 确定性文本避免 flakiness）
        2. upsert 到 BM25InvertedIndex
        3. 运行 100 次 query · 每次 query 包含 5-10 个 token
        4. 收集 latency · 计算 p95（95th percentile）
        5. 断言 p95 < threshold（local=100ms / CI=150ms）

    不变量：
        - 确定性文本（避免 flakiness）
        - 阈值：本地 100ms / CI 150ms（plan §5 风险 #1 缓解）
        - p95 计算：sorted(latencies)[int(0.95 * N)]
    """
    # CI 环境检测（plan §5 风险 #1 缓解）
    is_ci = os.environ.get("SUPERTEAM_BM25_CI_RELAX") == "1" or os.environ.get("CI") == "true"
    threshold_ms = _CI_THRESHOLD_MS if is_ci else _LOCAL_THRESHOLD_MS

    index = BM25InvertedIndex()

    # Step 1: 构造 10K 文档（确定性文本 · f"document {i} token {j}" 模式）
    # 文本生成 · 注入 ~100 个 tokens（含停用词 + content words）
    for doc_id in range(_NUM_DOCS):
        # 每个 doc 包含 100 tokens（20 停用词 + 80 content words）
        # 用确定性字符串避免 flakiness
        parts: list[str] = []
        for j in range(_TOKENS_PER_DOC):
            if j % 5 == 0:
                # 每 5 个 token 一个停用词（模拟真实文本）
                parts.append("the")
            else:
                # content words · 格式：f"d{doc_id}_t{j}"
                parts.append(f"d{doc_id}_t{j}")
        text = " ".join(parts)
        index.upsert(doc_id, text)

    # 验证 _doc_count = 10K
    assert len(index) == _NUM_DOCS, f"BM25-IT-001 _doc_count 期望 {_NUM_DOCS} 实际 {len(index)}"

    # Step 2-3: 运行 100 次 query · 测量 latency（毫秒）
    latencies_ms: list[float] = []
    for q_iter in range(_QUERY_ITERATIONS):
        # 确定性 query：包含 5-10 个 token（含停用词 + content words）
        # query 中至少 1 个 token 在 10K 文档中存在（确保非空结果）
        query_tokens: list[str] = []
        for k in range(8):
            # mix 停用词 + content words · content words 选择常见 ID
            if k % 2 == 0:
                query_tokens.append("the")
            else:
                # 选 doc_id % 1000（确保多数 doc 命中）
                query_tokens.append(f"d{q_iter % 1000}_t{k}")
        query_text = " ".join(query_tokens)

        # 测量 query latency
        start = time.perf_counter()
        results = index.query(query_text, top_k=10)
        end = time.perf_counter()

        latency_ms = (end - start) * 1000.0
        latencies_ms.append(latency_ms)

        # 验证 query 返回非空结果（确保 query 命中文档）
        assert len(results) > 0, f"BM25-IT-001 query iter {q_iter} 应返回非空结果"

    # Step 4: 计算 p95（95th percentile）
    # p95 = sorted(latencies)[int(0.95 * N)]（向上取整）
    sorted_latencies = sorted(latencies_ms)
    p95_index = int(0.95 * len(sorted_latencies))
    # 防止越界
    if p95_index >= len(sorted_latencies):
        p95_index = len(sorted_latencies) - 1
    p95_ms = sorted_latencies[p95_index]

    # 附加统计（调试用 · 不影响断言）
    median_ms = statistics.median(latencies_ms)
    max_ms = max(latencies_ms)
    min_ms = min(latencies_ms)

    # Step 5: 断言 p95 < threshold
    env_label = "CI" if is_ci else "local"
    assert p95_ms < threshold_ms, (
        f"BM25-IT-001 p95={p95_ms:.2f}ms 不满足 {env_label} 阈值 "
        f"{threshold_ms}ms (10K docs · median={median_ms:.2f}ms · "
        f"min={min_ms:.2f}ms · max={max_ms:.2f}ms · "
        f"N={_QUERY_ITERATIONS})"
    )
