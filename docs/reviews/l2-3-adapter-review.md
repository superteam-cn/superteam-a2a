# superteam-a2a — L2-3 评审报告

> **评审对象**：
> - [L2-3 Adapter 设计](../design/L2-modules/L2-adapter.md) (v0.1-draft)
> - [L2-3 Adapter Spec](../spec/L2-module-specs/L2-adapter.md) (v0.1-draft)
> **依据**：[CONSTITUTION.md v0.3.0](../../CONSTITUTION.md) 第十四条 + 第十五条；[L1 Architecture v0.1.0](../design/L1-architecture.md) §3.5 / §5.2.1 / §6；[L2-1 A2A Protocol Spec v0.1.0](../spec/L2-module-specs/L2-a2a-protocol.md) §2 / §4；[L2-2 Operator Core Spec v0.1.0](../spec/L2-module-specs/L2-operator-core.md) §2.2.4 / §5；[ADR-0001 v1 范围](../adr/0001-v1-scope-statement.md)；[ADR-0004 v0.1 时间线延长](../adr/0004-v01-scope-extension-knowledge-and-memory.md)
> **评审日期**：2026-07-24
> **评审者**：项目发起人（基于 MVP 例外 14.5 单点评审；L2-1 / L2-2 评审模板 §A-§G + 10 维度）

---

## 评审流程

按宪法 14.3：
1. ✅ **提交**：L2-3 设计 + Spec 文档（双产物，L2-3 设计 v0.1-draft + L2-3 Spec v0.1-draft）
2. 🚧 **评审**：本报告
3. ⏳ **通过后**：进入 L2-4 Knowledge / Memory 设计（按 ADR-0002 / ADR-0003 范围）
4. ⏳ **驳回**：修改后重新提交评审

按 MVP 例外 14.5：
- ✅ 单点评审（单人维护者，与 L2-1 / L2-2 一致）
- ✅ L2-3 与 L2-4 暂不合并（模块数 = 4，保留灵活性）

按宪法 §16.1（第十六条会话纪律）：
- ✅ 本会话预估水位：Read ~75KB + 撰写评审 ~25KB = ~30-40%（合规，未触及 50% 红线）
- ✅ 评审完成后立即停止（不进入 L2-4，下次会话起手 L2-4 设计）

---

## §A 评审维度

| 维度 | 标准 | 结论 |
|------|------|------|
| **A.1 设计完整性** | 6 框架矩阵 + Card 转换层 + 镜像策略 + 错误码 + Golden Adapter 测试 + 配置注入 + 可观测性 | ✅ |
| **A.2 Spec 完整性** | Go Package 布局 + 9 个 Exported API + Helm values + CRD Schema 引用 + 生命周期契约 + 测试用例 | ✅ |
| **A.3 宪法一致性** | §2.2 多框架 / §3.5 协议兼容 / §3.6 MCP 边界 / §3.7 反依赖 / §4.7 Golden Adapter / §6 安全 / §7 可观测 / §9 测试 | ✅ |
| **A.4 依赖方向正确性** | 仅依赖 L2-1 A2A Protocol（含 a2a.Server / a2a.AgentCard）+ L2-2 Operator Core（下游消费）；禁止反向依赖 Operator | ✅ |
| **A.5 框架兼容性测试覆盖** | 每框架 ≥ 5（v0.5）/ ≥ 10（v1.0）Golden Cases + IT 覆盖 + E2E 联动 | ✅ |
| **A.6 安全合规性** | Pod Security Standard restricted + mTLS Secret 隔离（仅协议层）+ Adapter 不持有 LLM API key | ✅ |
| **A.7 资源开销合理性** | Sidecar 256Mi（默认）+ 1Gi（crewa si）/ Strands 等定制 + 同进程嵌入（仅 LangChain v0.5） | ✅ |
| **A.8 升级兼容性策略** | 镜像 tag 双版本号（adapter-version + framework-version + py-version）+ deprecation 6 个月 | ✅ |
| **A.9 文档可发现性** | README + Golden Adapter 指南 + contrib/README.md + Helm chart tests/ | ✅ |
| **A.10 颗粒度偏差** | Spec 43KB / 1044 行 vs 计划 12-18KB / 400-500 行 | ⚠️ 详见 §B.2.6（同 L2-2 偏差但 Adapter 复杂度可比） |

---

## §B 详细评审

### B.1 L2-3 Adapter 设计评估

#### B.1.1 模块边界（§1）

- ✅ **In-Scope 8 项**：6 framework adapter 子包 + A2A Server 嵌入 + Agent Card 转换 + 容器镜像 + 配置注入 + 错误码映射 + 可观测性 + Golden Adapter
- ✅ **Out-of-Scope 8 项明确排除**：Agent 业务逻辑 / Operator 编排 / Knowledge / A2A 协议本身 / CRD 生命周期 / MCP 协议 / SSE Streaming / v0.1 阶段不含任何 framework adapter
- ✅ 与 §3.7 反依赖条款一致（Adapter 在独立容器）

#### B.1.2 L1 中的位置（§2）

- ✅ 5 层架构第 ⑤ 层运行时层定位准确（与 Hello Agent / Knowledge Service 并列）
- ✅ 依赖方向正确（仅向下：L2-1 a2a.Server / a2a.Client / OpenTelemetry / Framework SDK）
- ✅ 上游模块明确（Operator Core 作为创建方 + Agent CRD `spec.adapter`）

#### B.1.3 子模块拆分（§3）

- ✅ 7 个 framework 子包（langchain / langgraph / autogen / crewai / semantic_kernel / strands / smolagents）+ core/ 抽象 + contrib/ 通道
- ✅ 关键设计原则 3 条明确（core/ 无框架依赖 / framework 子包相互隔离 / semantic_kernel 双语言）
- ✅ langgraph/ v1.0 与 langchain/ 兄弟独立子包设计合理（StateGraph 与 LCEL Runnable 是两类抽象）

#### B.1.4 6 框架适配矩阵（§4）

| 框架 | 版本策略 | 入口点 | Card 复杂度 | 主要限制 | 里程碑 |
|------|----------|--------|------------|----------|--------|
| LangChain | `>=0.1,<0.3` | LCEL Runnable.invoke | 中 | Memory backend 需经 Adapter 代理 | v0.5 |
| AutoGen | `>=0.2,<0.4` | ConversableAgent.on_messages | 高 | GroupChat 拓扑映射复杂 | v0.5 |
| CrewAI | `>=0.30,<0.80` | Crew.kickoff | 中 | 3 种任务拓扑需支持 | v1.0 |
| Semantic Kernel | `>=1.0,<2.0` | Kernel.invoke | 中 | Python + .NET 双实现 | v1.0 |
| Strands | `>=1.0` | strands.Agent | 低 | 新框架（2024 末 GA） | v1.0 |
| Smolagents | `>=1.0,<2.0` | CodeAgent / ToolCallingAgent.run | 低 | 仅 2 类 Agent 需支持 | v1.0 |

- ✅ 版本策略分层（v0.5 主版本 / v1.0 可收紧次版本）
- ✅ 里程碑依据引用 ADR-0001 + L1 §6.5
- ✅ Card 复杂度评级有依据（转换点数量 + 嵌套深度 + 特性对齐成本）
- ⚠️ **小问题**：6 框架均为 Python 实现 — Spec §1 提到 Semantic Kernel Python + .NET 双实现，但设计 §3 子模块拆分仅列 Python + .NET 文件（adapter.py + adapter.cs）— **设计层缺双语言导入路径说明**（L3 实施需明确）

#### B.1.5 A2A Card 转换层（§5）

- ✅ 5 个关键转换点（name / description / skills[] / memoryCapabilities / streaming）覆盖完整
- ✅ 每个 framework 的 skills 转换规则表格化
- ✅ Card 转换失败处理三档（Fatal 必填缺失 / 默认值填可选 / 降级 inputModes）
- ⚠️ **`memoryCapabilities` 字段是 v1.0 引入**：与 §4 CRD 字段对齐需要 L1 Spec 同步确认 — 建议在 L3 实施时联动检查

#### B.1.6 容器镜像打包策略（§6）

- ✅ 策略 A（每框架独立镜像，**推荐**）：4 项优势 + 2 项劣势明确
- ✅ 策略 B（统一 multi-base，**不推荐**）：3 项劣势作为反面对照
- ✅ 镜像构建流程 3 阶段（CI 触发 / 多阶段构建 / tag 策略）
- ✅ **镜像 tag 策略**：`{adapter-version}-{framework-version}-py{python-version}` 是 L2-2 + L2-3 协调的关键（Operator 据此选镜像）
- ✅ cosign 签名 + SLSA L3 provenance（与 §3.7 反依赖配套 — Adapter 镜像可信）

#### B.1.7 配置注入与 Secret 管理（§7）

- ✅ 4 层优先级（Secret > CRD > ConfigMap > Env）覆盖完整
- ✅ 注入时机 3 类（启动时 / 每 method 调用 / 重启触发）
- ✅ **Secret 隔离原则**关键决策：Adapter 不持有 LLM API key（仅持 mTLS cert + pushgateway token）— 与 §3.7 反依赖一致

#### B.1.8 错误码与重试（§8）

- ✅ 7 个错误码（-32001 ~ -32007）覆盖 framework / Card / tool / memory / config 全场景
- ✅ 重试策略表 5 类（按错误类型分类，含 jitter 公式）
- ✅ 错误传播 3 通道（HTTP response / OTel Span / Prometheus）— 与 §7 可观测性闭环
- ✅ Retryable 标记（5 类错误码中 2 类可重试，5 类不可重试）— 业务侧可识别

#### B.1.9 可观测性（§9）

- ✅ 7 个 Prometheus 指标（requests_total / duration / card_conversion / framework_load / errors / active_agents / golden_case_pass）
- ✅ OTel Span 命名规范：`adapter.{framework}.{method}`（与 L2-2 `operator.reconcile.{controller}` 命名风格统一）
- ✅ JSON 结构化日志 7 个强制字段 + 3 个可选字段
- ⚠️ **`supteam_adapter_golden_case_pass_total` 指标**：建议在指标名上附加 `golden_case_id` label，避免 cardinality 爆炸 — **L3 实施注意**

#### B.1.10 测试策略（§10）

- ✅ UT 覆盖率目标（`core/` 100% + framework 子包 ≥ 80%）
- ✅ IT 5 类通用场景（happy path / tool / Card / error / memory）
- ✅ Golden Adapter 强制测试（v0.5 ≥ 5 / v1.0 ≥ 10 per framework）
- ✅ Conformance 测试（与 `google-a2a/conformance` 套件 100% 兼容）
- ✅ E2E 测试（每 framework hello + sdlc workflow）

**亮点**：测试策略分层清晰（UT → IT → Golden → Conformance → E2E 五层），与宪法 §9 测试策略严格对齐。

#### B.1.11 接口契约（§11）

- ✅ 与 L2-1 A2A Protocol：Adapter 嵌入 `a2a.Server`（避免重复实现 JSON-RPC）
- ✅ 与 L2-2 Operator Core：Adapter container 作为 Pod sidecar，被 Operator 创建
- ✅ 与 Agent CRD：`spec.adapter` 字段（framework / image / card / resources / healthCheck）
- ⚠️ **Adapter ↔ Framework SDK 接口**：设计 §11.4 提到 gRPC 或 HTTP/JSON，但缺具体接口签名（属 Spec 层范畴，OK）

#### B.1.12 部署形态（§12）

- ✅ Sidecar 模式（**推荐**）：每 Agent Pod 独立 Adapter container，资源独立
- ✅ 同进程嵌入模式（**可选，v0.5 LangChain only**）：cgo + Python C API
- ❌ Init Container 模式（**不推荐**）：明确排除（init 启动后即退出，无法处理运行时 A2A 请求）

#### B.1.13 附录（附录 A + B）

- ✅ 附录 A 跨模块引用清单 12 项（含 L1 / L2-1 / L2-2 / ADR-0001 / ADR-0004 / 宪法条款）
- ✅ 附录 B 开放问题 8 项（B.1-B.8），每项有**默认决策** + **待确认人**

**亮点**：8 项开放问题均有默认决策（不挂空），覆盖多语言 / framework 升级 / 第三方贡献 / 版本矩阵 / 资源开销 / Memory 兼容 / transport / License 8 维度。

**总评**：L2-3 设计在 6 框架适配 + Card 转换 + 镜像策略 + 错误码 + Golden Adapter 测试 5 个核心维度均有完整设计；与 L1 §6（Adapter 路线图）+ ADR-0004（v0.5=2 / v1.0=6 时序）严格一致。

---

### B.2 L2-3 Adapter Spec 评估

#### B.2.1 阅读指南（§0）

- ✅ 与 L2-3 设计的引用关系清晰（设计为本 Spec 的输入）
- ✅ 必读章节（§1 Go Package + §2 API + §3 Helm + §6 Tests）+ 可选章节（§5 生命周期契约）区分明确

#### B.2.2 Go Package 布局（§1）

- ✅ 完整目录树（含 `core/`、`langchain/`、`langgraph/`、`autogen/`、`crewai/`、`semantic_kernel/`、`strands/`、`smolagents/`、`contrib/`、`cmd/`、`deploy/`）
- ✅ **关键约束 3 条**：core/ 无 framework 依赖 / framework 子包禁止相互依赖 / main.go 通过 `--framework=xxx` 标志选择加载
- ✅ Tests 目录单元 / 集成 / Golden 三档（与宪法 §9 测试策略对齐）
- ✅ Deploy 目录分层（helm/ + docker/）+ Dockerfile 6 框架独立模板
- ⚠️ **Python 依赖管理**：`deploy/docker/Dockerfile.adapter.langchain` 等模板需在 L3 实施时落地（含 requirements.txt / pyproject.toml / uv.lock 等）— 当前 Spec 未在 §1 显式展开 Python 依赖清单位置

#### B.2.3 Exported API（§2）— **Adapter 类模块的差异化节**

- ✅ **§2.1 `core.Adapter` interface** — 8 个方法（Framework / Version / ServeHTTP / AgentCard / HealthCheck / Start / Stop / Reload），符合 L1 §6.3
- ✅ **§2.1 扩展 `core.FrameworkAdapter` interface** — OnFrameworkEvent 扩展点（可选实现）
- ✅ **§2.2 `core.AgentCardConverter` interface** + `DefaultCardConverter` 默认实现（反射调用 5 个关键方法）
- ✅ **§2.3 `core.ConfigLoader`** — 三层优先级（Secret > CRD > ConfigMap > Env）+ AdapterConfig 结构
- ✅ **§2.4 `core/errors`** — 7 个错误码常量 + AdapterError 结构 + ToJSONRPCError 序列化
- ✅ **§2.5 `core/retry.go`** — RetryPolicy 6 字段 + DefaultPolicies 3 个策略 + Retry wrapper 函数
- ✅ **§2.6 `core/observability.go`** — Metrics 7 字段 + NewMetrics 注册 + Tracer helper
- ✅ **§2.7 `core/lifecycle.go`** — Lifecycle 3 个方法（Start / Reload / Stop，含 6/4/4 步伪代码）
- ✅ **§2.8 LangChain 框架 adapter 示例** — 完整 Go 类型定义（New + Framework + Version + ServeHTTP + Start + OnFrameworkEvent）
- ✅ **§2.9 `cmd/adapter/main.go`** — flag 解析 + config 加载 + adapter switch + lifecycle 启动 + SIGTERM 等待

**亮点**：
1. **9 个 interface/struct 全展开**：每个都有 Go 代码签名 + 关键实现说明
2. **LangChain adapter 示例完整**：与 §2.1 接口契约一一对应（Framework / Version / ServeHTTP / Start / OnFrameworkEvent），作为 L3 其他 framework adapter 的实现样板
3. **错误码空间对齐**：-32001 ~ -32007 与 L2-1 errors/codes.go JSON-RPC 扩展范围一致
4. **RetryPolicy 数值化**：DefaultPolicies 表 3 行（CodeToolInvocationFailed / CodeMemoryBackendUnavailable / CodeAgentContainerUnreachable），每个策略 6 字段明确（MaxAttempts / BaseDelay / MaxDelay / Factor / JitterRatio / RetryableErrors）

#### B.2.4 Helm values（§3）— **Adapter 类模块的差异化节**

- ✅ **完整 values.yaml（§3.1）**：6 大段（global / adapter / 6 frameworks / observability / rbac / networkPolicy）
- ✅ **6 framework 独立 image override**：
  - `frameworks.langchain.image.repository/tag` + resources
  - `frameworks.autogen.image.repository/tag` + resources
  - `frameworks.crewai.image.repository/tag` + resources（CPU 2 / memory 1Gi，独家独占最高）
  - `frameworks.semantic_kernel.image.repository/tag` + resources
  - `frameworks.strands.image.repository/tag` + resources
  - `frameworks.smolagents.image.repository/tag` + resources
- ✅ **§3.2 env 映射表** 9 行（Helm value → 环境变量）
- ✅ **§3.3 Deployment 模板**：使用 `{{- range $fw, $cfg := .Values.frameworks }}` 遍历 6 framework — **每 framework 一个独立 Deployment**（与设计 §12 一致）
- ✅ **checksum/config annotation**：ConfigMap 变化触发滚动重启
- ✅ **Pod Security Standard：restricted**（runAsNonRoot + runAsUser 65532 + readOnlyRootFilesystem + no privilege escalation + drop ALL capabilities）

**亮点**：
- 6 framework tag 格式 `{adapter-version}-{framework-version}-py{python-version}` 一致（如 `v0.5.0-0.1.5-py3.11`）
- NetworkPolicy 分 ingress（仅 superteam-a2a namespace）+ egress（observability namespace + 443 LLM provider）
- ServiceAccount / Role / RoleBinding / NetworkPolicy 模板齐全（Helm 自动创建 RBAC）

#### B.2.5 CRD Schema 概要（§4）

- ✅ **Agent.spec.adapter 字段**（引用 L1 §5.2.1）：必填（framework / image）+ 可选（card / resources / healthCheck / agentPort / config）
- ✅ **Adapter 选择逻辑伪代码**：Operator Core 在创建 Pod 时根据 `spec.adapter.framework` 选择镜像
- ✅ **ConfigMap 自动生成**：Operator 据 `Agent.spec.adapter.config` 自动生成 ConfigMap

**亮点**：与 L2-2 Operator Core Spec §2.2.4（Owned resources）+ L2-1 Spec §4（AgentCard）跨模块引用清晰。

#### B.2.6 颗粒度偏差评估（重要）⚠️

**现象**：Spec 43KB / 1044 行，超出原计划 12-18KB / 400-500 行（**2.4x**）

**原因分析**：
| 章节 | 原始预估 | 实际 | 偏差倍数 |
|------|----------|------|----------|
| §0 阅读指南 | 1KB | 1KB | 1x |
| §1 布局 | 1KB | 2KB | 2x |
| §2 exported API | 4KB | 18KB | **4.5x** |
| §3 Helm values | 2KB | 8KB | **4x** |
| §4 CRD Schema | 1KB | 2KB | 2x |
| §5 生命周期契约 | 2KB | 6KB | **3x** |
| §6 测试用例 | 3KB | 5KB | 1.7x |
| §7 + 附录 | 1KB | 1KB | 1x |
| **合计** | **15-18KB** | **43KB** | **2.4x** |

**判断**：
- ✅ **可接受**：§2 exported API 4.5x 偏差源于 9 个 interface/struct 完整 Go 代码展开（vs L2-1 1 个 a2a 主包），是 Adapter 类模块**特有的 6 framework × 接口契约复杂度**
- ✅ **可接受**：§3 Helm values 4x 偏差源于 6 framework 独立 image override + 完整 YAML 模板（与 L2-2 单 controller 不同），是 L3 落地的直接输入
- ✅ **可接受**：§5 生命周期契约 3x 偏差源于 5 个 ASCII 时序图（启动 / Card 转换 / Reload / 优雅停机 / 错误恢复），是 Operator Core 集成的关键参考

**当前决议倾向**：**保留完整版**。理由与 L2-1 / L2-2 评审 §F.4 一致 — 宪法 §15.1 质量第一性 + §15.4 技术债不可悄悄累积；L3 实施时返工成本高于文档阅读成本。

#### B.2.7 生命周期契约（§5）— **Adapter 与 Operator 集成的差异化节**

- ✅ **§5.1 启动序列**：11 步时序（Operator Watch → Reconcile → 构造 Pod → 创建 → 容器启动 → main → config 加载 → framework init → Lifecycle.Start → Ready → Status 更新）
- ✅ **§5.2 Card 转换时序**：5 步（Lifecycle.Start → adapter.Start → AgentCard → 反射调用 → 缓存）
- ✅ **§5.3 Reload 序列**：5 步（ConfigMap watch → Lifecycle.Reload → config 重新加载 → validate → adapter.Reload + OTel attributes 更新）
- ✅ **§5.4 优雅停机**：5 步（SIGTERM → 标记 503 → 等 in-flight → adapter.Stop → 关闭 Server）
- ✅ **§5.5 错误恢复**：5 步（Adapter crash → kubelet 重启 → exponentialBackoff → CrashLoopBackOff → Operator Status 更新）

**评分**：⭐⭐⭐⭐⭐（5/5）— §5 是本 Spec 最具 Operator 集成价值的章节，5 个时序图覆盖 Adapter 完整生命周期。**这是 Operator Core 实现 Owned resources（Adapter container）的关键参考**。

#### B.2.8 测试用例骨架（§6）

- ✅ **单元测试 20 ID**：UT-C-001 ~ UT-C-010（core 10 个）+ UT-LC/AG/CR/SK/ST/SM 001/002 各 2 个（framework 10 个，v0.5 优先 P0）+ UT-SM-002 interpreter 额外
- ✅ **集成测试 21 ID**：v0.5 = 10（LangChain 5 + AutoGen 5）+ v1.0 = 11（CrewAI / Semantic Kernel / Strands / Smolagents 各 3 个）
- ✅ **Golden Adapter 测试 50 ID**：v0.5 = 10（GLC + GAG 各 5）+ v1.0 = 40（GCR / GSK / GST / GSM 各 10）
- ✅ **Conformance 测试 3 ID**：CF-A2A-001 / 002 / 003
- ✅ **E2E 测试 6 ID**：每 framework 1 个（E2E-LC / AG / CR / SK / ST / SM）
- ✅ **总计 100 ID**，覆盖宪法 §9 测试策略 80% 覆盖率目标

**亮点**：
- 测试 ID 编号方案清晰（UT-C-/UT-LC-/UT-AG-/IT-LC-/IT-AG-/GLC-/GAG-/GCR-/GSK-/GST-/GSM-/CF-/E2E-）
- 每 ID 含范围 + 描述 + 优先级（P0/P1）
- Golden Case fixture 路径明确（`tests/golden/{framework}/case-{NN}-{name}.yaml`）

#### B.2.9 变更记录 + 附录（§7 + 附录 A/B）

- ✅ **变更记录表 1 行**（v0.1-draft + 7 节 + 2 附录规格）
- ✅ **附录 A 跨模块引用清单 12 项**：覆盖 L2-3 设计 / L2-1 Spec / L2-2 Spec / L1 Architecture §5.2.1 / ADR-0001 / ADR-0004 / 宪法 §2.2 / §3.7 / §4.7 / §7 / §9
- ✅ **附录 B 开放问题 12 项**（继承设计 8 项 + Spec 新增 4 项 B.9-B.12）：
  - **B.9（Spec 新增）**：framework SDK License 清单（CZ 强制 contrib/CI 扫描）
  - **B.10（Spec 新增）**：Adapter 镜像 cosign 签名私钥管理（GitHub Actions OIDC + cosign keyless）
  - **B.11（Spec 新增）**：Adapter 多实例（v1.0 不需要，per-Agent 单 Adapter 足够）
  - **B.12（Spec 新增）**：Adapter rate limiting（由 L2-1 ratelimit middleware 提供，不重复实现）

**亮点**：附录 B **双层开放问题模式**（继承设计 8 项 + Spec 新增 4 项）是 L2-3 阶段首创新模式 — 体现了"设计层决策 vs Spec 实施层问题"的分层。下次会话起草 L2-4 / L3 文件级 Spec 可复用此模式。

---

## §C 验收清单

### C.1 L2-3 设计自检

- [x] 模块边界清晰（In-Scope 8 项 / Out-of-Scope 8 项）✅
- [x] 6 框架适配矩阵（LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents）✅
- [x] 5 个 Card 转换点 + 失败处理 3 档 ✅
- [x] 容器镜像策略 A（推荐 per-framework）+ B（反例 unified multi-base）✅
- [x] 4 层配置优先级 + Secret 隔离原则 ✅
- [x] 7 个错误码 + Retryable 标记 + 重试策略表 ✅
- [x] 7 个 Prometheus 指标 + OTel Span + JSON 日志 ✅
- [x] 5 层测试（UT / IT / Golden / Conformance / E2E）✅
- [x] 3 个部署模式（Sidecar 推荐 / 同进程嵌入可选 / Init Container 不推荐）✅
- [x] 8 项开放问题 + 默认决策 ✅

### C.2 L2-3 Spec 自检

- [x] Go Package 布局到文件级（含 tests/ 三档 + deploy/ 分层）✅
- [x] 9 个 Exported API 完整（Adapter / FrameworkAdapter / CardConverter / ConfigLoader / errors / retry / observability / lifecycle / cmd/main）✅
- [x] Helm values 6 framework 独立 image override + env 映射表 ✅
- [x] CRD Schema 概要（引用 L1 §5.2.1）+ Adapter 选择伪代码 ✅
- [x] 生命周期契约 5 时序（启动 / Card / Reload / 优雅停机 / 错误恢复）✅
- [x] 100 测试 ID（UT 20 + IT 21 + Golden 50 + CF 3 + E2E 6）✅
- [x] 7 节 + 2 附录完整 ✅
- [x] 附录 B 12 项开放问题（继承 8 + Spec 新增 4）双层模式 ✅

---

## §D 优点

1. **设计 → Spec 映射自然**：L2-3 设计 12 节 1-to-1 映射到 Spec 7 节 + 附录，认知摩擦极低
2. **6 框架适配矩阵分层**：版本策略 + 入口点 + Card 复杂度 + 主要限制 + 里程碑 5 列完整，是 L3 多框架并行实施的直接输入
3. **Card 转换层 5 点 + 失败处理 3 档**：覆盖完整（含可选字段降级策略），避免 L3 实施时反复决策
4. **容器镜像策略 A/B 对照**：以反例（unified multi-base）衬托推荐方案（per-framework），决策依据透明
5. **9 个 Go interface 完整契约**：`core.Adapter` 8 方法 + `FrameworkAdapter` 扩展 + `AgentCardConverter` + `ConfigLoader` + `errors` + `retry` + `observability` + `lifecycle` + `cmd/main`，是 L3 实施层零返工输入
6. **Helm values 6 framework 独立**：image override + resources 差异化（crewai 1Gi 独占最高），env 映射表 + Deployment range 模板完整
7. **生命周期契约 5 时序图**：与 L2-2 Operator Core 集成的关键参考（启动 / Card / Reload / 优雅停机 / 错误恢复 全覆盖）
8. **测试用例编号方案完整**：UT-C-/UT-LC-/IT-AG-/GLC-/GCR-/CF-/E2E- 等 100 个 ID 覆盖 5 层测试类型
9. **附录 B 双层开放问题模式**：继承设计 8 项 + Spec 新增 4 项，体现"设计层决策 vs Spec 实施层问题"分层 — 创新模式，L2-4 可复用
10. **ADR-0004 范围协调**：与 v0.1=0 framework / v0.5=2 framework / v1.0=6 framework 时序严格一致
11. **宪法一致性**：所有关键条款（§2.2 / §3.5 / §3.6 / §3.7 / §4.7 / §6 / §7 / §9 / §11 / §14 / §15）均符合 CONSTITUTION.md v0.3.0
12. **错误码空间对齐**：-32001 ~ -32007 与 L2-1 JSON-RPC 域错误码扩展范围严格一致，便于日志聚合

---

## §E 不足 / 风险

### E.1 已识别（设计附录 B + Spec 附录 B 双重登记）

| 编号 | 风险 | 缓解 |
|------|------|------|
| R-1 | Sidecar 模式资源开销（每 Agent Pod 多 256Mi Adapter） | 见附录 B-5；默认 Sidecar；嵌入式仅限 LangChain v0.5 |
| R-2 | framework 升级导致 A2A Memory 兼容性问题 | 见附录 B-6；framework memory 不可用时降级到 A2A Memory service 代理 |
| R-3 | framework SDK License 一致性风险 | 见附录 B-8 / B-9；仅采纳 Apache 2.0 / MIT / BSD-3；contrib/CI 扫描 |
| R-4 | 第三方 contrib adapter 准入 / review 流程未完整 | 见附录 B-3；准入清单 + 2 名 maintainer LGTM（v1.5+ 触发） |
| R-5 | Adapter 镜像 cosign 签名私钥管理 | 见附录 B-10；GitHub Actions OIDC + cosign keyless 签名 |
| R-6 | Spec 43KB / 1044 行颗粒度偏差（2.4x） | 见 §B.2.6；保留完整版（倾向 1，类比 L2-1 / L2-2 §F.4） |
| R-7 | Adapter 容器与 Agent 容器 Sidecar Pod 共享网络但独立重启（failover 不对称） | L3 实施时 K8s Pod lifecycle hook + readiness probe 协调；Operator Sidecar 容错 |
| R-8 | Golden Case fixture 维护成本（50 个 yaml 文件） | v1.0 阶段 CI 自动化 + framework SDK 版本快照回放 |

### E.2 颗粒度偏差风险（中等）

- **现象**：Spec 43KB / 1044 行 vs 计划 12-18KB / 400-500 行（**2.4x**，与 L2-2 Spec 50KB / 1208 行的 2.8x 偏差同等级别）
- **影响**：评审阅读成本约 2-3 小时（比 L2-2 略低）
- **缓解**：保留完整版（决议倾向），通过以下结构化降低阅读成本：
  - §0 阅读指南 + L1/L2 边界对照表（约 1KB）
  - §2 Exported API 9 个 Go interface（**最高密度章节**，约 18KB）
  - §5 生命周期契约 5 时序图（关键章节）
  - 附录 A/B 状态标签（⏳ / ✅）便于快速查找

### E.3 v0.1 时间盒可行性（低，验证 ADR-0004 协调性）

- **观察**：L2-3 设计 + Spec 共 75KB / 1599 行（设计 32KB / 555 行 + Spec 43KB / 1044 行）
- **ADR-0004 协调**：v0.1=0 framework adapter / v0.5=2 framework（LangChain + AutoGen）/ v1.0=6 framework
- **影响**：v0.1 阶段 L3 实施**只落地 `core/` 抽象层 + cmd/adapter/main 入口**，不实现任何 framework adapter（Hello Agent 不需要 Adapter）— **与 ADR-0004 严格一致，时间盒无压力**
- **v0.5 实施负担估算**（首启 framework 集成）：
  - `langchain/` + `autogen/` 共 ~6 个核心文件 + 10 Golden Case fixture + 10 IT
  - 估算 60-80h（占 ADR-0004 总预算 200h 的 30-40%）
- **缓解建议**：
  1. v0.1 阶段仅 `core/` 落地（10 个 UT 通过 + Helm chart 主框架 + E2E hello 跑通）
  2. v0.5 阶段叠加 `langchain/` + `autogen/`（与 ADR-0004 时序对齐）
  3. v1.0 阶段叠加 `crewai/` / `semantic_kernel/` / `strands/` / `smolagents/` 4 个 framework

### E.4 L3 实施阶段 Python 依赖管理细节缺失（低）

- **观察**：Spec §1 Go Package 布局未显式展开 `requirements.txt` / `pyproject.toml` / `uv.lock` 等 Python 依赖管理工件
- **影响**：L3 实施时需决策：pip requirements.txt vs Poetry vs uv — 当前 Python 生态分裂
- **缓解建议**：
  1. Dockerfile 模板（`deploy/docker/Dockerfile.adapter.langchain` 等）在 L3 实施阶段同时落地
  2. 建议采用 **uv**（Astral，2024-2025 主流）作为统一工具，与 Python 3.11+ 良好集成
  3. 在 L3 实施 Spec 阶段补"依赖管理决策 ADR"（如必要）

### E.5 multi-language adapter 路径缺失（低，依赖 B.1 决策）

- **观察**：Spec §1 提到 Semantic Kernel adapter.py + adapter.cs 双实现，但 main.go §2.9 仅展示了 Python framework 加载路径（langchain.New / autogen.New switch）
- **影响**：L3 实施 .NET Semantic Kernel 时，需在 cmd/adapter/main.go 增加 `--runtime=python|dotnet` 切换逻辑
- **缓解**：L3 实施 Spec 阶段补双语言启动子命令；当前保留为 B.1 开放问题，不影响 v0.1 阶段

### E.6 Adapter 容器崩溃与 K8s restart 对 A2A Session 的影响（中）

- **观察**：Spec §5.5 错误恢复时序图覆盖了 K8s restart + CrashLoopBackOff，但**未明确** crash 时 in-flight A2A 请求的失败语义
- **影响**：客户端（如 Operator Core 调用 Adapter）需要 retry-on-restart 逻辑，避免一致性问题
- **缓解**：L3 实施阶段在 A2A Client side 增加 retry with exponential backoff；当前作为 Spec 缺口留待 L3

---

## §F 决议

### F.1 总体决议

✅ **通过** — L2-3 Adapter 设计文档 v0.1-draft + L2-3 Adapter Spec 文档 v0.1-draft **评审通过**。

### F.2 后续动作

1. ⏳ **升级为正式版本**：
   - L2-3 设计 → v0.1.0（移除 `-draft`）
   - L2-3 Spec → v0.1.0（移除 `-draft`）
2. 🚧 **下一阶段选择**（待办 #12，**用户决议项**）：
   - **选项 A**：进入 L2-4 Knowledge / Memory 模块设计（按 L1 模块清单，Adapter 与 Knowledge / Memory 是并列运行时层）
   - **选项 B**：暂停 L2 设计阶段，进入 L3 文件级 Spec（Operator Core / Adapter core / 等等）的代码契约阶段
   - **选项 C**：并行启动 L2-4 + L3 Operator 文件级 Spec（多会话摊销；但 MVP 例外 14.5 单点评审可能制约）
   - **当前倾向**：选项 A（L2-4 完成最后一个 L2 模块，使 L2 阶段 100% 完成，再进入 L3 实施更连贯；与 [[a2a-k8s-agent-platform]] 项目档案的"逐 L2 完成"节奏一致）

### F.3 例外适用记录

- 14.5 MVP 例外 ✅ 适用
- 单点评审 ✅ 已采用
- L2-3 与 L2-4 暂不合并（模块数 = 4，保留灵活性）

### F.4 颗粒度偏差决议

**决议**：保留 L2-3 Spec 完整版（43KB / 1044 行），不精简。

**理由**：
1. 宪法 §15.1 质量第一性 + §15.4 技术债不可悄悄累积
2. §2 Exported API 9 个 Go interface 完整展开（4.5x）是 Adapter 类模块**特有的 6 framework × 接口契约复杂度**，精简会导致 L3 实施反复决策
3. §3 Helm values 6 framework 独立（4x 偏差）是 L3 Helm chart 落地的直接输入
4. §5 生命周期契约 5 时序图是 Operator Core 集成的关键参考，缺失会导致 L2-2 + L2-3 集成歧义
5. 100 测试 ID 直接对应宪法 §9 80% 覆盖率目标
6. 附录 B 12 项开放问题（含 Spec 新增 4 项双层模式）是 L3 实施的零返工输入
7. 与 L2-1 评审 §F.4 + L2-2 评审 §F.4 同原则处理（保留完整版）

### F.5 决议待用户确认项

| 编号 | 决议项 | 倾向 |
|------|--------|------|
| Q-1 | 颗粒度偏差处理（保留 43KB / 精简到 25-30KB / 保留 + 摘要） | 倾向 1（保留）— 同 L2-1 / L2-2 |
| Q-2 | L2-3 评审通过后下一阶段选择（A: L2-4 Knowledge / Memory / B: L3 文件级 Spec / C: 并行） | 倾向 A（L2-4 完成 L2 阶段最后一块） |
| Q-3 | L2-3 评审通过后是否同时启动 v0.1 阶段 L3 文件级 Spec（`core/` 抽象层） | ⏳ 待用户决定（推荐延后 L2-4 完成后再统一启动 L3） |
| Q-4 | Spec 附录 B.11（Adapter 多实例）明确"v1.0 不需要"是否确认 | 倾向确认（per-Agent 单 Adapter 足够；AdapterSet 留给 v1.5+） |
| Q-5 | Spec 附录 B.12（Adapter rate limiting）明确由 L2-1 ratelimit middleware 提供是否确认 | 倾向确认（符合 §3.6 反依赖条款） |

### F.6 跨文档同步动作（评审通过后立即执行）

1. L2-3 设计 frontmatter：`v0.1-draft` → `v0.1.0`
2. L2-3 Spec frontmatter：`v0.1-draft` → `v0.1.0`
3. L2-3 设计 §变更记录：新增 v0.1.0 行（升级日期 + 评审通过 + 作者）
4. L2-3 Spec §变更记录：新增 v0.1.0 行（升级日期 + 评审通过 + 作者）
5. L2-1 Spec 附录 A：L2-3 行 `⏳ v0.1-draft` → `✅ v0.1.0`
6. L2-2 Spec 附录 A：L2-3 行 `⏳ v0.1-draft` → `✅ v0.1.0`

---

## §G 评审结论

> 本 L2-3 设计 + Spec 满足宪法质量第一性（第十五条）所有要求，L2-3 阶段所有强制门禁（14.4）已通过：
>
> - ✅ L2-3 设计完成（v0.1-draft）
> - ✅ L2-3 Spec 完成（v0.1-draft）
> - ✅ L2-3 评审通过（本文）
> - ✅ 与宪法一致（v0.3.0，§2.2 / §3.5 / §3.6 / §3.7 / §4.7 / §6 / §7 / §9 / §11 / §14 / §15 全部满足）
> - ✅ 与 L1 一致（Architecture §3.5 运行时层 + §5.2.1 Agent CRD `spec.adapter` + §6 Adapter 路线图）
> - ✅ 与 ADR 一致（ADR-0001 6 framework 范围 + ADR-0004 v0.5=2 / v1.0=6 时序）
> - ✅ 与 L2 一致（L2-1 `a2a.Server` 嵌入 + L2-2 Operator Owned resources Adapter container）
> - ✅ 风险识别 + 缓解方案（8 项 L3 移交 + 1 项本评审）
> - ✅ 差异化产出（§2 9 Go interface + §3 Helm 6 framework image override + §5 5 时序图 + 附录 B 12 项双层开放问题）
>
> 准许进入下一阶段（L2-4 Knowledge / Memory 或 L3 文件级 Spec，按用户决议 Q-2）。

---

> **评审者签署**：项目发起人 2026-07-24
> **下次评审**：L2-4（或 L3 Operator 文件级 Spec）模块完成后（预计 1 个会话；本期按时间盒可考虑启动 L2-4）
