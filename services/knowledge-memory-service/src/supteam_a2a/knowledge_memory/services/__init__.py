"""PR-4b · 12 service 业务邏輯層 · 三層架構（Memory + Knowledge + Shared）。

L3-5 + L3-6 v0.2.0 + ADR-0006 D 方案單進程架構下，service 層承載：
- Memory service（4）· record/query/reinforce/gc · 完整業務邏輯實裝
- Knowledge service（4）· query/item/record/scope · Protocol stub（BM25 推 PR-4c）
- Shared service（4）· admission 委託 / visibility/inherit Protocol / wire_sync 實裝

憲法 §17 SOLID 6 原則：
- SRP：每個 service 一個職責
- OCP：service 通過 Protocol 擴展，不修改 InProcessService
- LSP：Memory service 任一實装可替换
- DIP：service 依賴 Protocol + 抽象
- ISP：Knowledge service Protocol 接口最小化
- CRP：優先組合（構造注入 backend）
"""
