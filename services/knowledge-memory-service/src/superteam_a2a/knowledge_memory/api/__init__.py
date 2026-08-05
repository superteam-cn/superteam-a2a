"""L3-6 §6 in-process API surface · D 方案单进程架构。

子包：
- context: InProcessContext frozen Pydantic + Clock 注入
- results: MemoryRecordResult + QueryMemoryResult 不可变快照
- service: MemoryBackendInProcessService Protocol + Impl
"""
