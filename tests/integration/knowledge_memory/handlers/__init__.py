"""tests/integration/knowledge_memory/handlers/ · 4 A2A handler 端到端 IT 測試。

PR-4b plan §7 IT 增量 6 ID：
- H-RM-IT-001 · recordMemory 端到端（admission pass + record_service mock）
- H-QM-IT-001 · queryMemory 端到端（MEMORY_QUERY_TOO_BROAD 觸發）
- H-QK-IT-001 · queryKnowledge 端到端（BM25 stub 空列表）
- H-GKI-IT-001 · getKnowledgeItem 端到端（not found stub）
- ERR-IT-001 · 23 錯誤碼靜態斷言
- ERR-IT-002 · wire_sync 靜態斷言

handler 與 service 解耦（mock service · 不實裝業務邏輯）。
父目錄 conftest.py 已恢復真實 kopf 模組（避免 MagicMock 污染）。
"""
