"""superteam-a2a Knowledge-Memory Service (C-6 · D 方案单进程合并).

ADR-0006 v1.0 Accepted · 2026-07-30 #71：
- 取消 L3-5 + L3-6 双进程架构
- 合并为单 Python 进程 `services/knowledge-memory-service`
- 单 container Deployment（8080 A2A server + admission validator + MemoryReconciler 60s timer）
- 25 指标同进程聚合（prometheus-client）

依据 L3-5 Spec v0.2.0 + v0.2.1 + L3-6 Spec v0.2.0 + v0.2.1。
L4 实施待 #76-#78 落地（CRD schema / A2A handlers / admission / MemoryReconciler）。
"""

from __future__ import annotations

__version__ = "0.1.0"
