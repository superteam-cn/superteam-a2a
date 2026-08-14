"""H-GKI-UT-003 · VisibilityService Protocol stub 拋 NotImplementedError。

驗證：
1. VisibilityService.resolve_visibility(item) 拋 NotImplementedError
2. VisibilityServiceProtocol runtime_checkable 允許 isinstance 檢查
3. 錯誤訊息提及 5 維矩陣

依據 PR-4b plan §7 H-GKI-UT-003 + L3-5 §5.4 5 維矩陣策略實裝推 PR-4c。
"""

from __future__ import annotations

import pytest
from superteam_a2a.knowledge_memory.services.shared.visibility import (
    VisibilityService,
    VisibilityServiceProtocol,
)


async def test_visibility_service_protocol_stub() -> None:
    """H-GKI-UT-003 · VisibilityService.resolve_visibility 拋 NotImplementedError。

    期望：
    1. VisibilityService().resolve_visibility(item) 拋 NotImplementedError
    2. 錯誤訊息提及 L3-5 §5.4 5 維矩陣
    """
    service = VisibilityService()
    with pytest.raises(NotImplementedError) as exc_info:
        await service.resolve_visibility(item={"name": "item-1"})
    assert "5-dim matrix" in str(exc_info.value) or "5 維矩陣" in str(exc_info.value)


def test_visibility_service_protocol_runtime_checkable() -> None:
    """VisibilityService 實例通過 isinstance(..., VisibilityServiceProtocol)。"""
    service = VisibilityService()
    assert isinstance(service, VisibilityServiceProtocol)


__all__ = [
    "test_visibility_service_protocol_runtime_checkable",
    "test_visibility_service_protocol_stub",
]
