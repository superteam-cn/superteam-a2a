"""superteam-a2a Operator (C-1).

Kopf handlers + async reconciler service for 4 CRDs (Agent / AgentSet / Workflow / Memory).
依据 L3-1 Spec v0.2.0 + L1 §2-§4。
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # 公开 API（CRD models 在 models 子包导出，本文件仅导出 operator 包级常量）
]
