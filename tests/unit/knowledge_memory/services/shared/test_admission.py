"""AdmissionService 完整實裝測試。

驗證：
1. AdmissionService.execute(memory) 委託 AdmissionValidatorImpl.validate
2. validator.validate 被呼叫一次 · timeout=0.050
3. validator 異常原樣透傳

依據 PR-4b plan §2.3 handler 復用 PR-4a admission algorithm + 50ms fail-closed。
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from superteam_a2a.knowledge_memory import (
    MemoryBackendError,
    MemoryErrorCode,
)
from superteam_a2a.knowledge_memory.handlers.admission_validator import (
    AdmissionValidatorImpl,
)
from superteam_a2a.knowledge_memory.services.shared.admission import (
    ADMISSION_TIMEOUT_SECONDS,
    AdmissionService,
)


async def test_admission_service_delegates_to_validator(sample_memory) -> None:
    """AdmissionService.execute 委託 AdmissionValidatorImpl.validate。

    期望：
    1. fake validator.validate 被呼叫一次
    2. 傳入參數：memory + timeout=0.050
    3. 返回 None
    """
    validator = AsyncMock(spec=AdmissionValidatorImpl)
    service = AdmissionService(validator=validator)

    result = await service.execute(sample_memory)

    validator.validate.assert_awaited_once()
    call_kwargs = validator.validate.await_args.kwargs
    assert call_kwargs["timeout"] == ADMISSION_TIMEOUT_SECONDS
    assert result is None


async def test_admission_service_propagates_validator_exception(sample_memory) -> None:
    """AdmissionService.execute 透傳 validator 異常。

    期望：
    1. fake validator.validate 拋 MemoryBackendError(MEMORY_ADMISSION_TIMEOUT)
    2. service 不重映射 · 原樣透傳
    """
    validator = AsyncMock(spec=AdmissionValidatorImpl)
    validator.validate.side_effect = MemoryBackendError(
        MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT,
        "admission.validate exceeded 50ms",
    )
    service = AdmissionService(validator=validator)

    with pytest.raises(MemoryBackendError) as exc_info:
        await service.execute(sample_memory)
    assert exc_info.value.code == MemoryErrorCode.MEMORY_ADMISSION_TIMEOUT


__all__ = [
    "test_admission_service_delegates_to_validator",
    "test_admission_service_propagates_validator_exception",
]
