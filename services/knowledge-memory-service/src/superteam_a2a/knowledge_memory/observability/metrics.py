"""10 Memory 业务指标定义（L3-6 §7.1 权威表 + plan §3.3 封闭枚举约束）。

- 6 Counter（reconcile_total / decay_applied_total / reinforce_total / gc_cleaned_total /
             in_process_call_total / rate_limited_total）
- 2 Histogram（reconcile_duration_seconds / admission_duration_seconds）
- 2 Gauge（promotion_eligible_total / bm25_index_size）
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# 1. MEMORY_RECONCILE_TOTAL · Counter · labels (phase, result)
MEMORY_RECONCILE_TOTAL = Counter(
    "superteam_memory_reconcile_total",
    "Total Memory reconcile attempts.",
    labelnames=("phase", "result"),
)

# 2. MEMORY_RECONCILE_DURATION_SECONDS · Histogram · labels (phase) · buckets
MEMORY_RECONCILE_DURATION_SECONDS = Histogram(
    "superteam_memory_reconcile_duration_seconds",
    "Memory reconcile batch duration.",
    labelnames=("phase",),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 50),
)

# 3. MEMORY_DECAY_APPLIED_TOTAL · Counter · labels (phase_from, phase_to)
MEMORY_DECAY_APPLIED_TOTAL = Counter(
    "superteam_memory_decay_applied_total",
    "Total decay transitions applied.",
    labelnames=("phase_from", "phase_to"),
)

# 4. MEMORY_REINFORCE_TOTAL · Counter · labels (result)
MEMORY_REINFORCE_TOTAL = Counter(
    "superteam_memory_reinforce_total",
    "Total reinforcement operations.",
    labelnames=("result",),
)

# 5. MEMORY_GC_CLEANED_TOTAL · Counter · labels (gc_state)
MEMORY_GC_CLEANED_TOTAL = Counter(
    "superteam_memory_gc_cleaned_total",
    "Total expired Memories deleted.",
    labelnames=("gc_state",),
)

# 6. MEMORY_PROMOTION_ELIGIBLE_TOTAL · Gauge · labels (visibility)
MEMORY_PROMOTION_ELIGIBLE_TOTAL = Gauge(
    "superteam_memory_promotion_eligible_total",
    "Current Memories eligible for promotion.",
    labelnames=("visibility",),
)

# 7. MEMORY_BM25_INDEX_SIZE · Gauge · labels (scope_level)
MEMORY_BM25_INDEX_SIZE = Gauge(
    "superteam_memory_bm25_index_size",
    "Indexed Memory count.",
    labelnames=("scope_level",),
)

# 8. MEMORY_ADMISSION_DURATION_SECONDS · Histogram · labels (validator) · buckets
MEMORY_ADMISSION_DURATION_SECONDS = Histogram(
    "superteam_memory_admission_duration_seconds",
    "Memory admission duration.",
    labelnames=("validator",),
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)

# 9. MEMORY_IN_PROCESS_CALL_TOTAL · Counter · labels (method, result)
MEMORY_IN_PROCESS_CALL_TOTAL = Counter(
    "superteam_memory_in_process_call_total",
    "L3-5 to L3-6 calls.",
    labelnames=("method", "result"),
)

# 10. MEMORY_RATE_LIMITED_TOTAL · Counter · labels (principal_type)
MEMORY_RATE_LIMITED_TOTAL = Counter(
    "superteam_memory_rate_limited_total",
    "Rate-limited Memory writes.",
    labelnames=("principal_type",),
)
