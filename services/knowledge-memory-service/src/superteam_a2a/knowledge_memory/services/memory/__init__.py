"""Memory 業務邏輯 service 層 · 4 文件。

- record · MemoryRecordService · 委託 InProcessService.record_memory_async（含 50ms fail-closed）
- query · MemoryQueryService · 委託 InProcessService.query_memory_async（含 industry 預檢 + confidence 後置過濾）
- reinforce · MemoryReinforceService · backend.patch_status CAS 提升 confidence
- gc · MemoryGCService · mark/archive/delete 狀態轉換

依據 L3-6 §6.4 + §5.7 不變量 2（線性化單 key 寫 + CAS 顯式失敗）。
"""
