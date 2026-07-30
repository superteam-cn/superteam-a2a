# L3 文件级 Spec：Memory backend（Card-driven Memory 服务 · Python-first · 同 Pod 第二 Python 进程 · #64-#67.x 起草）

> **模块定位**：C-7 Memory backend（Card-driven Memory 服务 · v0.1 · 同 Pod 第二 Python 进程 / 单 Uvicorn worker / 端口 8081 cluster-internal / 与 L3-5 Knowledge Service 共享 Deployment / 独占 MemoryReconciler 60s @kopf.timer + Leader Election Lease + 4 纯函数 decay/reinforce/GC/promotion + Clock Protocol + BM25 启动期全量重建）
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-7（Memory backend，见 L1 Architecture §3.5.3 + §4.3）
> **代码位置**：
> - **CRD types**：`packages/memory/src/supteam_a2a/memory/apis/v1alpha1/`（Memory schema Pydantic v2 12 spec 字段完整版 + 5 维 visibility 矩阵复用 + 4 级 scope 复用）
> - **A2A/Business 部署**：`services/memory-backend/src/supteam_a2a/memory_backend/`（ASGI 单进程 + 4 纯函数 + 60s kopf.timer + Leader Election + Clock Protocol + BM25 启动期全量重建 + Helm 7 模板与 L3-5 共享）
> - **部署共享**：`services/memory-backend/` 与 `services/knowledge-service/` 共享同 Deployment（同 Pod 内两个独立 Python 进程；详见 L3-5 §6.2 + 本 Spec §6）
> - **uv workspace 布局**：ADR-0005 §13.1
> **版本**：**v0.2.0**（2026-07-29 #64 骨架 + #65 §3-§6 + 2026-07-30 #66 §7-§13/附录 A/B + 2026-07-30 #67 独立评审通过 + #67.x 5 关注项同步修正 + §F 9 步跨文档同步）
> **状态**：✅ **v0.2.0 已通过独立评审**（§A-§Q 17 节 / 10 维度全 PASS · 0 阻塞项 · 5 关注项全关闭 · 4 建议项移交 v0.2.1 / L4 实施；Memory CRD 12 字段、60s reconciler、4 纯函数、MemoryBackend Protocol、10 指标、12 个零漂移错误码、共享 Helm chart、read/write 双 Role + admissionregistration/authentication/authorization 扩展、60 测试 ID + 集合相等静态断言、30 验收点全部形成文件级契约）
> **supersede / 归档标记（2026-07-29）**：本 v0.2.0 Spec 文档**仅 supersede Go reconciler / Go BM25 sync.Map / Go controller-runtime Reconcile() / Go k8s.io/utils/clock 实现条款**；wire contract（Memory CRD 12 spec 字段 / 4 纯函数公式 / 5 维 visibility 矩阵 / 4 级 scope 继承 / Leader Election Lease / 60s 周期 / decay 公式 `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` / 12 个 MEMORY_* 错误码 / Helm values）与 L2-4 v0.2.0 Spec 业务语义**完全继续有效**。L2-4 v0.1.0 Go baseline 已在 L2-4 Spec v0.2.0 起草时覆盖丢失（与 L2-1/L2-3/L3-1/L3-2/L3-3/L3-4/L3-5 同模式；建议 #64.x 后续会话追溯 v0.1.0 Go 归档登记）
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.5.3 + §4.3 C-7 + ADR-0005 §3.4 + §6.2 + §6.3 + §10 + §13.1 + L2-4 v0.2.0 Spec §7 MemoryReconciler + §6.6 共享 Deployment + L2-4 v0.2.0 Design §3-§14，Memory CRD Go struct → **Pydantic v2 BaseModel + Field(...) + populate_by_name + alias（与 L3-5 §3.3 5+5 简化版 wire 一致的 12 spec 字段完整版）**；Go controller-runtime Reconcile() → **Kopf `@kopf.timer(interval=60.0, id="memory-reconciler")` + 独立 async reconciler service + Leader Election via coordination.k8s.io/v1 Lease（renew 失败 3 次让位 + 30s grace period）**；Go sync.Map BM25 → **Python `dict[str, set[str]]` + anyio.to_thread.run_sync 启动期全量重建 + watch 增量**；Go k8s.io/utils/clock → **`Clock` Protocol + `RealClock` + `FakeClock`（测试用 freezegun 替代）**；Go 4 纯函数（apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion）→ **Python 同步 pure function + async wrapper（lru_cache 缓存 + 不阻塞 event loop）**；recordMemory/queryMemory → **Python ASGI handler + L3-5 逻辑 function-reference Protocol 委托；跨 container transport 在 L4 spike 中从 UDS/共享 runtime 选择，禁止 HTTP loopback**
> **上游约束**：
> - [`docs/design/L2-modules/L2-knowledge-memory.md`](../../design/L2-modules/L2-knowledge-memory.md) **v0.2.0**（2026-07-27 #39 评审通过 · 1920 行 / 97KB / 14 节 + 2 附录 / 5 项 Python 化关键决策 + 9 维度 Go→Python 对照表 + 22 项开放问题三层模式）
> - [`docs/spec/L2-module-specs/L2-knowledge-memory.md`](../../spec/L2-module-specs/L2-knowledge-memory.md) **v0.2.0**（2026-07-27 #42 补完 + #43 评审通过 · 4156 行 / 195KB / 16 节 + 2 附录 + §16 元数据 / 60 测试 ID + 30 验收点 + 22 开放问题 / 3 Pydantic v2 CRD types + 4 A2A method + 4 级 scope 继承 + 5 维矩阵 + admission 互斥 + MemoryReconciler 60s kopf.timer + BM25 倒排索引 + 22 错误码 + 20 指标）
> - [L1 Architecture v0.2.0 §3.5.3 MemoryReconciler + §4.3 C-7](../../design/L1-architecture.md)
> - [L1 Spec v0.2.0 §5.2.3 Memory YAML 示例](../../spec/L1-system-spec.md)
> - [ADR-0003 Memory 设计 §3 Memory CRD + §4 decay 公式 + §5 admission 互斥 + §6 MemoryReconciler](../../adr/0003-memory-design.md)
> - [ADR-0005 Python-first §3.4 Memory backend 模块映射 + §6.2 单进程原则 + §6.3 CPU offload + §10 structlog + §13.1 uv workspace](../../adr/0005-python-first-technology-stack.md)
> - [L3-1 Operator Core v0.2.0 §3.4 MemoryReconciler 协调 + §7 Helm 9 模板 + §7.3 RBAC](../../spec/L3-file-specs/L3-operator-core.md)
> - [L3-2 A2A Core v0.2.0 §5 ASGI server + §6 A2AClient + §9 15 Prometheus 指标 + §10 24 错误码](../../spec/L3-file-specs/L3-a2a-core.md)
> - [L3-3 Adapter SDK v0.2.0 §3 FrameworkAdapter Protocol](../../spec/L3-file-specs/L3-adapter-sdk.md)（L3-6 不依赖 Adapter SDK · 与 L3-4/L3-5 同模式 Card-driven 单实例）
> - [L3-4 Hello Agent v0.2.0 §3.2 HelloAgentExecutor + §5 ASGI server + §6.9 25 ID 测试](../../spec/L3-file-specs/L3-hello-agent.md)
> - [L3-5 Knowledge Service v0.2.0 §3.3 Memory 5+5 简化 schema（5 spec 字段 + 5 status 字段 · wire 与 L3-6 §3 12 spec 字段完整版完全一致）+ §6.2 共享 Deployment in-process function reference 契约 + §9.9 共享 Helm chart 段落](../../spec/L3-file-specs/L3-knowledge-service.md)（**L3-6 与 L3-5 共享 Deployment + 4 A2A method 委托 + 12 MEMORY_* 错误码与 L3-6 §8 完全一致**）
> **本 Spec 目的**：将 L2-4 Spec v0.2.0 中的 **MemoryReconciler 60s @kopf.timer + Leader Election Lease + 4 纯函数（apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion）+ Clock Protocol + BM25 启动期全量重建 + 12 个 MEMORY_* 错误码 + Helm 7 模板（与 L3-5 共享 chart）** 落地为 **文件级 Python 代码契约**——每个文件列明**绝对路径（基于 uv workspace 布局）**、**职责一句话**、**完整 import 列表**、**exported 符号签名（type hints + docstring 一行）**、**内部 helper 列表**、**关联测试文件路径 + 测试 ID 前缀**。是 L4 实施阶段（开发者打开 IDE 即可对照写代码）的直接输入。
> **配套 Spec**：[L3-1 Operator Core 文件级 Spec v0.2.0](./L3-operator-core.md)（2026-07-28 #56 评审通过 · CRD wire sync + MemoryReconciler 60s 周期 + §7 Helm 9 模板 + §7.3 RBAC）/ [L3-2 A2A Core Library 文件级 Spec v0.2.0](./L3-a2a-core.md)（2026-07-28 #54 评审通过 · ASGI + A2AClient + 15 指标 + 24 错误码）/ [L3-3 Adapter SDK 文件级 Spec v0.2.0](./L3-adapter-sdk.md)（2026-07-29 #58 评审通过 · L3-6 不依赖 Adapter SDK）/ [L3-4 Hello Agent 文件级 Spec v0.2.0](./L3-hello-agent.md)（2026-07-29 #61 评审通过）/ [L3-5 Knowledge Service 文件级 Spec v0.2.0](./L3-knowledge-service.md)（2026-07-29 #63.5 评审通过 · **关键引用 · §3.3 Memory 5+5 简化 schema + §5 admission 互斥 + §6.2 共享 Deployment in-process 契约 + §9.9 共享 Helm chart 段落 + §8.2 12 MEMORY_* 错误码权威名**）
> **配套 Review**：[`docs/reviews/l3-6-memory-backend-spec-review.md`](../../reviews/l3-6-memory-backend-spec-review.md) **v0.2.0**（2026-07-30 #67 · 525 行 / 67.9KB / §A-§Q 17 节 / 10 维度全 PASS · 0 阻塞项 · 5 关注项全关闭 · 4 建议项）

---

## 0. 阅读指南

- **读者**：Memory backend 实施工程师（L4 Python 编码）、Helm 部署工程师（同 Pod 共享 Deployment 双 Container 部署）、架构 Reviewer（Memory↔Knowledge 双向互斥边界 + 4 纯函数语义一致性）、A2A method 集成者（recordMemory / queryMemory 委托调用方）、L4 衰减/Promotion 算法集成者
- **必读章节**：
  - §1（模块使命 + 5 项关键不变量 + 5 项 Python 化关键决策 D-1~D-5 + 28 文件清单总览）
  - §2（Python 包结构 + ADR-0005 §13.1 uv workspace 布局 + 6 项边界规则）
  - §3（Memory CRD 12 spec 字段完整版 Pydantic v2 schema · 与 L3-5 §3.3 5+5 简化版 wire 一致 · wire 同步矩阵 · 衰减公式）
  - §4（MemoryReconciler 60s @kopf.timer + Leader Election Lease + 30s grace period + renew 失败 3 次让位）
  - §5（4 纯函数：apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion + Clock Protocol + RealClock + FakeClock + freezegun 替代）
  - §6（in-process function reference 契约：record_memory_async / query_memory_async + 与 L3-5 共享内存或 in-process call + 异常透传 3 项规则）
  - §7（observability + 10 指标 + structlog 8 字段 + 2-3 MEMORY_* EventReason）
  - §8（12 个 MEMORY_* 错误码 enum · **与 L2-4 v0.2.0 §9.1 权威名 100% 一致** + Retryable 矩阵）
  - §9（Helm values 7 模板 + 与 L3-5 共享 chart + memory-backend container + RBAC **拆 write Role**（L3-5-followup-1））
  - §10（60 测试 ID 矩阵 + 30 验收点 + 6 层级金字塔）
  - 附录 A（跨模块引用清单 5 子表）/ 附录 B（ADR / Constitution 5 子表追溯矩阵）
- **评审入口**：§10 验收清单 + 附录 A 5 子表 + 附录 B 5 子表 + 28 文件级契约 + 60 测试 ID 互相回链
- **配套阅读**：
  - [L2-4 Spec v0.2.0 §3-§15](../../spec/L2-module-specs/L2-knowledge-memory.md)（Memory CRD 12 spec 字段 + 4 A2A method + 4 级 scope + 5 维矩阵 + admission 互斥 + 60 测试 ID + 22 开放问题）
  - [L2-4 Design v0.2.0 §3-§14](../../design/L2-modules/L2-knowledge-memory.md)（5 项 Python 化决策 + 9 维度 Go→Python 对照表 + 22 开放问题）
  - [L1 Architecture v0.2.0 §3.5.3 MemoryReconciler + §4.3 C-7](../../design/L1-architecture.md)
  - [L1 Spec v0.2.0 §5.2.3 Memory YAML 示例](../../spec/L1-system-spec.md)
  - [ADR-0003 Memory 设计 §3 Memory CRD schema + §4.1 decay 公式 + §5 admission 互斥 + §6 MemoryReconciler](../../adr/0003-memory-design.md)
  - [ADR-0005 Python-first §3.4 + §6.2 + §6.3 + §10 + §13.1](../../adr/0005-python-first-technology-stack.md)
  - [L3-1 Operator Core v0.2.0 §3.4 MemoryReconciler 协调 + §7 Helm 9 模板 + §7.3 RBAC](../../spec/L3-file-specs/L3-operator-core.md)
  - [L3-2 A2A Core v0.2.0 §5 ASGI + §6 A2AClient + §9 15 指标 + §10 24 错误码](../../spec/L3-file-specs/L3-a2a-core.md)
  - [L3-3 Adapter SDK v0.2.0 §3 FrameworkAdapter Protocol](../../spec/L3-file-specs/L3-adapter-sdk.md)（L3-6 不依赖 Adapter SDK）
  - [L3-4 Hello Agent v0.2.0 §3.2 HelloAgentExecutor + §5 ASGI + §6.9 25 ID 测试](../../spec/L3-file-specs/L3-hello-agent.md)
  - **[L3-5 Knowledge Service v0.2.0 §3.3 Memory 5+5 简化 schema + §5 admission 互斥 + §6.2 共享 Deployment in-process 契约 + §9.9 共享 Helm chart 段落 + §8.2 12 MEMORY_* 错误码权威名](../../spec/L3-file-specs/L3-knowledge-service.md)**
  - [a2a-sdk 官方文档](https://github.com/google/a2a-python) · [Kopf 官方文档](https://kopf.readthedocs.io/) · [kubernetes_asyncio 文档](https://github.com/kubernetes-client/python/tree/master/kubernetes_asyncio) · [freezegun 文档](https://github.com/spulec/freezegun)

**与 L3-1/L3-2/L3-3/L3-4/L3-5 复用边界**：
- L3-6 复用 L3-2 §5 ASGI server（单进程 / 单 Uvicorn worker / port 8081 cluster-internal + `/healthz` `/readyz` `/metrics`）
- L3-6 复用 L3-2 §6 A2AClient（如需在 handler 内调用其他 A2A method；L3-6 主要做 server 端 in-process call 委托，不强依赖）
- L3-6 复用 L3-2 §9 15 Prometheus 指标（11 A2A + 4 Python runtime；L3-6 新增 10 个 Memory 业务指标 `superteam_memory_*`）
- L3-6 复用 L3-2 §10 24 错误码 enum（**L3-6 独占 12 个 MEMORY_* 错误码 · 与 L2-4 v0.2.0 §9.1 权威名 100% wire 一致 · 详见 §8**）
- L3-6 复用 L3-1 §3.1 Agent Controller + §3.4 MemoryReconciler 协调（CRD wire sync 共享）
- L3-6 复用 L3-1 §7 Helm 9 模板基础（适配为共享 7 模板 deployment 含 memory-backend container + L3-5 共享 chart）
- L3-6 复用 L3-1 §7.3 RBAC（**拆分 read-only (L3-5) / write (L3-6) 两个最小 Role 共享 SA `knowledge-service` · L3-5-followup-1 处理**）
- **L3-6 不依赖 L3-3 Adapter SDK**（Card-driven 直接实现 4 纯函数 + BM25 启动期全量重建；与 L3-4/L3-5 同模式）
- **L3-6 与 L3-5 共享 Deployment**：同 Pod 内两个独立 Python 进程（memory-backend port 8081 仅 kubelet probe + knowledge-service port 8080/8443 对外）；共享 Helm chart / Service / ServiceMonitor / NetworkPolicy；进程间遵循 §6 逻辑 function-reference Protocol，跨 container transport 待 L4 UDS/共享 runtime spike，禁止 HTTP loopback（**与 L3-5 §6.2 严格一致 · line 1488-1577 协调点**）
- **L3-6 独占 MemoryReconciler 60s 周期 + Leader Election + 4 纯函数 + Clock Protocol + BM25 启动期全量重建**：L3-5 不实现这 6 项，对应 L3-5 §6.1 协调点表格行 1445-1456

---

## 1. 模块使命与文件清单总览

### 1.1 模块使命（C-7 Memory backend · Card-driven 单实例 · 同 Pod 第二 Python 进程）

- **不是** Sidecar 模式 — 是与 L3-5 同 Pod 的**独立 Deployment 内第二个独立 Python 进程**（v0.1 单实例 / 单 Python 进程 / 单 Uvicorn worker / port 8081 cluster-internal）
- **Card**：`superteam-a2a.memory-backend` v0.1.0（**0 A2A method 暴露** · 内部 service · 4 纯函数 export via in-process function reference · L3-5 §4.3 / §4.4 recordMemory/queryMemory 委托调用）
- **Capabilities**：streaming=false / pushNotifications=false（v0.1 简化）
- **认证**：mTLS（cert-manager 颁发，Python `ssl.SSLContext`，与 L3-5 共享 TLS Secret `knowledge-service-tls`）
- **依赖 CRD**：Memory schema 12 字段完整版（通过 `kubernetes_asyncio` 异步客户端；L3-5 §3.3 简化 5+5 + L3-6 §3 完整 12 字段 wire 完全一致）
- **承担职责**：
  - MemoryReconciler 60s 周期（`@kopf.timer(interval=60.0, id="memory-reconciler")`）+ Leader Election Lease（`coordination.k8s.io/v1` Lease 30s grace period + renew 失败 3 次让位）
  - 4 纯函数 export（apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion + Clock Protocol + RealClock + FakeClock）
  - BM25 倒排索引启动期全量重建 + watch 增量（共享 L3-5 内存 dict · L3-6 §6.3 详细落地）
  - recordMemory / queryMemory 业务实现（供 L3-5 in-process call 委托 · K8s API apply/list + decay 计算 + 5 维 visibility 过滤）
  - GC 状态机（NONE → PENDING → CLEANED/KEPT）+ promotion 判定（v0.1 仅计算 `eligible_for_promotion` 不触发 · v0.5+ 触发 · OPEN-L2-4-007 推迟）
  - **MemoryBackend 抽象层定义**（L2-4 v0.2.0 未定义后端切换接口 · L3-6 核心新增点 · §5.7 详细落地）
- **不实现**：
  - 不实现 4 A2A method 暴露（L3-5 独占 · L3-6 仅实现业务 handler 供 in-process call）
  - 不实现 admission webhook 双向互斥（L3-5 独占 `@kopf.validation` · L3-6 §5 admission 互斥算法在 #65 补完）
  - 不实现业务 Agent 逻辑（仅 Card-driven 内部 service 暴露）
  - 不实现 Knowledge 业务（L3-5 独占）
  - 不实现 Adapter SDK（与 L3-4/L3-5 同模式 · 直接实现 4 纯函数）

### 1.2 5 项关键不变量（任何修改必须走 ADR）

1. **同 Pod 第二进程**：Memory backend v0.1 严格单实例，与 L3-5 同 Pod 部署（`replicaCount: 1`）；水平扩展需走 v0.5+ 决策（OPEN-MEMORY-001 · L2-4 v0.2.0 §15.5 继承）
2. **60s @kopf.timer 周期不变**：`interval=60.0` `id="memory-reconciler"` 永久不变（与 L2-4 Spec v0.2.0 §6.6 + L3-1 §3.4 协调点 + ADR-0003 §6 严格一致）
3. **L3-6 ↔ L3-5 共享 Deployment**：严格同 Pod 部署（共享 Helm chart / Service / ServiceMonitor / NetworkPolicy；进程间通过 Python in-process function reference — 详见 §6 · **与 L3-5 §6.2 line 1488-1577 严格一致**）
4. **4 纯函数数学永久不变**：`apply_decay` / `apply_reinforce` / `gc_expired` / `is_eligible_for_promotion` 函数签名与公式与 L2-4 v0.2.0 Spec §7.3 逐字符一致；衰减公式 `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` 永久不变
5. **wire contract 完全继承 L2-4 v0.2.0 Spec**：Memory CRD 12 spec 字段 wire 名 / 12 MEMORY_* 错误码 wire 名（**直接采用 L2-4 v0.2.0 §9.1 权威名，零漂移 · 避免 L3-5 #63.5.1 23 处漂移历史**）/ 4 级 scope 名 / 5 维 visibility name 永久不变

### 1.3 5 项 Python 化关键决策（D-1 ~ D-5 · 继承 L2-4 Design v0.2.0 §1）

| 编号 | 决策 | Go baseline | v0.2 Python | 落地位置 |
|------|------|-------------|-------------|----------|
| **D-1** | Memory CRD types | Go struct + `+kubebuilder:validation:` | **Pydantic v2 BaseModel + Field(...) + populate_by_name + alias（12 spec 字段完整版 · 与 L3-5 §3.3 5+5 简化版 wire 一致）** | §3.1 MemoryPhase + §3.2 MemorySpec + §3.3 MemoryStatus + §3.4 Memory |
| **D-2** | MemoryReconciler 60s 周期 | controller-runtime `Reconcile()` | **`@kopf.timer(interval=60.0, id="memory-reconciler")` + 独立 async reconciler service + Leader Election via coordination.k8s.io/v1 Lease（30s grace + renew 失败 3 次让位）** | §4.1 60s timer + §4.2 Leader Election + §4.3 退避策略 |
| **D-3** | Clock 时间穿越 | Go interface + k8s.io/utils/clock | **`Clock` Protocol + `RealClock` + `FakeClock`（测试用 freezegun 替代）** | §5.1 Clock Protocol + §5.2 FakeClock 单元测试 |
| **D-4** | 4 纯函数 | Go sync.Mutex 保护纯函数 | **Python 同步 pure function + async wrapper（lru_cache 缓存 + 不阻塞 event loop）+ 公式逐字符对齐 L2-4 §7.3** | §5.3 apply_decay + §5.4 apply_reinforce + §5.5 gc_expired + §5.6 is_eligible_for_promotion + §5.7 MemoryBackend 抽象层 |
| **D-5** | BM25 启动期重建 | sync.Map + startup hook | **`anyio.to_thread.run_sync` 启动期全量重建 + K8s watch 增量 + 共享 in-memory dict（与 L3-5 §4.2 bm25_index.search 共享存储）** | §6.3 BM25 rebuild 策略 |

### 1.4 文件清单总览（28 文件级契约 + 7 Helm 模板 + 1 Dockerfile + 1 CRD 示例 + 28 测试文件镜像）

| 类别 | 数量 | 路径前缀 | 备注 |
|------|------|----------|------|
| **CRD types（packages/memory/）** | 6 | `packages/memory/src/supteam_a2a/memory/apis/v1alpha1/` | Pydantic v2 + JSON Schema + 12 字段完整版 |
| **A2A/Business 部署（services/memory-backend/）** | 14 | `services/memory-backend/src/supteam_a2a/memory_backend/` | ASGI + 4 纯函数 + 60s timer + Leader + Clock + BM25 rebuild + 4 handler |
| **shared 公共（packages/shared-memory/）** | 4 | `packages/shared-memory/src/supteam_a2a/shared/memory/` | MemoryBackend 抽象层 + 5 维矩阵 + 4 级 scope 复用 + MemoryStore Protocol（与 L3-5 共享） |
| **测试文件镜像** | 28 | `tests/{unit,integration,e2e,contract,fuzz,perf}/memory*/` | 6 层级金字塔 |
| **Helm 模板** | 0（复用 L3-5 chart） | `helm/knowledge-service/templates/`（共享 deployment + memory-backend container） | 与 L3-5 共享 Helm chart |
| **Dockerfile** | 1 | `services/memory-backend/Dockerfile` | python:3.12-slim 多阶段 + uv build（与 L3-5 镜像） |
| **CRD 示例** | 1 | `examples/memory/memory.yaml` | L1 Spec §5.2.3 同步 |
| **总计** | **54** | — | 28 文件级契约 + 28 测试镜像 + 7 Helm + 1 Dockerfile + 1 CRD |

### 1.5 上游依赖关系图

```
┌─────────────────────────────────────────────────────────────────┐
│              L3-6 Memory backend v0.2 Python                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────┐                   │
│  │  packages/memory/ (CRD types)            │  ← Pydantic v2   │
│  │  - memory.py (MemorySpec 12 字段完整版)  │                   │
│  │  - memory_phase.py (5 态状态机)         │                   │
│  │  - memory_visibility.py (3 枚举)        │                   │
│  │  - gc_state.py (4 态状态机)             │                   │
│  │  - agent_reference.py (SA 引用)         │                   │
│  │  - source_knowledge_ref.py (KI 引用)    │                   │
│  └──────────────────────────────────────────┘                   │
│                     ↑                                           │
│  ┌──────────────────┴───────────────────────┐                   │
│  │  services/memory-backend/                │  ← ASGI + 4 纯函数│
│  │  - agent.py (AGENT, 50 行)              │                   │
│  │  - card.py (CARD, 40 行)                │                   │
│  │  - observability.py (OBS, 80 行)        │                   │
│  │  - _internals.py (INT, 60 行)           │                   │
│  │  - handlers/ (4 method, 30 行/个)       │                   │
│  │  - memory_reconciler.py (60s kopf.timer)│                   │
│  │  - leader_election.py (Lease 客户端)    │                   │
│  │  - clock.py (Protocol + Real + Fake)    │                   │
│  │  - pure_functions/ (4 纯函数 50 行/个) │                   │
│  │  - memory_backend/ (MemoryBackend 抽象) │                   │
│  └──────────────────────────────────────────┘                   │
│            ↑                                                     │
│            │  import（CRD types 复用）                          │
│            │                                                     │
│  ┌─────────┴──────────────────────────────────┐                 │
│  │  packages/shared-memory/ (与 L3-5 共享)   │  ← typing.Protocol│
│  │  - memory_backend.py (MemoryBackend 抽象) │                 │
│  │  - memory_store.py (RealMemoryStore)     │                 │
│  │  - decay_formula.py (衰减公式共享)        │                 │
│  │  - visibility_filter.py (5 维矩阵复用)   │                 │
│  └───────────────────────────────────────────┘                 │
│                                                                 │
│  外部依赖（仅 import 边界）：                                    │
│  - L3-5 knowledge-service: in-process function reference        │
│  - L3-2 a2a-core: ASGI server + A2AClient + 15 指标 + 24 错误码  │
│  - L3-1 operator: CRD wire sync + Helm 9 模板 + RBAC 基础       │
│  - a2a-sdk 官方: AgentExecutor + DefaultRequestHandler           │
│  - kopf: @kopf.timer + @kopf.validation 装饰器                  │
│  - kubernetes_asyncio: CRD 读写（Memory）                       │
│  - prometheus-client: 10 Memory 业务指标 + 复用 15 L3-2 指标     │
│  - structlog: 8 必含字段                                         │
│  - freezegun: FakeClock 时间穿越测试                             │
│  - cert-manager: mTLS TLSConfig + HotReloader                   │
│                                                                 │
│  Helm 部署（与 L3-5 共享 chart）：                              │
│  - 共享 deployment.yaml (双 container · memory-backend port 8081)│
│  - 共享 service.yaml (80/443 → 8080；8081 不进 Service)          │
│  - 共享 serviceaccount.yaml (cert-manager annotation)            │
│  - 拆 rbac/role.yaml: L3-5 read-only + L3-6 write (L3-5-followup-1)│
│  - 共享 networkpolicy.yaml (ingress/egress 限制)                │
│  - 共享 prometheusrule.yaml (6 告警规则 · 加 Memory 告警)        │
│  - 共享 servicemonitor.yaml (15 + 10 指标 scrape)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Python 包结构

> **说明**：本节给出 L3-6 完整 Python 包结构（与 L3-5 §2 同模式）；§2.3-§2.6 详细子包在 #65 Subagent 1 补完。

### 2.1 uv workspace 布局（ADR-0005 §13.1）

```
superteam-a2a/
├── packages/
│   ├── memory/                                    # CRD types（与 L3-5 共享 5 维矩阵 + 4 级 scope）
│   │   ├── pyproject.toml
│   │   └── src/supteam_a2a/memory/
│   │       ├── __init__.py
│   │       └── apis/
│   │           └── v1alpha1/
│   │               ├── __init__.py
│   │               ├── memory.py                   # MEM-CRD · Pydantic v2 BaseModel（12 spec 字段完整版）
│   │               ├── memory_phase.py             # MemoryPhase · 5 态状态机（Active/Decaying/Promotable/Expired/Error）
│   │               ├── memory_visibility.py        # MemoryVisibility · 3 枚举（scope-only/scope-and-children/agent-private）
│   │               ├── gc_state.py                 # GCState · 4 态（None/Pending/Cleaned/Kept）
│   │               ├── agent_reference.py          # AgentReference · ServiceAccount 引用（frozen）
│   │               └── source_knowledge_ref.py     # SourceKnowledgeRef · KnowledgeItem 引用（frozen）
│   ├── shared-memory/                              # MemoryBackend 抽象层 + 5 维矩阵 + 4 级 scope（与 L3-5 共享）
│   │   ├── pyproject.toml
│   │   └── src/supteam_a2a/shared/memory/
│   │       ├── __init__.py
│   │       ├── memory_backend.py                   # SMB-BACKEND · MemoryBackend Protocol + 切换接口
│   │       ├── memory_store.py                     # SMB-STORE · RealMemoryStore（CRD 即存储）
│   │       ├── decay_formula.py                    # SMB-DECAY · effectiveConfidence = c × exp(-d/dd) 公式
│   │       └── visibility_filter.py                # SMB-VIS · 5 维 visibility 过滤（与 L3-5 共享 SV-VIS）
│   └── ...
├── services/
│   └── memory-backend/                             # A2A/Business 部署（与 knowledge-service 共享 Deployment）
│       ├── pyproject.toml
│       ├── Dockerfile
│       ├── helm/                                   # 与 knowledge-service 共享 helm/ 目录
│       │   └── templates/                          # （仅 1 份共享 chart）
│       │       ├── _helpers.tpl
│       │       ├── deployment.yaml                 # 双 container · knowledge-service:8080 + memory-backend:8081
│       │       ├── service.yaml                    # 80/443 → 8080；8081 不进 Service
│       │       ├── serviceaccount.yaml             # cert-manager annotation
│       │       ├── rbac/
│       │       │   ├── role_readonly.yaml          # L3-5 read-only Role（knowledgescopes/knowledgeitems/memories read）
│       │       │   ├── role_write.yaml             # L3-6 write Role（memories write + patch status · L3-5-followup-1）
│       │       │   └── rolebinding.yaml            # 共享 SA `knowledge-service` 绑定两 Role
│       │       ├── networkpolicy.yaml              # ingress/egress 限制
│       │       ├── prometheusrule.yaml             # 6 告警（Knowledge × 4 + Memory × 2）
│       │       └── servicemonitor.yaml             # 15+10 指标 scrape（仅 port 8080）
│       └── src/supteam_a2a/memory_backend/
│           ├── __init__.py                         # public API: app, executor, card, in-process services
│           ├── agent.py                            # AGENT · MemoryBackendExecutor (50 行)
│           ├── card.py                             # CARD · build_memory_backend_card (40 行)
│           ├── observability.py                    # OBS · 10 指标 + bind_request_logger (80 行)
│           ├── _internals.py                       # INT · test fixture + helper (60 行)
│           ├── handlers/
│           │   ├── __init__.py
│           │   ├── record_memory.py                # H-RM · a2a.recordMemory handler (in-process 业务, 30 行)
│           │   ├── query_memory.py                 # H-QM · a2a.queryMemory handler (in-process 业务, 30 行)
│           │   ├── decay_handler.py                # H-DECAY · 60s kopf.timer 触发入口 (30 行)
│           │   └── promote_handler.py              # H-PROMOTE · promotion 判定入口 (30 行 · v0.1 仅算不触发)
│           ├── memory_reconciler.py                # REC · 60s @kopf.timer + 全流程 reconcile (80 行)
│           ├── leader_election.py                  # LE · coordination.k8s.io/v1 Lease 客户端 (50 行)
│           ├── clock.py                            # CLK · Clock Protocol + RealClock + FakeClock (40 行)
│           ├── pure_functions/
│           │   ├── __init__.py
│           │   ├── apply_decay.py                  # PF-DECAY · 衰减公式（exp） (50 行)
│           │   ├── apply_reinforce.py              # PF-REIN · 强化 + 1h 频次节流 (50 行)
│           │   ├── gc_expired.py                   # PF-GC · 过期清理 (50 行)
│           │   ├── is_eligible_for_promotion.py    # PF-PROM · promotion 判定 4 条件 (50 行)
│           │   └── memory_backend.py               # PF-BACKEND · MemoryBackend Protocol + InMemoryBackend (50 行 · 核心新增点)
│           ├── memory_backend/                     # MemoryBackend 抽象层实现（与 packages/shared-memory 配套）
│           │   ├── __init__.py
│           │   ├── in_memory.py                    # MB-IM · InMemoryBackend（默认 · CRD 即存储）
│           │   └── crd_store.py                    # MB-CRD · CRDStore（K8s API 适配器）
│           ├── bm25_index.py                       # BM25 · 启动期全量重建 + watch 增量 (60 行)
│           ├── admission_validator.py              # ADM · Memory admission 7 校验规则 (50 行)
│           ├── events.py                           # EVT · K8s Events emit (40 行 · 复用 L3-5 模式)
│           ├── errors.py                           # ERR · 12 MEMORY_* IntEnum (40 行 · 引用 L2-4 §9.1 权威名)
│           ├── metrics_server.py                   # MET · Prometheus /metrics endpoint (30 行)
│           └── middleware/
│               ├── __init__.py
│               └── ratelimit.py                    # ML-RL · 60/min per SA 滑窗限流 (40 行)
```

### 2.2 6 项边界规则（继承 L3-5 §2.2 + L3-1 §2.3 + 新增 1 项）

1. **单进程原则**（ADR-0005 §6.2）：单 Pod / 单 Python 进程 / 单 Uvicorn worker（与 L3-5 同 Pod 部署但独立 container）
2. **Card-driven 边界**（与 L3-4/L3-5 同模式）：不实现业务 Agent 逻辑；仅暴露 0 A2A method + 4 纯函数 in-process export
3. **依赖方向**：L3-6 → L3-2（a2a-core 复用 ASGI/Client/错误码）+ L3-1（CRD wire sync）+ L3-5（in-process 协议） + ADR-0003/0005 + Constitution v0.5.0；**不依赖 L3-3 Adapter SDK**
4. **包路径命名**：`packages/memory/` （CRD types · 区别于 L3-5 的 `packages/knowledge/`）+ `packages/shared-memory/` （与 L3-5 `packages/shared-visibility/` 对称）
5. **错误码权威源**：12 个 MEMORY_* 错误码**直接 import L2-4 v0.2.0 §9.1 权威名**（**禁止重新定义或漂移** · 避免 L3-5 #63.5.1 23 处漂移历史）
6. **in-process 异常透传**（L3-5 §6.2 line 1547-1550 3 项规则）：L3-6 抛出的 `A2AError` / `AdmissionTimeoutError` 等异常直接传播到 L3-5；L3-5 不 catch 并改 error code

### 2.3 依赖方向（继承 L3-5 §2.3 · 镜像）

L3-6 → L3-2（a2a-core）+ L3-1（operator-core）+ L3-5（in-process）+ ADR-0003/0005 + Constitution v0.5.0
L3-6 ⇍ L3-3（Adapter SDK · **不依赖**）
L3-6 ⇍ L3-4（Hello Agent · 同模式 Card-driven 单实例参考实现 · 仅参考）

### 2.4 镜像规则（与 L3-5 §2.4 同模式）

每个 production `src/.../*.py` 有同职责 `tests/.../test_*.py`（6 层级金字塔镜像）。

### 2.5 共享模式（与 L3-5 §2.5 同模式）

- L3-6 复用 L3-5 共享 `packages/shared-visibility/` 的 5 维矩阵 + 4 级 scope 解析（**不重复实现**）
- L3-6 新增 `packages/shared-memory/` 提供 `MemoryBackend` Protocol 抽象层（**L3-6 核心新增点**）
- L3-6 复用 L3-5 共享 `packages/shared-errors/` 的 24 个错误码 enum（**12 MEMORY_* 直接采用 L2-4 §9.1 权威名**）

### 2.6 工具链（继承 L3-5 §2.6 · 镜像）

```bash
uv sync --frozen
ruff format --check . && ruff check .
pyright --level error
bandit -r packages services && pip-audit
interrogate -f 100 packages services
lint-imports
pytest --cov=supteam_a2a.memory_backend --cov-fail-under=80
helm lint helm/knowledge-service && helm template knowledge-service helm/knowledge-service
```

**ST-MEMORY-BOUNDARY**（与 L3-5 §2.6 ST-KNOWLEDGE-BOUNDARY 对称）：L3-6 只依赖共享 Pydantic types、A2A public Protocol、K8s async client、kopf；禁止 Adapter SDK、业务 Agent、L3-5 私有实现、SDK private path。

---

## 3. Memory CRD（Pydantic v2 12 spec 字段完整版 · wire contract 与 L2-4 v0.2.0 §3.4 完全一致）

> **权威边界**：L2-4 v0.2.0 §3.4 定义的 Memory wire 为 12 个业务字段（`scopeRef` 等）；本节同时定义后端绑定投影 `BackendBindingSpec`，用于承载 `size/backendType/ttl/...`。绑定投影不是第二套 CRD wire，必须由 adapter 从 12 字段模型派生，禁止替换或重命名上游字段。

### 3.1 5 项 wire contract 永久不变

1. 所有时间为 `AwareDatetime` 且必须 UTC；naive datetime 拒绝。
2. enum 使用 `StrEnum`；序列化值与 Kubernetes JSON 字符串逐字符一致。
3. 引用与 metadata value object 使用 `frozen=True`；输入对象不得被后端原地修改。
4. Python snake_case 仅通过 `populate_by_name=True` + `alias` 映射到 camelCase wire。
5. 全模型 `extra="forbid"`；未知字段由 admission/schema 双层拒绝。

### 3.2 公共类型、metadata 与枚举

```python
from __future__ import annotations
import re
from enum import StrEnum
from typing import Annotated, Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

DNS_LABEL = re.compile(r"^[a-z0-9](?:[-a-z0-9]*[a-z0-9])?$")
LABEL_KEY = re.compile(r"^(?:[a-z0-9]([-a-z0-9_.]*[a-z0-9])?/)?[A-Za-z0-9]([-A-Za-z0-9_.]*[A-Za-z0-9])?$")
LABEL_VALUE = re.compile(r"^$|^[A-Za-z0-9]([-A-Za-z0-9_.]*[A-Za-z0-9])?$")
DnsLabel = Annotated[str, StringConstraints(min_length=1, max_length=63)]

class BackendType(StrEnum):
    DICT = "dict"
    IN_MEMORY = "in-memory"
    REDIS = "redis"

class MemoryScope(StrEnum):
    SESSION = "session"
    USER = "user"
    TENANT = "tenant"

class EvictionPolicy(StrEnum):
    FIFO = "FIFO"
    LRU = "LRU"

class BindingPhase(StrEnum):
    PENDING = "Pending"
    BOUND = "Bound"
    RELEASING = "Releasing"
    RELEASED = "Released"
    ERROR = "Error"

class MemoryPhase(StrEnum):
    ACTIVE = "Active"
    DECAYING = "Decaying"
    PROMOTABLE = "Promotable"
    EXPIRED = "Expired"
    ERROR = "Error"

class MemoryVisibility(StrEnum):
    SCOPE_ONLY = "scope-only"
    SCOPE_AND_CHILDREN = "scope-and-children"
    AGENT_PRIVATE = "agent-private"

class ObjectMeta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    name: DnsLabel
    namespace: DnsLabel = "default"
    labels: dict[str, str] = Field(default_factory=dict, max_length=64)
    annotations: dict[str, str] = Field(default_factory=dict, max_length=64)
    generation: int = Field(default=1, ge=1)
    creation_timestamp: AwareDatetime | None = Field(default=None, alias="creationTimestamp")
    finalizers: tuple[str, ...] = ()

    @field_validator("name", "namespace")
    @classmethod
    def valid_dns_label(cls, value: str) -> str:
        if not DNS_LABEL.fullmatch(value):
            raise ValueError("must be a lowercase DNS-1123 label")
        return value

    @field_validator("labels")
    @classmethod
    def valid_labels(cls, value: dict[str, str]) -> dict[str, str]:
        if any(len(k) > 253 or not LABEL_KEY.fullmatch(k) for k in value):
            raise ValueError("invalid Kubernetes label key")
        if any(len(v) > 63 or not LABEL_VALUE.fullmatch(v) for v in value.values()):
            raise ValueError("invalid Kubernetes label value")
        return value
```

### 3.3 12 字段 MemorySpec 与后端绑定投影

```python
class ScopeReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(min_length=1, max_length=128)
    level: Literal["industry", "organization", "team", "project"] | None = None

class AgentReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["ServiceAccount"] = "ServiceAccount"
    name: str = Field(min_length=1, max_length=253)

class ItemReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(min_length=1, max_length=253)
    namespace: DnsLabel | None = None

class MemorySpec(BaseModel):
    """L2-4 §3.4 的 12 字段 source-of-truth。"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scope_ref: ScopeReference = Field(alias="scopeRef")
    agent_ref: AgentReference = Field(alias="agentRef")
    content: dict[str, str] = Field(min_length=1, max_length=20)
    summary: str = Field(min_length=1, max_length=512)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    decay_days: int = Field(default=30, alias="decayDays", ge=1, le=3650)
    reinforced_count: int = Field(default=0, alias="reinforcedCount", ge=0)
    last_reinforced_at: AwareDatetime | None = Field(default=None, alias="lastReinforcedAt")
    memory_key_pattern: str | None = Field(default=None, alias="memoryKeyPattern", max_length=128)
    source_knowledge_ref: ItemReference | None = Field(default=None, alias="sourceKnowledgeRef")
    tags: list[str] | None = Field(default=None, max_length=10)
    visibility: MemoryVisibility = MemoryVisibility.SCOPE_AND_CHILDREN

    @field_validator("content")
    @classmethod
    def content_keys_and_values(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not k or len(k) > 128 for k in value):
            raise ValueError("content keys must contain 1..128 characters")
        if any(len(v.encode("utf-8")) > 4096 for v in value.values()):
            raise ValueError("each content value must be <= 4096 UTF-8 bytes")
        return value

    @field_validator("tags")
    @classmethod
    def unique_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and (any(not t or len(t) > 64 for t in value) or len(value) != len(set(value))):
            raise ValueError("tags must be unique non-empty values <= 64 chars")
        return value

    @model_validator(mode="after")
    def agent_private_has_name(self) -> "MemorySpec":
        if self.visibility is MemoryVisibility.AGENT_PRIVATE and not self.agent_ref.name:
            raise ValueError("MEMORY_AGENT_PRIVATE_REQUIRES_NAME")
        return self

class EncryptionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    enabled: bool = False
    key_rotation: str | None = Field(default=None, alias="keyRotation", pattern=r"^(?:[1-9][0-9]*)(?:h|d)$")

    @model_validator(mode="after")
    def rotation_requires_encryption(self) -> "EncryptionSpec":
        if not self.enabled and self.key_rotation is not None:
            raise ValueError("keyRotation requires encryption.enabled=true")
        return self

class BackendBindingSpec(BaseModel):
    """由 MemorySpec/Helm policy 派生的 8 字段后端绑定投影，不改变 CRD source wire。"""
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    size: int = Field(default=1024, ge=1, le=1_048_576)
    backend_type: BackendType = Field(default=BackendType.DICT, alias="backendType")
    ttl: int | None = Field(default=None, ge=1, le=31_536_000)
    scope: MemoryScope = MemoryScope.SESSION
    namespace_prefix: str = Field(default="memory", alias="namespacePrefix", min_length=1, max_length=48, pattern=r"^[a-z0-9](?:[-a-z0-9]*[a-z0-9])?$")
    policy: EvictionPolicy = EvictionPolicy.LRU
    encryption: EncryptionSpec = Field(default_factory=EncryptionSpec)
    key_rotation: str | None = Field(default=None, alias="keyRotation", pattern=r"^(?:[1-9][0-9]*)(?:h|d)$")

    @model_validator(mode="after")
    def backend_constraints(self) -> "BackendBindingSpec":
        if self.backend_type is BackendType.IN_MEMORY and self.size > 65_536:
            raise ValueError("in-memory size must be <= 65536 entries")
        if self.backend_type is BackendType.REDIS and self.namespace_prefix == "default":
            raise ValueError("redis requires a non-default namespacePrefix")
        if not self.encryption.enabled and self.key_rotation is not None:
            raise ValueError("keyRotation requires encryption.enabled=true")
        return self
```

`size` 表示最大 entry 数；`ttl` 单位秒，`None` 表示使用 `decayDays` 生命周期；`scope` 仅控制后端 key 隔离，不替代 Knowledge 的 4 级 `scopeRef.level`；`namespacePrefix` 组成 `<prefix>:<namespace>:<scope>:<name>`。

### 3.4 状态 schema、状态转换与错误码 wire

```python
class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    type: str = Field(min_length=1, max_length=64)
    status: Literal["True", "False", "Unknown"]
    reason: str = Field(min_length=1, max_length=128)
    message: str | None = Field(default=None, max_length=1024)
    last_transition_time: AwareDatetime = Field(alias="lastTransitionTime")
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)

class MemoryStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    phase: MemoryPhase | None = None
    message: str | None = Field(default=None, max_length=512)
    conditions: list[Condition] = Field(default_factory=list, max_length=16)
    last_decayed_at: AwareDatetime | None = Field(default=None, alias="lastDecayedAt")
    last_reinforced_at: AwareDatetime | None = Field(default=None, alias="lastReinforcedAt")
    effective_confidence: float | None = Field(default=None, alias="effectiveConfidence", ge=0.0, le=1.0)
    eligible_for_promotion: bool | None = Field(default=None, alias="eligibleForPromotion")
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)

class BackendBindingStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    phase: BindingPhase = BindingPhase.PENDING
    backend_ref: str | None = Field(default=None, alias="backendRef", max_length=253)
    size_in_use: int = Field(default=0, alias="sizeInUse", ge=0)
    last_reconcile_time: AwareDatetime | None = Field(default=None, alias="lastReconcileTime")
    conditions: list[Condition] = Field(default_factory=list, max_length=16)

class Memory(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    api_version: Literal["memory.superteam-a2a.io/v1alpha1"] = Field(default="memory.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: Literal["Memory"] = "Memory"
    metadata: ObjectMeta
    spec: MemorySpec
    status: MemoryStatus | None = None
```

| 场景 | 唯一权威名 | code | 实现保证 |
|---|---|---:|---|
| scope 不存在 | `MEMORY_SCOPE_NOT_FOUND` | -32101 | bind 前解析 scope，失败不创建 backendRef |
| content 超限 | `MEMORY_INVALID_CONTENT` | -32102 | Pydantic + admission 双重限制 1..20 keys |
| backend/K8s 未知异常 | `MEMORY_INTERNAL_ERROR` | -32105 | 仅边界 adapter 转换；保留 cause |
| decayDays 超限 | `MEMORY_DECAY_DAYS_EXCEEDED` | -32110 | `le=3650` 且 admission 显式映射 |
| admission 超时 | `MEMORY_ADMISSION_TIMEOUT` | -32112 | 50ms fail-closed，不降级为允许 |

`MEMORY_*` 名称必须从共享 `MemoryErrorCode` import；§3-§6 不声明第二份 enum。其余权威名仅可为 `MEMORY_FORBIDDEN`、`MEMORY_RATE_LIMIT`、`MEMORY_QUERY_TOO_BROAD`、`MEMORY_SOURCE_KI_NOT_FOUND`、`MEMORY_SOURCE_KI_SCOPE_MISMATCH`、`MEMORY_AGENT_PRIVATE_REQUIRES_NAME`、`MEMORY_AGENT_NOT_FOUND`。

### 3.5 边界规则、同步矩阵与 15 个测试 ID

- namespace 必须是 DNS-1123 label；业务 namespace 不得为 `kube-system`、`kube-public`、`kube-node-lease` 或 `superteam-a2a-system`。
- `size <= 1_048_576`；`in-memory <= 65_536`；quota 触发映射 `MEMORY_FORBIDDEN`，禁止引入独立的 quota 错误码。
- labels 最多 64 个，key/value 遵循 Kubernetes label grammar；annotations 最多 64 个且单值 <= 16KiB。
- `v1alpha1` 是唯一 served/storage 版本；未知 apiVersion 拒绝；未来 conversion webhook 必须保持 12 字段 round-trip。
- `status`、`backendRef`、`sizeInUse` 均由 reconciler 所有；用户 spec apply 不得覆盖。

| 测试 ID | 描述 |
|---|---|
| `TEST-MEM-001` | 12 个 MemorySpec 字段 camelCase round-trip 无漂移 |
| `TEST-MEM-002` | apiVersion/kind 默认值与 Literal 严格拒绝 |
| `TEST-MEM-003` | metadata name/namespace DNS-1123 边界 |
| `TEST-MEM-004` | labels key/value 与 64 项上限 |
| `TEST-MEM-005` | content 1..20 keys、value 4096 bytes |
| `TEST-MEM-006` | confidence 0/1 与越界拒绝 |
| `TEST-MEM-007` | decayDays 1/3650 与权威错误码映射 |
| `TEST-MEM-008` | tags 唯一性和 10 项上限 |
| `TEST-MEM-009` | agent-private 必须具备 ServiceAccount name |
| `TEST-MEM-010` | BackendBindingSpec dict/in-memory/redis 枚举 |
| `TEST-MEM-011` | size 总上限与 in-memory 子上限 |
| `TEST-MEM-012` | encryption/keyRotation 依赖规则 |
| `TEST-MEM-013` | Pending/Bound/Releasing/Released/Error status round-trip |
| `TEST-MEM-014` | status AwareDatetime 拒绝 naive datetime |
| `TEST-MEM-015` | v1alpha1 YAML/Pydantic/server-side dry-run 三方一致 |

---

## 4. MemoryReconciler 60s 周期 + Leader Election（Kopf timer + finalize）

### 4.1 固定 60s timer 与单 leader 入口

```python
import kopf

@kopf.timer(
    "memory.superteam-a2a.io", "v1alpha1", "memories",
    interval=60.0, id="memory-reconciler",
)
async def memory_reconciler_timer(*, memo: kopf.Memo, **_: object) -> None:
    service: MemoryReconcilerService = memo["memory_reconciler"]
    if not await service.leader.try_acquire_or_renew():
        return
    await service.reconcile_all(now=service.clock.now())
```

- `interval=60.0`、`id="memory-reconciler"` 为不变量；Helm 不得覆盖。
- Lease 为 `memory-reconciler-leader` / namespace `superteam-a2a-system`；duration 15s、renew deadline 10s、retry 5s。
- 连续 3 次 renew 失败立即丢弃本地 leadership；30s grace 内仅允许重获，不允许写 status。
- timer 不启动并发第二轮；上一轮未完成时跳过并记录 `result="overlap_skipped"`。

### 4.2 状态转换图与状态所有权

```text
                         validation/backend failure
                         ┌──────────────────────┐
                         v                      │ retryable next tick
[create] -> Pending -> Bound ----------------> Error
              |          |
              | delete   | delete/finalizer
              v          v
          Releasing -> Released
              | cleanup failure
              └------------------------------> Error
```

允许边：`Pending→Bound|Error|Releasing`、`Bound→Bound|Releasing|Error`、`Releasing→Released|Error`、`Error→Pending|Bound|Releasing|Error`。`Released` 为终态，仅 finalize 结束时写入；业务 `MemoryPhase` Active/Decaying/Promotable/Expired/Error 与绑定 phase 分层，禁止混用。

### 4.3 reconcile 算法、回滚与错误隔离

```python
class MemoryReconcilerService:
    async def reconcile_all(self, *, now: AwareDatetime) -> ReconcileSummary:
        if not await self.leader.is_leader():
            return ReconcileSummary()
        async with self._non_overlap_lock:
            memories = await self.backend.list_all(namespace="*")
            summary = ReconcileSummary()
            for raw in memories:
                try:
                    memory = Memory.model_validate(raw)
                    await self.admission.validate(memory, timeout=0.050)
                    binding = derive_binding(memory)
                    token = await self.backend.prepare(binding)
                    try:
                        await self.backend.bind(token, memory)
                        status = calculate_status(memory, self.clock)
                        await self.backend.patch_status(
                            memory.metadata.namespace, memory.metadata.name,
                            status, expected_generation=memory.metadata.generation,
                        )
                        await self.backend.commit(token)
                        summary.bound += 1
                    except BaseException:
                        await self.backend.rollback(token)
                        raise
                except AdmissionTimeoutError as exc:
                    await self._mark_error(raw, "MEMORY_ADMISSION_TIMEOUT", exc, now)
                    summary.errors += 1
                except BackendUnavailable as exc:
                    await self._mark_error(raw, "MEMORY_INTERNAL_ERROR", exc, now)
                    summary.errors += 1
                except Exception as exc:
                    await self._mark_error(raw, canonical_memory_code(exc), exc, now)
                    summary.errors += 1
            return summary
```

K8s 5xx 1/2/4/8s 最多 4 次；429 尊重 `Retry-After`；4xx 不重试；admission timeout 100/200/400ms 最多 3 次；leadership 在任何 await 后丢失均中止 commit。status patch 带 generation CAS，冲突重新读取，绝不覆盖新 spec。

### 4.4 finalize hook 五步资源清理

```python
MEMORY_FINALIZER = "memory.superteam-a2a.io/cleanup"

@kopf.on.delete("memory.superteam-a2a.io", "v1alpha1", "memories", id="memory-finalize")
async def finalize_memory(*, body: dict, memo: kopf.Memo, **_: object) -> None:
    await memo["memory_reconciler"].finalize(Memory.model_validate(body))

async def finalize(self, memory: Memory) -> None:
    await self.backend.mark_releasing(memory)                 # 1. phase=Releasing
    await self.backend.quiesce(memory.metadata.namespace, memory.metadata.name) # 2. drain <=5s
    await self.backend.release(memory)                        # 3. 幂等删除 data/TTL/Redis namespace
    await self.index.remove(memory.metadata.namespace, memory.metadata.name)    # 4. BM25/cache + Released
    await self.backend.remove_finalizer(memory, MEMORY_FINALIZER)               # 5. 成功才移除
```

cleanup 失败保留 finalizer 供 Kopf 重试；release 与 index.remove 必须幂等。

**§4 测试 ID（15）**：

| ID | 描述 |
|---|---|
| `TEST-MEM-016` | timer interval=60.0 且 id 固定 |
| `TEST-MEM-017` | 非 leader 无 list/patch 调用 |
| `TEST-MEM-018` | renew 连续 3 次失败让位 |
| `TEST-MEM-019` | 30s grace 内禁止 status 写入 |
| `TEST-MEM-020` | 重叠 timer 跳过而非并发 |
| `TEST-MEM-021` | Pending→Bound 成功路径 |
| `TEST-MEM-022` | Pending→Error validation 路径 |
| `TEST-MEM-023` | Error 重试后恢复 Bound |
| `TEST-MEM-024` | 单资源错误不阻塞后续资源 |
| `TEST-MEM-025` | status patch 只写 status + observedGeneration |
| `TEST-MEM-026` | K8s 5xx 1/2/4/8s 重试 |
| `TEST-MEM-027` | 4xx 不重试且 canonical code 不漂移 |
| `TEST-MEM-028` | prepare 后异常执行 rollback |
| `TEST-MEM-029` | finalize 五步顺序和幂等重放 |
| `TEST-MEM-030` | cleanup 失败保留 finalizer，成功移除 |

---

## 5. Clock、4 个纯函数与 MemoryBackend 抽象层

> **核心决策**：计算函数同步、stateless、不可变；I/O 仅在 `MemoryBackend` adapter 中。Clock 作为参数注入，禁止函数内部读取系统时间。

### 5.1 Clock Protocol、单调时间与 clock-skew 容忍

```python
@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...
    async def sleep(self, delay: float) -> None: ...
    def monotonic(self) -> float: ...

def elapsed_non_negative(start: datetime, end: datetime, *, tolerance_seconds: float = 5.0) -> float:
    skew = (end - start).total_seconds()
    if skew < -tolerance_seconds:
        raise ClockSkewError("wall clock moved backward beyond tolerance")
    return max(skew, 0.0)
```

wall clock 仅用于 wire timestamps；deadline、节流与重试使用 `monotonic()`。向后漂移 `<=5s` 钳制为 0，`>5s` 显式失败并映射 `MEMORY_INTERNAL_ERROR`；禁止产生负 elapsed_days。

### 5.2 SystemClock/FakeClock 注入

```python
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
    async def sleep(self, delay: float) -> None:
        await asyncio.sleep(delay)
    def monotonic(self) -> float:
        return time.monotonic()

class FakeClock:
    def __init__(self, start: datetime) -> None:
        if start.tzinfo is None:
            raise ValueError("FakeClock requires aware datetime")
        self._now, self._mono = start.astimezone(UTC), 0.0
    def now(self) -> datetime:
        return self._now
    def monotonic(self) -> float:
        return self._mono
    async def sleep(self, delay: float) -> None:
        self.advance(timedelta(seconds=delay))
    def advance(self, delta: timedelta) -> None:
        if delta.total_seconds() < 0:
            raise ValueError("FakeClock is monotonic")
        self._now += delta
        self._mono += delta.total_seconds()
```

生产注入 `SystemClock`；测试显式注入 `FakeClock`，不得 monkeypatch `datetime.now`。freezegun 仅验证第三方 timestamp adapter。

### 5.3 PUT 纯函数（validate + immutable record）

```python
def put(state: Mapping[str, Memory], memory: Memory, *, clock: Clock, max_size: int, ttl_seconds: int | None) -> PutResult:
    key = canonical_key(memory)
    if key not in state and len(state) >= max_size:
        raise MemoryContractError("MEMORY_FORBIDDEN", "backend capacity reached")
    now = clock.now()
    stored = memory.model_copy(deep=True)
    expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds else None
    output = dict(state)
    output[key] = stored
    return PutResult(state=MappingProxyType(output), memory=stored, stored_at=now, expires_at=expires_at)
```

同 key PUT 为原子 replace；idempotency key 重复 PUT 返回同 result。schema/content 错误映射 `MEMORY_INVALID_CONTENT`，无写权限与容量拒绝映射 `MEMORY_FORBIDDEN`。

### 5.4 GET 纯函数（TTL + snapshot）

```python
def get(state: Mapping[str, StoredMemory], namespace: str, name: str, *, clock: Clock) -> GetResult:
    record = state.get(canonical_key_parts(namespace, name))
    if record is None or (record.expires_at and clock.now() >= record.expires_at):
        return GetResult(found=False, memory=None)
    return GetResult(found=True, memory=record.memory.model_copy(deep=True))
```

不存在不是自创任何 `MEMORY_*`；handler 根据上下文返回空集合。backend 不可达只映射 `MEMORY_INTERNAL_ERROR`。完整封闭集见 §5.7。

### 5.5 DELETE 纯函数（幂等 tombstone）

```python
def delete(state: Mapping[str, StoredMemory], namespace: str, name: str, *, clock: Clock) -> DeleteResult:
    output = dict(state)
    removed = output.pop(canonical_key_parts(namespace, name), None)
    return DeleteResult(state=MappingProxyType(output), deleted=removed is not None, deleted_at=clock.now())
```

重复 DELETE 成功且 `deleted=False`；权限错误 `MEMORY_FORBIDDEN`，后端失败 `MEMORY_INTERNAL_ERROR`。

### 5.6 LIST 纯函数（稳定排序 + snapshot pagination）

```python
def list_memories(state: Mapping[str, StoredMemory], query: QueryMemoryRequest, *, clock: Clock) -> ListResult:
    if query.scope == "industry" and not (query.tags or query.min_confidence is not None):
        raise MemoryContractError("MEMORY_QUERY_TOO_BROAD")
    visible = [r for r in state.values() if not expired(r, clock.now()) and visible_to(r, query)]
    ordered = sorted(visible, key=lambda r: (r.memory.metadata.namespace, r.memory.metadata.name))
    page = ordered[query.offset:query.offset + query.limit]
    return ListResult(items=tuple(snapshot(r.memory) for r in page), total=len(ordered))
```

LIST 固定 `(namespace,name)` 排序；一次调用读取一个 immutable snapshot。visibility 拒绝映射 `MEMORY_FORBIDDEN`，过宽查询映射 `MEMORY_QUERY_TOO_BROAD`。

### 5.7 MemoryBackend Protocol（6 抽象方法 + 5 项不变量）

```python
@runtime_checkable
class MemoryBackend(Protocol):
    async def put(self, memory: Memory, *, idempotency_key: str | None = None) -> PutResult: ...
    async def get(self, namespace: str, name: str) -> Memory | None: ...
    async def delete(self, namespace: str, name: str) -> DeleteResult: ...
    async def list(self, query: QueryMemoryRequest) -> ListResult: ...
    async def patch_status(self, namespace: str, name: str, status: MemoryStatus, *, expected_generation: int) -> None: ...
    async def health(self) -> BackendHealth: ...
```

后端仅抛 `MemoryBackendError(code: MemoryErrorCode, retryable: bool, cause: Exception | None)`；adapter 直接 import §9.1 的 12 个 `MemoryErrorCode`。`dict`/`in-memory`/`redis` 必须通过同一 contract suite。

1. **不可变快照**：输入与返回对象 deep copy/frozen，不得改 caller 对象。
2. **线性化单 key 写**：PUT/DELETE/status patch 原子；CAS 冲突显式失败。
3. **Clock 唯一时间源**：TTL/节流/deadline 使用注入 Clock。
4. **错误码封闭集**：仅 L2-4 §9.1 十二个 `MEMORY_*`；禁止任何新增同义错误码。
5. **可替换语义**：切换 backendType 不改变排序、TTL、幂等与 caller 可观察结果。

**§5 测试 ID（22）**：

| ID | 描述 |
|---|---|
| `TEST-MEM-031` | SystemClock 返回 UTC aware datetime |
| `TEST-MEM-032` | FakeClock now/sleep/monotonic 同步推进 |
| `TEST-MEM-033` | FakeClock 拒绝倒退 |
| `TEST-MEM-034` | <=5s skew 钳制，>5s 显式失败 |
| `TEST-MEM-035` | PUT 新 key immutable snapshot |
| `TEST-MEM-036` | PUT 同 key 原子 replace |
| `TEST-MEM-037` | PUT capacity 映射 MEMORY_FORBIDDEN |
| `TEST-MEM-038` | PUT content 错误映射 MEMORY_INVALID_CONTENT |
| `TEST-MEM-039` | GET hit 返回 deep copy |
| `TEST-MEM-040` | GET miss 不创造新的 MEMORY_* 错误码 |
| `TEST-MEM-041` | GET TTL 精确边界过期 |
| `TEST-MEM-042` | DELETE existing 返回 deleted=true |
| `TEST-MEM-043` | DELETE 重放幂等 deleted=false |
| `TEST-MEM-044` | LIST 固定 namespace/name 排序 |
| `TEST-MEM-045` | LIST 并发 PUT 使用调用时 snapshot |
| `TEST-MEM-046` | LIST industry 无过滤映射 MEMORY_QUERY_TOO_BROAD |
| `TEST-MEM-047` | visibility 拒绝映射 MEMORY_FORBIDDEN |
| `TEST-MEM-048` | Protocol 六方法 runtime_checkable |
| `TEST-MEM-049` | dict/in-memory/redis contract suite 等价 |
| `TEST-MEM-050` | patch_status generation CAS 冲突显式失败 |
| `TEST-MEM-051` | backend exception 保留 cause 并映射 MEMORY_INTERNAL_ERROR |
| `TEST-MEM-052` | 权威错误码封闭集静态检查 |

---

## 6. in-process function reference 契约（与 L3-5 §6.2 严格一致）

### 6.1 三条运行时规则

1. **immutable 传递**：L3-5 传入 frozen/deep-copy snapshot；L3-6 不保存 caller mutable reference。
2. **显式失败**：全链 `async def` + exception propagation；L3-5 不 catch 后改 code，L3-6 不以模糊 `None` 表示 backend failure。
3. **单调时钟**：deadline/timeout/idempotency window 使用同一 `Clock.monotonic()`；wall-clock skew 不改变调用顺序。

```python
@runtime_checkable
class MemoryBackendInProcessService(Protocol):
    async def record_memory_async(self, memory: Memory, *, context: InProcessContext) -> MemoryRecordResult: ...
    async def query_memory_async(self, request: QueryMemoryRequest, *, context: InProcessContext) -> QueryMemoryResult: ...
```

**Clock 边界**：L3-6 在 `record_memory_async` / `query_memory_async` handler 入口将 `Clock.monotonic()` 通过 `InProcessContext` 暴露给 L3-5 调用方（用于 deadline/timeout/idempotency window 一致性）；L3-5 不得使用 `asyncio.get_event_loop().time()` 或本地 `time.monotonic()` 独立计算 deadline，必须读取 `context.clock.monotonic()`。`InProcessContext` 必须携带与 L3-6 §5.1 `Clock` 协议同源的 `clock` 字段（`RealClock` / `FakeClock`），且为 frozen 不可变。

禁止 HTTP loopback。共享 emptyDir 只提供模块 artifact；两个独立 Python 进程不能共享对象内存，因此实际跨 container transport 若无法 direct import，必须在 L4 spike 前将部署修正为同进程或使用明确 IPC，并保持本 Protocol 语义。

### 6.2 8 个边界测试（PUT/GET/DELETE/LIST 各 2 项）

| ID | 操作 | 并发/错误/时序完整描述 |
|---|---|---|
| `TEST-MEM-053` | PUT | 两个并发同 key + 同 idempotency key，仅一次 commit，二者返回同 resourceVersion |
| `TEST-MEM-054` | PUT | admission 50ms deadline 超时透传 `MEMORY_ADMISSION_TIMEOUT`，无临时 backendRef 泄漏 |
| `TEST-MEM-055` | GET | GET 与 DELETE 竞态线性化：只允许完整旧 snapshot 或 miss，不允许半对象 |
| `TEST-MEM-056` | GET | backend 断连保留 cause 并透传 `MEMORY_INTERNAL_ERROR`，L3-5 不重映射 |
| `TEST-MEM-057` | DELETE | 两个并发 DELETE 至多一次 `deleted=true`，两次调用均成功且 finalizer 可重放 |
| `TEST-MEM-058` | DELETE | clock deadline 到达后不进入 cleanup commit；已 prepare token 必须 rollback |
| `TEST-MEM-059` | LIST | LIST 与并发 PUT 使用单一 snapshot、稳定排序、无重复/半页数据 |
| `TEST-MEM-060` | LIST | industry 无 tag/confidence 过滤透传 `MEMORY_QUERY_TOO_BROAD` 且 0 次 backend scan |

**与 L3-5 §6.2 的部署级 8 ID 保持原名**：`MTLS-IT-001..005` 与 `E2E-WIRE-IT-001..003` 继续验证双 container、ServiceMonitor、RBAC、NetworkPolicy 与 record/query 委托链；上表是操作级补集，不替换它们。

### 6.3 协调点拓扑

```text
Knowledge Service Pod · replicaCount=1
├─ knowledge-service :8080
│  ├─ A2A recordMemory/queryMemory
│  ├─ admission_validator（唯一 owner；50ms fail-closed）
│  └─ MemoryBackendInProcessService client
└─ memory-backend :8081（不进 Service）
   ├─ MemoryBackend Protocol -> dict | in-memory | redis
   ├─ 60s timer + Lease + finalize
   └─ immutable record/query result

A2A envelope -> L3-5 admission -> immutable DTO -> L3-6 Protocol
             -> backend -> result/权威异常透传 -> L3-5 wire envelope
```

L3-5 独占四个 A2A method 与 admission；L3-6 独占 timer、Lease、后端 I/O 与生命周期算法；Service 仅暴露 8080。

### 6.4 与 L2-3 admission_validator 的 in-process 调用契约（五步互斥）

> 实际 validator owner 是 L3-5 §5；L2-3/L3-3 Adapter SDK 不被 L3-6 import。此处只定义适配边界，禁止复制 validator 实现。

1. **freeze input**：L3-5 用 `Memory.model_validate` 构建 immutable snapshot，记录 generation/request_id。
2. **50ms validation**：调用唯一 `admission_validator`；scope、SA、source KI 与 content 失败使用权威错误码。
3. **mutex lookup**：按 `scopeRef + contentHash` 查询；同 agent 可 supersede，不同 agent 拒绝；不得产生写。
4. **single handoff**：允许后只调用一次 `record_memory_async`；L3-6 不重复 admission，用 idempotency key 防重。
5. **propagate/commit**：L3-6 原样返回或抛权威异常；L3-5 只包装 envelope。超时/取消 rollback，禁止 fail-open。

```python
async def admitted_record_memory(req: RecordMemoryRequest, context: InProcessContext) -> MemoryRecordResult:
    memory = Memory.model_validate(req.memory).model_copy(deep=True)
    # 50ms admission deadline 必须以 L3-6 暴露的 Clock.monotonic() 为基准，与 handler
    # 内部 deadline/timeout/idempotency window 保持同一时间源。
    monotonic_deadline = context.clock.monotonic() + 0.050
    try:
        await asyncio.wait_for(
            admission_validator.validate_memory(memory),
            timeout=max(0.0, monotonic_deadline - context.clock.monotonic()),
        )
    except asyncio.TimeoutError as exc:
        raise AdmissionTimeoutError("MEMORY_ADMISSION_TIMEOUT") from exc
    await admission_validator.validate_ki_memory_mutex(memory)
    return await memory_service.record_memory_async(memory, context=context)
```

### 6.5 五项关键不变量 → 实现映射

| §1.2 不变量 | §3-§6 显式保证 |
|---|---|
| 同 Pod 第二进程 / 单实例 | §6.3 拓扑 + replicaCount=1 + 8081 不暴露；§6.1 标注跨进程机制需 L4 spike |
| 60s timer 固定 | §4.1 decorator 固定 `interval=60.0` / `id="memory-reconciler"` + TEST-MEM-016 |
| L3-5/L3-6 共享 Deployment | §6.1 Protocol、§6.3 拓扑、保留 MTLS/E2E-WIRE 8 ID |
| 4 生命周期纯函数数学不变 | §4.3 `calculate_status` 调用 L2-4 §7.3；§5 将存储操作与算法隔离，禁止 adapter 改公式 |
| L2-4 wire 完全继承 | §3.3 12 字段、§3.4 权威 code、§5.7 封闭错误集、TEST-MEM-001/052/060 |

**§3-§6 测试分布**：§3 `TEST-MEM-001..015`（15）+ §4 `016..030`（15）+ §5 `031..052`（22）+ §6 `053..060`（8）= **60 个唯一测试 ID**。

---

## 7. Observability（10 Memory 业务指标 + structlog 8 字段 + K8s Events）

> 实现位置：`services/memory-backend/src/superteam_a2a/memory_backend/observability/`；复用 L3-2 §9 的 11 A2A + 4 Python runtime 指标。L3-6 只新增下列 10 个低基数 Memory 指标，合计 25 个。

### 7.1 10 个 Memory 业务指标

| # | name | type | labels | help text | buckets |
|---:|---|---|---|---|---|
| 1 | `superteam_memory_reconcile_total` | Counter | `phase,result` | Total Memory reconcile attempts. | — |
| 2 | `superteam_memory_reconcile_duration_seconds` | Histogram | `phase` | Memory reconcile batch duration. | `.005,.01,.025,.05,.1,.25,.5,1,2.5,5,10,30,50` |
| 3 | `superteam_memory_decay_applied_total` | Counter | `phase_from,phase_to` | Total decay transitions applied. | — |
| 4 | `superteam_memory_reinforce_total` | Counter | `result` | Total reinforcement operations. | — |
| 5 | `superteam_memory_gc_cleaned_total` | Counter | `gc_state` | Total expired Memories deleted. | — |
| 6 | `superteam_memory_promotion_eligible_total` | Gauge | `visibility` | Current Memories eligible for promotion. | — |
| 7 | `superteam_memory_bm25_index_size` | Gauge | `scope_level` | Indexed Memory count. | — |
| 8 | `superteam_memory_admission_duration_seconds` | Histogram | `validator` | Memory admission duration. | `.001,.0025,.005,.01,.025,.05,.1,.25,.5,1,2.5,5` |
| 9 | `superteam_memory_in_process_call_total` | Counter | `method,result` | L3-5 to L3-6 calls. | — |
| 10 | `superteam_memory_rate_limited_total` | Counter | `principal_type` | Rate-limited Memory writes. | — |

`phase/result/gc_state/visibility/scope_level/validator/method/principal_type` 均为封闭枚举；禁止 `memory_name`、`service_account`、`scope_name`、`request_id` 进入 label。具体身份只进入脱敏日志/trace。`OBS-MEM-UT-001~010` 逐行验证 name/type/labels/help/buckets，`OBS-MEM-IT-001` 验证 `/metrics` 聚合 25 个指标且无高基数 label。

```python
from prometheus_client import Counter, Gauge, Histogram

MEMORY_RECONCILE_TOTAL = Counter(
    "superteam_memory_reconcile_total",
    "Total Memory reconcile attempts.",
    ("phase", "result"),
)
MEMORY_RECONCILE_DURATION = Histogram(
    "superteam_memory_reconcile_duration_seconds",
    "Memory reconcile batch duration.",
    ("phase",),
    buckets=(.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10, 30, 50),
)
MEMORY_PROMOTION_ELIGIBLE = Gauge(
    "superteam_memory_promotion_eligible_total",
    "Current Memories eligible for promotion.",
    ("visibility",),
)
```

计数更新遵循“操作完成后提交”：CAS 冲突记 `result="conflict"`，取消记 `result="cancelled"`，异常记 `result="error"`；不得在重试前预增 success。Histogram 使用 monotonic clock；60s timer 的整批 duration 门禁为 10K `<50s`，50K 目标由 L2-4 性能基线继续跟踪。

### 7.2 structlog 8 必含字段

```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class MemoryLogEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    timestamp: datetime
    level: Literal["debug", "info", "warning", "error", "critical"]
    service: Literal["memory-backend"] = "memory-backend"
    trace_id: str = Field(min_length=16, max_length=64)
    span_id: str = Field(min_length=8, max_length=32)
    request_id: str = Field(min_length=1, max_length=128)
    agent_id: str = Field(min_length=1, max_length=253)
    event: str = Field(min_length=1, max_length=128)
```

固定字段与 L3-2 §9.3、L3-5 §7.2 完全一致。`api_key/token/password/secret/memory_content/content/knowledge_body/tls_key/private_key` 递归替换为 `[REDACTED]`；异常 message 截断 1024 字符。允许附加 `memory_uid/scope_level/phase_from/phase_to/result/backend_kind/generation`，但禁止原始 content、完整 SA token 与 Secret data。

### 7.3 K8s Events（3 个 L3-6 EventReason）

```python
from enum import StrEnum

class MemoryEventReason(StrEnum):
    MEMORY_DECAY_APPLIED = "MemoryDecayApplied"
    MEMORY_GC_CLEANED = "MemoryGCCleaned"
    MEMORY_PROMOTION_ELIGIBLE = "MemoryPromotionEligible"
```

| reason | type | message 模板 | 去重 |
|---|---|---|---|
| `MemoryDecayApplied` | Normal | `Memory {namespace}/{name} changed {phase_from}->{phase_to}` | 同 UID/generation/phase transition |
| `MemoryGCCleaned` | Normal | `Memory {namespace}/{name} expired and was removed` | 同 UID/generation |
| `MemoryPromotionEligible` | Normal | `Memory {namespace}/{name} is eligible for promotion` | 首次从 false→true |

L3-5 的 `MemoryConflictDetected/Resolved` 仍归 admission owner，不在 L3-6 重发。Event type 仅 `Normal/Warning`，message 上限 1024 字符，添加 trace annotation；写 Event 失败只记 metric/log，不回滚已提交的 Memory 状态。`EVENT-MEM-UT-001~003` 验证 enum 固定、模板脱敏与幂等去重。

---

## 8. 错误码（12 个 MEMORY_* · 与 L2-4 v0.2.0 §9.1 零漂移）

> name/code 是封闭 wire contract。新增 `MEMORY_*` 必须先修改 L2-4 权威表并通过 ADR/兼容性评审；L3-6 不得本地扩展、简写或复用 code。

### 8.1 权威错误码表

| name | code | owner / trigger | HTTP | message template | Retryable |
|---|---:|---|---:|---|---|
| `MEMORY_SCOPE_NOT_FOUND` | -32101 | backend / scopeRef 不存在 | 404 | `Memory scope {scope_ref_name} was not found` | No |
| `MEMORY_INVALID_CONTENT` | -32102 | backend / content > 20 keys | 400 | `Memory content exceeds 20 keys (got {actual})` | No |
| `MEMORY_FORBIDDEN` | -32103 | admission / 写入拒绝 | 403 | `Memory write denied: {reason}` | No |
| `MEMORY_RATE_LIMIT` | -32104 | middleware / SA > 60/min | 429 | `Memory write rate exceeded 60/min for SA {service_account}` | Yes |
| `MEMORY_INTERNAL_ERROR` | -32105 | backend / K8s 5xx 或异常 | 500 | `Memory backend internal error` | Yes |
| `MEMORY_QUERY_TOO_BROAD` | -32106 | query / industry 无过滤 | 400 | `Memory query with scope=industry requires tag/confidence filter` | No |
| `MEMORY_SOURCE_KI_NOT_FOUND` | -32107 | admission / source KI 缺失 | 400 | `Memory sourceKnowledgeRef.name {name} was not found` | No |
| `MEMORY_SOURCE_KI_SCOPE_MISMATCH` | -32108 | admission / scope 不一致 | 400 | `Memory source KI scopeRef {ki_scope} != Memory scopeRef {mem_scope}` | No |
| `MEMORY_AGENT_PRIVATE_REQUIRES_NAME` | -32109 | admission / agent name 为空 | 400 | `Memory agent-private requires agentRef.name (got "")` | No |
| `MEMORY_DECAY_DAYS_EXCEEDED` | -32110 | admission / decayDays > 3650 | 400 | `Memory decayDays {decay_days} exceeds 3650` | No |
| `MEMORY_AGENT_NOT_FOUND` | -32111 | admission / SA 不存在 | 400 | `Memory agentRef.name {agent} (SA) was not found` | No |
| `MEMORY_ADMISSION_TIMEOUT` | -32112 | admission / 超过 50ms | 503 | `Memory admission exceeded 50ms` | Yes |

权威源为 [L2-4 v0.2.0 §9.1](../L2-module-specs/L2-knowledge-memory.md)；L3-5 §8.2 是同一 wire 镜像。`ERR-MEM-CF-001` 对三处 name/code 做集合相等比较，不接受子集。`TEST-MEM-051` 必须在 `tests/conformance/test_errors.py` 落地以下静态断言（与 L2-4 §9.1 + L3-5 §8.2 100% 集合相等）：

```python
# tests/conformance/test_errors.py
from superteam_a2a.memory_backend.errors import MemoryErrorCode
from superteam_a2a.knowledge_service.errors import MemoryErrorCode as KsMemoryErrorCode

L2_4_AUTHORITATIVE_NAMES: frozenset[str] = frozenset({
    "MEMORY_SCOPE_NOT_FOUND", "MEMORY_INVALID_CONTENT", "MEMORY_FORBIDDEN",
    "MEMORY_RATE_LIMIT", "MEMORY_INTERNAL_ERROR", "MEMORY_QUERY_TOO_BROAD",
    "MEMORY_SOURCE_KI_NOT_FOUND", "MEMORY_SOURCE_KI_SCOPE_MISMATCH",
    "MEMORY_AGENT_PRIVATE_REQUIRES_NAME", "MEMORY_DECAY_DAYS_EXCEEDED",
    "MEMORY_AGENT_NOT_FOUND", "MEMORY_ADMISSION_TIMEOUT",
})
L2_4_AUTHORITATIVE_CODES: frozenset[int] = frozenset(range(-32101, -32112 + 1))

def test_test_mem_051_memory_error_codes_match_l2_4_authoritative() -> None:
    assert {m.name for m in MemoryErrorCode} == L2_4_AUTHORITATIVE_NAMES
    assert {m.value for m in MemoryErrorCode} == L2_4_AUTHORITATIVE_CODES
    assert {m.name for m in MemoryErrorCode} == {m.name for m in KsMemoryErrorCode}
```

CI 门禁顺序（§11.6）将 `conformance → errors exact set` 列为强制步骤，集合不等即拒绝合并。

### 8.2 `MemoryErrorCode` 与 helper

```python
from enum import IntEnum
from typing import Any
from superteam_a2a.a2a.upstream import A2AError

class MemoryErrorCode(IntEnum):
    MEMORY_SCOPE_NOT_FOUND = -32101
    MEMORY_INVALID_CONTENT = -32102
    MEMORY_FORBIDDEN = -32103
    MEMORY_RATE_LIMIT = -32104
    MEMORY_INTERNAL_ERROR = -32105
    MEMORY_QUERY_TOO_BROAD = -32106
    MEMORY_SOURCE_KI_NOT_FOUND = -32107
    MEMORY_SOURCE_KI_SCOPE_MISMATCH = -32108
    MEMORY_AGENT_PRIVATE_REQUIRES_NAME = -32109
    MEMORY_DECAY_DAYS_EXCEEDED = -32110
    MEMORY_AGENT_NOT_FOUND = -32111
    MEMORY_ADMISSION_TIMEOUT = -32112


def memory_error(code: MemoryErrorCode, message: str, **data: Any) -> A2AError:
    return A2AError(
        code=code.value,
        message=message[:1024],
        data={"module": "memory", "code_name": code.name, **data},
    )
```

`memory_error()` 只接受 enum，禁止裸整数。`data` 可含 `retry_after_seconds/request_id/scope_level/backend_kind`，不得含 content/token/Secret。L3-6 抛出的 `A2AError` 由 L3-5 原样透传 code/message/data；未知 Python/K8s 异常在边界映射为 `MEMORY_INTERNAL_ERROR`，但 `CancelledError` 必须继续传播。

### 8.3 Retryable / Backoff / CircuitBreaker 矩阵

| error | Retryable | Backoff | CircuitBreaker |
|---|---|---|---|
| `MEMORY_SCOPE_NOT_FOUND` | No | none | No |
| `MEMORY_INVALID_CONTENT` | No | none | No |
| `MEMORY_FORBIDDEN` | No | none | No |
| `MEMORY_RATE_LIMIT` | Yes | 尊重 `Retry-After`，最迟到下一滑动窗口 | No |
| `MEMORY_INTERNAL_ERROR` | Yes | immediate once | Yes，连续 5 次打开 30s |
| `MEMORY_QUERY_TOO_BROAD` | No | none | No |
| `MEMORY_SOURCE_KI_NOT_FOUND` | No | none | No |
| `MEMORY_SOURCE_KI_SCOPE_MISMATCH` | No | none | No |
| `MEMORY_AGENT_PRIVATE_REQUIRES_NAME` | No | none | No |
| `MEMORY_DECAY_DAYS_EXCEEDED` | No | none | No |
| `MEMORY_AGENT_NOT_FOUND` | No | none | No |
| `MEMORY_ADMISSION_TIMEOUT` | Yes | 100/200/400ms | No；始终 fail-closed |

validation/authorization/conflict 永不重试。重试复用同一 idempotency key；任何已提交 CAS 不得重复执行 reinforcement/GC。Circuit Breaker 只覆盖 backend target，half-open 仅放行 1 个探测。`ERR-MEM-UT-001~012` 逐行断言 enum/code/HTTP/template/retry 元数据；`ERR-MEM-IT-001` 验证 L3-5 envelope 透传。

### 8.4 BackendHealth / CAS 映射

§5.7 `patch_status()` 的 `resourceVersion` 冲突是可观测的并发结果，不创建新 wire code：内部返回 `PatchOutcome.CONFLICT` 并按同一 generation 有界重读一次；重读仍冲突则映射 `MEMORY_INTERNAL_ERROR`。`BackendHealth(ready=False)`、K8s 5xx、Lease API 不可用统一映射 `MEMORY_INTERNAL_ERROR`；缺少业务对象才映射对应 `*_NOT_FOUND`。该封闭规则关闭 #65 移交关注项“BackendHealth schema / CAS 映射不明确”。

---

## 9. Helm Values 7 模板（共享 chart · 双业务进程 · RBAC 双 Role）

### 9.1 `_helpers.tpl` / values / schema

```yaml
replicaCount: 1
image: {repository: superteam-a2a/knowledge-service, tag: v0.2.0}
memoryBackendImage: {repository: superteam-a2a/memory-backend, tag: v0.2.0}
service: {httpPort: 80, httpsPort: 443, targetHttpPort: 8080, targetHttpsPort: 8443}
serviceAccount: {create: true, name: knowledge-service}
tls: {enabled: true, secretName: knowledge-service-tls, clientCASecretName: superteam-client-ca}
metrics: {path: /metrics, interval: 30s, scrapeTimeout: 10s}
memoryReconciler:
  intervalSeconds: 60
  batchSize: 1000
  lease: {name: memory-reconciler, durationSeconds: 30}
resources:
  knowledgeService: {requests: {cpu: 200m, memory: 512Mi}, limits: {cpu: 1500m, memory: 2Gi}}
  memoryBackend: {requests: {cpu: 200m, memory: 256Mi}, limits: {cpu: 1000m, memory: 1Gi}}
```

`_helpers.tpl` 定义 `knowledge-service.name/fullname/labels/selectorLabels/serviceAccountName`。`values.schema.json` 强制 `replicaCount const=1`、两 image tag 非空且非 `latest`、`intervalSeconds const=60`、端口 1..65535、production TLS=true、request≤limit。7 个逻辑模板组仍为 helpers/values、Deployment、Service、ServiceAccount、RBAC、NetworkPolicy、PrometheusRule+ServiceMonitor，对应 `HELM-DEPLOY-001~007`。

### 9.2 `deployment.yaml`（同 Pod 两个独立 Python 业务进程）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: {name: knowledge-service}
spec:
  replicas: 1
  strategy: {type: Recreate}
  selector: {matchLabels: {app.kubernetes.io/name: knowledge-service}}
  template:
    metadata: {labels: {app.kubernetes.io/name: knowledge-service}}
    spec:
      serviceAccountName: knowledge-service
      terminationGracePeriodSeconds: 30
      securityContext: {runAsNonRoot: true, seccompProfile: {type: RuntimeDefault}}
      containers:
      - name: knowledge-service
        image: superteam-a2a/knowledge-service:v0.2.0
        ports: [{name: http, containerPort: 8080}, {name: https, containerPort: 8443}]
        envFrom: [{configMapRef: {name: knowledge-service-config}}]
        livenessProbe: {httpGet: {path: /healthz, port: http}, initialDelaySeconds: 10, periodSeconds: 30}
        readinessProbe: {httpGet: {path: /readyz, port: http}, initialDelaySeconds: 5, periodSeconds: 10}
        securityContext: &restricted
          {runAsUser: 65532, allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, capabilities: {drop: [ALL]}}
        volumeMounts: [{name: tls, mountPath: /var/run/secrets/tls, readOnly: true}, {name: ipc, mountPath: /var/run/superteam}]
      - name: memory-backend
        image: superteam-a2a/memory-backend:v0.2.0
        ports: [{name: memory-health, containerPort: 8081}]
        env:
        - {name: MEMORY_RECONCILER_INTERVAL, value: "60"}
        - {name: LEASE_NAME, value: memory-reconciler}
        - {name: IPC_SOCKET, value: /var/run/superteam/memory.sock}
        livenessProbe: {httpGet: {path: /healthz, port: memory-health}, periodSeconds: 30}
        readinessProbe: {httpGet: {path: /readyz, port: memory-health}, periodSeconds: 10}
        securityContext: *restricted
        volumeMounts: [{name: ipc, mountPath: /var/run/superteam}]
      volumes:
      - {name: tls, secret: {secretName: knowledge-service-tls}}
      - {name: ipc, emptyDir: {medium: Memory, sizeLimit: 16Mi}}
```

8081 只用于 kubelet probe，不进入 Service。§6.1 的 function-reference 是逻辑 Protocol；两个 container 跨进程 transport 在 L4 spike 前固定为受限 Unix domain socket 候选，禁止 loopback HTTP 冒充“in-process”。transport 必须保持 async DTO、异常透传、取消与幂等语义；决策前不锁定实现。这显式保留 #65 transport 关注项。

### 9.3 `service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata: {name: knowledge-service, labels: {app.kubernetes.io/name: knowledge-service}}
spec:
  selector: {app.kubernetes.io/name: knowledge-service}
  ports:
  - {name: http, port: 80, targetPort: 8080}
  - {name: https, port: 443, targetPort: 8443}
```

443 承载 TLS 1.3 + mTLS A2A；80 仅 health/readiness/metrics。不得添加 8081 或 IPC socket 对外入口。

### 9.4 `serviceaccount.yaml`

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: knowledge-service
  annotations: {cert-manager.io/inject-ca-from: superteam-a2a/knowledge-service-serving}
automountServiceAccountToken: true
```

L3-5/L3-6 共享专用 SA；不得使用 default SA。token 仅用于 K8s API，采用 projected token、短 TTL 与 audience 约束。

### 9.5 `rbac/role_readonly.yaml` + `role_write.yaml` + bindings

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: {name: knowledge-service-read}
rules:
- {apiGroups: [superteam-a2a.io], resources: [knowledgescopes, knowledgeitems, memories], verbs: [get, list, watch]}
- {apiGroups: [""], resources: [configmaps], verbs: [get, list, watch]}
- {apiGroups: [""], resources: [secrets], resourceNames: [knowledge-service-tls, superteam-client-ca], verbs: [get, watch]}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: {name: memory-backend-write}
rules:
- {apiGroups: [superteam-a2a.io], resources: [memories/status], verbs: [get, patch, update]}
- {apiGroups: [superteam-a2a.io], resources: [memories], verbs: [get, list, watch, delete]}
- {apiGroups: [coordination.k8s.io], resources: [leases], resourceNames: [memory-reconciler], verbs: [get, create, update, patch]}
- {apiGroups: [""], resources: [events], verbs: [create, patch]}
- {apiGroups: [admissionregistration.k8s.io], resources: [validatingwebhookconfigurations], verbs: [get, list, watch]}
- {apiGroups: [authentication.k8s.io], resources: [tokenreviews], verbs: [create]}
- {apiGroups: [authorization.k8s.io], resources: [subjectaccessreviews], verbs: [create]}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: {name: knowledge-service-read}
subjects: [{kind: ServiceAccount, name: knowledge-service}]
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: Role, name: knowledge-service-read}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: {name: memory-backend-write}
subjects: [{kind: ServiceAccount, name: knowledge-service}]
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: Role, name: memory-backend-write}
```

read Role 绝不包含 create/update/patch/delete；write Role 不可写 KnowledgeScope/KnowledgeItem spec、Secret、WebhookConfiguration。Memory create 归 L3-5 A2A handler/admission 路径；L3-6 仅 status CAS 与 GC delete。两个 Role 共享 SA 是部署折中，不改变权限分离审计边界，关闭 L3-5-followup-1 的 Spec 侧拆分。

### 9.6 `networkpolicy.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: knowledge-service}
spec:
  podSelector: {matchLabels: {app.kubernetes.io/name: knowledge-service}}
  policyTypes: [Ingress, Egress]
  ingress:
  - {from: [{namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: superteam-a2a}}}], ports: [{port: 8443}]}
  - {from: [{namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: monitoring}}}], ports: [{port: 8080}]}
  egress:
  - {to: [{ipBlock: {cidr: 10.96.0.1/32}}], ports: [{port: 443}]}
  - {to: [{namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: observability}}}], ports: [{port: 4317}]}
```

默认 deny；仅 A2A/mTLS、Prometheus、K8s API、OTLP 显式允许。同 Pod Unix socket 不经过 NetworkPolicy，依赖 `emptyDir`、UID/GID 与文件 mode `0660` 隔离。

### 9.7 `prometheusrule.yaml`（8 条共享告警）

| alert | PromQL | for |
|---|---|---|
| KnowledgeQueryLatencyP99 | `histogram_quantile(0.99,sum by(le)(rate(superteam_knowledge_query_latency_seconds_bucket[5m]))) > 0.1` | 10m |
| KnowledgeBM25IndexStale | `increase(superteam_knowledge_query_total[10m]) > 0 and max(superteam_knowledge_bm25_index_size) == 0` | 5m |
| KnowledgeMemoryConflictRate | `sum(rate(superteam_knowledge_memory_conflict_total[5m])) > 0.1` | 10m |
| KnowledgeAdmissionFailureRate | `histogram_quantile(0.99,sum by(le)(rate(superteam_knowledge_admission_duration_seconds_bucket[5m]))) > 0.05` | 5m |
| KnowledgeServiceDown | `up{job="knowledge-service"} == 0` | 2m |
| KnowledgeMemoryReconcileErrorRate | `sum(rate(superteam_memory_reconcile_total{result="error"}[5m])) > 0.05` | 10m |
| MemoryReconcileDeadlineRisk | `histogram_quantile(0.99,sum by(le)(rate(superteam_memory_reconcile_duration_seconds_bucket[10m]))) > 50` | 5m |
| MemoryBackendNotReady | `up{job="knowledge-service"} == 1 and absent(superteam_memory_reconcile_total)` | 2m |

完整 PrometheusRule 模板（含 `apiVersion: monitoring.coreos.com/v1` + `metadata` + `spec.groups` + 8 条告警的 `alert/expr/for/labels/annotations`）：

```yaml
# helm/knowledge-service/templates/prometheusrule.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: knowledge-service
  labels:
    app.kubernetes.io/name: knowledge-service
    app.kubernetes.io/component: observability
spec:
  groups:
  - name: knowledge-service.rules
    interval: 30s
    rules:
    - alert: KnowledgeQueryLatencyP99
      expr: histogram_quantile(0.99, sum by (le) (rate(superteam_knowledge_query_latency_seconds_bucket[5m]))) > 0.1
      for: 10m
      labels:
        severity: warning
        service: knowledge-service
      annotations:
        summary: "Knowledge query p99 latency above 100ms for 10m"
        runbook_url: "https://runbooks.example.invalid/knowledge-service/query-latency"
    - alert: KnowledgeBM25IndexStale
      expr: increase(superteam_knowledge_query_total[10m]) > 0 and max(superteam_knowledge_bm25_index_size) == 0
      for: 5m
      labels:
        severity: critical
        service: knowledge-service
      annotations:
        summary: "BM25 index empty while queries are served"
        runbook_url: "https://runbooks.example.invalid/knowledge-service/bm25-stale"
    - alert: KnowledgeMemoryConflictRate
      expr: sum(rate(superteam_knowledge_memory_conflict_total[5m])) > 0.1
      for: 10m
      labels:
        severity: warning
        service: knowledge-service
      annotations:
        summary: "Knowledge/Memory conflict rate above 0.1/s for 10m"
        runbook_url: "https://runbooks.example.invalid/knowledge-service/memory-conflict"
    - alert: KnowledgeAdmissionFailureRate
      expr: histogram_quantile(0.99, sum by (le) (rate(superteam_knowledge_admission_duration_seconds_bucket[5m]))) > 0.05
      for: 5m
      labels:
        severity: critical
        service: knowledge-service
      annotations:
        summary: "Admission p99 above 50ms for 5m"
        runbook_url: "https://runbooks.example.invalid/knowledge-service/admission-fail"
    - alert: KnowledgeServiceDown
      expr: up{job="knowledge-service"} == 0
      for: 2m
      labels:
        severity: critical
        service: knowledge-service
      annotations:
        summary: "Knowledge Service scrape target down for 2m"
        runbook_url: "https://runbooks.example.invalid/knowledge-service/down"
    - alert: KnowledgeMemoryReconcileErrorRate
      expr: sum(rate(superteam_memory_reconcile_total{result="error"}[5m])) > 0.05
      for: 10m
      labels:
        severity: warning
        service: memory-backend
      annotations:
        summary: "Memory reconcile error rate above 0.05/s for 10m"
        runbook_url: "https://runbooks.example.invalid/memory-backend/reconcile-error"
    - alert: MemoryReconcileDeadlineRisk
      expr: histogram_quantile(0.99, sum by (le) (rate(superteam_memory_reconcile_duration_seconds_bucket[10m]))) > 50
      for: 5m
      labels:
        severity: critical
        service: memory-backend
      annotations:
        summary: "Memory reconcile p99 above 50s for 5m"
        runbook_url: "https://runbooks.example.invalid/memory-backend/reconcile-deadline"
    - alert: MemoryBackendNotReady
      expr: up{job="knowledge-service"} == 1 and absent(superteam_memory_reconcile_total)
      for: 2m
      labels:
        severity: critical
        service: memory-backend
      annotations:
        summary: "Memory backend scrape present but no reconcile metric emitted"
        runbook_url: "https://runbooks.example.invalid/memory-backend/not-ready"
```

全部模板含 severity/summary/runbook URL，并通过 `promtool check rules`。告警不得使用对象名 label。

### 9.8 `servicemonitor.yaml`

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata: {name: knowledge-service}
spec:
  selector: {matchLabels: {app.kubernetes.io/name: knowledge-service}}
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
    metricRelabelings:
    - {action: keep, sourceLabels: [__name__], regex: 'superteam_a2a_.*|python_.*|process_.*|superteam_knowledge_.*|superteam_memory_.*'}
```

L3-5 `/metrics` 汇聚两个 registry；Prometheus 禁止直连 8081。必须可见 15 个复用指标 + 10 个 Memory 指标。

### 9.9 共享 chart 不变量

Deployment 固定 `replicaCount=1`，包含 `knowledge-service` 与 `memory-backend` 两个业务 container，共享 SA/TLS/ConfigMap/IPC volume，但不得 import 对方私有模块。滚动策略使用 `Recreate` 防止两个 Pod 同时活跃；Lease 仍是 timer 唯一执行者的最终防线。

### 9.10 Helm 验证矩阵

| ID | 验证 |
|---|---|
| HELM-DEPLOY-001 | helpers/values schema 与 const=1/60 |
| HELM-DEPLOY-002 | 双 container、双 probe、restricted SecurityContext、IPC volume（emptyDir medium: Memory sizeLimit: 16Mi mounted to /var/run/superteam）、memory-backend env 三项（MEMORY_RECONCILER_INTERVAL=60 / LEASE_NAME=memory-reconciler / IPC_SOCKET=/var/run/superteam/memory.sock）、Recreate strategy、`securityContext: *restricted` YAML anchor |
| HELM-DEPLOY-003 | Service 不暴露 8081 |
| HELM-DEPLOY-004 | 专用 SA + read/write 双 Role 最小权限 |
| HELM-DEPLOY-005 | default-deny NetworkPolicy + UDS mode |
| HELM-DEPLOY-006 | 8 rules 通过 promtool |
| HELM-DEPLOY-007 | 25 指标经单一 ServiceMonitor 可见 |

---

## 10. 测试策略 + 验收清单

### 10.1 60 个唯一测试 ID 矩阵

> `TEST-MEM-001~060` 是 L3-6 基线；§7 `OBS/EVENT`、§8 `ERR`、§9 `HELM` 名称是这些能力组内的参数化 case，不重复增加基线计数。

| ID | 层级 | 目标 | 文件路径 |
|---|---|---|---|
| TEST-MEM-001 | UT | Memory alias round-trip | `tests/unit/models/test_memory.py` |
| TEST-MEM-002 | UT | 12 spec fields exact | `tests/unit/models/test_memory.py` |
| TEST-MEM-003 | UT | extra field forbidden | `tests/unit/models/test_memory.py` |
| TEST-MEM-004 | UT | immutable snapshot | `tests/unit/models/test_memory.py` |
| TEST-MEM-005 | UT | content max 20 keys | `tests/unit/models/test_memory.py` |
| TEST-MEM-006 | UT | confidence [0,1] | `tests/unit/models/test_memory.py` |
| TEST-MEM-007 | UT | decayDays [1,3650] | `tests/unit/models/test_memory.py` |
| TEST-MEM-008 | UT | ServiceAccount owner only | `tests/unit/models/test_memory.py` |
| TEST-MEM-009 | UT | source KI optional reference | `tests/unit/models/test_memory.py` |
| TEST-MEM-010 | UT | phase enum closed | `tests/unit/models/test_memory_status.py` |
| TEST-MEM-011 | UT | observedGeneration | `tests/unit/models/test_memory_status.py` |
| TEST-MEM-012 | UT | effectiveConfidence bounds | `tests/unit/models/test_memory_status.py` |
| TEST-MEM-013 | CF | CRD schema diff | `tests/conformance/test_memory_crd.py` |
| TEST-MEM-014 | CF | v1alpha1 wire uniqueness | `tests/conformance/test_memory_crd.py` |
| TEST-MEM-015 | IT | CRD CRUD/watch | `tests/integration/test_memory_crd.py` |
| TEST-MEM-016 | UT | timer interval exactly 60s | `tests/unit/reconciler/test_timer.py` |
| TEST-MEM-017 | UT | Lease single holder | `tests/unit/reconciler/test_leader.py` |
| TEST-MEM-018 | IT | Lease transfer <30s | `tests/integration/test_leader_election.py` |
| TEST-MEM-019 | UT | batch pagination | `tests/unit/reconciler/test_batch.py` |
| TEST-MEM-020 | UT | deterministic ordering | `tests/unit/reconciler/test_batch.py` |
| TEST-MEM-021 | UT | stale generation skip | `tests/unit/reconciler/test_generation.py` |
| TEST-MEM-022 | UT | status CAS success | `tests/unit/reconciler/test_patch.py` |
| TEST-MEM-023 | UT | status CAS conflict retry once | `tests/unit/reconciler/test_patch.py` |
| TEST-MEM-024 | UT | cancellation propagation | `tests/unit/reconciler/test_cancel.py` |
| TEST-MEM-025 | UT | partial batch isolation | `tests/unit/reconciler/test_batch.py` |
| TEST-MEM-026 | UT | idempotent replay | `tests/unit/reconciler/test_idempotency.py` |
| TEST-MEM-027 | TZ | phase transition clock boundary | `tests/time_travel/test_phase.py` |
| TEST-MEM-028 | TZ | UTC timezone invariance | `tests/time_travel/test_timezone.py` |
| TEST-MEM-029 | IT | backend unhealthy readiness | `tests/integration/test_readiness.py` |
| TEST-MEM-030 | PERF | 10K reconcile <50s | `tests/performance/test_reconcile.py` |
| TEST-MEM-031 | UT | Clock Protocol real clock | `tests/unit/services/test_clock.py` |
| TEST-MEM-032 | UT | FakeClock no sleep | `tests/unit/services/test_clock.py` |
| TEST-MEM-033 | UT | apply_decay formula | `tests/unit/services/test_decay.py` |
| TEST-MEM-034 | TZ | decay exact boundary | `tests/time_travel/test_decay.py` |
| TEST-MEM-035 | UT | apply_reinforce formula | `tests/unit/services/test_reinforce.py` |
| TEST-MEM-036 | UT | reinforce monotonicity | `tests/unit/services/test_reinforce.py` |
| TEST-MEM-037 | UT | gc_expired predicate | `tests/unit/services/test_gc.py` |
| TEST-MEM-038 | TZ | GC retention boundary | `tests/time_travel/test_gc.py` |
| TEST-MEM-039 | UT | promotion predicate | `tests/unit/services/test_promotion.py` |
| TEST-MEM-040 | TZ | promotion threshold boundary | `tests/time_travel/test_promotion.py` |
| TEST-MEM-041 | UT | pure functions no I/O | `tests/unit/services/test_purity.py` |
| TEST-MEM-042 | UT | backend Protocol conformance | `tests/unit/backend/test_protocol.py` |
| TEST-MEM-043 | UT | dict backend parity | `tests/unit/backend/test_dict_backend.py` |
| TEST-MEM-044 | UT | K8s backend parity | `tests/unit/backend/test_k8s_backend.py` |
| TEST-MEM-045 | UT | list snapshot isolation | `tests/unit/backend/test_list.py` |
| TEST-MEM-046 | UT | patch resourceVersion required | `tests/unit/backend/test_patch.py` |
| TEST-MEM-047 | UT | delete precondition UID | `tests/unit/backend/test_delete.py` |
| TEST-MEM-048 | UT | BackendHealth schema | `tests/unit/backend/test_health.py` |
| TEST-MEM-049 | UT | K8s 5xx mapping | `tests/unit/backend/test_errors.py` |
| TEST-MEM-050 | UT | not-found mapping | `tests/unit/backend/test_errors.py` |
| TEST-MEM-051 | CF | 12 errors exact set + 集合相等静态断言 | `tests/conformance/test_errors.py` |
| TEST-MEM-052 | PERF | 50K filter p95<50ms | `tests/performance/test_memory_filter.py` |
| TEST-MEM-053 | IT | Protocol DTO round-trip | `tests/integration/test_inprocess.py` |
| TEST-MEM-054 | IT | error passthrough | `tests/integration/test_inprocess.py` |
| TEST-MEM-055 | IT | timeout/cancel rollback | `tests/integration/test_inprocess.py` |
| TEST-MEM-056 | IT | idempotency key dedupe | `tests/integration/test_inprocess.py` |
| TEST-MEM-057 | E2E | record→reconcile→query | `tests/e2e/test_memory_lifecycle.py` |
| TEST-MEM-058 | E2E | admission mutex fail-closed | `tests/e2e/test_memory_mutex.py` |
| TEST-MEM-059 | DEPLOY | shared Pod/RBAC/probes | `tests/deploy/test_memory_backend.py` |
| TEST-MEM-060 | CF | L1/L2/L3 wire closure | `tests/conformance/test_memory_wire.py` |

分布：UT 39、IT 8、CF 4、TZ 5、PERF 2、E2E 2、DEPLOY 1；同一 ID 只归一个最高层级。Helm 7 组、Observability 10 行、Error 12 行作为对应基线 ID 的参数化 case 运行。

### 10.2 30 个 Spec 完整性验收点

- **AC-DOC-01~05**：§0-§13 + A/B 完整；28 文件有职责；Memory 12 字段；四生命周期函数；引用链可追踪。
- **AC-WIRE-01~06**：v1alpha1 schema 唯一；4 A2A method 不变；12 error name/code 不变；alias round-trip；异常透传；未知异常封闭映射。
- **AC-LIFE-01~04**：60s timer；Lease 唯一；decay/reinforce/GC/promotion 数学不变；FakeClock 可重复。
- **AC-BACKEND-01~04**：Protocol 后端等价；CAS 有界重试；BackendHealth 驱动 readiness；取消不提交半状态。
- **AC-SEC-01~04**：50ms admission fail-closed；双向互斥；read/write 双 Role；content/credential 不入日志。
- **AC-HELM-01~04**：replicaCount=1；同 Pod 两业务进程；8081 不暴露；7 模板 lint/render/promtool。
- **AC-TEST-01~03**：60/60 有路径；80/95 覆盖率；CF/E2E/PERF/DEPLOY 失败阻断合并。

### 10.3 六层测试金字塔

| 层级 | 目标占比 | 允许依赖 | 禁止 |
|---|---:|---|---|
| Unit / property | 60% | fake backend/FakeClock | K8s/网络/真实 sleep |
| Handler/Protocol | 10% | immutable DTO/in-memory transport | 私有跨包 import |
| Conformance | 5% | frozen schema/error fixtures | 宽松 subset 比较 |
| Integration/kind | 15% | real API/webhook/Lease | mock 掩盖 RBAC |
| E2E | 5% | shared Pod public entry | 直连 8081 |
| Performance/deploy | 5% | pinned image/chart | 非可重复环境数据 |

### 10.4 覆盖率与性能门禁

全包 line/branch `>=80%`；`apply_decay/apply_reinforce/gc_expired/is_eligible_for_promotion/memory_reconciler/clock/memory_backend/admission/leader_election` 各 `>=95%`。10K Memory 单轮 reconcile `<50s`，50K filter warm p95 `<50ms`，admission p99 `<50ms`。不得 exclude/xfail/调低样本绕过；性能机型、Python 版本、数据 seed 写入 artifact。

---

## 11. 工具链与部署（uv + Docker + cert-manager + Kopf + OTel + Argo CD）

### 11.1 七步开发工作流

1. `uv sync --frozen --all-extras` 还原 workspace lock，校验 Python 3.12 与同步版本。
2. `ruff format --check . && ruff check . && pyright` 执行格式、lint、strict type。
3. `bandit -r packages services && pip-audit && interrogate -f 100 packages services && lint-imports` 执行安全、供应链、docstring、边界门禁。
4. `pytest tests/unit tests/conformance tests/integration --cov=superteam_a2a.memory_backend --cov-fail-under=80` 执行 60 ID 与 80/95 双阈值。
5. `docker buildx build --target runtime`，生成 SBOM、Trivy 扫描并 Cosign 签名。
6. `helm lint`、`helm template`、`promtool check rules`、kind 安装，验证 cert-manager/Kopf/RBAC/Lease/E2E/PERF。
7. Argo CD sync staging，经 smoke/readiness 后 promote production；失败回滚不可变 tag。

`ST-MEMORY-BOUNDARY` 禁止 L3-6 import Adapter SDK、业务 Agent、L3-5 私有实现或 SDK private path；仅允许 shared Pydantic DTO、A2A public Protocol、K8s async client。任一门禁失败即拒绝合并。

### 11.2 多阶段 Dockerfile

```dockerfile
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /workspace
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY packages ./packages
COPY services/memory-backend ./services/memory-backend
RUN uv build services/memory-backend

FROM python:3.12-slim AS runtime
RUN groupadd -g 65532 app && useradd -u 65532 -g app -M app
WORKDIR /app
COPY --from=build /workspace/.venv /app/.venv
COPY --from=build /workspace/services/memory-backend /app/memory-backend
ENV PATH=/app/.venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65532:65532
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=3s CMD ["python", "-m", "superteam_a2a.memory_backend.healthcheck"]
ENTRYPOINT ["python", "-m", "superteam_a2a.memory_backend"]
```

runtime 不含编译器/cache，UID/GID 65532，Pod 使用 read-only rootfs。`DOCKER-DEPLOY-001~003` 验证可复现构建、non-root/restricted、health/SBOM/signature。

### 11.3 cert-manager 与共享 TLS

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata: {name: knowledge-service-serving}
spec:
  secretName: knowledge-service-tls
  duration: 2160h
  renewBefore: 720h
  dnsNames: [knowledge-service, knowledge-service.superteam-a2a.svc]
  usages: [server auth, client auth]
  issuerRef: {name: superteam-ca, kind: ClusterIssuer}
```

L3-6 不开放公网 TLS endpoint，但与 L3-5 共享 Secret/CA 以验证 Pod 身份与后续 transport。TLS 最低 1.3；Secret watch 原子替换，不记录 key/cert。IPC socket 另由文件权限隔离，不能把 TLS Secret 当作跨进程认证替代。

### 11.4 Kopf timer 与进程启动

```python
import kopf

@kopf.timer(
    "superteam-a2a.io",
    "v1alpha1",
    "memories",
    interval=60.0,
    sharp=True,
    id="memory-reconciler",
)
async def reconcile_memory_timer(**kwargs: object) -> None:
    await memory_reconciler.tick(kwargs)
```

Kopf/`kubernetes-asyncio` 版本由 `uv.lock` 固定。启动顺序：加载 Settings → 初始化日志/metrics/tracer → backend health → 竞争 Lease → 注册 timer → readiness=true。停止顺序：readiness=false → 停止接收 handoff → 最多 30s drain → 放弃 Lease → flush telemetry。`interval=60.0` 不允许 values 覆盖；admission 50ms 仍归 L3-5。

### 11.5 OTel Collector + Argo CD

```yaml
- name: otel-collector
  image: otel/opentelemetry-collector-contrib:0.104.0
  args: ["--config=/conf/collector.yaml"]
  securityContext: {runAsNonRoot: true, allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, capabilities: {drop: [ALL]}}
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: {name: knowledge-service, namespace: argocd}
spec:
  project: superteam-a2a
  source: {repoURL: https://example.invalid/superteam-a2a.git, targetRevision: v0.2.0, path: helm/knowledge-service}
  destination: {server: https://kubernetes.default.svc, namespace: superteam-a2a}
  syncPolicy: {automated: {prune: true, selfHeal: true}}
```

Collector 仅接收 localhost OTLP 并 TLS 转发；其为基础设施进程，不改变“两业务 Python 进程”不变量。AppSet 用 dev/staging/prod list generator；prod 使用签名不可变 tag 与人工 promote。

### 11.6 CI 门禁顺序与证据

`schema-diff → lint/type/import-boundary → unit/property → conformance → integration/kind → image scan/sign → helm/promtool → E2E/PERF`。每步输出 JUnit、coverage XML、rendered manifests、SBOM、签名摘要与性能 JSON；后一步不得在前一步失败时运行。L4 前必须完成跨进程 transport spike，产出 ADR 或确认 UDS 实现，禁止只靠文档假设。

---

## 12. 验收清单（§A-§G · 30 条）

> ✅ 仅表示文件级 Spec 已定义；L4 实施必须用 §10 测试重新证明，不得把文档勾选当作运行结果。

| ID | 维度 | 验收项 | Spec |
|---|---|---|---|
| ACCEPT-MEM-001 | A 算法 | Memory 12 spec 字段与 v1alpha1 schema 唯一 | ✅ |
| ACCEPT-MEM-002 | A 算法 | decay 公式与 L2-4/ADR-0003 相同 | ✅ |
| ACCEPT-MEM-003 | A 算法 | reinforce 公式与边界相同 | ✅ |
| ACCEPT-MEM-004 | A 算法 | GC/promotion 仅纯函数判定 | ✅ |
| ACCEPT-MEM-005 | A 算法 | FakeClock 不使用真实 sleep | ✅ |
| ACCEPT-MEM-006 | B 边界异常 | 60s timer + Lease 单执行者 | ✅ |
| ACCEPT-MEM-007 | B 边界异常 | Lease 转让/drain <30s | ✅ |
| ACCEPT-MEM-008 | B 边界异常 | CAS conflict 最多重读一次 | ✅ |
| ACCEPT-MEM-009 | B 边界异常 | BackendHealth false 驱动 not-ready | ✅ |
| ACCEPT-MEM-010 | C 接口 | 4 A2A method envelope 不变 | ✅ |
| ACCEPT-MEM-011 | C 接口 | L3-5→L3-6 DTO immutable | ✅ |
| ACCEPT-MEM-012 | C 接口 | 取消/超时 rollback 且透传 | ✅ |
| ACCEPT-MEM-013 | C 接口 | 12 MEMORY_* name/code 零漂移 | ✅ |
| ACCEPT-MEM-014 | C 接口 | 封闭错误集新增必须 ADR | ✅ |
| ACCEPT-MEM-015 | C 接口 | 跨进程 transport 留 L4 spike | ✅ |
| ACCEPT-MEM-016 | D 可观测 | 25 指标经单一 `/metrics` 可见 | ✅ |
| ACCEPT-MEM-017 | D 可观测 | 8 structlog 字段固定 | ✅ |
| ACCEPT-MEM-018 | D 可观测 | 3 EventReason enum/幂等 | ✅ |
| ACCEPT-MEM-019 | D 可观测 | content/token/Secret 全脱敏 | ✅ |
| ACCEPT-MEM-020 | E 安全准入 | admission 50ms fail-closed | ✅ |
| ACCEPT-MEM-021 | E 安全准入 | KI/Memory 双向互斥 | ✅ |
| ACCEPT-MEM-022 | E 安全准入 | read/write 两个最小 Role 共享 SA | ✅ |
| ACCEPT-MEM-023 | E 安全准入 | 8081 不进入 Service/NetworkPolicy | ✅ |
| ACCEPT-MEM-024 | F 性能部署 | replicaCount=1 + Recreate | ✅ |
| ACCEPT-MEM-025 | F 性能部署 | 同 Pod 两个业务 Python 进程 | ✅ |
| ACCEPT-MEM-026 | F 性能部署 | 10K reconcile <50s 门禁 | ✅ |
| ACCEPT-MEM-027 | F 性能部署 | Docker/cert/Kopf/OTel/Argo 契约 | ✅ |
| ACCEPT-MEM-028 | G 基线 | 60/60 测试能力组有路径 | ✅ |
| ACCEPT-MEM-029 | G 基线 | 全包 80% / 关键模块 95% | ✅ |
| ACCEPT-MEM-030 | G 基线 | §0-§13 + 附录 A/B 可追踪 | ✅ |

**文件级结果**：30/30 已定义；运行级结果仍为 0/30，等待 L4。错误码 conformance、RBAC kind、transport spike、10K/50K 性能证据是升级实施基线时的硬门禁。

---

## 13. 开放问题（上游 22 项三层模式 + L3-6 5 项）

### 13.1 继承业务层 12 项

| ID | 问题 | 状态 | 当前决议 / L3-6 动作 |
|---|---|---|---|
| OPEN-L2-4-001 | AgentCard 兼容 | 🟡 | 每 minor 跑 conformance |
| OPEN-L2-4-002 | Kopf timer 差异 | 🟡 | L4 kind spike，60s 不可漂移 |
| OPEN-L2-4-003 | GIL/BM25 | ✅ | anyio bounded offload |
| OPEN-L2-4-004 | FakeClock/sleep | ✅ | Clock Protocol，禁真实 sleep |
| OPEN-L2-4-005 | 多集群 Issuer | 🟡 | L4 验证 |
| OPEN-L2-4-006 | 50ms admission | ✅ | L3-5 fail-closed |
| OPEN-L2-4-007 | 自动 scope-up | 🔵 | v0.5+ |
| OPEN-L2-4-008 | Vector DB | 🔵 | MemoryBackend Protocol 保留扩展 |
| OPEN-L2-4-009 | Memory 全文搜索 | 🔵 | v0.5+，当前仅多维过滤 |
| OPEN-L2-4-010 | Leader in-flight | ✅ | readiness off + drain 30s |
| OPEN-L2-4-011 | Multi-cluster | 🔵 | v1.0+ |
| OPEN-L2-4-012 | PII 加密 | 🔵 | 安全 ADR 后实施 |

### 13.2 继承 Spec 层 4 项

| ID | 问题 | 状态 | 当前决议 / L3-6 动作 |
|---|---|---|---|
| OPEN-L2-4-013 | Settings/env 优先级 | 🟡 | L4 Settings fixture 验证 |
| OPEN-L2-4-014 | 10K index 内存 | 🟡 | PERF artifact 验证 |
| OPEN-L2-4-015 | Kopf 50ms timeout | 🟡 | real webhook kind spike |
| OPEN-L2-4-016 | CRD/chart 顺序 | ✅ | Argo sync wave + install gate |

### 13.3 继承 Python 层 6 项

| ID | 问题 | 状态 | 当前决议 / L3-6 动作 |
|---|---|---|---|
| OPEN-L2-4-017 | Protocol/BaseModel | ✅ | Protocol 与 immutable DTO 分离 |
| OPEN-L2-4-018 | GIL/admission | ✅ | 短 I/O；CPU 有界 offload |
| OPEN-L2-4-019 | workspace 发布 | ✅ | 同步版本 + uv.lock |
| OPEN-L2-4-020 | freezegun/sleep | ✅ | FakeClock 注入 |
| OPEN-L2-4-021 | a2a-python Pydantic | 🟡 | upstream schema-diff 跟踪 |
| OPEN-L2-4-022 | alias/camelCase | ✅ | model_dump(by_alias=True) conformance |

上游 22 项按业务 12 + Spec 4 + Python 6 分层，已解决 11/22，收敛率 50%；L3-6 不改变该分母。

### 13.4 继承 L3-5 协调项

| ID | 问题 | 状态 | L3-6 处理 |
|---|---|---|---|
| OPEN-L3-5-003 | `_SCOPE_CACHE` LRU | 🟡 | 4096/TTL60s，L4 验证 |
| OPEN-L3-5-004 | BM25 rebuild | 🟡 | startup+watch，性能门禁 |
| OPEN-L3-5-006 | L3-6 readiness | 🟡 | BackendHealth + Lease + transport gate |
| OPEN-L3-5-010 | read/write RBAC | ✅ Spec | §9.5 双 Role；待 kind 运行验证 |

### 13.5 L3-6 独占 5 项

| ID | 问题 | 状态 | 决策窗口 | 退出条件 |
|---|---|---|---|---|
| OPEN-MEMORY-001 | 跨 container “function reference” transport | 🟡 | L4 前 | UDS/共享 runtime spike + ADR；保持 async DTO/异常/取消/幂等 |
| OPEN-MEMORY-002 | 水平扩展与同 Pod 单实例冲突 | 🔵 | v0.5+ | shard/Lease/一致性设计通过 |
| OPEN-MEMORY-003 | Vector DB backend 选型 | 🔵 | v0.5+ | Chroma/Qdrant/pgvector/Milvus 基准 + ADR |
| OPEN-MEMORY-004 | Memory PII 字段加密 | 🔵 | 安全评审 | KMS/key rotation/threat model ADR |
| OPEN-MEMORY-005 | Multi-cluster Memory 同步 | 🔵 | v1.0+ | conflict/sovereignty/retention 设计通过 |

`OPEN-MEMORY-001` 是 L4 开工前唯一架构门禁；其余不得偷偷扩入 v0.2 MVP。错误码扩展不是开放问题：它属于封闭兼容性变更，必须先走 L2-4 + ADR。

---

## 附录 A：跨模块引用清单（5 子表）

### A.1 L1 引用

| 来源 | 权威点 | L3-6 映射 |
|---|---|---|
| L1 Architecture §3.5.3 | Memory backend 边界 | §1/§2/§6 |
| L1 Architecture §4.3 C-7 | Knowledge/Memory 协调 | §4-§6 |
| L1 Spec §5.2.3 | `v1alpha1` Memory YAML | §3.3/§10.1 TEST-MEM-014 |

L1 §5.2.3 是 v1alpha1 唯一性校核源；L3-6 仅添加 Python alias/validator，不新增 wire 字段。schema diff 必须比较 required/default/enum/format/nullable，关闭 #65 “v1alpha1 唯一性”关注项。

### A.2 L2 引用

| 来源 | 权威点 | L3-6 映射 |
|---|---|---|
| L2-1 A2A Spec | JSON-RPC/A2AError envelope | §6/§8 |
| L2-2 Operator Spec | Kopf/Lease/RBAC 基线 | §4/§9/§11 |
| L2-3 Adapter Spec | public Protocol 边界 | §1.4；明确不依赖私有 Adapter |
| L2-4 Design | Python-first 决策/开放问题 | §1.3/§13 |
| L2-4 Spec §3.4 | Memory 12 字段 | §3 |
| L2-4 Spec §6.4-§7 | 4 method + 生命周期 | §4-§6 |
| L2-4 Spec §9.1 | 12 MEMORY_* name/code | §8 |
| L2-4 Spec §10-§15 | observability/deploy/test/open | §7/§9-§13 |

### A.3 ADR / Constitution 引用

| 来源 | 约束 | 证据 |
|---|---|---|
| ADR-0003 | decay/reinforce/GC/promotion 与互斥 | §4/§5/§12 |
| ADR-0005 §3.4 | Python module mapping | §2 |
| ADR-0005 §6.2 | 单业务实例 | §6/§9.2 |
| ADR-0005 §6.3 | CPU bounded offload | §7/§10.4 |
| ADR-0005 §10 | OTel/structlog/metrics | §7/§11.5 |
| ADR-0005 §13.1 | uv workspace | §2/§11 |
| Constitution §7 | 可观测与脱敏 | §7 |
| Constitution §9.7 | 质量门禁 | §10/§11.6 |
| Constitution §16.1 | 分层文档水位纪律 | M.2/M.4 |

### A.4 配套 L3 Spec

| 来源 | 协调点 | L3-6 映射 |
|---|---|---|
| L3-1 §3.4/§7 | Operator 协调、Helm/RBAC | §4/§9 |
| L3-2 §9/§10 | 15 指标与 A2A 错误 envelope | §7/§8 |
| L3-3 §3 | public Protocol 模式 | §5；不 import 私有实现 |
| L3-4 §3.2/§5 | 单实例 ASGI 参考 | §6/§9 |
| L3-5 §3.3/§5 | Memory DTO + admission owner | §3/§6 |
| **L3-5 §6.2** | **共享 Deployment function-reference 契约** | **§6.1-§6.4；8 个边界 ID 逐项反向一致** |
| L3-5 §8.2 | 12 MEMORY_* 镜像 | §8 conformance |
| L3-5 §9.9 | 共享 chart | §9 |

### A.5 归档基线

| 基线 | 用途 | 纪律 |
|---|---|---|
| pre-python L2/L3 Go baseline | wire 历史与差异核对 | 只读，不复制实现 idiom |
| L2-4 v0.1 Go review | 回归风险来源 | Python v0.2 权威优先 |
| ADR-0005 migration review | Python 映射理由 | 冲突时走 ADR，不回退 Go |

---

## 附录 B：ADR / Constitution 引用矩阵（5 子表）

### B.1 架构映射

| 决策 | Owner | 实现位置 | 测试/验收 |
|---|---|---|---|
| 同 Pod 双业务进程 | ADR-0005/L3-5 | §6.3/§9.2 | TEST-MEM-059 / ACCEPT-MEM-025 |
| 单实例 + Lease | L2-4 | §4/§9.9 | TEST-MEM-016~018 |
| MemoryBackend Protocol | L3-6 | §5.7 | TEST-MEM-042~050 |
| transport 待 spike | L3-6 OPEN-001 | §6.1/§9.2/§13.5 | TEST-MEM-053~056 |

### B.2 接口契约

| 契约 | 权威源 | L3-6 镜像 | 兼容门禁 |
|---|---|---|---|
| Memory 12 字段 | L1 §5.2.3 + L2-4 §3.4 | §3 | TEST-MEM-001~015 |
| 4 A2A method | L2-4 §6 | §6 | TEST-MEM-053~058 |
| 12 MEMORY_* | L2-4 §9.1 | §8 | TEST-MEM-051/060 |
| error passthrough | L3-5 §6.2 | §6.2/§8.2 | TEST-MEM-054 |

### B.3 可见性与业务边界

| phase | L3-5 可见/负责 | L3-6 可见/负责 | 禁止 |
|---|---|---|---|
| Admission phase | caller、visibility、scope chain、互斥、50ms | immutable admitted DTO、idempotency key | L3-6 重跑 admission |
| Lifecycle phase | query envelope、wire response | timer/Lease/backend/CAS/decay/reinforce/GC/promotion | L3-5 改生命周期公式 |
| Read path | 5 维矩阵过滤与对外结果 | backend snapshot/filter primitive | 绕过 L3-5 暴露 8081 |
| Write path | recordMemory + CR create | status patch + expired delete | L3-6 创建 KI/改 scope |

该“双 phase 可见性矩阵”关闭 #65 移交关注项：admission 与 lifecycle 分层，但共享同一 scope/visibility 语义，默认拒绝且不重复授权。

### B.4 安全

| 控制 | 规范 | L3-6 证据 |
|---|---|---|
| fail-closed | Constitution §6 / ADR-0003 | §6.4/§12 |
| 最小权限 | Constitution §6 | §9.5 read/write 双 Role |
| restricted Pod | Constitution §6 | §9.2/§11.2 |
| credential/content 脱敏 | Constitution §7 | §7.2/§7.3 |
| TLS/identity | ADR-0005 | §9.3/§11.3 |
| 供应链 | Constitution §9.7 | §11.1/§11.6 |

### B.5 可观测性与测试

| 维度 | 契约 | 门禁 |
|---|---|---|
| Metrics | 15 shared + 10 Memory；低基数 | OBS-MEM-UT-001~010 + IT-001 |
| Logs | 8 fixed fields + recursive redaction | unit snapshot + secret canary |
| Events | 3 fixed enum + idempotent dedupe | EVENT-MEM-UT-001~003 |
| Trace | handoff/backend/reconcile child spans | TEST-MEM-053~057 |
| Coverage | package ≥80%，critical ≥95% | CI coverage artifact |
| Performance | 10K reconcile <50s；50K filter p95<50ms；admission p99<50ms | TEST-MEM-030/052 + L3-5 PERF；固定 seed/机型/Python artifact |
| Deploy | 7 Helm groups + Docker/cert/Kopf/OTel/Argo | HELM-DEPLOY-001~007 + TEST-MEM-059 |

性能门禁必须在 PR artifact 明确样本规模、冷热状态、硬件、Python/依赖版本与 p50/p95/p99；这补全 L3-5-followup-5 对 tests row 的明确描述。

---

## 文档元数据与后续入口

### M.1 版本与状态

| 字段 | 值 |
|---|---|
| 版本 | **v0.2.0**（#64 骨架 + #65 §3-§6 + #66 §7-§13/附录 A/B + #67 独立评审通过 + #67.x 5 关注项同步修正 + §F 9 步跨文档同步） |
| 状态 | ✅ 评审通过 · 5 关注项全关闭 · 4 建议项移交 v0.2.1 / L4 实施 |
| 上游 | L1 Architecture v0.2.0 §3.5.3 + L1 Spec v0.2.0 §5.2.3 + L2-4 Spec v0.2.0 + L2-4 Design v0.2.0 + L3-5 §6.2 协调点 |
| 同级已通过 | L3-1 v0.2.0 (#56) + L3-2 v0.2.0 (#54) + L3-3 v0.2.0 (#58) + L3-4 v0.2.0 (#61) + L3-5 v0.2.0 (#63.5) |
| 评审报告 | [l3-6-memory-backend-spec-review.md](../../reviews/l3-6-memory-backend-spec-review.md) #67 · 525 行 / 67.9KB / §A-§Q 17 节 / 10 维度全 PASS / 5 关注项全关闭 / 4 建议项 |
| 当前变更边界 | §0-§13 + 附录 A/B 已完整；本次未实施 L4 代码、未运行 kind/PERF |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-27 #43 | L2-4 Knowledge/Memory Spec v0.2.0 评审通过 | L2-4 上游就绪 |
| 2026-07-29 #63.5 | L3-5 Knowledge Service Spec v0.2.0 评审通过 + 错误码 23 处漂移修正 | L3-5 上游就绪 |
| 2026-07-29 #64 | L3-6 Memory backend Spec v0.2-draft 骨架稿：头部 11 段 + §0-§13 占位 + 附录 A/B + M.1-M.6 | v0.2-draft 骨架稿 |
| 2026-07-29 #65 | §3-§6：Memory 12 字段、60s reconciler、4 纯函数、Clock/MemoryBackend Protocol、function-reference 边界 | 60 测试 ID 映射 + 错误码零漂移 |
| 2026-07-30 #66 | §7-§13 + 附录 A/B：10 指标、12 错误码、共享 Helm/RBAC 双 Role、60 ID、30 验收、22+5 开放问题、五项移交关注点闭环 | v0.2-draft-full 已补完，待 #67 独立评审 |
| **2026-07-30 #67** | **L3-6 独立评审 #67：10 维度全 PASS · 0 阻塞项 · 5 关注项全关闭 · 4 建议项移交 v0.2.1 / L4 实施** | **评审通过，5 关注项 / 4 建议项台账建立** |
| **2026-07-30 #67.x** | **5 关注项同步修正：TEST-MEM-051 集合相等静态断言 + §9.7 PrometheusRule 完整 YAML + HELM-DEPLOY-002 IPC/env/Recreate 补全 + role_write 补 admissionregistration/authn/authz + Clock.monotonic() 暴露到 handler 边界 + §F 9 步跨文档同步** | **v0.2.0 升级落地** |

### M.3 配套引用

- L3-1 Operator Core v0.2.0：`docs/spec/L3-file-specs/L3-operator-core.md`（§3.1 Agent Controller + §3.4 MemoryReconciler 协调 + §7 Helm 9 模板 + §7.3 RBAC + §9 验收清单）
- L3-2 A2A Core v0.2.0：`docs/spec/L3-file-specs/L3-a2a-core.md`（§5 ASGI server + §6 A2AClient + §9 15 Prometheus 指标 + §10 24 错误码）
- L3-3 Adapter SDK v0.2.0：`docs/spec/L3-file-specs/L3-adapter-sdk.md`（§3 FrameworkAdapter Protocol · **L3-6 不依赖**）
- L3-4 Hello Agent v0.2.0：`docs/spec/L3-file-specs/L3-hello-agent.md`（§3.2 HelloAgentExecutor + §5 ASGI + §6.9 25 ID 测试 · 同模式 Card-driven 单实例参考实现）
- **L3-5 Knowledge Service v0.2.0：`docs/spec/L3-file-specs/L3-knowledge-service.md`（**关键引用** · §3.3 Memory 5+5 简化 schema + §5 admission 互斥 + **§6.2 共享 Deployment in-process function reference 契约 · line 1488-1577** + §9.9 共享 Helm chart 段落 + §8.2 12 MEMORY_* 错误码权威名）**
- L2-4 Knowledge/Memory Spec v0.2.0：`docs/spec/L2-module-specs/L2-knowledge-memory.md`（Memory CRD 12 spec 字段 + 4 A2A method + 4 级 scope + 5 维矩阵 + admission 互斥 + MemoryReconciler 60s kopf.timer + 60 测试 ID + 22 开放问题 · **§3.4 Memory CRD 12 字段完整版 + §6.4-§6.5 A2A method + §7 MemoryReconciler + §9.1 22 错误码权威名（**L3-6 §8 100% wire 一致**）**）
- L2-4 Knowledge/Memory Design v0.2.0：`docs/design/L2-modules/L2-knowledge-memory.md`（5 项 Python 化决策 + 9 维度 Go→Python 对照表 + 22 开放问题）
- L1 Architecture v0.2.0：`docs/design/L1-architecture.md` §3.5.3 + §4.3 C-7
- L1 Spec v0.2.0：`docs/spec/L1-system-spec.md` §5.2.3 Memory YAML 示例
- ADR-0003 Memory 设计：`docs/adr/0003-memory-design.md`（§3 Memory CRD schema + §4.1 decay 公式 + §5 admission 互斥 + §6 MemoryReconciler）
- ADR-0005 Python-first：`docs/adr/0005-python-first-technology-stack.md`（§3.4 Memory backend 模块映射 + §6.2 单进程原则 + §6.3 CPU offload + §10 structlog + §13.1 uv workspace）
- Constitution v0.5.0：`CONSTITUTION.md`（§16.1 水位纪律 + §16.1-application 实际水位判断）

### M.4 下次会话固定入口

1. **L4 前架构门禁**：关闭 OPEN-MEMORY-001，完成跨 container UDS/共享 runtime transport spike 并记录 ADR；kind 验证 read/write 双 Role（含 admissionregistration/authentication/authorization 扩展）、webhook 50ms、Lease/readiness。
2. **L3-5 v0.2.1 微同步**：将 §9.5 read-only Role 与本 Spec §9.5 write Role 对齐（确认 admissionregistration/authn/authz 不进入 read-only Role）；附录 B B.5 明确性能 artifact 行。
3. **v0.2.1 微同步**：关注项台账 4 建议项（§M-2.1 BackendBindingSpec 派生映射 / §M-2.2 收敛率说明 / §M-2.3 9 关键模块覆盖率映射 / §M-2.4 EventReason 白名单继承说明）。
4. **L4 实施启动**：Phase 1 MVP Core 实施层落地（L3-5-followup-2 性能门禁验证 / L3-5-followup-3 kind webhook 真实环境验证 / L3-5-followup-4 _SCOPE_CACHE / BM25 rebuild 策略）。
5. **#67.x 关注项修正**（已落地于 v0.2.0 PR）：TEST-MEM-051 集合相等静态断言 / §9.7 PrometheusRule 完整 YAML / HELM-DEPLOY-002 IPC+env+Recreate 描述 / role_write admissionregistration+authn+authz / Clock.monotonic() 暴露到 handler 边界。

### M.5 关注项台账（v0.2.0 评审 + 升级落地后）

| 编号 | 关注项 | 状态 | 解决位置 | 移交 |
|---|---|---|---|---|
| L3-6-followup-1 | TEST-MEM-051 集合相等静态断言（与 L2-4 §9.1 + L3-5 §8.2 集合相等；CI 强制） | ✅ 关闭 | §8.1 + §10.1 TEST-MEM-051 + §11.6 CI | — |
| L3-6-followup-2 | §9.7 PrometheusRule 完整 YAML 渲染（8 alert + labels/annotations/runbook） | ✅ 关闭 | §9.7 | — |
| L3-6-followup-3 | HELM-DEPLOY-002 描述补 IPC volume + env 三项 + Recreate + `*restricted` anchor | ✅ 关闭 | §9.10 + §9.2 | — |
| L3-6-followup-4 | role_write 补 admissionregistration.k8s.io / authentication.k8s.io / authorization.k8s.io 规则 | ✅ 关闭 | §9.5 role_write.yaml | kind 验证移交 L4 |
| L3-6-followup-5 | Clock.monotonic() 暴露到 record_memory_async / query_memory_async handler 边界（InProcessContext.clock） | ✅ 关闭 | §6.1 + §6.4 | — |

**建议项（v0.2.1 微同步）**：
- §M-2.1 BackendBindingSpec 8 字段与 L3-5 §3.3 Memory 5+5 简化 schema 派生映射表
- §M-2.2 收敛率 11/31 = 35% 明确算法说明
- §M-2.3 9 关键模块覆盖率与 60 测试 ID 映射表
- §M-2.4 EventReason 3 枚举白名单继承 L3-5 §7.3 + L3-1 §7.1.5 引用

### M.6 文档元数据

- **创建日期**：2026-07-29 #64
- **最后更新**：2026-07-30 #67.x（v0.2.0 升级 + 5 关注项全关闭 + §F 9 步跨文档同步）
- **下次更新**：L4 前架构门禁（OPEN-MEMORY-001 transport spike）/ v0.2.1 微同步（4 建议项）
- **依赖完整性**：上游 L1 v0.2.0 + L2-4 v0.2.0 + L3-1/2/3/4/5 v0.2.0 全部就绪
- **下游影响**：L4 实施 Memory backend 工程师 + RBAC write Role 含 admissionregistration/authn/authz（L3-6-followup-4 kind 验证）+ Leader Election 实施 + 性能门禁验证（L3-5-followup-2）+ _SCOPE_CACHE / BM25 rebuild 策略（L3-5-followup-4）+ 跨 container transport spike（OPEN-MEMORY-001）
- **本次变更摘要**：v0.2-draft-full → v0.2.0；头部 4 处微同步（版本/状态/配套 Review 引用/supersede 描述）；M.1 状态 ✅ + 评审引用 #67；M.2 增 #67 + #67.x 两行；M.4 重写为 L4 前门禁 + v0.2.1 微同步 + 评审修正历史；M.5 关注项台账 5 项 L3-6-followup-1~5 全部 ✅ + 4 建议项 v0.2.1；M.6 更新；§8.1 TEST-MEM-051 静态断言代码块新增；§9.5 role_write 补 3 条规则；§9.7 完整 PrometheusRule YAML；§9.10 HELM-DEPLOY-002 描述补全；§6.1 Clock 边界 + InProcessContext.clock 显式；§6.4 admission 示例改用 `monotonic_deadline`

---

> **签署**：本 L3-6 Memory backend 文件级 Spec Python v0.2.0 由 #64 起草、#65 补完 §3-§6、#66 补完 §7-§13 与附录 A/B、#67 独立评审通过（10 维度全 PASS / 0 阻塞 / 5 关注项 / 4 建议项）、#67.x 5 关注项同步修正（TEST-MEM-051 集合相等静态断言 + §9.7 PrometheusRule 完整 YAML + HELM-DEPLOY-002 描述补全 + role_write 扩展 admissionregistration/authn/authz + Clock.monotonic() 暴露到 handler 边界）+ §F 9 步跨文档同步。依据 [L1 Architecture v0.2.0 §3.5.3 + §4.3 C-7](../../design/L1-architecture.md)、[L1 Spec v0.2.0 §5.2.3 Memory YAML](../../spec/L1-system-spec.md)、[L2-4 Knowledge/Memory Spec v0.2.0 §3-§15](../../spec/L2-module-specs/L2-knowledge-memory.md)、[L2-4 Knowledge/Memory Design v0.2.0 §3-§14](../../design/L2-modules/L2-knowledge-memory.md)、[L3-1 Operator Core v0.2.0 §3.4 + §7](../../spec/L3-file-specs/L3-operator-core.md)、[L3-2 A2A Core v0.2.0 §5 + §6 + §9 + §10](../../spec/L3-file-specs/L3-a2a-core.md)、[L3-3 Adapter SDK v0.2.0 §3](../../spec/L3-file-specs/L3-adapter-sdk.md)、[L3-4 Hello Agent v0.2.0 §3.2 + §5](../../spec/L3-file-specs/L3-hello-agent.md)、**[L3-5 Knowledge Service v0.2.0 §3.3 Memory 5+5 简化 schema + §5 admission + §6.2 共享 Deployment 协调点（line 1488-1577）+ §9.9 共享 Helm chart 段落 + §8.2 12 MEMORY_* 错误码权威名](../../spec/L3-file-specs/L3-knowledge-service.md)**、[ADR-0003 Memory 设计](../../adr/0003-memory-design.md)、[ADR-0005 Python-first §3.4 + §6.2 + §6.3 + §10 + §13.1](../../adr/0005-python-first-technology-stack.md) 与 Constitution v0.5.0 编写。**当前 v0.2.0 已具备进入 L4 实施（Phase 1 MVP Core）的条件；L4 前架构门禁 OPEN-MEMORY-001（跨 container transport spike + ADR）必须先关闭，4 建议项（§M-2.1~2.4）移交 v0.2.1 微同步**。
