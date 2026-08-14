"""AdmissionService · 業務邏輯層 admission 路徑。

委託 `AdmissionValidatorImpl` (PR-4a 已實裝 5 步算法 + 50ms fail-closed)。

PR-4b plan §2.3：handler 復用 PR-4a admission algorithm。50ms fail-closed
單一來源在 AdmissionValidatorImpl；本 service 層僅負責構造調用上下文，
業務邏輯全部在 AdmissionValidatorImpl。

DIP：service 依賴 AdmissionValidatorImpl（PR-4a 已實裝）；CRP：構造注入 validator。
"""

from __future__ import annotations

from superteam_a2a.knowledge_memory.backend.memory import Memory
from superteam_a2a.knowledge_memory.handlers.admission_validator import (
    AdmissionValidatorImpl,
)

# §6.4 step 2 50ms admission deadline fail-closed（與 api/service.py 同源）
ADMISSION_TIMEOUT_SECONDS: float = 0.050


class AdmissionService:
    """Admission 業務邏輯 · 委託 AdmissionValidatorImpl。

    構造注入：
    - validator · AdmissionValidatorImpl（PR-4a 已實裝 5 步算法 + 50ms fail-closed）
    - timeout · float（默認 0.050 = 50ms · fail-closed 硬上限）
    """

    def __init__(
        self,
        *,
        validator: AdmissionValidatorImpl,
        timeout: float = ADMISSION_TIMEOUT_SECONDS,
    ) -> None:
        self._validator = validator
        self._timeout = timeout

    async def execute(self, memory: Memory) -> None:
        """執行 admission 校驗 · 委託 validator.validate。

        參數：
        - memory · Memory 頂層 CRD

        返回：
        - None（校驗通過）

        異常：
        - MemoryBackendError · 12 MEMORY_* 封閉錯誤碼（透傳 · 不重映射）
        - KnowledgeContractError · KNOWLEDGE_* 錯誤碼（PR-4a 5 步算法拋出）

        不變量：
        - 50ms fail-closed（timeout 嚴格 ≤ 0.050）
        - validator 異常原樣透傳（不重映射）
        """
        await self._validator.validate(memory, timeout=self._timeout)


__all__ = [
    "ADMISSION_TIMEOUT_SECONDS",
    "AdmissionService",
]
