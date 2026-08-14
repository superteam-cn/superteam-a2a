"""H-GKI-UT-002 · InheritService Protocol stub 拋 NotImplementedError。

驗證：
1. InheritService.resolve_inherit_chain(scope_ref) 拋 NotImplementedError
2. InheritServiceProtocol runtime_checkable 允許 isinstance 檢查
3. 錯誤訊息提及 4 級 scope 繼承規則

依據 PR-4b plan §7 H-GKI-UT-002 + L3-5 §5.5 4 級 scope 繼承規則實裝推 PR-4c。
"""

from __future__ import annotations

import pytest
from superteam_a2a.knowledge_memory.services.shared.inherit import (
    InheritService,
    InheritServiceProtocol,
)


async def test_inherit_service_protocol_stub() -> None:
    """H-GKI-UT-002 · InheritService.resolve_inherit_chain 拋 NotImplementedError。

    期望：
    1. InheritService().resolve_inherit_chain(scope_ref) 拋 NotImplementedError
    2. 錯誤訊息提及 4 級 scope 繼承規則
    """
    service = InheritService()
    with pytest.raises(NotImplementedError) as exc_info:
        await service.resolve_inherit_chain(scope_ref={"name": "scope-1", "level": "scope"})
    assert "4-level scope" in str(exc_info.value) or "4 級 scope" in str(exc_info.value)


def test_inherit_service_protocol_runtime_checkable() -> None:
    """InheritService 實例通過 isinstance(..., InheritServiceProtocol)。"""
    service = InheritService()
    assert isinstance(service, InheritServiceProtocol)


__all__ = [
    "test_inherit_service_protocol_runtime_checkable",
    "test_inherit_service_protocol_stub",
]
