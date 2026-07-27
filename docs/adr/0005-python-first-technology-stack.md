# ADR-0005：Python-first 全栈技术栈迁移

> **架构级元决策**：本 ADR 将 `superteam-a2a` 的平台自有实现从 Go-first 调整为 **Python-first**。它只 supersede ADR-0001~0004、L1/L2/L3 中与 Go / kubebuilder / controller-runtime / client-go 绑定的**实现条款**；协议、CRD、知识/记忆语义、版本范围与质量门禁继续有效。
>
> **执行门禁**：本 ADR 与宪法 v0.5.0 通过后，才能更新 L1 v0.2；L1 v0.2 评审通过后，才能更新 L2 v0.2；L2 v0.2 评审通过后，才能重写 Python L3。L3 评审通过前不得初始化产品实现代码。

---

## 状态

| 字段 | 值 |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-24 |
| **Deciders** | 项目发起人（CoderZhangfujiang） |
| **Reviewers** | 项目发起人（依据宪法 14.5 MVP 例外，单点评审） |
| **Supersedes** | ADR-0001~0004 中 Go struct / Go package / kubebuilder / controller-runtime / client-go 等实现语言条款（仅实现条款） |
| **Superseded by** | 无 |
| **Related** | ADR-0001（版本范围）、ADR-0002（知识管理）、ADR-0003（Memory）、ADR-0004（v0.1 范围与时间线） |
| **Constitution** | v0.5.0（Python-first + 语言中立质量门禁） |

---

## 1. 背景（Context）

### 1.1 当前项目阶段

截至 2026-07-24，项目完成：

- ADR-0001~0004；
- 宪法 v0.4.0；
- L1 Architecture / System Spec v0.1.0；
- L2 四模块设计、Spec 与评审；
- L3-1 Operator Core、L3-2 A2A Core 两份 Go 文件级 draft。

尚未创建产品 `src/`、`go.mod`、`pyproject.toml`，也没有进入 L4 实现。因此这次调整发生在**设计已深入、实现尚未开始**的窗口：协议和业务契约已经清晰，但还没有生产代码迁移成本。

### 1.2 用户决策

用户明确选择：

> `superteam-a2a` 使用全栈 Python 技术栈。

这里的“全栈 Python”定义为：

- Operator Core：Python；
- A2A Core：Python；
- Adapter SDK 与平台官方 Adapter：Python；
- Knowledge Service / Memory backend：Python；
- Hello Agent：Python；
- 构建、测试、静态检查和工程工具以 Python 生态为主。

不意味着第三方 Agent Runtime 必须是 Python。平台仍必须通过 A2A/localhost 边界兼容 Python、JavaScript、.NET、Java、Rust 等运行时。

### 1.3 为什么现在调整

1. **框架生态匹配**：LangChain、AutoGen、CrewAI、Semantic Kernel Python、Strands、Smolagents 的主流用法集中在 Python，Python Adapter 可减少跨语言桥接。
2. **单人维护效率**：用户投入约 2h/day。统一核心语言可减少 Go 控制面 + Python Agent 双语言上下文切换。
3. **官方 A2A Python SDK 可复用**：不再需要自研完整 Go A2A envelope/type/server/client，可将精力用于 Kubernetes 原生运行时、扩展 method 与可靠性。
4. **尚未编码**：当前只有文档，不存在生产数据迁移、Go API 兼容或双栈发布问题。
5. **质量第一**：现在显式重做设计门禁，比实现中途“边写边换”更符合宪法第十四、十五条。

### 1.4 影响规模

静态审计发现约 20~21 个权威/历史 Markdown 文件中有约 562 处 Go、`.go`、kubebuilder、controller-runtime、client-go、envtest、godoc 或 Go 工具链绑定。此变更不是文本替换，而是：

- Operator 运行模型变化；
- A2A 上游复用策略变化；
- 类型与 Schema 单一来源变化；
- 异步 I/O、GIL 和多进程约束变化；
- 测试工具和集成测试方法变化；
- L3 文件树与接口签名整体变化。

---

## 2. 决策（Decision）

### 2.1 核心结论

`superteam-a2a` 平台自有代码采用 **Python 3.12+ / async-first / typed-first / protocol-first** 技术栈。

Python-first 不降低任何外部承诺：Kubernetes 原生、A2A 兼容、mTLS、可观测性、幂等 reconcile、Leader Election、80% 测试覆盖和 Design-First 门禁全部保留。

### 2.2 技术栈基线

| 领域 | 采纳技术 | 约束 |
|---|---|---|
| Python | Python 3.12+ | 优先生态兼容和稳定性；升级走依赖评审 |
| Workspace / lock | `uv` workspace + `pyproject.toml` + `uv.lock` | CI 必须 `uv sync --frozen` |
| Package layout | PEP 420 namespace package | 各模块独立发布依赖，统一 `superteam_a2a.*` 命名空间 |
| Operator framework | Kopf | handler/retry/resume/finalizer/admission 需 kind 验证 |
| Kubernetes client | `kubernetes_asyncio` | 禁止在 event loop 内调用阻塞式 K8s client |
| A2A | 官方 `a2a-sdk` | 标准类型/Server/Client 优先复用；不 fork |
| ASGI | 官方 A2A SDK ASGI + Starlette/FastAPI + Uvicorn | A2A 与 probe/admin 路由边界显式 |
| HTTP client | `httpx.AsyncClient` | 进程级复用连接池；所有请求必须 timeout |
| 类型/Schema | Pydantic v2 + `pydantic-settings` | strict model；JSON Schema 2020-12 |
| Retry | Tenacity | 仍受 method idempotency gate 约束 |
| Metrics | `prometheus-client` | 保留既有指标名与 label 基数限制 |
| Trace | OpenTelemetry Python SDK | W3C Trace Context |
| Logs | `structlog` + stdlib logging | JSON；敏感内容禁记 |
| Unit/IT | pytest + pytest-asyncio/AnyIO + respx | async 路径必须真实 await |
| Property/Fuzz | Hypothesis + hypothesis-jsonschema | envelope/schema/FSM/算法 |
| Type gate | Pyright strict | 禁止 unchecked `Any` 穿过公共边界 |
| Lint/format | Ruff | 单一 formatter/linter |
| Security | Bandit + pip-audit + Trivy/Cosign | Python 依赖 + 镜像双层扫描 |
| E2E | kind + pytest | 真实 K8s reconcile / webhook / mTLS |
| Package image | `python:3.12-slim` 多阶段构建 | 非 root、read-only rootfs、最小依赖 |

精确依赖版本不在本 ADR 硬编码；在 L3/首个 lockfile 中 pin，并由 compatibility matrix 与 CI 验证。

---

## 3. 模块映射

### 3.1 Operator Core

原 Go controller-runtime 的 4 Controller 映射为 Kopf handlers + 独立 service/reconciler：

| 原模块 | Python 形态 |
|---|---|
| AgentReconciler | `operator.handlers.agent` + `AgentReconciler` service |
| AgentSetReconciler | `operator.handlers.agentset` + `AgentSetReconciler` service |
| WorkflowReconciler | `operator.handlers.workflow` + `WorkflowReconciler` service |
| MemoryReconciler | `operator.handlers.memory` + lifecycle services |
| manager setup | Kopf startup/cleanup hooks + operator settings |
| finalizer | Kopf delete/finalizer semantics + explicit helper |
| workqueue/retry | Kopf retry/backoff + project error classifier |
| admission | Kopf validation webhook + cert-manager TLS |
| leader election | Kubernetes Lease 或经 kind 证明等价的 Kopf coordination |

**关键原则**：handler 只做事件适配、依赖解析和状态写回；可测试的业务逻辑放在普通 async service 中。不得把全部 reconcile 逻辑堆进 decorator 函数。

### 3.2 A2A Core

标准 A2A 资源优先直接复用官方 SDK：

- Agent Card；
- Message / Part；
- Task / TaskState / Artifact；
- 标准请求响应 envelope；
- 标准 ASGI server/client 能力；
- 上游 conformance 兼容。

项目自有层只负责：

- `a2a.queryKnowledge`；
- `a2a.getKnowledgeItem`；
- `a2a.recordMemory`；
- `a2a.queryMemory`；
- K8s Service/EndpointSlice Discovery；
- 项目授权、限流、重试、Circuit Breaker、P2C；
- 项目指标、Trace 与结构化日志；
- 与上游 SDK 隔离的 compatibility adapter。

所有官方 SDK import 应集中在 `superteam_a2a.a2a.upstream` 边界，防止 SDK 升级扩散到业务模块。

### 3.3 Adapter SDK

- 使用 `typing.Protocol` / ABC 定义 async Adapter contract；
- Python-native framework 可以采用同进程 plugin；
- 默认部署仍保留 Sidecar，以维护进程隔离、资源边界和 framework 依赖隔离；
- 各 framework Adapter 独立 workspace package 和镜像；
- Adapter 必须复用 A2A Core 的 Server、Schema、TLS、限流和 Trace，不复制协议实现。

### 3.4 Knowledge / Memory

- Pydantic model 表达 CRD 与 A2A extension DTO；
- CRD/etcd 仍是持久化事实来源；
- Knowledge Service + Memory backend v0.1 仍共享 Deployment；
- 内存倒排索引 + BM25 保留，不引入外部搜索引擎；
- Memory decay/reinforce/GC/promotion 算法保持数学等价；
- Clock 使用 `Protocol` 注入，测试使用 FakeClock；
- 大索引 rebuild/search 使用受控线程 offload，不阻塞 async event loop。

### 3.5 Hello Agent

- 使用 Python 实现最小 Agent 与 A2A Server 集成；
- 作为官方 SDK、Adapter contract、mTLS、可观测性、Helm 和 E2E 的 Golden Agent；
- 不引入具体 LLM provider 作为 Hello path 前置条件。

---

## 4. 保持不变的公共契约

以下内容不因语言迁移改变：

1. **Kubernetes 基线**：Kubernetes 1.28+、Helm 3、CRD、Status、Finalizer、Leader Election、Admission、RBAC、NetworkPolicy。
2. **6 个 CRD**：Agent、AgentSet、Workflow、KnowledgeScope、KnowledgeItem、Memory。
3. **6 个 v0.1 A2A method**：sendMessage、getTask、queryKnowledge、getKnowledgeItem、recordMemory、queryMemory。
4. **Wire shape**：JSON 字段名、enum、时间格式、错误码、Task 状态机、Agent Card 路径。
5. **安全**：mTLS、SPIFFE ID 格式、ServiceAccount、最小权限、默认拒绝网络策略。
6. **可观测性**：指标名、Span 语义、日志字段、敏感内容禁记、高基数 label 禁令。
7. **Knowledge / Memory**：4 级 scope、agent-private 正交维度、可追溯字段、decay/reinforce/GC 公式。
8. **质量**：Design-First、评审、覆盖率 ≥80%、Conformance、kind E2E、镜像签名和扫描。

若 Python 实现无法满足上述契约，必须先提交新 ADR；不得以“Python 限制”为由静默降级。

---

## 5. 类型与 Schema 单一来源

### 5.1 Pydantic 作为项目类型源

项目自有 DTO、配置与 CRD model 使用 Pydantic v2 strict model：

- 禁止公共字段使用无约束 `Any`；
- 开启明确的 extra policy；
- 所有时间必须 timezone-aware UTC；
- enum 使用 `StrEnum`；
- immutable value object 默认 frozen；
- alias 保持 Kubernetes/A2A camelCase wire 字段；
- 业务层使用 Pythonic snake_case 属性。

### 5.2 CRD Schema 生成

Pydantic model → JSON Schema 2020-12 → deterministic Kubernetes OpenAPI v3 generator → checked-in CRD YAML。

生成器必须：

- 稳定排序，重复生成无 diff；
- 保留 `x-kubernetes-*` 扩展；
- 拒绝 Kubernetes 不支持的 schema 特性；
- 对 required/optional/default/nullable 做契约测试；
- 生成结果与示例 YAML 做 round-trip；
- 在 CI 中验证工作区无未提交生成差异。

官方 A2A SDK 已提供的标准类型不得重新定义；项目 Pydantic model 只覆盖扩展 method 与项目资源。

---

## 6. 异步、并发与进程模型

### 6.1 async-first

所有跨网络/磁盘边界使用 async：

- Kubernetes API；
- A2A HTTP；
- Agent Card Discovery；
- webhook；
- OpenTelemetry exporter；
- shutdown/flush。

禁止在 async handler 内直接调用阻塞 SDK。无法替换的阻塞工作必须通过受限 `anyio.to_thread.run_sync` / executor，并设置并发上限、timeout 与指标。

### 6.2 单进程原则

含本地 TaskStore、Discovery cache、BM25 index 或 limiter state 的 Pod 默认：

- 单 Python 进程；
- 单 Uvicorn worker；
- 单 event loop；
- 通过多个 Pod 水平扩展，而不是同 Pod 多 worker。

原因：多 worker 会复制内存状态、打破 task/idempotency/cache 一致性。若未来引入外部一致性存储，可以通过 ADR 重新评估多 worker。

### 6.3 GIL 与 CPU 工作

- JSON/Pydantic 校验保持短路径；
- BM25 rebuild/search、批量 decay 等 CPU 路径必须 benchmark；
- 超过 event-loop lag 门限时 offload 到线程；
- 线程池必须有固定容量和 backpressure；
- 不因 GIL 私自引入 Go/Rust extension；需要原生扩展时走 ADR。

### 6.4 取消与优雅停机

- 所有 background task 使用 structured concurrency/TaskGroup；
- ctx cancel 对应 asyncio cancellation；
- SIGTERM 顺序为 readiness=false → 停止接收 → 等待 in-flight → flush trace/log → 退出；
- 不得吞掉 `CancelledError`；
- 测试必须覆盖 shutdown timeout 和 partial failure。

---

## 7. Kubernetes Operator 可靠性门禁

Kopf 不能因为“框架宣称 production-ready”而自动视为与 controller-runtime 等价。进入 L4 前，L2/L3 必须定义并在 kind 验证：

1. create/update/resume/delete handler 幂等；
2. Operator 重启后 progress 恢复；
3. finalizer 失败重试和删除不泄漏；
4. API conflict / 409 重试；
5. watch reconnect 与 resourceVersion 过期；
6. event storm/backpressure；
7. leader failover；
8. timer/daemon 仅 leader 执行；
9. status patch 不覆盖 spec；
10. webhook TLS reload 与 fail-closed；
11. 多 namespace watch 权限；
12. graceful shutdown 后任务可恢复。

Leader Election 优先使用 `coordination.k8s.io/v1 Lease`；若采用 Kopf peering，必须证明它满足同等单活、故障切换和 RBAC 约束，并记录额外 CRD 成本。

---

## 8. A2A 与上游 SDK 门禁

在 L2-1 Python 版本批准前，需要完成只读文档验证或非产品 spike，确认：

- 官方包名和受支持 Python 版本；
- 当前协议版本；
- Agent Card/Task/Message/Artifact 类型；
- ASGI server 与 async client 能力；
- JSON-RPC / HTTP / SSE 边界；
- 自定义 method 注册扩展点；
- mTLS 自定义 transport 能力；
- conformance 套件接入方式；
- upstream error/type 在 minor upgrade 下的兼容策略。

若 SDK 不直接支持项目扩展 method：

- 在 compatibility adapter 外围增加 router；
- 标准 method 仍交给 SDK；
- 不复制/修改 SDK 标准类型；
- 不 fork 上游仓库；
- 通过 contract test 保证同一 JSON wire shape。

---

## 9. 安全决策

### 9.1 mTLS / SPIFFE

v0.1 必须保持 mTLS，不以 Python 库成熟度为理由降级：

- cert-manager 挂载 server cert/key/client CA；
- 使用 `ssl.SSLContext`，最低 TLS 1.3；
- client cert 必须校验；
- SPIFFE ID 从 URI SAN 解析并严格校验；
- 证书热更新通过原子替换 SSL context/transport；
- 不记录 cert/key 原文。

`py-spiffe` / Workload API 在 L3 前做兼容性验证。若不能稳定满足 SVID watch 和热更新，v0.1 使用 cert-manager mounted certificate + URI SAN，SPIRE Workload API 集成延期但必须登记，不得取消身份语义。

### 9.2 Python 供应链

- lockfile 必须提交；
- CI 使用 `uv sync --frozen`；
- 禁止浮动生产依赖；
- pip-audit + Dependabot/Renovate；
- Bandit + secret scan；
- Trivy/Grype 扫镜像；
- Cosign/Sigstore 签名；
- SBOM 包含 Python wheel 和系统包。

### 9.3 运行时

- 非 root；
- read-only rootfs；
- drop all capabilities；
- `allowPrivilegeEscalation=false`；
- framework Adapter 与 Operator 使用不同镜像和 ServiceAccount；
- 禁止把 Agent framework 依赖安装到 Operator image。

---

## 10. 可观测性决策

语言迁移不改指标契约：

- `supteam_operator_*`；
- `supteam_a2a_*`；
- `supteam_adapter_*`；
- `supteam_knowledge_*`；
- `supteam_memory_*`。

Python 特定要求：

- 进程默认单 worker，避免 Prometheus multiprocess mode 复杂性；
- 所有 async background task 捕获异常并记录 trace；
- 增加 event-loop lag、thread-offload queue depth、active tasks；
- OpenTelemetry 使用显式 provider 注入，测试不能污染全局 provider；
- structlog event 必须保留既有 trace/task/agent/workflow/namespace 字段；
- Message/Memory/Knowledge content 永不进入普通日志。

新增 Python runtime 指标不得破坏或重定义既有指标语义。

---

## 11. 测试与质量门禁

### 11.1 静态门禁

```text
uv sync --frozen
ruff format --check .
ruff check .
pyright
bandit -r packages services agents adapters
pip-audit
```

- Pyright 使用 strict；
- public API 禁止未解释的 `Any`；
- Ruff 不能通过全局 ignore 绕过错误；
- type ignore 必须最小范围并附原因；
- 生成代码单独配置，不降低手写代码门禁。

### 11.2 测试门禁

| 层级 | 工具 | 要求 |
|---|---|---|
| Unit | pytest / pytest-asyncio / AnyIO | 核心 ≥80%；算法/类型 ≥90% |
| Property/Fuzz | Hypothesis | Schema、FSM、decay/reinforce、P2C |
| HTTP | respx / ASGI test client | timeout/retry/error/mTLS boundary |
| Operator IT | kind + fake/mock client | real watch/reconcile/webhook/leader failover |
| Conformance | 上游 A2A suite | 标准 method 100% |
| E2E | kind + Helm | Hello/Workflow/Knowledge/Memory 全链路 |
| Performance | pytest-benchmark / Locust | p50/p95/p99 + event-loop lag |

Python 没有 envtest 的完全等价替代。单元测试使用 fake/mock，关键 Controller 集成测试必须上 kind，不能把 mock 测试标记为“真实 reconcile”。

---

## 12. 性能边界

### 12.1 不预先降低 SLO

现有设计中的延迟/吞吐目标先作为迁移基线保留。Python benchmark 完成前，不得以主观判断放宽。

至少测量：

- 1 KiB A2A loopback p50/p95/p99；
- Pydantic params/result validation；
- Agent Card cache hit/miss；
- EndpointSlice watch invalidation；
- retry/circuit/P2C hot path；
- 10K KnowledgeItem rebuild/query；
- Memory batch decay；
- reconcile throughput；
- event-loop lag；
- RSS/CPU per Pod。

### 12.2 触发升级决策

若 Python 无法满足 SLO：

1. 先 profile；
2. 减少不必要分配/重复校验；
3. 使用连接池、cache、batch 和受控 thread offload；
4. 通过 Pod 水平扩容验证；
5. 仍不满足时提交 ADR，讨论原生扩展或局部服务替代。

禁止未经 ADR 静默加入 Go sidecar，避免重新产生双语言核心。

---

## 13. 工程布局

L3 通过后采用 `uv` workspace：

```text
pyproject.toml
uv.lock
packages/
  a2a-core/src/superteam_a2a/a2a/
  operator/src/superteam_a2a/operator/
  adapter-sdk/src/superteam_a2a/adapter/
services/
  knowledge-service/src/superteam_a2a/knowledge/
  memory-backend/src/superteam_a2a/memory/
agents/
  hello/src/superteam_a2a/hello/
adapters/
  langchain/
  autogen/
  crewai/
  semantic-kernel/
  strands/
  smolagents/
tests/
  integration/
  conformance/
  e2e/
```

- 根配置统一质量工具；
- package 各自声明最小运行依赖；
- framework 依赖仅存在于对应 Adapter package/image；
- Operator/A2A Core 不依赖任何 Agent framework；
- console script 作为进程入口；
- 不使用隐式 `PYTHONPATH`；
- lockfile 是可重复构建的一部分。

---

## 14. 文档迁移门禁

### 14.1 顺序

1. ADR-0005 Accepted；
2. 宪法 v0.5.0；
3. L1 Architecture / System Spec v0.2 + review；
4. L2-1~L2-4 Python v0.2 + 每模块 review；
5. 归档 Go L3 draft；
6. 重写 Python L3-1/L3-2；
7. 编写 Python L3-3~L3-6；
8. L3 统一 review；
9. 初始化 Python workspace；
10. L4 实现。

### 14.2 历史处理

- Accepted ADR 和旧 review 是历史记录，不改写成“当时已经评审 Python”；
- 旧 ADR 仅加 supersede 指针；
- L1/L2 权威文档在原路径升 v0.2，保留 changelog；
- L3 Go 文档未评审，但项目当前无 `.git` 历史，因此复制到 `docs/archive/pre-python-2026-07-24/` 后再重写原路径；
- archive 不作为现行实现输入。

### 14.3 一致性扫描

迁移完成后，除 archive、历史 review、ADR supersede 说明外，现行 v0.2 文档不得把以下内容作为实现选择：

- Go 1.22；
- `.go` 文件树；
- kubebuilder；
- controller-runtime；
- client-go；
- envtest；
- godoc；
- go vet / golangci-lint。

历史比较文字可以出现，但必须明确标记为 superseded/history。

---

## 15. 后果（Consequences）

### 15.1 正面

- ✅ 平台语言与主流 Agent 框架生态一致；
- ✅ 官方 A2A Python SDK 可复用，减少协议自研面；
- ✅ 单人维护减少语言切换；
- ✅ Pydantic 提供 runtime validation + JSON Schema；
- ✅ async I/O 适合 A2A、K8s watch、webhook 和 Discovery；
- ✅ Adapter 开发门槛降低；
- ✅ 当前无生产代码，迁移没有运行时兼容成本；
- ✅ 通过 ADR 和重新评审避免隐性技术债。

### 15.2 负面

- ⚠️ 已完成 L1/L2/L3 文档需要系统性重写；
- ⚠️ Kopf 与 controller-runtime 的成熟模式不一一对应；
- ⚠️ Python GIL/单进程状态要求更严格；
- ⚠️ K8s Python async 生态不像 client-go 一样官方统一；
- ⚠️ mTLS/SPIFFE 热更新需要额外验证；
- ⚠️ 缺少 envtest 等价物，真实 Operator IT 更依赖 kind；
- ⚠️ Python dependency/supply-chain 面更大；
- ⚠️ 性能上限需要基准测试证明。

### 15.3 工作量影响

本 ADR 不改变 ADR-0004 的功能范围，但设计重写会延迟 L4 开始。时间线需要在 L1 v0.2 review 时重新估算；不得在没有新估算的情况下继续沿用 2027-01-20 作为无风险承诺。

---

## 16. 备选方案（Alternatives）

### A. 全栈 Python（采纳）

如本 ADR。符合用户明确选择，且当前未编码，是迁移成本最低的时间点。

### B. Go Operator + Python 数据面（未采纳）

保留 Operator/controller-runtime，A2A/Adapter/Knowledge/Memory 使用 Python。

**未采纳理由**：

- 不符合用户“全栈 Python”选择；
- 单人维护持续承担双语言工具链；
- 类型/Schema 在 Go/Python 间重复；
- Adapter 与 Operator 调试上下文分裂。

### C. 仅 Adapter/Agent 使用 Python（未采纳）

保留现有 Go L1/L2/L3，只写 Python Adapter。

**未采纳理由**：只能称“Python Agent 生态接入”，不能称平台 Python 技术栈；A2A Core 和 Knowledge/Memory 仍需跨语言维护。

### D. 自研 Python A2A 实现（未采纳）

把现有 Go A2A Spec 逐行翻译为 Python，不使用官方 SDK。

**未采纳理由**：

- 与“跟随上游”目标冲突；
- 重复实现标准类型和 conformance；
- 协议演进维护成本过高；
- 项目差异化不在重新发明 A2A SDK。

### E. 立即开始 Python 编码、后补文档（未采纳）

**未采纳理由**：直接违反宪法 §14.4 和 §15.4。

---

## 17. 回滚与退出策略

### 17.1 L4 前回滚

若在 L1/L2/L3 阶段发现 Python 方案无法满足关键约束：

- 本 ADR 标记 Superseded；
- 新 ADR 记录回到 Go 或混合栈的原因与证据；
- Go L3 archive 可作为恢复输入；
- 现行 Python 文档保留历史，不静默删除。

### 17.2 L4 后回滚

进入实现后不得“大爆炸回滚”。必须：

1. 按模块测量问题；
2. 优先优化 Python；
3. 用 A2A/HTTP 边界隔离需要替换的模块；
4. 保持 CRD/wire compatibility；
5. 分阶段双跑与 E2E；
6. 经 ADR 后切换。

### 17.3 不可接受的退出方式

- 不记录就加入 Go 二进制；
- 因单个性能测试失败重写全项目；
- 降低安全/测试/可观测性换取性能；
- fork 官方 A2A SDK 长期维护；
- 在 Operator 中引入 Agent framework 依赖。

---

## 18. 实施清单

### Phase A：决策与宪法

- [x] 用户选择全栈 Python；
- [x] ADR-0005 Accepted；
- [ ] ADR-0001~0004 添加 implementation superseded 指针；
- [ ] 宪法 v0.5.0；
- [ ] 宪法 changelog 同步。

### Phase B：L1

- [ ] L1 Architecture v0.2-draft；
- [ ] L1 System Spec v0.2-draft；
- [ ] Python stack compatibility review；
- [ ] L1 v0.2.0 批准。

### Phase C：L2

- [ ] L2-1 A2A Python 设计/Spec/review；
- [ ] L2-2 Operator Python 设计/Spec/review；
- [ ] L2-3 Adapter Python 设计/Spec/review；
- [ ] L2-4 Knowledge/Memory Python 设计/Spec/review。

### Phase D：L3

- [ ] 归档 L3-1/L3-2 Go draft；
- [ ] 重写 Python L3-1/L3-2；
- [ ] 完成 Python L3-3~L3-6；
- [ ] L3 统一 review。

### Phase E：L4

- [ ] 初始化 uv workspace；
- [ ] 锁依赖；
- [ ] 类型/schema contract first；
- [ ] Operator/A2A/Adapter/Knowledge/Memory 实现；
- [ ] kind/conformance/E2E；
- [ ] benchmark；
- [ ] release readiness review。

---

## 19. 参考（References）

- [Official A2A Python SDK](https://github.com/google-a2a/a2a-python)
- [A2A Protocol](https://github.com/google-a2a/A2A)
- [Kopf — Kubernetes Operators Framework](https://kopf.readthedocs.io/en/latest/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [`kubernetes_asyncio`](https://github.com/tomplus/kubernetes_asyncio)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Prometheus Python Client](https://prometheus.github.io/client_python/)
- [uv](https://docs.astral.sh/uv/)
- [Python 3.12](https://docs.python.org/3.12/)
- [Kubernetes Operator Pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [CONSTITUTION.md](../../CONSTITUTION.md) §14 / §15 / §16

---

## 20. 签署

本 ADR 由项目发起人于 **2026-07-24** 批准生效（依据宪法 14.5 MVP 例外，单点评审）。

批准语义：平台自有代码采用全栈 Python；任何核心模块偏离 Python、任何公共契约降级、任何未记录的双语言引入，都必须重新走 ADR。
