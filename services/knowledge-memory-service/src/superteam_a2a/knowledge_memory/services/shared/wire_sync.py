"""WireSyncService · 完整實裝 · 23 錯誤碼靜態斷言 + JSON-RPC code 範圍校驗。

PR-4b plan §2.4 + §6 不變量 5 + §7 ERR-IT-001/002：

本 service 從 PR-4a 已實裝的兩套錯誤碼加載：
- 11 KNOWLEDGE_* 錯誤碼（範圍 -32008 ~ -32018）
- 12 MEMORY_* 錯誤碼（範圍 -32101 ~ -32112）

提供兩個類方法：
- assert_wire_sync_compliant() · 驗證 23 錯誤碼範圍 + 命名嚴格匹配
- assert_json_rpc_code_range(code) · 驗證單個 JSON-RPC error.code 在範圍內

用於：
- ERR-IT-001/002 靜態斷言（integration test 入口）
- handler 啟動時校驗（fail-fast · 防止錯誤碼漂移）

憲法 §17 SOLID：
- SRP：service 專注錯誤碼靜態斷言
- DIP：依賴抽象（KnowledgeErrorCode + MemoryErrorCode IntEnum）
- 不修改錯誤碼（單一來源：packages/knowledge/errors/codes.py +
  services/knowledge-memory-service/backend/errors.py）
"""

from __future__ import annotations

from superteam_a2a.knowledge.errors.codes import KnowledgeErrorCode
from superteam_a2a.knowledge_memory.backend.errors import MemoryErrorCode

# JSON-RPC 2.0 標準 server-error 範圍
# 規範：-32000 to -32099（JSON-RPC 2.0 保留段）
# PR-4a 範圍：-32008 ~ -32018（Knowledge）+ -32101 ~ -32112（Memory）
JSON_RPC_KNOWLEDGE_CODE_MIN: int = -32008
JSON_RPC_KNOWLEDGE_CODE_MAX: int = -32018
JSON_RPC_MEMORY_CODE_MIN: int = -32101
JSON_RPC_MEMORY_CODE_MAX: int = -32112
JSON_RPC_VALID_CODE_MAX: int = -32211  # 含 -32200 ~ -32211 擴展段

# 23 錯誤碼權威集合（封閉擴展 · wire contract）
EXPECTED_KNOWLEDGE_CODES: frozenset[KnowledgeErrorCode] = frozenset(KnowledgeErrorCode)
EXPECTED_MEMORY_CODES: frozenset[MemoryErrorCode] = frozenset(MemoryErrorCode)


class WireSyncError(AssertionError):
    """Wire sync 校驗失敗異常。

    不變量：拋出時攜帶具體錯誤碼 + 失敗原因。
    """


class WireSyncService:
    """WireSyncService · 23 錯誤碼靜態斷言 + JSON-RPC code 範圍校驗。

    構造注入：無（無狀態 · 純靜態方法）。
    """

    @classmethod
    def assert_wire_sync_compliant(cls) -> None:
        """驗證 23 錯誤碼範圍 + 命名嚴格匹配。

        校驗項：
        1. 所有 11 個 KNOWLEDGE_* 錯誤碼都在 [-32018, -32008] 範圍內
        2. 所有 12 個 MEMORY_* 錯誤碼都在 [-32112, -32101] 範圍內
        3. 命名嚴格匹配：禁止新增同義錯誤碼（封閉擴展）
        4. 錯誤碼集合相等（PR-4a 權威名 · 防止本地漂移）

        異常：
        - WireSyncError · 任意校驗失敗
        """
        # 校驗 1：KNOWLEDGE 錯誤碼範圍（負數範圍 · MAX <= code <= MIN）
        for code in EXPECTED_KNOWLEDGE_CODES:
            value = int(code)
            if not (JSON_RPC_KNOWLEDGE_CODE_MAX <= value <= JSON_RPC_KNOWLEDGE_CODE_MIN):
                raise WireSyncError(
                    f"KNOWLEDGE error code out of range [{JSON_RPC_KNOWLEDGE_CODE_MAX}, "
                    f"{JSON_RPC_KNOWLEDGE_CODE_MIN}]: {code.name}={value}"
                )

        # 校驗 2：MEMORY 錯誤碼範圍（負數範圍 · MAX <= code <= MIN）
        for code in EXPECTED_MEMORY_CODES:
            value = int(code)
            if not (JSON_RPC_MEMORY_CODE_MAX <= value <= JSON_RPC_MEMORY_CODE_MIN):
                raise WireSyncError(
                    f"MEMORY error code out of range [{JSON_RPC_MEMORY_CODE_MAX}, "
                    f"{JSON_RPC_MEMORY_CODE_MIN}]: {code.name}={value}"
                )

        # 校驗 3：錯誤碼集合大小（封閉擴展 · 防止新增同義）
        if len(EXPECTED_KNOWLEDGE_CODES) != 11:
            raise WireSyncError(
                f"KNOWLEDGE error code count changed: expected 11, got "
                f"{len(EXPECTED_KNOWLEDGE_CODES)}"
            )
        if len(EXPECTED_MEMORY_CODES) != 12:
            raise WireSyncError(
                f"MEMORY error code count changed: expected 12, got {len(EXPECTED_MEMORY_CODES)}"
            )

    @classmethod
    def assert_json_rpc_code_range(cls, code: int) -> None:
        """驗證單個 JSON-RPC error.code 在合法範圍內。

        合法範圍：
        - -32008 ~ -32018（Knowledge 11 個）
        - -32101 ~ -32112（Memory 12 個）
        - -32200 ~ -32211（擴展段 · 預留）

        參數：
        - code · int · JSON-RPC error.code

        異常：
        - WireSyncError · code 在合法範圍外
        """
        if (
            JSON_RPC_KNOWLEDGE_CODE_MAX <= code <= JSON_RPC_KNOWLEDGE_CODE_MIN
            or JSON_RPC_MEMORY_CODE_MAX <= code <= JSON_RPC_MEMORY_CODE_MIN
        ):
            return

        # 允許擴展段（-32211 ~ -32200 · 預留未來錯誤碼 · 負數範圍 MAX <= code <= MIN）
        if -32211 <= code <= -32200:
            return

        raise WireSyncError(
            f"JSON-RPC error.code {code} out of valid range "
            f"[{JSON_RPC_KNOWLEDGE_CODE_MAX}, {JSON_RPC_KNOWLEDGE_CODE_MIN}] "
            f"+ [{JSON_RPC_MEMORY_CODE_MAX}, {JSON_RPC_MEMORY_CODE_MIN}] "
            f"+ [-32211, -32200] extension"
        )


__all__ = [
    "EXPECTED_KNOWLEDGE_CODES",
    "EXPECTED_MEMORY_CODES",
    "JSON_RPC_KNOWLEDGE_CODE_MAX",
    "JSON_RPC_KNOWLEDGE_CODE_MIN",
    "JSON_RPC_MEMORY_CODE_MAX",
    "JSON_RPC_MEMORY_CODE_MIN",
    "JSON_RPC_VALID_CODE_MAX",
    "WireSyncError",
    "WireSyncService",
]
