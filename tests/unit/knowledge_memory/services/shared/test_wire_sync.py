"""WireSyncService 完整實裝測試 · 23 錯誤碼靜態斷言。

驗證：
1. WireSyncService.assert_wire_sync_compliant() 不拋異常
2. WireSyncService.assert_json_rpc_code_range(合法 code) 不�異常
3. WireSyncService.assert_json_rpc_code_range(非法 code) � WireSyncError
4. 知識錯誤碼數量 = 11 + Memory 錯誤碼數量 = 12

依據 PR-4b plan §2.4 + §6 不變量 5 + §7 ERR-IT-001/002。
"""

from __future__ import annotations

import pytest
from superteam_a2a.knowledge.errors.codes import KnowledgeErrorCode
from superteam_a2a.knowledge_memory import MemoryErrorCode
from superteam_a2a.knowledge_memory.services.shared.wire_sync import (
    EXPECTED_KNOWLEDGE_CODES,
    EXPECTED_MEMORY_CODES,
    JSON_RPC_KNOWLEDGE_CODE_MAX,
    JSON_RPC_KNOWLEDGE_CODE_MIN,
    JSON_RPC_MEMORY_CODE_MAX,
    JSON_RPC_MEMORY_CODE_MIN,
    WireSyncError,
    WireSyncService,
)


def test_wire_sync_assert_compliant_passes() -> None:
    """WireSyncService.assert_wire_sync_compliant() 通過 · 23 錯誤碼在範圍內。

    期望：
    1. assert_wire_sync_compliant() 不拋異常
    2. EXPECTED_KNOWLEDGE_CODES 數量 == 11
    3. EXPECTED_MEMORY_CODES 數量 == 12
    """
    WireSyncService.assert_wire_sync_compliant()

    assert len(EXPECTED_KNOWLEDGE_CODES) == 11
    assert len(EXPECTED_MEMORY_CODES) == 12


def test_wire_sync_assert_knowledge_range() -> None:
    """所有 KnowledgeErrorCode 都在 [-32018, -32008] 範圍內（負數範圍）。

    期望：
    1. 遍歷 KnowledgeErrorCode · 每個都在範圍內
    """
    for code in KnowledgeErrorCode:
        value = int(code)
        assert JSON_RPC_KNOWLEDGE_CODE_MAX <= value <= JSON_RPC_KNOWLEDGE_CODE_MIN


def test_wire_sync_assert_memory_range() -> None:
    """所有 MemoryErrorCode 都在 [-32112, -32101] 範圍內（負數範圍）。

    期望：
    1. 遍歷 MemoryErrorCode · 每個都在範圍內
    """
    for code in MemoryErrorCode:
        value = int(code)
        assert JSON_RPC_MEMORY_CODE_MAX <= value <= JSON_RPC_MEMORY_CODE_MIN


@pytest.mark.parametrize("code", [-32008, -32015, -32018, -32101, -32107, -32112])
def test_wire_sync_assert_json_rpc_code_range_accepts_valid(code: int) -> None:
    """assert_json_rpc_code_range(合法 code) 不拋異常。

    參數：
    - code · 已知合法錯誤碼（含 Knowledge + Memory 兩端）
    """
    WireSyncService.assert_json_rpc_code_range(code)


@pytest.mark.parametrize("code", [-32000, -32050, -32100, -32212, -32700])
def test_wire_sync_assert_json_rpc_code_range_rejects_invalid(code: int) -> None:
    """assert_json_rpc_code_range(非法 code) 拋 WireSyncError。

    參數：
    - code · 非法錯誤碼（不在範圍內）
    """
    with pytest.raises(WireSyncError):
        WireSyncService.assert_json_rpc_code_range(code)


def test_wire_sync_extension_range_accepted() -> None:
    """assert_json_rpc_code_range(-32200 ~ -32211 擴展段) 不拋異常。

    期望：
    1. 擴展段（預留未來錯誤碼）也通過校驗
    """
    WireSyncService.assert_json_rpc_code_range(-32200)
    WireSyncService.assert_json_rpc_code_range(-32211)


__all__ = [
    "test_wire_sync_assert_compliant_passes",
    "test_wire_sync_assert_json_rpc_code_range_accepts_valid",
    "test_wire_sync_assert_json_rpc_code_range_rejects_invalid",
    "test_wire_sync_assert_knowledge_range",
    "test_wire_sync_assert_memory_range",
    "test_wire_sync_extension_range_accepted",
]
