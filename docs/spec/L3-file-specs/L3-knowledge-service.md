# L3 文件级 Spec：Knowledge Service（Card-driven 知识服务 · Python-first）

> **模块定位**：C-6 Knowledge Service（Card-driven 知识服务 · v0.1 · 独立 Deployment / 单 Python 进程 / 单 Uvicorn worker / 暴露 4 A2A method · 与 MemoryReconciler 共享 Deployment）
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-6（Knowledge Service，见 L1 Architecture §3.5.2 + §4.3）
> **代码位置**：
> - **CRD types**：`packages/knowledge/src/supteam_a2a/knowledge/`（KnowledgeScope + KnowledgeItem Pydantic v2 + 5 维 visibility 矩阵 + 4 级 scope 继承 + admission 双向互斥 + BM25 倒排索引）
> - **A2A Agent 部署**：`services/knowledge-service/src/supteam_a2a/knowledge_service/`（Card-driven ASGI 单进程 + 4 A2A method handler + Helm 7 模板）
> - **部署共享**：`services/knowledge-service/` 与 `services/memory-backend/` 共享同 Deployment（同 Pod 内两个独立 Python 进程；详见 L3-6 Memory backend Spec）
> - **uv workspace 布局**：ADR-0005 §13.1
> **版本**：**v0.2-draft**（2026-07-29 #63.1 骨架稿；基于 L2-4 v0.2.0 #43 评审通过 + L3-1 v0.2.0 + L3-2 v0.2.0 + L3-3 v0.2.0 + L3-4 v0.2.0；L3 阶段 5/4 启动 Spec 起草）
> **状态**：🚧 **v0.2-draft 骨架稿**（#63.1 本会话起草：头部 + §0-§2 + 附录 A 占位 + §16 元数据；§3-§10 + 附录 B 后续 4-5 会话补完）
> **supersede / 归档标记（2026-07-29）**：本 v0.2-draft Spec 文档**仅 supersede Go struct / Go interface / Go package / Go CRD annotation 实现条款**；wire contract（3 CRD 字段 / 4 A2A method handler / 4 级 scope 继承 / 5 维 visibility 矩阵 / admission 双向互斥 / BM25 评分 / 错误码范围 / Helm values）与 L2-4 v0.2.0 Spec 业务语义**完全继续有效**。L2-4 v0.1.0 Go baseline 已在 L2-4 Spec v0.2.0 起草时覆盖丢失（与 L2-1/L2-3/L3-1/L3-2/L3-3/L3-4 同模式；建议 #63.x 后续会话追溯 v0.1.0 Go 归档登记）
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §3.5.2 + §4.3 C-6 + ADR-0005 §3.4 + §6.2 + §6.3 + §10 + §13.1 + L2-4 v0.2.0 Spec §2-§15 + L2-4 v0.2.0 Design §3-§14，CRD types Go struct → **Pydantic v2 BaseModel + Field(...) + populate_by_name + alias**；Go interface{} → **typing.Protocol + @runtime_checkable**；Go admission webhook → **Kopf `@kopf.validation` decorator + cert-manager TLS + 50ms fail-closed**；Go BM25 sync.Map → **Python `dict[str, set[str]]` + anyio.to_thread.run_sync CPU offload**；Go 4 级 scope 继承 → **Python `ScopeResolver` async service + 显式 ScopeError 异常**；Go 5 维矩阵 → **Python `dict[KnowledgeVisibility, Callable]` 策略表 + asyncio.Lock**；Card-driven Agent → **ASGI（Uvicorn 单 worker）+ 官方 `a2a-python` SDK + `superteam_a2a.a2a.upstream` 边界**
> **上游约束**：
> - [`docs/design/L2-modules/L2-knowledge-memory.md`](../../design/L2-modules/L2-knowledge-memory.md) **v0.2.0**（2026-07-27 #39 评审通过 · 1920 行 / 97KB / 14 节 + 2 附录 / 5 项 Python 化关键决策 + 9 维度 Go→Python 对照表 + 22 项开放问题三层模式）
> - [`docs/spec/L2-module-specs/L2-knowledge-memory.md`](../../spec/L2-module-specs/L2-knowledge-memory.md) **v0.2.0**（2026-07-27 #42 补完 + #43 评审通过 · 4152 行 / 194.6KB / 16 节 + 2 附录 + §16 元数据 / 60 测试 ID + 30 验收点 + 22 开放问题 / 3 Pydantic v2 CRD types + 4 A2A method + 4 级 scope 继承 + 5 维矩阵 + admission 互斥 + MemoryReconciler 60s kopf.timer + BM25 倒排索引 + 23 错误码 + 20 指标）
> - [L1 Architecture v0.2.0 §3.5.2 Knowledge Service](../../design/L1-architecture.md)（C-6 · Card-driven 单实例 / 单 Python 进程 / 单 Uvicorn worker）
> - [L1 Spec v0.2.0 §5.2.2 KnowledgeScope + KnowledgeItem YAML](../../spec/L1-system-spec.md)（CRD 字段约束）
> - [ADR-0002 知识管理设计](../../adr/0002-knowledge-management-design.md)（4 级 scope 继承 + 5 维 visibility + admission 互斥）
> - [ADR-0005 Python-first §3.4 Knowledge Service 模块映射 + §6.2 单进程原则 + §6.3 CPU offload + §10 structlog 字段 + §13.1 uv workspace](../../adr/0005-python-first-technology-stack.md)
> - [L3-1 Operator Core v0.2.0 §3.1 Agent Controller + §7 RBAC/Helm 9 模板 + §3.4 MemoryReconciler 协调](../../spec/L3-file-specs/L3-operator-core.md)（CRD wire sync + MemoryReconciler 接入）
> - [L3-2 A2A Core v0.2.0 §5 ASGI server + §6 A2AClient + §9 15 Prometheus 指标 + §10 24 错误码](../../spec/L3-file-specs/L3-a2a-core.md)（wire 复用）
> - [L3-3 Adapter SDK v0.2.0 §3 FrameworkAdapter Protocol](../../spec/L3-file-specs/L3-adapter-sdk.md)（L3-5 不依赖 Adapter SDK；Card-driven 直接实现 A2A 端点）
> - [L3-4 Hello Agent v0.2.0 §3.2 HelloAgentExecutor + §5 ASGI server + §6.9 25 ID 测试](../../spec/L3-file-specs/L3-hello-agent.md)（同模式 Card-driven 单实例参考实现）
> **本 Spec 目的**：将 L2-4 Spec v0.2.0 中的 **3 CRD types（KnowledgeScope / KnowledgeItem / Memory schema）+ 4 A2A method handler（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）+ 4 级 scope 继承 + 5 维 visibility 矩阵 + admission 双向互斥 + BM25 倒排索引 + 23 错误码 + Helm 7 模板** 落地为 **文件级 Python 代码契约**——每个文件列明**绝对路径（基于 uv workspace 布局）**、**职责一句话**、**完整 import 列表**、**exported 符号签名（type hints + docstring 一行）**、**内部 helper 列表**、**关联测试文件路径 + 测试 ID 前缀**。是 L4 实施阶段（开发者打开 IDE 即可对照写代码）的直接输入。
> **配套 Spec**：[L3-1 Operator Core 文件级 Spec v0.2.0](./L3-operator-core.md)（2026-07-28 #56 评审通过 · CRD wire sync + MemoryReconciler 60s 周期）/ [L3-2 A2A Core Library 文件级 Spec v0.2.0](./L3-a2a-core.md)（2026-07-28 #54 评审通过 · ASGI + A2AClient + 15 指标 + 24 错误码）/ [L3-3 Adapter SDK 文件级 Spec v0.2.0](./L3-adapter-sdk.md)（2026-07-29 #58 评审通过 · L3-5 不依赖 Adapter SDK）/ [L3-4 Hello Agent 文件级 Spec v0.2.0](./L3-hello-agent.md)（2026-07-29 #61 评审通过 · 同模式 Card-driven 单实例参考实现）/ [L3-6 Memory backend 文件级 Spec](./L3-memory-backend.md)（待起草 · 共享 Deployment / MemoryReconciler 60s kopf.timer 详细落地）
> **配套 Review**：[L3-5 Knowledge Service Spec 评审报告](../../reviews/l3-5-knowledge-service-spec-review.md)（本骨架稿后独立评审 · #63.x 后续会话创建）

---

## 0. 阅读指南

- **读者**：Knowledge Service 实施工程师（L4 Python 编码）、Helm 部署工程师（Card-driven 单实例 / 共享 Deployment）、架构 Reviewer（Knowledge↔Memory 双向互斥边界一致性）、A2A method 集成者（4 method handler 调用方）
- **必读章节**：
  - §1（模块使命 + 5 项 Python 化关键决策 + 40 → 30 文件清单总览）
  - §2（Python 包结构 6 子包 / 30 文件级契约）
  - §3（3 CRD types Pydantic v2 完整 schema + 4 级 scope + 5 维 visibility 矩阵）
  - §4（4 A2A method handler Pydantic schema + queryKnowledge BM25 倒排索引路径）
  - §5（admission webhook 双向互斥 + cert-manager TLS + 50ms fail-closed）
  - §6（MemoryReconciler 协调点 — 60s 周期 + Leader Election + decay/reinforce 数学，详细落地见 L3-6）
  - §7（observability + 20 Prometheus 指标 + structlog + OTel + K8s Events）
  - §8（23 错误码 enum + Retryable 矩阵）
  - §9（Helm values 7 模板 + env 映射）
  - §10（验收清单 30 条 + 60 测试 ID 矩阵 + 22 开放问题状态）
  - 附录 A（跨模块引用清单 5 子表）/ 附录 B（ADR / Constitution 5 子表追溯矩阵）
- **评审入口**：§10 验收清单 + 附录 A 5 子表 + 附录 B 5 子表 + 30 文件级契约 + 60 测试 ID 互相回链
- **配套阅读**：
  - [L2-4 Knowledge/Memory Spec v0.2.0 §0-§15](../../spec/L2-module-specs/L2-knowledge-memory.md)（CRD types + 4 A2A method + 4 级 scope + 5 维矩阵 + admission 互斥 + 60 测试 ID + 22 开放问题）
  - [L2-4 Knowledge/Memory Design v0.2.0 §3-§14](../../design/L2-modules/L2-knowledge-memory.md)（5 项 Python 化决策 + 9 维度 Go→Python 对照表 + 22 开放问题）
  - [L1 Architecture v0.2.0 §3.5.2 Knowledge Service + §4.3 C-6](../../design/L1-architecture.md)（Card-driven 单实例约束）
  - [L1 Spec v0.2.0 §5.2.2 KnowledgeScope + KnowledgeItem YAML 示例](../../spec/L1-system-spec.md)
  - [ADR-0002 知识管理设计](../../adr/0002-knowledge-management-design.md)（4 级 scope + 5 维 visibility + admission 互斥业务规则）
  - [ADR-0003 Memory 设计](../../adr/0003-memory-design.md)（Memory 衰减公式 + admission 互斥）
  - [ADR-0005 Python-first §3.4 + §6.2 + §6.3 + §10 + §13.1](../../adr/0005-python-first-technology-stack.md)
  - [L3-1 Operator Core v0.2.0 §3.1 Agent Controller + §3.4 MemoryReconciler + §7 Helm 9 模板 + §7.3 RBAC](../../spec/L3-file-specs/L3-operator-core.md)
  - [L3-2 A2A Core v0.2.0 §5 ASGI + §6 A2AClient + §9 15 指标 + §10 24 错误码](../../spec/L3-file-specs/L3-a2a-core.md)
  - [L3-3 Adapter SDK v0.2.0 §3 FrameworkAdapter Protocol](../../spec/L3-file-specs/L3-adapter-sdk.md)（L3-5 不依赖 Adapter SDK）
  - [L3-4 Hello Agent v0.2.0 §3.2 HelloAgentExecutor + §5 ASGI server 复用 + §6.9 25 ID 测试](../../spec/L3-file-specs/L3-hello-agent.md)
  - [a2a-sdk 官方文档](https://github.com/google/a2a-python) · [Kopf 官方文档](https://kopf.readthedocs.io/) · [kubernetes_asyncio 文档](https://github.com/kubernetes-client/python/tree/master/kubernetes_asyncio)

**与 L3-1/L3-2/L3-3/L3-4 复用边界**：
- L3-5 复用 L3-2 §5 ASGI server（单进程 / 单 Uvicorn worker / port 8080 + `/healthz` `/readyz` `/metrics`）
- L3-5 复用 L3-2 §6 A2AClient（如需在 handler 内调用其他 A2A method；L3-5 主要做 server 端，不强依赖）
- L3-5 复用 L3-2 §9 15 Prometheus 指标（11 A2A + 4 Python runtime；L3-5 不新增基础指标）
- L3-5 复用 L3-2 §10 24 错误码 enum（**L3-5 新增 11 个 KNOWLEDGE_* + 12 个 MEMORY_* = 23 个错误码**，**与 L2-4 v0.2.0 Spec §9 完全一致**；详见 §8）
- L3-5 复用 L3-1 §3.1 Agent Controller reconcile CRD 生命周期（KnowledgeScope / KnowledgeItem）
- L3-5 复用 L3-1 §7 Helm 9 模板基础（适配为 7 模板 Knowledge Service 单实例）
- L3-5 复用 L3-1 §7.3 RBAC ClusterRole（Knowledge Service 仅需 CRD read + 自身 ServiceAccount token）
- **L3-5 不依赖 L3-3 Adapter SDK**（Card-driven 直接实现 A2A 端点；与 L3-4 Hello Agent 同模式）
- L3-5 与 L3-6 Memory backend 共享 Deployment（**同 Pod 内两个独立 Python 进程**；共享 Helm chart / Service / ServiceMonitor / NetworkPolicy / RBAC；进程间通过共享内存或 in-process call 通信 — 详见 §6.2）

**与 L3-6 Memory backend 边界**：
- L3-5 暴露 4 A2A method：queryKnowledge / getKnowledgeItem（Knowledge）/ recordMemory / queryMemory（Memory — 实际 handler 调用 L3-6 内部 service）
- L3-6 详细落地 MemoryReconciler 60s 周期 + Leader Election + decay/reinforce + GC + promotion；L3-5 §6 仅给出协调点（共享 Deployment 边界 + handler 调用契约 + in-process function reference）
- L3-5 §5 admission webhook 包含 Knowledge↔Memory 双向互斥校验（详见 §5.3）

**5 项 Python 化关键决策（D-1 ~ D-5）**（继承 L2-4 Design v0.2.0 §1）：

| 编号 | 决策 | Go baseline | v0.2 Python | 落地位置 |
|------|------|-------------|-------------|----------|
| **D-1** | CRD types | Go struct + `+kubebuilder:validation:` | **Pydantic v2 BaseModel + Field(...) + populate_by_name + alias** | §3.1 KnowledgeScope + §3.2 KnowledgeItem + §3.3 Memory schema |
| **D-2** | BM25 检索 | Go `map[string][]Item.ID` + mutex | **Python `dict[str, set[str]]` + `anyio.to_thread.run_sync` 受控线程 offload** | §4.2 queryKnowledge handler 检索路径 |
| **D-3** | MemoryReconciler 周期 | controller-runtime `Reconcile()` | **Kopf `@kopf.timer(interval=60.0)` + 独立 async service + Leader Election via coordination.k8s.io/v1 Lease** | §6.1（协调点，详细 L3-6） |
| **D-4** | Clock 时间穿越 | Go interface + k8s.io/utils/clock | **`Protocol[now, advance]` + `RealClock` + `FakeClock`** | §6.2 共享 in-process function + 测试用 `freezegun` |
| **D-5** | admission webhook | Go `admissionv1.Handler` | **Kopf `@kopf.validation` decorator + cert-manager TLS + 50ms fail-closed** | §5.1 双向互斥 validator |

**9 维度 Go→Python 对照**（继承 L2-4 Design v0.2.0 §1）：

| 维度 | Go baseline | Python v0.2 | L3-5 落地位置 |
|------|-------------|-------------|----------------|
| **CRD types** | Go struct + kubebuilder annotation | Pydantic v2 + Field | §3.1-§3.3 |
| **算法抽象** | Go interface{} | typing.Protocol + @runtime_checkable | §4.1 Visibility 策略表 + §4.2 检索路径 |
| **scope 继承** | Go func + error | Python async def + ScopeError | §3.4 ScopeResolver |
| **5 维矩阵** | Go switch + sync.Map | dict + asyncio.Lock | §3.5 VisibilityResolver |
| **检索** | sync in-process | async + anyio.to_thread.run_sync | §4.2 BM25 倒排索引 |
| **Memory timer** | controller-runtime Reconcile() | Kopf @kopf.timer + Leader Election | §6.1（详细 L3-6） |
| **admission** | admissionv1.Handler | Kopf @kopf.validation + 50ms fail-closed | §5.1 |
| **A2A server** | Go a2a.NewServer | ASGI + 官方 a2a-python + upstream 边界 | §4 4 A2A method handler |
| **错误码** | Go constants + errors.New | StrEnum + a2a-python JSON-RPC error | §8 23 错误码 enum |

---

## 1. 模块使命与文件清单总览

### 1.1 模块使命（C-6 Knowledge Service · Card-driven 单实例）

- **不是** Sidecar 模式 — 是独立 Deployment（v0.1 单实例 / 单 Python 进程 / 单 Uvicorn worker）
- **Card**：`superteam-a2a.knowledge-service` v0.1.0（4 Skills：query_knowledge / get_knowledge_item / record_memory / query_memory）
- **Capabilities**：streaming=false / pushNotifications=false（v0.1 简化）
- **认证**：mTLS（cert-manager 颁发，Python `ssl.SSLContext`）
- **依赖 CRD**：KnowledgeScope / KnowledgeItem / Memory schema（通过 `kubernetes_asyncio` 异步客户端读取）
- **承担职责**：
  - 暴露 4 个 A2A method（Knowledge 2 + Memory 2；Memory 2 method 实际调用同 Pod 内 L3-6 内部 service）
  - Knowledge↔Memory admission 双向互斥校验（不与 L3-6 重复实现）
  - 4 级 scope 继承 + 5 维 visibility 矩阵解析
  - BM25 倒排索引查询（queryKnowledge method）
  - KnowledgeItem 详情拉取（getKnowledgeItem method）
- **不实现**：
  - 不实现业务 Agent 逻辑（仅 Card-driven A2A 端点暴露）
  - 不实现 Memory 写入/读取业务（调用 L3-6 in-process service）
  - 不实现 MemoryReconciler 60s 周期 reconcile（详细 L3-6 落地）
  - 不实现 Adapter SDK（与 L3-4 同模式 — 直接实现 A2A 端点）

### 1.2 5 项关键不变量（任何修改必须走 ADR）

1. **Card-driven 单实例**：Knowledge Service v0.1 严格单实例（`replicaCount: 1`）；水平扩展需走 v0.5+ 决策（OPEN-KNOWLEDGE-001）
2. **4 个 A2A method 不变**：queryKnowledge / getKnowledgeItem / recordMemory / queryMemory — method 名与 wire contract 永久不变（与 L2-1 Spec v0.2.0 §3 envelope 一致）
3. **Knowledge↔Memory 共享 Deployment**：L3-5 与 L3-6 严格同 Pod 部署（共享 Helm chart / Service / ServiceMonitor / NetworkPolicy / RBAC；进程间通过 in-process function reference — 详见 §6.2）
4. **不实现业务 Agent 逻辑**：仅暴露 4 A2A method；不承载 framework adapter 业务
5. **wire contract 完全继承 L2-4 v0.2.0 Spec**：CRD field 名 camelCase / 4 A2A method envelope / 23 错误码 wire 名 / 4 级 scope 名（agent / agentset / workflow / system） / 5 维 visibility name 永久不变

### 1.3 文件清单总览（30 文件级契约 + 7 Helm 模板 + 1 Dockerfile + 2 CRD 示例 + 30 测试文件镜像）

| 类别 | 数量 | 路径前缀 | 备注 |
|------|------|----------|------|
| **CRD types（packages/knowledge/）** | 8 | `packages/knowledge/src/supteam_a2a/knowledge/` | Pydantic v2 + JSON Schema |
| **A2A Agent 部署（services/knowledge-service/）** | 12 | `services/knowledge-service/src/supteam_a2a/knowledge_service/` | ASGI + 4 handler + Card |
| **shared 公共（packages/shared-visibility/）** | 4 | `packages/shared-visibility/src/supteam_a2a/shared/visibility/` | 5 维矩阵 + 4 级 scope 复用（与 L3-6 共享） |
| **测试文件镜像** | 30 | `tests/{unit,integration,e2e,contract,fuzz,perf}/knowledge*/` | 6 层级金字塔 |
| **Helm 模板** | 7 | `helm/knowledge-service/templates/` | deployment + service + serviceaccount + rbac + networkpolicy + prometheusrule + servicemonitor |
| **Dockerfile** | 1 | `services/knowledge-service/Dockerfile` | python:3.12-slim 多阶段 + uv build |
| **CRD 示例** | 2 | `examples/knowledge/{knowledgescope,knowledgeitem}.yaml` | L1 Spec §5.2.2 同步 |
| **总计** | **64** | — | 30 文件级契约 + 30 测试镜像 + 7 Helm + 1 Dockerfile + 2 CRD |

详细文件清单见 §1.4（待 #63.2 补完时展开）。

### 1.4 文件清单（30 文件级契约 · 详细 · 待 #63.2 展开）

> **说明**：本骨架稿仅列文件清单汇总（30 文件级契约 / 6 子包）；具体每个文件的**绝对路径 / 职责一句话 / 完整 import 列表 / exported 符号签名 / 内部 helper 列表 / 关联测试文件路径 + 测试 ID 前缀**待 #63.2 补完时逐项展开（参照 L3-1 v0.2.0 §1.4 700+ 行 / 162 文件清单模式）。

| 序号 | 路径（基于 uv workspace） | 职责一句话 | 关联测试 ID 前缀 |
|------|--------------------------|------------|-----------------|
| 1-8 | `packages/knowledge/src/supteam_a2a/knowledge/crd/{knowledgescope,knowledgeitem,memory_schema,scope_reference,item_reference,inherit_rules,scope_level,scope_phase}.py` | 3 Pydantic v2 CRD types + 5 辅助类型 | KS-CRD / KI-CRD / MEM-CRD |
| 9-12 | `services/knowledge-service/src/supteam_a2a/knowledge_service/{agent,card,observability,_internals}.py` | 4 A2A method handler + Card + observability | AGENT / CARD / OBS |
| 13-16 | `services/knowledge-service/src/supteam_a2a/knowledge_service/handlers/{query_knowledge,get_knowledge_item,record_memory,query_memory}.py` | 4 A2A method handler 独立文件（业务下沉） | H-QK / H-GKI / H-RM / H-QM |
| 17-20 | `services/knowledge-service/src/supteam_a2a/knowledge_service/{scope_resolver,visibility_resolver,bm25_index,admission_validator}.py` | 4 级 scope + 5 维矩阵 + BM25 + admission 互斥 | SCOPE / VIS / BM25 / ADM |
| 21-24 | `services/knowledge-service/src/supteam_a2a/knowledge_service/{events,errors,metrics_server,__init__}.py` | K8s Events + 23 错误码 enum + metrics server + public API | EVT / ERR / MET |
| 25-28 | `packages/shared-visibility/src/supteam_a2a/shared/visibility/{scope_resolver,visibility_matrix,knowledge_type,scope_inherit}.py` | 5 维矩阵 + 4 级 scope + KnowledgeType 枚举（与 L3-6 共享） | SV-SCOPE / SV-VIS / SV-KT / SV-INH |
| 29-30 | `services/knowledge-service/src/supteam_a2a/knowledge_service/{retrieval_service,scope_cache}.py` | 检索 service + 4 级 scope 缓存（`_SCOPE_CACHE: dict[str, KnowledgeScope]` + LRU 1024） | RETR / SC |

**30 测试文件镜像清单**（与 L3-2 / L3-4 同模式，6 层级金字塔）：

| 层级 | 数量 | 路径 | 测试 ID 前缀 |
|------|------|------|--------------|
| **UT** | 11 | `tests/unit/knowledge*/` | KS-CRD-UT / KI-CRD-UT / SCOPE-UT / VIS-UT / BM25-UT / H-QK-UT / H-GKI-UT / H-RM-UT / H-QM-UT / ERR-UT / CARD-UT |
| **IT** | 8 | `tests/integration/knowledge*/` | KS-CRD-IT / KI-CRD-IT / ADM-IT / ENVTEST-IT / TLS-IT / MTLS-IT / E2E-WIRE-IT / DEPLOY-IT |
| **CF** | 3 | `tests/contract/knowledge*/` | CF-QK / CF-GKI / CF-MEM |
| **E2E** | 3 | `tests/e2e/knowledge*/` | E2E-KNOWLEDGE / E2E-MEMORY / E2E-MUTEX |
| **TZ** | 3 | `tests/timezone/knowledge*/` | TZ-DECAY / TZ-PROMOTE / TZ-GC |
| **PERF** | 2 | `tests/perf/knowledge*/` | PERF-BM25 / PERF-MEM |

**总计 60 测试 ID**（与 L2-4 Spec v0.2.0 §12 60 测试 ID 完全一致；详见 §10 矩阵）。

### 1.5 上游依赖关系图

```
┌─────────────────────────────────────────────────────────────────┐
│              L3-5 Knowledge Service v0.2 Python                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────┐                   │
│  │  packages/knowledge/ (CRD types)         │  ← Pydantic v2   │
│  │  - knowledgescope.py (KS-CRD)            │                   │
│  │  - knowledgeitem.py  (KI-CRD)            │                   │
│  │  - memory_schema.py (MEM-CRD)            │                   │
│  └──────────────────────────────────────────┘                   │
│                     ↑                                           │
│  ┌──────────────────┴───────────────────────┐                   │
│  │  services/knowledge-service/             │  ← ASGI + 4 handler│
│  │  - agent.py (AGENT, 50 行)              │                   │
│  │  - card.py (CARD, 40 行)                │                   │
│  │  - observability.py (OBS, 80 行)        │                   │
│  │  - _internals.py (INT, 60 行)           │                   │
│  │  - handlers/ (4 method, 30 行/个)       │                   │
│  │  - scope_resolver.py (SCOPE)            │                   │
│  │  - visibility_resolver.py (VIS)         │                   │
│  │  - bm25_index.py (BM25)                 │                   │
│  │  - admission_validator.py (ADM)         │                   │
│  └──────────────────────────────────────────┘                   │
│            ↑                                                     │
│            │  import（CRD types 复用）                          │
│            │                                                     │
│  ┌─────────┴──────────────────────────────────┐                 │
│  │  packages/shared-visibility/ (与 L3-6 共享)│  ← typing.Protocol│
│  │  - scope_resolver.py (SV-SCOPE)           │                 │
│  │  - visibility_matrix.py (SV-VIS)          │                 │
│  │  - knowledge_type.py (SV-KT)              │                 │
│  │  - scope_inherit.py (SV-INH)              │                 │
│  └───────────────────────────────────────────┘                 │
│                                                                 │
│  外部依赖（仅 import 边界）：                                    │
│  - L3-2 a2a-core: ASGI server + A2AClient + 15 指标 + 24 错误码  │
│  - L3-1 operator: CRD wire sync + Helm 9 模板 + RBAC 基础       │
│  - L3-6 memory-backend: in-process function reference（共享 Pod）│
│  - a2a-sdk 官方: AgentExecutor + DefaultRequestHandler           │
│  - kopf: @kopf.validation decorator（admission webhook 互斥）   │
│  - kubernetes_asyncio: CRD 读取（KnowledgeScope / KI / Memory）  │
│  - prometheus-client: 11 A2A + 4 runtime + 5 Knowledge 指标     │
│  - structlog: 8 必含字段                                         │
│  - OpenTelemetry: W3C traceparent                                │
│  - cert-manager: mTLS TLSConfig + HotReloader                   │
│                                                                 │
│  Helm 部署（7 模板）：                                          │
│  - deployment.yaml (单实例 + 双探针 + SecurityContext)           │
│  - service.yaml (80/443 双端口 + mTLS)                          │
│  - serviceaccount.yaml (cert-manager annotation)                │
│  - rbac/role.yaml + rolebinding.yaml (read CRD only)            │
│  - networkpolicy.yaml (ingress/egress 限制)                     │
│  - prometheusrule.yaml (6 告警规则)                              │
│  - servicemonitor.yaml (15 + 5 指标 scrape)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Python 包结构

### 2.1 uv workspace 布局（ADR-0005 §13.1）

```
superteam-a2a/
├── packages/
│   ├── knowledge/                                # CRD types（与 L3-6 共享）
│   │   ├── pyproject.toml
│   │   └── src/supteam_a2a/knowledge/
│   │       ├── __init__.py
│   │       ├── crd/
│   │       │   ├── knowledgescope.py             # KS-CRD · Pydantic v2 BaseModel
│   │       │   ├── knowledgeitem.py              # KI-CRD · Pydantic v2 BaseModel
│   │       │   ├── memory_schema.py              # MEM-CRD · Pydantic v2 BaseModel
│   │       │   ├── scope_reference.py            # ScopeReference · 4 级 scope 引用
│   │       │   ├── item_reference.py             # ItemReference · KnowledgeItem 引用
│   │       │   ├── inherit_rules.py              # InheritRules · 4 级继承规则
│   │       │   ├── scope_level.py                # ScopeLevel · agent/agentset/workflow/system enum
│   │       │   └── scope_phase.py                # ScopePhase · Active/Pending/Archived enum
│   │       └── ...
│   ├── shared-visibility/                        # 5 维矩阵 + 4 级 scope（与 L3-6 共享）
│   │   ├── pyproject.toml
│   │   └── src/supteam_a2a/shared/visibility/
│   │       ├── __init__.py
│   │       ├── scope_resolver.py                 # SV-SCOPE · 4 级继承解析
│   │       ├── visibility_matrix.py              # SV-VIS · 5 维 visibility 策略表
│   │       ├── knowledge_type.py                 # SV-KT · KnowledgeType enum (procedural/factual/episodic/conceptual)
│   │       └── scope_inherit.py                  # SV-INH · ScopeInherit 计算
│   └── ...
├── services/
│   └── knowledge-service/                        # A2A Agent 部署（与 memory-backend 共享 Deployment）
│       ├── pyproject.toml
│       ├── Dockerfile
│       ├── helm/
│       │   └── templates/
│       │       ├── _helpers.tpl
│       │       ├── deployment.yaml               # 单实例 + 双探针 + SecurityContext
│       │       ├── service.yaml                  # 80/443 双端口 + mTLS
│       │       ├── serviceaccount.yaml           # cert-manager annotation
│       │       ├── rbac/role.yaml                # CRD read only
│       │       ├── rbac/rolebinding.yaml
│       │       ├── networkpolicy.yaml            # ingress/egress 限制
│       │       ├── prometheusrule.yaml           # 6 告警规则
│       │       └── servicemonitor.yaml           # 15+5 指标 scrape
│       └── src/supteam_a2a/knowledge_service/
│           ├── __init__.py                       # public API: app, executor, card
│           ├── agent.py                          # AGENT · KnowledgeServiceExecutor (50 行)
│           ├── card.py                           # CARD · build_knowledge_service_card (40 行)
│           ├── observability.py                  # OBS · 5 指标 + bind_request_logger (80 行)
│           ├── _internals.py                     # INT · test fixture + helper (60 行)
│           ├── handlers/
│           │   ├── __init__.py
│           │   ├── query_knowledge.py            # H-QK · a2a.queryKnowledge handler (30 行)
│           │   ├── get_knowledge_item.py         # H-GKI · a2a.getKnowledgeItem handler (30 行)
│           │   ├── record_memory.py              # H-RM · a2a.recordMemory handler (调用 L3-6 in-process · 30 行)
│           │   └── query_memory.py               # H-QM · a2a.queryMemory handler (调用 L3-6 in-process · 30 行)
│           ├── scope_resolver.py                 # SCOPE · 4 级 scope 解析（async service）
│           ├── visibility_resolver.py            # VIS · 5 维 visibility 策略表
│           ├── bm25_index.py                     # BM25 · 倒排索引（dict + anyio.to_thread.run_sync）
│           ├── admission_validator.py            # ADM · Knowledge↔Memory 双向互斥
│           ├── retrieval_service.py              # RETR · 检索 service（queryKnowledge 入口）
│           ├── scope_cache.py                    # SC · 4 级 scope 缓存（LRU 1024）
│           ├── events.py                         # EVT · K8s Events 8 种类
│           ├── errors.py                         # ERR · 23 错误码 enum（KNOWLEDGE_*-32008~-32018 + MEMORY_*-32101~-32112）
│           └── metrics_server.py                 # MET · /healthz /readyz /metrics 端口 8080
└── tests/
    ├── unit/knowledge/                           # 11 UT（6 层级金字塔）
    ├── integration/knowledge/                    # 8 IT
    ├── contract/knowledge/                       # 3 CF（与 L2-4 wire contract 一致）
    ├── e2e/knowledge/                            # 3 E2E
    ├── timezone/knowledge/                       # 3 TZ（decay / promote / GC 时间穿越）
    └── perf/knowledge/                           # 2 PERF（BM25 / Memory 检索）
```

### 2.2 8 项边界规则（继承 L3-1 §2.3 + L3-2 §2.3 + L3-3 §2.3 + L3-4 §2.2 + 新增 2 项）

| # | 规则 | 强度 | 落地位置 |
|---|------|------|----------|
| 1 | Knowledge Service v0.1 **不实现业务 Agent 逻辑** | MUST | §1.1 + §4 4 handler |
| 2 | 仅暴露 **2 A2A method**（queryKnowledge / getKnowledgeItem）— recordMemory/queryMemory **委托 L3-6** | MUST | §4 4 handler |
| 3 | 严格单实例（`replicaCount: 1`） | MUST | §9 deployment.yaml + §1.2 不变量 1 |
| 4 | 与 L3-6 Memory backend **共享 Deployment** | MUST | §9 deployment.yaml + §6.2 |
| 5 | **不依赖 Adapter SDK**（Card-driven 直接实现 A2A 端点） | MUST | §4 4 handler（不 import L3-3） |
| 6 | **不依赖 L3-2 A2AClient**（仅 server 端） | SHOULD | §4 4 handler（仅 import L3-2 ASGI server） |
| 7 | **CRD types 复用 packages/knowledge/**（不重新实现） | MUST | §3.1-§3.3 + §1.5 依赖图 |
| 8 | admission 双向互斥仅 L3-5 §5 实现（**L3-6 不重复**） | MUST | §5 + 与 L3-6 边界 |

### 2.3 依赖方向

```
L4 实施工程师
    ↓ import
services/knowledge-service/src/supteam_a2a/knowledge_service/
    ↓ import
packages/knowledge/src/supteam_a2a/knowledge/crd/         (CRD types 复用)
packages/shared-visibility/src/supteam_a2a/shared/visibility/  (与 L3-6 共享)
L3-2 a2a-core: ASGI server + 15 指标 + 24 错误码            (外部 import)
L3-1 operator: CRD wire sync（无 import 依赖；通过 K8s API 通信）
L3-6 memory-backend: in-process function reference（共享 Pod；详细 §6.2）
```

**禁止反向依赖**（与 L3-1 / L3-2 / L3-3 / L3-4 同模式）：
- L3-5 **不得** import L3-3 Adapter SDK（rule 5）
- L3-5 **不得** import L3-1 Operator（仅通过 K8s API 通信）
- L3-5 **不得** 重新实现 CRD types（rule 7）
- L3-5 **不得** 在 L3-6 之前实现 Memory 业务逻辑（rule 2）

---

## 3. 3 CRD Types（Pydantic v2 完整 schema · 详细待 #63.2 补完）

> **说明**：本骨架稿仅列章节结构与测试 ID 数量；Pydantic v2 BaseModel 完整 schema 字段约束、Field(...) 校验、JSON Schema 2020-12 生成示例待 #63.2 补完（参照 L2-4 Spec v0.2.0 §3 完整 Pydantic schema 模式）。

### 3.1 KnowledgeScope CRD（KS-CRD · 6 spec 字段 + 6 status 字段 · ADR-0002 §3.1）

- 完整 Pydantic v2 schema 见 L2-4 Spec v0.2.0 §3.1
- 6 spec 字段：`scope_level` (ScopeLevel enum) / `parent_ref` (ScopeReference optional) / `subject_ref` (SubjectReference) / `inherit_rules` (InheritRules) / `visibility` (KnowledgeVisibility 5 维) / `description` (str)
- 6 status 字段：`phase` (ScopePhase enum) / `observed_generation` (int) / `last_updated` (datetime) / `child_scopes` (list[ScopeReference]) / `knowledge_item_count` (int) / `active_queries_5m` (int)
- 状态机：Pending → Active → Archived（详见 L2-4 Spec §3.1.2）
- 测试 ID：`KS-CRD-UT-001~006`（6）/ `KS-CRD-IT-001~004`（4）= 10 ID

### 3.2 KnowledgeItem CRD（KI-CRD · 7 spec 字段 + 7 status 字段 · ADR-0002 §3.2）

- 完整 Pydantic v2 schema 见 L2-4 Spec v0.2.0 §3.2
- 7 spec 字段：`scope_ref` (ScopeReference) / `knowledge_type` (KnowledgeType enum) / `content` (str) / `tags` (list[str]) / `version` (int) / `superseded_by` (ItemReference optional) / `confidence` (float 0.0-1.0)
- 7 status 字段：`phase` (ItemPhase enum) / `indexed_at` (datetime) / `last_accessed` (datetime) / `access_count_24h` (int) / `bm25_score_avg` (float) / `decay_state` (DecayState) / `effective_confidence` (float)
- 状态机：Indexing → Active → Decaying → Superseded → Archived
- 测试 ID：`KI-CRD-UT-001~007`（7）/ `KI-CRD-IT-001~004`（4）= 11 ID

### 3.3 Memory Schema（MEM-CRD · 5 spec 字段 + 5 status 字段 · ADR-0003 §3）

- 完整 Pydantic v2 schema 见 L2-4 Spec v0.2.0 §3.3
- 5 spec 字段：`agent_ref` (SubjectReference) / `task_ref` (TaskReference optional) / `content` (str) / `scope_ref` (ScopeReference) / `decay_days` (int)
- 5 status 字段：`phase` (MemoryPhase enum) / `confidence` (float) / `effective_confidence` (float) / `last_reinforced` (datetime) / `gc_state` (GCState)
- 衰减公式：`effectiveConfidence = confidence × exp(-elapsed_days / decayDays)`（ADR-0003 §4.1）
- 测试 ID：`MEM-CRD-UT-001~005`（5）/ `MEM-CRD-IT-001~002`（2）= 7 ID

---

## 4. 4 A2A Method Handler（详细待 #63.2 / #63.3 补完）

### 4.1 queryKnowledge handler（H-QK · BM25 倒排索引路径 · 30 行）

- **A2A method 名**：`a2a.queryKnowledge`（**项目扩展** · 详见 L1 Architecture §6.2 line 292）
- **入口签名**：`async def query_knowledge(query: QueryKnowledgeRequest, context: ServerCallContext) -> QueryKnowledgeResponse`
- **业务流程**：
  1. 解析 `QueryKnowledgeRequest`（Pydantic v2 BaseModel）→ `query.text` / `query.scope_ref` / `query.filters`
  2. 调用 `scope_resolver.resolve(scope_ref)` 解析 4 级 scope 继承链
  3. 调用 `visibility_resolver.filter(agent_ref, scope_ref, knowledge_type)` 应用 5 维 visibility 矩阵
  4. 调用 `bm25_index.search(query.text, scope_filter, type_filter)` 异步检索（`anyio.to_thread.run_sync` 包装）
  5. 返回 `QueryKnowledgeResponse(items=[KnowledgeItemReference, ...])`
- **测试 ID**：`H-QK-UT-001~005`（5）/ `H-QK-IT-001~003`（3）/ `H-QK-CF-001`（1）/ `H-QK-E2E-001`（1）= 10 ID

### 4.2 getKnowledgeItem handler（H-GKI · 按 name + version 拉取 · 30 行）

- **A2A method 名**：`a2a.getKnowledgeItem`（**项目扩展** · 详见 L1 Architecture §6.2 line 293）
- **入口签名**：`async def get_knowledge_item(req: GetKnowledgeItemRequest, context: ServerCallContext) -> GetKnowledgeItemResponse`
- **业务流程**：
  1. 解析 `GetKnowledgeItemRequest`（Pydantic v2 BaseModel）→ `req.scope_ref` / `req.name` / `req.version`
  2. 调用 `kubernetes_asyncio.CustomObjectsApi.get_namespaced_custom_object("knowledgescope", "knowledgeitem", req.scope_ref.namespace, req.name)`
  3. 校验 `version` 匹配（如不匹配返回 `KNOWLEDGE_VERSION_MISMATCH` 错误码）
  4. 应用 5 维 visibility 矩阵（agent 是否可见）
  5. 返回 `GetKnowledgeItemResponse(item=KnowledgeItemDetail)`
- **测试 ID**：`H-GKI-UT-001~004`（4）/ `H-GKI-IT-001~002`（2）/ `H-GKI-CF-001`（1）/ `H-GKI-E2E-001`（1）= 8 ID

### 4.3 recordMemory handler（H-RM · 委托 L3-6 in-process · 30 行）

- **A2A method 名**：`a2a.recordMemory`（**项目扩展** · 详见 L1 Architecture §6.2 line 294）
- **入口签名**：`async def record_memory(req: RecordMemoryRequest, context: ServerCallContext) -> RecordMemoryResponse`
- **业务流程**：
  1. 解析 `RecordMemoryRequest`（Pydantic v2 BaseModel）→ `req.agent_ref` / `req.task_ref` / `req.content` / `req.scope_ref` / `req.decay_days`
  2. **admission 双向互斥校验**（详见 §5.3）— 校验 KnowledgeItem 与 Memory content 互斥
  3. 调用 `l3_6_in_process.record_memory(req)`（L3-6 内部 service in-process function reference；详见 §6.2）
  4. 返回 `RecordMemoryResponse(memory_ref=MemoryReference, effective_confidence=float)`
- **测试 ID**：`H-RM-UT-001~003`（3）/ `H-RM-IT-001~002`（2）/ `H-RM-CF-001`（1）/ `H-RM-E2E-001`（1）= 7 ID

### 4.4 queryMemory handler（H-QM · 委托 L3-6 in-process · 30 行）

- **A2A method 名**：`a2a.queryMemory`（**项目扩展** · 详见 L1 Architecture §6.2 line 295）
- **入口签名**：`async def query_memory(req: QueryMemoryRequest, context: ServerCallContext) -> QueryMemoryResponse`
- **业务流程**：
  1. 解析 `QueryMemoryRequest`（Pydantic v2 BaseModel）→ `req.agent_ref` / `req.scope_ref` / `req.filters` / `req.min_confidence`
  2. 调用 `l3_6_in_process.query_memory(req)`（L3-6 内部 service in-process function reference）
  3. 返回 `QueryMemoryResponse(items=[MemoryReference, ...], total_count=int)`
- **测试 ID**：`H-QM-UT-001~003`（3）/ `H-QM-IT-001~002`（2）/ `H-QM-CF-001`（1）/ `H-QM-E2E-001`（1）= 7 ID

---

## 5. Admission Webhook 双向互斥（详细待 #63.2 补完）

### 5.1 admission_validator.py（ADM · Knowledge↔Memory 互斥 · 50 行）

- **Kopf `@kopf.validation` decorator**（`@kopf.validation("knowledgeitem.create", "knowledgeitem.update")` + `@kopf.validation("memory.create", "memory.update")`）
- **互斥规则**（与 L2-4 Spec v0.2.0 §5.2 完全一致）：
  1. **同一 scope_ref + 同一 content 哈希**：KnowledgeItem 与 Memory **二选一**（agent 不能同时创建）
  2. **同一 content 哈希**：KnowledgeItem supersede 时，旧 Memory 自动标记为 `superseded_by`
  3. **scope_ref 冲突**：KnowledgeItem scope_ref 与 Memory scope_ref 不能为父子关系（避免继承循环）
- **cert-manager TLS**：L3-1 §7.1.2 webhookconfig.yaml 复用 4 webhook 配置契约
- **50ms fail-closed**：Kopf admission 超时返回 `AdmissionResponse(allowed=False, reason="admission timeout")`
- **测试 ID**：`ADM-UT-001~005`（5）/ `ADM-IT-001~003`（3，含 envtest 实际 K8s API）/ `ADM-E2E-001`（1）= 9 ID

### 5.2 KnowledgeItem vs Memory 互斥校验实现（5 步算法）

1. 计算 `content_hash = sha256(req.content).hexdigest()[:16]`
2. 查询同 `content_hash` 的 Memory CRD
3. 如存在 → 校验是否同 `agent_ref`（同 agent 允许 supersede）
4. 如存在 + 不同 agent → 拒绝（`KNOWLEDGE_MEMORY_CONFLICT` -32012）
5. 不存在 → 允许创建

### 5.3 scope_ref 父子循环检测（4 步算法）

1. 解析 `scope_ref.parent_ref` 链
2. 沿链向上追溯至 `system` scope
3. 校验链中无重复 `scope_level`
4. 重复 → 拒绝（`SCOPE_CIRCULAR_REFERENCE` -32009）

---

## 6. MemoryReconciler 协调点（详细落地见 L3-6 Memory backend Spec）

### 6.1 协调点（不重复实现 MemoryReconciler）

- **L3-5 仅暴露 4 A2A method**（§4）；不实现 MemoryReconciler 60s 周期 reconcile
- **L3-5 §5 admission 包含 Knowledge↔Memory 互斥**；不实现 Memory decay/reinforce/GC/promotion
- **L3-6 Memory backend 详细落地**：60s 周期 + Leader Election + decay 公式 + BM25 rebuild + GC 算法

### 6.2 与 L3-6 共享 Deployment 的 in-process function reference

```
Knowledge Service Pod (replicaCount: 1)
├── Container 1: knowledge-service (port 8080)
│   ├── ASGI server (L3-2 复用)
│   ├── 4 A2A method handler (L3-5 §4)
│   └── import l3_6_in_process.record_memory / query_memory
│       (in-process function reference · 同一 Pod 内 Python 进程间调用)
└── Container 2: memory-backend (port 8081)  ← L3-6 详细落地
    ├── 60s kopf.timer reconcile
    ├── Leader Election Lease
    └── export l3_6_in_process.record_memory / query_memory
        (供 Container 1 调用)
```

**进程间通信**：同一 Pod 内两个独立 Python 进程，通过共享内存或 in-process call 通信（L3-6 Spec 详细定义协议；L3-5 仅依赖接口契约）

---

## 7. Observability（详细待 #63.3 补完）

### 7.1 指标（11 A2A + 4 Python runtime + 5 Knowledge = 20 指标）

- **复用 L3-2 §9 15 指标**（11 A2A + 4 Python runtime）
- **L3-5 新增 5 个 Knowledge 指标**（`knowledge_query_total` / `knowledge_query_duration_seconds` / `knowledge_bm25_index_size` / `knowledge_memory_conflict_total` / `knowledge_admission_latency_seconds`）

### 7.2 structlog 8 必含字段（与 L3-2 §9.3 完全一致）

- `trace_id` / `agent` / `method` / `task_id` / `namespace` / `ts` / `outcome` / `latency_ms`

### 7.3 K8s Events（8 类 EventReason）

- `KnowledgeItemCreated` / `KnowledgeItemUpdated` / `KnowledgeItemDeleted` / `ScopeResolved` / `MemoryRecordStart` / `MemoryRecordEnd` / `AdmissionAllowed` / `AdmissionDenied`

---

## 8. 错误码（23 错误码 enum · 详细待 #63.3 补完）

### 8.1 11 个 KNOWLEDGE_* 错误码（-32008 ~ -32018 · JSON-RPC code）

- `KNOWLEDGE_NOT_FOUND` (-32008) / `KNOWLEDGE_VERSION_MISMATCH` (-32009) / `KNOWLEDGE_SCOPE_CIRCULAR` (-32010) / `KNOWLEDGE_INHERIT_BROKEN` (-32011) / `KNOWLEDGE_MEMORY_CONFLICT` (-32012) / `KNOWLEDGE_VISIBILITY_DENIED` (-32013) / `KNOWLEDGE_BM25_TIMEOUT` (-32014) / `KNOWLEDGE_INDEX_STALE` (-32015) / `KNOWLEDGE_INTERNAL_ERROR` (-32016) / `KNOWLEDGE_ADMISSION_TIMEOUT` (-32017) / `KNOWLEDGE_INVALID_REQUEST` (-32018)

### 8.2 12 个 MEMORY_* 错误码（-32101 ~ -32112 · JSON-RPC code）

- `MEMORY_NOT_FOUND` (-32101) / `MEMORY_CONFIDENCE_TOO_LOW` (-32102) / `MEMORY_GC_PENDING` (-32103) / `MEMORY_DECAY_EXPIRED` (-32104) / `MEMORY_LEADER_LOST` (-32105) / `MEMORY_INTERNAL_ERROR` (-32106) / `MEMORY_SCOPE_INVALID` (-32107) / `MEMORY_AGENT_MISMATCH` (-32108) / `MEMORY_TASK_MISSING` (-32109) / `MEMORY_PROMOTION_FAILED` (-32110) / `MEMORY_RECONCILE_CONFLICT` (-32111) / `MEMORY_TIMEOUT` (-32112)

### 8.3 Retryable 矩阵（与 L2-4 Spec §9.3 完全一致）

- **可重试**（5 类）：`KNOWLEDGE_BM25_TIMEOUT` / `KNOWLEDGE_INDEX_STALE` / `KNOWLEDGE_INTERNAL_ERROR` / `MEMORY_LEADER_LOST` / `MEMORY_RECONCILE_CONFLICT` / `MEMORY_TIMEOUT`
- **不可重试**（18 类）：其余 17 个 + `KNOWLEDGE_INVALID_REQUEST` + `KNOWLEDGE_VISIBILITY_DENIED`

---

## 9. Helm Values 7 模板（详细待 #63.3 补完）

### 9.1 _helpers.tpl

- 标准 K8s label + annotation 模板
- `knowledge-service.fullname` / `knowledge-service.name` / `knowledge-service.chart` / `knowledge-service.labels` / `knowledge-service.selectorLabels`

### 9.2 deployment.yaml（单实例 + 双探针 + SecurityContext）

- `replicaCount: 1`（不变量 1）
- `image.repository: superteam-a2a/knowledge-service` / `image.tag: v0.1.0` / `image.pullPolicy: IfNotPresent`
- `resources.requests: {cpu: 200m, memory: 512Mi}` / `resources.limits: {cpu: 1500m, memory: 2Gi}`
- `securityContext.runAsNonRoot: true` / `runAsUser: 65532` / `readOnlyRootFilesystem: true` / `seccompProfile: RuntimeDefault` / `capabilities.drop: ["ALL"]`
- `livenessProbe: /healthz port 8080 initialDelay 10s period 30s`
- `readinessProbe: /readyz port 8080 initialDelay 5s period 10s`
- `terminationGracePeriodSeconds: 30`

### 9.3 service.yaml（80/443 双端口 + mTLS）

- `port 80 → targetPort 8080 http`
- `port 443 → targetPort 8443 https`（mTLS）

### 9.4 serviceaccount.yaml

- `cert-manager.io/inject-ca-from: superteam-a2a/knowledge-service-serving`

### 9.5 rbac/role.yaml + rolebinding.yaml（CRD read only）

- `apiGroups: ["superteam-a2a.io"]` / `resources: ["knowledgescopes", "knowledgeitems", "memories"]` / `verbs: ["get", "list", "watch"]`

### 9.6 networkpolicy.yaml

- ingress: 8443 from operator namespace + l3-6 pod
- egress: K8s API + cert-manager + Prometheus

### 9.7 prometheusrule.yaml（6 告警规则）

- `KnowledgeQueryLatencyP99` / `KnowledgeBM25IndexStale` / `KnowledgeMemoryConflictRate` / `KnowledgeAdmissionFailureRate` / `KnowledgeServiceDown` / `KnowledgeMemoryReconcileErrorRate`

### 9.8 servicemonitor.yaml（15 + 5 指标 scrape）

- 端口 8080 / path `/metrics` / interval 30s

---

## 10. 测试策略 + 验收清单（详细待 #63.3 / #63.4 补完）

### 10.1 60 测试 ID 矩阵（与 L2-4 Spec v0.2.0 §12 完全一致）

| 层级 | 数量 | 测试 ID 前缀分布 |
|------|------|------------------|
| **UT** | 11 | KS-CRD-UT / KI-CRD-UT / MEM-CRD-UT / SCOPE-UT / VIS-UT / BM25-UT / H-QK-UT / H-GKI-UT / H-RM-UT / H-QM-UT / ERR-UT |
| **IT** | 8 | KS-CRD-IT / KI-CRD-IT / MEM-CRD-IT / ADM-IT / ENVTEST-IT / TLS-IT / MTLS-IT / E2E-WIRE-IT |
| **CF** | 3 | CF-QK / CF-GKI / CF-MEM |
| **E2E** | 3 | E2E-KNOWLEDGE / E2E-MEMORY / E2E-MUTEX |
| **TZ** | 3 | TZ-DECAY / TZ-PROMOTE / TZ-GC |
| **PERF** | 2 | PERF-BM25 / PERF-MEM |
| **DEPLOY** | 30 | HELM-* / DOCKER-* / DEPLOY-*（7 Helm + 1 Docker + 22 文件镜像） |
| **总计** | **60** | — |

### 10.2 验收清单 30 条（待 #63.3 补完）

- §10.2.1 文档完整性 5 / §10.2.2 wire contract 6 / §10.2.3 5 维矩阵 4 / §10.2.4 4 级 scope 4 / §10.2.5 admission 互斥 4 / §10.2.6 Helm 部署 4 / §10.2.7 测试矩阵 3 = 30 条

### 10.3 工具链（与 L3-1 §8.3 + L3-2 §13.3 + L3-4 §11.3 同模式）

- pyright strict + ruff format/lint + bandit + pip-audit + interrogate + import-linter（**`ST-KNOWLEDGE-BOUNDARY` 规则** + `ST-KNOWLEDGE-CONFTEST` 双重规则）+ uv + Hatchling + Docker 多阶段 + Helm 3.14 + cert-manager + kopf + OTel Collector + Argo CD

### 10.4 覆盖率

- 单元测试覆盖率 ≥ 80%（全包）/ ≥ 95%（关键模块：scope_resolver / visibility_resolver / bm25_index / admission_validator）

---

## 11. 工具链与部署（待 #63.4 补完）

- 7 步开发工作流（与 L3-1 §13.4 + L3-4 §12.4 同模式）
- 多阶段 Dockerfile（python:3.12-slim → uv build → runtime）
- cert-manager 颁发（2160h / 720h renewBefore）
- kopf 启动配置（`@kopf.timer(interval=60.0)` 仅 L3-6，L3-5 仅 `@kopf.validation` admission）
- OTel Collector sidecar
- Argo CD Application + AppSet

---

## 12. 验收清单（待 #63.4 补完）

- §A-§G 7 维度 + 30 条 + 60/60 ID 矩阵 + 7 Helm 部署交付

---

## 13. 开放问题（待 #63.4 补完 · 继承 L2-4 Design 22 项 + L3-5 新增）

- 继承 L2-4 Design v0.2.0 §1 22 项开放问题
- L3-5 新增项（与 L3-6 共享 Deployment 边界 / in-process call 协议 / `_SCOPE_CACHE` LRU 策略 / BM25 rebuild 触发条件 / admission 互斥边界）

---

## 附录 A：跨模块引用清单（v0.2-draft · 待 #63.4 补完）

### A.1 L1 引用

| L1 文档 | 章节 | 用途 | 强度 |
|---------|------|------|------|
| [L1 Architecture v0.2.0](../../design/L1-architecture.md) | §3.5.2 Knowledge Service 形态约束 | Card-driven 单实例 / 单 Python 进程 / 单 Uvicorn worker | MUST |
| [L1 Architecture v0.2.0](../../design/L1-architecture.md) | §3.5.3 MemoryReconciler 协调点 | 与 L3-5 共享 Deployment | MUST |
| [L1 Architecture v0.2.0](../../design/L1-architecture.md) | §4.3 C-6 模块映射 | `services/knowledge-service/` 代码位置 | MUST |
| [L1 Spec v0.2.0](../../spec/L1-system-spec.md) | §5.2.2 KnowledgeScope + KnowledgeItem YAML 示例 | CRD 字段约束 | MUST |
| [L1 Architecture v0.2.0](../../design/L1-architecture.md) | §6.2 4 A2A method wire | queryKnowledge / getKnowledgeItem / recordMemory / queryMemory 名 | MUST |

### A.2 L2 引用

| L2 文档 | 章节 | 用途 | 强度 |
|---------|------|------|------|
| [L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §3 3 CRD types Pydantic v2 schema | CRD field 名 / alias / Field 校验 | MUST |
| [L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §4 4 级 scope + 5 维矩阵 | scope_resolver + visibility_resolver 实现 | MUST |
| [L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §5 admission 双向互斥 | admission_validator 实现 | MUST |
| [L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §6 4 A2A method handler | handler 业务逻辑 | MUST |
| [L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §8 BM25 倒排索引 | bm25_index + retrieval_service 实现 | MUST |
| [L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §9 23 错误码 enum | ERR enum 与 JSON-RPC code 映射 | MUST |
| [L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §11 Helm values | 7 模板契约 | MUST |
| [L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §12 60 测试 ID | 镜像规则 | MUST |
| [L2-4 Spec v0.2.0](../../spec/L2-module-specs/L2-knowledge-memory.md) | §15 22 开放问题 | 状态与移交 | MUST |
| [L2-4 Design v0.2.0](../../design/L2-modules/L2-knowledge-memory.md) | §1 5 项 Python 化决策 | D-1 Pydantic / D-2 BM25 / D-3 timer / D-4 Clock / D-5 admission | MUST |
| [L2-4 Design v0.2.0](../../design/L2-modules/L2-knowledge-memory.md) | §3-§14 设计细节 | scope / visibility / admission / BM25 / MemoryReconciler | MUST |

### A.3 ADR + Constitution 引用

| 文档 | 章节 | 用途 | 强度 |
|------|------|------|------|
| [ADR-0002 知识管理设计](../../adr/0002-knowledge-management-design.md) | §3 4 级 scope 继承 | scope_resolver 算法 | MUST |
| [ADR-0002 知识管理设计](../../adr/0002-knowledge-management-design.md) | §4 5 维 visibility 矩阵 | visibility_resolver 策略表 | MUST |
| [ADR-0002 知识管理设计](../../adr/0002-knowledge-management-design.md) | §5 2 个 A2A method 业务规则 | queryKnowledge / getKnowledgeItem | MUST |
| [ADR-0003 Memory 设计](../../adr/0003-memory-design.md) | §3 Memory CRD schema | MEM-CRD | MUST |
| [ADR-0003 Memory 设计](../../adr/0003-memory-design.md) | §4.1 decay 公式 | effectiveConfidence = confidence × exp(-elapsed_days / decayDays) | MUST |
| [ADR-0003 Memory 设计](../../adr/0003-memory-design.md) | §5 admission 互斥 | KnowledgeItem vs Memory content 互斥 | MUST |
| [ADR-0005 Python-first](../../adr/0005-python-first-technology-stack.md) | §3.4 Knowledge Service 模块映射 | packages/knowledge + services/knowledge-service 双仓库 | MUST |
| [ADR-0005 Python-first](../../adr/0005-python-first-technology-stack.md) | §6.2 单进程原则 | 单 Pod / 单 Python 进程 / 单 Uvicorn worker | MUST |
| [ADR-0005 Python-first](../../adr/0005-python-first-technology-stack.md) | §6.3 CPU offload | `anyio.to_thread.run_sync` 包装 BM25 检索 | MUST |
| [ADR-0005 Python-first](../../adr/0005-python-first-technology-stack.md) | §10 structlog 字段 | 8 必含字段 | MUST |
| [ADR-0005 Python-first](../../adr/0005-python-first-technology-stack.md) | §11 静态门禁 | 6 重门禁 | MUST |
| [ADR-0005 Python-first](../../adr/0005-python-first-technology-stack.md) | §13.1 uv workspace 布局 | 双仓库路径 | MUST |
| [ADR-0005 Python-first](../../adr/0005-python-first-technology-stack.md) | §13.6 上游追踪 | a2a-sdk / kopf / kubernetes_asyncio pin | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §3.4 单进程原则 | Card-driven 单实例 | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §3.7 Python-first 边界 | 不得依赖 Adapter SDK | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §3.8 Python-first 实现栈 | 全栈 Python | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §6 mTLS + cert-manager | TLSConfig + HotReloader | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §7 可观测性 | 11+4+5 指标 + structlog + OTel + K8s Events | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §9.7 静态质量 | pyright strict + ruff + bandit + pip-audit + interrogate + import-linter | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §13.1 uv workspace | 双仓库布局 | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §14.4 评审门禁 | 每个 L3 Spec 必须通过 10 维度评审 | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §15.5 质量红线 | 覆盖率 ≥ 80% 全包 / ≥ 95% 关键模块 | MUST |
| [CONSTITUTION v0.5.0](../../../CONSTITUTION.md) | §16 会话管理 | 50% 水位 / 实际水位判断 | MUST |

### A.4 配套 L3 Spec 引用

| L3 配套 | 状态 | L3-5 引用位置 |
|---------|------|----------------|
| [L3-1 Operator Core v0.2.0](./L3-operator-core.md) | ✅ v0.2.0（#56 评审通过） | §0 + §1.5 依赖图（CRD wire sync + Helm 9 模板基础） |
| [L3-2 A2A Core v0.2.0](./L3-a2a-core.md) | ✅ v0.2.0（#54 评审通过） | §0 + §1.5（ASGI + A2AClient + 15 指标 + 24 错误码） |
| [L3-3 Adapter SDK v0.2.0](./L3-adapter-sdk.md) | ✅ v0.2.0（#58 评审通过） | §0 边界（**L3-5 不依赖 Adapter SDK**） |
| [L3-4 Hello Agent v0.2.0](./L3-hello-agent.md) | ✅ v0.2.0（#61 评审通过） | §0 + §1.5（同模式 Card-driven 单实例参考实现） |
| [L3-6 Memory backend v0.2-draft](./L3-memory-backend.md) | **待起草**（#64 启动） | §6.2 共享 Deployment 协调点（in-process function reference） |

### A.5 归档基线

| 归档文档 | 状态 | 本 Spec 用途 |
|----------|------|--------------|
| [L2-knowledge-memory-spec-v0.1.0-go-baseline.md](../../archive/pre-python-2026-07-24/L2-knowledge-memory-spec-v0.1.0-go-baseline.md) | 2026-07-26 归档丢失（与 L2-1/L2-3/L3-1/L3-2/L3-3/L3-4 同模式）· **建议 #63.x 后续会话追溯 v0.1.0 Go 归档登记** | 仅保留 4 A2A method / 4 级 scope / 5 维矩阵 / admission 互斥 / BM25 / 23 错误码 wire 业务语义 |

---

## 文档元数据与后续入口

### M.1 版本与状态

| 字段 | 值 |
|---|---|
| 版本 | **v0.2-draft**（2026-07-29 #63.1 骨架稿） |
| 状态 | 🚧 骨架稿（头部 + §0-§13 + 附录 A 占位 + §16 元数据；§3-§10 + 附录 B 待 #63.2-#63.5 补完） |
| 上游 | L1 Architecture v0.2.0 §3.5.2 + L1 Spec v0.2.0 §5.2.2 + L2-4 Spec v0.2.0 + L2-4 Design v0.2.0 |
| 同级已通过 | L3-1 Operator Core v0.2.0 (#56) + L3-2 A2A Core v0.2.0 (#54) + L3-3 Adapter SDK v0.2.0 (#58) + L3-4 Hello Agent v0.2.0 (#61) |
| 评审报告 | `docs/reviews/l3-5-knowledge-service-spec-review.md`（待 #63.5 独立评审创建） |
| 当前变更边界 | v0.2-draft 骨架；未通过独立评审；不进入 L4 实施 |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-27 #43 | L2-4 Knowledge/Memory Spec v0.2.0 评审通过 | L2-4 上游就绪 |
| 2026-07-29 #63.1（本会话） | L3-5 Knowledge Service Spec v0.2-draft 骨架稿：头部 11 段 + §0 阅读指南 + 5 项 Python 化关键决策 D-1~D-5 + 9 维度 Go→Python 对照 + §1 模块使命 + 5 项关键不变量 + 30 文件清单汇总 + 60 测试 ID 镜像规则 + 8 边界规则 + §2 Python 包结构 + §3 3 CRD types 章节结构 + §4 4 A2A method handler 章节结构 + §5 admission 双向互斥章节结构 + §6 MemoryReconciler 协调点 + §7 observability 章节结构 + §8 23 错误码章节结构 + §9 Helm values 7 模板章节结构 + §10 测试策略 60 ID 矩阵 + §11-§13 占位 + 附录 A 5 子表 + 文档元数据 M.1-M.4 | **v0.2-draft 骨架稿** → 待 #63.2-#63.5 补完 §3-§10 + 附录 B |

### M.3 配套引用

- L3-1 Operator Core v0.2.0：`docs/spec/L3-file-specs/L3-operator-core.md`（§3.1 Agent Controller + §3.4 MemoryReconciler 协调 + §7 Helm 9 模板 + §7.3 RBAC + §9 验收清单）
- L3-2 A2A Core v0.2.0：`docs/spec/L3-file-specs/L3-a2a-core.md`（§5 ASGI server + §6 A2AClient + §9 15 指标 + §10 24 错误码）
- L3-3 Adapter SDK v0.2.0：`docs/spec/L3-file-specs/L3-adapter-sdk.md`（§3 FrameworkAdapter Protocol · **L3-5 不依赖**）
- L3-4 Hello Agent v0.2.0：`docs/spec/L3-file-specs/L3-hello-agent.md`（§3.2 HelloAgentExecutor + §5 ASGI server + §6.9 25 ID 测试 · 同模式 Card-driven 单实例参考实现）
- L3-6 Memory backend v0.2-draft：`docs/spec/L3-file-specs/L3-memory-backend.md`（待 #64 启动 · §6.2 共享 Deployment 协调点）
- L2-4 Knowledge/Memory Spec v0.2.0：`docs/spec/L2-module-specs/L2-knowledge-memory.md`（CRD types + 4 A2A method + 4 级 scope + 5 维矩阵 + admission 互斥 + 60 测试 ID + 22 开放问题）
- L2-4 Knowledge/Memory Design v0.2.0：`docs/design/L2-modules/L2-knowledge-memory.md`（5 项 Python 化决策 + 9 维度 Go→Python 对照表 + 22 开放问题）
- L1 Architecture v0.2.0：`docs/design/L1-architecture.md` §3.5.2 + §4.3 C-6

### M.4 下次会话固定入口

1. **#63.2 L3-5 §3 CRD types 补完**（§3.1 KnowledgeScope 完整 Pydantic schema 60 行 / §3.2 KnowledgeItem 完整 Pydantic schema 80 行 / §3.3 Memory schema 完整 Pydantic schema 50 行 + 10/11/7 测试 ID 矩阵 = 28 ID）
2. **#63.3 L3-5 §4-§9 补完**（§4 4 A2A method handler 完整代码契约 30 行/个 = 120 行 + §5 admission_validator 完整代码契约 50 行 + §6 MemoryReconciler 协调点 完整代码契约 30 行 + §7 observability 5 指标 + K8s Events 8 类 + §8 23 错误码完整 enum + §9 Helm values 7 模板 完整契约 = 10+8+7 测试 ID = 25 ID）
3. **#63.4 L3-5 §10-§13 + 附录 A/B 补完**（§10 测试策略 60 ID 完整矩阵 + §11 工具链 + §12 验收清单 30 条 + §13 开放问题 25 项三层模式 + 附录 B ADR/Constitution 引用矩阵 5 子表）
4. **#63.5 L3-5 独立评审 + 升级 v0.2.0**（参照 L3-3 / L3-4 评审模板 40-60KB / §A-§P 10 维度 / 0 阻塞项 / 3 关注项 / 4 建议项）
5. **#63.6 L3-5 §F 6 步跨文档同步**（ROADMAP / README / CONSTITUTION-CHANGELOG / L3-1 附录 A.4 / L3-2 附录 A.4 / L3-3 附录 A.4）
6. **#64.1 L3-6 Memory backend 启动**（基于 L2-4 v0.2.0 Spec + L3-5 §6.2 共享 Deployment 协调点；建议拆 5 会话避免 §16.1 50% 临界）

### M.5 关注项台账（待 #63.5 评审后创建）

- 暂无（骨架稿未进入独立评审）

### M.6 文档元数据

- **创建日期**：2026-07-29 #63.1
- **最后更新**：2026-07-29 #63.1
- **下次更新**：#63.2（§3 CRD types 补完）
- **依赖完整性**：上游 L1 v0.2.0 + L2-4 v0.2.0 + L3-1/2/3/4 v0.2.0 全部就绪
- **下游影响**：L4 实施 Knowledge Service 工程师 + L3-6 Memory backend Spec §6.2 协调点引用

---

> **签署**：本 L3-5 Knowledge Service 文件级 Spec Python v0.2-draft 骨架稿由 #63.1 起，依据 [L1 Architecture v0.2.0 §3.5.2 + §4.3 C-6](../../design/L1-architecture.md)、[L1 Spec v0.2.0 §5.2.2 KnowledgeScope + KnowledgeItem YAML](../../spec/L1-system-spec.md)、[L2-4 Knowledge/Memory Spec v0.2.0 §3-§15](../../spec/L2-module-specs/L2-knowledge-memory.md)、[L2-4 Knowledge/Memory Design v0.2.0 §3-§14](../../design/L2-modules/L2-knowledge-memory.md)、[L3-1 Operator Core v0.2.0 §3.1 + §7](../../spec/L3-file-specs/L3-operator-core.md)、[L3-2 A2A Core v0.2.0 §5 + §6 + §9 + §10](../../spec/L3-file-specs/L3-a2a-core.md)、[L3-3 Adapter SDK v0.2.0 §3 FrameworkAdapter Protocol](../../spec/L3-file-specs/L3-adapter-sdk.md)、[L3-4 Hello Agent v0.2.0 §3.2 + §5](../../spec/L3-file-specs/L3-hello-agent.md)、[ADR-0002 知识管理设计](../../adr/0002-knowledge-management-design.md)、[ADR-0003 Memory 设计](../../adr/0003-memory-design.md)、[ADR-0005 Python-first §3.4 + §6.2 + §6.3 + §10 + §13.1](../../adr/0005-python-first-technology-stack.md) 与 Constitution v0.5.0 编写。**当前骨架稿仅具备进入 #63.2-#63.5 补完 + 独立评审的准备条件；§3-§10 + 完整附录 A/B 补完后才能进入独立评审 → 升级 v0.2.0**。
