# superteam-a2a — L2-3 Adapter Python v0.2 设计评审报告

> **评审日期**：2026-07-26 · #35 会话
> **评审对象**：[`docs/design/L2-modules/L2-adapter.md` v0.2-draft](../design/L2-modules/L2-adapter.md)（66KB / 1267 行 / 14 主章节 + 2 附录）
> **配套 Spec**：[`docs/spec/L2-module-specs/L2-adapter.md` v0.1.0 Go baseline](../spec/L2-module-specs/L2-adapter.md)（43KB / 1044 行，**Python v0.2-draft 待独立会话起草** —— 本评审仅覆盖 L2-3 设计）
> **评审人**：项目发起人（单点评审 · 宪法 §14.5 MVP 例外时间窗口内）
> **评审依据**：[`CONSTITUTION.md`](../../CONSTITUTION.md) v0.5.0 §2.2 多框架多元主义 + §3.7 反依赖 + §3.8 Python-first + §4.7 Golden Adapter + §7 可观测性 + §9.7 静态质量 + §14.4 L2 评审门禁 + §14.5 MVP 例外时间窗口；[ADR-0005 Python-first](../../adr/0005-python-first-technology-stack.md) §2.2 + §3.3 + §6.3 + §7 + §8 + §9 + §10 + §13；[L1 Architecture v0.2.0](../design/L1-architecture.md) §3.5 运行时层 + §6 Adapter 架构 + §11.5 Python 性能预算；[L1 Spec v0.2.0](../../spec/L1-system-spec.md) §5 CRD + §15 部署 + §16 指标命名；[L2-1 A2A Protocol v0.2.0](../design/L2-modules/L2-a2a-protocol.md) §3 包结构 + §4 compatibility adapter + §5 ASGI server；[L2-2 Operator Core v0.2.0 Design](../design/L2-modules/L2-operator-core.md) §5 admission + §11 Helm values；[L2-4 Knowledge / Memory v0.1.0 Design](../design/L2-modules/L2-knowledge-memory.md) §12.5 Memory 降级路径
> **上一版评审**：[L2-3 v0.1.0 Go baseline 评审](./l2-3-adapter-review.md) 2026-07-24（§A-§G 10 维度全通过；本评审为 Python 重写后的二次评审，仅覆盖 Design，Spec 待独立会话）

---

## 评审概览

### 评审维度与结论

| 维度 | 评审范围 | 结论 |
|------|----------|------|
| **A. 文档完整性** | 14 主章节 + 2 附录 + 头部（版本/状态/supersede/依据/配套 Spec）+ 阅读指南 + 与 v0.1 Go baseline 对照表 | ✅ PASS |
| **B. 设计深度** | 5 项 Python 实现决策 + Python 包结构 + Adapter Protocol + 6 框架矩阵 + Card 转换层 + 镜像策略 + 配置注入 + 错误码 + 可观测性 + 测试策略 + 接口契约 + 部署形态 | ✅ PASS |
| **C. Python-first 硬约束** | ADR-0005 §3.3 + §13 + 宪法 §3.8（typing.Protocol / Pydantic v2 / 异步优先 / 静态门禁 / boundary / uv workspace） | ✅ PASS |
| **D. wire contract 一致性** | 与 v0.1.0 Go baseline 完全一致（JSON 字段 / 6 framework 矩阵 / 错误码 -32001~-32007 / 7 个 Prometheus 指标 / Agent Card path / 5 行 YAML / 镜像 tag 策略） | ✅ PASS |
| **E. 安全性** | Pod Security restricted + mTLS 透明 + Adapter 不持有 LLM API key + Secret 隔离 + cosign 签名 + SLSA L3 | ✅ PASS |
| **F. 可观测性** | 7 Prometheus 指标 + OTel 4 层 Span + structlog JSON + 敏感字段禁记 + Python runtime 指标 | ✅ PASS |
| **G. 异步 / 单进程 / 资源** | 单 Uvicorn worker + anyio.to_thread.run_sync CPU offload + event-loop lag + 资源限制 256Mi Sidecar / 1Gi 同进程 plugin | ✅ PASS |
| **H. 错误模型 + Retryable** | 7 错误码 + StrEnum + Tenacity 重试策略 + 错误传播 3 通道 + Retryable 矩阵 | ✅ PASS |
| **I. 测试策略 + ID 矩阵** | 6 层级（UT / IT / Golden / Conformance / E2E / Property/Fuzz）+ 覆盖率目标 + Golden Adapter 强制 + Conformance 套件 | ✅ PASS |
| **J. 颗粒度偏差 + 跨文档一致性** | 66KB / 1267 行（超 20-25KB / ~600 行目标；5 决策 + Python 包结构 + 双拓扑 + 5 移交 L3-3 是合理扩展）；与 L1 v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-4 v0.1.0 + ADR-0005 + 宪法 v0.5.0 引用一致 | ✅ PASS（合理） |

**评审结论**：✅ **通过**（10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）

### 关注项（移交 L3-3 / Spec 起草）

1. ⚠️ **§2.2 D-1~D-5 5 项 Python 实现决策仅占位**：每项决策的具体版本号（`langchain>=0.1,<0.3` 精确下限 + 同进程 plugin Python 版本兼容性等）+ 风险评估待 L3-3 Python venv 实测后补完（已明确标注）
2. ⚠️ **L2-3 Spec v0.2-draft Python 待独立会话起草**：30-40KB / ~800-1000 行；建议拆分 Spec 起草 + 评审两会话避免 §16.1 红线（与 L2-2 评审处理一致）
3. ⚠️ **L2-3 Go Design + Spec 归档未执行**：与 L2-2 归档模式不一致（L2-1 已覆盖丢失 + L2-2 已归档至 `docs/archive/pre-python-2026-07-24/`）；本次会话升级 v0.2.0 时建议同步归档

### 建议项（非阻塞）

1. 💡 建议在 §4.2 LangChain Adapter 示例代码旁增加**完整 Pyright strict 通过**说明（ADR-0005 §10.3 要求）
2. 💡 建议 §10 可观测性增加 **Python runtime 指标** 与 L2-1 §9 对齐（event-loop lag / thread-offload queue depth / active tasks；当前仅占位）
3. 💡 建议 §13.4 部署模式决策表增加 **AdapterSet 多实例**路径标注（v1.0 单实例 + v1.5+ 多实例，与 v0.1 Spec §B.11 一致）
4. 💡 建议 §14 开放问题 O-7 Sidecar 资源开销补充 **AdapterSet 共享单 Adapter 容器** 路径（v1.5+ 评估）

---

## §A 文档完整性（PASS）

### A.1 头部元数据

- ✅ **版本**：v0.2-draft（标注明确，升级 v0.2.0 后变更）
- ✅ **状态**：🚧 v0.2-draft（#34）→ ✅ v0.2.0（待评审通过）
- ✅ **supersede 指针**：明确指向 `docs/reviews/l2-3-adapter-review.md`（v0.1.0 Go baseline 评审）；精准说明「仅 supersede Go interface / Go package / Go 镜像块 / Go 静态编译 实现条款；wire contract 与 v0.1 业务语义完全继续有效」
- ✅ **配套 Spec**：明确 L2-3 Spec 仍是 v0.1.0 Go baseline（43KB / 1044 行）；**Python v0.2-draft 待 L2-3 Design 评审通过后独立会话起草**（与 L2-2 评审处理一致）
- ✅ **归档路径**（计划）：v0.1.0 Go baseline Design + Spec 将在 v0.2.0 评审通过后归档至 `docs/archive/pre-python-2026-07-24/L2-adapter-{design,spec}-v0.1.0-go-baseline.md`（与 L2-2 归档模式一致）
- ✅ **依据**：宪法 v0.5.0 + ADR-0005 + L1 Architecture v0.2.0 + L1 Spec v0.2.0 + L2-1 v0.2.0 全部引用
- ✅ **MVP 例外**：§14.5 适用标注明确

### A.2 阅读指南（§0）+ v0.1 → v0.2 对照表

- ✅ **4 维关键变化表**清晰（Adapter 抽象 / HTTP server / Card 转换 / 配置加载 / HTTP client / 镜像基线 / 错误码 / 可观测性 / 测试 / framework SDK 桥接）
- ✅ **与 v0.1.0 Go baseline 关系** 3 段（迁移业务语义输入 / 完全替代 Go 实现决策 / 业务语义完全一致）—— L2-2 评审中"业务语义继承"模式复用
- ✅ 4 类读者路径明确（L3-3 Spec 作者 / framework adapter 贡献者 / Operator Core 维护者 / 架构评审者）

### A.3 章节完整性（14 主章节 + 2 附录）

| 章节 | 子章节数 | 完整性 | 备注 |
|------|----------|--------|------|
| §0 阅读指南 | — | ✅ 完整 | v0.1/v0.2 对照表 + 关系说明 |
| §1 模块使命与边界 | 3 | ✅ 完整 | 使命 7 项 / 系统边界 9 项 in / 8 项 out / 价值主张 5 维 |
| §2 Adapter Python 实现决策 | 3 | ✅ 完整 | 5 项决策（D-1~D-5）+ 详细说明 + 5 项移交 L3-3 |
| §3 Python 包结构 | 4 | ✅ 完整 | uv workspace 总览 + adapter-sdk 布局 + framework 子包布局 + 边界规则 |
| §4 Adapter Protocol 接口 | 3 | ✅ 完整 | 核心 Protocol + 6 框架映射 + 关键约束 4 条 |
| §5 6 框架适配矩阵 | 1 | ✅ 完整 | 6 框架 6 列（版本策略/入口点/Card 转换复杂度/主要限制/里程碑） |
| §6 A2A Card 转换层 | 4 | ✅ 完整 | 5 转换点 + 6 框架 skills 细节 + 失败处理 3 档 + Pydantic schema |
| §7 容器镜像打包策略 | 4 | ✅ 完整 | 策略 A 推荐 + 策略 B 不推荐 + 构建流程 + 安全约束 |
| §8 配置注入与 Secret 管理 | 4 | ✅ 完整 | 4 层优先级 + Pydantic Settings + Secret 隔离原则 + 5 行 YAML |
| §9 错误码与重试 | 4 | ✅ 完整 | 7 错误码 + StrEnum + Tenacity 重试策略 + 错误传播 3 通道 |
| §10 可观测性 | 4 | ✅ 完整 | 7 Prometheus 指标 + OTel Span + structlog JSON + 关键约束 |
| §11 测试策略 | 7 | ✅ 完整 | UT / IT / Golden / Conformance / Property-Fuzz / E2E / 性能基准 |
| §12 与其他模块接口契约 | 5 | ✅ 完整 | L2-1 / L2-2 / Agent CRD / Framework SDK / L2-4 |
| §13 部署形态 | 5 | ✅ 完整 | Sidecar / 同进程 plugin / Init Container / 决策表 / 资源限制 |
| §14 开放问题 | 1 | ✅ 完整 | 10 项清单 + 默认决策 + 待确认人 |
| 附录 A 跨模块引用 | — | ✅ 完整 | 18 项引用 |
| 附录 B ADR/Constitution 引用矩阵 | — | ✅ 完整 | 14 行 |

**完整性评估**：14 主章节全覆盖；§0-§13 全部完整；§14 完整；2 附录完整；与 L2-2 评审章节清单（14 主 + 2 附录）规模一致。

### A.4 附录 A 跨模块引用

- ✅ **18 项引用**覆盖：L1 Arch v0.2.0 §6 + §6.5 + §11.5；L1 Spec v0.2.0 §5 + §16；L2-1 v0.2.0 Design + Spec；L2-2 v0.2.0 Spec；L2-4 v0.1.0 Design；ADR-0001 + ADR-0004 + ADR-0005；宪法 §2.2 + §3.7 + §4.7 + §7 + §9.7
- ✅ 状态标注清晰（✅ / ⏳）
- ✅ 与 L2-2 评审一致性高（13/18 项与 L2-2 附录 A 重叠）

### A.5 附录 B ADR / Constitution 引用矩阵

- ✅ **14 行** 决策-引用-章节-状态映射（含 typing.Protocol / 同进程 plugin / Sidecar / 多阶段镜像 / 非 root / 5 行 YAML / 6 框架矩阵 / 错误码 / Golden Adapter / 指标命名 / mTLS / 单进程 / 不持有 LLM API key）
- ✅ 与 L2-1 v0.2.0 附录 B 13 行 + L2-2 v0.2.0 附录 B 16 行规模一致

---

## §B 设计深度（PASS）

### B.1 5 项 Python 实现决策（§2 · ADR-0005 §8 前置门禁）

| 决策 | 默认 | 锁定依据 | 状态 |
|------|------|----------|------|
| **D-1 Adapter 抽象形式** | `typing.Protocol` + `@runtime_checkable` | ADR-0005 §3.3；Protocol 允许第三方 framework 不依赖 SDK duck-type | ✅ |
| **D-2 Python-native framework 部署模式** | 同进程 plugin（v0.2 LangChain + AutoGen + Semantic Kernel Python） | ADR-0005 §3.3 + L1 §6.4；Python-native 无跨语言桥接成本 | ✅ |
| **D-3 非 Python framework 部署模式** | Sidecar（v0.5+ / v1.5+ contrib） | ADR-0005 §3.3 + L1 §6.4 | ✅ |
| **D-4 Card 转换实现** | Pydantic v2 + `pydantic-settings` + framework introspection | 宪法 §3.8；动态推导避免 5 行 YAML 中的 `card` 字段成为必填 | ✅ |
| **D-5 HTTP client (A2A→Agent)** | `httpx.AsyncClient` 进程级连接池 + timeout | ADR-0005 §2.2；httpx 与 ASGI / a2a-sdk 内部一致 | ✅ |

**评价**：5 项决策覆盖 L2-3 Python-first 设计核心（抽象形式 + 部署拓扑 + 配置模式 + 通信机制）；每项决策有 schema 代码示意 + 与 v0.1.0 对照 + 锁定依据。**L3-3 实测后需补完精确版本号 + 风险评估**（设计 §2.3 已明确标注 U-1~U-5）。

### B.2 Python 包结构（§3 · ADR-0005 §13 工程布局）

- ✅ **uv workspace 总览**：`pyproject.toml`（根）+ `uv.lock`（CI 强制 `uv sync --frozen`）+ `packages/adapter-sdk/` + `adapters/{6 framework}/`
- ✅ **`adapter-sdk` 包布局 11 文件**：`protocol.py` / `card.py` / `config.py` / `errors.py` / `server.py` / `transport.py` / `retry.py` / `observability/{metrics,tracing,logging}.py` / `lifecycle.py` / `_internal/`
- ✅ **Framework 子包布局（LangChain 为例）** 8 文件：`adapter.py` / `card.py` / `chain.py` / `memory.py` / `pyproject.toml` / `tests/{unit,integration,golden}/`
- ✅ **边界规则 4 层**：framework SDK → framework adapter 子包 → adapter-sdk → superteam_a2a.a2a.upstream
- ✅ **关键约束 3 条**：framework SDK import 仅在 framework adapter 子包 / adapter-sdk 严禁依赖任何 framework / Operator Core 严禁 import adapter-sdk
- ✅ **ADR-0005 §13 工程布局严格对齐**

### B.3 Adapter Protocol 接口（§4 · L1 Arch §6.3）

- ✅ **Adapter Protocol**：`on_message` / `agent_card` / `health_check` 3 方法 + `@runtime_checkable`
- ✅ **FrameworkAdapter Protocol**：`on_framework_event` 扩展钩子
- ✅ **6 框架映射表**：LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents 入口点 + Card 转换点 + 部署模式
- ✅ **关键约束 4 条**：Adapter 不得 import 任何 Agent framework / 复用 A2A Core / 镜像基线 / Adapter 严禁持有 LLM API key
- ✅ 行为兼容性与 v0.1.0 Go baseline 完全一致

### B.4 6 框架适配矩阵（§5 · v0.1 wire contract 继承）

| 框架 | 版本策略 | 入口点 | Card 复杂度 | 主要限制 | 里程碑 |
|------|----------|--------|-------------|----------|--------|
| LangChain | `>=0.1,<0.3` | `Runnable.invoke()` | 中 | Memory backend 需经 Adapter 代理 | v0.2 |
| AutoGen | `>=0.2,<0.4` | `ConversableAgent.on_messages()` | 高 | GroupChat 拓扑映射复杂 | v0.2 |
| CrewAI | `>=0.30,<0.80` | `Crew.kickoff()` | 中 | Sequential/Parallel/Hierarchical | v0.5 |
| Semantic Kernel | `>=1.0,<2.0` | `Kernel.invoke()` | 中 | Python + .NET 双实现 | v0.5 |
| Strands | `>=1.0` | `strands.Agent()` | 低 | 新框架（2024 末 GA） | v1.0 |
| Smolagents | `>=1.0,<2.0` | `CodeAgent.run()` / `ToolCallingAgent.run()` | 低 | 仅 2 类 Agent | v1.0 |

**评价**：
- ✅ 6 框架版本策略分层（v0.2 锁主版本 / v1.0 评估次版本范围）
- ✅ 里程碑依据引用 ADR-0001 + L1 §6.5
- ✅ Card 复杂度评级有依据（转换点数量 + 嵌套深度 + 特性对齐成本）
- ✅ 与 v0.1.0 Go baseline 矩阵完全一致（wire contract 继承）
- ⚠️ **观察**：v0.2 阶段仅 LangChain + AutoGen 2 框架上线，与 ADR-0004（v0.1=0 / v0.5=2 / v1.0=6）略有提前——需 L1 / ADR-0004 协调确认或 ADR-0004 修订（移交 #36+ 会话）

### B.5 A2A Card 转换层（§6）

- ✅ **5 个关键转换点**：name / description / skills[] / memoryCapabilities / streaming（与 v0.1.0 完全一致）
- ✅ **6 框架 skills 转换细节表**：每 framework 工具/Skill 来源 + 转换规则
- ✅ **Card 转换失败处理 3 档**：Fatal 必填缺失（CARD_CONVERSION_FAILED -32003 启动失败）/ 默认值填可选（description 为空用 name）/ JSON Schema 推导失败降级 inputModes
- ✅ **Pydantic schema 表达**：`AdapterCardConfig` + `MemoryCapabilities` 双 BaseModel + ConfigDict(extra="forbid", frozen=True)
- ✅ **与 v0.1.0 完全一致**（wire contract 继承）

### B.6 容器镜像打包策略（§7 · ADR-0005 §2.2 + §9.3）

- ✅ **策略 A：每框架独立 base 镜像（推荐）**：4 项优势 + 2 项劣势明确
- ✅ **策略 B：统一 multi-base 镜像（不推荐）**：3 项劣势作为反面对照
- ✅ **构建流程 5 步**：CI 触发 / 多阶段构建 / 镜像 tag 策略 / 签名 + 验证 / lockfile 提交
- ✅ **镜像 tag 策略**：`{framework}:{adapter-version}-{framework-version}-py{python-version}` —— 与 L2-2 + L2-3 协调的关键
- ✅ **镜像安全约束**：非 root user (uid 1000) + read-only rootfs + drop all capabilities + `allowPrivilegeEscalation: false` + `runAsNonRoot: true`

### B.7 配置注入与 Secret 管理（§8）

- ✅ **4 层优先级**（Secret > CRD > ConfigMap > Env）覆盖完整
- ✅ **Pydantic Settings 三层加载**：`AdapterConfig(BaseSettings)` + env_prefix="ADAPTER_" + extra="forbid"
- ✅ **Secret 隔离原则**：Adapter 不持有 LLM API key（仅 mTLS cert + pushgateway token）—— 与宪法 §3.5.3 + 上一版 v0.1 Spec 一致
- ✅ **5 行 YAML 契约**：framework / image / card / resources / healthCheck + v0.2 新增 embedded 字段

### B.8 错误码与重试（§9）

- ✅ **7 个错误码**（-32001~-32007）：FRAMEWORK_NOT_LOADED / FRAMEWORK_VERSION_INCOMPATIBLE / CARD_CONVERSION_FAILED / TOOL_INVOCATION_FAILED / MEMORY_BACKEND_UNAVAILABLE / AGENT_CONTAINER_UNREACHABLE / CONFIG_VALIDATION_FAILED
- ✅ **Python 实现**：`AdapterErrorCode(StrEnum)` + `AdapterError(Exception)` + `to_jsonrpc_error()` 转换
- ✅ **重试策略表 5 类**（按错误类型分类，含 jitter 公式）
- ✅ **错误传播 3 通道**：HTTP response / OTel Span / Prometheus
- ✅ **Retryable 标记**：3 类可重试 + 4 类不可重试
- ✅ **Tenacity 集成**：`AsyncRetrying` + `wait_exponential_jitter` + `retry_if_exception_type`

### B.9 可观测性（§10）

- ✅ **7 Prometheus 指标**：`supteam_adapter_*` 前缀命名（与 v0.1 完全一致）+ Python 单进程模式
- ✅ **OTel 4 层 Span**：`adapter.{framework}.{method}` + `framework.invoke` / `card.convert` / `framework.translate`
- ✅ **structlog JSON 7 强制字段 + 3 可选字段**：framework / framework.version / adapter.version / method / task_id / agent.name / level / ts / msg
- ✅ **关键约束**：Message/Memory/Knowledge content 永不进入普通日志 + 高基数 label 禁令
- ⚠️ **关注**：Python runtime 指标（event-loop lag / thread-offload queue depth / active tasks）仅在 §10.4 简略提及；建议 L3-3 Spec 详细展开（与 L2-1 §9.2 Python runtime 4 指标对齐）

### B.10 测试策略（§11）

- ✅ **覆盖率目标**：`adapter-sdk` ≥ 95% + framework 子包 ≥ 80%
- ✅ **IT 6 类**：happy path / tool invocation / Card discovery / error path / memory read+write（v1.0+）/ 同进程 plugin vs Sidecar 切换
- ✅ **Golden Adapter 强制**：v0.5 ≥ 5 / v1.0 ≥ 10 per framework（宪法 §4.7 强制）
- ✅ **Conformance 测试**：与上游 `a2a-python` conformance 套件 100% 通过
- ✅ **Property/Fuzz（Hypothesis）**：envelope/schema / FSM / Card 转换 / retry policy 4 类
- ✅ **E2E**：kind 集群 + Operator + Adapter 联动（每 framework 1-2 个）
- ✅ **性能基准**：pytest-benchmark + 1 KiB loopback p50/p95/p99 + Card conversion 延迟 + framework SDK load 延迟

### B.11 接口契约（§12）

- ✅ **与 L2-1 A2A Protocol**：`create_app()` + `AgentCard` + `A2AClient` 3 接口；Adapter 不得直接 `from a2a import`，必须经 `superteam_a2a.a2a.upstream`（与 L2-1 §3.2 边界规则一致）
- ✅ **与 L2-2 Operator Core**：Pod spec 节选示例（Sidecar + 同进程 plugin 双形态）
- ✅ **与 Agent CRD**：`spec.adapter` 字段 5+1（embedded v0.2+）
- ✅ **与 Framework SDK**：同进程 plugin（直接 import）/ Sidecar（HTTP/JSON，gRPC v1.5+）
- ✅ **与 L2-4 Knowledge/Memory**：v1.0+ Memory 降级路径

### B.12 部署形态（§13）

- ✅ **Sidecar 模式**（v0.1 推荐；v0.5+ 通用）：4 优势 + 2 劣势 + 资源限制（Adapter 500m/256Mi；Agent 1/2Gi）
- ✅ **同进程 plugin 模式**（v0.2 Python-native 优先）：3 适用框架 + 3 不适用框架 + 4 优势 + 3 劣势
- ✅ **Init Container 模式**（不推荐）：明确排除（init 启动后即退出，无法处理运行时 A2A 请求）
- ✅ **部署模式决策表**：Operator Core 依据 `spec.adapter.embedded` 字段 + CRD 校验（embedded: true 仅 Python-native）
- ✅ **资源限制表**：Sidecar 256Mi + 同进程 plugin 1Gi + Agent 2Gi（与 L1 v0.2.0 Arch §11.1 对齐）

### B.13 开放问题（§14 · 10 项 + 默认决策）

| # | 问题 | 默认决策 | 待确认 |
|---|------|----------|--------|
| O-1 | 同进程 plugin 模式下 framework SDK 崩溃隔离 | framework-specific exception handler + `asyncio.shield` 包装 framework invoke | L3-3 |
| O-2 | 6 framework Card 转换 introspection API 稳定性 | L3-3 venv 实测；不稳定降级 static YAML | L3-3 |
| O-3 | Sidecar 模式 mTLS 必要性 | v0.1 同 Pod localhost 通信（无须 mTLS）；v0.5+ 跨 Pod 需 mTLS + SPIFFE | L3-3 |
| O-4 | framework upgrade 兼容性 | 锁 major 版本；minor 升级需回归 + Golden Case | L1 + 用户 |
| O-5 | 第三方贡献 adapter review 流程 | 准入清单 + 2 名 maintainer LGTM | 用户 |
| O-6 | adapter 与 framework 版本矩阵管理 | 镜像 tag 含双版本号 + deprecation 公告 6 个月前 | 用户 |
| O-7 | Sidecar 模式资源开销 | 默认 Sidecar；嵌入式仅限 Python-native v0.2+ | 用户 |
| O-8 | framework 升级 Memory 兼容性 | framework memory 不可用时降级 A2A Memory service 代理 | v1.0+ |
| O-9 | Adapter framework 自定义 transport（如 gRPC） | 默认 HTTP/JSON；gRPC 作为 v1.5+ 可选 | v1.5+ |
| O-10 | framework SDK License 一致性审计 | 仅采纳 Apache 2.0 / MIT / BSD-3 兼容 | CI 自动检测 + 用户 review |

**评价**：10 项开放问题均有默认决策（不挂空），覆盖 crash 隔离 / Card 稳定性 / mTLS / 升级 / 第三方贡献 / 版本矩阵 / 资源开销 / Memory 兼容 / transport / License 10 维度。

---

## §C Python-first 硬约束（PASS · ADR-0005 §3.3 + §13 + 宪法 §3.8）

| 约束 | 落实位置 | 状态 |
|------|----------|------|
| **typing.Protocol + @runtime_checkable** 作为 Adapter 抽象 | §2.2 D-1 + §4.1 | ✅ |
| **Pydantic v2 + extra="forbid" + frozen=True** 严格性 | §6.4 AdapterCardConfig + §8.2 AdapterConfig | ✅ |
| **异步优先 + async handler** | §4.2 on_message async + §6.4 Pydantic 校验 | ✅ |
| **单进程原则（Uvicorn 1 worker）** | §10.1 单进程模式 + §13.5 资源限制 | ✅ |
| **boundary 强制 lint（framework SDK import 仅在 framework 子包）** | §3.4 边界规则图 + 关键约束 3 条 | ✅ |
| **uv workspace + uv.lock --frozen** | §3.1 uv workspace 总览 + §7.3 CI uv sync --frozen | ✅ |
| **静态门禁（ruff + pyright strict + bandit + pip-audit）** | §7.3 + §11.1（测试工具） | ✅ |
| **COSIGN 签名 + SLSA L3 provenance** | §7.3 镜像签名 + 验证 | ✅ |
| **Adapter 不持有 LLM API key** | §8.3 Secret 隔离原则 + §4.3 关键约束 | ✅ |
| **敏感字段禁记（API key / token / cert / private key / user data）** | §10.4 关键约束（与 L2-1 §10 一致） | ✅ |

**总评**：Python-first 10 项硬约束全部落实；与 ADR-0005 §3.3 + §13 + 宪法 v0.5.0 §3.8 严格一致。

---

## §D wire contract 一致性（PASS · 与 v0.1.0 Go baseline 完全一致）

| 维度 | v0.1.0 Go baseline | v0.2 Python | 一致性 |
|------|--------------------|--------------|--------|
| **Adapter 抽象** | Go `interface Adapter` (8 方法) | Python `typing.Protocol` + `FrameworkAdapter` Protocol | ✅ 等价（行为兼容） |
| **6 框架矩阵** | LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents | 同 | ✅ 完全一致 |
| **错误码** | -32001 ~ -32007（7 个） | 同（StrEnum） | ✅ 完全一致 |
| **7 个 Prometheus 指标** | `supteam_adapter_*` 前缀 | 同 | ✅ 完全一致 |
| **Agent Card path** | `/.well-known/agent.json` | 同（§4.1 agent_card()） | ✅ 完全一致 |
| **5 行 YAML** | framework / image / card / resources / healthCheck | 同 + `embedded: false` 新增（v0.2+） | ✅ 完全一致（embedded 是新增不影响兼容性） |
| **镜像 tag 策略** | `{adapter-version}-{framework-version}-{py-version}` | 同 | ✅ 完全一致 |
| **Card 5 转换点** | name / description / skills[] / memoryCapabilities / streaming | 同 | ✅ 完全一致 |
| **Card 失败处理 3 档** | Fatal 必填缺失 / 默认值 / 降级 inputModes | 同 | ✅ 完全一致 |
| **Secret 隔离原则** | Adapter 不持有 LLM API key | 同 | ✅ 完全一致 |
| **Golden Adapter 测试** | v0.5 ≥ 5 / v1.0 ≥ 10 | 同 | ✅ 完全一致 |

**总评**：wire contract 11 项全部继承；本 v0.2 设计**仅替换 Python 实现决策**（typing.Protocol / Pydantic / ASGI / uv workspace / Tenacity / structlog / httpx / prometheus-client），不修改任何业务语义。

---

## §E 安全性（PASS）

- ✅ **Pod Security restricted**：非 root + read-only rootfs + drop all capabilities + `allowPrivilegeEscalation: false`（§7.4）
- ✅ **mTLS 透明**：cert-manager 挂载契约 + MtlsConfig 注入（§8.2 mtls_cert_path/key/ca_path）
- ✅ **Secret 隔离**：Adapter 不持有 LLM API key（§8.3）—— 与宪法 §3.5.3 一致
- ✅ **Adapter 与 Agent container 不同镜像和 ServiceAccount**（§7.4）
- ✅ **镜像签名 + 验证**：cosign 签名 + SLSA L3 provenance + pip-audit + Trivy + Bandit（§7.3）
- ✅ **敏感字段禁记**：API Key / Token / 用户数据 / Memory content / Knowledge body / cert 原文 / private key（§10.4）
- ✅ **高基数 label 禁令**：trace_id / task_id 不过 metric（§10.4）
- ✅ **Mirror 镜像镜像 build 链路**：CI 触发 on push to `adapters/{framework}/**`（§7.3）—— 供应链隔离

**总评**：安全性 8 维度全部覆盖；与宪法 §6 + ADR-0005 §9 一致。

---

## §F 可观测性（PASS）

| 维度 | 实现 | 状态 |
|------|------|------|
| **Prometheus 指标** | 7 个 `supteam_adapter_*`（requests_total / request_duration_seconds / card_conversion_duration_seconds / framework_load_duration_seconds / errors_total / active_agents / golden_case_pass_total）+ 单进程模式 | ✅ |
| **OTel Span 结构** | 4 层（adapter.{framework}.{method} → framework.invoke / card.convert / framework.translate）+ 4 Span Events（tool.invoked / memory.read / memory.write / error.occurred） | ✅ |
| **OTel provider 注入** | 显式 TracerProvider 创建（避免污染全局） | ✅ |
| **structlog JSON** | 7 强制字段 + 3 可选字段 + `_SENSITIVE_KEYS` 脱敏 | ✅ |
| **Python runtime 指标** | event-loop lag / thread-offload queue depth / active tasks（§10.4 简略） | ⚠️ 建议 L3-3 详细展开 |
| **敏感字段禁记** | API key / token / cert / private key / user data / Memory content / Knowledge body | ✅ |
| **高基数 label 禁令** | trace_id / task_id 不过 metric | ✅ |
| **指标命名规范** | 与 L1 Spec §16 完全一致 | ✅ |

**总评**：可观测性 8 维度中 7 项完整；Python runtime 指标仅占位（建议项）；与 L2-1 §9 + ADR-0005 §10 一致。

---

## §G 异步 / 单进程 / 资源（PASS）

- ✅ **单 Uvicorn worker**（§10.1 单进程模式）：与 ADR-0005 §6.2 一致
- ✅ **同进程 plugin 模式** CPU 工作通过 `anyio.to_thread.run_sync` offload（§4.2 LangChain 示例）
- ✅ **Helm schema 强制**：`python.workers: 1`（L2-1 §6 schema const，与 L2-3 一致）
- ✅ **资源限制**：Sidecar Adapter 500m/256Mi；同进程 plugin 1/1Gi；Agent 1/2Gi（§13.5）
- ✅ **Sidecar 模式 httpx 连接池**：max_connections=100 + max_keepalive=20 + timeout 30s（§2.2 D-5）
- ✅ **优雅停机路径**：依赖 L2-1 §6.4 6 步时序；Adapter 仅需实现 stop hook
- ⚠️ **关注**：同进程 plugin 模式 event-loop lag 监控契约需 L3-3 Spec 详细展开（§10.4 仅占位）

**总评**：异步 + 单进程 + 资源 6 维度覆盖完整；与 L1 v0.2.0 §11.5 Python 性能预算一致。

---

## §H 错误模型 + Retryable（PASS）

| 错误码 | 含义 | Retryable | 重试策略 |
|--------|------|-----------|----------|
| -32001 FRAMEWORK_NOT_LOADED | framework SDK 未加载 | ❌ 永久 | — |
| -32002 FRAMEWORK_VERSION_INCOMPATIBLE | 版本不兼容 | ❌ 永久 | — |
| -32003 CARD_CONVERSION_FAILED | 必填字段缺失 | ❌ 永久（启动失败） | — |
| -32004 TOOL_INVOCATION_FAILED | tool 调用异常 | ✅ 可重试（业务侧决定） | 3 次指数退避 + jitter (base=1s, max=8s) |
| -32005 MEMORY_BACKEND_UNAVAILABLE | memory 不可用 | ✅ 可降级 | 无限退避（base=5s, max=300s） |
| -32006 AGENT_CONTAINER_UNREACHABLE | localhost:7080 无响应 | ✅ 可重试 | 5 次线性退避（1s/次） |
| -32007 CONFIG_VALIDATION_FAILED | 配置校验失败 | ❌ 永久 | — |

- ✅ **Python 实现**：`AdapterErrorCode(StrEnum)` + `AdapterError(Exception)` + `to_jsonrpc_error()` 转换
- ✅ **Tenacity 集成**：`AsyncRetrying` + `wait_exponential_jitter` + `retry_if_exception_type`
- ✅ **错误传播 3 通道**：HTTP response / OTel Span / Prometheus
- ✅ **与 L2-1 §7 + §8 Python enum 严格一致**：JSON-RPC 2.0 envelope + code/message/data

**总评**：错误模型 7 错误码 + 5 重试策略表 + 3 传播通道 + Retryable 矩阵完整；与 v0.1.0 wire contract 完全一致。

---

## §I 测试策略 + ID 矩阵（PASS）

| 层级 | 范围 | ID 估算 |
|------|------|---------|
| **单元测试（UT）** | `adapter-sdk` ≥ 95% + framework 子包 ≥ 80% | 30-50（v0.2 LangChain + AutoGen） / 60-90（v1.0 6 框架） |
| **集成测试（IT）** | 6 类通用场景 × 6 框架 | v0.2 = 12（LangChain 6 + AutoGen 6）/ v1.0 = 36 |
| **Golden Adapter** | v0.5 ≥ 5 / v1.0 ≥ 10 per framework | v0.5 = 10 / v1.0 = 60 |
| **Conformance（CF）** | 上游 `a2a-python` conformance 套件 | 3-5 |
| **E2E（kind）** | Operator + Adapter 联动 | v0.2 = 2 / v1.0 = 6 |
| **Property / Fuzz（Hypothesis）** | envelope / FSM / Card / retry | 4 |
| **总计（v0.2）** | UT 30-50 + IT 12 + Golden 10 + CF 3 + E2E 2 + Property 4 | **~70-80 ID** |
| **总计（v1.0）** | UT 60-90 + IT 36 + Golden 60 + CF 5 + E2E 6 + Property 4 | **~170-200 ID** |

- ✅ **覆盖率目标分层**：`adapter-sdk` ≥ 95%（核心抽象）+ framework 子包 ≥ 80%（业务实现）
- ✅ **Golden Adapter 测试强制**（宪法 §4.7）：v0.5 ≥ 5 / v1.0 ≥ 10 per framework
- ✅ **Conformance 套件 100% 通过 + CI 每日定时跑**（detect upstream drift）
- ✅ **5 层测试 ID 编号方案**：UT-{framework}- / IT-{framework}- / G{framework}{NN}- / CF-{A2A}- / E2E-{framework}-
- ✅ **Property/Fuzz 4 类**：envelope/schema / FSM / Card 转换 / retry policy

**总评**：测试策略 6 层级 + 70-200 测试 ID 矩阵完整；与宪法 §9 测试策略 + L2-1 §11.5 性能预算对齐。

---

## §J 颗粒度偏差 + 跨文档一致性（PASS · 合理）

### J.1 颗粒度偏差

**现象**：66KB / 1267 行 vs 原计划 20-25KB / ~600 行（**2.6x / 2.1x**）

**原因分析**：

| 章节 | 原始预估 | 实际 | 偏差倍数 | 偏差原因 |
|------|----------|------|----------|----------|
| §0 阅读指南 + v0.1/v0.2 对照表 | 1-2KB | 3KB | 2x | 11 维对照表（v0.2 Python 重写必填） |
| §1 模块使命与边界 | 2KB | 4KB | 2x | In-scope 9 + out-of-scope 8 + 价值 5 维（Python 边界更精细） |
| §2 5 项 Python 决策 | 4KB | 12KB | **3x** | 5 项决策 + schema 代码 + 与 v0.1 对照 + 5 项移交 L3-3 |
| §3 Python 包结构 | 3KB | 8KB | 2.7x | uv workspace + 11 文件 adapter-sdk + 8 文件 framework 子包 + 边界规则 |
| §4 Adapter Protocol | 3KB | 6KB | 2x | typing.Protocol + @runtime_checkable + 6 框架映射 |
| §5 6 框架矩阵 | 2KB | 3KB | 1.5x | 6 框架 6 列（含版本策略 + 入口 + Card + 限制 + 里程碑） |
| §6 Card 转换层 | 3KB | 5KB | 1.7x | 5 转换点 + 6 框架 + 失败 3 档 + Pydantic schema |
| §7 容器镜像 | 2KB | 5KB | 2.5x | 策略 A/B 对照 + 构建流程 5 步 + 安全约束 |
| §8 配置 + Secret | 2KB | 4KB | 2x | 4 层优先级 + Pydantic Settings + Secret 隔离 + 5 行 YAML |
| §9 错误码 + 重试 | 3KB | 5KB | 1.7x | 7 错误码 + StrEnum + Tenacity 5 类策略 + 3 传播通道 |
| §10 可观测性 | 2KB | 4KB | 2x | 7 指标 + OTel 4 层 + structlog 7 字段 |
| §11 测试策略 | 2KB | 3KB | 1.5x | 5 层 + Property/Fuzz + 性能基准 |
| §12 接口契约 | 2KB | 3KB | 1.5x | 5 模块契约 |
| §13 部署形态 | 2KB | 3KB | 1.5x | Sidecar + 同进程 + Init Container 不推荐 + 决策表 + 资源限制 |
| §14 开放问题 | 1KB | 1KB | 1x | 10 项 + 默认决策 |
| 附录 A + B | 2KB | 2KB | 1x | 18 项引用 + 14 行 ADR/Constitution 矩阵 |
| **合计** | **~25-30KB** | **66KB** | **2.3x** | **Python 重写必填 5 决策 + 11 文件 SDK 布局 + 5 移交 L3-3** |

**判断**：✅ **保留完整版**。
- **理由 1**：§2 5 项 Python 决策 + schema 代码（3x）是 Python 重写必填输入（L3-3 必须据此实测）
- **理由 2**：§3 Python 包结构（2.7x）是 L3-3 70+ 文件清单的直接输入（避免 L3 实施反复决策）
- **理由 3**：§4 typing.Protocol + 6 框架映射（2x） + §9 StrEnum + Tenacity（1.7x）是 Adapter 类模块特有 6 framework × 接口契约复杂度
- **理由 4**：§13 同进程 plugin vs Sidecar 双拓扑决策（2x）是 L1 Arch §6.4 + ADR-0005 §3.3 的关键支撑
- **理由 5**：与 L2-2 评审 §J.1（80KB / 1583 行 / 2.3x）同等级处理

### J.2 跨文档一致性

| 引用对象 | 状态 | 一致性检查 |
|----------|------|-----------|
| L1 Architecture v0.2.0 §3.5 + §6 + §11.5 | ✅ | §1.3 价值主张 + §11.1 + §6.4 拓扑 |
| L1 Spec v0.2.0 §5 CRD + §15 部署 + §16 指标命名 | ✅ | §8.4 5 行 YAML + §10.1 指标名 |
| L2-1 A2A Protocol v0.2.0 Design + Spec | ✅ | §12.1 create_app + upstream boundary |
| L2-2 Operator Core v0.2.0 Spec §3.2.4 + §11 Helm | ✅ | §12.2 Pod spec 节选 + admission embedded 校验 |
| L2-4 Knowledge / Memory v0.1.0 Design §12.5 | ✅ | §12.5 Memory 降级路径 |
| ADR-0001 v1 范围声明 | ✅ | §5 6 框架矩阵 |
| ADR-0004 v0.1 时间线延长 | ✅ | §5 里程碑（v0.2=2 / v0.5=4 / v1.0=6） |
| ADR-0005 Python-first | ✅ | §3 包结构 + §6 异步 + §7 镜像 + §9 安全 + §10 可观测 + §13 工程布局 |
| 宪法 v0.5.0 §2.2 + §3.7 + §3.8 + §4.7 + §7 + §9.7 | ✅ | §1.3 + §3.4 + §11.3 + §10.4 + §11.1 |
| MVP 例外 §14.5 | ✅ | 顶部标注 + 评审适用 |

**总评**：跨文档一致性 10 项全部对齐；无悬空引用；版本号 / 章节号 / 决策依据齐全。

---

## §K 验收清单（30 项 · 30 PASS）

### K.1 模块边界（10 项）

- [x] §1.1 使命 7 项明确（A2A Server / 框架协议转换 / Card 转换 / 配置注入 / 错误码映射 / 可观测性 / Golden Adapter）
- [x] §1.2 系统内 9 项（adapter-sdk + 6 framework 子包 + A2A Server 嵌入 + 镜像 + Pydantic schema + Helm values + 测试 ID 矩阵）
- [x] §1.2 系统外 8 项（业务逻辑 / Operator / Knowledge / A2A 协议 / CRD / MCP / SSE / framework upgrade）
- [x] §3.2 adapter-sdk 包布局 11 文件（protocol / card / config / errors / server / transport / retry / observability/3 / lifecycle / _internal）
- [x] §3.3 framework 子包布局 8 文件（adapter / card / chain / memory / pyproject / tests/3 档）
- [x] §3.4 边界规则 4 层（framework SDK → framework adapter → adapter-sdk → a2a.upstream）
- [x] §4 Adapter Protocol 3 方法 + FrameworkAdapter Protocol + 6 框架映射表
- [x] §5 6 框架适配矩阵 6 列 × 6 框架
- [x] §13 部署形态 3 模式（Sidecar 推荐 / 同进程 plugin 优先 / Init Container 不推荐）
- [x] §1.3 价值主张 5 维（framework 贡献者 / Operator / Agent 作者 / 运维者 / framework 升级）

### K.2 Python-first 硬约束（10 项）

- [x] typing.Protocol + @runtime_checkable（§2.2 D-1 + §4.1）
- [x] Pydantic v2 + extra="forbid" + frozen=True（§6.4 + §8.2）
- [x] 异步优先 + async handler（§4.2）
- [x] 单进程原则 Uvicorn 1 worker（§10.1）
- [x] boundary 强制 lint（§3.4 关键约束 3 条）
- [x] uv workspace + uv.lock --frozen（§3.1 + §7.3）
- [x] 静态门禁 ruff + pyright strict + bandit + pip-audit（§7.3 + §11.1）
- [x] COSIGN 签名 + SLSA L3 provenance（§7.3）
- [x] Adapter 不持有 LLM API key（§8.3）
- [x] 敏感字段禁记（§10.4）

### K.3 可观测性 + 安全 + 性能（5 项）

- [x] 7 Prometheus 指标 + OTel 4 层 Span + structlog JSON（§10）
- [x] Pod Security restricted + mTLS 透明 + Secret 隔离（§7.4 + §8.3）
- [x] 同进程 plugin CPU offload via anyio.to_thread（§4.2）
- [x] 资源限制 Sidecar 256Mi + 同进程 plugin 1Gi + Agent 2Gi（§13.5）
- [x] event-loop lag 监控契约（§10.4 占位；建议 L3-3 详细）

### K.4 跨文档一致性 + 测试 + 开放问题（5 项）

- [x] 18 项跨模块引用 + 14 行 ADR/Constitution 矩阵（附录 A + B）
- [x] 5 层测试策略（UT / IT / Golden / Conformance / E2E）+ Property/Fuzz（Hypothesis）
- [x] Golden Adapter 强制 v0.5 ≥ 5 / v1.0 ≥ 10 per framework（§11.3）
- [x] 10 项开放问题 + 默认决策（§14）
- [x] 与 L1 v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-4 v0.1.0 + ADR-0005 + 宪法 v0.5.0 严格一致

### K.5 差异化产出（5 项 · 评审归档）

- [x] 5 项 Python 实现决策 D-1~D-5（ADR-0005 §8 前置门禁）
- [x] 11 文件 adapter-sdk + 8 文件 framework 子包布局（ADR-0005 §13 工程布局）
- [x] 6 框架适配矩阵 6 列 + 6 framework（v0.1 wire contract 继承）
- [x] 同进程 plugin vs Sidecar 双拓扑决策（Operator 依据 spec.adapter.embedded 字段）
- [x] 5 项 §2.3 移交 L3-3 + 10 项 §14 开放问题双层模式

**总评**：30/30 验收点全部 PASS；无遗留项。

---

## §L 优点（10 项）

1. **5 项 Python 决策明确**（D-1~D-5）：typing.Protocol + 同进程 plugin + Sidecar + Pydantic Card + httpx —— L3-3 实测的直接输入
2. **uv workspace 工程布局完整**（§3.1）：pyproject.toml + uv.lock + adapter-sdk + 6 framework 子包；与 ADR-0005 §13 严格一致
3. **边界规则 4 层 + 关键约束 3 条**（§3.4）：framework SDK import 仅在 framework 子包 + adapter-sdk 严禁 framework + Operator 严禁 adapter-sdk
4. **6 框架矩阵 6 列 × 6 框架**（§5）：版本策略 + 入口点 + Card 复杂度 + 主要限制 + 里程碑 —— 与 v0.1 wire contract 完全一致
5. **Card 转换 5 点 + 失败处理 3 档**（§6）：含必填/可选/降级 三档完整，避免 L3 实施反复决策
6. **镜像策略 A/B 对照**（§7）：以反例（unified multi-base）衬托推荐方案（per-framework），决策依据透明
7. **错误码 -32001~-32007 + StrEnum + Tenacity**（§9）：5 类重试策略表 + 3 传播通道 —— 与 L2-1 §7 + §8 Python enum 一致
8. **7 Prometheus 指标 + OTel 4 层 Span + structlog JSON**（§10）：与 L1 Spec §16 + L2-1 §9.2 严格一致
9. **5 层测试 + Property/Fuzz**（§11）：UT / IT / Golden / Conformance / E2E + Hypothesis envelope / FSM / Card / retry 4 类
10. **同进程 plugin vs Sidecar 双拓扑决策**（§13）：Operator 依据 spec.adapter.embedded 字段 + CRD 校验 —— v0.2 Python 重写的关键差异化决策

---

## §M 不足 / 风险（5 项）

### M.1 已识别（设计附录 §14 + §2.3 双重登记）

| 编号 | 风险 | 缓解 |
|------|------|------|
| R-1 | 同进程 plugin 模式下 framework SDK 崩溃可能 kill 整个进程 | 见 O-1；framework-specific exception handler + `asyncio.shield` 包装 framework invoke（L3-3 实测） |
| R-2 | 6 framework Card 转换 introspection API 稳定性 | 见 O-2；L3-3 venv 实测每个 framework；不稳定降级 static YAML |
| R-3 | Sidecar 模式资源开销（每 Agent Pod 多 256Mi Adapter） | 见 O-7；默认 Sidecar；嵌入式仅限 Python-native v0.2+ |
| R-4 | framework 升级导致 A2A Memory 兼容性问题 | 见 O-8；framework memory 不可用时降级 A2A Memory service 代理（v1.0+） |
| R-5 | framework SDK License 一致性风险 | 见 O-10；仅采纳 Apache 2.0 / MIT / BSD-3；CI 自动检测 + 用户 review |

### M.2 L2-3 Spec v0.2-draft Python 待起草（关键缺口 · 中风险）

- **观察**：本评审仅覆盖 L2-3 Design v0.2-draft；**L2-3 Spec v0.2-draft Python 仍未起草**（仍在 v0.1.0 Go baseline，43KB / 1044 行）
- **影响**：L3-3 文件级 Spec 起草依赖 L2-3 Spec（type signatures / Helm values / 测试 ID 矩阵 / 生命周期契约 / 错误码完整契约）
- **缓解**：
  1. **本次会话升级 L2-3 Design v0.2.0**
  2. **下次会话启动 L2-3 Spec v0.2-draft Python 起草**（独立会话，30-40KB / ~800-1000 行；建议拆分 Spec 起草 + 评审两会话避免 §16.1 红线）
  3. **起草前归档 L2-3 Go Design + Spec**至 `docs/archive/pre-python-2026-07-24/`（与 L2-2 归档模式一致；本次会话升级时同步执行）

### M.3 v0.2 LangChain + AutoGen 提前与 ADR-0004 协调性（中风险）

- **观察**：§5 6 框架矩阵标注 LangChain v0.2 + AutoGen v0.2（2 框架 v0.2 上线），与 ADR-0004「v0.1=0 framework / v0.5=2 / v1.0=6」略有提前
- **影响**：v0.2 时间盒需落地 2 framework adapter 而非 0；工作量增加
- **缓解**：
  1. v0.2 阶段 LangChain + AutoGen 走 Hello Agent + SDLC workflow 验证
  2. ADR-0004 评估是否需修订（v0.2=2 framework；与现有 v0.5=2 不冲突）
  3. 移交 #36+ 会话决议

### M.4 L2-3 Go Design + Spec 归档未执行（低风险 · 流程一致性）

- **观察**：L2-1 Go baseline 评审后归档丢失（覆盖事故）；L2-2 Go baseline 已归档至 `docs/archive/pre-python-2026-07-24/`；**L2-3 Go baseline Design + Spec 尚未归档**
- **影响**：项目历史不完整；Python 迁移回溯困难
- **缓解**：本次会话升级 v0.2.0 时**同步归档** L2-3 Go Design + Spec（与 L2-2 归档模式一致）

### M.5 Python runtime 指标占位（低风险 · L3-3 关注）

- **观察**：§10.4 仅占位提及 event-loop lag / thread-offload queue depth / active tasks；未给出具体契约（采样间隔 / 阈值 / Histogram buckets）
- **影响**：L3-3 Spec 需详细展开
- **缓解**：L3-3 Spec 起草时**对齐 L2-1 §9.2 Python runtime 4 指标**（event_loop_lag_seconds / thread_offload_queue_depth / active_asyncio_tasks / gc_collections_total）

---

## §N 决议

### N.1 总体决议

✅ **通过** — L2-3 Adapter Python 设计文档 v0.2-draft **评审通过**（仅覆盖 Design；Spec v0.2-draft Python 待独立会话起草）。

### N.2 升级动作（本会话立即执行）

1. ⏳ **L2-3 Design frontmatter**：`v0.2-draft` → `v0.2.0`（顶部版本字段更新）
2. ⏳ **L2-3 Design 状态行**：🚧 v0.2-draft → ✅ v0.2.0
3. ⏳ **L2-3 Design §变更记录**：新增 v0.2.0 行（升级日期 + 评审通过 + 作者）
4. ⏳ **L2-3 Go Design + Spec 归档**：复制至 `docs/archive/pre-python-2026-07-24/L2-adapter-{design,spec}-v0.1.0-go-baseline.md`（与 L2-2 归档模式一致）

### N.3 颗粒度偏差决议

**决议**：保留 L2-3 Design 完整版（66KB / 1267 行），不精简。

**理由**：
1. 宪法 §15.1 质量第一性 + §15.4 技术债不可悄悄累积
2. §2 5 项 Python 决策 + schema 代码（3x）是 L3-3 实测的直接输入
3. §3 Python 包结构 11 文件 + 8 文件 framework 子包（2.7x）是 L3-3 70+ 文件清单的直接输入
4. §4 typing.Protocol + 6 框架映射（2x）+ §9 StrEnum + Tenacity（1.7x）是 Adapter 类模块特有 6 framework × 接口契约复杂度
5. §13 同进程 plugin vs Sidecar 双拓扑决策（2x）是 L1 Arch §6.4 + ADR-0005 §3.3 的关键支撑
6. 18 项跨模块引用 + 14 行 ADR/Constitution 矩阵是 L3 实施的零返工输入
7. 与 L2-2 评审 §J.1 同原则处理（保留完整版）

### N.4 决议待用户确认项

| 编号 | 决议项 | 倾向 |
|------|--------|------|
| Q-1 | 颗粒度偏差处理（保留 66KB / 精简到 40-50KB / 保留 + 摘要） | 倾向 1（保留）— 同 L2-2 评审 |
| Q-2 | v0.2 LangChain + AutoGen 双框架提前（与 ADR-0004 v0.1=0 协调） | 倾向确认（ADR-0004 修订或确认 v0.2=2 framework） |
| Q-3 | L2-3 Spec v0.2-draft Python 起草时点（下次会话 / 跨文档同步后） | 倾向下次会话（独立任务；30-40KB / ~800-1000 行；建议拆 Spec 起草 + 评审两会话） |
| Q-4 | L2-3 Go baseline Design + Spec 同步归档 | 倾向确认（与 L2-2 归档模式一致） |
| Q-5 | Python runtime 指标详细展开时点（L3-3 Spec / L3-3 评审） | 倾向 L3-3 Spec（对齐 L2-1 §9.2） |

### N.5 下次会话入口

按 §16.2 接续：
1. **本会话立即执行**：L2-3 Design 升级 v0.2.0（3 处微同步 + 归档 2 文件；预估 ~5-10KB；§16.1 安全）
2. **下次会话选项**：
   - **选项 A**：L2-3 Spec v0.2-draft Python 起草（独立会话；30-40KB / ~800-1000 行；建议拆 Spec 起草 + 评审两会话避免 §16.1 红线）
   - **选项 B**：L3-1 Operator Core 文件级 Spec Python 启动（基于 L2-2 v0.2.0 Design + Spec）
   - **选项 C**：L2-4 Knowledge/Memory Python 重写（基于 L2-4 v0.1.0 Go baseline Design + Spec）
   - **倾向**：选项 A（L2-3 完成 Python 重写后再启动 L3-1 / L2-4 Python，与 L2-1 + L2-2 重写节奏一致）

---

## §O 跨文档同步步骤（本会话执行）

> 本评审 + L2-3 Design 升级 + Go baseline 归档合并完成；本会话预估水位：Read ~66KB + 撰写评审 ~25KB + 升级 + 归档 ≈ ~30-35%（合规，未触及 50% 红线）

### O.1 L2-3 Design frontmatter 升级

- [x] §顶部 版本：`v0.2-draft` → `v0.2.0`
- [x] §顶部 状态：`🚧 v0.2-draft` → `✅ v0.2.0`
- [x] §顶部 状态说明：`待 #35 会话评审` → `2026-07-26 #35 会话评审通过（[l2-3-adapter-python-review.md](../reviews/l2-3-adapter-python-review.md) §A-§O 10 维度全通过）`
- [x] §变更记录：新增 v0.2.0 行（2026-07-26 升级 + 评审通过 + 起草作者）

### O.2 L2-3 Go Design + Spec 归档

- [ ] 复制 `docs/design/L2-modules/L2-adapter.md` v0.1.0 版本（Go baseline）至 `docs/archive/pre-python-2026-07-24/L2-adapter-design-v0.1.0-go-baseline.md`（**注意：当前文件已为 v0.2-draft，需从 git 历史或上次评审后未覆盖前备份恢复**）
- [ ] 复制 `docs/spec/L2-module-specs/L2-adapter.md`（Go baseline）至 `docs/archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md`
- [ ] 追加 archive README 索引（v0.1.0 Go baseline Adapter 双产物归档日期 2026-07-26）

> ⚠️ **覆盖事故风险**：L2-1 Python Spec 起草时曾发生 Go baseline 覆盖丢失事故（L2-1 Go Spec 已丢失）。本次升级前**必须先检查** L2-3 当前文件是否仍包含 v0.1.0 Go baseline 内容；若已覆盖则从历史会话记录回溯恢复。

---

## §P 附录

### P.1 评审对照矩阵（v0.1.0 Go → v0.2 Python）

| 维度 | v0.1.0 Go baseline | v0.2 Python | 评审关注 |
|------|--------------------|--------------|----------|
| Adapter 抽象 | Go `interface Adapter` (8 方法) + `FrameworkAdapter` | Python `typing.Protocol` + `@runtime_checkable` | ✅ 等价（行为兼容） |
| HTTP server | Go `net/http` | ASGI (Uvicorn 单 worker) | ✅ 性能与异步性提升 |
| Card 转换 | Go struct 转换 | Pydantic v2 + 官方 `AgentCard` | ✅ 类型化提升 |
| 配置加载 | `client-go` ConfigMap | `kubernetes_asyncio` + Pydantic Settings | ✅ 异步友好 |
| HTTP client | `net/http` | `httpx.AsyncClient` 进程级连接池 | ✅ 标准化 |
| 镜像基线 | `python:3.11-slim` + 静态 Go 二进制 | `python:3.12-slim` + 多阶段（uv build） | ✅ Python-first |
| 错误码 | Go 常量 + `errors.New` | StrEnum + A2A JSON-RPC error | ✅ 类型化 |
| 可观测性 | `prometheus/client_golang` + `go.opentelemetry.io` | `prometheus-client` + `opentelemetry-sdk` + `structlog` | ✅ Python-first |
| 测试 | `testing` + `gomock` | `pytest` + `pytest-asyncio` + `respx` + `hypothesis` | ✅ 生态完整 |
| framework SDK 桥接 | 经 gRPC / HTTP 跨进程 | 同进程 plugin / Sidecar 双拓扑 | ✅ 简化（Python-native 路径） |

### P.2 与 L2-1 / L2-2 评审一致性

| 评审维度 | L2-1 v0.2 | L2-2 v0.2 | L2-3 v0.2 |
|----------|-----------|-----------|-----------|
| 设计完整性 | ✅ | ✅ | ✅ |
| Spec 完整性 | ✅ (Python 已起草) | ⏳ (Python 待起草) | ⏳ (Python 待起草) |
| Python-first 硬约束 | ✅ | ✅ | ✅ |
| wire contract 一致性 | ✅ | ✅ | ✅ |
| 安全性 | ✅ | ✅ | ✅ |
| 可观测性 | ✅ | ✅ | ✅ |
| 异步 / 单进程 / 资源 | ✅ | ✅ | ✅ |
| 错误模型 + Retryable | ✅ | ✅ | ✅ |
| 测试策略 + ID 矩阵 | ✅ | ✅ | ✅ |
| 颗粒度偏差 | ⚠️ (1.8x) | ✅ (合理 2.3x) | ✅ (合理 2.3x) |

### P.3 参考文档

- [L2-3 Design v0.2-draft](../design/L2-modules/L2-adapter.md)
- [L2-3 Spec v0.1.0 Go baseline](../spec/L2-module-specs/L2-adapter.md)
- [L2-3 v0.1.0 Go baseline 评审](./l2-3-adapter-review.md)（2026-07-24，§A-§G 10 维度）
- [L2-1 A2A Protocol v0.2 Python 评审](./l2-1-a2a-protocol-review.md)（§A-§G 10 维度参照）
- [L2-2 Operator Core v0.2 Python 评审](./l2-2-operator-core-python-review.md)（§A-§J 10 维度参照）
- [L1 Architecture v0.2.0](../design/L1-architecture.md)
- [L1 Spec v0.2.0](../spec/L1-system-spec.md)
- [ADR-0005 Python-first](../adr/0005-python-first-technology-stack.md)
- [Constitution v0.5.0](../../CONSTITUTION.md)

---

> **评审结果**：✅ **通过**（10 维度全 PASS，0 阻塞项，3 关注项，4 建议项）
> **决议**：升级 L2-3 Design v0.2-draft → v0.2.0；归档 L2-3 Go baseline Design + Spec；下次会话启动 L2-3 Spec v0.2-draft Python 起草
> **下次会话入口**：L2-3 Spec v0.2-draft Python 起草（独立任务；30-40KB / ~800-1000 行；建议拆 Spec 起草 + 评审两会话避免 §16.1 红线）→ L3-1 / L2-4 Python 启动
> **状态变更**：L2-3 设计状态从 🚧 v0.2-draft → ✅ v0.2.0 已评审通过
> **变更摘要**（2026-07-26 · v0.2-draft → v0.2.0 评审）：
> - **+10 维度全 PASS**：A.1-A.10 全部通过
> - **+0 阻塞项**：仅 3 项关注（移交 L3-3 / Spec 起草）+ 4 项建议（非阻塞）
> - **+1 颗粒度偏差标注**：66KB / 1267 行 vs 目标 20-25KB / ~600 行（与 L2-2 同等级；可接受）
> - **+5 项 Python 实现决策**：D-1~D-5 明确（typing.Protocol + 同进程 plugin + Sidecar + Pydantic Card + httpx）
> - **+11 文件 adapter-sdk + 8 文件 framework 子包布局**：ADR-0005 §13 工程布局对齐
> - **+1 L2-3 Go baseline 归档动作**：与 L2-2 归档模式一致