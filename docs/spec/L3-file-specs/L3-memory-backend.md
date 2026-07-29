# L3 文件级 Spec：Memory backend（Card-driven Memory 服务 · Python-first · 同 Pod 第二 Python 进程 · #64 起草）

> **模块定位**：C-7 Memory backend（Card-driven Memory 服务 · v0.1 · 同 Pod 第二 Python 进程 / 单 Uvicorn worker / 端口 8081 cluster-internal / 与 L3-5 Knowledge Service 共享 Deployment / 独占 MemoryReconciler 60s @kopf.timer + Leader Election Lease + 4 纯函数 decay/reinforce/GC/promotion + Clock Protocol + BM25 启动期全量重建）
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-7（Memory backend，见 L1 Architecture §3.5.3 + §4.3）
> **代码位置**：
> - **CRD types**：`packages/memory/src/supteam_a2a/memory/apis/v1alpha1/`（Memory schema Pydantic v2 12 spec 字段完整版 + 5 维 visibility 矩阵复用 + 4 级 scope 复用）
> - **A2A/Business 部署**：`services/memory-backend/src/supteam_a2a/memory_backend/`（ASGI 单进程 + 4 纯函数 + 60s kopf.timer + Leader Election + Clock Protocol + BM25 启动期全量重建 + Helm 7 模板与 L3-5 共享）
> - **部署共享**：`services/memory-backend/` 与 `services/knowledge-service/` 共享同 Deployment（同 Pod 内两个独立 Python 进程；详见 L3-5 §6.2 + 本 Spec §6）
> - **uv workspace 布局**：ADR-0005 §13.1
> **版本**：**v0.2-draft-full**（2026-07-29 #64 骨架；目标 #65 §3-§6 补完 + #66 §7-§13 + 附录 A/B + #67 独立评审 → 升级 v0.2.0）
> **状态**：🟡 **v0.2-draft-full 进行中**（头部 11 段 + §0 + §1 模块使命 + 5 项关键不变量 + 5 项 Python 化决策 D-1~D-5 + 28 文件清单 + §2 Python 包结构 + §3-§13 占位章节结构 + 附录 A/B 5 子表 + 文档元数据 M.1-M.6；§3-§10 + 完整附录 A/B 待 #65/#66 Subagent 补完；§6 in-process 契约 + §8 错误码（**详见 L2-4 v0.2.0 §9.1 权威名**） + §9 Helm 共享 chart + L3-5-followup-1 RBAC 拆 write Role 为 L3-6 关键新增点）
> **supersede / 归档标记（2026-07-29）**：本 v0.2-draft Spec 文档**仅 supersede Go reconciler / Go BM25 sync.Map / Go controller-runtime Reconcile() / Go k8s.io/utils/clock 实现条款**；wire contract（Memory CRD 12 spec 字段 / 4 纯函数公式 / 5 维 visibility 矩阵 / 4 级 scope 继承 / Leader Election Lease / 60s 周期 / decay 公式 `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` / 12 个 MEMORY_* 错误码 / Helm values）与 L2-4 v0.2.0 Spec 业务语义**完全继续有效**。L2-4 v0.1.0 Go baseline 已在 L2-4 Spec v0.2.0 起草时覆盖丢失（与 L2-1/L2-3/L3-1/L3-2/L3-3/L3-4/L3-5 同模式；建议 #64.x 后续会话追溯 v0.1.0 Go 归档登记）
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.5.3 + §4.3 C-7 + ADR-0005 §3.4 + §6.2 + §6.3 + §10 + §13.1 + L2-4 v0.2.0 Spec §7 MemoryReconciler + §6.6 共享 Deployment + L2-4 v0.2.0 Design §3-§14，Memory CRD Go struct → **Pydantic v2 BaseModel + Field(...) + populate_by_name + alias（与 L3-5 §3.3 5+5 简化版 wire 一致的 12 spec 字段完整版）**；Go controller-runtime Reconcile() → **Kopf `@kopf.timer(interval=60.0, id="memory-reconciler")` + 独立 async reconciler service + Leader Election via coordination.k8s.io/v1 Lease（renew 失败 3 次让位 + 30s grace period）**；Go sync.Map BM25 → **Python `dict[str, set[str]]` + anyio.to_thread.run_sync 启动期全量重建 + watch 增量**；Go k8s.io/utils/clock → **`Clock` Protocol + `RealClock` + `FakeClock`（测试用 freezegun 替代）**；Go 4 纯函数（apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion）→ **Python 同步 pure function + async wrapper（lru_cache 缓存 + 不阻塞 event loop）**；recordMemory/queryMemory → **Python ASGI handler + L3-5 in-process call 委托（共享 Deployment 同 Pod 内 Python import，无 HTTP loopback）**
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
> **配套 Review**：待 #67 独立评审（目标 550-650 行 / 50-60KB / §A-§Q 17 节 / 10 维度全 PASS）

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
- **L3-6 与 L3-5 共享 Deployment**：同 Pod 内两个独立 Python 进程（memory-backend port 8081 cluster-internal + knowledge-service port 8080 对外）；共享 Helm chart / Service / ServiceMonitor / NetworkPolicy；进程间通过 Python in-process function reference — 详见 §6（**与 L3-5 §6.2 严格一致 · line 1488-1577 协调点**）
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

## 3. Memory CRD（Pydantic v2 12 spec 字段完整版 · wire contract 与 L2-4 v0.2.0 §3.4 + L3-5 §3.3 完全一致）

> **说明**：本节在 #65 Subagent 1 补完完整 Pydantic v2 schema 代码（目标 ~300 行 Pydantic + ~100 行 wire 同步矩阵 + ~80 行测试 ID）。**本骨架稿仅占位并明确关键 wire 引用 + 5 项 wire contract 永久不变**，避免 §16.1 50% 临界。

### 3.1 5 项 wire contract 永久不变（与 L3-5 §3 顶部 + L2-4 v0.2.0 §3 完全一致）

1. **时间字段**：`AwareDatetime` UTC（业务层 `datetime.now(UTC)`）；L2-4 §3.7 锁定
2. **枚举用 `StrEnum`**：与 K8s API server 字符串值兼容
3. **不可变 value object**：`frozen=True`（AgentReference / SourceKnowledgeRef / MemoryVisibility 枚举值）
4. **`populate_by_name=True` + `alias`**：实现 camelCase ↔ snake_case 单向映射
5. **`extra="forbid"`**：与 K8s API server strict 校验一致；L2-4 §3.7 锁定

**详细 Pydantic v2 schema 代码、wire 同步矩阵、衰减公式、关联测试 ID 在 #65 Subagent 1 补完（约 300 行 Pydantic + 100 行 wire 同步矩阵 + 80 行测试 ID）**。

### 3.2 Memory CRD 关键引用清单

| 字段 | 引用源 | 备注 |
|------|--------|------|
| 12 spec 字段完整版 | L2-4 v0.2.0 §3.4 (`L 601-686`) | 与 L3-5 §3.3 5+5 简化版 wire 一致 |
| 7 status 字段 | L2-4 v0.2.0 §3.4 status 子资源 (`L 663-674`) | phase / conditions / last_decayed_at / last_reinforced_at / effective_confidence / eligible_for_promotion / observed_generation |
| MemoryPhase 5 态 | L2-4 v0.2.0 §3.4 (`L 614-620`) | ACTIVE / DECAYING / PROMOTABLE / EXPIRED / ERROR |
| MemoryVisibility 3 枚举 | L2-4 v0.2.0 §3.4 (`L 623-627`) | scope-only / scope-and-children / agent-private |
| GCState 4 态 | L3-5 v0.2.0 §3.3 (`L 680-686`) | NONE / PENDING / CLEANED / KEPT |
| 5 维 visibility 矩阵 | L2-4 v0.2.0 §4.5 (`L 877-883`) | 4 scope × 3 visibility + agent-private 短路 |
| 衰减公式 | L2-4 v0.2.0 §7.3 + ADR-0003 §4.1 | `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` |
| wire 同步矩阵 | L2-4 v0.2.0 §3.5 (`L 688-699`) | v0.1.0 Go baseline → v0.2 Python wire 兼容性逐字段 |

### 3.3-§3.5 占位（#65 Subagent 1 补完）

- §3.3 MemorySpec 12 字段 Pydantic v2 schema（target ~120 行）
- §3.4 MemoryStatus 7 字段 Pydantic v2 schema（target ~80 行）
- §3.5 Memory 顶层 + ObjectMeta + wire 同步矩阵 5 列（target ~100 行）+ 衰减公式 + 28 测试 ID

---

## 4. MemoryReconciler 60s 周期 + Leader Election（Kopf @kopf.timer + coordination.k8s.io/v1 Lease）

> **说明**：本节在 #65 Subagent 1 补完完整 Python 代码（目标 ~200 行 timer + lease + 退避策略 + 6 测试 ID）。本骨架稿仅占位 + 关键引用。

### 4.1 60s @kopf.timer 周期（继承 L2-4 v0.2.0 §6.6 + L3-1 §3.4 + ADR-0003 §6）

```python
# 骨架占位（#65 补完）
@kopf.timer(interval=60.0, id="memory-reconciler")
async def memory_reconciler_timer(**kwargs):
    """60s 周期触发；调用 MemoryReconcilerService.reconcile_all() 全流程。"""
    ...
```

**关键不变量**：
- `interval=60.0` 永久不变（与 L2-4 Spec v0.2.0 §6.6 + L3-1 §3.4 严格一致）
- `id="memory-reconciler"` 永久不变（与 kopf 框架绑定）
- 每次触发调用 `MemoryReconcilerService.reconcile_all()` 同步全流程（不并发避免分裂脑）

### 4.2 Leader Election Lease（`coordination.k8s.io/v1` Lease · 30s grace + renew 失败 3 次让位）

```python
# 骨架占位（#65 补完）
class LeaderElectionLeaseClient:
    """30s grace period + renew 失败 3 次让位。
    Lease namespace: superteam-a2a
    Lease name: memory-reconciler-leader
    holderIdentity: <pod_name>
    leaseDurationSeconds: 15
    renewDeadlineSeconds: 10
    retryPeriodSeconds: 5
    """
    ...
```

**关键不变量**（L2-4 v0.2.0 §7.6 `L 2225-2297`）：
- leaseDurationSeconds: 15（< 60s 周期 · 保证 leader 在 60s 周期内持锁）
- renewDeadlineSeconds: 10（rennew 失败后 10s 内让位）
- retryPeriodSeconds: 5（acquire 间隔）
- 失败 3 次连续 renew → release lease + acquire（让位）
- v0.1 仅 1 实例 + 单 leader（L3-5 同 Pod 部署约束）

### 4.3 退避策略 + 错误处理

| 异常类型 | 退避策略 | 行为 |
|----------|----------|------|
| K8s API 5xx | 指数退避 1s/2s/4s/8s（Tenacity · max 4 次） | 重试 |
| K8s API 4xx | 立即失败 | 记录 structlog + 跳过 |
| admission timeout (50ms) | 100/200/400ms 退避（Tenacity · max 3 次） | 重试（与 §5 admission 一致） |
| Leader 失锁 | 立即退出 reconcile | 下个周期重试 |
| 4 纯函数异常（除零等） | 立即失败 + 标记 status.phase=ERROR | 记录 K8s Event |

### 4.4 占位

- §4.4 完整 timer 实现 + reconcile_all 全流程（target ~120 行）+ 6 测试 ID · 在 #65 补完

---

## 5. 4 纯函数 + Clock Protocol（pure function + async wrapper + freezegun）

> **说明**：本节在 #65 Subagent 1 补完完整 Python 代码（目标 ~250 行 4 纯函数 + ~80 行 Clock Protocol + ~50 行 MemoryBackend 抽象层 + ~20 测试 ID）。本骨架稿仅占位 + 关键公式 + 不变量。

### 5.1 Clock Protocol（继承 L2-4 v0.2.0 §7.1 + ADR-0003 §4.2 + L3-5 D-4）

```python
# 骨架占位（#65 补完）
from typing import Protocol, runtime_checkable
from datetime import datetime, timezone


@runtime_checkable
class Clock(Protocol):
    """Clock Protocol · 业务层时间源（ADR-0003 §4.2 + L2-4 §7.1）。"""
    def now(self) -> datetime: ...
    def advance(self, seconds: float) -> None: ...  # 仅 FakeClock


class RealClock:
    """RealClock · datetime.now(UTC)（生产）。"""
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FakeClock:
    """FakeClock · 测试用；初始时间可调（freezegun 替代或显式 advance）。"""
    def __init__(self, start: datetime | None = None) -> None:
        self._current = start or datetime(2026, 1, 1, tzinfo=timezone.utc)
    def now(self) -> datetime:
        return self._current
    def advance(self, seconds: float) -> None:
        from datetime import timedelta
        self._current += timedelta(seconds=seconds)
```

### 5.2-§5.7 4 纯函数 + MemoryBackend 抽象层（#65 Subagent 1 补完）

| 子节 | 函数 | 公式 / 契约 | 测试 ID 前缀 |
|------|------|-------------|--------------|
| §5.2 | FakeClock 单元测试 | `test_fake_clock_advance_seconds` | MEM-CLOCK-UT |
| §5.3 | `apply_decay(confidence, elapsed_days, decay_days)` | `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` | MEM-DECAY-UT/TZ |
| §5.4 | `apply_reinforce(memory, now, clock)` | `reinforced_count += 1; last_reinforced_at = now`（**1h 频次节流**：若距 last_reinforced_at < 1h 则拒绝） | MEM-REINFORCE-UT |
| §5.5 | `gc_expired(memories, clock)` | 过滤 `effective_confidence < 0.01` 的 Memory → `gc_state=Pending` | MEM-GC-UT/TZ |
| §5.6 | `is_eligible_for_promotion(memory)` | **4 条件**（L2-4 §7.3 promotion.py）：`effective_confidence > 0.7 + reinforced_count > 10 + last_reinforced_at < 7d + visibility in {agent-private, scope-and-children}` | MEM-PROMOTE-UT |
| **§5.7** | **`MemoryBackend` Protocol**（**L3-6 核心新增点**） | `Protocol[put_memory / get_memory / list_memories / delete_memory / patch_status]` + `InMemoryBackend` 默认实现 + `CRDStore` 适配器（K8s API）+ `BM25Backend`（v0.5+ 预留 · OPEN-L2-4-008） | MEM-BACKEND-UT/CF |

**§5.7 MemoryBackend 抽象层关键设计**（避免 L2-4 v0.2.0 §8.5 留 OPEN-L2-4-008 推迟到 v0.5+）：
- v0.1 默认实现 `InMemoryBackend`（dict 存储 + 5 维矩阵过滤）— 与 L2-4 "CRD 即存储" 语义兼容
- v0.1 适配器 `CRDStore`（K8s API 异步读写）— 完整实现 v0.2 业务
- v0.5+ 预留 `BM25Backend`（OPEN-L2-4-008 + OPEN-L2-4-009）— `search.backend=vector` + `Memory.count > 10K` 触发
- 接口契约（Protocol 抽象方法）：
  ```python
  @runtime_checkable
  class MemoryBackend(Protocol):
      async def put_memory(self, mem: Memory) -> MemoryRecordResult: ...
      async def get_memory(self, name: str, namespace: str) -> Memory | None: ...
      async def list_memories(self, query: QueryMemoryRequest) -> list[MemorySummary]: ...
      async def delete_memory(self, name: str, namespace: str) -> None: ...
      async def patch_status(self, name: str, namespace: str, status: MemoryStatus) -> None: ...
  ```

---

## 6. in-process function reference 契约（与 L3-5 §6.2 严格一致 · line 1488-1577 协调点）

> **说明**：本节在 #65 Subagent 1 补完完整 Python Protocol 代码（target ~120 行 + 3 项规则 + 8 边界测试 ID）。本骨架稿仅占位 + 关键引用 + 3 项规则。

### 6.1 in-process function reference 契约（**与 L3-5 §6.2 严格一致**）

```python
# 骨架占位（#65 补完；与 L3-5 §6.2 line 1520-1545 严格镜像）
from typing import Protocol, runtime_checkable
from superteam_a2a.memory.apis.v1alpha1.memory import Memory
from superteam_a2a.memory_backend.pure_functions.memory_backend import (
    MemoryRecordResult, QueryMemoryRequest, QueryMemoryResult,
)


@runtime_checkable
class MemoryBackendInProcessService(Protocol):
    """L3-6 export 的 in-process service Protocol（L3-5 调用契约）。
    **与 L3-5 §6.2 line 1530-1533 严格镜像**。
    """
    async def record_memory_async(self, mem: Memory) -> MemoryRecordResult: ...
    async def query_memory_async(self, req: QueryMemoryRequest) -> QueryMemoryResult: ...


# L3-6 端 export：
#   from services.memory_backend.src.supteam_a2a.memory_backend.svc import (
#       record_memory_async, query_memory_async,
#   )
```

### 6.2 调用契约 3 项规则（**与 L3-5 §6.2 line 1547-1550 完全一致**）

1. **`async def` 全异步**：所有 L3-6 export 函数均为 `async def`；L3-5 调用必须 `await`
2. **异常透传**：L3-6 抛出的 `A2AError` / `AdmissionTimeoutError` 等异常直接传播到 L3-5；L3-5 **不 catch 并改 error code**（避免双重映射）
3. **不走 HTTP**：L3-5 ↔ L3-6 仅同 Pod 内 Python in-process call（共享 emptyDir 卷挂载 `/app/memory_backend` 路径）；**禁止 HTTP loopback**

### 6.3 BM25 启动期全量重建 + watch 增量（与 L3-5 §4.2 bm25_index 共享存储）

- **启动期**：`anyio.to_thread.run_sync(MemoryReconcilerService.bm25_rebuild_all)` — 全量 list Memory CRD + 构建 `dict[str, set[str]]` 倒排索引
- **watch 增量**：K8s watch Memory CRD events（add/update/delete）→ 增量更新 BM25 dict
- **共享存储**：L3-5 §4.2 `bm25_index.search` 与 L3-6 `bm25_index.rebuild` 共享 in-memory dict（同 Pod 进程间 Python 对象引用）
- **线程安全**：`asyncio.Lock` 保护 BM25 dict 读写（避免 split-brain）

### 6.4 8 项 L3-5 ↔ L3-6 边界测试 ID（**与 L3-5 §6.2 line 1561-1568 严格镜像**）

- `MTLS-IT-001` 共享 Deployment 双 Container 启动顺序（knowledge-service 等待 memory-backend 就绪）
- `MTLS-IT-002` in-process function reference 调用契约（async def + exception propagation）
- `MTLS-IT-003` 共享 ServiceMonitor scrape（port 8080 · interval 30s · 15+10 指标）
- `MTLS-IT-004` 共享 RBAC ClusterRole 拆分（read-only Role + write Role 共享 SA）
- `MTLS-IT-005` 共享 NetworkPolicy ingress/egress（operator namespace + cert-manager）
- `E2E-WIRE-IT-001` wire contract 端到端（CRD apply → L3-6 in-process → L3-5 A2A response · wire 一致性）
- `E2E-WIRE-IT-002` recordMemory 委托链（recordMemory A2A call → L3-5 admission → L3-6 record_memory_async → K8s API apply → effective_confidence 计算 → response）
- `E2E-WIRE-IT-003` queryMemory 委托链（queryMemory A2A call → L3-5 min_confidence 默认 0.01 → L3-6 query_memory_async → 5 维 visibility 过滤 → effective_confidence 阈值过滤 → response）

---

## 7. Observability（10 Memory 业务指标 + structlog 8 字段 + K8s Events）

> **说明**：本节在 #66 Subagent 2 补完完整 10 指标表 + structlog Pydantic 模型 + 2-3 MEMORY_* EventReason（target ~200 行）。本骨架稿仅占位 + 关键引用。

### 7.1 10 指标分布（**复用 L3-2 §9 15 指标 + 新增 10 Memory 业务指标** = 25 总指标）

| 类别 | 数量 | 命名规范 | 落地位置 |
|------|----:|----------|----------|
| **复用 L3-2 11 A2A 指标** | 11 | `superteam_a2a_<noun>` | L3-2 §9.1（继承） |
| **复用 L3-2 4 Python runtime** | 4 | `python_*` / `process_*` | L3-2 §9.2（继承） |
| **L3-6 独占 10 Memory 业务指标** | 10 | `superteam_memory_*` | L3-6 §7.1（#66 补完） |
| **总计** | **25** | — | — |

**L3-6 独占 10 指标预览**（**#66 补完完整 labels/buckets/help**）：
- `superteam_memory_reconcile_total` (Counter, `phase,result`)
- `superteam_memory_reconcile_duration_seconds` (Histogram, `phase`, `.005,...,10`)
- `superteam_memory_decay_applied_total` (Counter, `phase`)
- `superteam_memory_reinforce_total` (Counter, `result`)
- `superteam_memory_gc_cleaned_total` (Counter, `gc_state`)
- `superteam_memory_promotion_eligible_total` (Counter, `visibility`)
- `superteam_memory_bm25_index_size` (Gauge, `scope_level`)
- `superteam_memory_admission_duration_seconds` (Histogram, `validator`, `.001,...,5`)
- `superteam_memory_in_process_call_total` (Counter, `method,result`)
- `superteam_memory_rate_limited_total` (Counter, `service_account`)

### 7.2 structlog 8 必含字段（**与 L3-2 §9.3 + L3-5 §7.2 完全一致**）

- timestamp / level / service=`memory-backend` / trace_id / span_id / request_id / agent_id / event
- 9 项脱敏白名单 + 1024 字符截断（与 L3-5 §7.2 line 1637 镜像）

### 7.3 2-3 MEMORY_* EventReason（**L3-6 独占新增 · #66 补完**）

- `MEMORY_CONFLICT_DETECTED` (Normal, L3-5 §7.3 共享) — 5 维矩阵冲突
- `MEMORY_CONFLICT_RESOLVED` (Normal, L3-5 §7.3 共享) — 冲突解决
- `MEMORY_DECAY_APPLIED` (Normal, L3-6 独占新增) — 60s 周期 decay 应用
- `MEMORY_GC_CLEANED` (Warning, L3-6 独占新增) — GC 清理
- `MEMORY_PROMOTED` (Normal, L3-6 独占新增 · v0.5+ 触发) — promotion 到 KnowledgeItem

---

## 8. 错误码（12 个 MEMORY_* · **与 L2-4 v0.2.0 §9.1 权威名 100% 一致 · 零漂移**）

> **说明**：本节在 #66 Subagent 2 补完完整 IntEnum + 表格 + Retryable 矩阵（target ~120 行）。**本骨架稿仅占位 + 关键 wire 引用，**不写具体错误码名**以避免 L3-5 #63.5.1 23 处漂移历史重演**；#66 Subagent 2 必须直接 import L2-4 v0.2.0 §9.1 权威表。

### 8.1 关键 wire 引用（**防漂移核心**）

**12 个 MEMORY_* 错误码 JSON-RPC code 范围 `-32101 ~ -32112`**（**与 L2-4 v0.2.0 §9.1 权威名 100% 一致**）：

| name（**权威**） | code | HTTP | Retryable | message 模板（权威） |
|------|---:|---:|---|---|
| `MEMORY_SCOPE_NOT_FOUND` | -32101 | 404 | No | `Memory scope {scope_ref_name} was not found` |
| `MEMORY_INVALID_CONTENT` | -32102 | 400 | No | `Memory content exceeds 20 keys (got {actual})` |
| `MEMORY_FORBIDDEN` | -32103 | 403 | No | `Memory write denied: {reason}` |
| `MEMORY_RATE_LIMIT` | -32104 | 429 | Yes | `Memory write rate exceeded 60/min for SA {service_account}` |
| `MEMORY_INTERNAL_ERROR` | -32105 | 500 | Yes | `Memory backend internal error` |
| `MEMORY_QUERY_TOO_BROAD` | -32106 | 400 | No | `Memory query with scope=industry requires tag/confidence filter` |
| `MEMORY_SOURCE_KI_NOT_FOUND` | -32107 | 400 | No | `Memory sourceKnowledgeRef.name {name} was not found` |
| `MEMORY_SOURCE_KI_SCOPE_MISMATCH` | -32108 | 400 | No | `Memory source KI scopeRef {ki_scope} != Memory scopeRef {mem_scope}` |
| `MEMORY_AGENT_PRIVATE_REQUIRES_NAME` | -32109 | 400 | No | `Memory agent-private requires agentRef.name (got "")` |
| `MEMORY_DECAY_DAYS_EXCEEDED` | -32110 | 400 | No | `Memory decayDays {decay_days} exceeds 3650` |
| `MEMORY_AGENT_NOT_FOUND` | -32111 | 400 | No | `Memory agentRef.name {agent} (SA) was not found` |
| **`MEMORY_ADMISSION_TIMEOUT`** | **-32112** | 503 | Yes | `Memory admission exceeded 50ms` |

**权威源**：[L2-4 Spec v0.2.0 §9.1 (`L 2686-2714`)](../../spec/L2-module-specs/L2-knowledge-memory.md)

**L3-6 §8 关键纪律**（**避免 L3-5 #63.5.1 23 处漂移历史**）：
- **#66 Subagent 2 必须**直接 Read L2-4 v0.2.0 §9.1 完整段，**逐字符**复制 12 个 name + code + HTTP + Retryable + message 模板
- 禁止在 L3-6 §8 重新定义或改名任何 MEMORY_* 错误码
- 禁止将 MEMORY_* 名称简写（如 `MEMORY_NOT_FOUND`、`MEMORY_SUBJECT_NOT_FOUND`）—— 这些是 L3-5 #63.5 评审发现的漂移名
- 配套 IntEnum（`MemoryErrorCode`）与 helper 函数（`memory_error()`）定义在 §8.2-§8.3 #66 补完

### 8.2-§8.3 占位（#66 Subagent 2 补完）

- §8.2 `MemoryErrorCode` IntEnum 定义（target ~30 行 · 直接 import L2-4 权威 enum）
- §8.3 Retryable 矩阵 12 行 × Retryable/Backoff/CircuitBreaker（target ~50 行）
- §8.4 `memory_error()` helper + 错误码使用示例（target ~40 行）

---

## 9. Helm Values 7 模板（**与 L3-5 共享 chart · memory-backend container · RBAC 拆 write Role**）

> **说明**：本节在 #66 Subagent 2 补完完整 7 Helm 模板（target ~250 行）。本骨架稿仅占位 + 关键差异点 + L3-5-followup-1 RBAC 拆分。

### 9.1 关键差异（vs L3-5 v0.2.0 §9 · 共享 chart）

| 资源 | L3-5 独占 | L3-6 独占 | 共享 | L3-6 落地位置 |
|------|----------|----------|------|--------------|
| **Deployment name `knowledge-service`** | | | ✅ | §9.2 双 container（replicaCount: 1） |
| **Container 1 (knowledge-service / 8080)** | ✅ 业务代码 | | | （L3-5 独占） |
| **Container 2 (memory-backend / 8081)** | | ✅ 业务代码 | | §9.2 L3-6 独占 |
| **ConfigMap `knowledge-service-config`** | | | ✅ | scope-cache/BM25/OTLP/log |
| **ServiceAccount `knowledge-service`** | | | ✅ | 双 container 共用（cert-manager annotation） |
| **Service 80/443 → 8080** | ✅ ASGI 入口 | | | 8081 **不进 Service**（in-process only） |
| **ServiceMonitor（scrape port http=8080）** | L3-5 5 指标 | L3-6 10 指标 | ✅ | §9.8 metricRelabel keep 扩到 `superteam_memory_.*` |
| **RBAC Role** | read-only | write-only | ⚠️ | **§9.5 拆 2 个最小 Role 共享 SA（L3-5-followup-1）** |
| **NetworkPolicy ingress/egress** | | | ✅ | superteam-a2a ns:8443 + monitoring ns:8080 |
| **cert-manager TLS** | | | ✅ | `knowledge-service-tls` Secret 共享 |
| **PrometheusRule 6 告警** | L3-5 Knowledge* | L3-6 Memory* | ✅ | §9.7 同一 CR 加 2 Memory 告警 |

### 9.2 §9.9 共享 chart 段落（**L3-6 镜像 L3-5 v0.2.0 §9.9 line 1922-1924**）

```yaml
# 与 L3-5 knowledge-service 共享 Helm chart
# 7 个逻辑模板组：helpers/values、Deployment、Service、ServiceAccount、RBAC、NetworkPolicy、PrometheusRule+ServiceMonitor
# 对应 HELM-DEPLOY-001~007
# Deployment 固定 replicaCount: 1，包含 knowledge-service 与 memory-backend 两个业务 container
# 共享 SA/TLS/ConfigMap，以 async in-process/localhost 协议协调
# 但不得 import 对方私有模块
```

### 9.3 values 契约（**L3-6 镜像 L3-5 v0.2.0 §9.1 · 加 memoryBackendImage**）

```yaml
replicaCount: 1
image: {repository: superteam-a2a/knowledge-service, tag: v0.2.0}
memoryBackendImage: {repository: superteam-a2a/memory-backend, tag: v0.2.0}  # L3-6 独占
service: {httpPort: 80, httpsPort: 443, targetHttpPort: 8080, targetHttpsPort: 8443}
serviceAccount: {create: true, name: knowledge-service}
tls: {enabled: true, secretName: knowledge-service-tls, clientCASecretName: superteam-client-ca}
metrics: {path: /metrics, interval: 30s}
resources: {requests: {cpu: 200m, memory: 512Mi}, limits: {cpu: 1500m, memory: 2Gi}}
```

### 9.4-§9.9 占位（#66 Subagent 2 补完）

- §9.4 deployment.yaml 双 container 模板（target ~80 行 · 共享 L3-5 §9.2 + 加 memory-backend container）
- §9.5 service.yaml（80/443 → 8080/8443 · 8081 不进 Service · target ~30 行）
- §9.6 serviceaccount.yaml（cert-manager annotation · target ~30 行）
- **§9.7 rbac/role_readonly.yaml + rbac/role_write.yaml + rbac/rolebinding.yaml（**L3-5-followup-1 拆分** · 2 个最小 Role 共享 SA · target ~80 行）**
- §9.8 networkpolicy.yaml（ingress/egress 限制 · target ~40 行）
- §9.9 prometheusrule.yaml（6 告警 + 加 2 Memory 告警 · target ~50 行）
- §9.10 servicemonitor.yaml（15+10 指标 scrape · target ~40 行）

---

## 10. 测试策略 + 验收清单

> **说明**：本节在 #66 Subagent 2 补完完整 60 测试 ID 矩阵 + 30 验收点（target ~200 行）。本骨架稿仅占位 + 关键 ID 前缀 + 6 层级金字塔。

### 10.1 60 测试 ID 分布（**继承 L3-5 §10.1 + 新增 10 个 Memory 专属前缀**）

| 类别 | 数量 | ID 前缀 | 备注 |
|------|----:|---------|------|
| **UT** | 18 | KS-CRD-UT / KI-CRD-UT / **MEM-CRD-UT** / **MEM-REC-UT** / **MEM-DECAY-UT** / **MEM-REINFORCE-UT** / **MEM-GC-UT** / **MEM-PROMOTE-UT** / **MEM-LE-UT** / **MEM-CLOCK-UT** / **MEM-BM25-UT** / **MEM-BACKEND-UT** / H-RM-UT / H-QM-UT / ADM-UT / VIS-UT / BM25-UT / ERR-UT | L3-6 独占 10 个新前缀 |
| **IT** | 8 | KS-CRD-IT / KI-CRD-IT / **MEM-CRD-IT** / ADM-IT / ENVTEST-IT / TLS-IT / **MTLS-IT** / E2E-WIRE-IT | L3-6 独占 2 个新前缀 |
| **CF** | 3 | CF-QK / CF-GKI / **CF-MEM** | L3-6 独占 1 个新前缀 |
| **E2E** | 3 | E2E-KNOWLEDGE / E2E-MEMORY / E2E-MUTEX | |
| **TZ** | 3 | TZ-DECAY / TZ-PROMOTE / TZ-GC | 与 L3-5 一致 |
| **PERF** | 2 | PERF-BM25 / **PERF-MEM** | L3-6 独占 1 个新前缀 |
| **INPROC** | 2 | **INPROC-IT-001/002** | L3-6 独占新前缀 · in-process call 契约 |
| **DEPLOY** | 21 | HELM-DEPLOY × 7 + DOCKER-DEPLOY × 3 + DEPLOY × 11 | 与 L3-5 共享 |
| **总计** | **60** | — | 6 层级金字塔镜像规则 |

### 10.2 30 验收点（**继承 L3-5 §10.2 · 镜像 7 子组**）

- **AC-DOC** 文档完整性（5 条）· **AC-WIRE** wire contract（6 条）· **AC-VIS** 5 维矩阵（4 条）· **AC-SCOPE** 4 级 scope（4 条）· **AC-ADM** admission 互斥（4 条）· **AC-HELM** Helm 部署（4 条）· **AC-TEST** 测试矩阵（3 条）— 与 L3-5 镜像规则

### 10.3 6 层级金字塔（**继承 L3-5 §10.3**）

- **UT 60%** + Property 5% + HTTP 10% + CT 5% + IT 15% + E2E 5%

### 10.4 覆盖率门槛（**继承 L3-5 §10.4 · L3-6 关键模块扩展**）

- 全包 ≥ 80%
- 关键模块 ≥ 95%（**L3-6 关键模块**：apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion + memory_reconciler + clock_protocol + memory_backend + admission_validator + leader_election + bm25_rebuild）

---

## 11. 工具链与部署（uv workspace + Dockerfile + cert-manager + Kopf + OTel + Argo CD）

> **说明**：本节在 #66 Subagent 2 补完完整工具链 7 步工作流（target ~150 行）。本骨架稿仅占位 + 关键命令。

### 11.1 七步开发工作流（**继承 L3-5 §11.1**）

```bash
# 1. 环境就绪
uv sync --frozen

# 2. 代码风格
ruff format --check . && ruff check .

# 3. 静态类型
pyright --level error

# 4. 安全扫描
bandit -r packages services && pip-audit

# 5. 文档完整性
interrogate -f 100 packages services

# 6. 单元测试
pytest --cov=supteam_a2a.memory_backend --cov-fail-under=80

# 7. Helm 部署
helm lint helm/knowledge-service && helm template knowledge-service helm/knowledge-service
```

### 11.2-§11.5 占位（#66 Subagent 2 补完）

- §11.2 多阶段 Dockerfile（python:3.12-slim + ghcr.io/astral-sh/uv:0.5 + uv sync frozen + groupadd 65532 + USER 65532:65532 + readOnlyRootFilesystem · 与 L3-5 §11.2 镜像）
- §11.3 cert-manager Certificate（duration 2160h + renewBefore 720h + dnsNames + usages [server auth, client auth] + ClusterIssuer `superteam-ca` · 与 L3-5 §11.3 共享 Secret `knowledge-service-tls`）
- §11.4 Kopf 启动配置（**L3-6 独占 `@kopf.timer(interval=60.0, id="memory-reconciler")` + 50ms fail-closed** + uv.lock pin）
- §11.5 OTel Collector sidecar + Argo CD Application/AppSet（与 L3-5 §11.5 镜像）

---

## 12. 验收清单（§A-§G · 30 条）

> **说明**：本节在 #66 Subagent 2 补完完整 30 条验收清单（target ~80 行）。本骨架稿仅占位 + 7 子组结构。

§A-§G 7 子组（与 L3-5 §12 镜像）：
- **§A 算法正确性**（5 条 · A.2 双向互斥 + A.5 decay/reinforce/GC/promotion）
- **§B 边界与异常**（4 条 · B.2 Memory 写入限流 60/SA/分钟 + B.4 Leader Election 唯一性 + 转让 < 30s）
- **§C 接口契约**（5 条 · C.1 4 A2A method JSON-RPC 2.0 wire + C.2 错误码范围 -32101~-32112）
- **§D 可观测性**（4 条 · D.1 25 指标 `/metrics` 200 OK + D.4 decay/reinforce/admission/GC 4 类关键路径埋点）
- **§E 安全/准入**（4 条 · E.1 admission webhook + E.2 50ms fail-closed + E.4 RBAC 拆 2 Role 共享 SA（L3-5-followup-1）+ NetworkPolicy 隔离）
- **§F 性能/门禁**（4 条 · F.3 MemoryReconciler 60s 周期 reconcile 10000 Memory 完成 < 50s（PERF-MEM-001））
- **§G 验收基线**（4 条 · G.1 v0.2 Spec 落地 + G.2 #67 评审通过 + G.3 错误码 0 漂移 + G.4 RBAC 拆分生效）

---

## 13. 开放问题（22 项三层模式 + L3-6 新增 3-5 项）

> **说明**：本节在 #66 Subagent 2 补完完整 22 项三层模式（target ~100 行）。本骨架稿仅占位 + 关键 OPEN 项。

### 13.1 继承 L2-4 v0.2.0 §15 业务层 12 项（OPEN-L2-4-001 ~ 012）

### 13.2 继承 L2-4 v0.2.0 §15 Spec 层 4 项（OPEN-L2-4-013 ~ 016）

### 13.3 继承 L3-5 v0.2.0 §13 22 项中 3 项（OPEN-L3-5-004 BM25 rebuild / OPEN-L3-5-006 readiness / OPEN-L3-5-010 RBAC）

### 13.4 L3-6 独占新增 3-5 项（**待 #66 Subagent 2 补完**）

- **OPEN-MEMORY-001** Memory backend 水平扩展（与 L3-5 同 Pod 单实例约束冲突；v0.5+ 决策）
- **OPEN-MEMORY-002** MemoryBackend 抽象层 v0.5+ Vector DB 后端选型（Chroma / Qdrant / pgvector / Milvus · OPEN-L2-4-008 继承）
- **OPEN-MEMORY-003** Memory 全文搜索 BM25 over content（OPEN-L2-4-009 继承 · v0.1 仅内存多维过滤）
- **OPEN-MEMORY-004** Memory PII 字段加密（OPEN-L2-4-012 继承 · 待安全审计）
- **OPEN-MEMORY-005** Multi-cluster Memory 同步（OPEN-L2-4-011 继承 · 待 v0.5+）

---

## 附录 A：跨模块引用清单（5 子表 · v0.2-draft 占位）

> **说明**：本节在 #66 Subagent 2 补完完整 5 子表（target ~60 行）。本骨架稿仅占位。

### A.1 L1 引用（架构 + Spec）
### A.2 L2 引用（L2-1/2-3/4 spec + design）
### A.3 ADR + Constitution 引用（矩阵式）
### A.4 配套 L3 Spec 引用（**A.4 必须反向引用 L3-5 §6.2 共享 Deployment in-process 契约 · line 1488-1577**）
### A.5 归档基线

---

## 附录 B：ADR / Constitution 引用矩阵（5 子表 · v0.2-draft 占位）

> **说明**：本节在 #66 Subagent 2 补完完整 5 子表（target ~80 行）。本骨架稿仅占位。

### B.1 架构映射
### B.2 接口契约
### B.3 可见性与业务边界
### B.4 安全
### B.5 可观测性与测试

---

## 文档元数据与后续入口

### M.1 版本与状态

| 字段 | 值 |
|---|---|
| 版本 | **v0.2-draft-full**（2026-07-29 #64 骨架） |
| 状态 | 🟡 进行中 · 目标 #65 §3-§6 补完 + #66 §7-§13 + 附录 A/B + #67 独立评审 → 升级 v0.2.0 |
| 上游 | L1 Architecture v0.2.0 §3.5.3 + L1 Spec v0.2.0 §5.2.3 + L2-4 Spec v0.2.0 + L2-4 Design v0.2.0 + L3-5 §6.2 协调点 |
| 同级已通过 | L3-1 v0.2.0 (#56) + L3-2 v0.2.0 (#54) + L3-3 v0.2.0 (#58) + L3-4 v0.2.0 (#61) + L3-5 v0.2.0 (#63.5) |
| 评审报告 | 待 #67 独立评审（目标 550-650 行 / 50-60KB / §A-§Q 17 节 / 10 维度全 PASS） |
| 当前变更边界 | v0.2-draft 骨架稿仅占位；§3-§10 + 完整附录 A/B 待 #65/#66 Subagent 补完；M.4 已写入 4 次会话移交路径 |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-27 #43 | L2-4 Knowledge/Memory Spec v0.2.0 评审通过 | L2-4 上游就绪 |
| 2026-07-29 #63.5 | L3-5 Knowledge Service Spec v0.2.0 评审通过 + 错误码 23 处漂移修正 | L3-5 上游就绪 |
| **2026-07-29 #64（本会话）** | **L3-6 Memory backend Spec v0.2-draft 骨架稿：头部 11 段 + §0 阅读指南 + 5 项关键不变量 + 5 项 Python 化决策 D-1~D-5 + 28 文件清单 + 6 项边界规则 + §2 Python 包结构 + §3-§13 占位章节结构 + 附录 A/B 5 子表 + 文档元数据 M.1-M.6 + L3-5-followup-1 RBAC 拆 write Role 预告** | **v0.2-draft 骨架稿** · §3-§6 待 #65 Subagent 1 补完 · §7-§13 + 附录 A/B 待 #66 Subagent 2 补完 |

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

1. **#65 §3-§6 补完**（Subagent 1 隔离 ~95K tokens）：Memory CRD 12 字段完整 Pydantic v2 schema（§3.3-§3.5）+ MemoryReconciler 60s kopf.timer（§4.1-§4.4）+ 4 纯函数（§5.3-§5.6）+ **MemoryBackend 抽象层**（§5.7 核心新增点）+ Clock Protocol（§5.1-§5.2）+ in-process function reference 契约（§6.1-§6.4 + 8 边界测试 ID）
2. **#66 §7-§13 + 附录 A/B 补完**（Subagent 2 隔离 ~160K tokens）：Observability 10 指标（§7.1）+ structlog 8 字段（§7.2）+ 2-3 MEMORY_* EventReason（§7.3）+ 12 MEMORY_* 错误码（§8.1-§8.3 · **强制直接 import L2-4 §9.1 权威名零漂移**）+ Helm 7 模板共享 chart（§9.2-§9.10 · **含 L3-5-followup-1 RBAC 拆 2 Role 共享 SA**）+ 60 测试 ID 矩阵（§10.1-§10.4）+ 工具链 7 步（§11.1-§11.5）+ 30 验收点（§12）+ 22 开放问题三层模式（§13.1-§13.4）+ 附录 A 5 子表 + 附录 B 5 子表
3. **#67 L3-6 独立评审**（Subagent 3 隔离 ~140K tokens）：目标 550-650 行 / 50-60KB 评审报告 / §A-§Q 17 节 / 10 维度全 PASS + 4-5 关注项
4. **#67.x 升级**（主 Agent + Subagent 4 修正（如需））：头部 3 处 + §M.1-M.6 微同步 + 错误码零漂移验证 + §F 6 步跨文档同步（ROADMAP 5/5 → 6/6 / README / CONSTITUTION-CHANGELOG / L3-1/L3-2/L3-3/L3-4/L3-5 附录 A 升级）
5. **L3-5-followup-1 RBAC 拆 write Role 落地**：在 L3-6 §9.7 rbac/role_write.yaml 拆分 + kind 测试验证（与 L3-5 共享 SA `knowledge-service`）

### M.5 关注项台账（v0.2-draft 骨架稿待补完）

```
- 暂无（骨架稿未进入独立评审；M.4 已写入 4 次会话移交路径）
```

### M.6 文档元数据

- **创建日期**：2026-07-29 #64
- **最后更新**：2026-07-29 #64
- **下次更新**：#65（§3-§6 补完）
- **依赖完整性**：上游 L1 v0.2.0 + L2-4 v0.2.0 + L3-1/2/3/4/5 v0.2.0 全部就绪
- **下游影响**：L4 实施 Memory backend 工程师 + RBAC write Role 拆分（L3-5-followup-1）+ Leader Election 实施 + 性能门禁验证（L3-5-followup-2）+ _SCOPE_CACHE / BM25 rebuild 策略（L3-5-followup-4）

---

> **签署**：本 L3-6 Memory backend 文件级 Spec Python v0.2-draft 骨架稿由 #64 起，依据 [L1 Architecture v0.2.0 §3.5.3 + §4.3 C-7](../../design/L1-architecture.md)、[L1 Spec v0.2.0 §5.2.3 Memory YAML](../../spec/L1-system-spec.md)、[L2-4 Knowledge/Memory Spec v0.2.0 §3-§15](../../spec/L2-module-specs/L2-knowledge-memory.md)、[L2-4 Knowledge/Memory Design v0.2.0 §3-§14](../../design/L2-modules/L2-knowledge-memory.md)、[L3-1 Operator Core v0.2.0 §3.4 + §7](../../spec/L3-file-specs/L3-operator-core.md)、[L3-2 A2A Core v0.2.0 §5 + §6 + §9 + §10](../../spec/L3-file-specs/L3-a2a-core.md)、[L3-3 Adapter SDK v0.2.0 §3](../../spec/L3-file-specs/L3-adapter-sdk.md)、[L3-4 Hello Agent v0.2.0 §3.2 + §5](../../spec/L3-file-specs/L3-hello-agent.md)、**[L3-5 Knowledge Service v0.2.0 §3.3 Memory 5+5 简化 schema + §5 admission + §6.2 共享 Deployment 协调点（line 1488-1577）+ §9.9 共享 Helm chart 段落 + §8.2 12 MEMORY_* 错误码权威名](../../spec/L3-file-specs/L3-knowledge-service.md)**、[ADR-0003 Memory 设计](../../adr/0003-memory-design.md)、[ADR-0005 Python-first §3.4 + §6.2 + §6.3 + §10 + §13.1](../../adr/0005-python-first-technology-stack.md) 与 Constitution v0.5.0 编写。**当前骨架稿仅具备进入 #65 §3-§6 补完 + #66 §7-§13 + 附录 A/B 补完 + #67 独立评审 + #67.x v0.2.0 升级的准备条件；§3-§10 + 完整附录 A/B 补完后才能进入独立评审 → 升级 v0.2.0**。
