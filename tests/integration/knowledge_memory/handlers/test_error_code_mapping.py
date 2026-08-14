"""ERR-IT-001/002 · 23 錯誤碼靜態斷言 IT 測試。

PR-4b plan §7 IT 增量：
- ERR-IT-001 · 23 錯誤碼 → JSON-RPC error.code 映射靜態斷言
- ERR-IT-002 · wire_sync 靜態斷言（IntEnum 完整性 + 命名嚴格匹配）

驗證：
1. 11 KNOWLEDGE_* 錯誤碼範圍 -32008 ~ -32018
2. 12 MEMORY_* 錯誤碼範圍 -32101 ~ -32112
3. 23 錯誤碼全部通過 assert_json_rpc_code_range 校驗
4. 所有錯誤碼都是 IntEnum 成員（無裸整數）
5. 命名嚴格匹配（封閉擴展 · 無新增同義錯誤碼）
"""

from __future__ import annotations

import sys
from enum import IntEnum
from pathlib import Path

# 路径前置
_REPO_ROOT = Path(__file__).resolve().parents[5]
_KM_SRC = _REPO_ROOT / "services" / "knowledge-memory-service" / "src"
_KN_SRC = _REPO_ROOT / "packages" / "knowledge" / "src"

_KM_PATH = str(_KM_SRC)
if _KM_PATH not in sys.path:
    sys.path.insert(0, _KM_PATH)
_KN_PATH = str(_KN_SRC)
if _KN_PATH not in sys.path:
    sys.path.insert(0, _KN_PATH)

from superteam_a2a.knowledge.errors.codes import KnowledgeErrorCode  # noqa: E402
from superteam_a2a.knowledge_memory import MemoryErrorCode  # noqa: E402
from superteam_a2a.knowledge_memory.services.shared.wire_sync import (  # noqa: E402
    EXPECTED_KNOWLEDGE_CODES,
    EXPECTED_MEMORY_CODES,
    JSON_RPC_KNOWLEDGE_CODE_MAX,
    JSON_RPC_KNOWLEDGE_CODE_MIN,
    JSON_RPC_MEMORY_CODE_MAX,
    JSON_RPC_MEMORY_CODE_MIN,
    WireSyncError,
    WireSyncService,
)


# ERR-IT-001
def test_23_error_codes_map_to_json_rpc_range() -> None:
    """ERR-IT-001 · 23 錯誤碼靜態斷言 + JSON-RPC 範圍校驗。

    驗證：
    1. 11 KNOWLEDGE_* 錯誤碼全部在 [-32018, -32008] 範圍
    2. 12 MEMORY_* 錯誤碼全部在 [-32112, -32101] 範圍
    3. 23 錯誤碼全部通過 assert_json_rpc_code_range
    """
    # Knowledge 範圍校驗
    knowledge_codes = list(KnowledgeErrorCode)
    assert len(knowledge_codes) == 11, f"expected 11 KNOWLEDGE codes, got {len(knowledge_codes)}"
    for code in knowledge_codes:
        value = int(code)
        assert JSON_RPC_KNOWLEDGE_CODE_MAX <= value <= JSON_RPC_KNOWLEDGE_CODE_MIN, (
            f"KNOWLEDGE code {code.name}={value} out of range"
        )
        # assert_json_rpc_code_range 不拋異常
        WireSyncService.assert_json_rpc_code_range(value)

    # Memory 範圍校驗
    memory_codes = list(MemoryErrorCode)
    assert len(memory_codes) == 12, f"expected 12 MEMORY codes, got {len(memory_codes)}"
    for code in memory_codes:
        value = int(code)
        assert JSON_RPC_MEMORY_CODE_MAX <= value <= JSON_RPC_MEMORY_CODE_MIN, (
            f"MEMORY code {code.name}={value} out of range"
        )
        # assert_json_rpc_code_range 不拋異常
        WireSyncService.assert_json_rpc_code_range(value)

    # 總計 23 錯誤碼
    assert len(knowledge_codes) + len(memory_codes) == 23


# ERR-IT-002
def test_wire_sync_static_assertion_compliant() -> None:
    """ERR-IT-002 · wire_sync 靜態斷言 · IntEnum 完整性 + 命名嚴格匹配。

    驗證：
    1. assert_wire_sync_compliant() 不拋異常（23 錯誤碼範圍校驗通過）
    2. KnowledgeErrorCode + MemoryErrorCode 都是 IntEnum 子類
    3. 23 錯誤碼全部是 IntEnum 成員（無裸整數）
    4. 命名嚴格匹配（封閉擴展 · 無新增同義錯誤碼）
    5. EXPECTED_KNOWLEDGE_CODES + EXPECTED_MEMORY_CODES 與權威表一致
    """
    # wire_sync 靜態斷言
    WireSyncService.assert_wire_sync_compliant()

    # IntEnum 完整性
    assert issubclass(KnowledgeErrorCode, IntEnum)
    assert issubclass(MemoryErrorCode, IntEnum)

    # 所有錯誤碼都是 IntEnum 成員（無裸整數污染）
    for code in KnowledgeErrorCode:
        assert isinstance(code, KnowledgeErrorCode)
        assert isinstance(code, IntEnum)
        assert isinstance(code.value, int)
    for code in MemoryErrorCode:
        assert isinstance(code, MemoryErrorCode)
        assert isinstance(code, IntEnum)
        assert isinstance(code.value, int)

    # 命名嚴格匹配（封閉擴展）
    assert len(EXPECTED_KNOWLEDGE_CODES) == 11
    assert len(EXPECTED_MEMORY_CODES) == 12
    assert len(EXPECTED_KNOWLEDGE_CODES) + len(EXPECTED_MEMORY_CODES) == 23

    # 集合相等（PR-4a 權威名 · 防止本地漂移）
    assert frozenset(KnowledgeErrorCode) == EXPECTED_KNOWLEDGE_CODES
    assert frozenset(MemoryErrorCode) == EXPECTED_MEMORY_CODES


# ERR-IT-002a · to_json_rpc_error_code helper 單元測試（defensive）
def test_to_json_rpc_error_code_helper() -> None:
    """ERR-IT-002a · WireSyncService.to_json_rpc_error_code 統一映射 helper。

    驗證：
    1. MemoryBackendError → MemoryErrorCode.value
    2. KnowledgeError → KnowledgeErrorCode.value
    3. 其他異常 → -32603（JSON-RPC 2.0 internal_error）
    """
    from superteam_a2a.knowledge.errors.codes import (
        KnowledgeContractError,
        KnowledgeError,
    )
    from superteam_a2a.knowledge_memory.backend.errors import (
        MemoryBackendError,
        MemoryContractError,
    )

    # Memory 異常映射
    mem_exc = MemoryBackendError(MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT, "test")
    assert WireSyncService.to_json_rpc_error_code(mem_exc) == -32112

    mem_contract_exc = MemoryContractError(MemoryErrorCode.MEMORY_INVALID_CONTENT, "test contract")
    assert WireSyncService.to_json_rpc_error_code(mem_contract_exc) == -32102

    # Knowledge 異常映射
    kn_exc = KnowledgeError(KnowledgeErrorCode.KNOWLEDGE_ITEM_NOT_FOUND, "test kn")
    assert WireSyncService.to_json_rpc_error_code(kn_exc) == -32012

    kn_contract_exc = KnowledgeContractError(
        KnowledgeErrorCode.KNOWLEDGE_INVALID_TYPE, "test contract"
    )
    assert WireSyncService.to_json_rpc_error_code(kn_contract_exc) == -32010

    # 其他異常 → -32603
    generic_exc = ValueError("test")
    assert WireSyncService.to_json_rpc_error_code(generic_exc) == -32603


# ERR-IT-002b · 非法 code 觸發 WireSyncError
def test_assert_json_rpc_code_range_rejects_invalid() -> None:
    """ERR-IT-002b · assert_json_rpc_code_range 非法 code 拋 WireSyncError。

    驗證：
    1. -32000（JSON-RPC 保留段）拋 WireSyncError
    2. -32700（JSON-RPC ParseError）拋 WireSyncError
    3. -32212（擴展段外）拋 WireSyncError
    """
    with __import__("pytest").raises(WireSyncError):
        WireSyncService.assert_json_rpc_code_range(-32000)
    with __import__("pytest").raises(WireSyncError):
        WireSyncService.assert_json_rpc_code_range(-32700)
    with __import__("pytest").raises(WireSyncError):
        WireSyncService.assert_json_rpc_code_range(-32212)


__all__ = [
    "test_23_error_codes_map_to_json_rpc_range",
    "test_assert_json_rpc_code_range_rejects_invalid",
    "test_to_json_rpc_error_code_helper",
    "test_wire_sync_static_assertion_compliant",
]
