"""Shared 業務邏輯 service 層 · 4 文件（依賴順序最後實裝）。

依據 PR-4b plan §2.2 依賴關係：Shared → Knowledge → Memory 單向依賴。

- admission · AdmissionService · 委託 PR-4a AdmissionValidatorImpl（含 50ms fail-closed）
- visibility · VisibilityService · Protocol stub（5 維矩陣策略實裝推 PR-4c）
- inherit · InheritService · Protocol stub（4 級 scope 繼承規則推 PR-4c）
- wire_sync · WireSyncService · 完整實裝：23 錯誤碼靜態斷言

5 項關鍵不變量驗證（PR-4b plan §6）：
1. wire contract 完全繼承 L2-4 v0.2.0 Spec
2. 50ms fail-closed（admission 委託 AdmissionValidatorImpl）
3. Pydantic v2 + populate_by_name + alias + extra=forbid + frozen
4. Python-first 邊界（≤ 4 第三方依賴）
5. JSON-RPC error.code 映射（23 錯誤碼範圍 -32101 ~ -32211）
"""
