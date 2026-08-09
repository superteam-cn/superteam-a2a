# L3 文件级 Spec：Knowledge Service（Card-driven 知识服务 · Python-first）

> **模块定位**：C-6 Knowledge Service（Card-driven 知识服务 · v0.1 · 独立 Deployment / 单 Python 进程 / 单 Uvicorn worker / 暴露 4 A2A method · 与 MemoryReconciler 共享 Deployment）
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-6（Knowledge Service，见 L1 Architecture §3.5.2 + §4.3）
> **代码位置**：
> - **CRD types**：`packages/knowledge/src/supteam_a2a/knowledge/`（KnowledgeScope + KnowledgeItem Pydantic v2 + 5 维 visibility 矩阵 + 4 级 scope 继承 + admission 双向互斥 + BM25 倒排索引）
> - **A2A Agent 部署**：`services/knowledge-service/src/supteam_a2a/knowledge_service/`（Card-driven ASGI 单进程 + 4 A2A method handler + Helm 7 模板）
> - **部署共享**：`services/knowledge-service/` 与 `services/memory-backend/` 共享同 Deployment（同 Pod 内两个独立 Python 进程；详见 L3-6 Memory backend Spec）
> - **uv workspace 布局**：ADR-0005 §13.1
> **版本**：**v0.2.0**（2026-07-29 #63.5；§3-§13 + 附录 A/B 文件级契约完整 + #63.5 独立评审通过 + #63.5.1 错误码 23 处漂移修正）
> **状态**：✅ **v0.2.0 已通过独立评审**（§A-§Q 10 维度全 PASS / 0 阻塞项 / 4 关注项（2 关闭 + 2 移交）/ 4 建议项）
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
> **配套 Spec**：[L3-1 Operator Core 文件级 Spec v0.2.0](./L3-operator-core.md)（2026-07-28 #56 评审通过 · CRD wire sync + MemoryReconciler 60s 周期）/ [L3-2 A2A Core Library 文件级 Spec v0.2.0](./L3-a2a-core.md)（2026-07-28 #54 评审通过 · ASGI + A2AClient + 15 指标 + 24 错误码）/ [L3-3 Adapter SDK 文件级 Spec v0.2.0](./L3-adapter-sdk.md)（2026-07-29 #58 评审通过 · L3-5 不依赖 Adapter SDK）/ [L3-4 Hello Agent 文件级 Spec v0.2.0](./L3-hello-agent.md)（2026-07-29 #61 评审通过 · 同模式 Card-driven 单实例参考实现）/ [L3-6 Memory backend 文件级 Spec v0.2.0](./L3-memory-backend.md)（2026-07-30 #67 评审通过 · [评审报告](../../reviews/l3-6-memory-backend-spec-review.md) 10 维度全 PASS · 共享 Deployment / MemoryReconciler 60s kopf.timer 完整落地 + MemoryBackend 抽象层 + 12 MEMORY_* 错误码零漂移）
> **配套 Review**：[L3-5 Knowledge Service Spec 评审报告](../../reviews/l3-5-knowledge-service-spec-review.md)（2026-07-29 #63.5 · 552 行 / 57KB / §A-§Q 17 节 / 10 维度全 PASS · 0 阻塞项 · 4 关注项 · 4 建议项）

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

详细文件清单见 §1.4。

### 1.4 文件清单（30 文件级契约 · 完整）

> **说明**：下表锁定 30 个文件级契约的 uv workspace 路径、职责与测试 ID 前缀；各 exported 符号与 helper 的完整契约分别在 §2-§11 展开。

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

## 3. 3 CRD Types（Pydantic v2 完整 schema · wire contract 完全继承 L2-4 v0.2.0 §3）

> **本节目的**：将 [L2-4 Spec v0.2.0 §3.2 / §3.3 / §3.4](../../spec/L2-module-specs/L2-knowledge-memory.md) 的 3 个 Pydantic v2 BaseModel 完整 schema 落地为 L3-5 文件级契约。每个 CRD 包含：(a) 完整 import 列表；(b) 完整 Pydantic v2 BaseModel 定义；(c) wire 同步矩阵（与 L2-4 v0.2.0 Spec §3 字段约束 1:1 对齐）；(d) 关联测试 ID（前缀 KS-CRD / KI-CRD / MEM-CRD）；(e) 状态机与上游引用链接。
>
> **CRD 生成链路**（继承 L2-4 Spec §3.1）：`BaseModel.model_json_schema()` → deterministic OpenAPI v3 schema（`sort_keys=True` + x-kubernetes-* extensions）→ `scripts/crd_gen.py` → checked-in CRD YAML → `kubectl apply --dry-run=server` 校验。CI 门禁：`git diff --exit-code charts/superteam-a2a/crds/` + round-trip test。
>
> **5 项 wire contract 永久不变**（与 L2-4 v0.2.0 §3.7 一致）：
> 1. 所有时间字段 `AwareDatetime`（UTC）；业务层 `datetime.now(UTC)`
> 2. 枚举用 `StrEnum`（wire 字符串值兼容）
> 3. 不可变 value object 加 `frozen=True`（SubjectReference / ScopeReference / AgentReference / ItemReference）
> 4. `populate_by_name=True` + `alias` 实现 wire camelCase ↔ Pythonic snake_case 单向映射
> 5. `extra="forbid"` 严格模式（与 K8s API server strict 校验一致）

### 3.1 KnowledgeScope CRD（KS-CRD · 6 spec + 6 status · ADR-0002 §3.1 + L2-4 v0.2.0 §3.2）

**文件路径**：`packages/knowledge/src/supteam_a2a/knowledge/crd/knowledgescope.py`

**完整 Pydantic v2 schema**（继承 L2-4 Spec v0.2.0 §3.2 完整实现 · 60 行）：

```python
# packages/knowledge/src/supteam_a2a/knowledge/crd/knowledgescope.py
# KS-CRD · Pydantic v2 BaseModel + Field(...) + populate_by_name + alias
# wire contract 完全继承 L2-4 Spec v0.2.0 §3.2
# CRD YAML 单一来源：charts/superteam-a2a/crds/knowledgescope.yaml
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, AwareDatetime
from superteam_a2a.shared.meta import ObjectMeta, Condition


class ScopeLevel(StrEnum):
    """4 级作用域枚举（ADR-0002 §3.1 + L2-4 Spec §3.2）。"""

    AGENT = "agent"  # agent-scoped；唯一 1 个 per SA
    AGENTSET = "agentset"  # agentset-scoped；多 agent 共享
    WORKFLOW = "workflow"  # workflow-scoped；任务级临时
    SYSTEM = "system"  # cluster-wide；只读


class ScopePhase(StrEnum):
    """KnowledgeScope status.phase 状态机。"""

    PENDING = "Pending"  # 创建中
    ACTIVE = "Active"  # 正常
    ARCHIVED = "Archived"  # 已归档


class SubjectKind(StrEnum):
    """Subject 引用类型。"""

    AGENT = "Agent"
    AGENTSET = "AgentSet"
    WORKFLOW = "Workflow"
    SYSTEM = "System"


class SubjectReference(BaseModel):
    """指向 Agent / AgentSet / Workflow 的不可变引用。"""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    kind: SubjectKind = Field(..., description="主体类型")
    name: str = Field(..., min_length=1, max_length=253)


class ScopeReference(BaseModel):
    """指向 KnowledgeScope 的不可变引用。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., min_length=1, max_length=128)
    level: ScopeLevel | None = Field(default=None, description="冗余缓存；admission 校验一致性")


class InheritRules(BaseModel):
    """4 级 scope 继承过滤规则（admission webhook 强制 · 与 L2-4 Spec §3.2 一致）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    include_types: list[str] | None = Field(default=None, max_length=11, alias="includeTypes")
    exclude_types: list[str] | None = Field(default=None, max_length=11, alias="excludeTypes")


class KnowledgeVisibility(StrEnum):
    """5 维 visibility 矩阵（ADR-0002 §4 + L2-4 Spec §4.5）。"""

    SCOPE_ONLY = "scope-only"
    SCOPE_AND_CHILDREN = "scope-and-children"
    PUBLIC_READABLE = "public-readable"
    AGENT_PRIVATE = "agent-private"
    SYSTEM_READONLY = "system-readonly"


class KnowledgeScopeSpec(BaseModel):
    """KnowledgeScope CRD spec（6 字段 · ADR-0002 §3.1 + L1 v0.2.0 §5.2.2）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope_level: ScopeLevel = Field(..., alias="scopeLevel", description="作用域级别")
    name: str = Field(..., min_length=1, max_length=64)
    subject_ref: SubjectReference = Field(
        ..., alias="subjectRef", description="Agent / AgentSet / Workflow 主体引用"
    )
    parent_ref: ScopeReference | None = Field(
        default=None, alias="parentRef", description="system 必须为 None；其他 level 严格递增 1 级"
    )
    inherit_rules: InheritRules | None = Field(
        default=None, alias="inheritRules", description="4 级 scope 继承过滤规则（admission 强制）"
    )
    visibility: KnowledgeVisibility = Field(
        default=KnowledgeVisibility.SCOPE_AND_CHILDREN,
        description="5 维 visibility 矩阵；PUBLIC_READABLE 仅 system scope 允许",
    )
    # 6 spec 字段 + metadata 引用类型


class KnowledgeScopeStatus(BaseModel):
    """KnowledgeScope CRD status（6 字段）。"""

    model_config = ConfigDict(extra="forbid")

    phase: ScopePhase | None = None
    observed_generation: int | None = Field(default=None, alias="observedGeneration", ge=0)
    last_updated: AwareDatetime | None = Field(default=None, alias="lastUpdated")
    child_scopes: list[ScopeReference] = Field(default_factory=list, alias="childScopes")
    knowledge_item_count: int | None = Field(default=None, alias="knowledgeItemCount", ge=0)
    active_queries_5m: int | None = Field(default=None, alias="activeQueries5m", ge=0)


class KnowledgeScope(BaseModel):
    """KnowledgeScope CRD 顶层。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(default="knowledge.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: str = Field(default="KnowledgeScope")
    metadata: ObjectMeta
    spec: KnowledgeScopeSpec
    status: KnowledgeScopeStatus | None = None
```

**wire 同步矩阵（与 L2-4 Spec v0.2.0 §3.2 字段 1:1 对齐）**：

| Spec 字段 | Python 字段 | wire alias | type | 校验 | L2-4 对齐 |
|-----------|-------------|-----------|------|------|-----------|
| `scopeLevel` | `scope_level` | `scopeLevel` | `ScopeLevel` | required · StrEnum | ✅ §3.2 L24 |
| `name` | `name` | — | `str` | min=1, max=64 | ✅ §3.2 L24 |
| `subjectRef` | `subject_ref` | `subjectRef` | `SubjectReference` | required · frozen | ✅ §3.2 L25 |
| `parentRef` | `parent_ref` | `parentRef` | `ScopeReference` | optional · frozen | ✅ §3.2 L26 |
| `inheritRules` | `inherit_rules` | `inheritRules` | `InheritRules` | optional · frozen | ✅ §3.2 L27 |
| `visibility` | `visibility` | — | `KnowledgeVisibility` | default=SCOPE_AND_CHILDREN | ✅ §3.2 L28 |

| Status 字段 | wire alias | type | 校验 | L2-4 对齐 |
|------------|-----------|------|------|-----------|
| `phase` | — | `ScopePhase` | PENDING/ACTIVE/ARCHIVED | ✅ §3.2 L32 |
| `observedGeneration` | `observedGeneration` | `int` | ge=0 | ✅ §3.2 L33 |
| `lastUpdated` | `lastUpdated` | `AwareDatetime` | UTC | ✅ §3.2 L34 |
| `childScopes` | `childScopes` | `list[ScopeReference]` | default=[] | ✅ §3.2 L35 |
| `knowledgeItemCount` | `knowledgeItemCount` | `int` | ge=0 | ✅ §3.2 L36 |
| `activeQueries5m` | `activeQueries5m` | `int` | ge=0 | ✅ §3.2 L37 |

**状态机**：Pending → Active → Archived（详见 L2-4 Spec §3.1.2）。

**关联测试 ID（KS-CRD · 10 ID）**：
- `KS-CRD-UT-001` `KnowledgeScopeSpec` 6 字段 Pydantic 校验（min_length / max_length / enum）
- `KS-CRD-UT-002` `SubjectReference` frozen + populate_by_name 双向（snake_case ↔ camelCase）
- `KS-CRD-UT-003` `ScopeReference` frozen + optional level 缓存
- `KS-CRD-UT-004` `InheritRules` include_types / exclude_types 长度 ≤ 11
- `KS-CRD-UT-005` `KnowledgeVisibility` 5 维 enum 序列化（StrEnum → JSON 字符串值）
- `KS-CRD-IT-001` `model_json_schema()` 推导确定性（`sort_keys=True` + x-kubernetes-* extensions 注入）
- `KS-CRD-IT-002` CRD YAML round-trip test（Pydantic ↔ YAML ↔ Pydantic）
- `KS-CRD-IT-003` `kubectl apply --dry-run=server -f charts/superteam-a2a/crds/knowledgescope.yaml` schema 校验

**上游引用**：
- [L2-4 Spec v0.2.0 §3.2 KnowledgeScope CRD Pydantic 完整 schema](../../spec/L2-module-specs/L2-knowledge-memory.md)（wire 完全对齐）
- [L1 Spec v0.2.0 §5.2.2 KnowledgeScope YAML 示例](../../spec/L1-system-spec.md)（CRD 字段约束）
- [ADR-0002 知识管理设计 §3 4 级 scope 继承](../../adr/0002-knowledge-management-design.md)（业务规则）
- [L2-4 Design v0.2.0 §3 KS-CRD Python 化决策 D-1](../../design/L2-modules/L2-knowledge-memory.md)
- [L3-1 Operator Core v0.2.0 §3.1 Agent Controller reconcile CRD 生命周期](../../spec/L3-file-specs/L3-operator-core.md)

### 3.2 KnowledgeItem CRD（KI-CRD · 7 spec + 7 status · ADR-0002 §3.2 + L2-4 v0.2.0 §3.3）

**文件路径**：`packages/knowledge/src/supteam_a2a/knowledge/crd/knowledgeitem.py`

**完整 Pydantic v2 schema**（继承 L2-4 Spec v0.2.0 §3.3 完整实现 · 80 行）：

```python
# packages/knowledge/src/supteam_a2a/knowledge/crd/knowledgeitem.py
# KI-CRD · Pydantic v2 BaseModel + Field(...) + populate_by_name + alias
# wire contract 完全继承 L2-4 Spec v0.2.0 §3.3
# CRD YAML 单一来源：charts/superteam-a2a/crds/knowledgeitem.yaml
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, AwareDatetime
from superteam_a2a.shared.meta import ObjectMeta, Condition
from superteam_a2a.knowledge.crd.knowledgescope import (
    ScopeReference,
    SubjectReference,
)


class KnowledgeType(StrEnum):
    """KnowledgeItem 4 类枚举（ADR-0002 §3.2 · 与 L2-4 Spec §3.3 完全一致）。"""

    PROCEDURAL = "procedural"  # 操作流程 / SOP
    FACTUAL = "factual"  # 事实知识 / 定义
    EPISODIC = "episodic"  # 事件 / 案例
    CONCEPTUAL = "conceptual"  # 概念 / 模型


class ItemPhase(StrEnum):
    """KnowledgeItem status.phase 状态机。"""

    INDEXING = "Indexing"  # 索引中
    ACTIVE = "Active"  # 正常
    DECAYING = "Decaying"  # 衰减中
    SUPERSEDED = "Superseded"  # 被新版本替代
    ARCHIVED = "Archived"  # 已归档


class ItemReference(BaseModel):
    """KnowledgeItem 不可变引用（Memory.sourceKnowledgeRef 使用）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., min_length=1, max_length=128)
    version: int = Field(..., ge=1)


class DecayState(BaseModel):
    """KnowledgeItem 衰减状态（status.effective_confidence 计算依据）。"""

    model_config = ConfigDict(extra="forbid")

    last_accessed: AwareDatetime | None = Field(default=None, alias="lastAccessed")
    access_count_24h: int = Field(default=0, alias="accessCount24h", ge=0)
    decay_days: int = Field(default=90, ge=1, le=3650, alias="decayDays")


class KnowledgeItemSpec(BaseModel):
    """KnowledgeItem CRD spec（7 字段 · ADR-0002 §3.2 + L1 v0.2.0 §5.2.3）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    scope_ref: ScopeReference = Field(..., alias="scopeRef")
    knowledge_type: KnowledgeType = Field(..., alias="knowledgeType")
    content: str = Field(..., min_length=1, max_length=65536, description="64KB Markdown body")
    tags: list[str] | None = Field(default=None, max_length=20)
    version: int = Field(default=1, ge=1)
    superseded_by: ItemReference | None = Field(
        default=None, alias="supersededBy", description="新版本引用；旧版本标记为 SUPERSEDED 状态"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="初始置信度；status.effective_confidence 由衰减公式计算",
    )
    # 7 spec 字段（距上限 15 距离 8）


class KnowledgeItemStatus(BaseModel):
    """KnowledgeItem CRD status（7 字段）。"""

    model_config = ConfigDict(extra="forbid")

    phase: ItemPhase | None = None
    indexed_at: AwareDatetime | None = Field(default=None, alias="indexedAt")
    last_accessed: AwareDatetime | None = Field(default=None, alias="lastAccessed")
    access_count_24h: int = Field(default=0, alias="accessCount24h", ge=0)
    bm25_score_avg: float | None = Field(default=None, alias="bm25ScoreAvg", ge=0.0)
    decay_state: DecayState | None = Field(default=None, alias="decayState")
    effective_confidence: float | None = Field(
        default=None, alias="effectiveConfidence", ge=0.0, le=1.0
    )


class KnowledgeItem(BaseModel):
    """KnowledgeItem CRD 顶层。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(default="knowledge.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: str = Field(default="KnowledgeItem")
    metadata: ObjectMeta
    spec: KnowledgeItemSpec
    status: KnowledgeItemStatus | None = None
```

**wire 同步矩阵（与 L2-4 Spec v0.2.0 §3.3 字段 1:1 对齐）**：

| Spec 字段 | Python 字段 | wire alias | type | 校验 | L2-4 对齐 |
|-----------|-------------|-----------|------|------|-----------|
| `scopeRef` | `scope_ref` | `scopeRef` | `ScopeReference` | required · frozen | ✅ §3.3 L26 |
| `knowledgeType` | `knowledge_type` | `knowledgeType` | `KnowledgeType` | required · StrEnum | ✅ §3.3 L27 |
| `content` | `content` | — | `str` | min=1, max=65536 | ✅ §3.3 L28 |
| `tags` | `tags` | — | `list[str]` | optional · max_length=20 | ✅ §3.3 L29 |
| `version` | `version` | — | `int` | default=1, ge=1 | ✅ §3.3 L30 |
| `supersededBy` | `superseded_by` | `supersededBy` | `ItemReference` | optional · frozen | ✅ §3.3 L31 |
| `confidence` | `confidence` | — | `float` | default=1.0, ge=0.0, le=1.0 | ✅ §3.3 L32 |

| Status 字段 | wire alias | type | 校验 | L2-4 对齐 |
|------------|-----------|------|------|-----------|
| `phase` | — | `ItemPhase` | INDEXING/ACTIVE/DECAYING/SUPERSEDED/ARCHIVED | ✅ §3.3 L37 |
| `indexedAt` | `indexedAt` | `AwareDatetime` | UTC | ✅ §3.3 L38 |
| `lastAccessed` | `lastAccessed` | `AwareDatetime` | UTC | ✅ §3.3 L39 |
| `accessCount24h` | `accessCount24h` | `int` | default=0, ge=0 | ✅ §3.3 L40 |
| `bm25ScoreAvg` | `bm25ScoreAvg` | `float` | optional, ge=0.0 | ✅ §3.3 L41 |
| `decayState` | `decayState` | `DecayState` | optional | ✅ §3.3 L42 |
| `effectiveConfidence` | `effectiveConfidence` | `float` | optional, ge=0.0, le=1.0 | ✅ §3.3 L43 |

**状态机**：Indexing → Active → Decaying → Superseded → Archived（详见 L2-4 Spec §3.3）。

**关联测试 ID（KI-CRD · 11 ID）**：
- `KI-CRD-UT-001` `KnowledgeItemSpec` 7 字段 Pydantic 校验（content 64KB 上限 · confidence [0,1]）
- `KI-CRD-UT-002` `KnowledgeType` 4 类 enum 序列化（procedural/factual/episodic/conceptual）
- `KI-CRD-UT-003` `ItemReference` frozen + version 必填
- `KI-CRD-UT-004` `DecayState` 嵌套 status（last_accessed / access_count_24h / decay_days）
- `KI-CRD-UT-005` `superseded_by` 链校验（v3.supersededBy → v2 → v1 单调）
- `KI-CRD-UT-006` tags 长度 ≤ 20 + 字符串去重
- `KI-CRD-UT-007` `KnowledgeItemStatus` phase 状态机转换校验
- `KI-CRD-IT-001` `model_json_schema()` 推导确定性 + x-kubernetes-* extensions 注入
- `KI-CRD-IT-002` CRD YAML round-trip test + 7 status 字段映射
- `KI-CRD-IT-003` `kubectl apply --dry-run=server -f charts/superteam-a2a/crds/knowledgeitem.yaml` schema 校验

**上游引用**：
- [L2-4 Spec v0.2.0 §3.3 KnowledgeItem CRD Pydantic 完整 schema](../../spec/L2-module-specs/L2-knowledge-memory.md)（wire 完全对齐）
- [L1 Spec v0.2.0 §5.2.2 KnowledgeItem YAML 示例](../../spec/L1-system-spec.md)
- [ADR-0002 知识管理设计 §3.2 KnowledgeItem 字段约束](../../adr/0002-knowledge-management-design.md)
- [L2-4 Design v0.2.0 §3 KI-CRD Python 化决策 D-1](../../design/L2-modules/L2-knowledge-memory.md)

### 3.3 Memory Schema（MEM-CRD · 5 spec + 5 status · ADR-0003 §3 + L2-4 v0.2.0 §3.4）

**文件路径**：`packages/knowledge/src/supteam_a2a/knowledge/crd/memory_schema.py`（注：`memory_schema.py` 而非 `memory.py`，避免与 L2-4 `packages/memory/src/supteam_a2a/memory/apis/v1alpha1/memory.py` 命名冲突）

**完整 Pydantic v2 schema**（继承 L2-4 Spec v0.2.0 §3.4 完整实现 · 50 行）：

```python
# packages/knowledge/src/supteam_a2a/knowledge/crd/memory_schema.py
# MEM-CRD · Pydantic v2 BaseModel + Field(...) + populate_by_name + alias
# wire contract 完全继承 L2-4 Spec v0.2.0 §3.4（与 L2-4 packages/memory/apis/v1alpha1/memory.py 对齐）
# CRD YAML 单一来源：charts/superteam-a2a/crds/memory.yaml
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, AwareDatetime
from superteam_a2a.shared.meta import ObjectMeta, Condition
from superteam_a2a.knowledge.crd.knowledgescope import (
    ScopeReference,
    SubjectReference,
    SubjectKind,
)


class MemoryPhase(StrEnum):
    """Memory status.phase 5 态状态机（ADR-0003 §3 + L2-4 Spec §3.4）。"""

    ACTIVE = "Active"  # effective_confidence > 0.5
    DECAYING = "Decaying"  # 0.01 ≤ effective_confidence ≤ 0.5
    PROMOTABLE = "Promotable"  # eligible_for_promotion = true（v0.1 仅算不触发）
    EXPIRED = "Expired"  # effective_confidence < 0.01
    ERROR = "Error"  # reconcile 失败


class GCState(StrEnum):
    """Memory GC 状态机（L3-6 详细落地 · L3-5 仅作为 schema 字段）。"""

    NONE = "None"  # 未标记
    PENDING = "Pending"  # 待清理
    CLEANED = "Cleaned"  # 已清理
    KEPT = "Kept"  # 保留（reinforce 后）


class TaskReference(BaseModel):
    """Memory 关联任务引用（Workflow scope 必填；Agent / AgentSet scope 可选）。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., min_length=1, max_length=128)
    namespace: str = Field(default="default", min_length=1, max_length=128)


class MemorySpec(BaseModel):
    """Memory CRD spec（5 字段 · ADR-0003 §3 + L2-4 Spec §3.4 · 注：L3-5 复用 KS-CRD 文件路径下；L3-6 packages/memory/ 也有完整定义；二者 wire 完全一致）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    subject: str = Field(
        ..., min_length=1, max_length=253, description="三元组主语（Agent name / Workflow name 等）"
    )
    predicate: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="三元组谓词（如 'has-skill' / 'completed-task' / 'observed-event'）",
    )
    object: str = Field(
        ..., min_length=1, max_length=512, description="三元组宾语（free-form 字符串值）"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="初始置信度；status.effective_confidence 由衰减公式计算",
    )
    decay_days: int = Field(
        default=30, ge=1, le=3650, alias="decayDays", description="decay 半衰期；超过 3650 拒绝"
    )
    # 5 spec 字段（距上限 15 距离 10；与 L2-4 §3.4 12 字段版差异：L3-5 简化字段集，详细完整版由 L3-6 落地）


class MemoryStatus(BaseModel):
    """Memory CRD status（5 字段）。"""

    model_config = ConfigDict(extra="forbid")

    phase: MemoryPhase | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    effective_confidence: float | None = Field(
        default=None,
        alias="effectiveConfidence",
        ge=0.0,
        le=1.0,
        description="effectiveConfidence = confidence × exp(-elapsed_days / decayDays)（ADR-0003 §4.1）",
    )
    last_reinforced: AwareDatetime | None = Field(default=None, alias="lastReinforced")
    gc_state: GCState = Field(default=GCState.NONE, alias="gcState")


class Memory(BaseModel):
    """Memory CRD 顶层。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(default="memory.superteam-a2a.io/v1alpha1", alias="apiVersion")
    kind: str = Field(default="Memory")
    metadata: ObjectMeta
    spec: MemorySpec
    status: MemoryStatus | None = None
```

**wire 同步矩阵（与 L2-4 Spec v0.2.0 §3.4 字段 1:1 对齐 · 5+5 简化字段集）**：

| Spec 字段 | Python 字段 | wire alias | type | 校验 | L2-4 对齐 |
|-----------|-------------|-----------|------|------|-----------|
| `subject` | `subject` | — | `str` | min=1, max=253 | ✅ §3.4 L24（三元组主语） |
| `predicate` | `predicate` | — | `str` | min=1, max=128 | ✅ §3.4 L25（三元组谓词） |
| `object` | `object` | — | `str` | min=1, max=512 | ✅ §3.4 L26（三元组宾语） |
| `confidence` | `confidence` | — | `float` | default=1.0, ge=0.0, le=1.0 | ✅ §3.4 L27 |
| `decayDays` | `decay_days` | `decayDays` | `int` | default=30, ge=1, le=3650 | ✅ §3.4 L28 |

| Status 字段 | wire alias | type | 校验 | L2-4 对齐 |
|------------|-----------|------|------|-----------|
| `phase` | — | `MemoryPhase` | ACTIVE/DECAYING/PROMOTABLE/EXPIRED/ERROR | ✅ §3.4 L34 |
| `confidence` | — | `float` | optional, ge=0.0, le=1.0 | ✅ §3.4 L35 |
| `effectiveConfidence` | `effectiveConfidence` | `float` | optional, ge=0.0, le=1.0 | ✅ §3.4 L36 |
| `lastReinforced` | `lastReinforced` | `AwareDatetime` | UTC | ✅ §3.4 L37 |
| `gcState` | `gcState` | `GCState` | default=NONE | ✅ §3.4 L38 |

**衰减公式**（ADR-0003 §4.1 + L2-4 Spec §3.4）：

```
effectiveConfidence = confidence × exp(-elapsed_days / decayDays)
```

其中：
- `confidence` = Memory spec.confidence（初始置信度）
- `elapsed_days` = (now - last_reinforced) / 86400
- `decayDays` = Memory spec.decay_days
- 当 `effectiveConfidence < 0.01` 时 status.phase 转为 `EXPIRED`（L3-6 60s kopf.timer 详细落地）

**关联测试 ID（MEM-CRD · 7 ID）**：
- `MEM-CRD-UT-001` `MemorySpec` 5 字段 Pydantic 校验（三元组 subject / predicate / object + confidence + decayDays）
- `MEM-CRD-UT-002` `MemoryPhase` 5 态 enum 序列化（ACTIVE/DECAYING/PROMOTABLE/EXPIRED/ERROR）
- `MEM-CRD-UT-003` `GCState` 4 态 enum（NONE/PENDING/CLEANED/KEPT）
- `MEM-CRD-UT-004` `decay_days` 边界校验（ge=1, le=3650；超过 3650 拒绝）
- `MEM-CRD-UT-005` `effective_confidence` 衰减公式（confidence × exp(-elapsed_days / decayDays)）纯函数单元测试
- `MEM-CRD-IT-001` `model_json_schema()` 推导确定性 + x-kubernetes-* extensions 注入
- `MEM-CRD-IT-002` CRD YAML round-trip test + 5+5 status 字段映射 + 衰减公式常量校验

**上游引用**：
- [L2-4 Spec v0.2.0 §3.4 Memory CRD Pydantic 完整 schema](../../spec/L2-module-specs/L2-knowledge-memory.md)（wire 完全对齐 · 12 spec 字段完整版）
- [ADR-0003 Memory 设计 §3 Memory CRD schema + §4.1 decay 公式](../../adr/0003-memory-design.md)
- [L2-4 Design v0.2.0 §3 MEM-CRD Python 化决策 D-1](../../design/L2-modules/L2-knowledge-memory.md)
- [L3-6 Memory backend v0.2-draft §6 MemoryReconciler 60s kopf.timer 详细落地](./L3-memory-backend.md)（待 #64 起草）

---

**§3 总结**：
- **3 CRD types 共 18 spec + 19 status 字段**，全部 wire contract 永久不变（与 L2-4 v0.2.0 §3 完全一致）
- **28 测试 ID 命名规范**（KS-CRD × 8 / KI-CRD × 10 / MEM-CRD × 7 · 含 UT + IT + CF）
- **wire 同步矩阵**：3 个 CRD 各 1 张表（与 L2-4 v0.2.0 §3.2 / §3.3 / §3.4 字段 1:1 对齐）
- **CRD 生成链路**：Pydantic `model_json_schema()` → OpenAPI v3 → CRD YAML → `kubectl apply --dry-run=server`

---

## 4. 4 A2A Method Handler（Python Protocol + 30 行/个 · wire contract 完全继承 L2-4 v0.2.0 §6）

> **本节目的**：将 [L2-4 Spec v0.2.0 §6.2 / §6.3 / §6.4 / §6.5](../../spec/L2-module-specs/L2-knowledge-memory.md) 的 4 个 A2A method handler 落地为 L3-5 文件级 Python Protocol 契约（**完整 30 行/个**，参照 L3-4 Hello Agent §3.2 `HelloAgentExecutor` 模式）。每个 handler 包含：(a) 完整 Pydantic v2 Request/Response schema；(b) Python Protocol（`@runtime_checkable`）；(c) BM25 检索路径 / 委托 L3-6 调用契约 / 5 维 visibility 过滤；(d) wire 同步矩阵（与 L2-4 v0.2.0 §6 字段 1:1 对齐）；(e) 关联测试 ID（前缀 H-QK / H-GKI / H-RM / H-QM）。
>
> **5 项关键不变量**（来自 §1.2）：
> 1. **method 名永久不变**：`queryKnowledge` / `getKnowledgeItem` / `recordMemory` / `queryMemory`（与 L2-1 Spec v0.2.0 §3 envelope 一致）
> 2. **envelope 完全继承 L2-4 v0.2.0 §6**：camelCase wire ↔ snake_case Python（`populate_by_name=True` + `alias`）
> 3. **Knowledge 2 method（queryKnowledge / getKnowledgeItem）由 L3-5 实现**；Memory 2 method（recordMemory / queryMemory）**委托 L3-6 in-process function reference**（共享 Deployment）
> 4. **不依赖 L3-3 Adapter SDK**（Card-driven 直接实现 A2A 端点）
> 5. **不实现业务 Agent 逻辑**（仅暴露 4 A2A method 端点）

### 4.1 queryKnowledge handler（H-QK · BM25 倒排索引路径 · 30 行）

**A2A method 名**：`a2a.queryKnowledge`（**项目扩展** · 与 L1 Architecture §6.2 line 292 + L2-4 Spec v0.2.0 §6.2 完全一致）

**文件路径**：`services/knowledge-service/src/supteam_a2a/knowledge_service/handlers/query_knowledge.py`

**完整 Python Protocol + 30 行实现**：

```python
# services/knowledge-service/src/supteam_a2a/knowledge_service/handlers/query_knowledge.py
# H-QK · a2a.queryKnowledge handler · BM25 倒排索引路径
# wire contract 完全继承 L2-4 Spec v0.2.0 §6.2
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field, ConfigDict
import anyio
from superteam_a2a.a2a.upstream import A2AError, ServerCallContext
from superteam_a2a.knowledge.crd.knowledgeitem import KnowledgeItemSummary
from superteam_a2a.knowledge_service.deps import (
    get_scope_resolver,
    get_bm25_index,
    get_visibility_resolver,
)


class QueryKnowledgeRequest(BaseModel):
    """queryKnowledge 入参 · wire alias camelCase（继承 L2-4 §6.2）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    query: str = Field(..., min_length=1, max_length=512)
    scope_filter: ScopeReference | None = Field(default=None, alias="scopeFilter")
    visibility_filter: KnowledgeVisibility | None = Field(default=None, alias="visibilityFilter")
    max_results: int = Field(default=10, ge=1, le=50, alias="maxResults")


class QueryKnowledgeResponse(BaseModel):
    """queryKnowledge 返回值 · wire alias camelCase。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    items: list[KnowledgeItemSummary]
    total_count: int = Field(..., ge=0, alias="totalCount")


@runtime_checkable
class QueryKnowledgeHandler(Protocol):
    """queryKnowledge handler Protocol；4 handler 共同实现此契约。"""

    async def __call__(
        self, req: QueryKnowledgeRequest, ctx: ServerCallContext
    ) -> QueryKnowledgeResponse: ...


async def handle_query_knowledge(
    req: QueryKnowledgeRequest, ctx: ServerCallContext
) -> QueryKnowledgeResponse:
    """a2a.queryKnowledge 业务实现（BM25 + 5 维 visibility 过滤）。"""
    scope_resolver = get_scope_resolver()
    bm25 = get_bm25_index()
    vis = get_visibility_resolver()
    scope_chain = await scope_resolver.resolve(req.scope_filter)  # 4 级 scope 解析
    candidates = await anyio.to_thread.run_sync(  # CPU offload（D-2）
        bm25.search, req.query, scope_chain, req.max_results * 2
    )
    visible = [c for c in candidates if vis.is_visible(ctx.caller_agent, c, req.visibility_filter)]
    items = [
        KnowledgeItemSummary(
            name=c.name,
            scope=c.scope,
            type=c.type,
            title=c.title,
            summary=c.summary,
            version=c.version,
            relevance_score=c.bm25_score,
        )
        for c in visible[: req.max_results]
    ]
    return QueryKnowledgeResponse(items=items, total_count=len(items))
```

**wire 同步矩阵（与 L2-4 Spec v0.2.0 §6.2 字段 1:1 对齐）**：

| Request 字段 | Python 字段 | wire alias | type | 校验 | L2-4 对齐 |
|-------------|-------------|-----------|------|------|-----------|
| `query` | `query` | — | `str` | min=1, max=512 | ✅ §6.2 L13 |
| `scopeFilter` | `scope_filter` | `scopeFilter` | `ScopeReference` | optional · frozen | ✅ §6.2 L14 |
| `visibilityFilter` | `visibility_filter` | `visibilityFilter` | `KnowledgeVisibility` | optional · StrEnum | ✅ §6.2 L15 |
| `maxResults` | `max_results` | `maxResults` | `int` | default=10, ge=1, le=50 | ✅ §6.2 L16 |

| Response 字段 | wire alias | type | 校验 | L2-4 对齐 |
|-------------|-----------|------|------|-----------|
| `items` | — | `list[KnowledgeItemSummary]` | required | ✅ §6.2 L19 |
| `totalCount` | `totalCount` | `int` | ge=0 | ✅ §6.2 L20 |

**业务流程**：
1. 解析 `QueryKnowledgeRequest`（Pydantic v2 自动校验 `query` 长度 / `scope_filter` / `visibility_filter`）
2. 调用 `scope_resolver.resolve(scope_filter)` 解析 4 级 scope 继承链（agent / agentset / workflow / system；详见 §3.1 ScopeLevel）
3. 调用 `visibility_resolver.is_visible(caller_agent, item, visibility_filter)` 应用 5 维 visibility 矩阵过滤
4. 调用 `bm25_index.search(query.text, scope_chain, max_results * 2)` 异步检索（`anyio.to_thread.run_sync` 包装 · D-2 Python 化决策）
5. 截取 top `max_results` 条；返回 `QueryKnowledgeResponse`

**关联测试 ID（H-QK · 10 ID）**：
- `H-QK-UT-001` `QueryKnowledgeRequest` Pydantic 校验（query min=1 max=512 · maxResults [1,50]）
- `H-QK-UT-002` `QueryKnowledgeResponse` schema 校验（items list · totalCount ≥ 0）
- `H-QK-UT-003` BM25 倒排索引纯函数（`dict[str, set[str]]` + IDF 公式 · K1=1.5 / B=0.75）
- `H-QK-UT-004` 5 维 visibility 矩阵过滤（agent-private 短路 · PUBLIC_READABLE 仅 system scope）
- `H-QK-UT-005` `anyio.to_thread.run_sync` CPU offload（thread pool size = 4 · timeout 200ms）
- `H-QK-IT-001` scope_resolver 4 级继承链解析（agent → agentset → workflow → system）
- `H-QK-IT-002` BM25 检索 10K items P95 ≤ 200ms（性能门禁）
- `H-QK-IT-003` visibility 拒绝场景（agent-private 项不可见）
- `H-QK-CF-001` wire contract 一致性测试（与 L2-4 §6.2 schema 比对）
- `H-QK-E2E-001` 端到端 e2e（CRD apply → queryKnowledge A2A call → response）

**上游引用**：
- [L2-4 Spec v0.2.0 §6.2 `a2a.queryKnowledge` handler 完整实现](../../spec/L2-module-specs/L2-knowledge-memory.md)
- [L2-4 Spec v0.2.0 §8 BM25 倒排索引](../../spec/L2-module-specs/L2-knowledge-memory.md)（K1=1.5 / B=0.75 / IDF 公式）
- [L2-4 Design v0.2.0 §3 D-2 BM25 检索 Python 化决策](../../design/L2-modules/L2-knowledge-memory.md)
- [L3-2 A2A Core v0.2.0 §5 ASGI server 单进程原则 + §9 15 指标](../../spec/L3-file-specs/L3-a2a-core.md)
- [ADR-0005 §6.3 CPU offload（anyio.to_thread.run_sync）](../../adr/0005-python-first-technology-stack.md)

### 4.2 getKnowledgeItem handler（H-GKI · 按 name + version 拉取 · 30 行）

**A2A method 名**：`a2a.getKnowledgeItem`（**项目扩展** · 与 L1 Architecture §6.2 line 293 + L2-4 Spec v0.2.0 §6.3 完全一致）

**文件路径**：`services/knowledge-service/src/supteam_a2a/knowledge_service/handlers/get_knowledge_item.py`

**完整 Python Protocol + 30 行实现**：

```python
# services/knowledge-service/src/supteam_a2a/knowledge_service/handlers/get_knowledge_item.py
# H-GKI · a2a.getKnowledgeItem handler · 按 name + version 拉取 + 5 维 visibility
# wire contract 完全继承 L2-4 Spec v0.2.0 §6.3
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field, ConfigDict
from superteam_a2a.a2a.upstream import A2AError, ServerCallContext, ErrorCode
from superteam_a2a.knowledge.crd.knowledgeitem import KnowledgeItem, ItemReference
from superteam_a2a.knowledge.crd.knowledgescope import ScopeReference
from superteam_a2a.knowledge_service.deps import get_k8s_client, get_visibility_resolver
from superteam_a2a.knowledge_service.errors import KNOWLEDGE_VERSION_NOT_FOUND


class GetKnowledgeItemRequest(BaseModel):
    """getKnowledgeItem 入参 · wire alias camelCase（继承 L2-4 §6.3）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scope_ref: ScopeReference = Field(..., alias="scopeRef")
    name: str = Field(..., min_length=1, max_length=128)
    version: int | None = Field(default=None, ge=1)


class GetKnowledgeItemResponse(BaseModel):
    """getKnowledgeItem 返回值 · wire alias camelCase。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    item: KnowledgeItem  # 完整 Pydantic 对象
    item_ref: ItemReference = Field(..., alias="itemRef")


@runtime_checkable
class GetKnowledgeItemHandler(Protocol):
    """getKnowledgeItem handler Protocol。"""

    async def __call__(
        self, req: GetKnowledgeItemRequest, ctx: ServerCallContext
    ) -> GetKnowledgeItemResponse: ...


async def handle_get_knowledge_item(
    req: GetKnowledgeItemRequest, ctx: ServerCallContext
) -> GetKnowledgeItemResponse:
    """a2a.getKnowledgeItem 业务实现（K8s API 拉取 + 父子链解析 + 5 维 visibility）。"""
    k8s = get_k8s_client()
    vis = get_visibility_resolver()
    raw = await k8s.get_namespaced_custom_object(  # KnowledgeItem CR 拉取
        group="knowledge.superteam-a2a.io",
        version="v1alpha1",
        namespace=req.scope_ref.namespace,
        plural="knowledgeitems",
        name=req.name,
    )
    item = KnowledgeItem.model_validate(raw)
    if req.version is not None and item.spec.version != req.version:  # version 匹配校验
        raise A2AError(
            KNOWLEDGE_VERSION_NOT_FOUND,
            f"version {req.version} != {item.spec.version} (item latest={item.spec.version})",
        )
    if not vis.is_visible(ctx.caller_agent, item, None):  # 5 维 visibility 过滤
        raise A2AError(404, f"KnowledgeItem {req.name} not visible")
    return GetKnowledgeItemResponse(
        item=item, item_ref=ItemReference(name=item.metadata.name, version=item.spec.version)
    )
```

**wire 同步矩阵（与 L2-4 Spec v0.2.0 §6.3 字段 1:1 对齐）**：

| Request 字段 | Python 字段 | wire alias | type | 校验 | L2-4 对齐 |
|-------------|-------------|-----------|------|------|-----------|
| `scopeRef` | `scope_ref` | `scopeRef` | `ScopeReference` | required · frozen | ✅ §6.3 L19 |
| `name` | `name` | — | `str` | min=1, max=128 | ✅ §6.3 L20 |
| `version` | `version` | — | `int` | optional · ge=1 | ✅ §6.3 L21 |

| Response 字段 | wire alias | type | L2-4 对齐 |
|-------------|-----------|------|-----------|
| `item` | — | `KnowledgeItem` | ✅ §6.3 L24 |
| `itemRef` | `itemRef` | `ItemReference` | ✅ §6.3 L25 |

**业务流程**：
1. 解析 `GetKnowledgeItemRequest`（Pydantic 自动校验）
2. 调用 `kubernetes_asyncio.CustomObjectsApi.get_namespaced_custom_object("knowledge.superteam-a2a.io/v1alpha1", "knowledgeitems", namespace, name)` 拉取 CRD
3. 校验 `version` 匹配（如不匹配返回 `KNOWLEDGE_VERSION_NOT_FOUND` -32013；详见 §8.1）
4. 应用 5 维 visibility 矩阵（agent-private 短路；PUBLIC_READABLE 仅 system scope 允许）
5. 返回 `GetKnowledgeItemResponse(item, item_ref)`

**关联测试 ID（H-GKI · 8 ID）**：
- `H-GKI-UT-001` `GetKnowledgeItemRequest` Pydantic 校验（scope_ref required · name min=1 max=128）
- `H-GKI-UT-002` `GetKnowledgeItemResponse` schema 校验（item + itemRef 完整）
- `H-GKI-UT-003` version 匹配校验（version 不匹配 → KNOWLEDGE_VERSION_NOT_FOUND）
- `H-GKI-UT-004` 5 维 visibility 拒绝场景（agent-private 项不可见）
- `H-GKI-IT-001` K8s API mock（`respx` mock `get_namespaced_custom_object` 返回 fixture）
- `H-GKI-IT-002` scope_ref 父子链解析（child_scopes 递归）
- `H-GKI-CF-001` wire contract 一致性测试（与 L2-4 §6.3 schema 比对）
- `H-GKI-E2E-001` 端到端 e2e（CRD apply → getKnowledgeItem A2A call → response）

**上游引用**：
- [L2-4 Spec v0.2.0 §6.3 `a2a.getKnowledgeItem` handler 完整实现](../../spec/L2-module-specs/L2-knowledge-memory.md)
- [L3-1 Operator Core v0.2.0 §3.1 Agent Controller reconcile CRD 生命周期](../../spec/L3-file-specs/L3-operator-core.md)

### 4.3 recordMemory handler（H-RM · 委托 L3-6 in-process · 30 行）

**A2A method 名**：`a2a.recordMemory`（**项目扩展** · 与 L1 Architecture §6.2 line 294 + L2-4 Spec v0.2.0 §6.4 完全一致）

**文件路径**：`services/knowledge-service/src/supteam_a2a/knowledge_service/handlers/record_memory.py`

**完整 Python Protocol + 30 行实现**：

```python
# services/knowledge-service/src/supteam_a2a/knowledge_service/handlers/record_memory.py
# H-RM · a2a.recordMemory handler · 委托 L3-6 in-process function reference（共享 Deployment）
# wire contract 完全继承 L2-4 Spec v0.2.0 §6.4
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from superteam_a2a.a2a.upstream import A2AError, ServerCallContext
from superteam_a2a.knowledge.crd.memory_schema import Memory, MemorySpec, MemoryPhase
from superteam_a2a.knowledge.crd.knowledgescope import ScopeReference
from superteam_a2a.knowledge_service.admission_validator import validate_knowledge_memory_mutex
from superteam_a2a.knowledge_service.l3_6_in_process import record_memory_async


class RecordMemoryRequest(BaseModel):
    """recordMemory 入参 · wire alias camelCase（继承 L2-4 §6.4）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    agent_ref: AgentReference = Field(..., alias="agentRef")
    task_ref: TaskReference | None = Field(default=None, alias="taskRef")
    content: str = Field(..., min_length=1, max_length=512)
    scope_ref: ScopeReference = Field(..., alias="scopeRef")
    decay_days: int = Field(default=30, ge=1, le=3650, alias="decayDays")


class RecordMemoryResponse(BaseModel):
    """recordMemory 返回值 · wire alias camelCase。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    memory_ref: MemoryReference = Field(..., alias="memoryRef")
    effective_confidence: float = Field(..., alias="effectiveConfidence", ge=0.0, le=1.0)


@runtime_checkable
class RecordMemoryHandler(Protocol):
    """recordMemory handler Protocol；委托 L3-6。"""

    async def __call__(
        self, req: RecordMemoryRequest, ctx: ServerCallContext
    ) -> RecordMemoryResponse: ...


async def handle_record_memory(
    req: RecordMemoryRequest, ctx: ServerCallContext
) -> RecordMemoryResponse:
    """a2a.recordMemory 业务实现（admission 互斥 + 委托 L3-6）。"""
    await validate_knowledge_memory_mutex(req)  # admission 双向互斥校验（§5）
    mem = Memory(
        metadata=ObjectMeta(name=...),
        spec=MemorySpec(
            subject=req.agent_ref.name,
            predicate="record",
            object=req.content,
            confidence=1.0,
            decay_days=req.decay_days,
        ),
    )
    result = await record_memory_async(mem)  # 委托 L3-6 in-process（§6.2）
    return RecordMemoryResponse(
        memory_ref=MemoryReference(name=mem.metadata.name),
        effective_confidence=result.effective_confidence,
    )
```

**wire 同步矩阵（与 L2-4 Spec v0.2.0 §6.4 字段 1:1 对齐）**：

| Request 字段 | Python 字段 | wire alias | type | 校验 | L2-4 对齐 |
|-------------|-------------|-----------|------|------|-----------|
| `agentRef` | `agent_ref` | `agentRef` | `AgentReference` | required · ServiceAccount only | ✅ §6.4 L13 |
| `taskRef` | `task_ref` | `taskRef` | `TaskReference` | optional · frozen | ✅ §6.4 L14 |
| `content` | `content` | — | `str` | min=1, max=512 | ✅ §6.4 L15 |
| `scopeRef` | `scope_ref` | `scopeRef` | `ScopeReference` | required · frozen | ✅ §6.4 L16 |
| `decayDays` | `decay_days` | `decayDays` | `int` | default=30, ge=1, le=3650 | ✅ §6.4 L17 |

| Response 字段 | wire alias | type | 校验 | L2-4 对齐 |
|-------------|-----------|------|------|-----------|
| `memoryRef` | `memoryRef` | `MemoryReference` | required | ✅ §6.4 L21 |
| `effectiveConfidence` | `effectiveConfidence` | `float` | ge=0.0, le=1.0 | ✅ §6.4 L22 |

**业务流程**：
1. 解析 `RecordMemoryRequest`（Pydantic 自动校验）
2. **admission 双向互斥校验**（详见 §5.2 / §5.3）— KnowledgeItem vs Memory content 互斥 + scope_ref 父子循环检测
3. 调用 `record_memory_async(memory_obj)`（L3-6 in-process function reference · 共享 Deployment 同 Pod 内 Python 进程间调用；详见 §6.2）
4. 返回 `RecordMemoryResponse(memory_ref, effective_confidence)`

**关联测试 ID（H-RM · 7 ID）**：
- `H-RM-UT-001` `RecordMemoryRequest` Pydantic 校验（agent_ref required ServiceAccount · decayDays [1, 3650]）
- `H-RM-UT-002` `RecordMemoryResponse` schema 校验（memory_ref + effectiveConfidence [0,1]）
- `H-RM-UT-003` admission 双向互斥校验（KnowledgeItem vs Memory content 同 hash 拒绝）
- `H-RM-IT-001` L3-6 in-process function reference 调用契约（async def + exception propagation）
- `H-RM-IT-002` rate limit 60/min per SA（与 L2-4 §6.4 一致）
- `H-RM-CF-001` wire contract 一致性测试（与 L2-4 §6.4 schema 比对）
- `H-RM-E2E-001` 端到端 e2e（recordMemory A2A call → L3-6 in-process → K8s API apply → response）

**上游引用**：
- [L2-4 Spec v0.2.0 §6.4 `a2a.recordMemory` handler 完整实现](../../spec/L2-module-specs/L2-knowledge-memory.md)
- [L3-6 Memory backend v0.2-draft §6 MemoryReconciler 60s kopf.timer 详细落地](./L3-memory-backend.md)（待 #64 起草）
- [§6.2 与 L3-6 共享 Deployment 的 in-process function reference](#62-与-l3-6-共享-deployment-的-in-process-function-reference)

### 4.4 queryMemory handler（H-QM · 委托 L3-6 in-process · 30 行）

**A2A method 名**：`a2a.queryMemory`（**项目扩展** · 与 L1 Architecture §6.2 line 295 + L2-4 Spec v0.2.0 §6.5 完全一致）

**文件路径**：`services/knowledge-service/src/supteam_a2a/knowledge_service/handlers/query_memory.py`

**完整 Python Protocol + 30 行实现**：

```python
# services/knowledge-service/src/supteam_a2a/knowledge_service/handlers/query_memory.py
# H-QM · a2a.queryMemory handler · 委托 L3-6 in-process function reference（共享 Deployment）
# wire contract 完全继承 L2-4 Spec v0.2.0 §6.5
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field, ConfigDict
from superteam_a2a.a2a.upstream import A2AError, ServerCallContext
from superteam_a2a.knowledge.crd.knowledgescope import ScopeReference
from superteam_a2a.knowledge_service.l3_6_in_process import query_memory_async


class QueryMemoryRequest(BaseModel):
    """queryMemory 入参 · wire alias camelCase（继承 L2-4 §6.5）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    agent_ref: AgentReference = Field(..., alias="agentRef")
    scope_ref: ScopeReference | None = Field(default=None, alias="scopeRef")
    filters: dict[str, str] | None = None
    min_confidence: float | None = Field(default=None, alias="minConfidence", ge=0.0, le=1.0)


class MemoryReference(BaseModel):
    """Memory 引用（Pydantic · 与 L2-4 §6.5 wire 完全一致）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str
    subject: str
    predicate: str
    effective_confidence: float = Field(..., alias="effectiveConfidence", ge=0.0, le=1.0)


class QueryMemoryResponse(BaseModel):
    """queryMemory 返回值 · wire alias camelCase。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    items: list[MemoryReference]
    total_count: int = Field(..., ge=0, alias="totalCount")


@runtime_checkable
class QueryMemoryHandler(Protocol):
    """queryMemory handler Protocol；委托 L3-6。"""

    async def __call__(
        self, req: QueryMemoryRequest, ctx: ServerCallContext
    ) -> QueryMemoryResponse: ...


async def handle_query_memory(
    req: QueryMemoryRequest, ctx: ServerCallContext
) -> QueryMemoryResponse:
    """a2a.queryMemory 业务实现（effectiveConfidence 过滤 + 委托 L3-6）。"""
    if req.min_confidence is None:  # 默认 0.01（过滤 EXPIRED）
        req = req.model_copy(update={"min_confidence": 0.01})
    result = await query_memory_async(req)  # 委托 L3-6 in-process（§6.2）
    return QueryMemoryResponse(
        items=[
            MemoryReference(
                name=m.name,
                subject=m.subject,
                predicate=m.predicate,
                effective_confidence=m.effective_confidence,
            )
            for m in result.items
        ],
        total_count=result.total_count,
    )
```

**wire 同步矩阵（与 L2-4 Spec v0.2.0 §6.5 字段 1:1 对齐）**：

| Request 字段 | Python 字段 | wire alias | type | 校验 | L2-4 对齐 |
|-------------|-------------|-----------|------|------|-----------|
| `agentRef` | `agent_ref` | `agentRef` | `AgentReference` | required · ServiceAccount only | ✅ §6.5 L12 |
| `scopeRef` | `scope_ref` | `scopeRef` | `ScopeReference` | optional · frozen | ✅ §6.5 L13 |
| `filters` | `filters` | — | `dict[str, str]` | optional | ✅ §6.5 L14 |
| `minConfidence` | `min_confidence` | `minConfidence` | `float` | optional · ge=0.0, le=1.0 | ✅ §6.5 L15 |

| Response 字段 | wire alias | type | L2-4 对齐 |
|-------------|-----------|------|-----------|
| `items` | — | `list[MemoryReference]` | ✅ §6.5 L18 |
| `totalCount` | `totalCount` | `int` | ✅ §6.5 L19 |

**业务流程**：
1. 解析 `QueryMemoryRequest`（Pydantic 自动校验）
2. 若 `min_confidence` 未指定，默认设为 0.01（过滤 EXPIRED 状态 Memory）
3. 调用 `query_memory_async(req)`（L3-6 in-process function reference · 共享 Deployment 同 Pod 内调用；详见 §6.2）
4. 返回 `QueryMemoryResponse(items, total_count)`

**关联测试 ID（H-QM · 7 ID）**：
- `H-QM-UT-001` `QueryMemoryRequest` Pydantic 校验（agent_ref required · minConfidence [0,1]）
- `H-QM-UT-002` `QueryMemoryResponse` schema 校验（items + totalCount ≥ 0）
- `H-QM-UT-003` effectiveConfidence 过滤（默认 0.01 阈值 · EXPIRED 状态自动过滤）
- `H-QM-IT-001` L3-6 in-process function reference 调用契约（async def + exception propagation）
- `H-QM-IT-002` 5 维 visibility 矩阵过滤（agent-private 短路 · MemoryVisibility 3 类）
- `H-QM-CF-001` wire contract 一致性测试（与 L2-4 §6.5 schema 比对）
- `H-QM-E2E-001` 端到端 e2e（queryMemory A2A call → L3-6 in-process → K8s API list → response）

**上游引用**：
- [L2-4 Spec v0.2.0 §6.5 `a2a.queryMemory` handler 完整实现](../../spec/L2-module-specs/L2-knowledge-memory.md)
- [ADR-0003 §4.1 decay 公式](../../adr/0003-memory-design.md)（effectiveConfidence = confidence × exp(-elapsed_days / decayDays)）
- [§6.2 与 L3-6 共享 Deployment 的 in-process function reference](#62-与-l3-6-共享-deployment-的-in-process-function-reference)

---

**§4 总结**：
- **4 A2A method handler 共 32 测试 ID**（H-QK × 10 + H-GKI × 8 + H-RM × 7 + H-QM × 7）
- **wire contract 永久不变**（与 L2-4 v0.2.0 §6 字段 1:1 对齐）
- **Knowledge 2 method（L3-5 实现）+ Memory 2 method（委托 L3-6 in-process）**
- **30 行/个 Python Protocol + handler 实现**（与 L3-4 Hello Agent §3.2 `HelloAgentExecutor` 同模式）

---

## 5. Admission Webhook 双向互斥（Kopf @kopf.validation + 50ms fail-closed · wire contract 完全继承 L2-4 v0.2.0 §5）

> **本节目的**：将 [L2-4 Spec v0.2.0 §5 admission webhook 双向互斥](../../spec/L2-module-specs/L2-knowledge-memory.md) 落地为 L3-5 文件级 Python 契约。包含：(a) 完整 admission_validator.py Protocol（50 行）；(b) KnowledgeItem vs Memory 互斥校验 5 步算法；(c) scope_ref 父子循环检测 4 步算法；(d) cert-manager TLS + 50ms fail-closed；(e) 关联测试 ID（ADM / ADM-IT）。
>
> **5 项关键约束**（来自 §1.2 + ADR-0003 §5 + L2-4 Spec §5）：
> 1. **互斥规则永久不变**：同 scope_ref + 同 content 哈希的 KnowledgeItem 与 Memory 二选一
> 2. **Kopf `@kopf.validation` decorator**：4 个 hook（`knowledgeitem.create` / `knowledgeitem.update` / `memory.create` / `memory.update`）
> 3. **cert-manager TLS**：webhookconfig.yaml 复用 L3-1 §7.1.2 4 webhook 配置契约
> 4. **50ms fail-closed**：Kopf admission 超时返回 `AdmissionResponse(allowed=False, reason="admission timeout")`
> 5. **scope_ref 父子链检测**：max_depth=8 · BFS · visited set · 重复 → 拒绝（逻辑拒绝，不映射独立 wire 错误码）

### 5.1 admission_validator.py（ADM · Knowledge↔Memory 互斥 · 50 行）

**文件路径**：`services/knowledge-service/src/supteam_a2a/knowledge_service/admission_validator.py`

**完整 Python Protocol + 50 行实现**：

```python
# services/knowledge-service/src/supteam_a2a/knowledge_service/admission_validator.py
# ADM · Knowledge↔Memory 双向互斥 validator · Kopf @kopf.validation decorator + 50ms fail-closed
# wire contract 完全继承 L2-4 Spec v0.2.0 §5 + ADR-0003 §5
from __future__ import annotations
import asyncio
import hashlib
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field, ConfigDict
import kopf
from superteam_a2a.knowledge.crd.knowledgescope import (
    KnowledgeScope,
    ScopeReference,
    ScopeLevel,
)
from superteam_a2a.knowledge.crd.knowledgeitem import KnowledgeItem
from superteam_a2a.knowledge.crd.memory_schema import Memory
from superteam_a2a.a2a.upstream import A2AError
from superteam_a2a.knowledge_service.errors import (
    KNOWLEDGE_ITEM_NOT_FOUND,
    KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY,
    KNOWLEDGE_OWNER_KIND_FORBIDDEN,
    KNOWLEDGE_ADMISSION_TIMEOUT,
    MEMORY_SCOPE_NOT_FOUND,
    MEMORY_DECAY_DAYS_EXCEEDED,
    MEMORY_AGENT_NOT_FOUND,
    MEMORY_ADMISSION_TIMEOUT,
)


@runtime_checkable
class AdmissionDecision(Protocol):
    """Admission 决策契约（Kopf AdmissionResponse 子集）。"""

    allowed: bool
    reason: str | None = None


@runtime_checkable
class KnowledgeMemoryMutexValidator(Protocol):
    """KnowledgeItem ↔ Memory 互斥校验 Protocol。"""

    async def validate_ki_memory_mutex(self, ki: KnowledgeItem) -> AdmissionDecision: ...
    async def validate_scope_chain(self, scope: KnowledgeScope) -> AdmissionDecision: ...


# 50ms fail-closed 装饰器（asyncio.wait_for）
def fail_closed_50ms(coro):
    """admission 超时 50ms 返回 fail-closed（拒绝）。"""

    async def wrapper(*args, **kwargs):
        try:
            return await asyncio.wait_for(coro(*args, **kwargs), timeout=0.050)
        except asyncio.TimeoutError:
            return AdmissionDecision(allowed=False, reason="admission timeout (>50ms)")

    return wrapper


@kopf.validation("knowledgeitem.create", "knowledgeitem.update")
@fail_closed_50ms
async def validate_knowledge_item(spec, **kwargs):
    """KnowledgeItem admission webhook（互斥校验 + scope 校验）。"""
    ki = KnowledgeItem.model_validate(spec)  # Pydantic 自动校验
    mutex = KnowledgeMemoryMutexValidator()  # DI 注入
    # 1. scope_ref 父子链检测（§5.3 4 步算法）
    scope_decision = await mutex.validate_scope_chain(ki.spec.scope_ref)
    if not scope_decision.allowed:
        raise kopf.AdmissionError(scope_decision.reason or "scope circular reference")
    # 2. KnowledgeItem ↔ Memory 互斥（§5.2 5 步算法）
    mutex_decision = await mutex.validate_ki_memory_mutex(ki)
    if not mutex_decision.allowed:
        raise kopf.AdmissionError(KNOWLEDGE_ITEM_NOT_FOUND)  # -32012 (mutex 拒绝标记 KI 不可用)
    return AdmissionDecision(allowed=True)


@kopf.validation("memory.create", "memory.update")
@fail_closed_50ms
async def validate_memory(spec, **kwargs):
    """Memory admission webhook（互斥校验 + decay_days 边界）。"""
    mem = Memory.model_validate(spec)
    if mem.spec.decay_days > 3650:  # 边界校验（与 L2-4 §3.4 一致）
        raise kopf.AdmissionError("decay_days > 3650")
    return AdmissionDecision(allowed=True)
```

**wire 同步矩阵（与 L2-4 Spec v0.2.0 §5.1 / §5.2 / §5.3 字段 1:1 对齐；wire 名 + JSON-RPC code 与 §8 完全一致）**：

| admission 校验项 | wire 名 | 错误码（JSON-RPC） | L2-4 对齐 |
|----------------|---------|-------------------|-----------|
| KnowledgeItem vs Memory 互斥 | `KNOWLEDGE_ITEM_NOT_FOUND` | -32012 | ✅ §5.1 |
| scope_ref 父子循环（业务拒绝，无独立错误码） | （fail-closed via Kopf AdmissionError） | n/a（reference） | ✅ §5.3 |
| visibility=public-readable + scope.level≠industry | `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY` | -32015 | ✅ §5.1 |
| KI.ownerRef.kind=ServiceAccount | `KNOWLEDGE_OWNER_KIND_FORBIDDEN` | -32017 | ✅ §5.1 |
| admission 50ms 超时 | `KNOWLEDGE_ADMISSION_TIMEOUT` | -32018 | ✅ §5.1 |
| Memory decay_days > 3650 | `MEMORY_DECAY_DAYS_EXCEEDED` | -32110 | ✅ §5.2 |
| Memory scope 不存在 | `MEMORY_SCOPE_NOT_FOUND` | -32101 | ✅ §5.2 |
| Memory agentRef.name SA 不存在 | `MEMORY_AGENT_NOT_FOUND` | -32111 | ✅ §5.2 |
| Memory admission 50ms 超时 | `MEMORY_ADMISSION_TIMEOUT` | -32112 | ✅ §5.2 |

**cert-manager TLS + 50ms fail-closed**：
- **cert-manager 颁发**：L3-1 §7.1.2 webhookconfig.yaml 复用 4 webhook 配置契约（`knowledgeitem-create` / `knowledgeitem-update` / `memory-create` / `memory-update`）
- **TLS 续期**：2160h / 720h renewBefore（与 L3-1 §7 Helm 9 模板 + cert-manager v1.14 标准一致）
- **50ms fail-closed**：`asyncio.wait_for(coro, timeout=0.050)` + `kopf.AdmissionError("admission timeout (>50ms)")`

**关联测试 ID（ADM · 9 ID）**：
- `ADM-UT-001` KnowledgeItem vs Memory content hash 互斥（同 hash + 不同 agent 拒绝）
- `ADM-UT-002` KnowledgeItem vs Memory content hash 同 agent supersede 允许
- `ADM-UT-003` scope_ref 父子循环检测（BFS + visited set · max_depth=8）
- `ADM-UT-004` 50ms fail-closed 装饰器（超时 → `AdmissionDecision(allowed=False, reason="admission timeout")`）
- `ADM-UT-005` decay_days 边界校验（>3650 拒绝）
- `ADM-IT-001` envtest admission 实际 K8s API（apply CR → webhook 触发 → 决策验证）
- `ADM-IT-002` cert-manager TLS 颁发 + 续期（2160h / 720h renewBefore）
- `ADM-IT-003` mTLS 双向认证（webhook server cert + kube-apiserver CA bundle 验证）
- `ADM-E2E-001` 端到端 e2e（kubectl apply Memory + 互斥 KI → 拒绝 → kubectl apply Memory → 成功）

**上游引用**：
- [L2-4 Spec v0.2.0 §5 admission webhook 详细规格（双向互斥）](../../spec/L2-module-specs/L2-knowledge-memory.md)
- [ADR-0003 Memory 设计 §5 admission 互斥](../../adr/0003-memory-design.md)
- [L3-1 Operator Core v0.2.0 §7.1.2 webhookconfig.yaml 4 webhook 配置](../../spec/L3-file-specs/L3-operator-core.md)
- [Kopf 官方文档 admission](https://kopf.readthedocs.io/en/latest/admission/)

### 5.2 KnowledgeItem vs Memory 互斥校验实现（5 步算法 · wire 与 L2-4 Spec §5.1 完全一致）

**算法伪代码**（与 L2-4 Spec v0.2.0 §5.1 算法 1:1 对齐）：

```python
# 5 步算法 · 校验 KnowledgeItem 与 Memory 同 scope_ref + 同 content 哈希是否冲突
# 详细实现见 admission_validator.py:KnowledgeMemoryMutexValidator.validate_ki_memory_mutex


async def validate_ki_memory_mutex(ki: KnowledgeItem) -> AdmissionDecision:
    """5 步算法实现（与 L2-4 Spec §5.1 1:1 对齐）。"""
    # 1. 计算 content_hash（sha256 前 16 位 · 与 wire 名一致）
    content_hash = hashlib.sha256(ki.spec.content.encode("utf-8")).hexdigest()[:16]

    # 2. 查询同 content_hash 的 Memory CRD（K8s API label selector）
    k8s = get_k8s_client()
    memories = await k8s.list_namespaced_custom_object(
        group="memory.superteam-a2a.io",
        version="v1alpha1",
        namespace=ki.spec.scope_ref.namespace,
        plural="memories",
        label_selector=f"contentHash={content_hash}",
    )

    # 3. 不存在 → 允许创建（短路返回）
    if not memories["items"]:
        return AdmissionDecision(allowed=True)

    # 4. 存在 → 校验是否同 agent_ref（同 agent 允许 supersede）
    for mem_raw in memories["items"]:
        mem = Memory.model_validate(mem_raw)
        if mem.spec.subject == ki.metadata.labels.get("agent"):
            return AdmissionDecision(allowed=True, reason="same agent supersede")

    # 5. 存在 + 不同 agent → 拒绝（KNOWLEDGE_ITEM_NOT_FOUND -32012 标记 KI 不可用）
    raise kopf.AdmissionError(KNOWLEDGE_ITEM_NOT_FOUND)  # -32012
```

**5 步算法步骤详解**：

| 步骤 | 操作 | 错误码（失败时） |
|------|------|------------------|
| **1** | 计算 `content_hash = sha256(req.content).hexdigest()[:16]`（16 hex chars · 64 bit） | — |
| **2** | 查询同 `content_hash` 的 Memory CRD（K8s API `label_selector`） | — |
| **3** | 不存在 → 允许创建（短路返回 `AdmissionDecision(allowed=True)`） | — |
| **4** | 存在 → 校验是否同 `agent_ref`（同 agent 允许 supersede；自动标记旧 Memory 为 SUPERSEDED） | — |
| **5** | 存在 + 不同 agent → 拒绝 `KNOWLEDGE_ITEM_NOT_FOUND` (-32012 标记 KI 不可用) | `KNOWLEDGE_ITEM_NOT_FOUND` (-32012) |

**关联测试 ID**（继承 §5.1 ADM 测试矩阵）：
- `ADM-UT-001` content_hash 计算正确性（sha256 前 16 hex chars · 64 bit 空间）
- `ADM-UT-002` 同 agent supersede 场景（旧 Memory 自动标记 SUPERSEDED）
- `ADM-UT-003` 不同 agent 拒绝场景（`KNOWLEDGE_ITEM_NOT_FOUND` 错误码）
- `ADM-UT-004` K8s API label_selector 索引性能（10K Memory 下查询 P95 ≤ 50ms）

### 5.3 scope_ref 父子循环检测（4 步算法 · wire 与 L2-4 Spec §5.3 完全一致）

**算法伪代码**（与 L2-4 Spec v0.2.0 §5.3 算法 1:1 对齐）：

```python
# 4 步算法 · 校验 scope_ref.parent_ref 链是否存在循环引用
# 详细实现见 admission_validator.py:KnowledgeMemoryMutexValidator.validate_scope_chain


async def validate_scope_chain(scope_ref: ScopeReference) -> AdmissionDecision:
    """4 步算法实现（与 L2-4 Spec §5.3 1:1 对齐）。"""
    k8s = get_k8s_client()
    visited: set[str] = set()  # 步骤 2: visited set
    current_ref = scope_ref
    depth = 0

    # 1. 解析 scope_ref.parent_ref 链（BFS）
    while current_ref is not None and depth < 8:  # 步骤 3: max_depth = 8
        # 2. 沿链向上追溯至 system scope
        if current_ref.name in visited:
            # 3. 校验链中无重复 scope_level（出现重复 → 循环）
            raise kopf.AdmissionError(
                "scope circular reference"
            )  # -32009 (逻辑拒绝，无独立 wire 错误码)
        visited.add(current_ref.name)
        current_scope = await k8s.get_namespaced_custom_object(
            group="knowledge.superteam-a2a.io",
            version="v1alpha1",
            namespace=current_ref.namespace,
            plural="knowledgescopes",
            name=current_ref.name,
        )
        ks = KnowledgeScope.model_validate(current_scope)
        # 4. 沿 parent_ref 向上追溯
        current_ref = ks.spec.parent_ref
        depth += 1

    if depth >= 8:
        # max_depth 超过 → 拒绝（避免无限循环）
        raise kopf.AdmissionError("max_depth=8 exceeded")

    return AdmissionDecision(allowed=True)
```

**4 步算法步骤详解**：

| 步骤 | 操作 | 错误码（失败时） |
|------|------|------------------|
| **1** | 解析 `scope_ref.parent_ref` 链（BFS · 避免递归栈溢出） | — |
| **2** | 沿链向上追溯至 `system` scope（system 是 root · parent_ref 必须为 None） | — |
| **3** | 校验链中无重复 `scope_level`（visited set 检测循环；max_depth=8） | — |
| **4** | 重复 → 拒绝（scope circular reference · 逻辑拒绝不映射独立 wire 错误码） | n/a（reference） |

**关联测试 ID**（继承 §5.1 ADM 测试矩阵）：
- `ADM-UT-005` 4 级 scope 链合法场景（agent → agentset → workflow → system）
- `ADM-UT-006` 父子循环场景（agent → workflow → agent）
- `ADM-UT-007` max_depth=8 边界（9 级链拒绝）
- `ADM-UT-008` BFS vs DFS 性能对比（BFS P95 ≤ 50ms · 8 级 8 个 K8s API call）

---

**§5 总结**：
- **Admission webhook 双向互斥 = 5 步算法 + 4 步算法**（与 L2-4 Spec v0.2.0 §5.1 / §5.3 字段 1:1 对齐）
- **cert-manager TLS + 50ms fail-closed**（与 L3-1 §7.1.2 webhookconfig.yaml 一致）
- **9 + 8 = 17 测试 ID**（ADM × 9 · 含 envtest 实际 K8s API + cert-manager TLS 续期）

---

## 6. MemoryReconciler 协调点（仅协调点 · 详细落地见 L3-6 Memory backend Spec · #64 起草）

> **本节目的**：明确 L3-5 与 L3-6 共享 Deployment 的边界 —— **L3-5 仅暴露 4 A2A method + admission webhook + scope/visibility/BM25 算法，不实现 MemoryReconciler 60s 周期 reconcile**。L3-6 详细落地 60s `kopf.timer` + Leader Election + decay/reinforce/GC/promotion 数学（见 [L3-6 Memory backend v0.2-draft §6](./L3-memory-backend.md) · 待 #64 起草）。本节定义：
>
> 1. **协调点**（§6.1）：L3-5 仅 `@kopf.validation` admission decorator；不实现 `kopf.timer(interval=60.0)`
> 2. **共享 Deployment 边界**（§6.2）：同 Pod 内两个独立 Python 进程 + in-process function reference 协议
> 3. **in-process function reference 契约**：async def + exception propagation + 不走 HTTP
>
> **3 项关键约束**：
> 1. **L3-5 不实现 MemoryReconciler 60s 周期**（L3-6 独占 `kopf.timer(interval=60.0)`）
> 2. **L3-5 不实现 decay/reinforce/GC/promotion 数学**（L3-6 独占 `Clock` Protocol + `RealClock` + `FakeClock`）
> 3. **L3-5 不实现 BM25 rebuild 启动期全量重建**（L3-6 独占 + 共享 in-memory 倒排索引）

### 6.1 协调点（不重复实现 MemoryReconciler · 仅 admission decorator）

**L3-5 与 L3-6 边界**：

| 职责 | L3-5（Knowledge Service） | L3-6（Memory backend） | 协调点 |
|------|---------------------------|------------------------|--------|
| **4 A2A method 暴露** | ✅（§4） | ❌ | L3-5 ASGI server 暴露；L3-6 in-process function reference |
| **admission webhook 双向互斥** | ✅（§5） | ❌ | L3-5 独占 `@kopf.validation` decorator |
| **4 级 scope 解析 + 5 维 visibility 矩阵** | ✅（§3.1 + §4.1） | ❌ | L3-5 独占 `ScopeResolver` + `VisibilityResolver` |
| **BM25 倒排索引（查询）** | ✅（§4.1 queryKnowledge） | ❌ | L3-5 独占 `bm25_index.search` + `anyio.to_thread.run_sync` |
| **BM25 倒排索引（重建）** | ❌ | ✅（启动期全量 + watch 增量） | L3-6 独占 + 共享内存 dict |
| **MemoryReconciler 60s 周期** | ❌ | ✅（`@kopf.timer(interval=60.0)`） | L3-6 独占 |
| **decay/reinforce/GC/promotion 数学** | ❌ | ✅（`Clock` Protocol + `RealClock` + `FakeClock`） | L3-6 独占 |
| **Leader Election Lease** | ❌ | ✅（`coordination.k8s.io/v1` Lease） | L3-6 独占 |
| **recordMemory / queryMemory 业务** | 委托 L3-6（in-process call） | ✅（K8s API apply/list + decay 计算） | L3-6 export `record_memory_async` / `query_memory_async` |
| **promotion to KnowledgeItem** | ❌ | ✅（v0.1 仅算不触发） | L3-6 独占 |

**L3-5 admission webhook 范围**（仅 `@kopf.validation`，**不实现 `@kopf.timer`**）：

```python
# L3-5 仅 @kopf.validation · L3-6 独占 @kopf.timer
import kopf


@kopf.validation("knowledgeitem.create", "knowledgeitem.update")  # L3-5 独占
async def validate_knowledge_item(spec, **kwargs): ...


@kopf.validation("memory.create", "memory.update")  # L3-5 独占（双向互斥右侧）
async def validate_memory(spec, **kwargs): ...


# L3-6 独占（不在 L3-5 实现）：
# @kopf.timer(interval=60.0, id="memory-reconciler")
# async def reconcile_memory(memories, **kwargs): ...
```

**L3-5 不实现的 5 项 MemoryReconciler 职责**（边界清晰化）：
1. ❌ `apply_decay(mem, now)` → `effective_confidence`（L2-4 §7.3 纯函数）
2. ❌ `apply_reinforce(mem, ts)` → `reinforced_count + last_reinforced_at`（L2-4 §7.3 纯函数）
3. ❌ `gc_expired(memories, now)` → 待清理列表（L2-4 §7.3 纯函数）
4. ❌ `is_eligible_for_promotion(mem, now)` → bool（L2-4 §7.3 纯函数）
5. ❌ Leader Election Lease 状态机（Standby ↔ Leader · 30s grace period · renew 失败 3 次让位）

**L3-5 Leader Election 协调**：L3-5 **不参与** Leader Election（无 `@kopf.timer` 装饰器）；L3-6 独占 Leader Election Lease，L3-5 与 L3-6 共享 Deployment 同 Pod 内协作。

### 6.2 与 L3-6 单进程架构（同 ADR-0006 D 方案 · v0.2.1 · 2026-07-30 #71）

**架构决策**（[ADR-0006 v1.0 Accepted · D 方案](../../adr/0006-memory-transport.md)）：取消 L3-5 + L3-6 双进程架构，**合并为单 Python 进程**（L3-5 + L3-6 同一 Python runtime），消除 IPC 边界 + 50ms admission deadline 零风险 + Card-driven 单实例天然适合。

**单进程架构**（同 Pod 内一个 Python 进程 · 合并 services/knowledge-service + services/memory-backend → services/knowledge-memory-service）：

```
Knowledge-Memory Service Pod (replicaCount: 1)
└── Container 1: knowledge-memory-service (port 8080 · gRPC/HTTP)
    ├── ASGI server (L3-2 §5 复用 · Uvicorn 单 worker)
    ├── 4 A2A method handler (L3-5 §4)
    │   ├── queryKnowledge (L3-5 实现 · BM25 倒排索引)
    │   ├── getKnowledgeItem (L3-5 实现 · K8s API 拉取)
    │   ├── recordMemory (L3-5 admission + L3-6 委托 · 同进程直接调用)
    │   └── queryMemory (L3-5 admission + L3-6 委托 · 同进程直接调用)
    ├── admission webhook (L3-5 §5 · Kopf @kopf.validation · 50ms fail-closed)
    ├── MemoryReconciler 60s @kopf.timer (L3-6 §6.1 详细落地 · decay / reinforce / GC / promotion)
    ├── Leader Election Lease (L3-6 §7.6 · 30s grace + 3x renew fail)
    ├── Clock Protocol + RealClock + FakeClock (L3-6 §5.1)
    ├── BM25 启动期全量重建 + watch 增量 (L3-6 §4.2)
    └── import memory_backend.record_memory_async / query_memory_async
        (in-process function reference · 同进程直接 import + 调用)
```

**进程内调用机制**（**单进程 · 无 IPC 边界 · 无序列化**）：

- **调用方式**：同进程内 `from superteam_a2a.memory_backend.svc import record_memory_async, query_memory_async` + `result = await record_memory_async(mem, context=context)`
- **优势**：<1μs 直接函数调用（vs UDS ~10μs · vs HTTP ~2ms p99）+ 强类型（Protocol 约束）+ 25 指标同进程聚合
- **限制**：未来扩展 sidecar / DaemonSet 需重新设计（但 v0.1 单实例已锁定，OPEN-MEMORY-002 推迟到 v0.5+）

**调用契约 3 项规则**（防止破坏 L3-5 ↔ L3-6 边界）：
1. **`async def` 全异步**：所有 L3-6 export 函数均为 `async def`；L3-5 调用必须 `await`
2. **异常透传**：L3-6 抛出的 `A2AError` / `AdmissionTimeoutError` 等异常直接传播到 L3-5；L3-5 **不 catch 并改 error code**（避免双重映射）
3. **单调时钟**：deadline/timeout/idempotency window 使用同一 `Clock.monotonic()`（L3-6 §5.1 暴露到 InProcessContext.clock）；**禁止 `asyncio.get_event_loop().time()` 或本地 `time.monotonic()` 独立计算**

**Clock 边界**（与 L3-6 §6.1 一致）：L3-6 在 `record_memory_async` / `query_memory_async` handler 入口将 `Clock.monotonic()` 通过 `InProcessContext` 暴露给 L3-5 调用方（用于 deadline/timeout/idempotency window 一致性）；L3-5 必须读取 `context.clock.monotonic()`，不得使用 `asyncio.get_event_loop().time()` 或本地 `time.monotonic()` 独立计算 deadline。

**单 container Deployment 的 Helm 部署形态**（与 §9 deployment.yaml 一致）：
- **单 Deployment**：`Deployment` 名称 `knowledge-memory-service` 包含一个 Container（同 Pod）
- **单 Service**：port 8080（HTTP/mTLS）对外暴露
- **单 ServiceMonitor**：port 8080 scrape 15+5+5=25 指标（L3-5 5 + L3-6 10 + shared 10）
- **单 RBAC**：ClusterRole 同时包含 `knowledgescopes` + `knowledgeitems` + `memories` 3 类 CRD read/write + admissionregistration/authn/authz 扩展
- **单 NetworkPolicy**：ingress 仅允许 operator namespace + cert-manager；egress K8s API + Prometheus + cert-manager
- **单 cert-manager**：mTLS TLSConfig + HotReloader（与 L3-1 §7.1.2 同模式）

**关联测试 ID（L3-5 ↔ L3-6 边界 · 8 ID · D 方案调整）**：
- `MTLS-IT-001` ~~共享 Deployment 双 Container 启动顺序~~ → 已废弃（D 方案单进程）
- `MTLS-IT-002` in-process function reference 调用契约（async def + exception propagation）· 同进程直接 import
- `MTLS-IT-003` 共享 ServiceMonitor scrape（port 8080 · interval 30s · 25 指标）
- `MTLS-IT-004` 共享 RBAC ClusterRole（knowledgescopes + knowledgeitems + memories + admissionregistration/authn/authz）
- `MTLS-IT-005` 共享 NetworkPolicy ingress/egress（operator namespace + cert-manager）
- `E2E-WIRE-IT-001` wire contract 端到端（CRD apply → L3-6 同进程 → L3-5 A2A response · wire 一致性）
- `E2E-WIRE-IT-002` recordMemory 委托链（recordMemory A2A call → L3-5 admission → L3-6 record_memory_async 同进程 → K8s API apply → effective_confidence 计算 → response）
- `E2E-WIRE-IT-003` queryMemory 委托链（queryMemory A2A call → L3-5 min_confidence 默认 0.01 → L3-6 query_memory_async 同进程 → 5 维 visibility 过滤 → effective_confidence 阈值过滤 → response）

**上游引用**：
- [L2-4 Spec v0.2.0 §7 MemoryReconciler reconcile 流程](../../spec/L2-module-specs/L2-knowledge-memory.md)（详细算法）
- [L2-4 Design v0.2.0 §3 D-3 MemoryReconciler timer 决策 + D-4 Clock Protocol 决策](../../design/L2-modules/L2-knowledge-memory.md)
- [L3-6 Memory backend v0.2.1 §6 MemoryReconciler 60s kopf.timer 详细落地](./L3-memory-backend.md)
- [L3-1 Operator Core v0.2.0 §3.4 MemoryReconciler 协调](../../spec/L3-file-specs/L3-operator-core.md)
- [ADR-0005 §6.2 单进程原则 + §13.1 uv workspace 双仓库](../../adr/0005-python-first-technology-stack.md)
- **[ADR-0006 v1.0 Accepted · D 方案（合并 L3-5 + L3-6 单进程）](../../adr/0006-memory-transport.md) · 2026-07-30 #71**

---

**§6 总结**：
- **L3-5 仅暴露 4 A2A method + admission webhook + scope/visibility/BM25 算法**；**不实现** MemoryReconciler 60s 周期
- **共享 Deployment 边界清晰**：同 Pod 内两个独立 Python 进程 · in-process call（不走 HTTP）
- **8 测试 ID**（MTLS-IT × 5 + E2E-WIRE-IT × 3）验证 L3-5 ↔ L3-6 边界一致性

---

## 7. Observability（20 指标 + structlog + K8s Events）

> 实现位置：`services/knowledge-service/src/superteam_a2a/knowledge_service/observability/`；遵循 [ADR-0005 §10](../../adr/0005-python-first-technology-stack.md) 与 [Constitution §7](../../../CONSTITUTION.md)。

### 7.1 指标（11 A2A + 4 Python runtime + 5 Knowledge = 20 指标）

| # | name | type | labels | help text | buckets |
|---|---|---|---|---|---|
| 1 | `superteam_a2a_rpc_total` | Counter | `agent,method,status` | Total A2A RPC requests. | — |
| 2 | `superteam_a2a_rpc_duration_seconds` | Histogram | `agent,method` | A2A RPC latency. | `.005,.01,.025,.05,.1,.25,.5,1,2.5,5,10` |
| 3 | `superteam_a2a_active_streams` | Gauge | — | Current active A2A streams. | — |
| 4 | `superteam_a2a_circuit_breaker_state` | Gauge | `target,state` | Circuit-breaker state. | — |
| 5 | `superteam_a2a_retry_total` | Counter | `method,attempt` | Total retry attempts. | — |
| 6 | `superteam_a2a_discovery_watch_reconnects_total` | Counter | `namespace` | Discovery watch reconnects. | — |
| 7 | `superteam_a2a_agent_card_cache_hits_total` | Counter | `cache` | Agent Card cache hits. | — |
| 8 | `superteam_a2a_cert_reload_failures_total` | Counter | — | Certificate reload failures. | — |
| 9 | `superteam_a2a_extension_router_dispatch_total` | Counter | `method,status` | Extension dispatches. | — |
| 10 | `superteam_a2a_request_body_bytes` | Histogram | `method` | Request body bytes. | `128,512,1024,4096,16384,65536,262144,1048576` |
| 11 | `superteam_a2a_response_body_bytes` | Histogram | `method` | Response body bytes. | `128,512,1024,4096,16384,65536,262144,1048576` |
| 12 | `python_gc_duration_seconds` | Histogram | `generation` | Python GC duration. | `.0001,.0005,.001,.005,.01,.05,.1,.5,1` |
| 13 | `python_info` | Gauge | `version,implementation` | Python runtime information. | — |
| 14 | `process_cpu_seconds_total` | Counter | — | Process CPU time. | — |
| 15 | `process_resident_memory_bytes` | Gauge | — | Resident memory bytes. | — |
| 16 | `superteam_knowledge_query_total` | Counter | `scope_level,visibility` | Total Knowledge queries. | — |
| 17 | `superteam_knowledge_query_latency_seconds` | Histogram | `scope_level` | Knowledge query latency. | `.005,.01,.025,.05,.1,.25,.5,1,2.5,5` |
| 18 | `superteam_knowledge_bm25_index_size` | Gauge | `scope_level` | Indexed KnowledgeItem count. | — |
| 19 | `superteam_knowledge_memory_conflict_total` | Counter | `conflict_type` | Knowledge/Memory conflicts. | — |
| 20 | `superteam_knowledge_admission_duration_seconds` | Histogram | `validator` | Admission duration. | `.001,.0025,.005,.01,.025,.05,.1,.25,.5` |

11 个 A2A name/labels 继承 [L3-2 §9.1](./L3-a2a-core.md)。`scope_level`、`visibility`、`conflict_type` 仅接受受控枚举，禁止 CR 名称进入 label。`OBS-UT-001~020` 逐项验证 name/type/labels/help/buckets。

### 7.2 structlog 8 必含字段（与 L3-2 §9.3 完全一致）

```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class KnowledgeLogEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    timestamp: datetime
    level: Literal["debug", "info", "warning", "error", "critical"]
    service: Literal["knowledge-service"] = "knowledge-service"
    trace_id: str = Field(min_length=16, max_length=64)
    span_id: str = Field(min_length=8, max_length=32)
    request_id: str = Field(min_length=1, max_length=128)
    agent_id: str = Field(min_length=1, max_length=253)
    event: str = Field(min_length=1, max_length=128)
```

固定字段为 `timestamp/level/service/trace_id/span_id/request_id/agent_id/event`。`api_key/token/password/secret/memory_content/knowledge_body/tls_key/private_key` 必须递归脱敏；异常 message 上限 1024 字符。

### 7.3 K8s Events（8 类 EventReason）

```python
from enum import StrEnum
from kubernetes_asyncio.client import CoreV1Api


class EventReason(StrEnum):
    KNOWLEDGE_ITEM_CREATED = "KnowledgeItemCreated"
    KNOWLEDGE_ITEM_UPDATED = "KnowledgeItemUpdated"
    KNOWLEDGE_ITEM_DELETED = "KnowledgeItemDeleted"
    KNOWLEDGE_SCOPE_ARCHIVED = "KnowledgeScopeArchived"
    MEMORY_CONFLICT_DETECTED = "MemoryConflictDetected"
    MEMORY_CONFLICT_RESOLVED = "MemoryConflictResolved"
    ADMISSION_REJECTED = "AdmissionRejected"
    SCOPE_CIRCULAR_REFERENCE_DETECTED = "ScopeCircularReferenceDetected"


async def emit_event(
    core: CoreV1Api,
    namespace: str,
    involved_object: dict[str, object],
    reason: EventReason,
    message: str,
    *,
    type_: str = "Normal",
) -> None:
    if type_ not in {"Normal", "Warning"}:
        raise ValueError("type_ must be Normal or Warning")
    body = {
        "involvedObject": involved_object,
        "reason": reason.value,
        "type": type_,
        "message": message[:1024],
    }
    await core.create_namespaced_event(namespace=namespace, body=body)
```

| reason | type | message 模板 |
|---|---|---|
| KnowledgeItemCreated | Normal | `KnowledgeItem {namespace}/{name} created in scope {scope}` |
| KnowledgeItemUpdated | Normal | `KnowledgeItem {namespace}/{name} updated to version {version}` |
| KnowledgeItemDeleted | Normal | `KnowledgeItem {namespace}/{name} deleted` |
| KnowledgeScopeArchived | Normal | `KnowledgeScope {namespace}/{name} archived` |
| MemoryConflictDetected | Warning | `Memory conflict {conflict_type} detected for {namespace}/{name}` |
| MemoryConflictResolved | Normal | `Memory conflict resolved for {namespace}/{name}` |
| AdmissionRejected | Warning | `Admission rejected for {kind}/{namespace}/{name}: {reason}` |
| ScopeCircularReferenceDetected | Warning | `Circular scope reference detected at {namespace}/{name}` |

继承 L3-1 §7.1.5 的白名单、Normal/Warning、1024 字符截断和 trace annotation 约束；禁止运行时拼接 reason。

---

## 8. 错误码（23 个 JSON-RPC enum）

> name/code 作为 L3-5/L3-6 wire 契约锁定；4 A2A method envelope 完全继承 [L2-4 Spec v0.2.0 §9](../L2-module-specs/L2-knowledge-memory.md)。

### 8.1 11 个 KNOWLEDGE_* 错误码（-32008 ~ -32018）

| name | code | HTTP status | message template | Retryable |
|---|---:|---:|---|---|
| `KNOWLEDGE_SCOPE_NOT_FOUND` | -32008 | 404 | `Knowledge scope {scope_ref_name} was not found` | No |
| `KNOWLEDGE_QUERY_TOO_LONG` | -32009 | 400 | `Knowledge query length {actual} exceeds 512` | No |
| `KNOWLEDGE_INVALID_TYPE` | -32010 | 400 | `Knowledge typeFilter {type} is not a valid enum value` | No |
| `KNOWLEDGE_INTERNAL_ERROR` | -32011 | 500 | `Knowledge service internal error` | Yes |
| `KNOWLEDGE_ITEM_NOT_FOUND` | -32012 | 404 | `Knowledge item {name} was not found` | No |
| `KNOWLEDGE_VERSION_NOT_FOUND` | -32013 | 404 | `Knowledge item {name} version {version} was not found` | No |
| `KNOWLEDGE_FORBIDDEN` | -32014 | 403 | `Knowledge {name} is not accessible to agent {agent_id}` | No |
| `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY` | -32015 | 400 | `Knowledge {name} visibility=public-readable requires scope.level=industry` | No |
| `KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS` | -32016 | 400 | `Knowledge {name} visibility=agent-private is only supported in v0.5+` | No |
| `KNOWLEDGE_OWNER_KIND_FORBIDDEN` | -32017 | 400 | `Knowledge {name} ownerRef.kind={kind} is forbidden (use Memory)` | No |
| `KNOWLEDGE_ADMISSION_TIMEOUT` | -32018 | 503 | `Knowledge admission exceeded 50ms` | Yes |

```python
from enum import IntEnum


class KnowledgeErrorCode(IntEnum):
    """Knowledge Service 错误码（JSON-RPC code 范围 -32008 ~ -32018）。"""

    KNOWLEDGE_SCOPE_NOT_FOUND = -32008
    KNOWLEDGE_QUERY_TOO_LONG = -32009
    KNOWLEDGE_INVALID_TYPE = -32010
    KNOWLEDGE_INTERNAL_ERROR = -32011
    KNOWLEDGE_ITEM_NOT_FOUND = -32012
    KNOWLEDGE_VERSION_NOT_FOUND = -32013
    KNOWLEDGE_FORBIDDEN = -32014
    KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY = -32015
    KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS = -32016
    KNOWLEDGE_OWNER_KIND_FORBIDDEN = -32017
    KNOWLEDGE_ADMISSION_TIMEOUT = -32018
```

### 8.2 12 个 MEMORY_* 错误码（-32101 ~ -32112）

| name | code | HTTP status | message template | Retryable |
|---|---:|---:|---|---|
| `MEMORY_SCOPE_NOT_FOUND` | -32101 | 404 | `Memory scope {scope_ref_name} was not found` | No |
| `MEMORY_INVALID_CONTENT` | -32102 | 400 | `Memory content exceeds 20 keys (got {actual})` | No |
| `MEMORY_FORBIDDEN` | -32103 | 403 | `Memory write denied: {reason}` | No |
| `MEMORY_RATE_LIMIT` | -32104 | 429 | `Memory write rate exceeded 60/min for SA {service_account}` | Yes |
| `MEMORY_INTERNAL_ERROR` | -32105 | 500 | `Memory backend internal error` | Yes |
| `MEMORY_QUERY_TOO_BROAD` | -32106 | 400 | `Memory query with scope=industry requires tag/confidence filter` | No |
| `MEMORY_SOURCE_KI_NOT_FOUND` | -32107 | 400 | `Memory sourceKnowledgeRef.name {name} was not found` | No |
| `MEMORY_SOURCE_KI_SCOPE_MISMATCH` | -32108 | 400 | `Memory source KI scopeRef {ki_scope} != Memory scopeRef {mem_scope}` | No |
| `MEMORY_AGENT_PRIVATE_REQUIRES_NAME` | -32109 | 400 | `Memory agent-private requires agentRef.name (got "")` | No |
| `MEMORY_DECAY_DAYS_EXCEEDED` | -32110 | 400 | `Memory decayDays {decay_days} exceeds 3650` | No |
| `MEMORY_AGENT_NOT_FOUND` | -32111 | 400 | `Memory agentRef.name {agent} (SA) was not found` | No |
| `MEMORY_ADMISSION_TIMEOUT` | -32112 | 503 | `Memory admission exceeded 50ms` | Yes |

```python
from enum import IntEnum


class MemoryErrorCode(IntEnum):
    """Memory backend 错误码（JSON-RPC code 范围 -32101 ~ -32112）。"""

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
```

### 8.3 Retryable 矩阵（23 行 × Retryable / Backoff / CircuitBreaker）

| error | Retryable | Backoff | CircuitBreaker |
|---|---|---|---|
| KNOWLEDGE_SCOPE_NOT_FOUND | No | none | No |
| KNOWLEDGE_QUERY_TOO_LONG | No | none | No |
| KNOWLEDGE_INVALID_TYPE | No | none | No |
| KNOWLEDGE_INTERNAL_ERROR | Yes | immediate once | Yes, service target |
| KNOWLEDGE_ITEM_NOT_FOUND | No | none | No |
| KNOWLEDGE_VERSION_NOT_FOUND | No | none | No |
| KNOWLEDGE_FORBIDDEN | No | none | No |
| KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY | No | none | No |
| KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS | No | none | No |
| KNOWLEDGE_OWNER_KIND_FORBIDDEN | No | none | No |
| KNOWLEDGE_ADMISSION_TIMEOUT | Yes | 100/200/400ms | No; fail-closed |
| MEMORY_SCOPE_NOT_FOUND | No | none | No |
| MEMORY_INVALID_CONTENT | No | none | No |
| MEMORY_FORBIDDEN | No | none | No |
| MEMORY_RATE_LIMIT | Yes | 1s boundary | No; honor Retry-After |
| MEMORY_INTERNAL_ERROR | Yes | immediate once | Yes, service target |
| MEMORY_QUERY_TOO_BROAD | No | none | No |
| MEMORY_SOURCE_KI_NOT_FOUND | No | none | No |
| MEMORY_SOURCE_KI_SCOPE_MISMATCH | No | none | No |
| MEMORY_AGENT_PRIVATE_REQUIRES_NAME | No | none | No |
| MEMORY_DECAY_DAYS_EXCEEDED | No | none | No |
| MEMORY_AGENT_NOT_FOUND | No | none | No |
| MEMORY_ADMISSION_TIMEOUT | Yes | 100/200/400ms | No; fail-closed |

Tenacity 仅对 Retryable=Yes 生效；validation/authorization/conflict 永不重试。Circuit Breaker 连续 5 次失败打开 30s，half-open 放行 1 个探测请求。`ERR-UT-001~023` 按行断言 enum/code/HTTP/message/retry 元数据。

---

## 9. Helm Values 7 模板完整契约

### 9.1 `_helpers.tpl` 与 values 根契约

```yaml
replicaCount: 1
image: {repository: superteam-a2a/knowledge-service, tag: v0.2.0}
memoryBackendImage: {repository: superteam-a2a/memory-backend, tag: v0.2.0}
service: {httpPort: 80, httpsPort: 443, targetHttpPort: 8080, targetHttpsPort: 8443}
serviceAccount: {create: true, name: knowledge-service}
tls: {enabled: true, secretName: knowledge-service-tls, clientCASecretName: superteam-client-ca}
metrics: {path: /metrics, interval: 30s}
resources: {requests: {cpu: 200m, memory: 512Mi}, limits: {cpu: 1500m, memory: 2Gi}}
```

`_helpers.tpl` 必须定义 `knowledge-service.name/fullname/labels/selectorLabels`，统一 app.kubernetes.io 标签。values.schema.json 强制：`replicaCount const=1`、两个 image tag 非空且非 latest、端口 1..65535、production `tls.enabled=true`、resources requests/limits 必填且 request≤limit。ConfigMap 仅保存 scope-cache/BM25/OTLP/log 非敏感配置；TLS/client CA 使用两个 Secret。

### 9.2 `deployment.yaml`（单实例 + 双探针 + SecurityContext）

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
        securityContext: {runAsUser: 65532, allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, capabilities: {drop: [ALL]}}
        volumeMounts: [{name: tls, mountPath: /var/run/secrets/tls, readOnly: true}]
      - name: memory-backend
        image: superteam-a2a/memory-backend:v0.2.0
        ports: [{name: memory, containerPort: 8081}]
        securityContext: {runAsUser: 65532, allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, capabilities: {drop: [ALL]}}
      volumes: [{name: tls, secret: {secretName: knowledge-service-tls}}]
```

验证 `replicas==1`、两个独立 Python 业务进程位于两个 container、双探针存在、restricted SecurityContext 不可弱化、Secret 只读挂载。

### 9.3 `service.yaml`（80/443 双端口 + mTLS）

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

443 强制 TLS 1.3、client cert 与 SPIFFE URI SAN；80 仅 health/readiness/metrics，匿名明文 A2A 拒绝。引用 `knowledge-service-tls` 与 `superteam-client-ca` Secret。

### 9.4 `serviceaccount.yaml`

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: knowledge-service
  annotations: {cert-manager.io/inject-ca-from: superteam-a2a/knowledge-service-serving}
automountServiceAccountToken: true
```

不得使用 default SA；L3-5/L3-6 共享专用账号。名称须 DNS-1123；关闭 create 时必须提供等权专用 SA。

### 9.5 `rbac/role.yaml` + `rolebinding.yaml`（CRD read only，7 apiGroups）

```yaml
rules:
- {apiGroups: [superteam-a2a.io], resources: [knowledgescopes, knowledgeitems, memories], verbs: [get, list, watch]}
- {apiGroups: [""], resources: [configmaps, events], verbs: [get, list, watch, create, patch]}
- {apiGroups: [""], resources: [secrets], resourceNames: [knowledge-service-tls, superteam-client-ca], verbs: [get, watch]}
- {apiGroups: [coordination.k8s.io], resources: [leases], verbs: [get, list, watch]}
- {apiGroups: [admissionregistration.k8s.io], resources: [validatingwebhookconfigurations], verbs: [get, list, watch]}
- {apiGroups: [authentication.k8s.io], resources: [tokenreviews], verbs: [create]}
- {apiGroups: [authorization.k8s.io], resources: [subjectaccessreviews], verbs: [create]}
```

RoleBinding 将 Role 绑定到 `knowledge-service` SA。CRD 仅 get/list/watch；Secret 限 resourceNames。L3-6 写权限由独立最小化 Role 增补，不扩张本 Role。

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
  - {to: [{namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: default}}}], ports: [{port: 443}]}
  - {to: [{namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: observability}}}], ports: [{port: 4317}]}
```

默认 deny；仅 A2A/Operator、Prometheus、K8s API、OTLP 显式允许。同 Pod L3-5↔L3-6 不经过 NetworkPolicy。

### 9.7 `prometheusrule.yaml`（6 告警规则）

| alert | 完整 PromQL | for |
|---|---|---|
| KnowledgeQueryLatencyP99 | `histogram_quantile(0.99,sum by(le)(rate(superteam_knowledge_query_latency_seconds_bucket[5m]))) > 0.1` | 10m |
| KnowledgeBM25IndexStale | `increase(superteam_knowledge_query_total[10m]) > 0 and max(superteam_knowledge_bm25_index_size) == 0` | 5m |
| KnowledgeMemoryConflictRate | `sum(rate(superteam_knowledge_memory_conflict_total[5m])) > 0.1` | 10m |
| KnowledgeAdmissionFailureRate | `histogram_quantile(0.99,sum by(le)(rate(superteam_knowledge_admission_duration_seconds_bucket[5m]))) > 0.05` | 5m |
| KnowledgeServiceDown | `up{job="knowledge-service"} == 0` | 2m |
| KnowledgeMemoryReconcileErrorRate | `sum(rate(superteam_knowledge_memory_conflict_total{conflict_type="reconcile"}[5m])) > 0.05` | 10m |

模板逐行生成 alert/expr/for/labels.severity/annotations.summary；全部通过 `promtool check rules`。

### 9.8 `servicemonitor.yaml`（15 + 5 指标 scrape）

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata: {name: knowledge-service}
spec:
  selector: {matchLabels: {app.kubernetes.io/name: knowledge-service}}
  endpoints: [{port: http, path: /metrics, interval: 30s, scrapeTimeout: 10s}]
```

metricRelabel keep regex 为 `superteam_a2a_.*|python_.*|process_.*|superteam_knowledge_.*`；必须 scrape §7.1 20 指标，禁止 scrape 8081，interval≥scrapeTimeout。

### 9.9 与 L3-6 memory-backend 共享 Helm chart

7 个逻辑模板组：helpers/values、Deployment、Service、ServiceAccount、RBAC、NetworkPolicy、PrometheusRule+ServiceMonitor，对应 `HELM-DEPLOY-001~007`。Deployment 固定 `replicaCount: 1`，包含 `knowledge-service` 与 `memory-backend` 两个业务 container，共享 SA/TLS/ConfigMap，以 async in-process/localhost 协议协调，但不得 import 对方私有模块。

---

## 10. 测试策略 + 验收清单

### 10.1 60 测试 ID 矩阵

> 按 60 个测试能力组计数；每组可含参数化 case。§7 `OBS-UT-001~020`、§8 `ERR-UT-001~023`、`TZ-DECAY/PROMOTE/GC-001~003`、`PERF-BM25/MEM-001~002` 是组内明细，不重复增加 60 基线。

| # | ID | 层级 | 目标 | 文件路径 |
|---:|---|---|---|---|
| 1 | `KS-CRD-UT` | UT | KnowledgeScope schema | `tests/unit/models/test_knowledge_scope.py` |
| 2 | `KI-CRD-UT` | UT | KnowledgeItem schema | `tests/unit/models/test_knowledge_item.py` |
| 3 | `MEM-CRD-UT` | UT | Memory schema | `tests/unit/models/test_memory.py` |
| 4 | `SCOPE-UT` | UT | 4-level scope | `tests/unit/services/test_scope_resolver.py` |
| 5 | `VIS-UT` | UT | 5D visibility | `tests/unit/services/test_visibility_resolver.py` |
| 6 | `BM25-UT` | UT | BM25 build/search | `tests/unit/services/test_bm25_index.py` |
| 7 | `H-QK-UT` | UT | queryKnowledge | `tests/unit/handlers/test_query_knowledge.py` |
| 8 | `H-GKI-UT` | UT | getKnowledgeItem | `tests/unit/handlers/test_get_knowledge_item.py` |
| 9 | `H-RM-UT` | UT | recordMemory | `tests/unit/handlers/test_record_memory.py` |
| 10 | `H-QM-UT` | UT | queryMemory | `tests/unit/handlers/test_query_memory.py` |
| 11 | `ERR-UT` | UT | 23 errors | `tests/unit/handlers/test_errors.py` |
| 12 | `KS-CRD-IT` | IT | Scope CRUD/watch | `tests/integration/test_knowledge_scope_crd.py` |
| 13 | `KI-CRD-IT` | IT | Item CRUD/watch | `tests/integration/test_knowledge_item_crd.py` |
| 14 | `MEM-CRD-IT` | IT | Memory wire | `tests/integration/test_memory_crd.py` |
| 15 | `ADM-IT` | IT | admission | `tests/integration/test_admission.py` |
| 16 | `ENVTEST-IT` | IT | kind API | `tests/integration/test_kind_environment.py` |
| 17 | `TLS-IT` | IT | TLS reload | `tests/integration/test_tls.py` |
| 18 | `MTLS-IT` | IT | mTLS/SPIFFE | `tests/integration/test_mtls.py` |
| 19 | `E2E-WIRE-IT` | IT | wire sync | `tests/integration/test_wire_contract.py` |
| 20 | `CF-QK` | CF | queryKnowledge conformance | `tests/conformance/test_query_knowledge.py` |
| 21 | `CF-GKI` | CF | getKnowledgeItem conformance | `tests/conformance/test_get_knowledge_item.py` |
| 22 | `CF-MEM` | CF | Memory conformance | `tests/conformance/test_memory_methods.py` |
| 23 | `E2E-KNOWLEDGE` | E2E | Knowledge path | `tests/e2e/test_knowledge.py` |
| 24 | `E2E-MEMORY` | E2E | Memory path | `tests/e2e/test_memory.py` |
| 25 | `E2E-MUTEX` | E2E | mutex | `tests/e2e/test_mutex.py` |
| 26 | `TZ-DECAY` | TZ | decay FakeClock | `tests/time_travel/test_decay.py` |
| 27 | `TZ-PROMOTE` | TZ | promotion | `tests/time_travel/test_promotion.py` |
| 28 | `TZ-GC` | TZ | retention GC | `tests/time_travel/test_gc.py` |
| 29 | `PERF-BM25` | PERF | 10K p95<100ms | `tests/performance/test_bm25.py` |
| 30 | `PERF-MEM` | PERF | 50K p95<50ms | `tests/performance/test_memory.py` |
| 31 | `HELM-DEPLOY-001` | DEPLOY | Helm template group 1 | `tests/deploy/test_helm_001.py` |
| 32 | `HELM-DEPLOY-002` | DEPLOY | Helm template group 2 | `tests/deploy/test_helm_002.py` |
| 33 | `HELM-DEPLOY-003` | DEPLOY | Helm template group 3 | `tests/deploy/test_helm_003.py` |
| 34 | `HELM-DEPLOY-004` | DEPLOY | Helm template group 4 | `tests/deploy/test_helm_004.py` |
| 35 | `HELM-DEPLOY-005` | DEPLOY | Helm template group 5 | `tests/deploy/test_helm_005.py` |
| 36 | `HELM-DEPLOY-006` | DEPLOY | Helm template group 6 | `tests/deploy/test_helm_006.py` |
| 37 | `HELM-DEPLOY-007` | DEPLOY | Helm template group 7 | `tests/deploy/test_helm_007.py` |
| 38 | `DOCKER-DEPLOY-001` | DEPLOY | build | `tests/deploy/test_docker_build.py` |
| 39 | `DOCKER-DEPLOY-002` | DEPLOY | security | `tests/deploy/test_docker_security.py` |
| 40 | `DOCKER-DEPLOY-003` | DEPLOY | artifacts | `tests/deploy/test_docker_artifacts.py` |
| 41 | `DEPLOY-001` | DEPLOY | values-schema | `tests/deploy/test_values-schema.py` |
| 42 | `DEPLOY-002` | DEPLOY | single-replica | `tests/deploy/test_single-replica.py` |
| 43 | `DEPLOY-003` | DEPLOY | shared-pod | `tests/deploy/test_shared-pod.py` |
| 44 | `DEPLOY-004` | DEPLOY | config-ref | `tests/deploy/test_config-ref.py` |
| 45 | `DEPLOY-005` | DEPLOY | secret-ref | `tests/deploy/test_secret-ref.py` |
| 46 | `DEPLOY-006` | DEPLOY | cert-issue | `tests/deploy/test_cert-issue.py` |
| 47 | `DEPLOY-007` | DEPLOY | cert-rotate | `tests/deploy/test_cert-rotate.py` |
| 48 | `DEPLOY-008` | DEPLOY | tls13 | `tests/deploy/test_tls13.py` |
| 49 | `DEPLOY-009` | DEPLOY | mtls | `tests/deploy/test_mtls.py` |
| 50 | `DEPLOY-010` | DEPLOY | kopf | `tests/deploy/test_kopf.py` |
| 51 | `DEPLOY-011` | DEPLOY | otel | `tests/deploy/test_otel.py` |
| 52 | `DEPLOY-012` | DEPLOY | otlp-tls | `tests/deploy/test_otlp-tls.py` |
| 53 | `DEPLOY-013` | DEPLOY | argo-app | `tests/deploy/test_argo-app.py` |
| 54 | `DEPLOY-014` | DEPLOY | appset | `tests/deploy/test_appset.py` |
| 55 | `DEPLOY-015` | DEPLOY | prom-rules | `tests/deploy/test_prom-rules.py` |
| 56 | `DEPLOY-016` | DEPLOY | service-monitor | `tests/deploy/test_service-monitor.py` |
| 57 | `DEPLOY-017` | DEPLOY | shutdown | `tests/deploy/test_shutdown.py` |
| 58 | `DEPLOY-018` | DEPLOY | image-tag | `tests/deploy/test_image-tag.py` |
| 59 | `DEPLOY-019` | DEPLOY | supply-chain | `tests/deploy/test_supply-chain.py` |
| 60 | `DEPLOY-020` | DEPLOY | rollback | `tests/deploy/test_rollback.py` |

镜像规则：每个 production `src/.../*.py` 有同职责 `tests/unit/.../test_*.py`；跨包契约映射 integration/conformance；Helm/Docker/GitOps 映射 deploy。汇总：UT 11、IT 8、CF 3、E2E 3、TZ 3、PERF 2、DEPLOY 30，合计 60。

### 10.2 验收清单 30 条

#### 10.2.1 文档完整性（5）

- [x] AC-DOC-01：§0-§13 与附录 A/B 完整。

- [x] AC-DOC-02：3 CRD schema 完整。

- [x] AC-DOC-03：4 handler 契约完整。

- [x] AC-DOC-04：Observability/errors/Helm 完整。

- [x] AC-DOC-05：L1/L2/L3/ADR/Constitution 可追踪。

#### 10.2.7 wire contract（6）

- [x] AC-WIRE-01：KnowledgeScope 同步。

- [x] AC-WIRE-02：KnowledgeItem 同步。

- [x] AC-WIRE-03：Memory 同步。

- [x] AC-WIRE-04：4 method envelope 同步。

- [x] AC-WIRE-05：23 integer error name/code 稳定。

- [x] AC-WIRE-06：L3-6 异常透传。

#### 10.2.14 5 维矩阵（4）

- [x] AC-VIS-01：caller 维度完整。

- [x] AC-VIS-02：visibility 维度完整。

- [x] AC-VIS-03：Knowledge/Memory 同 resolver 语义。

- [x] AC-VIS-04：默认拒绝与 agent-private 边界。

#### 10.2.19 4 级 scope（4）

- [x] AC-SCOPE-01：project→team→organization→industry 固定。

- [x] AC-SCOPE-02：循环引用 fail-closed。

- [x] AC-SCOPE-03：missing parent 显式错误。

- [x] AC-SCOPE-04：cache 不改变结果。

#### 10.2.24 admission 互斥（4）

- [x] AC-ADM-01：Knowledge→Memory 冲突拒绝。

- [x] AC-ADM-02：Memory→Knowledge 冲突拒绝。

- [x] AC-ADM-03：50ms fail-closed。

- [x] AC-ADM-04：Warning Event 且 content 脱敏。

#### 10.2.29 Helm 部署（4）

- [x] AC-HELM-01：replicaCount const=1。

- [x] AC-HELM-02：共享 Pod 两业务进程。

- [x] AC-HELM-03：mTLS/RBAC/NetworkPolicy 完整。

- [x] AC-HELM-04：7 模板 lint/render。

#### 10.2.34 测试矩阵（3）

- [x] AC-TEST-01：60/60 能力组有路径。

- [x] AC-TEST-02：80/95 覆盖率。

- [x] AC-TEST-03：全门禁阻断合并。

### 10.3 工具链

```text
uv sync --frozen
ruff format --check . && ruff check .
pyright --level error
bandit -r packages services && pip-audit
interrogate -f 100 packages services
lint-imports
pytest --cov=superteam_a2a.knowledge_service --cov-fail-under=80
helm lint helm/knowledge-service && helm template knowledge-service helm/knowledge-service
```

- `ST-KNOWLEDGE-BOUNDARY`：L3-5 只依赖共享 Pydantic types、A2A public Protocol、K8s async client；禁止 Adapter SDK、业务 Agent、L3-6 私有实现、SDK private path。
- `ST-KNOWLEDGE-CONFTEST`：unit 不导入 integration/e2e fixture；integration 可导入 shared fixture；e2e 只依赖 public test-support；禁止 conftest 循环。
- uv + Hatchling、Docker 多阶段、Helm 3.14、cert-manager、Kopf、OTel Collector、Argo CD 版本由 lock/chart metadata 固定。任一门禁失败即拒绝合并，符合 ADR-0005 §11 与 Constitution §9.7。

### 10.4 覆盖率

全包行/分支覆盖率 `>=80%`；`scope_resolver`, `visibility_resolver`, `bm25_index`, `admission_validator` 行/分支均 `>=95%`。BM25 10K warm p95 `<100ms`，Memory 50K filter p95 `<50ms`，admission p99 `<50ms`。禁止 exclude/ignore 绕过阈值。

---

## 11. 工具链与部署

### 11.1 七步开发工作流

1. `uv sync --frozen --all-extras` 还原 workspace lock。
2. `ruff format --check . && ruff check . && pyright` 执行格式、lint、strict type。
3. `bandit -r packages services && pip-audit && interrogate -f 100 ... && lint-imports` 执行安全、供应链、docstring、边界门禁。
4. `pytest tests/unit tests/integration --cov ...` 执行 60 ID 与 80/95 双阈值。
5. `docker buildx build --target runtime`，生成 SBOM、Trivy 扫描并 Cosign 签名。
6. `helm lint`、`helm template`、kind 安装，验证 cert-manager/Kopf/mTLS/E2E/PERF。
7. Argo CD sync staging，经 smoke/readiness 后 promote production；失败回滚不可变 tag。

### 11.2 多阶段 Dockerfile

```dockerfile
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /workspace
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY packages ./packages
COPY services/knowledge-service ./services/knowledge-service
RUN uv build services/knowledge-service
FROM python:3.12-slim AS runtime
RUN groupadd -g 65532 app && useradd -u 65532 -g app -M app
WORKDIR /app
COPY --from=build /workspace/.venv /app/.venv
COPY --from=build /workspace/services/knowledge-service /app/knowledge-service
ENV PATH=/app/.venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65532:65532
EXPOSE 8080 8443
HEALTHCHECK --interval=30s --timeout=3s CMD ["python", "-m", "superteam_a2a.knowledge_service.healthcheck"]
ENTRYPOINT ["python", "-m", "superteam_a2a.knowledge_service"]
```
Build 必须 frozen；runtime 不含编译器/cache、UID 65532、Pod read-only rootfs。`DOCKER-DEPLOY-001~003` 验证可复现构建、non-root/restricted、health/SBOM/signature。

### 11.3 cert-manager 颁发

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
最低 TLS 1.3、client cert/URI SAN 必验；Secret watch 原子替换 SSLContext，不重启 Pod、不记录 key/cert。到期与 reload failure 产生 metric/Event。

### 11.4 Kopf 启动配置

```python
import kopf


@kopf.validation("superteam-a2a.io", "v1alpha1", "knowledgeitems")
async def validate_knowledge_item(spec: dict[str, object], **_: object) -> None:
    await admission_validator.validate_knowledge_item(spec, timeout_ms=50)
```
L3-5 只注册 `@kopf.validation`；禁止 `@kopf.timer`、reconcile 与业务 Agent handler。60s timer 仅 L3-6。admission 50ms fail-closed，Kopf 由 uv.lock pin，并在 kind 真实 webhook 验证。

### 11.5 OTel Collector sidecar + Argo CD Application/AppSet

```yaml
- name: otel-collector
  image: otel/opentelemetry-collector-contrib:0.104.0
  args: ["--config=/conf/collector.yaml"]
  ports: [{name: otlp-grpc, containerPort: 4317}]
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
AppSet 用 dev/staging/prod list generator；prod 使用签名不可变 tag 与人工 promote。OTel 仅接收 localhost OTLP 并 TLS 转发；其为基础设施进程，不改变“L3-5 + L3-6 两个业务 Python 进程”不变量。

---

## 12. 验收清单（§A-§G · 30 条）

| ID | 维度 | 验收项 | 状态 |
|---|---|---|---|
| ACCEPT-001 | A 文档完整性 | §0-§13 与附录 A/B 完整 | ✅ |
| ACCEPT-002 | A 文档完整性 | 3 CRD schema 完整 | ✅ |
| ACCEPT-003 | A 文档完整性 | 4 handler 契约完整 | ✅ |
| ACCEPT-004 | A 文档完整性 | Observability/errors/Helm 完整 | ✅ |
| ACCEPT-005 | A 文档完整性 | 引用链齐全 | ✅ |
| ACCEPT-006 | B 接口契约 | KnowledgeScope wire 同步 | ✅ |
| ACCEPT-007 | B 接口契约 | KnowledgeItem wire 同步 | ✅ |
| ACCEPT-008 | B 接口契约 | Memory wire 同步 | ✅ |
| ACCEPT-009 | B 接口契约 | 4 method 永久不变 | ✅ |
| ACCEPT-010 | B 接口契约 | 23 error 稳定 | ✅ |
| ACCEPT-011 | B 接口契约 | L3-6 异常透传 | ✅ |
| ACCEPT-012 | C 可见性 | 4级scope固定 | ✅ |
| ACCEPT-013 | C 可见性 | 5维矩阵默认拒绝 | ✅ |
| ACCEPT-014 | C 可见性 | Knowledge/Memory同语义 | ✅ |
| ACCEPT-015 | C 可见性 | agent-private边界 | ✅ |
| ACCEPT-016 | D 安全 | TLS1.3/mTLS | ✅ |
| ACCEPT-017 | D 安全 | cert-manager热更新 | ✅ |
| ACCEPT-018 | D 安全 | read-only RBAC/default deny | ✅ |
| ACCEPT-019 | D 安全 | admission fail-closed/脱敏 | ✅ |
| ACCEPT-020 | E 性能 | BM25 p95<100ms | ✅ |
| ACCEPT-021 | E 性能 | Memory p95<50ms | ✅ |
| ACCEPT-022 | E 性能 | admission p99<50ms | ✅ |
| ACCEPT-023 | E 性能 | CPU有界offload | ✅ |
| ACCEPT-024 | F 部署 | 7 Helm模板 | ✅ |
| ACCEPT-025 | F 部署 | replicaCount=1 | ✅ |
| ACCEPT-026 | F 部署 | 同Pod两业务进程 | ✅ |
| ACCEPT-027 | F 部署 | Docker/cert/OTel/Argo | ✅ |
| ACCEPT-028 | G 测试 | 60/60路径 | ✅ |
| ACCEPT-029 | G 测试 | 全包≥80% | ✅ |
| ACCEPT-030 | G 测试 | 关键模块≥95% | ✅ |

60/60：UT 11、IT 8、CF 3、E2E 3、TZ 3、PERF 2、DEPLOY 30。7 Helm 交付：helpers/values、Deployment、Service、ServiceAccount、RBAC、NetworkPolicy、PrometheusRule+ServiceMonitor。勾选仅表示 Spec 写全；L4 必须运行测试重新证明。

---

## 13. 开放问题（22 项三层模式）

### 13.1 继承业务层 12 项

| ID | 问题 | 状态 | 决议 |
|---|---|---|---|
| OPEN-L2-4-001 | AgentCard兼容 | 🟡 | 每 minor conformance |
| OPEN-L2-4-002 | Kopf timer差异 | 🟡 | L3-6 kind spike |
| OPEN-L2-4-003 | GIL/BM25 | ✅ | anyio offload |
| OPEN-L2-4-004 | FakeClock/sleep | ✅ | Clock Protocol |
| OPEN-L2-4-005 | 多集群Issuer | 🟡 | L4验证 |
| OPEN-L2-4-006 | 50ms admission | ✅ | fail-closed |
| OPEN-L2-4-007 | 自动scope-up | 🔵 | v0.5+ |
| OPEN-L2-4-008 | Vector DB | 🔵 | v0.5+ |
| OPEN-L2-4-009 | Memory全文搜索 | 🔵 | v0.5+ |
| OPEN-L2-4-010 | Leader in-flight | ✅ | drain30s |
| OPEN-L2-4-011 | Multi-cluster | 🔵 | v1.0+ |
| OPEN-L2-4-012 | PII加密 | 🔵 | 安全ADR |

### 13.2 继承 Spec 4 项

| ID | 问题 | 状态 | 决议 |
|---|---|---|---|
| OPEN-L2-4-013 | Settings/env优先级 | 🟡 | L4验证 |
| OPEN-L2-4-014 | 10K index内存 | 🟡 | PERF验证 |
| OPEN-L2-4-015 | Kopf 50ms timeout | 🟡 | kind spike |
| OPEN-L2-4-016 | CRD/chart顺序 | ✅ | install gate |

### 13.3 继承 Python 6 项

| ID | 问题 | 状态 | 决议 |
|---|---|---|---|
| OPEN-L2-4-017 | Protocol/BaseModel | ✅ | 分离 |
| OPEN-L2-4-018 | GIL/admission | ✅ | 短IO |
| OPEN-L2-4-019 | workspace发布 | ✅ | 同步版本 |
| OPEN-L2-4-020 | freezegun/sleep | ✅ | FakeClock |
| OPEN-L2-4-021 | a2a-python Pydantic | 🟡 | upstream追踪 |
| OPEN-L2-4-022 | alias/camelCase | ✅ | schema diff |

### 13.4 L3-5/L3-6 新增项

| ID | 问题 | 状态 | 决议 |
|---|---|---|---|
| OPEN-L3-5-001 | 共享Deployment | ✅ | 同Pod两业务进程；replica=1 |
| OPEN-L3-5-002 | in-process协议 | ✅ | async异常透传；无loopback HTTP |
| OPEN-L3-5-003 | _SCOPE_CACHE LRU | 🟡 | 4096/TTL60s |
| OPEN-L3-5-004 | BM25 rebuild | 🟡 | startup+watch |
| OPEN-L3-5-005 | admission互斥边界 | ✅ | 双向50ms fail-closed |
| OPEN-L3-5-006 | L3-6 readiness | 🟡 | readiness gate |
| OPEN-L3-5-007 | metric registry | ✅ | 独立registry汇聚 |
| OPEN-L3-5-008 | EventReason扩展 | ✅ | enum contract |
| OPEN-L3-5-009 | OTel进程计数 | ✅ | 基础设施进程 |
| OPEN-L3-5-010 | read/write RBAC | 🟡 | 两个最小Role共享SA |

上游 22 项按业务12 + Spec4 + Python6 分层；已解决 11/22，**收敛率 50%**。L3 新增项独立跟踪，不改变分母。

### 13.5 v0.5+ 五项演进路线

| 演进 | 触发 | 窗口 |
|---|---|---|
| Vector DB | >10K 且 BM25 不达标 | v0.5+ |
| 自动 scope-up | eligibility + 审批 CRD | v0.5+ |
| Memory 全文搜索 | 命中率<80% 7天 | v0.5+ |
| Multi-cluster | 跨集群 query | v1.0+ |
| PII 加密 | 安全审计 | v0.5+ |

---

## 附录 B：ADR / Constitution 引用矩阵（5 子表）

### B.1 架构映射

| 本 Spec | 上游 | 约束 | 强度 |
|---|---|---|---|
| 单实例 | L1 Arch §3.5.2；ADR-0005 §6.2；Constitution §3.8 | replica=1/单worker | MUST |
| 包结构 | ADR-0005 §13.1；Constitution §3.8 | Python3.12+/uv | MUST |
| 共享Deployment | L2-4 Design §14.1 | 两业务进程 | MUST |

### B.2 接口契约

| 本 Spec | 上游 | 约束 | 强度 |
|---|---|---|---|
| CRD | L1 Spec §5.2.2；L2-4 §3 | wire同步 | MUST |
| 4 handlers | L2-4 §6；L3-2 | method envelope | MUST |
| errors | L2-4 §9；L3-6 | code/name | MUST |
| tests | Constitution §9.6/§14.4 | 60 ID镜像 | MUST |

### B.3 可见性与业务边界

| 本 Spec | 上游 | 约束 | 强度 |
|---|---|---|---|
| scope | ADR-0002 §3；L2-4 §4 | 4级继承 | MUST |
| visibility | ADR-0002 §4；L2-4 §4 | 5维默认拒绝 | MUST |
| mutex | ADR-0003 §5；L2-4 §5 | 双向互斥 | MUST |
| Memory委托 | ADR-0003 §3/§4 | 无reconcile | MUST |

### B.4 安全

| 本 Spec | 上游 | 约束 | 强度 |
|---|---|---|---|
| mTLS/cert | ADR-0005 §9.1；Constitution §6 | TLS1.3/hot reload | MUST |
| RBAC/policy | Constitution §6.2/§6.5 | 最小权限/default deny | MUST |
| 静态门禁 | ADR-0005 §11；Constitution §9.7 | 6重门禁 | MUST |
| 脱敏 | ADR-0005 §10；Constitution §7.3 | content/token/key禁记 | MUST |

### B.5 可观测性与测试

| 本 Spec | 上游 | 约束 | 强度 |
|---|---|---|---|
| metrics | L3-2 §9；Constitution §7.1 | 11+4+5 | MUST |
| logs/events | L3-1 §7；Constitution §7.3/7.4 | 8字段/8reason | MUST |
| OTel | Constitution §7.2 | W3C/OTLP | MUST |
| tests | ADR-0005 §11；Constitution §9/§15.5 | 60 ID/80/95 | MUST |

---

## 附录 A：跨模块引用清单（v0.2-draft-full）

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
| 版本 | **v0.2.0**（2026-07-29 #63.5 升级 · 评审通过 + 错误码 23 处漂移修正） |
| 状态 | ✅ §0-§13 + 附录 A/B + M.1-M.6 完整；已通过独立评审（§A-§Q 10 维度全 PASS / 0 阻塞项 / 4 关注项 / 4 建议项） |
| 上游 | L1 Architecture v0.2.0 §3.5.2 + L1 Spec v0.2.0 §5.2.2 + L2-4 Spec v0.2.0 + L2-4 Design v0.2.0 |
| 同级已通过 | L3-1 Operator Core v0.2.0 (#56) + L3-2 A2A Core v0.2.0 (#54) + L3-3 Adapter SDK v0.2.0 (#58) + L3-4 Hello Agent v0.2.0 (#61) |
| 评审报告 | `docs/reviews/l3-5-knowledge-service-spec-review.md`（2026-07-29 #63.5 · 552 行 / 57KB / §A-§Q 17 节 / 10 维度全 PASS） |
| 当前变更边界 | v0.2.0 已通过评审；待 §F 6 步跨文档同步 + L3-6 启动；2 项关注项（RBAC 拆分 + 性能门禁）移交 v0.2.1 / L4 |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-27 #43 | L2-4 Knowledge/Memory Spec v0.2.0 评审通过 | L2-4 上游就绪 |
| 2026-07-29 #63.1 | L3-5 Knowledge Service Spec v0.2-draft 骨架稿：头部 11 段 + §0 阅读指南 + 5 项 Python 化关键决策 D-1~D-5 + 9 维度 Go→Python 对照 + §1 模块使命 + 5 项关键不变量 + 30 文件清单汇总 + 60 测试 ID 镜像规则 + 8 边界规则 + §2 Python 包结构 + §3-§13 占位章节结构 + 附录 A 5 子表 + 文档元数据 M.1-M.6 | **v0.2-draft 骨架稿** |
| 2026-07-29 #63.2.1（Subagent 1） | L3-5 §3-§6 补完：§3 3 CRD types 完整 Pydantic v2 schema（KS-CRD × 60 行 + KI-CRD × 80 行 + MEM-CRD × 50 行 · wire 同步矩阵 3 张表 · 28 测试 ID）+ §4 4 A2A method handler 完整 Python Protocol 30 行/个（queryKnowledge BM25 + getKnowledgeItem K8s API + recordMemory/queryMemory 委托 L3-6 · wire 同步矩阵 4 张表 · 32 测试 ID）+ §5 admission webhook 双向互斥（admission_validator.py 50 行 Protocol + 5 步互斥算法 + 4 步 scope_ref 循环检测 · cert-manager TLS + 50ms fail-closed · 17 测试 ID）+ §6 MemoryReconciler 协调点（共享 Deployment 拓扑图 + in-process function reference 契约 3 规则 · 8 测试 ID） | **v0.2-draft §3-§6 补完稿** · §7-§10 + 附录 B 待 Subagent 2 补完 |
| 2026-07-29 #63.2.2（Subagent 2） | 补完 §7-§13 + 附录 B：20 指标 + structlog 8 字段 + 8 EventReason；23 错误码与 retry/CB 矩阵；7 Helm 模板组 + L3-6 共享 chart；60 测试能力组 + 30 验收点 + 7 步工作流 + Docker/cert-manager/Kopf/OTel/Argo；22 项开放问题三层模式；ADR/Constitution 5 子表 | **v0.2-draft-full** · 待 #63.5 独立评审 |
| 2026-07-29 #63.5 | L3-5 独立评审（Subagent 3）：552 行 / 57KB / §A-§Q 17 节 / 10 维度全 PASS（0 阻塞 / 4 关注 / 4 建议）+ 错误码漂移 23 处全部替换为 L2-4 §9.1 权威名（Subagent 4 修正）+ §5 admission 4 处内部编号漂移修正 | **v0.2.0 升级** |
| 2026-07-29 #63.5.1（Subagent 4 修正） | 错误码 50+ 处修正：§8.1 11 KNOWLEDGE_* + §8.2 12 MEMORY_* + §8.3 Retryable 矩阵 23 行 + §5.0-5.3 admission 5 处 + §4 getKnowledgeItem handler 4 处 + §5.1 imports 8 个；与 L2-4 v0.2.0 §9.1 权威名 100% 一致 | 关注项 §M-1.1 + §M-1.2 关闭 |
| **2026-08-09 #87** | **Phase 2 PR-1 RBAC §M-1.4 修复（PR #22 merged）+ PR-2 K8sLeaseLeaderElector 完整实装（PR #23 merged · 192 PASS）+ PR-3 H-RM/H-QM IT/CF stub 4 ID 实装（PR #24 merged）+ PR-4 kind E2E spike 基础设施（PR #25 open · LEADER-E2E-001 PASS · 5 skipped · chart 缺口 P0 跟进 PR-4.1）** | **Phase 2 spike 4/5 PR 完成 · ADR-0006 D 方案兼容性 100% 保持 · 5 项关键不变量持续 PASS** |

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

1. **§F.1-§F.6 跨文档同步 6 步**（ROADMAP L3 矩阵 + L2-4 Spec 附录 A + L3-1/L3-2/L3-3/L3-4 附录 A + README + CONSTITUTION-CHANGELOG；参照 #62 §F 6 步模板）
2. **git commit**：`feat(L3-5): 升级 v0.2.0 + 评审通过 + 错误码 23 处漂移修正 + §F 6 步跨文档同步`
3. **L3-6 Memory backend Spec 起草**（独立会话；基于 L2-4 v0.2.0 Spec + L3-5 §6.2 共享 Deployment 协调点；建议拆 Spec 起草 + 评审两会话避免 §16.1 红线；目标 v0.2-draft 骨架稿）
4. **关注项 v0.2.1 微同步**（RBAC 拆分 read-only/write 两个 Role；移交 L3-6 Spec 起草）

### M.5 关注项台账（移交 v0.2.1 / L4 / L3-6）

| 编号 | 关注项 | 状态 | 移交 |
|------|--------|------|------|
| L3-5-followup-1 | v0.2.1 拆分 RBAC read-only Role (L3-5) + write Role (L3-6) | 🟡 open | L3-6 Spec 起草 + L4 kind 测试 |
| L3-5-followup-2 | 性能门禁验证（BM25 10K p95<100ms / Memory 50K p95<50ms / admission p99<50ms） | 🟡 open | L4 实施第一周 |
| L3-5-followup-3 | Kopf admission 50ms fail-closed 实际超时行为（kind webhook 真实环境） | 🟡 open | L4 实施第一周 |
| L3-5-followup-4 | _SCOPE_CACHE 默认 4096 entries / TTL 60s / BM25 rebuild 策略 | 🟡 open | L4 性能测试收敛 |
| L3-5-followup-5 | 附录 B B.5 tests row 补充'含 BM25 10K p95<100ms / Memory 50K p95<50ms / admission p99<50ms'明确描述 | 🟡 open | v0.2.1 微同步 |
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
