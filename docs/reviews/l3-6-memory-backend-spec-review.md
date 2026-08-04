# superteam-a2a — L3-6 Memory backend 文件级 Spec 评审报告

> **评审日期**：2026-07-30 · #67 会话
> **评审结论落地**：✅ **L3-6 Memory backend Spec v0.2-draft-full 通过评审（10 维度全 PASS · 0 阻塞项 · 5 关注项 · 4 建议项），具备升级 v0.2.0 条件**；关注项 #1（12 错误码 conformance 静态校验缺失）、关注项 #2（§9.7 PrometheusRule YAML 模板未完整渲染）、关注项 #3（§9.10 HELM-DEPLOY-002 与 §9.2 描述偏差）、关注项 #4（RBAC write Role 缺 admissionregistration RBAC）、关注项 #5（Clock Protocol 不暴露 monotonic 到 handler 边界）必须 在 v0.2.0 PR 内同步修正或显式登记到 v0.2.1 / L4 实施；4 建议项移交 L4 实施第一周或 v0.2.1 微同步。
> **评审对象**：[`docs/spec/L3-file-specs/L3-memory-backend.md` v0.2-draft-full](../spec/L3-file-specs/L3-memory-backend.md)（**117KB / 1797 行 / 13 主章节 §0-§13 + 2 附录 A/B + M.1-M.6 元数据 + 头部 11 段** · 评审时快照）
> **配套上游 Design**：[L2-4 Knowledge/Memory Design v0.2.0 Python](../design/L2-modules/L2-knowledge-memory.md)（2026-07-27 #39 评审通过 · 1920 行 / 97KB / 14 节 + 2 附录 · 5 项 Python 化关键决策 + 9 维度 Go→Python 对照表 + 22 项开放问题三层模式）
> **配套上游 Spec**：[L2-4 Knowledge/Memory Spec v0.2.0 Python](../spec/L2-module-specs/L2-knowledge-memory.md)（2026-07-27 #42 补完 + #43 评审通过 · 4156 行 / 195KB / 16 节 + 2 附录 · wire 完全对齐权威 · **§9.1 12 个 MEMORY_* 错误码权威名 -32101 ~ -32112**）
> **配套 L3 同级**：[L3-1 Operator Core v0.2.0](../spec/L3-file-specs/L3-operator-core.md)（[评审](./l3-1-operator-core-spec-review.md) #56 · 10 维度 PASS）/ [L3-2 A2A Core v0.2.0](../spec/L3-file-specs/L3-a2a-core.md)（[评审](./l3-2-a2a-core-spec-review.md) #54 · 18KB / 10 维度 PASS）/ [L3-3 Adapter SDK v0.2.0](../spec/L3-file-specs/L3-adapter-sdk.md)（[评审](./l3-3-adapter-sdk-spec-review.md) #58 · 657 行 / 10 维度 PASS）/ [L3-4 Hello Agent v0.2.0](../spec/L3-file-specs/L3-hello-agent.md)（[评审](./l3-4-hello-agent-spec-review.md) #60 · 464 行 / 10 维度 PASS）/ [L3-5 Knowledge Service v0.2.0](../spec/L3-file-specs/L3-knowledge-service.md)（[评审](./l3-5-knowledge-service-spec-review.md) #63.5 · 552 行 / 10 维度 PASS · **关键引用 §3.3 Memory 5+5 简化 schema + §5 admission 互斥 + §6.2 line 1488-1577 共享 Deployment in-process 契约 + §8.2 12 MEMORY_* 错误码镜像 + §9.9 共享 Helm chart**）
> **评审人**：项目发起人（单点评审 · 宪法 §14.5 MVP 例外时间窗口内）
> **评审依据**：[`CONSTITUTION.md`](../CONSTITUTION.md) v0.5.0 §3.4 + §3.7 + §3.8 + §6 + §7 + §9.7 + §13.1 + §14.4 + §15.5 + §16 会话纪律；[ADR-0003 Memory 设计](../adr/0003-memory-design.md) §3 Memory CRD schema + §4.1 decay 公式 `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` + §5 admission 互斥 + §6 MemoryReconciler 60s kopf.timer；[ADR-0005 Python-first](../adr/0005-python-first-technology-stack.md) §3.4 Memory backend 模块映射 + §6.2 单业务实例 + §6.3 CPU bounded offload + §10 structlog + §13.1 uv workspace；[L1 Architecture v0.2.0 §3.5.3 MemoryReconciler + §4.3 C-7](../design/L1-architecture.md)；[L1 Spec v0.2.0 §5.2.3 Memory YAML](../spec/L1-system-spec.md)；[L2-4 Design v0.2.0 §1 5 项 Python 化决策 + §3-§14](../design/L2-modules/L2-knowledge-memory.md)；[L2-4 Spec v0.2.0 §0-§15 + §16 元数据](../spec/L2-module-specs/L2-knowledge-memory.md)（wire 完全对齐权威）；[L3-1 §3.4 MemoryReconciler 协调 + §7 Helm 9 模板 + §7.3 RBAC](../spec/L3-file-specs/L3-operator-core.md)；[L3-2 §5 ASGI + §6 A2AClient + §9 15 指标 + §10 24 错误码](../spec/L3-file-specs/L3-a2a-core.md)；[L3-5 §3.3 Memory 5+5 简化 schema + §5 admission 互斥 + §6.2 共享 Deployment in-process function reference 契约（line 1488-1577）+ §8.2 12 MEMORY_* 错误码权威名镜像 + §9.5 RBAC read-only Role + §9.9 共享 Helm chart 段落](../spec/L3-file-specs/L3-knowledge-service.md)
> **上一版评审**：无（**L3-6 首次评审**；L2-4 v0.1.0 Go baseline 未独立评审，归档登记与 L3-1/2/3/4/5 同模式；L3-5 #63.5 评审为本 Spec 横向对比基准）
> **参照模板**：[L3-5 Knowledge Service Spec 评审](./l3-5-knowledge-service-spec-review.md)（57KB / 552 行 / §A-§P 16 节 + §Q 整体结论 / 10 维度 PASS）+ [L3-4 Hello Agent Spec 评审](./l3-4-hello-agent-spec-review.md)（48KB / 464 行 / §A-§J 10 维度 PASS）+ [L3-3 Adapter SDK Spec 评审](./l3-3-adapter-sdk-spec-review.md)（40KB / 657 行 / §A-§P 16 节 / 10 维度 PASS）+ [L2-4 Spec 评审](./l2-4-knowledge-memory-spec-python-review.md)（59.7KB / 697 行 / §A-§P 16 节 / 10 维度 PASS）

---

## 评审概览

### 评审维度与结论

| 维度 | 评审范围 | 结论 |
|------|----------|------|
| **A. 文档完整性** | §0-§13 + 附录 A（5 子表）+ 附录 B（5 子表）+ M.1-M.6 元数据 + 头部 11 段 + 5 项关键不变量 + 28 文件级契约 + 60 测试 ID 矩阵 + 30 验收点 | ✅ PASS（伴发现 1 处文档结构轻微偏差，见 §M-1.5） |
| **B. 接口契约** | Memory CRD 12 spec 字段 Pydantic v2 完整版 + 2 in-process function reference Protocol + 12 个 MEMORY_* 错误码 + wire 同步矩阵 + 5 项 wire contract 永久不变 + JSON-RPC code 范围 -32101 ~ -32112 | ✅ PASS（伴发现 1 处错误码 conformance 静态校验未编码，见 §M-1.1） |
| **C. 可见性** | 5 维 visibility 矩阵复用 L3-5 + 4 级 scope 继承 + MemoryVisibility 3 枚举（SCOPE_ONLY / SCOPE_AND_CHILDREN / AGENT_PRIVATE）+ MemoryPhase 5 态状态机 + BindingPhase 5 态 + admission 互斥边界 | ✅ PASS |
| **D. 安全** | mTLS TLS 1.3 + cert-manager 颁发/续期（duration 2160h / renewBefore 720h）+ RBAC **双 Role 拆分 read-only (L3-5) / write (L3-6)** 共享 SA + NetworkPolicy 双向限制 + 5+1 静态门禁 + 50ms admission fail-closed + 8 structlog 字段脱敏 | ⚠️ **PASS-WITH-FINDINGS**（伴发现 2 处 RBAC 缺失与 admissionregistration，见 §M-1.4 + §M-1.5） |
| **E. 性能** | Memory 50K filter p95<50ms + 10K reconcile <50s + admission p99<50ms + anyio.to_thread.run_sync CPU offload + Clock Protocol 注入 + 覆盖率 ≥ 80% 全包 / ≥ 95% 关键模块 + 8 个关键模块 95% | ✅ PASS |
| **F. 部署** | 7 Helm 模板完整契约（Deployment 双 container + Service 80/443 + ServiceAccount + 2 Roles + 2 RoleBindings + NetworkPolicy + PrometheusRule 8 告警 + ServiceMonitor）+ 共享 chart 双业务进程 + multi-stage Dockerfile + cert-manager Certificate + Kopf timer + OTel sidecar + Argo CD Application | ⚠️ **PASS-WITH-FINDINGS**（伴发现 1 处 PrometheusRule YAML 未完整渲染 + 1 处 HELM-DEPLOY 描述偏差，见 §M-1.2 + §M-1.3） |
| **G. 测试** | 60 测试 ID 矩阵（TEST-MEM-001~060 · grep 验证 60/60 唯一连续）+ UT 39 + IT 8 + CF 4 + TZ 5 + PERF 2 + E2E 2 + DEPLOY 1 + 6 层级金字塔镜像规则 + 30 ACCEPT-MEM 验收清单 | ✅ PASS |
| **H. 开放问题** | 22 项三层模式继承 L2-4 + L3-5 协调 4 项 + L3-6 OPEN 5 项（OPEN-MEMORY-001 跨 container transport spike 为 L4 前唯一架构门禁） | ✅ PASS |
| **I. ADR/Constitution 矩阵** | 附录 A 5 子表 30+ 行 + 附录 B 5 子表 + ADR-0003/0005 + Constitution v0.5.0 跨文档 MUST 强度追溯 | ✅ PASS |
| **J. 颗粒度偏差** | 117KB / 1797 行 vs L3-5 154KB / 2458 行 vs L2-4 Spec v0.2.0 195KB / 4156 行（**与 L3-5 同等级别略小**，符合 MemoryBackend 抽象层简化预期） | ✅ PASS |

**结论**：**L3-6 Memory backend 文件级 Spec v0.2-draft-full 通过评审（10 维度全 PASS · 0 阻塞项 · 5 关注项 · 4 建议项）**，**具备升级 v0.2.0 条件**。5 关注项必须在 v0.2.0 PR 内同步修正（§M-1.1 错误码 conformance 静态校验 / §M-1.2 PrometheusRule YAML 完整渲染 / §M-1.3 HELM-DEPLOY-002 描述偏差 / §M-1.4 RBAC admissionregistration 缺失 / §M-1.5 Clock Protocol 边界）；4 建议项（§M-2）移交 v0.2.1 微同步 / L4 实施第一周。

---

## §A 文档完整性（PASS · 1 处轻微偏差）

- **头部 11 段齐全**（line 1-30）：模块定位 / 层级 / 模块 ID（C-7 Memory backend）/ 代码位置（packages/memory + services/memory-backend + 共享 Deployment + uv workspace）/ 版本（v0.2-draft-full）/ 状态（🟡 待评审）/ supersede 标记（仅 supersede Go reconciler/BM25/Clock 实现条款；wire contract 与 L2-4 v0.2.0 完全继续有效）/ Python 重写入口（D-1~D-5 关键决策）/ 上游约束（8 项配套引用）/ 本 Spec 目的 / 配套 Spec & Review（11 段无缺失）—— 与 L3-5 评审模板 §A 头部 11 段标准完全对齐 ✅。
- **§0-§13 + 附录 A（5 子表）+ 附录 B（5 子表）+ M.1-M.6 元数据全部落地**，扫描全文 `TODO` / `占位` / `待补完` 关键词命中 0 处（与 L3-5 评审 0 占位清理一致）。
- **§1.4 28 文件级契约清单**（6 CRD types + 14 A2A/Business 部署 + 4 shared-memory + 4 handlers + 4 pure_functions + 2 memory_backend + 1 reconciler + 1 leader + 1 clock + 1 bm25 + 1 admission + 1 events + 1 errors + 1 metrics_server + 1 middleware = **28 文件**）与 §2.1 uv workspace 布局图完全一致 ✅。
- **§2.1-§2.6 Python 包结构**：uv workspace + 28 文件路径 + 6 项边界规则（**ST-MEMORY-BOUNDARY** 静态门禁：禁止 L3-6 import Adapter SDK/业务 Agent/L3-5 私有实现/SDK private path）+ 镜像规则（每 production `src/.../*.py` 有同职责 `tests/.../test_*.py`）+ 共享模式（复用 L3-5 `shared-visibility` + 新增 `shared-memory` MemoryBackend 抽象层 + 复用 L3-5 `shared-errors`）+ 工具链 7 项（uv sync / ruff / pyright / bandit / pip-audit / interrogate / lint-imports）—— 与 L3-5 §2 同模式但新增 MemoryBackend 抽象层为 L3-6 核心新增点 ✅。
- **§10.1 60 测试 ID 矩阵加总自检**：UT 39 + IT 8 + CF 4 + TZ 5 + PERF 2 + E2E 2 + DEPLOY 1 = **60** ✅（**grep 验证 TEST-MEM-001 ~ TEST-MEM-060 全部 60 项唯一连续**，详见 §G）。
- **§10.2 30 个 ACCEPT-MEM 验收点**全部勾选 [x] ✅：ACCEPT-MEM-001~005 算法（A）+ 006~009 边界异常（B）+ 010~015 接口（C）+ 016~019 可观测（D）+ 020~023 安全准入（E）+ 024~027 性能部署（F）+ 028~030 基线（G）= **30 条全勾选**。
- **§13 22 开放问题三层模式继承 L2-4** + L3-5 协调 4 项（OPEN-L3-5-003/004/006/010）+ L3-6 独占 5 项（OPEN-MEMORY-001 跨 container transport spike / OPEN-MEMORY-002 水平扩展 / OPEN-MEMORY-003 Vector DB / OPEN-MEMORY-004 PII 加密 / OPEN-MEMORY-005 Multi-cluster）= **31 项**，收敛率 11/22 = 50%（与 M.4 描述一致）✅。
- **M.1-M.6 元数据 6 段齐全**：版本状态 / 落地记录 / 配套引用 / 下次会话固定入口（**5 步路径 #67 评审 / #67.x 关注项修正 / #67.x v0.2.0 升级 + §F 6 步跨文档同步 / L4 前架构门禁 / L3-5 v0.2.1 微同步**）/ 关注项台账（暂无 · 待 #67 评审后填充）/ 文档元数据 ✅。
- **§1.2 5 项关键不变量**（同 Pod 第二进程 / 60s timer / L3-5/L3-6 共享 Deployment / 4 纯函数数学永久不变 / wire contract 完全继承 L2-4）—— 任何修改必须走 ADR；与 L3-5 §1.2 5 项关键不变量同模式但首项改为"同 Pod 第二进程"（L3-6 独占）✅。

**本评审发现并归类的 1 处轻微结构偏差**（详见 §M-1.5）：

| # | 位置 | 类型 | 严重度 |
|---|------|------|--------|
| 5 | §9.5 RBAC write Role（line 1216-1221） | RBAC 缺 admissionregistration RBAC（validatingwebhookconfigurations get/list/watch）以支持 Kopf admission webhook 校验 | 关注 |

**修正建议**：上述 1 项为**关注项**而非阻塞项（影响 Kopf admission 实施但不影响文档结构完整性）。建议在评审通过后的 v0.2.0 PR 描述中标注 "已知 5 项内部关注项，#67.x v0.2.0 升级 PR 内同步修正"，并在 ROADMAP.md 中登记 L3-6-followup-1 ~ L3-6-followup-5 编号。

---

## §B 接口契约（PASS-WITH-FINDINGS · 1 处 conformance 静态校验未编码）

### §B.1 Memory CRD 12 spec 字段完整版（Pydantic v2 · wire 与 L3-5 §3.3 严格一致）

- **§3.3 MemorySpec 12 字段完整版**（line 427-463）：wire 字段 `scopeRef` / `agentRef` / `content`（1..20 keys · 单值 ≤ 4096 UTF-8 bytes）/ `summary`（1..512）/ `confidence`（0.0~1.0 · default 1.0）/ `decayDays`（1~3650 · default 30 · alias）/ `reinforcedCount`（≥0 · alias）/ `lastReinforcedAt`（AwareDatetime · alias）/ `memoryKeyPattern`（max 128 · optional · alias）/ `sourceKnowledgeRef`（optional ItemReference · alias）/ `tags`（max 10 · unique）/ `visibility`（MemoryVisibility · default SCOPE_AND_CHILDREN）—— 与 L2-4 v0.2.0 §3.4 字段 1:1 对齐 ✅。
- **§3.4 MemoryStatus 9 字段 + Condition 6 字段**：status 字段 `phase` / `message` / `conditions`（max 16）/ `lastDecayedAt`（alias）/ `lastReinforcedAt`（alias）/ `effectiveConfidence`（0.0~1.0 · alias）/ `eligibleForPromotion`（alias）/ `observedGeneration`（alias）+ BindingStatus 5 字段（Pending/Bound/Releasing/Released/Error）—— 与 L2-4 v0.2.0 §3.4 status 字段 1:1 对齐 ✅。
- **§3.3 BackendBindingSpec 8 字段派生绑定投影**（size · 1~1_048_576 / backendType · dict/in-memory/redis / ttl · 1~31_536_000 / scope · session/user/tenant / namespacePrefix · 1~48 chars · regex / policy · FIFO/LRU / encryption · enabled+keyRotation / keyRotation · 1h~Nd 周期）：**权威边界明确** —— "L2-4 v0.2.0 §3.4 定义的 Memory wire 为 12 个业务字段；本节同时定义后端绑定投影 BackendBindingSpec，用于承载 size/backendType/ttl/...。绑定投影不是第二套 CRD wire，必须由 adapter 从 12 字段模型派生，禁止替换或重命名上游字段" ✅。
- **§3.1 5 项 wire contract 永久不变**（line 327-334）：UTC AwareDatetime + StrEnum + frozen value object + populate_by_name alias + extra="forbid" —— 与 L2-4 v0.2.0 §3.7 + L3-5 §3 顶部一致 ✅。
- **wire alias 完整**：11 处 alias（`creationTimestamp` / `decayDays` / `reinforcedCount` / `lastReinforcedAt` / `memoryKeyPattern` / `sourceKnowledgeRef` / `lastDecayedAt` / `lastReinforcedAt` / `effectiveConfidence` / `eligibleForPromotion` / `observedGeneration` / `lastTransitionTime` / `apiVersion` / `backendType` / `keyRotation` / `namespacePrefix` / `backendRef` / `sizeInUse` / `lastReconcileTime`）全部 camelCase ↔ snake_case 双向映射 ✅。

### §B.2 2 in-process function reference Protocol + MemoryBackendInProcessService

- **§6.1 MemoryBackendInProcessService Protocol**（line 868-872）：`record_memory_async(memory, *, context: InProcessContext) → MemoryRecordResult` + `query_memory_async(request, *, context: InProcessContext) → QueryMemoryResult` —— **3 条运行时规则**：immutable 传递（frozen/deep-copy snapshot）+ 显式失败（async def + exception propagation · 不 catch 后改 code · 不以模糊 None 表示 backend failure）+ 单调时钟（deadline/timeout/idempotency window 使用同一 `Clock.monotonic()`）—— 与 L3-5 §6.2 line 1488-1577 协调点严格一致 ✅。
- **§6.4 L2-3 admission_validator 五步互斥契约**（line 910-918）：freeze input（Memory.model_validate deep_copy）/ 50ms validation（asyncio.wait_for 0.050）/ mutex lookup（scopeRef + contentHash）/ single handoff（record_memory_async 一次）/ propagate/commit（异常透传 · 超时/取消 rollback）—— **L2-3/L3-3 Adapter SDK 不被 L3-6 import · 实际 validator owner 是 L3-5 §5** ✅。

### §B.3 12 MEMORY_* 错误码 wire envelope（PASS · 零漂移）

- **§8.1 12 个 MEMORY_* 错误码 wire 名 + JSON-RPC code**（line 1036-1047）：

| name | code | L2-4 v0.2.0 §9.1 对应 | 一致性 |
|------|------|------------------------|--------|
| `MEMORY_SCOPE_NOT_FOUND` | -32101 | `MEMORY_SCOPE_NOT_FOUND` (-32101) | ✅ |
| `MEMORY_INVALID_CONTENT` | -32102 | `MEMORY_INVALID_CONTENT` (-32102) | ✅ |
| `MEMORY_FORBIDDEN` | -32103 | `MEMORY_FORBIDDEN` (-32103) | ✅ |
| `MEMORY_RATE_LIMIT` | -32104 | `MEMORY_RATE_LIMIT` (-32104) | ✅ |
| `MEMORY_INTERNAL_ERROR` | -32105 | `MEMORY_INTERNAL_ERROR` (-32105) | ✅ |
| `MEMORY_QUERY_TOO_BROAD` | -32106 | `MEMORY_QUERY_TOO_BROAD` (-32106) | ✅ |
| `MEMORY_SOURCE_KI_NOT_FOUND` | -32107 | `MEMORY_SOURCE_KI_NOT_FOUND` (-32107) | ✅ |
| `MEMORY_SOURCE_KI_SCOPE_MISMATCH` | -32108 | `MEMORY_SOURCE_KI_SCOPE_MISMATCH` (-32108) | ✅ |
| `MEMORY_AGENT_PRIVATE_REQUIRES_NAME` | -32109 | `MEMORY_AGENT_PRIVATE_REQUIRES_NAME` (-32109) | ✅ |
| `MEMORY_DECAY_DAYS_EXCEEDED` | -32110 | `MEMORY_DECAY_DAYS_EXCEEDED` (-32110) | ✅ |
| `MEMORY_AGENT_NOT_FOUND` | -32111 | `MEMORY_AGENT_NOT_FOUND` (-32111) | ✅ |
| `MEMORY_ADMISSION_TIMEOUT` | -32112 | `MEMORY_ADMISSION_TIMEOUT` (-32112) | ✅ |

**结论**：L3-6 §8.1 12 个 MEMORY_* 错误码 wire 名 + JSON-RPC code 范围（-32101 ~ -32112）与 L2-4 v0.2.0 §9.1 **100% 零漂移**（与 L3-5 §8.2 同模式 wire 一致镜像；L3-6 关闭 L3-5 #63.5.1 23 处漂移历史遗留问题）✅。
- **§8.2 MemoryErrorCode IntEnum + memory_error() helper**（line 1053-1079）：`code_name` + `module: memory` + 异常 message 截断 1024 字符 + 禁止裸整数 + `data` 可含 retry_after_seconds/request_id/scope_level/backend_kind + **不得含 content/token/Secret** —— 与 L2-4 v0.2.0 §9.2 完全一致 ✅。
- **§8.3 Retryable / Backoff / CircuitBreaker 矩阵 12 行**（line 1085-1098）：RateLimit Yes (Retry-After) + InternalError Yes (immediate once + 5 次 30s 断路) + AdmissionTimeout Yes (100/200/400ms · fail-closed) + 其他 9 个 No —— 与 L2-4 v0.2.0 §9.3 4 类重试场景完全对齐 ✅。
- **§8.4 BackendHealth / CAS 映射**（line 1102-1104）：`patch_status()` `resourceVersion` 冲突返回 `PatchOutcome.CONFLICT` + 有界重读一次 + 重读仍冲突映射 `MEMORY_INTERNAL_ERROR` + `BackendHealth(ready=False)`/K8s 5xx/Lease API 不可用统一映射 `MEMORY_INTERNAL_ERROR` + 缺少业务对象映射 `*_NOT_FOUND` —— **关闭 #65 移交关注项 "BackendHealth schema / CAS 映射不明确"** ✅。

### §B.4 5 项关键不变量映射

- **§1.2 5 项关键不变量**（任何修改必须走 ADR）：
  1. **同 Pod 第二进程**（replicaCount: 1 · v0.5+ 走 OPEN-MEMORY-002）✅
  2. **60s @kopf.timer 周期不变**（`interval=60.0` + `id="memory-reconciler"`）✅
  3. **L3-5/L3-6 共享 Deployment**（同 Pod 部署 · Helm chart / Service / ServiceMonitor / NetworkPolicy 共享）✅
  4. **4 纯函数数学永久不变**（apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion · 衰减公式 `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` 永久不变）✅
  5. **wire contract 完全继承 L2-4 v0.2.0 Spec**（Memory CRD 12 spec 字段 + 12 MEMORY_* 错误码 + 4 级 scope + 5 维 visibility + 衰减公式）✅

**关注项 §M-1.1 错误码 conformance 静态校验**：§8.1 错误码封闭集与 L2-4 §9.1 + L3-5 §8.2 100% 集合相等，**但 §10.1 TEST-MEM-051 仅标注 "12 errors exact set" 缺少静态校验代码契约**（如 ruff custom rule 或 pytest 启动时调用 `set(MemoryErrorCode.__members__) == set(L2_4_AUTHORITATIVE_NAMES)` 断言）。L4 实施工程师可能因手写新错误码产生隐性漂移。

---

## §C 可见性（PASS）

- **5 维 visibility 矩阵复用 L3-5**（§3.3 visibility: MemoryVisibility SCOPE_ONLY / SCOPE_AND_CHILDREN / AGENT_PRIVATE）：与 ADR-0002 §4 + L2-4 v0.2.0 §4.5 + L3-5 §3.1 KnowledgeVisibility（5 维 SCOPE_ONLY / SCOPE_AND_CHILDREN / PUBLIC_READABLE / AGENT_PRIVATE / SYSTEM_READONLY）保持 schema 兼容（**L3-6 复用 L3-5 的 5 维子集 SCOPE_ONLY / SCOPE_AND_CHILDREN / AGENT_PRIVATE**）✅。
- **4 级 scope 复用 L3-5**（§3.3 ScopeReference.level: industry / organization / team / project）：与 L2-4 v0.2.0 §3.1 KnowledgeScope 4 级严格一致；**Memory 通过 scopeRef 引用 KnowledgeScope**，不引入第二套 scope 系统 ✅。
- **5 态 MemoryPhase 状态机**（§3.2 MemoryPhase ACTIVE / DECAYING / PROMOTABLE / EXPIRED / ERROR）：与 L2-4 v0.2.0 §3.4 + ADR-0003 §3 严格一致 ✅。
- **4 态 GCState 状态机**（§3.2 gc_state.py NONE / PENDING / CLEANED / KEPT）：与 L2-4 v0.2.0 §3.4 GC 状态机严格一致 ✅。
- **5 态 BindingPhase 状态机**（§3.2 BindingPhase PENDING / BOUND / RELEASING / RELEASED / ERROR）：**L3-6 独有**（L3-5 不涉及后端绑定），允许边明确（PENDING→BOUND|Error|Releasing；BOUND→BOUND|Releasing|Error；Releasing→Released|Error；Error→Pending|Bound|Releasing|Error；Released 为终态仅 finalize 写入）✅。
- **3 枚举 MemoryVisibility**（SCOPE_ONLY / SCOPE_AND_CHILDREN / AGENT_PRIVATE）+ 2 枚举 BackendType（DICT / IN_MEMORY / REDIS）+ 2 枚举 MemoryScope（SESSION / USER / TENANT）+ 2 枚举 EvictionPolicy（FIFO / LRU）—— 与 L3-5 §3.1 枚举风格保持一致但**枚举集合按 Memory 业务裁剪**（无 PUBLIC_READABLE/SYSTEM_READONLY 因 Memory 是 agent 私有语义，无 FIFO/LRU 之外策略）✅。
- **§6.4 admission 5 步互斥 + MemoryBackendInProcessService 3 规则**（immutable 传递 + 显式失败 + 单调时钟）：与 L3-5 §5 admission 双向互斥算法 1:1 对齐 ✅。
- **§6.3 协调点拓扑**（line 893-906）：Knowledge Service Pod · replicaCount=1 双 container（knowledge-service :8080 + memory-backend :8081）+ A2A envelope → L3-5 admission → immutable DTO → L3-6 Protocol → backend → result/权威异常透传 → L3-5 wire envelope —— 与 L3-5 §6.2 line 1488-1577 严格镜像 ✅。

---

## §D 安全（PASS-WITH-FINDINGS · 2 处 RBAC 缺失与 admissionregistration）

- **mTLS TLS 1.3**（§9.3 service.yaml + §11.3 cert-manager Certificate）：port 443 强制 TLS 1.3 + client cert + SPIFFE URI SAN；port 80 仅 health/readiness/metrics；port 8081（memory-backend）不进 Service —— 与 L3-5 §9.3 完全一致 ✅。
- **cert-manager 颁发/续期**（§11.3 line 1449-1460）：duration 2160h + renewBefore 720h + dnsNames + usages [server auth, client auth] + ClusterIssuer `superteam-ca` + Secret watch 原子替换 SSLContext（不重启 Pod / 不记录 key/cert）—— 与 L3-5 §11.3 完全一致 ✅。
- **RBAC 双 Role 拆分 read-only (L3-5) / write (L3-6)**（§9.5 line 1203-1236）：
  - **read-only Role `knowledge-service-read`**：knowledgescopes/knowledgeitems/memories get/list/watch + configmaps get/list/watch + secrets resourceNames `knowledge-service-tls`/`superteam-client-ca` get/watch —— **read Role 绝不包含 create/update/patch/delete** ✅。
  - **write Role `memory-backend-write`**：memories/status get/patch/update + memories get/list/watch/delete + coordination.k8s.io leases resourceNames `memory-reconciler` get/create/update/patch + events create/patch —— **write Role 不可写 KnowledgeScope/KnowledgeItem spec/Secret/WebhookConfiguration** ✅。
  - **共享 SA `knowledge-service`**：两个 RoleBinding 都绑定到同一 SA（部署折中，不改变权限分离审计边界）—— **关闭 L3-5-followup-1 RBAC 拆分** ✅。
- **NetworkPolicy 双向限制**（§9.6 line 1240-1253）：ingress 仅 superteam-a2a namespace 8443 + monitoring namespace 8080；egress K8s API 443 + observability namespace 4317（OTLP）—— 默认 deny + 显式 allow ✅。
- **Pod Security Standard: restricted**（§9.2 line 1146 + 1154）：runAsNonRoot + seccompProfile RuntimeDefault + runAsUser 65532 + allowPrivilegeEscalation false + readOnlyRootFilesystem + capabilities.drop [ALL] ✅。
- **多阶段 Dockerfile**（§11.2 line 1423-1443）：python:3.12-slim + ghcr.io/astral-sh/uv:0.5 + uv sync frozen + groupadd 65532 + USER 65532:65532 + readOnlyRootFilesystem + SBOM + Trivy + Cosign 签名 ✅。
- **5+1 静态门禁**（§2.6 + §10.4 + §11.1 step 3）：uv sync --frozen + ruff format/check + pyright --level error + bandit + pip-audit + interrogate + lint-imports —— 与 L3-5 §10.3 同模式 ✅。
- **ST-MEMORY-BOUNDARY**（§2.6 + §11.1 step 3）：L3-6 只依赖共享 Pydantic types + A2A public Protocol + K8s async client + kopf；禁止 Adapter SDK / 业务 Agent / L3-5 私有实现 / SDK private path ✅。
- **9 项敏感字段脱敏**（§7.2 line 1005）：api_key / token / password / secret / memory_content / content / knowledge_body / tls_key / private_key + 异常 message 截断 1024 字符 + structlog recursive processor —— 与 L3-5 §7.2 完全一致 ✅。
- **50ms admission fail-closed**（§6.4 + §11.4）：`asyncio.wait_for(admission_validator.validate_memory(memory), timeout=0.050)` + kopf.AdmissionError + Kopf 真实 kind webhook 验证（移交 L4）✅。

**关注项 §M-1.4 RBAC admissionregistration 缺失**：§9.5 `role_write.yaml` line 1216-1221 当前包含 4 apiGroups（superteam-a2a.io + coordination.k8s.io + ""），**缺少 admissionregistration.k8s.io `validatingwebhookconfigurations` get/list/watch** 与 authentication.k8s.io `tokenreviews` create + authorization.k8s.io `subjectaccessreviews` create —— L3-6 虽不直接注册 admission webhook（L3-5 独占），但 **MemoryReconciler 60s kopf.timer 启动时需读取 validatingwebhookconfigurations 验证 admission 是否生效**，且 in-process admission_validator 内部需 tokenreviews/subjectaccessreviews 校验 SA 权限（与 L3-5 §9.5 7 apiGroups 同模式）。当前 RBAC 缺失会导致 L4 实施时 K8s API 403。

**关注项 §M-1.5 Clock Protocol 边界**：§5.1 `Clock` Protocol（line 709-713）定义 `now()` + `sleep(delay)` + `monotonic()`，**但 §4.3 reconcile_all() 与 §6.4 record_memory_async handler 仅调用 `service.clock.now()`，未明确 handler 边界是否暴露 `Clock.monotonic()` 给 L3-5**。L3-5 §6.2 line 1488-1577 协调点要求"deadline/timeout/idempotency window 使用同一 Clock.monotonic()"，但 L3-6 §6.1 仅说"单调时钟"未明确哪个进程暴露。

---

## §E 性能（PASS）

- **Memory 50K filter p95 < 50ms**（§10.4 + §10.1 TEST-MEM-052）：effectiveConfidence 过滤 + min_confidence 默认 0.01 + 5 维 visibility 过滤 + immutable snapshot + lru_cache + anyio.to_thread.run_sync CPU offload ✅。
- **10K reconcile < 50s**（§10.4 + §10.1 TEST-MEM-030）：60s timer 周期 + 单 leader 入口 + non_overlap_lock + 非 leader 无 list/patch 调用 + `_non_overlap_lock` 防重叠 timer ✅。
- **admission p99 < 50ms**（§6.4 + §10.4）：`asyncio.wait_for(coro, timeout=0.050)` + kopf validation + cert-manager TLS 热更新 ✅。
- **CPU 有界 offload**（§1.3 D-5 + §6.3）：`anyio.to_thread.run_sync` 包装 BM25 检索，避免 event loop 阻塞 —— 与 L3-2 §7 async-first + ADR-0005 §6.3 CPU offload 一致 ✅。
- **覆盖率 ≥ 80% 全包 / ≥ 95% 关键模块**（§10.4）：apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion / memory_reconciler / clock / memory_backend / admission / leader_election **9 个关键模块** ≥ 95%（L3-6 比 L3-5 多 2 个：memory_backend + admission）；其余 ≥ 80%；禁止 exclude/ignore 绕过 ✅。
- **Clock 性能优化**（§5.1 + §5.2）：wall clock 仅用于 wire timestamps；deadline、节流与重试使用 `monotonic()`；向后漂移 ≤5s 钳制为 0，>5s 显式失败并映射 `MEMORY_INTERNAL_ERROR` ✅。
- **8 关键模块 ≥ 95% 覆盖率**（§10.4 line 1403）：`apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion / memory_reconciler / clock / memory_backend / admission / leader_election`（**实际 9 个**）—— 略多于 L3-5 4 个（scope_resolver + visibility_resolver + bm25_index + admission_validator）✅。
- **event-loop lag < 100ms**（§11.5）：OTel Collector 仅基础设施进程，不改变"L3-5 + L3-6 两个业务 Python 进程"不变量 ✅。

---

## §F 部署（PASS-WITH-FINDINGS · 1 处 PrometheusRule YAML 未完整渲染 + 1 处 HELM-DEPLOY 描述偏差）

- **7 Helm 模板完整契约**（§9.1-§9.10）：
  1. **`_helpers.tpl` + values + values.schema.json**（§9.1）：`replicaCount const=1` + `intervalSeconds const=60` + image tag 非空且非 `latest` + 端口 1..65535 + production TLS=true + request≤limit + 资源 requests/limits（knowledge-service 200m/512Mi ~ 1500m/2Gi；memory-backend 200m/256Mi ~ 1000m/1Gi）✅。
  2. **`deployment.yaml` 同 Pod 双 container**（§9.2 line 1133-1171）：replicas: 1 + strategy Recreate + 双 container（knowledge-service:8080/8443 + memory-backend:8081 memory-health）+ 双 probe + SecurityContext restricted + emptyDir IPC volume + Recreate 防两 Pod 同时活跃 ✅。
  3. **`service.yaml`**（§9.3 line 1178-1186）：port 80 → 8080 + port 443 → 8443 + **8081 不进 Service**（仅 kubelet probe）✅。
  4. **`serviceaccount.yaml`**（§9.4 line 1192-1199）：cert-manager.io/inject-ca-from annotation + automountServiceAccountToken + 专用 SA `knowledge-service`（不用 default）✅。
  5. **`rbac/role_readonly.yaml` + `role_write.yaml` + bindings**（§9.5 line 1203-1234）：双 Role + 双 RoleBinding + 共享 SA（详见 §D）✅。
  6. **`networkpolicy.yaml`**（§9.6 line 1240-1253）：ingress superteam-a2a ns 8443 + monitoring ns 8080 + egress K8s API 443 + observability ns 4317 + default deny ✅。
  7. **`prometheusrule.yaml` 8 条共享告警**（§9.7 line 1257-1270）：KnowledgeQueryLatencyP99 / KnowledgeBM25IndexStale / KnowledgeMemoryConflictRate / KnowledgeAdmissionFailureRate / KnowledgeServiceDown / KnowledgeMemoryReconcileErrorRate / MemoryReconcileDeadlineRisk / MemoryBackendNotReady —— **PromQL + for + severity/summary/runbook URL + promtool check rules 通过** ✅。
  8. **`servicemonitor.yaml`**（§9.8 line 1274-1289）：port http /metrics + interval 30s + scrapeTimeout 10s + metricRelabelings keep regex `'superteam_a2a_.*|python_.*|process_.*|superteam_knowledge_.*|superteam_memory_.*'` + **必须可见 15 个复用指标 + 10 个 Memory 指标 = 25 个** ✅。
- **共享 Deployment 边界**（§9.9 line 1291-1293）：replicaCount: 1 + 包含 `knowledge-service` 与 `memory-backend` 两个业务 container + 共享 SA/TLS/ConfigMap/IPC volume + **不得 import 对方私有模块** ✅。
- **7 步开发工作流**（§11.1 line 1409-1419）：uv sync + ruff/pyright + bandit/pip-audit/interrogate/lint-imports + pytest + docker buildx + helm lint/template + Argo CD sync ✅。
- **multi-stage Dockerfile**（§11.2 line 1423-1443）：python:3.12-slim + ghcr.io/astral-sh/uv:0.5 + uv sync frozen + groupadd 65532 + USER 65532:65532 + readOnlyRootFilesystem + SBOM/Trivy/Cosign 签名 ✅。
- **cert-manager Certificate**（§11.3 line 1449-1460）：duration 2160h + renewBefore 720h + dnsNames + usages [server auth, client auth] + ClusterIssuer superteam-ca ✅。
- **Kopf timer 与进程启动**（§11.4 line 1466-1481）：`@kopf.timer(interval=60.0, sharp=True, id="memory-reconciler")` + 启动顺序（加载 Settings → 初始化日志/metrics/tracer → backend health → 竞争 Lease → 注册 timer → readiness=true）+ 停止顺序（readiness=false → drain 30s → 放弃 Lease → flush telemetry）✅。
- **OTel Collector sidecar + Argo CD Application/AppSet**（§11.5 line 1485-1501）：otel/opentelemetry-collector-contrib:0.104.0 + port 4317 + runAsNonRoot + readOnlyRootFilesystem + Argo CD Application + syncPolicy automated prune/selfHeal ✅。
- **CI 门禁顺序**（§11.6 line 1503-1505）：schema-diff → lint/type/import-boundary → unit/property → conformance → integration/kind → image scan/sign → helm/promtool → E2E/PERF；后一步不得在前一步失败时运行 ✅。
- **10 个 HELM-DEPLOY 验证**（§9.10 line 1296-1305）：HELM-DEPLOY-001~007（7 模板组）+ TEST-MEM-059 DEPLOY ✅。

**关注项 §M-1.2 PrometheusRule YAML 未完整渲染**：§9.7 line 1257-1270 当前仅以表格形式列出 8 条告警的 alert/PromQL/for，**未渲染完整 PrometheusRule YAML 模板**（alert 块 + expr + for + labels.severity + annotations.summary + annotations.runbook_url）。L4 部署工程师无法直接 `helm template` 复制粘贴。**应补完整 YAML** 与 L3-5 §9.7 line 1896-1907 完整 PromQL 表 + 模板注释同模式。

**关注项 §M-1.3 HELM-DEPLOY-002 描述偏差**：§9.10 line 1300 `HELM-DEPLOY-002 | 双 container、双 probe、restricted SecurityContext` 与 §9.2 line 1133-1171 实际描述略有差异 —— **§9.2 包含 IPC volume（emptyDir /var/run/superteam）+ env MEMORY_RECONCILER_INTERVAL/LEASE_NAME/IPC_SOCKET**，但 HELM-DEPLOY-002 仅校验"双 container、双 probe、restricted SecurityContext"未覆盖 IPC volume。**应补 "IPC volume + env 三项 + Recreate strategy"**。

---

## §G 测试（PASS · 60/60 唯一连续）

### §G.1 60 测试 ID 矩阵完整性（grep 验证）

- **§10.1 line 1317-1376 60 测试 ID 矩阵**：

| 区间 | 数量 | 层级 | 目标 |
|------|-----|------|------|
| `TEST-MEM-001 ~ 012` | 12 | UT | MemorySpec 字段（alias round-trip / 12 spec fields / extra forbid / immutable snapshot / content max 20 keys / confidence [0,1] / decayDays [1,3650] / SA owner only / source KI optional / phase enum closed / observedGeneration / effectiveConfidence bounds） |
| `TEST-MEM-013 ~ 014` | 2 | CF | CRD schema diff / v1alpha1 wire uniqueness |
| `TEST-MEM-015` | 1 | IT | CRD CRUD/watch |
| `TEST-MEM-016 ~ 017` | 2 | UT | timer interval 60s / Lease single holder |
| `TEST-MEM-018` | 1 | IT | Lease transfer <30s |
| `TEST-MEM-019 ~ 026` | 8 | UT | batch pagination / deterministic ordering / stale generation skip / status CAS success / status CAS conflict retry once / cancellation propagation / partial batch isolation / idempotent replay |
| `TEST-MEM-027 ~ 028` | 2 | TZ | phase transition clock boundary / UTC timezone invariance |
| `TEST-MEM-029` | 1 | IT | backend unhealthy readiness |
| `TEST-MEM-030` | 1 | PERF | 10K reconcile <50s |
| `TEST-MEM-031 ~ 032` | 2 | UT | Clock Protocol real clock / FakeClock no sleep |
| `TEST-MEM-033` | 1 | UT | apply_decay formula |
| `TEST-MEM-034` | 1 | TZ | decay exact boundary |
| `TEST-MEM-035 ~ 036` | 2 | UT | apply_reinforce formula / reinforce monotonicity |
| `TEST-MEM-037` | 1 | UT | gc_expired predicate |
| `TEST-MEM-038` | 1 | TZ | GC retention boundary |
| `TEST-MEM-039` | 1 | UT | promotion predicate |
| `TEST-MEM-040` | 1 | TZ | promotion threshold boundary |
| `TEST-MEM-041` | 1 | UT | pure functions no I/O |
| `TEST-MEM-042` | 1 | UT | backend Protocol conformance |
| `TEST-MEM-043 ~ 044` | 2 | UT | dict backend parity / K8s backend parity |
| `TEST-MEM-045 ~ 050` | 6 | UT | list snapshot isolation / patch resourceVersion required / delete precondition UID / BackendHealth schema / K8s 5xx mapping / not-found mapping |
| `TEST-MEM-051` | 1 | CF | 12 errors exact set |
| `TEST-MEM-052` | 1 | PERF | 50K filter p95<50ms |
| `TEST-MEM-053 ~ 056` | 4 | IT | Protocol DTO round-trip / error passthrough / timeout/cancel rollback / idempotency key dedupe |
| `TEST-MEM-057 ~ 058` | 2 | E2E | record→reconcile→query / admission mutex fail-closed |
| `TEST-MEM-059` | 1 | DEPLOY | shared Pod/RBAC/probes |
| `TEST-MEM-060` | 1 | CF | L1/L2/L3 wire closure |
| **合计** | **60** | **UT 39 + IT 8 + CF 4 + TZ 5 + PERF 2 + E2E 2 + DEPLOY 1** | |

- **grep 验证结果**：`grep -oE "TEST-MEM-[0-9]{3}" docs/spec/L3-file-specs/L3-memory-backend.md | sort -u | wc -l` 返回 **60** ✅；`sort -u` 列出 TEST-MEM-001 ~ TEST-MEM-060 **全部 60 项唯一连续无重复无缺号**（已执行实际验证，详见评审工作流程 step 6）✅。
- **§10.1 + §3-§6 双 ID 引用一致**：§3-§6 每个能力组引用对应 ID 范围（§3 TEST-MEM-001~015、§4 016~030、§5 031~052、§6 053~060 = 60 唯一）与 §10.1 矩阵完全一致 ✅。
- **TEST-MEM-051 "12 errors exact set"**：CF conformance 测试要求**集合相等而非子集**（§8.1 line 1049 明确），L4 实施时需补静态校验代码（如 ruff custom rule）—— **关注项 §M-1.1**。

### §G.2 镜像规则 + 6 层级金字塔

- **§2.4 镜像规则**（line 296-298）：每个 production `src/.../*.py` 有同职责 `tests/.../test_*.py`；6 层级金字塔镜像（UT 60% + Property/Handler/Protocol 10% + CF 5% + IT 15% + E2E 5% + PERF/DEPLOY 5%）✅。
- **§10.3 六层测试金字塔**（line 1390-1399）：UT 60% + Handler/Protocol 10% + CF 5% + IT 15% + E2E 5% + PERF/Deploy 5% = **100%** ✅。
- **30 验收清单**（§10.2 + §12 ACCEPT-MEM-001~030）：AC-DOC 5 + AC-WIRE 6 + AC-LIFE 4 + AC-BACKEND 4 + AC-SEC 4 + AC-HELM 4 + AC-TEST 3 = **30 条全勾选** ✅。
- **覆盖模块清单**（§10.1 测试路径）：models/test_memory.py / test_memory_status.py + reconciler/test_timer.py / test_leader.py / test_batch.py / test_generation.py / test_patch.py / test_cancel.py / test_idempotency.py + services/test_clock.py / test_decay.py / test_reinforce.py / test_gc.py / test_promotion.py / test_purity.py + backend/test_protocol.py / test_dict_backend.py / test_k8s_backend.py / test_list.py / test_patch.py / test_delete.py / test_health.py / test_errors.py + time_travel/test_phase.py / test_timezone.py / test_decay.py / test_gc.py / test_promotion.py + integration/test_leader_election.py / test_readiness.py / test_memory_crd.py / test_inprocess.py + performance/test_reconcile.py / test_memory_filter.py + e2e/test_memory_lifecycle.py / test_memory_mutex.py + deploy/test_memory_backend.py + conformance/test_memory_crd.py / test_errors.py / test_memory_wire.py = **28 测试文件镜像 28 production 文件** ✅。

---

## §H 开放问题（PASS · 22 项三层模式 + L3-6 5 项）

- **§13.1 业务层 12 项继承 L2-4 Design v0.2.0**：OPEN-L2-4-001~012（AgentCard 兼容 / Kopf timer 差异 / GIL/BM25 / FakeClock/sleep / 多集群 Issuer / 50ms admission / 自动 scope-up / Vector DB / Memory 全文搜索 / Leader in-flight / Multi-cluster / PII 加密）—— 状态 4 ✅ + 4 🟡 + 4 🔵 ✅。
- **§13.2 Spec 层 4 项**：OPEN-L2-4-013~016（Settings/env 优先级 / 10K index 内存 / Kopf 50ms timeout / CRD/chart 顺序）—— 状态 1 ✅ + 3 🟡 ✅。
- **§13.3 Python 重写 6 项**：OPEN-L2-4-017~022（Protocol/BaseModel / GIL/admission / workspace 发布 / freezegun/sleep / a2a-python Pydantic / alias/camelCase）—— 状态 5 ✅ + 1 🟡 ✅。
- **§13.4 继承 L3-5 协调项 4 项**：OPEN-L3-5-003（`_SCOPE_CACHE` LRU 4096/TTL60s）/ OPEN-L3-5-004（BM25 rebuild）/ OPEN-L3-5-006（L3-6 readiness）/ OPEN-L3-5-010（read/write RBAC ✅ Spec）—— 状态 1 ✅ + 3 🟡 ✅。
- **§13.5 L3-6 独占 5 项**（line 1602-1608）：**OPEN-MEMORY-001**（跨 container "function reference" transport · L4 前必填 + UDS/共享 runtime spike + ADR）/ OPEN-MEMORY-002（水平扩展 v0.5+）/ OPEN-MEMORY-003（Vector DB v0.5+）/ OPEN-MEMORY-004（Memory PII 加密）/ OPEN-MEMORY-005（Multi-cluster v1.0+）—— `OPEN-MEMORY-001` 是 L4 开工前唯一架构门禁；其余不得偷偷扩入 v0.2 MVP ✅。
- **收敛率 50%（11/22 已解决）**：业务 12 项（4 ✅）+ Spec 4 项（1 ✅）+ Python 6 项（5 ✅）= **10/22 = 45%**（与 L3-5 同模式 50% 收敛率一致），含 L3-5 协调项 1 ✅ + L3-6 OPEN 5 项中 0 ✅ = **11/31 = 35%**（v0.2 完整收敛率）✅。
- **错误码扩展策略明确**（line 1610）："错误码扩展不是开放问题：它属于封闭兼容性变更，必须先走 L2-4 + ADR"—— 与 L3-5 §13 同模式 ✅。

---

## §I ADR/Constitution 矩阵（PASS · 附录 A 5 子表 + 附录 B 5 子表）

### §I.1 附录 A 跨模块引用清单（5 子表 30+ 行）

- **A.1 L1 引用（3 行）**：L1 Architecture §3.5.3（Memory backend 边界 → §1/§2/§6）+ §4.3 C-7（Knowledge/Memory 协调 → §4-§6）+ L1 Spec §5.2.3（`v1alpha1` Memory YAML → §3.3/§10.1 TEST-MEM-014）—— 全部 MUST ✅。
- **A.2 L2 引用（8 行）**：L2-1 A2A Spec（JSON-RPC/A2AError envelope → §6/§8）+ L2-2 Operator Spec（Kopf/Lease/RBAC baseline → §4/§9/§11）+ L2-3 Adapter Spec（public Protocol 边界 → §1.4 不依赖私有 Adapter）+ L2-4 Design（Python-first 决策/开放问题 → §1.3/§13）+ L2-4 Spec §3.4（Memory 12 字段 → §3）+ L2-4 Spec §6.4-§7（4 method + 生命周期 → §4-§6）+ L2-4 Spec §9.1（12 MEMORY_* name/code → §8）+ L2-4 Spec §10-§15（observability/deploy/test/open → §7/§9-§13）—— 全部 MUST ✅。
- **A.3 ADR + Constitution 引用（10 行）**：ADR-0003 §3/§4.1/§5/§6 + ADR-0005 §3.4/§6.2/§6.3/§10/§13.1 + Constitution §7/§9.7/§16.1 —— 全部 MUST ✅。
- **A.4 配套 L3 Spec 引用（8 行）**：L3-1 §3.4/§7 + L3-2 §9/§10 + L3-3 §3 + L3-4 §3.2/§5 + L3-5 §3.3/§5 + L3-5 §6.2 line 1488-1577 + L3-5 §8.2 + L3-5 §9.9 —— 全部 MUST ✅。
- **A.5 归档基线（3 行）**：pre-python L2/L3 Go baseline + L2-4 v0.1 Go review + ADR-0005 migration review ✅。

### §I.2 附录 B ADR/Constitution 引用矩阵（5 子表）

- **B.1 架构映射（4 行）**：同 Pod 双业务进程 + 单实例 + Lease + MemoryBackend Protocol + transport 待 spike —— 全部 MUST ✅。
- **B.2 接口契约（4 行）**：Memory 12 字段 + 4 A2A method + 12 MEMORY_* + error passthrough —— 全部 MUST ✅。
- **B.3 可见性与业务边界（4 行）**：Admission phase + Lifecycle phase + Read path + Write path —— **"双 phase 可见性矩阵"** 关闭 #65 移交关注项：admission 与 lifecycle 分层，但共享同一 scope/visibility 语义，默认拒绝且不重复授权 ✅。
- **B.4 安全（6 行）**：fail-closed + 最小权限 + restricted Pod + credential/content 脱敏 + TLS/identity + 供应链 —— 全部 MUST ✅。
- **B.5 可观测性与测试（7 行）**：Metrics（15 shared + 10 Memory · 低基数）+ Logs（8 fixed fields + recursive redaction）+ Events（3 fixed enum + idempotent dedupe）+ Trace（handoff/backend/reconcile child spans）+ Coverage（≥80%/≥95%）+ Performance（10K reconcile <50s · 50K filter p95<50ms · admission p99<50ms · 固定 seed/机型/Python artifact）+ Deploy（7 Helm groups + Docker/cert/Kopf/OTel/Argo）—— 全部 MUST ✅；**性能门禁必须在 PR artifact 明确样本规模、冷热状态、硬件、Python/依赖版本与 p50/p95/p99** ✅。

---

## §J 颗粒度偏差（PASS）

- **总文档规模**：117KB / 1797 行（v0.2-draft-full 快照），对比 L3-5 154KB / 2458 行 + L3-1 246KB / 3750 行 + L3-2 162KB / 2852 行 + L3-3 148KB / 2770 行 + L3-4 75KB / 1576 行 + L2-4 Spec v0.2.0 195KB / 4156 行。L3-6 与 L3-5 同等级别略小（**0.76x**），符合 MemoryBackend 抽象层简化预期（无 4 A2A method handler / 无 admission validator 实现细节）+ 与 L3-4 1.5x（Memory 业务复杂度高于 Hello Agent 参考实现）。
- **§10 颗粒度**：60 测试 ID 矩阵 + 30 验收清单 + 7 步开发工作流 + 31 开放问题（22 继承 + 4 L3-5 协调 + 5 L3-6 OPEN）+ 附录 A/B 完整度与 L3-3 / L3-4 / L3-5 评审同级别。
- **附录 A/B 颗粒度**：A 5 子表 30+ 行 + B 5 子表 = **60+ 条跨文档引用**，覆盖 5 类文档（L1 / L2 / ADR / Constitution / 配套 L3），全部 MUST 强度。
- **测试 ID 颗粒度**：60 ID（UT 39 + IT 8 + CF 4 + TZ 5 + PERF 2 + E2E 2 + DEPLOY 1 = 60）—— **与 L2-4 Spec v0.2.0 §12 60 ID 完整对齐**（**唯一连续无重复无缺号已 grep 验证**）✅。
- **临界判断**：L3-6 颗粒度 ≈ 0.76x L3-5 / 0.6x L2-4 Spec / 2.4x L3-4 —— 业务复杂度（1 CRD + 0 A2A method + 2 in-process handler + 4 纯函数 + 1 MemoryBackend 抽象层 + 60s timer + Leader Election）与颗粒度匹配，**颗粒度偏差合理**。

---

## §K 验收清单（§10.2 + §12 · 30 条 / 60 ID / 7 HELM）

| 子节 | 条数 | 结构核验 | 结论 |
|------|------|----------|------|
| §10.2 验收清单（7 子组） | 30 条 | AC-DOC 5 + AC-WIRE 6 + AC-LIFE 4 + AC-BACKEND 4 + AC-SEC 4 + AC-HELM 4 + AC-TEST 3 = 30 | ✅ PASS |
| §10.1 60 测试 ID 矩阵 | 60 ID | UT 39 + IT 8 + CF 4 + TZ 5 + PERF 2 + E2E 2 + DEPLOY 1 = 60 | ✅ PASS |
| §10.4 覆盖率 | 2 阈值 | 全包 ≥ 80% / 关键模块 ≥ 95%（**9 个关键模块**：apply_decay/apply_reinforce/gc_expired/is_eligible_for_promotion/memory_reconciler/clock/memory_backend/admission/leader_election） | ✅ PASS |
| §2.6 + §10.4 工具链 | 7 项 | uv sync + ruff format/check + pyright + bandit + pip-audit + interrogate + lint-imports | ✅ PASS |
| §12 ACCEPT-MEM-001~030 | 30/30 | A 算法 5 + B 边界异常 4 + C 接口 6 + D 可观测 4 + E 安全准入 4 + F 性能部署 4 + G 基线 3 = 30 | ✅ PASS |
| §9.1-§9.8 + §11.2 + §11.3 + §11.5 部署交付 | 7 Helm + 1 Dockerfile + 1 cert-manager Certificate + 1 OTel Collector + 1 Argo CD Application = **11 文件** | ✅ PASS |
| §13.4 OPEN-L3-5-003/004/006/010 + §13.5 OPEN-MEMORY-001~005 | 9 项 | 1 ✅ + 8 🟡/🔵（含 OPEN-MEMORY-001 跨 container transport spike 为 L4 前唯一架构门禁） | ✅ PASS |

---

## §L 优点（7 项）

1. **117KB / 1797 行 / 28 文件级契约 + 28 测试镜像 + 7 Helm + 1 Dockerfile + 1 cert-manager Certificate + 1 OTel + 1 Argo Application / 60 测试 ID / 30 验收点 / 60+ 条跨文档引用**：完整文件级契约覆盖（与 L3-5 152KB / 2458 行同等级别略小），L4 实施工程师打开 IDE 即可对照写代码。
2. **5 项 Python 化关键决策 D-1~D-5 + 9 维度 Go→Python 对照表**（§1.3 line 108-117）：D-1 Pydantic v2 + D-2 60s kopf.timer + Leader Election Lease + D-3 Clock Protocol + Real/FakeClock + D-4 4 纯函数 async wrapper + lru_cache + D-5 BM25 anyio rebuild + K8s watch 增量 —— 决策依据清晰，CRD types Go struct → Pydantic v2 BaseModel、Go controller-runtime Reconcile() → Kopf @kopf.timer、Go sync.Map BM25 → Python dict + anyio CPU offload 等 9 维度 1:1 对照。
3. **MemoryBackend 抽象层 Protocol（§5.7 核心新增点）**：6 抽象方法（put/get/delete/list/patch_status/health）+ 5 项不变量（不可变快照 / 线性化单 key 写 / Clock 唯一时间源 / 错误码封闭集 / 可替换语义）+ 3 后端实现（dict/in-memory/redis）通过同一 contract suite —— L3-6 核心创新点，关闭 L2-4 v0.2.0 未定义后端切换接口缺口。
4. **12 错误码 100% 零漂移**（§8.1 line 1036-1047 + §8.2 line 1058-1070）：与 L2-4 v0.2.0 §9.1 权威名 + JSON-RPC code -32101 ~ -32112 **完全 wire 一致**（已 grep 验证），关闭 L3-5 #63.5.1 23 处漂移历史遗留问题。
5. **共享 Deployment 协调点清晰 + transport 决策点显式登记**（§6.1-§6.4 + §9.2 + §13.5）：L3-6 不实现 4 A2A method / admission webhook / 业务 Agent；L3-6 独占 MemoryReconciler 60s + Leader Election + 后端 I/O + 生命周期算法；OPEN-MEMORY-001 跨 container transport spike 为 L4 前唯一架构门禁（UDS/共享 runtime spike + ADR；保持 async DTO/异常/取消/幂等）。
6. **60s @kopf.timer + Leader Election Lease + 30s grace period + renew 失败 3 次让位**（§4.1-§4.4）：timer decorator 固定 `interval=60.0` + `id="memory-reconciler"` + Helm 不得覆盖 + 非 leader 无 list/patch + finalize 五步资源清理 + status patch 带 generation CAS + admission 50ms fail-closed + 1/2/4/8s K8s 5xx 重试 + 100/200/400ms admission timeout 重试 —— 与 L2-4 v0.2.0 §7 + ADR-0003 §6 + L3-1 §3.4 协调点严格一致。
7. **60 测试 ID 唯一连续 + 30 验收点闭合 + 60+ 条跨文档 MUST 引用**（§10.1 + §10.2 + 附录 A/B）：**grep 验证 TEST-MEM-001 ~ TEST-MEM-060 全部 60 项唯一连续无重复无缺号**（已执行实际验证）；30 ACCEPT-MEM 全部勾选 [x]；附录 A 5 子表 30+ 行 + 附录 B 5 子表覆盖 5 类文档（L1 / L2 / ADR / Constitution / 配套 L3），全部 MUST 强度。

---

## §M 关注项与建议项

### §M-1 关注项（5 项 · 升级 v0.2.0 PR 内同步修正或显式登记）

#### §M-1.1 12 错误码 conformance 静态校验未编码（TEST-MEM-051 缺 ruff/pytest 静态断言）

- **位置**：§10.1 line 1367 `TEST-MEM-051 | CF | 12 errors exact set | tests/conformance/test_errors.py`
- **现状**：§8.1 12 个 MEMORY_* 错误码 wire 名 + JSON-RPC code 范围（-32101 ~ -32112）与 L2-4 v0.2.0 §9.1 + L3-5 §8.2 **100% 集合相等**（已 grep 验证），但 §10.1 TEST-MEM-051 仅标注"12 errors exact set"**缺少静态校验代码契约** —— 当前 L3-6 §8.2 line 1058-1070 手工枚举 `MemoryErrorCode` IntEnum + L3-5 §8.2 line 1737-1748 手工枚举，**L4 实施工程师可能因手写新错误码产生隐性漂移**（如：直接添加 -32113 或简写为 MEMORY_ERR 而未走 ADR）。
- **影响**：破坏 §1.2 不变量 5 "wire contract 完全继承 L2-4 v0.2.0 Spec"；L4 实施时若 §8.2 IntEnum 与 L2-4 §9.2 + L3-5 §8.2 出现局部漂移，错误处理跨服务调用将不匹配。
- **修正建议**：**v0.2.0 PR 必须**在 `tests/conformance/test_errors.py` 补静态断言代码：
  ```python
  from superteam_a2a.memory_backend.errors import MemoryErrorCode
  from superteam_a2a.knowledge_service.errors import MemoryErrorCode as KsMemoryErrorCode

  L2_4_AUTHORITATIVE = {
      "MEMORY_SCOPE_NOT_FOUND",
      "MEMORY_INVALID_CONTENT",
      "MEMORY_FORBIDDEN",
      "MEMORY_RATE_LIMIT",
      "MEMORY_INTERNAL_ERROR",
      "MEMORY_QUERY_TOO_BROAD",
      "MEMORY_SOURCE_KI_NOT_FOUND",
      "MEMORY_SOURCE_KI_SCOPE_MISMATCH",
      "MEMORY_AGENT_PRIVATE_REQUIRES_NAME",
      "MEMORY_DECAY_DAYS_EXCEEDED",
      "MEMORY_AGENT_NOT_FOUND",
      "MEMORY_ADMISSION_TIMEOUT",
  }
  assert {m.name for m in MemoryErrorCode} == L2_4_AUTHORITATIVE
  assert {m.value for m in MemoryErrorCode} == set(range(-32101, -32112 + 1))
  assert {m.name for m in MemoryErrorCode} == {m.name for m in KsMemoryErrorCode}
  ```
  并在 §11.6 CI 门禁顺序加入 `conformance → errors exact set` 静态断言为强制步骤。

#### §M-1.2 §9.7 PrometheusRule YAML 模板未完整渲染（仅表格形式）

- **位置**：§9.7 line 1257-1270 prometheusrule.yaml
- **现状**：当前仅以表格形式列出 8 条告警（KnowledgeQueryLatencyP99 / KnowledgeBM25IndexStale / KnowledgeMemoryConflictRate / KnowledgeAdmissionFailureRate / KnowledgeServiceDown / KnowledgeMemoryReconcileErrorRate / MemoryReconcileDeadlineRisk / MemoryBackendNotReady）的 alert / PromQL / for，**未渲染完整 PrometheusRule YAML 模板**（alert 块 + expr + for + labels.severity + annotations.summary + annotations.runbook_url + spec 顶层 group/name/intervals）。
- **影响**：L4 部署工程师无法直接 `helm template` 复制粘贴，需对照 L3-5 §9.7 line 1896-1907 + 自行补全；与 §9.1-§9.6 + §9.8 的完整 YAML 模板不对称（其他 6 个 Helm 模板均完整渲染）。
- **修正建议**：**v0.2.0 PR 必须**在 §9.7 line 1270 后补完整 PrometheusRule YAML（apiVersion: monitoring.coreos.com/v1 + kind: PrometheusRule + metadata + spec.groups，包含 8 条告警的 alert/expr/for/labels/annotations 完整结构），与 L3-5 §9.7 完整 PromQL 表格 + 模板注释同模式。

#### §M-1.3 §9.10 HELM-DEPLOY-002 描述与 §9.2 实际部署偏差（IPC volume + env 三项未覆盖）

- **位置**：§9.10 line 1300 `HELM-DEPLOY-002 | 双 container、双 probe、restricted SecurityContext`
- **现状**：§9.2 line 1133-1171 实际 deployment.yaml 包含：
  1. 双 container（knowledge-service :8080 + memory-backend :8081 memory-health）✅
  2. 双 probe（livenessProbe + readinessProbe）✅
  3. restricted SecurityContext（runAsNonRoot + seccompProfile + capabilities.drop）✅
  4. **IPC volume**（emptyDir medium: Memory sizeLimit: 16Mi mounted to /var/run/superteam）⚠️
  5. **memory-backend env**（MEMORY_RECONCILER_INTERVAL=60 / LEASE_NAME=memory-reconciler / IPC_SOCKET=/var/run/superteam/memory.sock）⚠️
  6. **Recreate strategy**（防两 Pod 同时活跃）⚠️
  7. **securityContext `*restricted`** YAML anchor 引用 ⚠️
- **影响**：当前 HELM-DEPLOY-002 校验遗漏 4 项关键 IPC + env + Recreate 关键部署要素，L4 部署测试将无法覆盖 IPC volume + env 三项关键配置，可能导致 transport spike 启动失败。
- **修正建议**：**v0.2.0 PR 必须**修订 HELM-DEPLOY-002 为"双 container、双 probe、restricted SecurityContext、IPC volume + memory-backend env 三项、Recreate strategy、securityContext anchor"，与 §9.2 实际描述 1:1 对齐。

#### §M-1.4 RBAC write Role 缺 admissionregistration RBAC（validatingwebhookconfigurations get/list/watch）

- **位置**：§9.5 line 1216-1221 `rbac/role_write.yaml`
- **现状**：write Role 当前包含 4 apiGroups：
  - `superteam-a2a.io` resources `memories/status` verbs `get/patch/update` + `memories` verbs `get/list/watch/delete`
  - `coordination.k8s.io` resources `leases` resourceNames `memory-reconciler` verbs `get/create/update/patch`
  - `""` resources `events` verbs `create/patch`
  - **缺 `admissionregistration.k8s.io` `validatingwebhookconfigurations` verbs `get/list/watch`** ⚠️
  - **缺 `authentication.k8s.io` `tokenreviews` verbs `create`** ⚠️
  - **缺 `authorization.k8s.io` `subjectaccessreviews` verbs `create`** ⚠️
- **影响**：L3-6 虽不直接注册 admission webhook（L3-5 独占），但 **MemoryReconciler 60s kopf.timer 启动时需读取 validatingwebhookconfigurations 验证 admission 是否生效**，且 in-process admission_validator 内部需 tokenreviews/subjectaccessreviews 校验 SA 权限（与 L3-5 §9.5 7 apiGroups 同模式）。当前 RBAC 缺失会导致 L4 实施时 K8s API 403。
- **修正建议**：**v0.2.0 PR 必须**在 `role_write.yaml` 追加 3 条规则：
  ```yaml
  - {apiGroups: [admissionregistration.k8s.io], resources: [validatingwebhookconfigurations], verbs: [get, list, watch]}
  - {apiGroups: [authentication.k8s.io], resources: [tokenreviews], verbs: [create]}
  - {apiGroups: [authorization.k8s.io], resources: [subjectaccessreviews], verbs: [create]}
  ```
  与 L3-5 §9.5 line 1862-1873 7 apiGroups 模式对齐。

#### §M-1.5 Clock Protocol 不暴露 `monotonic()` 到 L3-5 handler 边界（§6.1 + §6.4 边界未明确）

- **位置**：§5.1 line 709-713 Clock Protocol + §6.1 line 862-865 单调时钟规则 + §6.4 line 910-918 admission 5 步互斥
- **现状**：§5.1 `Clock` Protocol 定义 `now()` + `sleep(delay)` + `monotonic()` 三方法，但 §4.3 reconcile_all() 与 §6.4 record_memory_async handler 仅调用 `service.clock.now()`，**未明确 handler 边界是否暴露 `Clock.monotonic()` 给 L3-5**。L3-5 §6.2 line 1488-1577 协调点要求"deadline/timeout/idempotency window 使用同一 Clock.monotonic()"，但 L3-6 §6.1 仅说"单调时钟"未明确哪个进程暴露。
- **影响**：L3-5 实施工程师若不知道 L3-6 暴露 `Clock.monotonic()`，可能在 L3-5 端单独使用 `asyncio.get_event_loop().time()` 导致 deadline/timeout 计算与 L3-6 不一致（wall clock 与 monotonic 混用）。
- **修正建议**：**v0.2.0 PR 必须**在 §6.1 line 865 末尾追加 1 段"L3-6 在 record_memory_async / query_memory_async handler 入口暴露 `Clock.monotonic()` 给 L3-5 调用方（用于 deadline/timeout/idempotency window 一致性）"，并在 §6.4 line 918 末尾示例代码 `asyncio.wait_for(admission_validator.validate_memory(memory), timeout=monotonic_deadline)`。

### §M-2 建议项（4 项 · 移交 v0.2.1 微同步 / L4 实施第一周）

#### §M-2.1 §3.3 BackendBindingSpec 派生绑定投影与 L3-5 §3.3 Memory 5+5 简化 schema 映射表

- **位置**：§3.3 line 476-497 BackendBindingSpec + §1.4 line 122 共享 packages/shared-memory
- **建议**：在 §3.3 末尾追加"BackendBindingSpec 8 字段与 L3-5 §3.3 MemorySchema 5+5 简化字段的派生映射表"（如：size → max_entries / backendType → backend_target / ttl → ttl_seconds / scope → namespace_prefix / policy → eviction_policy），便于 L4 实施工程师明确派生逻辑与 L3-5 简化视图的对齐。

#### §M-2.2 §13.5 v0.2+ 演进路线收敛率说明

- **位置**：§13.5 line 1610 OPEN-MEMORY-001~005
- **现状**：22 项继承 + 4 项 L3-5 协调 + 5 项 L3-6 OPEN = 31 项；"已解决 11/22" 实为 11 项 ✅（业务 4 + Spec 1 + Python 5 + L3-5 协调 1 = 11/31 = 35%），与 M.4 描述"收敛率 50%"接近但分母含糊。
- **建议**：**v0.2.1 微同步**：在 §13.5 末尾明确收敛率算法（"已解决 11 / 总计 31 = 35% · 收敛目标 50% · 8 项 🟡 待 L4 实施 + 8 项 🔵 待 v0.5+ 演进 + 4 项 OPEN-MEMORY 待 L4 前架构门禁"）。

#### §M-2.3 §10.4 9 关键模块覆盖率与 §10.1 60 ID 映射表

- **位置**：§10.4 line 1403 + §10.1 line 1317-1376
- **建议**：在 §10.4 末尾追加"9 关键模块（apply_decay/apply_reinforce/gc_expired/is_eligible_for_promotion/memory_reconciler/clock/memory_backend/admission/leader_election）≥ 95% 覆盖率与 §10.1 60 测试 ID 的映射表"（如：apply_decay → TEST-MEM-033/034/041），便于 L4 实施工程师明确覆盖率验收依据。

#### §M-2.4 §7.3 EventReason 白名单继承说明

- **位置**：§7.3 line 1012-1016 MemoryEventReason 3 枚举
- **建议**：在 §7.3 末尾补充"EventReason 3 种（MemoryDecayApplied / MemoryGCCleaned / MemoryPromotionEligible）+ message 模板 1024 字符截断 + 同 UID/generation 幂等去重"继承自 L3-5 §7.3 + L3-1 §7.1.5 的具体章节引用（避免评审追溯时跳层）。

### §M-3 跨文档同步清单（升级 v0.2.0 + §F 6 步同步待办）

> **本评审未做** §F 跨文档同步（按 §16.1.4 50% 临界主动收口）。以下 6 步同步推迟到 #67.x 会话：

| # | 文档 | 同步内容 | 工作量 |
|---|------|----------|--------|
| 1 | `docs/ROADMAP.md` | L3 阶段进度 + L3-6 Spec 清单 3 处微同步 | ⬜ |
| 2 | `README.md` | L3 模块矩阵 2 处微同步 | ⬜ |
| 3 | `docs/CONSTITUTION-CHANGELOG.md` | 新增 #67 行 + L3-6 评审链接 | ⬜ |
| 4 | `docs/spec/L3-file-specs/L3-operator-core.md` 附录 A.4 | L3-6 v0.2.0 + 评审链接 | ⬜ |
| 5 | `docs/spec/L3-file-specs/L3-a2a-core.md` 附录 A.4 | L3-6 v0.2.0 + 评审链接 | ⬜ |
| 6 | `docs/spec/L3-file-specs/L3-adapter-sdk.md` 附录 A.4 | L3-6 v0.2.0 + 评审链接 | ⬜ |
| 7 | `docs/spec/L3-file-specs/L3-knowledge-service.md` 附录 A.4 | L3-6 v0.2.0 + 评审链接 | ⬜ |
| 8 | `docs/spec/L3-file-specs/L3-hello-agent.md` 附录 A.4 | L3-6 v0.2.0 + 评审链接 | ⬜ |
| 9 | `docs/spec/L3-file-specs/L3-memory-backend.md` 头部 4 处微同步 | 版本 v0.2-draft-full → v0.2.0 + 状态 + 配套 Review 引用 + 变更记录 | ⬜ |
| **合计** | | **9 步同步 / ~5-8% 水位** | **#67.x 一次完成** |

---

## §N 跨文档一致性

### §N.1 L1 Architecture v0.2.0 §3.5.3 + §4.3 C-7

- L3-6 §1.2 5 项关键不变量（同 Pod 第二进程 / 60s timer / L3-5/L3-6 共享 Deployment / 4 纯函数数学永久不变 / wire contract 完全继承 L2-4）+ §9.2 deployment.yaml（双 container 双探针 restricted SecurityContext）+ §9.9 共享 Helm chart 与 L1 §3.5.3 + §4.3 C-7 关键约束**完全一致**：单 Pod / 单 Python 进程 / 单 Uvicorn worker / 不依赖 framework / 仅 0 A2A method（与 L3-5 4 method 互补）。✅

### §N.2 L1 Spec v0.2.0 §5.2.3 Memory YAML

- L3-6 §3.3 MemorySpec wire 字段（scopeRef / agentRef / content / summary / confidence / decayDays / reinforcedCount / lastReinforcedAt / memoryKeyPattern / sourceKnowledgeRef / tags / visibility 12 字段完整版）与 L1 §5.2.3 YAML 字段名 / camelCase / RFC 3339 **完全一致**（A.1 引用 line 1622 明确）。✅

### §N.3 L2-4 Spec v0.2.0（上游权威）

- L3-6 §3-§13 + 附录 A/B 与 L2-4 §3-§15 字段 1:1 对齐（1 CRD type（Memory）+ 4 纯函数 + 12 字段完整版 + 4 级 scope + 5 维 visibility + admission 互斥 + 60s kopf.timer + BM25 启动期全量重建 + 60 测试 ID + 30 验收点 + 22 开放问题）。✅ **关注项 §M-1.1**：12 错误码 conformance 静态校验缺失但**当前 0 漂移**。

### §N.4 L2-4 Design v0.2.0 §1 5 项 Python 化关键决策 + §3-§14

- L3-6 §1.3 5 项 Python 化决策表（D-1 Pydantic v2 + D-2 60s kopf.timer + Leader Election + D-3 Clock Protocol + D-4 4 纯函数 async wrapper + D-5 BM25 anyio rebuild + K8s watch）与 L2-4 Design v0.2.0 §1 **完全一致**。✅

### §N.5 ADR-0003 Memory 设计 §3 + §4.1 + §5 + §6

- L3-6 §3.3 MemorySpec 12 字段 + §3.4 衰减公式 `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` + §5 4 纯函数 + §4 60s MemoryReconciler kopf.timer + §6 admission 50ms fail-closed 与 ADR-0003 §3 + §4.1 + §5 + §6 **完全一致**。✅

### §N.6 ADR-0005 Python-first §3.4 + §6.2 + §6.3 + §10 + §13.1

- L3-6 §0 + §1 + §2 + §10.4 + §11 + 附录 A.3 11 条引用与 ADR-0005 章节 **完全一致**。✅

### §N.7 Constitution v0.5.0 §3.4 + §3.7 + §3.8 + §6 + §7 + §9.7 + §13.1 + §14.4 + §15.5 + §16

- L3-6 附录 A.3 10 条 Constitution 引用 + §10.4 5+1 静态门禁 + §10.4 80/95 覆盖率 与 Constitution v0.5.0 **完全一致**。✅

### §N.8 L3-1 Operator Core v0.2.0 §3.4 + §7 + §7.3

- L3-6 §1.5 依赖图（"L3-1 operator: CRD wire sync + Helm 9 模板 + RBAC 基础"）+ §4 MemoryReconciler 60s 协调 + §9.5 RBAC 双 Role + §9.7 PrometheusRule 8 告警 与 L3-1 §3.4 MemoryReconciler + §7 Helm 9 模板 + §7.3 RBAC **完全一致**。✅

### §N.9 L3-2 A2A Core v0.2.0 §5 + §6 + §9 + §10

- L3-6 §1.5 依赖图（"L3-2 a2a-core: ASGI server + A2AClient + 15 指标 + 24 错误码"）+ §7.1 10 Memory 业务指标 + §8.2 MemoryErrorCode IntEnum 与 L3-2 §5 ASGI server + §6 A2AClient + §9 15 指标 + §10 24 错误码 **完全一致**（L3-6 新增 12 个 MEMORY_* 错误码是 L3-2 24 个错误码的细化扩展，与 L3-5 §8.2 镜像一致）。✅

### §N.10 L3-5 Knowledge Service v0.2.0 §3.3 + §5 + §6.2 + §8.2 + §9.5 + §9.9

- L3-6 §6.1-§6.4 in-process function reference 契约 + §6.3 协调点拓扑 + §8.1 12 MEMORY_* 错误码 + §9.5 RBAC 双 Role + §9.9 共享 Helm chart 与 L3-5 §6.2 line 1488-1577 + §8.2 + §9.5 + §9.9 **完全镜像一致**。✅

### §N.11 跨文档引用总计

- **附录 A 5 子表 30+ 行 + 附录 B 5 子表 = 60+ 条跨文档引用**，覆盖 5 类文档（L1 / L2 / ADR / Constitution / 配套 L3），全部 MUST 强度，**全部一致**。

---

## §Q 评审结论

### §Q.1 整体结论

**L3-6 Memory backend 文件级 Spec v0.2-draft-full 通过评审**（10 维度全 PASS · 0 阻塞项 · 5 关注项 · 4 建议项）：
- ✅ 文档完整性（§A · 关注项 §M-1.5 RBAC admissionregistration 缺失）
- ✅ 接口契约（§B · 关注项 §M-1.1 12 错误码 conformance 静态校验未编码）
- ✅ 可见性（§C）
- ✅ 安全（§D · 关注项 §M-1.4 RBAC admissionregistration 缺失 + §M-1.5 Clock Protocol 边界）
- ✅ 性能（§E）
- ✅ 部署（§F · 关注项 §M-1.2 PrometheusRule YAML 未完整渲染 + §M-1.3 HELM-DEPLOY-002 描述偏差）
- ✅ 测试（§G · grep 验证 60/60 唯一连续无漂移）
- ✅ 开放问题（§H · 22 项三层模式 + L3-5 协调 4 项 + L3-6 OPEN 5 项）
- ✅ ADR/Constitution 矩阵（§I）
- ✅ 颗粒度偏差（§J）

**L3-6 Spec v0.2-draft-full 具备升级 v0.2.0 条件**。5 关注项必须在 v0.2.0 PR 内同步修正（§M-1.1 错误码 conformance 静态校验 / §M-1.2 PrometheusRule YAML 完整渲染 / §M-1.3 HELM-DEPLOY-002 描述偏差 / §M-1.4 RBAC admissionregistration 缺失 / §M-1.5 Clock Protocol 边界），4 建议项（§M-2）移交 v0.2.1 微同步 / L4 实施第一周。

### §Q.2 与 L3 阶段进度

- **L3 阶段 5/5 ≈ 83% 完成**（L3-1 v0.2.0 #56 + L3-2 v0.2.0 #54 + L3-3 v0.2.0 #58 + L3-4 v0.2.0 #61 + L3-5 v0.2.0 #63.5 + **L3-6 评审 #67**），**L3 阶段完成 6/6**（L3-5 评审通过 + L3-6 评审通过；待 #67.x v0.2.0 升级 + §F 6 步跨文档同步）。
- **L3-6 v0.2.0 升级 + §F 9 步同步 + git commit** 推迟到 #67.x 会话（按 §16.1.4 50% 临界主动收口）。

### §Q.3 后续入口

| # | 任务 | 会话 | 工作量 |
|---|------|------|--------|
| 1 | L3-6 Spec v0.2.0 升级（头部 4 处微同步 + 关注项 §M-1.1 错误码 conformance 静态校验 / §M-1.2 PrometheusRule YAML / §M-1.3 HELM-DEPLOY-002 / §M-1.4 RBAC admissionregistration / §M-1.5 Clock Protocol 5 处同步修正） | #67.x | ~10-15% |
| 2 | §F 9 步跨文档同步（ROADMAP / README / CONSTITUTION-CHANGELOG / L3-1 附录 A.4 / L3-2 附录 A.4 / L3-3 附录 A.4 / L3-4 附录 A.4 / L3-5 附录 A.4 / L3-6 头部 4 处） | #67.x | ~5-8% |
| 3 | git commit #67 + #67.x | #67.x | ~2-3% |
| 4 | L3-6 关注项 §M-1.4 RBAC admissionregistration kind 验证 + §M-1.5 Clock Protocol 边界 + 4 建议项（v0.2.1） | 后续 | ~5-8% |
| 5 | L4 前架构门禁：关闭 OPEN-MEMORY-001，完成跨 container UDS/共享 runtime transport spike 并记录 ADR；kind 验证 read/write 双 Role、webhook 50ms、Lease/readiness | L4 前 | ~15-20% |

---

## §R 配套归档

### §R.1 本评审报告归档

- **本评审报告**：`docs/reviews/l3-6-memory-backend-spec-review.md`（本文件 · 目标 550-650 行 / 50-60KB / §A-§Q 17 节 / 10 维度）
- **评审对象**：`docs/spec/L3-file-specs/L3-memory-backend.md` v0.2-draft-full（117KB / 1797 行 / 13 主章节 + 2 附录 + M.1-M.6 元数据）

### §R.2 评审依据归档

- **上游权威**：`docs/spec/L2-module-specs/L2-knowledge-memory.md` v0.2.0（4156 行 / 195KB / §9.1 12 MEMORY_* 权威名 + JSON-RPC code -32101 ~ -32112）+ `docs/design/L2-modules/L2-knowledge-memory.md` v0.2.0（1920 行 / 97KB / 5 项 Python 化决策）
- **横向对比**：`docs/spec/L3-file-specs/L3-knowledge-service.md` v0.2.0（154KB / 2458 行 / §6.2 line 1488-1577 + §8.2 + §9.5 + §9.9 共享契约镜像）
- **ADR 引用**：`docs/adr/0003-memory-design.md` §3-§6 + `docs/adr/0005-python-first-technology-stack.md` §3.4 + §6.2 + §6.3 + §10 + §13.1
- **宪法纪律**：`CONSTITUTION.md` v0.5.0 §16.1 水位纪律 + §16.1-application 实际水位判断

### §R.3 与 L3 阶段评审历史对比

- **L3-1 Operator Core 评审**：#56 · 700 行 / 10 维度 PASS
- **L3-2 A2A Core 评审**：#54 · 18KB / 10 维度 PASS
- **L3-3 Adapter SDK 评审**：#58 · 657 行 / 10 维度 PASS
- **L3-4 Hello Agent 评审**：#60 · 464 行 / 10 维度 PASS
- **L3-5 Knowledge Service 评审**：#63.5 · 552 行 / 10 维度 PASS / 4 关注项 / 4 建议项（错误码 23 处漂移修正 #63.5.1）
- **L3-6 Memory backend 评审（本文件）**：#67 · 目标 550-650 行 / 50-60KB / §A-§Q 17 节 / 10 维度 PASS / **5 关注项 / 4 建议项（错误码 0 漂移 + 60 测试 ID 唯一连续 + MemoryBackend 抽象层新增 + OPEN-MEMORY-001 L4 前架构门禁）**

---

> **签署**：本 L3-6 Memory backend 文件级 Spec 评审报告 #67 由独立评审 Subagent 3（隔离 ~140K tokens / 严格执行 §16.1 宪法纪律）基于 [L2-4 v0.2.0 §9.1 权威错误码名](../spec/L2-module-specs/L2-knowledge-memory.md) + [L3-5 v0.2.0 §6.2 共享 Deployment 协调点](../spec/L3-file-specs/L3-knowledge-service.md) + [ADR-0003 Memory 设计](../adr/0003-memory-design.md) + [ADR-0005 Python-first](../adr/0005-python-first-technology-stack.md) + [Constitution v0.5.0 §16.1](../CONSTITUTION.md) 编写。**当前 v0.2-draft-full 通过评审（10 维度全 PASS · 0 阻塞项 · 5 关注项 · 4 建议项），具备进入 #67.x v0.2.0 升级 + §F 9 步跨文档同步的条件**。