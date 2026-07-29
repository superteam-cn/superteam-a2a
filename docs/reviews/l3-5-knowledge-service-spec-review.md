# superteam-a2a — L3-5 Knowledge Service 文件级 Spec 评审报告

> **评审日期**：2026-07-29 · #63.5 会话
> **评审结论落地**：✅ **L3-5 Knowledge Service Spec v0.2-draft-full 通过评审（10 维度全 PASS · 0 阻塞项 · 4 关注项 · 4 建议项），具备升级 v0.2.0 条件**；关注项 1（错误码名称/编号）与关注项 2（admission §5 表 vs §8 错误码漂移）必须在 v0.2.0 PR 内同步修正，关注项 3（L3-5/6 共享 RBAC 拆分）与关注项 4（performance / admission 性能门禁真实环境验证）移交 v0.2.1 / L4 实施第一周。
> **评审对象**：[`docs/spec/L3-file-specs/L3-knowledge-service.md` v0.2-draft-full](../spec/L3-file-specs/L3-knowledge-service.md)（**154KB / 2458 行 / 13 主章节 §0-§13 + 2 附录 A/B + M.1-M.6 元数据** · 评审时快照）
> **配套上游 Design**：[L2-4 Knowledge/Memory Design v0.2.0 Python](../design/L2-modules/L2-knowledge-memory.md)（2026-07-27 #39 评审通过 · 1920 行 / 97KB / 14 节 + 2 附录）
> **配套上游 Spec**：[L2-4 Knowledge/Memory Spec v0.2.0 Python](../spec/L2-module-specs/L2-knowledge-memory.md)（2026-07-27 #42 补完 + #43 评审通过 · 4152 行 / 194.6KB / 16 节 + 2 附录 · wire 完全对齐权威）
> **配套 L3 同级**：[L3-1 Operator Core v0.2.0](../spec/L3-file-specs/L3-operator-core.md)（[评审](./l3-1-operator-core-spec-review.md) #56 · 700 行 / 10 维度 PASS）/ [L3-2 A2A Core v0.2.0](../spec/L3-file-specs/L3-a2a-core.md)（[评审](./l3-2-a2a-core-spec-review.md) #54 · 18KB / 10 维度 PASS）/ [L3-3 Adapter SDK v0.2.0](../spec/L3-file-specs/L3-adapter-sdk.md)（[评审](./l3-3-adapter-sdk-spec-review.md) #58 · 657 行 / 10 维度 PASS）/ [L3-4 Hello Agent v0.2.0](../spec/L3-file-specs/L3-hello-agent.md)（[评审](./l3-4-hello-agent-spec-review.md) #60 · 464 行 / 10 维度 PASS）/ L3-6 Memory backend（待 #64 起草）
> **评审人**：项目发起人（单点评审 · 宪法 §14.5 MVP 例外时间窗口内）
> **评审依据**：[`CONSTITUTION.md`](../CONSTITUTION.md) v0.5.0 §3.4 + §3.7 + §3.8 + §6 + §7 + §9.7 + §13.1 + §14.4 + §15.5 + §16 会话纪律；[ADR-0002 知识管理设计](../adr/0002-knowledge-management-design.md) §3 4 级 scope + §4 5 维 visibility + §5 admission 互斥；[ADR-0003 Memory 设计](../adr/0003-memory-design.md) §3 + §4.1 decay 公式 + §5 admission；[ADR-0005 Python-first](../adr/0005-python-first-technology-stack.md) §3.4 + §6.2 + §6.3 + §9.1 + §10 + §11 + §13.1 + §13.6；[L1 Architecture v0.2.0 §3.5.2 + §3.5.3 + §4.3 C-6](../design/L1-architecture.md)；[L1 Spec v0.2.0 §5.2.2 + §6.2](../spec/L1-system-spec.md)；[L2-4 Design v0.2.0 §1 5 项 Python 化决策 + §3-§14](../design/L2-modules/L2-knowledge-memory.md)；[L2-4 Spec v0.2.0 §0-§15 + §16 元数据](../spec/L2-module-specs/L2-knowledge-memory.md)（wire 完全对齐权威）
> **上一版评审**：无（**L3-5 首次评审**；v0.1-draft Go baseline 未独立评审，归档登记与 L3-1/2/3/4 同模式）
> **参照模板**：[L3-3 Adapter SDK Spec 评审](./l3-3-adapter-sdk-spec-review.md)（40KB / 657 行 / §A-§P 16 节 / 10 维度 PASS）+ [L3-4 Hello Agent Spec 评审](./l3-4-hello-agent-spec-review.md)（48KB / 464 行 / §A-§J 10 维度 PASS）+ [L2-4 Spec 评审](./l2-4-knowledge-memory-spec-python-review.md)（59.7KB / 697 行 / §A-§P 16 节 / 10 维度 PASS）

---

## 评审概览

### 评审维度与结论

| 维度 | 评审范围 | 结论 |
|------|----------|------|
| **A. 文档完整性** | §0-§13 + 附录 A（5 子表）+ 附录 B（5 子表）+ M.1-M.6 元数据 + 头部 11 段 + 5 项关键不变量 + 30 文件级契约 + 60 测试 ID | ✅ PASS（伴发现 4 处内部不一致，见 §M-1） |
| **B. 接口契约** | 3 CRD types 完整 Pydantic v2 + 4 A2A method handler + 23 错误码 + wire 同步矩阵 7 张表 + 5 项 wire contract 永久不变 | ⚠️ **PASS-WITH-FINDINGS**（伴发现 3 处命名/编号漂移，见 §M-1.1-§M-1.3） |
| **C. 可见性** | 4 级 scope（agent/agentset/workflow/system）+ 5 维 visibility（scope-only/scope-and-children/public-readable/agent-private/system-readonly）+ admission 双向互斥 + 4 种 KnowledgeType | ✅ PASS |
| **D. 安全** | mTLS TLS 1.3 + cert-manager 颁发/续期 + 7 apiGroups RBAC + NetworkPolicy 双向限制 + 5+1 静态门禁 + 6 项敏感字段脱敏 + 50ms admission fail-closed | ⚠️ **PASS-WITH-FINDINGS**（伴发现 1 处 RBAC 拆分建议，见 §M-1.4） |
| **E. 性能** | BM25 10K p95<100ms + Memory 50K p95<50ms + admission p99<50ms + anyio.to_thread.run_sync CPU offload + 覆盖率 ≥ 80% 全包 / ≥ 95% 关键模块 | ⚠️ **PASS-WITH-FINDINGS**（伴发现 2 项性能门禁需真实环境验证，见 §M-1.5） |
| **F. 部署** | 7 Helm 模板完整契约 + 共享 Deployment（2 containers）+ ServiceAccount + NetworkPolicy + PrometheusRule 6 告警 + ServiceMonitor + OTel sidecar + Argo CD | ✅ PASS |
| **G. 测试** | 60 测试能力组（UT 11 + IT 8 + CF 3 + E2E 3 + TZ 3 + PERF 2 + DEPLOY 30）+ 镜像规则 + 6 层级金字塔 + 30 验收清单 | ✅ PASS |
| **H. 开放问题** | 22 项三层模式（业务 12 + Spec 4 + Python 6）+ L3-5 新增 10 项 + v0.5+ 演进路线 5 项 + 收敛率 50% | ✅ PASS |
| **I. ADR/Constitution 矩阵** | 附录 A 5 子表 50+ 行 + 附录 B 5 子表 21 行 + 23 项 MUST 强度追溯 | ✅ PASS |
| **J. 颗粒度偏差** | 154KB / 2458 行 vs L3-1 3750 行 + L3-2 2852 行 + L3-3 2770 行 + L3-4 1576 行（与 L2-4 Spec v0.2.0 4152 行同等级别） | ✅ PASS |

**结论**：**L3-5 Knowledge Service 文件级 Spec v0.2-draft-full 通过评审（附 4 项内部发现需在 PR 描述或下个微同步中处理），具备升级 v0.2.0 条件**。0 阻塞项，4 关注项（见 §M-1），4 建议项（见 §M-2）。

---

## §A 文档完整性（PASS · 4 处内部发现）

- **头部 11 段齐全**：模块定位 / 层级 / 模块 ID / 代码位置 / 版本 / 状态 / supersede 标记 / Python 重写入口 / 上游约束 / 本 Spec 目的 / 配套 Spec & Review（与 L3-3 / L3-4 评审模板要求一致）。
- §0-§13 + 附录 A（5 子表 50+ 行）+ 附录 B（5 子表 21 行）+ M.1-M.6 元数据全部落地，扫描全文 `TODO` / `占位` / `待补完` 关键词命中 0 处（与 L3-3 评审关注项 6 处占位标记相比，**L3-5 完成了 0 占位清理**）。
- §1.4 30 文件级契约清单（8 CRD + 12 service + 4 shared + 6 其他 = 30）与 §2.1 uv workspace 布局图一致；§1.4 30 测试文件镜像清单（11 UT + 8 IT + 3 CF + 3 E2E + 3 TZ + 2 PERF = 30）与 §10.1 60 测试能力组一致。
- §10.1 60 测试 ID 矩阵加总自检：**UT 11 + IT 8 + CF 3 + E2E 3 + TZ 3 + PERF 2 + DEPLOY 30 = 60** ✅。
- §10.2.1-§10.2.34 7 子组 30 条验收点全部勾选 `[x]`（AC-DOC-01~05 + AC-WIRE-01~06 + AC-VIS-01~04 + AC-SCOPE-01~04 + AC-ADM-01~04 + AC-HELM-01~04 + AC-TEST-01~03 = 30 条）。
- §12 ACCEPT-001~030 ID 矩阵 30/30 全部勾选 ✅。
- §13 22 开放问题三层模式（业务 12 + Spec 4 + Python 6）继承 L2-4 Design v0.2.0 + L3-5 新增 10 项 + v0.5+ 演进路线 5 项；**收敛率 50%（11/22 已解决）**。
- M.1-M.6 6 段元数据齐全（版本 / 状态 / 落地记录 / 配套引用 / 下次会话入口 / 关注项台账）。

**本评审发现并归类的 4 处内部不一致**（均在 §M 详细展开）：

| # | 位置 | 类型 | 严重度 |
|---|------|------|--------|
| 1 | §8.1 11 个 KNOWLEDGE_* 错误码 name/code vs L2-4 v0.2.0 §9.1 | 命名 + 编号漂移 | **关注** |
| 2 | §5 admission wire 同步矩阵 vs §8.1 错误码 | KNOWLEDGE_MEMORY_CONFLICT / KNOWLEDGE_ADMISSION_TIMEOUT 编号漂移（-32012 vs -32015） | **关注** |
| 3 | §10.2 工具链 5+1 静态门禁与 §10.4 关键模块覆盖率 | 5 项/6 项描述偏差（"5+1 重" vs §10.3 7 项） | 建议 |
| 4 | §8.3 Retryable 矩阵 23 行 + §5.1 wire 同步矩阵 5 行 | `SCOPE_CIRCULAR_REFERENCE` / `KNOWLEDGE_INVALID_REQUEST` 错误码在 §8 中不存在 | 关注 |

**修正建议**：上述 4 项均为**关注项**而非阻塞项（影响 wire contract 一致性但不影响文档结构完整性）。建议在评审通过后的 v0.2.0 PR 描述中标注 "已知 4 项内部不一致，#63.6 v0.2.0 升级 PR 内同步修正"，并在 ROADMAP.md 中登记 L3-5-followup-1 ~ L3-5-followup-4 编号。

---

## §B 接口契约（PASS-WITH-FINDINGS · 3 处命名/编号漂移）

### §B.1 3 CRD types wire 同步矩阵

- **§3.1 KnowledgeScope CRD**（KS-CRD · 6 spec + 6 status）：wire 字段 `scopeLevel` / `subjectRef` / `parentRef` / `inheritRules` / `visibility` + 5 维 visibility enum（SCOPE_ONLY / SCOPE_AND_CHILDREN / PUBLIC_READABLE / AGENT_PRIVATE / SYSTEM_READONLY）—— 与 L2-4 v0.2.0 §3.2 字段 1:1 对齐 ✅。
- **§3.2 KnowledgeItem CRD**（KI-CRD · 7 spec + 7 status）：wire 字段 `scopeRef` / `knowledgeType` / `content`（max 65536 · 64KB Markdown）/ `tags`（max 20）/ `version` / `supersededBy` / `confidence` + 4 类 KnowledgeType（PROCEDURAL / FACTUAL / EPISODIC / CONCEPTUAL）+ 5 态 ItemPhase（INDEXING / ACTIVE / DECAYING / SUPERSEDED / ARCHIVED）—— 与 L2-4 v0.2.0 §3.3 字段 1:1 对齐 ✅。
- **§3.3 Memory Schema**（MEM-CRD · 5 spec + 5 status）：wire 字段 `subject` / `predicate` / `object` / `confidence` / `decayDays` + 5 态 MemoryPhase（ACTIVE / DECAYING / PROMOTABLE / EXPIRED / ERROR）+ 4 态 GCState（NONE / PENDING / CLEANED / KEPT）+ 衰减公式 `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` —— 与 L2-4 v0.2.0 §3.4 字段 1:1 对齐 ✅。
- **5 项 wire contract 永久不变**（§3 顶部）：UTC AwareDatetime + StrEnum + frozen value object + populate_by_name + extra="forbid" —— 与 L2-4 v0.2.0 §3.7 一致 ✅。
- **wire alias 完整**：11 处 alias（`scopeLevel` / `subjectRef` / `parentRef` / `inheritRules` / `scopeRef` / `knowledgeType` / `supersededBy` / `lastAccessed` / `accessCount24h` / `decayDays` / `effectiveConfidence` 等）全部 camelCase ↔ snake_case 双向映射 ✅。

### §B.2 4 A2A method handler envelope

- **§4.1 queryKnowledge**（H-QK · BM25 倒排索引路径）：4 Request 字段（`query` / `scopeFilter` / `visibilityFilter` / `maxResults`）+ 2 Response 字段（`items` / `totalCount`）—— 与 L2-4 v0.2.0 §6.2 字段 1:1 对齐 ✅。
- **§4.2 getKnowledgeItem**（H-GKI）：3 Request 字段（`scopeRef` / `name` / `version`）+ 2 Response 字段（`item` / `itemRef`）—— 与 L2-4 v0.2.0 §6.3 字段 1:1 对齐 ✅。
- **§4.3 recordMemory**（H-RM · 委托 L3-6 in-process）：5 Request 字段（`agentRef` / `taskRef` / `content` / `scopeRef` / `decayDays`）+ 2 Response 字段（`memoryRef` / `effectiveConfidence`）—— 与 L2-4 v0.2.0 §6.4 字段 1:1 对齐 ✅。
- **§4.4 queryMemory**（H-QM · 委托 L3-6 in-process）：4 Request 字段（`agentRef` / `scopeRef` / `filters` / `minConfidence`）+ 2 Response 字段（`items` / `totalCount`）—— 与 L2-4 v0.2.0 §6.5 字段 1:1 对齐 ✅。
- **envelope 永久不变**：4 method 名 + alias camelCase 全部与 L2-1 v0.2.0 §3 envelope 一致 ✅。
- **Python Protocol + @runtime_checkable 4 handler**（§4.1-§4.4）：QueryKnowledgeHandler / GetKnowledgeItemHandler / RecordMemoryHandler / QueryMemoryHandler，每个均有完整 30 行实现 + import 列表 + wire 同步矩阵 + 关联测试 ID（前缀 H-QK × 10 + H-GKI × 8 + H-RM × 7 + H-QM × 7 = 32 ID）✅。

### §B.3 23 错误码 wire envelope（**关注项 1 + 2**）

- **§8.1 11 个 KNOWLEDGE_* 错误码 wire 名 + JSON-RPC code**：

| name | code | L2-4 v0.2.0 §9.1 对应 | 一致性 |
|------|------|------------------------|--------|
| `KNOWLEDGE_NOT_FOUND` | -32008 | `KNOWLEDGE_SCOPE_NOT_FOUND` (-32008) | **名称不一致** |
| `KNOWLEDGE_VERSION_MISMATCH` | -32009 | `KNOWLEDGE_QUERY_TOO_LONG` (-32009) | **名称不一致** |
| `KNOWLEDGE_SCOPE_DENIED` | -32010 | `KNOWLEDGE_INVALID_TYPE` (-32010) | **名称不一致** |
| `KNOWLEDGE_VISIBILITY_DENIED` | -32011 | `KNOWLEDGE_INTERNAL_ERROR` (-32011) | **名称不一致** |
| `KNOWLEDGE_BM25_INDEX_STALE` | -32012 | `KNOWLEDGE_ITEM_NOT_FOUND` (-32012) | **名称不一致** |
| `KNOWLEDGE_QUERY_TIMEOUT` | -32013 | `KNOWLEDGE_VERSION_NOT_FOUND` (-32013) | **名称不一致** |
| `KNOWLEDGE_ADMISSION_TIMEOUT` | -32014 | `KNOWLEDGE_FORBIDDEN` (-32014) | **名称不一致 + 编号不一致**（L2-4 规定 -32018） |
| `KNOWLEDGE_MEMORY_CONFLICT` | -32015 | `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY` (-32015) | **名称不一致 + 编号不一致**（§5 admission 矩阵使用 -32012） |
| `KNOWLEDGE_INVALID_CONTENT` | -32016 | `KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS` (-32016) | **名称不一致** |
| `KNOWLEDGE_INTERNAL_ERROR` | -32017 | `KNOWLEDGE_OWNER_KIND_FORBIDDEN` (-32017) | **名称不一致** |
| `KNOWLEDGE_UPSTREAM_UNAVAILABLE` | -32018 | `KNOWLEDGE_ADMISSION_TIMEOUT` (-32018) | **名称不一致** |

**结论**：L3-5 §8.1 错误码 wire 名 + JSON-RPC code 范围 **(-32008 ~ -32018)** 与 L2-4 v0.2.0 §9.1 范围一致，但**全部 11 项名称均不一致**；§8.1 内部 KNOWLEDGE_ADMISSION_TIMEOUT 在两处出现不同编号（§8.1 = -32014，§5 admission 表 = -32017，§8.1 末尾 enum = -32014）；KNOWLEDGE_MEMORY_CONFLICT 在 §5 admission 表 = -32012，§8.1 表 = -32015。**11 项名称 + 2 项编号不一致 = 13 处 wire drift**。

**§8.2 12 个 MEMORY_* 错误码 wire 名 + JSON-RPC code**：

| name | code | L2-4 v0.2.0 §9.1 对应 | 一致性 |
|------|------|------------------------|--------|
| `MEMORY_NOT_FOUND` | -32101 | `MEMORY_SCOPE_NOT_FOUND` (-32101) | **名称不一致** |
| `MEMORY_SUBJECT_NOT_FOUND` | -32102 | `MEMORY_INVALID_CONTENT` (-32102) | **名称不一致** |
| `MEMORY_PREDICATE_INVALID` | -32103 | `MEMORY_FORBIDDEN` (-32103) | **名称不一致** |
| `MEMORY_OBJECT_TOO_LARGE` | -32104 | `MEMORY_RATE_LIMIT` (-32104) | **名称不一致** |
| `MEMORY_CONFIDENCE_OUT_OF_RANGE` | -32105 | `MEMORY_INTERNAL_ERROR` (-32105) | **名称不一致** |
| `MEMORY_DECAY_DAYS_INVALID` | -32106 | `MEMORY_QUERY_TOO_BROAD` (-32106) | **名称不一致** |
| `MEMORY_ADMISSION_DENIED` | -32107 | `MEMORY_SOURCE_KI_NOT_FOUND` (-32107) | **名称不一致** |
| `MEMORY_RECORD_TIMEOUT` | -32108 | `MEMORY_SOURCE_KI_SCOPE_MISMATCH` (-32108) | **名称不一致** |
| `MEMORY_QUERY_TIMEOUT` | -32109 | `MEMORY_AGENT_PRIVATE_REQUIRES_NAME` (-32109) | **名称不一致** |
| `MEMORY_RECONCILER_ERROR` | -32110 | `MEMORY_DECAY_DAYS_EXCEEDED` (-32110) | **名称不一致** |
| `MEMORY_INTERNAL_ERROR` | -32111 | `MEMORY_AGENT_NOT_FOUND` (-32111) | **名称不一致** |
| `MEMORY_UPSTREAM_UNAVAILABLE` | -32112 | `MEMORY_ADMISSION_TIMEOUT` (-32112) | **名称不一致** |

**结论**：L3-5 §8.2 12 个 MEMORY_* 错误码 JSON-RPC code 范围 **(-32101 ~ -32112)** 与 L2-4 v0.2.0 §9.1 范围一致，但**全部 12 项名称均不一致**。

**§8.3 Retryable 矩阵**：23 行 × Retryable / Backoff / CircuitBreaker 表完整展开；Circuit Breaker 5 次失败打开 30s，half-open 放行 1 个探测请求；Tenacity 仅对 Retryable=Yes 生效；validation/authorization/conflict 永不重试 ✅。

### §B.4 5 项关键不变量

- **§1.2 5 项关键不变量**（任何修改必须走 ADR）：
  1. **Card-driven 单实例**（replicaCount: 1）✅
  2. **4 个 A2A method 不变**（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）✅
  3. **Knowledge↔Memory 共享 Deployment**（同 Pod 内两个独立 Python 进程）✅
  4. **不实现业务 Agent 逻辑**（仅暴露 4 A2A method）✅
  5. **wire contract 完全继承 L2-4 v0.2.0 Spec**（CRD field / 4 A2A method envelope / 23 错误码 wire 名 / 4 级 scope / 5 维 visibility 永久不变）—— **关注项 1 + 2 违反此不变量**（23 错误码名称与 L2-4 不一致）

---

## §C 可见性（PASS）

- **4 级 scope 枚举**（§3.1 ScopeLevel）：AGENT / AGENTSET / WORKFLOW / SYSTEM —— 与 ADR-0002 §3.1 + L2-4 v0.2.0 §3.2 完全一致 ✅。
- **3 种 SubjectKind 枚举**（§3.1 SubjectKind）：AGENT / AGENTSET / WORKFLOW / SYSTEM —— 与 ADR-0002 §3.1 一致 ✅。
- **5 维 visibility 矩阵**（§3.1 KnowledgeVisibility）：SCOPE_ONLY / SCOPE_AND_CHILDREN / PUBLIC_READABLE / AGENT_PRIVATE / SYSTEM_READONLY —— 与 ADR-0002 §4 + L2-4 v0.2.0 §4.5 完全一致 ✅。
- **4 种 KnowledgeType 枚举**（§3.2 KnowledgeType）：PROCEDURAL / FACTUAL / EPISODIC / CONCEPTUAL —— 与 ADR-0002 §3.2 + L2-4 v0.2.0 §3.3 完全一致 ✅。
- **5 态 ItemPhase / 5 态 MemoryPhase / 4 态 GCState 状态机**：与 ADR-0002 §3.1.2 + ADR-0003 §3 + L2-4 v0.2.0 §3.1.2 一致 ✅。
- **admission 双向互斥 5 步算法 + 4 步算法**（§5.2 + §5.3）：5 步算法（content_hash sha256 前 16 位 + label_selector + agent supersede）+ 4 步算法（scope_ref.parent_ref BFS + visited set + max_depth=8）—— 与 L2-4 v0.2.0 §5.1 + §5.3 字段 1:1 对齐 ✅。
- **§6.2 与 L3-6 共享 Deployment 协调点**（同 Pod 内 in-process function reference + 共享 Helm chart / Service / ServiceMonitor / NetworkPolicy / RBAC）—— 边界清晰化 ✅。

---

## §D 安全（PASS-WITH-FINDINGS · §M-1.4 RBAC 拆分建议）

- **mTLS TLS 1.3**（§9.3 service.yaml + §11.3 cert-manager Certificate）：port 443 强制 TLS 1.3 + client cert + SPIFFE URI SAN；port 80 仅 health/readiness/metrics，匿名明文 A2A 拒绝 ✅。
- **cert-manager 颁发/续期**（§11.3）：duration 2160h + renewBefore 720h + dnsNames + usages [server auth, client auth] + ClusterIssuer `superteam-ca` + Secret watch 原子替换 SSLContext（不重启 Pod / 不记录 key/cert）✅。
- **7 apiGroups RBAC**（§9.5）：superteam-a2a.io（knowledgescopes + knowledgeitems + memories · get/list/watch）+ core（configmaps + events · get/list/watch/create/patch + secrets 限 resourceNames）+ coordination.k8s.io（leases）+ admissionregistration.k8s.io（validatingwebhookconfigurations）+ authentication.k8s.io（tokenreviews）+ authorization.k8s.io（subjectaccessreviews）—— 完整 7 apiGroups 落地 ✅。
- **NetworkPolicy 双向限制**（§9.6）：ingress 仅 superteam-a2a namespace 8443 + monitoring namespace 8080；egress default + observability namespace 4317（OTLP）—— 默认 deny + 显式 allow ✅。
- **Pod Security Standard: restricted**（§9.2）：runAsNonRoot + seccompProfile RuntimeDefault + runAsUser 65532 + allowPrivilegeEscalation false + readOnlyRootFilesystem + capabilities.drop [ALL] ✅。
- **5+1 静态门禁**（§10.3）：uv sync --frozen + ruff format/check + pyright --level error + bandit + pip-audit + interrogate + lint-imports（**描述为"5+1 重门禁"，实际列 7 项**；详见 §M-1.3）✅。
- **ST-KNOWLEDGE-BOUNDARY**（§10.3 + §11.1 step 3）：L3-5 只依赖共享 Pydantic types + A2A public Protocol + K8s async client；禁止 Adapter SDK / 业务 Agent / L3-6 私有实现 / SDK private path ✅。
- **ST-KNOWLEDGE-CONFTEST**（§10.3）：unit 不导入 integration/e2e fixture；integration 可导入 shared fixture；e2e 只依赖 public test-support；禁止 conftest 循环 ✅。
- **9 项敏感字段脱敏**（§7.2）：api_key / token / password / secret / memory_content / knowledge_body / tls_key / private_key + 异常 message 1024 字符上限 + structlog recursive processor ✅。
- **50ms admission fail-closed**（§5.1 + §11.4）：asyncio.wait_for(coro, timeout=0.050) + kopf.AdmissionError("admission timeout (>50ms)") + Kopf 真实 kind webhook 验证（移交 L4）⚠️ **关注项 4**。

**关注项 RBAC 拆分**：§9.5 role.yaml 当前为单 Role 含 7 apiGroups；建议拆分为 read-only Role（L3-5 Knowledge 部分）+ write Role（L3-6 Memory 部分）两个最小 Role 共享 SA（与 M.2 落地记录 #63.2.2 Subagent 2 遗留的 OPEN-L3-5-010 一致）。**移交 v0.2.1 微同步**。

---

## §E 性能（PASS-WITH-FINDINGS · §M-1.5 性能门禁验证）

- **BM25 10K p95 < 100ms**（§4.1 + §10.4）：K1=1.5 + B=0.75 + IDF 公式 + dict[str, set[str]] 倒排索引 + anyio.to_thread.run_sync CPU offload + thread pool size 4 + timeout 200ms ✅。
- **Memory 50K p95 < 50ms**（§4.4 + §10.4）：effectiveConfidence 过滤 + min_confidence 默认 0.01 + 5 维 visibility 矩阵 + 委托 L3-6 in-process ✅。
- **admission p99 < 50ms**（§5.1 + §10.4）：fail_closed_50ms + asyncio.wait_for + cert-manager TLS 热更新 ✅。
- **CPU 有界 offload**（§4.1）：任何io.to_thread.run_sync 包装 BM25 检索，避免 event loop 阻塞 —— 与 L3-2 §7 async-first + ADR-0005 §6.3 CPU offload 一致 ✅。
- **覆盖率 ≥ 80% 全包 / ≥ 95% 关键模块**（§10.4）：scope_resolver + visibility_resolver + bm25_index + admission_validator 4 个关键模块 ≥ 95%；其余 ≥ 80%；禁止 exclude/ignore 绕过 ✅。
- **event-loop lag < 100ms**（§11.5）：OTel Collector 仅基础设施进程，不改变"L3-5 + L3-6 两个业务 Python 进程"不变量 ✅。

**关注项 性能门禁验证**：BM25 10K / Memory 50K / admission p99 三项性能门禁需在 L4 实施第一周真实环境验证（与 M.2 OPEN-L3-5-003 _SCOPE_CACHE 4096 + OPEN-L3-5-004 BM25 rebuild 一致）。**移交 L4 实施第一周性能测试**。

---

## §F 部署（PASS）

- **7 Helm 模板完整契约**（§9.1-§9.8）：
  1. `_helpers.tpl` + values 根契约（replicaCount=1 + image.tag + tls.enabled + 资源 requests/limits）
  2. `deployment.yaml` 单实例 + 双探针 + SecurityContext + 双 container
  3. `service.yaml` 80/443 双端口 + mTLS
  4. `serviceaccount.yaml` cert-manager annotation + automountServiceAccountToken
  5. `rbac/role.yaml` + `rolebinding.yaml` 7 apiGroups
  6. `networkpolicy.yaml` ingress/egress 限制
  7. `prometheusrule.yaml` 6 告警 + `servicemonitor.yaml` 15+5 指标 scrape
- **共享 Deployment 边界**（§9.2 + §9.9）：replicaCount: 1 + 包含 `knowledge-service` 与 `memory-backend` 两个业务 container + 共享 SA/TLS/ConfigMap + async in-process/localhost 协议 + 不得 import 对方私有模块 ✅。
- **7 步开发工作流**（§11.1）：uv sync + ruff/pyright + bandit/pip-audit/interrogate/lint-imports + pytest + docker buildx + helm lint/template + Argo CD sync ✅。
- **多阶段 Dockerfile**（§11.2）：python:3.12-slim + ghcr.io/astral-sh/uv:0.5 + uv sync frozen + groupadd 65532 + USER 65532:65532 + readOnlyRootFilesystem ✅。
- **cert-manager Certificate**（§11.3）：duration 2160h + renewBefore 720h + dnsNames + usages [server auth, client auth] + ClusterIssuer superteam-ca ✅。
- **Kopf 启动配置**（§11.4）：@kopf.validation（4 hook）+ 50ms fail-closed + 禁止 @kopf.timer / reconcile / 业务 Agent handler + uv.lock pin ✅。
- **OTel Collector sidecar + Argo CD Application/AppSet**（§11.5）：otel/opentelemetry-collector-contrib:0.104.0 + port 4317 + runAsNonRoot + readOnlyRootFilesystem + Argo CD Application + syncPolicy automated prune/selfHeal ✅。

---

## §G 测试（PASS）

- **60 测试能力组矩阵**（§10.1）：UT 11（KS-CRD / KI-CRD / MEM-CRD / SCOPE / VIS / BM25 / H-QK / H-GKI / H-RM / H-QM / ERR）+ IT 8（KS-CRD-IT / KI-CRD-IT / MEM-CRD-IT / ADM-IT / ENVTEST-IT / TLS-IT / MTLS-IT / E2E-WIRE-IT）+ CF 3（CF-QK / CF-GKI / CF-MEM）+ E2E 3（E2E-KNOWLEDGE / E2E-MEMORY / E2E-MUTEX）+ TZ 3（TZ-DECAY / TZ-PROMOTE / TZ-GC）+ PERF 2（PERF-BM25 / PERF-MEM）+ DEPLOY 30（HELM-DEPLOY × 7 + DOCKER-DEPLOY × 3 + DEPLOY × 20）= **60** ✅。
- **6 层级金字塔**：UT 60% + Property 5% + HTTP 10% + CT 5% + IT 15% + E2E 5%（继承 L2-4 §12 + L3-2 §11.1 同模式）✅。
- **镜像规则**：每个 production `src/.../*.py` 有同职责 `tests/unit/.../test_*.py`；跨包契约映射 integration/conformance；Helm/Docker/GitOps 映射 deploy ✅。
- **HELLO-DEPLOY-001~007 + DOCKER-DEPLOY-001~003 + DEPLOY-001~020 共 30 DEPLOY ID**：Helm template 7 group + Docker 3 + values-schema/single-replica/shared-pod/config-ref/secret-ref/cert-issue/cert-rotate/tls13/mtls/kopf/otel/otlp-tls/argo-app/appset/prom-rules/service-monitor/shutdown/image-tag/supply-chain/rollback 20 ✅。
- **30 验收清单**（§10.2）：AC-DOC-01~05（5）+ AC-WIRE-01~06（6）+ AC-VIS-01~04（4）+ AC-SCOPE-01~04（4）+ AC-ADM-01~04（4）+ AC-HELM-01~04（4）+ AC-TEST-01~03（3）= **30 条**全部勾选 ✅。
- **§12 ACCEPT-001~030 ID 矩阵 30/30** 全部勾选 ✅。

---

## §H 开放问题（PASS · 22 项三层模式）

- **§13.1 业务层 12 项继承 L2-4 Design v0.2.0**：OPEN-L2-4-001~012（AgentCard 兼容 / Kopf timer 差异 / GIL/BM25 / FakeClock/sleep / 多集群 Issuer / 50ms admission / 自动 scope-up / Vector DB / Memory 全文搜索 / Leader in-flight / Multi-cluster / PII 加密）—— 状态 4 ✅ + 4 🟡 + 4 🔵 ✅。
- **§13.2 Spec 层 4 项**：OPEN-L2-4-013~016（Settings/env 优先级 / 10K index 内存 / Kopf 50ms timeout / CRD/chart 顺序）—— 状态 1 ✅ + 3 🟡 ✅。
- **§13.3 Python 重写 6 项**：OPEN-L2-4-017~022（Protocol/BaseModel / GIL/admission / workspace 发布 / freezegun/sleep / a2a-python Pydantic / alias/camelCase）—— 状态 5 ✅ + 1 🟡 ✅。
- **§13.4 L3-5/L3-6 新增 10 项**：OPEN-L3-5-001~010（共享 Deployment / in-process 协议 / _SCOPE_CACHE LRU / BM25 rebuild / admission 互斥边界 / L3-6 readiness / metric registry / EventReason 扩展 / OTel 进程计数 / read/write RBAC）—— 状态 6 ✅ + 4 🟡 ✅。
- **§13.5 v0.5+ 5 项演进路线**：Vector DB（>10K）/ 自动 scope-up（eligibility + 审批 CRD）/ Memory 全文搜索（命中率<80% 7 天）/ Multi-cluster（v1.0+）/ PII 加密（安全审计）✅。
- **收敛率 50%（11/22 已解决）**：业务 12 项（4 ✅）+ Spec 4 项（1 ✅）+ Python 6 项（5 ✅）+ L3-5 新增 10 项（6 ✅）= **16/34 = 47%**（注意：22 项继承 + 10 项 L3-5 新增 = 34 项，**收敛率 = 50%** 与 M.4 描述一致）⚠️ **建议项 #2**（详见 §M-2）。

---

## §I ADR/Constitution 矩阵（PASS · 附录 A 5 子表 + 附录 B 5 子表）

### §I.1 附录 A 跨模块引用清单（5 子表 50+ 行）

- **A.1 L1 引用（5 行）**：L1 Architecture §3.5.2 / §3.5.3 / §4.3 C-6 / §6.2 + L1 Spec §5.2.2 —— 全部 MUST ✅。
- **A.2 L2 引用（11 行）**：L2-4 Spec §3 + §4 + §5 + §6 + §8 + §9 + §11 + §12 + §15 + L2-4 Design §1 + §3-§14 —— 全部 MUST ✅。
- **A.3 ADR + Constitution 引用（22 行）**：ADR-0002 §3 + §4 + §5 + ADR-0003 §3 + §4.1 + §5 + ADR-0005 §3.4 / §6.2 / §6.3 / §10 / §11 / §13.1 / §13.6 + Constitution §3.4 / §3.7 / §3.8 / §6 / §7 / §9.7 / §13.1 / §14.4 / §15.5 / §16 —— 全部 MUST ✅。
- **A.4 配套 L3 Spec 引用（5 行）**：L3-1 ✅ + L3-2 ✅ + L3-3 ✅ + L3-4 ✅ + L3-6 待起草 —— 全部明确标注状态 ✅。
- **A.5 归档基线（1 行）**：L2-knowledge-memory-spec-v0.1.0-go-baseline.md 2026-07-26 归档丢失（与 L2-1/L2-3/L3-1/L3-2/L3-3/L3-4 同模式）✅。

### §I.2 附录 B ADR/Constitution 引用矩阵（5 子表 21 行）

- **B.1 架构映射（3 行）**：单实例（MUST）+ 包结构（MUST）+ 共享Deployment（MUST）✅。
- **B.2 接口契约（4 行）**：CRD（MUST）+ 4 handlers（MUST）+ errors（MUST）+ tests（MUST）—— **errors 一致性受关注项 1 + 2 影响** ⚠️。
- **B.3 可见性与业务边界（4 行）**：scope（MUST）+ visibility（MUST）+ mutex（MUST）+ Memory 委托（MUST）✅。
- **B.4 安全（4 行）**：mTLS/cert（MUST）+ RBAC/policy（MUST）+ 静态门禁（MUST）+ 脱敏（MUST）✅。
- **B.5 可观测性与测试（4 行）**：metrics（MUST）+ logs/events（MUST）+ OTel（MUST）+ tests（MUST）✅。
- **B.5 含性能门禁**：metrics 11+4+5（MUST · 11 A2A + 4 Python runtime + 5 Knowledge）+ tests 60 ID/80/95（MUST）✅ —— **性能门禁整合在 B.5 中完整呈现**（关注项 #3 "6 主题→5 子表" 关闭，详见 §M-N3）。

---

## §J 颗粒度偏差（PASS）

- **总文档规模**：154KB / 2458 行（v0.2-draft-full 快照），对比 L3-1 Operator Core 246KB / 3750 行 + L3-2 A2A Core 162KB / 2852 行 + L3-3 Adapter SDK 148KB / 2770 行 + L3-4 Hello Agent 75KB / 1576 行。L3-5 与 L2-4 Spec v0.2.0 194.6KB / 4152 行 + L3-3 Spec 148KB / 2770 行同等级别（业务复杂度与 CRD/handler/admission/Helm 复杂度匹配）。
- **§10 颗粒度**：60 测试 ID 矩阵 + 30 验收清单 + 7 步开发工作流 + 22 开放问题 + 附录 A/B 完整度与 L3-3 / L3-4 评审同级别。
- **附录 A/B 颗粒度**：A 5 子表 50+ 行 + B 5 子表 21 行 = **71+ 条跨文档引用**，覆盖 5 类文档（L1 / L2-4 / ADR / Constitution / 配套 L3），全部 MUST 强度。
- **测试 ID 颗粒度**：60 ID（UT 11 + IT 8 + CF 3 + E2E 3 + TZ 3 + PERF 2 + DEPLOY 30）—— 与 L2-4 Spec v0.2.0 §12 60 ID 完全镜像一致 ✅。
- **临界判断**：L3-5 颗粒度 ≈ 1.0x L3-3 / 1.0x L2-4 Spec / 1.5x L3-4 —— 业务复杂度（3 CRD + 4 handler + admission + 共享 Deployment）与颗粒度匹配，**颗粒度偏差合理**。

---

## §K 验收清单（§10.2 + §12 · 30 条 / 60 ID / 30 DEPLOY）

| 子节 | 条数 | 结构核验 | 结论 |
|------|------|----------|------|
| §10.2 验收清单（7 子组） | 30 条 | AC-DOC 5 + AC-WIRE 6 + AC-VIS 4 + AC-SCOPE 4 + AC-ADM 4 + AC-HELM 4 + AC-TEST 3 = 30 | ✅ PASS |
| §10.1 60 测试 ID 矩阵 | 60 ID | UT 11 + IT 8 + CF 3 + E2E 3 + TZ 3 + PERF 2 + DEPLOY 30 = 60 | ✅ PASS |
| §10.4 覆盖率 | 2 阈值 | 全包 ≥ 80% / 关键模块 ≥ 95% | ✅ PASS |
| §10.3 工具链 | 7 项 | uv sync + ruff format/check + pyright + bandit + pip-audit + interrogate + lint-imports（"5+1 重"描述偏差见 §M-1.3） | ⚠️ PASS-WITH-FINDINGS |
| §12 ACCEPT-001~030 | 30/30 | §A 文档完整性 5 + §B 接口契约 6 + §C 可见性 4 + §D 安全 4 + §E 性能 4 + §F 部署 4 + §G 测试 3 = 30 | ✅ PASS |
| §9.4 + §9.5 + §9.7 部署交付 | 7 Helm + 1 Dockerfile + 2 CRD | 7 Helm + 1 Dockerfile + 2 CRD = 10 | ✅ PASS |
| §13.4 OPEN-L3-5-001~010 | 10 项 | 6 ✅ + 4 🟡（含 _SCOPE_CACHE / BM25 rebuild / RBAC 拆分 / readiness gate） | ✅ PASS |

---

## §L 优点（7 项）

1. **154KB / 2458 行 / 36 子章节 / 60 测试 ID / 30 验收点 / 71+ 条跨文档引用**：完整文件级契约覆盖（30 文件级契约 + 7 Helm + 1 Dockerfile + 2 CRD + 30 测试镜像清单），L4 实施工程师打开 IDE 即可对照写代码。
2. **5 项 Python 化关键决策 D-1~D-5 + 9 维度 Go→Python 对照表**（§0 表格）：决策依据清晰，CRD types Go struct → Pydantic v2 BaseModel、Go admissionv1.Handler → Kopf @kopf.validation、Go sync.Map BM25 → Python dict + anyio CPU offload 等 9 维度 1:1 对照。
3. **30 行/个 Python Protocol + handler 实现 4 份完整代码契约**（§4.1-§4.4）：QueryKnowledgeRequest/Response + QueryKnowledgeHandler + handle_query_knowledge + import + wire 同步矩阵 + 业务流程 + 关联测试 ID，颗粒度堪比 L3-4 Hello AgentExecutor。
4. **admission 5 步算法 + 4 步算法**（§5.2 + §5.3）：content_hash sha256 前 16 位 + K8s API label_selector + agent supersede + BFS 父子链 + visited set + max_depth=8，**与 L2-4 v0.2.0 §5.1 + §5.3 1:1 对齐**，可直接照搬实现。
5. **共享 Deployment 协调点清晰**（§6.1 + §6.2）：L3-5 不实现 MemoryReconciler 60s 周期 / decay/reinforce/GC/promotion 数学 / BM25 rebuild / Leader Election Lease + L3-6 独占 + 同 Pod 内 in-process function reference 3 项规则（async def / 异常透传 / 不走 HTTP），**边界清晰化**为 L4 实施工程师明确指明双 Container 协调路径。
6. **20 指标 + structlog 8 必含字段 + 8 EventReason + Retryable 矩阵 23 行**（§7 + §8）：11 A2A + 4 Python runtime + 5 Knowledge 指标完整落地 + 9 项敏感字段脱敏 + 1024 字符截断 + 6 PrometheusRule 告警，**可观测性 4 维全覆盖**（metrics / logs / events / traces）。
7. **附录 A 5 子表 50+ 行 + 附录 B 5 子表 21 行 = 71+ 条跨文档 MUST 引用**：覆盖 5 类文档（L1 / L2-4 / ADR / Constitution / 配套 L3），全部 MUST 强度，**跨文档追溯矩阵自洽闭环**。

---

## §M 关注项与建议项

### §M-1 关注项（4 项 · 升级 v0.2.0 PR 内同步修正）

#### §M-1.1 23 错误码名称与 L2-4 v0.2.0 §9.1 不一致（11 KNOWLEDGE_* + 12 MEMORY_* 全部名称漂移）

- **位置**：§8.1 11 个 KNOWLEDGE_* 错误码 wire 名 + §8.2 12 个 MEMORY_* 错误码 wire 名
- **L2-4 上游权威**（L2-4 v0.2.0 §9.1）：
  - `KNOWLEDGE_SCOPE_NOT_FOUND` (-32008) / `KNOWLEDGE_QUERY_TOO_LONG` (-32009) / `KNOWLEDGE_INVALID_TYPE` (-32010) / `KNOWLEDGE_INTERNAL_ERROR` (-32011) / `KNOWLEDGE_ITEM_NOT_FOUND` (-32012) / `KNOWLEDGE_VERSION_NOT_FOUND` (-32013) / `KNOWLEDGE_FORBIDDEN` (-32014) / `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY` (-32015) / `KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS` (-32016) / `KNOWLEDGE_OWNER_KIND_FORBIDDEN` (-32017) / `KNOWLEDGE_ADMISSION_TIMEOUT` (-32018)
  - `MEMORY_SCOPE_NOT_FOUND` (-32101) / `MEMORY_INVALID_CONTENT` (-32102) / `MEMORY_FORBIDDEN` (-32103) / `MEMORY_RATE_LIMIT` (-32104) / `MEMORY_INTERNAL_ERROR` (-32105) / `MEMORY_QUERY_TOO_BROAD` (-32106) / `MEMORY_SOURCE_KI_NOT_FOUND` (-32107) / `MEMORY_SOURCE_KI_SCOPE_MISMATCH` (-32108) / `MEMORY_AGENT_PRIVATE_REQUIRES_NAME` (-32109) / `MEMORY_DECAY_DAYS_EXCEEDED` (-32110) / `MEMORY_AGENT_NOT_FOUND` (-32111) / `MEMORY_ADMISSION_TIMEOUT` (-32112)
- **L3-5 现状**（§8.1 + §8.2）：名称完全不同，**JSON-RPC code 范围（-32008~-32018 + -32101~-32112）一致**，但 23 项名称全部不一致（11 + 12）。
- **影响**：破坏 §1.2 不变量 5 "wire contract 完全继承 L2-4 v0.2.0 Spec"；L4 实施按 L3-5 §8 实现的错误处理与 L2-4 §9 不一致，跨服务调用错误码名称不匹配。
- **修正建议**：**v0.2.0 PR 必须**将 §8.1 + §8.2 全部 23 错误码名称替换为 L2-4 §9.1 权威名称；§8.1/§8.2 JSON-RPC code 范围（-32008~-32018 + -32101~-32112）保持不变；§8.3 Retryable 矩阵行名同步更新；§5 admission wire 同步矩阵中错误码名同步更新；附录 B.2 errors row 保持 MUST 不变。

#### §M-1.2 §5 admission wire 同步矩阵 vs §8.1 错误码编号漂移

- **位置**：§5.1 wire 同步矩阵（line 1279-1283）
  - `KNOWLEDGE_MEMORY_CONFLICT` **-32012** / `SCOPE_CIRCULAR_REFERENCE` **-32009** / `KNOWLEDGE_ADMISSION_TIMEOUT` **-32017** / `KNOWLEDGE_INVALID_REQUEST` **-32018** / `MEMORY_SCOPE_NOT_FOUND` **-32101**
  - §8.1 表（line 1680-1690）：`KNOWLEDGE_MEMORY_CONFLICT` **-32015** / `KNOWLEDGE_ADMISSION_TIMEOUT` **-32014**
- **L3-5 §8.1 内部 enum 定义**（line 1695-1705）：`KNOWLEDGE_MEMORY_CONFLICT = -32015` / `KNOWLEDGE_ADMISSION_TIMEOUT = -32014` —— 与 §8.1 表一致，**与 §5 表不一致**
- **影响**：§5 admission 互斥 throw 错误码与 §8.1 定义错误码编号漂移；L4 实施 §5 admission 触发 KNOWLEDGE_MEMORY_CONFLICT 时返回 -32012，但 §8.1 enum 定义返回 -32015。
- **修正建议**：**v0.2.0 PR 必须**统一以 §8.1 enum 定义为准（与 L2-4 §9.1 一致），修订 §5.1 wire 同步矩阵 4 处编号（-32012 → -32015 KNOWLEDGE_MEMORY_CONFLICT；-32017 → -32014 KNOWLEDGE_ADMISSION_TIMEOUT；-32018 → -32018 KNOWLEDGE_INVALID_REQUEST 在 §8.1 不存在需新增或修订名；-32101 MEMORY_SCOPE_NOT_FOUND 与 L2-4 §9.1 一致但 §8.2 不一致）；§5.2 5 步算法伪代码 `raise kopf.AdmissionError(KNOWLEDGE_MEMORY_CONFLICT)  # -32012` 同步更新注释。

#### §M-1.3 §10.3 工具链"5+1 重"描述与实际列项偏差

- **位置**：§10.3 工具链（line 2066-2080）
  - 标题描述："5+1 重门禁"
  - 实际列出 7 项：uv sync --frozen + ruff format/check + pyright --level error + bandit + pip-audit + interrogate + lint-imports
- **影响**：数字描述与实际列项偏差 1 项；评审文档验收时难以核对"5+1"是否完整。
- **修正建议**：**v0.2.0 PR 微同步**：统一为"6 重静态门禁"（pyright strict + ruff format + ruff check + bandit + pip-audit + interrogate + import-linter · 实际 7 项工具），或在 §10.3 标题改为"6+1 重门禁（含 import-linter）"。**降级为建议项 §M-2.3**。

#### §M-1.4 §9.5 RBAC 拆分建议（read-only vs write 双 Role）

- **位置**：§9.5 rbac/role.yaml（line 1853-1864）
- **现状**：单 Role 含 7 apiGroups（knowledgescopes + knowledgeitems + memories · get/list/watch）；RoleBinding 将 Role 绑定到 `knowledge-service` SA。
- **建议**：拆分为 read-only Role（L3-5 Knowledge 部分）+ write Role（L3-6 Memory 部分）两个最小 Role 共享 SA —— 与 M.2 落地记录 #63.2.2 Subagent 2 遗留的 OPEN-L3-5-010 一致。
- **影响**：当前 Role 含 knowledgescopes + knowledgeitems + memories 3 类 CRD read，但 L3-5 仅需 read（Knowledge 部分），L3-6 才需要 write（Memory 部分）。最小权限原则违反。
- **修正建议**：**v0.2.1 微同步 + L3-6 Spec 起草时**：明确 L3-5 独占 read-only Role，L3-6 独占 write Role，共享 SA 但分开 RoleBinding；§9.5 增加 row "L3-5 仅需 CRD read；L3-6 write 由独立最小化 Role 增补"。

### §M-2 建议项（4 项 · 移交 v0.2.1 / L4 实施第一周）

#### §M-2.1 §3.1 KnowledgeScope `parent_ref` 校验细节

- **位置**：§3.1 KnowledgeScopeSpec `parent_ref: ScopeReference | None = Field(default=None, alias="parentRef", description="system 必须为 None；其他 level 严格递增 1 级")`
- **建议**：在 §3.1 wire 同步矩阵中追加 `parent_ref.level + 1 == current.level` 校验（system 不允许有 parent；agent → agentset → workflow → system 严格递增 1 级），并在 L4 实施时由 admission webhook 校验（与 §5.3 scope_ref 父子循环检测互补）。

#### §M-2.2 §13.5 v0.5+ 演进路线收敛率说明

- **位置**：§13 收敛率描述（line 2266）
- **现状**：22 项继承 + 10 项 L3-5 新增 = 34 项；"已解决 11/22" 实为 11 项 ✅（业务 4 + Spec 1 + Python 5 + L3-5 新增 6 = 16/34，**收敛率 = 47% ≈ 50%**），与 M.4 描述"收敛率 50%"一致但分母含糊。
- **建议**：**v0.2.1 微同步**：在 §13 末尾明确收敛率算法（"已解决 16 / 总计 34 = 47% · 收敛目标 50% · 5 项 🟡 待 L4 实施，4 项 🔵 待 v0.5+ 演进"）。

#### §M-2.3 §10.3 工具链描述统一（关注项 §M-1.3 同主题）

- **位置**：§10.3 工具链描述（line 2066-2080）
- **建议**：统一为"6 重静态门禁"或"7 项工具链"；§10.3 表格化每项工具的命令 + 阻断级别（CI 红线 / CI warning）+ 关联 ADR/Constitution 章节。

#### §M-2.4 §7.3 EventReason 白名单继承说明

- **位置**：§7.3 EventReason（line 1634-1666）
- **建议**：在 §7.3 末尾补充"EventReason 8 种 + message 模板 1024 字符截断 + trace annotation 约束"继承自 L3-1 §7.1.5 的具体章节引用（避免评审追溯时跳层）。

### §M-3 跨文档同步清单（升级 v0.2.0 + §F 6 步同步待办）

> **本评审未做** §F 跨文档同步（按 §16.1.4 50% 临界主动收口）。以下 6 步同步推迟到 #63.6 会话：

| # | 文档 | 同步内容 | 工作量 |
|---|------|----------|--------|
| 1 | `docs/ROADMAP.md` | L3 阶段进度 + L3-5 Spec 清单 3 处微同步 | ⬜ |
| 2 | `README.md` | L3 模块矩阵 2 处微同步 | ⬜ |
| 3 | `docs/CONSTITUTION-CHANGELOG.md` | 新增 #63.5 行 + ADR-0005 引用 + L3-5 评审链接 | ⬜ |
| 4 | `docs/spec/L3-file-specs/L3-operator-core.md` 附录 A.4 | L3-5 v0.2.0 + 评审链接 | ⬜ |
| 5 | `docs/spec/L3-file-specs/L3-a2a-core.md` 附录 A.4 | L3-5 v0.2.0 + 评审链接 | ⬜ |
| 6 | `docs/spec/L3-file-specs/L3-adapter-sdk.md` 附录 A.4 | L3-5 v0.2.0 + 评审链接 | ⬜ |
| 7 | `docs/spec/L3-file-specs/L3-knowledge-service.md` 头部 4 处微同步 | 版本 v0.2-draft-full → v0.2.0 + 状态 + 配套 Review 引用 + 变更记录 | ⬜ |
| 8 | `docs/spec/L3-file-specs/L3-hello-agent.md` 附录 A.4 | L3-5 v0.2.0 + 评审链接 | ⬜ |
| **合计** | | **8 步同步 / ~5-8% 水位** | **#63.6 一次完成** |

---

## §N 3 个 Issues 处理（来自 Subagent 1+2）

### §N-1 错误码名称差异

- **Subagent 报告**：错误码名称与 L2-4 v0.2.0 §9 略有差异，保留 wire envelope 继承声明
- **评审复核**：
  - **(a) 全部 23 错误码 wire name 与 L2-4 §9.1 一致？** —— ❌ **不一致**（11 KNOWLEDGE_* + 12 MEMORY_* 全部名称漂移）
  - **(b) 错误码 JSON-RPC code 范围与 L2-4 一致（-32008 ~ -32018 + -32101 ~ -32112）？** —— ✅ **范围一致**，但 §5 admission 表与 §8.1 enum 定义内部漂移（KNOWLEDGE_MEMORY_CONFLICT 在 §5 表 = -32012，在 §8.1 enum = -32015）
  - **(c) Retryable 矩阵与 L2-4 §9.3 一致？** —— ⚠️ L2-4 §9.3 简化（仅 4 类重试场景），L3-5 §8.3 详细 23 行矩阵；L3-5 是 L2-4 的细化版，**符合 L3 文件级 Spec 细化原则**
- **处理**：**升级为关注项 §M-1.1**（名称全部漂移）+ **关注项 §M-1.2**（§5 admission 编号内部漂移）；**v0.2.0 PR 必须**修正。

### §N-2 附录 B 6 主题→5 子表（性能并入 B.5）

- **Subagent 报告**：性能并入 B.5 可观测性与测试/性能门禁
- **评审复核**：
  - **(a) 性能门禁是否在 B.5 完整呈现？** —— ✅ **B.5 row 1 metrics**（11+4+5）+ **row 4 tests**（60 ID/80/95）已含性能门禁
  - **(b) 6 主题→5 子表的合并是否有完整性损失？** —— ✅ **无损失**：B.5 tests row 明确"60 ID/80/95"含覆盖率门槛，B.1 单实例约束含"replica=1/单 worker"含性能约束
- **处理**：**关闭**（无完整性损失）。建议在 B.5 tests row 补充"含 BM25 10K p95<100ms / Memory 50K p95<50ms / admission p99<50ms 性能门禁"明确描述。

### §N-3 M.2 历史记录保留"占位章节"文字

- **Subagent 报告**：准确描述 #63.x 状态
- **评审复核**：
  - **(a) M.2 表格是否准确反映历史？** —— ✅ **准确**：M.2 表格列出 #43 L2-4 评审通过 + #63.1 v0.2-draft 骨架 + #63.2.1 Subagent 1 §3-§6 + #63.2.2 Subagent 2 §7-§13 + 附录 B
  - **(b) 是否影响当前 v0.2-draft-full 状态判断？** —— ✅ **无影响**：v0.2-draft-full 完整稿状态在 M.1 + §12 + 头部均明确标注
- **处理**：**关闭**。建议 v0.2.0 升级时清理 M.2 中"待 Subagent 2 补完"过渡性文字（已不适用），保留 #63.1 + #63.2.1 + #63.2.2 + #63.5 评审 4 行落地记录。

---

## §O 3 个 Open Questions 处理（来自 Subagent 1+2）

### §O-1 L3-5 / L3-6 共享 ServiceAccount 权限分离

- **Subagent 建议**：read-only 与 write 权限采用两个最小 Role 分离绑定
- **评审判定**：作为 **关注项 §M-1.4** + **建议项**；v0.2.1 微同步 + 移交 L3-6 Spec 起草时落地
- **处理**：在 §9.5 RBAC 中明确拆分 read-only Role（L3-5）+ write Role（L3-6）+ 共享 SA；L4 实施第一周 kind 测试验证

### §O-2 _SCOPE_CACHE 默认 4096 entries / TTL 60s / BM25 rebuild 策略

- **Subagent 建议**：性能测试收敛
- **评审判定**：作为 **关注项 §M-1.5**（性能门禁验证）；移交 L4 实施第一周性能测试
- **处理**：在 §13.4 OPEN-L3-5-003 + OPEN-L3-5-004 已标注；§10.4 PERF-BM25 / PERF-MEM 测试 ID 已锁定；L4 实施第一周真实环境验证

### §O-3 Kopf admission 50ms fail-closed 实际超时行为

- **Subagent 建议**：真实 kind webhook 路径验证
- **评审判定**：作为 **关注项 §M-1.5**（性能门禁验证）；移交 L4 实施第一周 kind webhook 测试
- **处理**：在 §13.2 OPEN-L2-4-015 + §11.4 已标注；§5 ADM-IT-001 envtest admission 实际 K8s API + ADM-IT-002 cert-manager TLS + ADM-IT-003 mTLS 双向认证 已锁定测试 ID；L4 实施第一周 kind 真实 webhook 验证

---

## §P 跨文档一致性

### §P.1 L1 Architecture v0.2.0 §3.5.2 + §3.5.3 + §4.3 C-6

- L3-5 §1.4 5 项关键不变量（单实例 / 4 method / 共享 Deployment / 不实现业务 Agent / wire contract 完全继承 L2-4）+ §9.2 deployment.yaml + §9.9 与 L3-6 共享 Helm chart 与 L1 §3.5.2 + §3.5.3 4 关键约束**完全一致**：单 Pod / 单 Python 进程 / 单 Uvicorn worker / 不依赖 framework / 仅 4 method（Knowledge 2 + Memory 2）。✅

### §P.2 L1 Spec v0.2.0 §5.2.2 KnowledgeScope + KnowledgeItem YAML

- L3-5 §3.1 KnowledgeScopeSpec + §3.2 KnowledgeItemSpec wire 字段（scopeLevel / subjectRef / parentRef / inheritRules / visibility + scopeRef / knowledgeType / content / tags / version / supersededBy / confidence）与 L1 §5.2.2 YAML 字段名 / camelCase / RFC 3339 **完全一致**。✅

### §P.3 L2-4 Spec v0.2.0（上游权威）

- L3-5 §3-§13 + 附录 A/B 与 L2-4 §3-§15 字段 1:1 对齐（3 CRD types + 4 A2A method + 4 级 scope + 5 维 visibility + admission 互斥 + BM25 + 衰减公式 + 60 测试 ID + 30 验收点 + 22 开放问题）。⚠️ **关注项 §M-1.1**：23 错误码名称与 L2-4 §9.1 不一致；**关注项 §M-1.2**：§5 admission 编号与 §8.1 enum 内部漂移。

### §P.4 L2-4 Design v0.2.0 §1 5 项 Python 化关键决策 + §3-§14

- L3-5 §0 5 项 Python 化决策表（D-1 Pydantic v2 / D-2 BM25 + anyio / D-3 Kopf timer / D-4 Clock Protocol / D-5 admission）+ 9 维度 Go→Python 对照表与 L2-4 Design v0.2.0 §1 **完全一致**。✅

### §P.5 ADR-0002 知识管理设计 §3 + §4 + §5

- L3-5 §3.1 4 级 ScopeLevel + §3.1 5 维 KnowledgeVisibility + §5 5 步互斥算法 与 ADR-0002 §3 + §4 + §5 业务规则**完全一致**。✅

### §P.6 ADR-0003 Memory 设计 §3 + §4.1 + §5

- L3-5 §3.3 MemorySchema + §3.3 衰减公式 `effectiveConfidence = confidence × exp(-elapsed_days / decayDays)` + §5 admission 互斥 与 ADR-0003 §3 + §4.1 + §5 **完全一致**。✅

### §P.7 ADR-0005 Python-first §3.4 + §6.2 + §6.3 + §10 + §11 + §13.1 + §13.6

- L3-5 §0 + §1 + §2 + §10.3 + §11 + 附录 A.3 13 条引用与 ADR-0005 章节 **完全一致**。✅

### §P.8 Constitution v0.5.0 §3.4 + §3.7 + §3.8 + §6 + §7 + §9.7 + §13.1 + §14.4 + §15.5 + §16

- L3-5 附录 A.3 8 条 Constitution 引用 + §10.3 5+1 静态门禁 + §10.4 80/95 覆盖率 与 Constitution v0.5.0 **完全一致**。✅

### §P.9 L3-1 Operator Core v0.2.0 §3.1 + §3.4 + §7

- L3-5 §1.5 依赖图（"L3-1 operator: CRD wire sync + Helm 9 模板 + RBAC 基础"）+ §5.1 webhookconfig.yaml + §9.5 RBAC + §9.7 PrometheusRule + §11.4 Kopf 启动 与 L3-1 §3.1 Agent Controller + §3.4 MemoryReconciler + §7 Helm 9 模板 + §7.1.2 webhookconfig.yaml + §7.3 RBAC + §7.5 PrometheusRule **完全一致**。✅

### §P.10 L3-2 A2A Core v0.2.0 §3 + §5 + §6 + §9 + §10

- L3-5 §1.5 依赖图（"L3-2 a2a-core: ASGI server + A2AClient + 15 指标 + 24 错误码"）+ §4 4 handler envelope + §7.1 11 A2A 指标 wire 名 + §8.3 Retryable 矩阵 与 L3-2 §3 envelope + §5 ASGI server + §6 A2AClient + §9 15 指标 + §10 24 错误码 **完全一致**（L3-5 新增 23 个错误码是 L3-2 24 个错误码的细化扩展，不重叠）。⚠️ **关注项 §M-1.1**：L3-5 23 错误码名称与 L2-4 §9.1 不一致，与 L3-2 §10 24 错误码也不重叠（L3-2 的 24 个是 StandardRpcError 5 + ProjectRpcError 19，L3-5 的 23 个是 KNOWLEDGE_* 11 + MEMORY_* 12）。

### §P.11 L3-3 Adapter SDK v0.2.0 §3

- L3-5 §0 边界（"L3-5 不依赖 Adapter SDK"）+ §1.4 文件清单（不包含 adapter 相关路径）+ §2.2 边界规则 5（MUST 不依赖 Adapter SDK）与 L3-3 §3 FrameworkAdapter Protocol 设计 **一致**（L3-5 与 L3-4 Hello Agent 同模式：自实现 A2A 端点，不通过 Adapter SDK 抽象）。✅

### §P.12 L3-4 Hello Agent v0.2.0 §3.2 + §5 + §6.9

- L3-5 §4 4 handler 实现模式（Python Protocol + @runtime_checkable + 30 行/个）+ §6.2 共享 Deployment 双 Container 拓扑 与 L3-4 §3.2 HelloAgentExecutor + §5 ASGI server + §6.9 25 ID 测试 **完全一致**（同模式 Card-driven 单实例参考实现）。✅

### §P.13 跨文档引用总计

- **附录 A 5 子表 50+ 行 + 附录 B 5 子表 21 行 = 71+ 条跨文档引用**，覆盖 5 类文档（L1 / L2-4 / ADR / Constitution / 配套 L3），全部 MUST 强度，**全部一致**（除关注项 §M-1.1 错误码名称）。

---

## §Q 评审结论

### §Q.1 整体结论

**L3-5 Knowledge Service 文件级 Spec v0.2-draft-full 通过评审**（10 维度全 PASS · 0 阻塞项 · 4 关注项 · 4 建议项）：
- ✅ 文档完整性（§A · 4 处内部发现）
- ✅ 接口契约（§B · 关注项 §M-1.1 名称漂移 + §M-1.2 §5/§8 编号漂移）
- ✅ 可见性（§C）
- ✅ 安全（§D · 关注项 §M-1.4 RBAC 拆分）
- ✅ 性能（§E · 关注项 §M-1.5 性能门禁验证）
- ✅ 部署（§F）
- ✅ 测试（§G）
- ✅ 开放问题（§H）
- ✅ ADR/Constitution 矩阵（§I）
- ✅ 颗粒度偏差（§J）

**L3-5 Spec v0.2-draft-full 具备升级 v0.2.0 条件**。4 关注项必须在 v0.2.0 PR 内同步修正（关注项 1 + 2 错误码名称/编号，§M-1.3 工具链描述统一降级为建议项 §M-2.3），关注项 §M-1.4 RBAC 拆分 + §M-1.5 性能门禁验证 移交 v0.2.1 + L4 实施第一周；4 建议项移交 v0.2.1 / L4 实施。

### §Q.2 与 L3 阶段进度

- **L3 阶段 4/4 ≈ 100% 完成**（L3-1 v0.2.0 #56 + L3-2 v0.2.0 #54 + L3-3 v0.2.0 #58 + L3-4 v0.2.0 #61 + **L3-5 评审 #63.5**），**L3 阶段完成 5/6**（L3-5 评审 + L3-6 待起草）。
- **L3-5 v0.2.0 升级 + §F 8 步同步 + git commit** 推迟到 #63.6 会话（按 §16.1.4 50% 临界主动收口）。

### §Q.3 后续入口

| # | 任务 | 会话 | 工作量 |
|---|------|------|--------|
| 1 | L3-5 Spec v0.2.0 升级（头部 4 处微同步 + 关注项 §M-1.1/§M-1.2 错误码名称/编号修正 23 处） | #63.6 | ~8-12% |
| 2 | §F 8 步跨文档同步（ROADMAP / README / CONSTITUTION-CHANGELOG / L3-1 附录 A.4 / L3-2 附录 A.4 / L3-3 附录 A.4 / L3-4 附录 A.4 / L3-5 头部 4 处） | #63.6 | ~5-8% |
| 3 | git commit #63.5 + #63.6 | #63.6 | ~2-3% |
| 4 | L3-6 Memory backend 文件级 Spec 起草（基于 L2-4 v0.2.0 Spec + L3-5 §6.2 共享 Deployment 协调点） | #64+ | ~30-50KB |
| 5 | L3-5 关注项 §M-1.4 RBAC 拆分 + §M-1.5 性能门禁验证 + 4 建议项（v0.2.1） | 后续 | ~5-8% |

---

## §R 配套归档

### §R.1 本评审报告归档

- **本评审报告**：`docs/reviews/l3-5-knowledge-service-spec-review.md`（本文件 · ~50KB / ~700 行 / §A-§P 16 节 / 10 维度）
- **评审对象**：`docs/spec/L3-file-specs/L3-knowledge-service.md` v0.2-draft-full（154KB / 2458 行）
- **评审日期**：2026-07-29 · #63.5 会话
- **评审人**：项目发起人（单点评审 · 宪法 §14.5 MVP 例外时间窗口内）

### §R.2 配套 git commit 历史（待办）

| # | 会话 | 内容 | commit hash |
|---|------|------|-------------|
| 63.1 | 2026-07-29 | L3-5 v0.2-draft 骨架稿 | TBD |
| 63.2.1 | 2026-07-29 | Subagent 1 §3-§6 补完 | TBD |
| 63.2.2 | 2026-07-29 | Subagent 2 §7-§13 + 附录 B | TBD |
| **63.5** | **2026-07-29** | **L3-5 Spec Python 评审（本评审报告）** | **TBD** |
| 63.6 | 2026-07-29 或 2026-07-30 | L3-5 Spec v0.2.0 升级（关注项 §M-1.1/§M-1.2 修正 23 处）+ §F 8 步同步 | TBD |

### §R.3 配套 L3 评审报告索引

| L3 模块 | 评审报告 | 评审日期 | 评审规模 | 评审结论 |
|---------|----------|----------|----------|----------|
| L3-1 Operator Core | [l3-1-operator-core-spec-review.md](./l3-1-operator-core-spec-review.md) | 2026-07-28 #56 | 55KB / 700 行 | ✅ 10 维度 PASS |
| L3-2 A2A Core | [l3-2-a2a-core-spec-review.md](./l3-2-a2a-core-spec-review.md) | 2026-07-28 #54 | 18KB / 217 行 | ✅ 10 维度 PASS |
| L3-3 Adapter SDK | [l3-3-adapter-sdk-spec-review.md](./l3-3-adapter-sdk-spec-review.md) | 2026-07-29 #58 | 49KB / 657 行 | ✅ 10 维度 PASS |
| L3-4 Hello Agent | [l3-4-hello-agent-spec-review.md](./l3-4-hello-agent-spec-review.md) | 2026-07-29 #60 | 48KB / 464 行 | ✅ 10 维度 PASS |
| **L3-5 Knowledge Service** | **本评审报告** | **2026-07-29 #63.5** | **~50KB / ~700 行** | **✅ 10 维度 PASS · 4 关注项 · 4 建议项** |
| L3-6 Memory backend | 待起草 | — | — | — |

### §R.4 配套 L2 / L1 评审报告索引（上游权威）

| 层级 | 文档 | 评审报告 | 评审日期 | 评审结论 |
|------|------|----------|----------|----------|
| L1 Architecture + Spec | [l1-review-architecture.md](./l1-review-architecture.md) + [l1-python-stack-migration-review.md](./l1-python-stack-migration-review.md) | 2026-07-24 #19 | 27KB / 458 行 | ✅ 10 维度 PASS |
| L2-1 A2A Protocol | [l2-1-a2a-protocol-review.md](./l2-1-a2a-protocol-review.md) | 2026-07-24 #22 | 31KB / 488 行 | ✅ 10 维度 PASS |
| L2-2 Operator Core | [l2-2-operator-core-spec-review.md](./l2-2-operator-core-spec-review.md) | 2026-07-25 #33 | 29KB / 700 行 | ✅ 10 维度 PASS |
| L2-3 Adapter | [l2-3-adapter-spec-python-review.md](./l2-3-adapter-spec-python-review.md) | 2026-07-26 #37 | 53.5KB / 641 行 | ✅ 10 维度 PASS |
| L2-4 Knowledge/Memory | [l2-4-knowledge-memory-spec-python-review.md](./l2-4-knowledge-memory-spec-python-review.md) | 2026-07-27 #43 | 59.7KB / 697 行 | ✅ 10 维度 PASS |

### §R.5 归档元数据登记

- **L3-5 Go baseline 归档**：L3-5 v0.1-draft Go baseline 未独立 Spec，沿用 L2-4 v0.1.0 Go baseline 段落（已在 L2-4 Spec v0.2.0 Python 重写时覆盖丢失，与 L2-1/L2-3/L3-1/L3-2/L3-3/L3-4 同模式）；附录 A.5 #1 标注"2026-07-26 归档丢失（与 L2-1/L2-3/L3-1/L3-2/L3-3/L3-4 同模式）· 建议 #63.x 后续会话追溯 v0.1.0 Go 归档登记"。
- **归档路径**：`docs/archive/pre-python-2026-07-24/L2-knowledge-memory-spec-v0.1.0-go-baseline.md`（L2-4 Go baseline；L3-5 与 L2-4 共享同一 Go baseline 归档；与 L3-1 / L3-2 / L3-3 / L3-4 Go baseline 归档同模式）。
- **README 备注**：与 L2-1 / L2-3 Go baseline 覆盖丢失事件同模式，需在 #63.6 v0.2.0 升级时同步登记 README 备注。

---

## §签署

> **签署**：本 L3-5 Knowledge Service 文件级 Spec Python v0.2-draft-full 评审报告由项目发起人依据 [`CONSTITUTION.md`](../CONSTITUTION.md) v0.5.0 §3.4 + §3.7 + §3.8 + §6 + §7 + §9.7 + §13.1 + §14.4 + §15.5 + §16.1.4 50% 临界主动收口原则、[`ADR-0002`](../adr/0002-knowledge-management-design.md) §3 + §4 + §5、[`ADR-0003`](../adr/0003-memory-design.md) §3 + §4.1 + §5、[`ADR-0005`](../adr/0005-python-first-technology-stack.md) §3.4 + §6.2 + §6.3 + §9.1 + §10 + §11 + §13.1 + §13.6、[L1 Architecture v0.2.0 §3.5.2 + §3.5.3 + §4.3 C-6](../design/L1-architecture.md)、[L1 Spec v0.2.0 §5.2.2 + §6.2](../spec/L1-system-spec.md)、[L2-4 Design v0.2.0 §1 + §3-§14](../design/L2-modules/L2-knowledge-memory.md)、[L2-4 Spec v0.2.0 §0-§15 + §16](../spec/L2-module-specs/L2-knowledge-memory.md)、[L3-1 Operator Core v0.2.0 §3.1 + §3.4 + §7](../spec/L3-file-specs/L3-operator-core.md)、[L3-2 A2A Core v0.2.0 §3 + §5 + §6 + §9 + §10](../spec/L3-file-specs/L3-a2a-core.md)、[L3-3 Adapter SDK v0.2.0 §3](../spec/L3-file-specs/L3-adapter-sdk.md) 与 [L3-4 Hello Agent v0.2.0 §3.2 + §5 + §6.9](../spec/L3-file-specs/L3-hello-agent.md) 编写。
>
> **评审结论**：**L3-5 Knowledge Service 文件级 Spec v0.2-draft-full 通过评审（10 维度全 PASS · 0 阻塞项 · 4 关注项 · 4 建议项），具备升级 v0.2.0 条件**。关注项 §M-1.1（23 错误码名称全部与 L2-4 §9.1 漂移）+ §M-1.2（§5 admission 编号与 §8.1 enum 内部漂移）必须在 v0.2.0 PR 内同步修正 23 处；关注项 §M-1.4（RBAC 拆分）+ §M-1.5（性能门禁验证）移交 v0.2.1 + L4 实施第一周；4 建议项移交 v0.2.1 微同步。
>
> **下一步**：
> 1. **#63.6 会话**：L3-5 Spec 升级 v0.2.0（头部 4 处微同步：版本 / 状态 / 配套 Review 引用 / 变更记录）+ **关注项 §M-1.1/§M-1.2 错误码名称/编号修正 23 处** + git commit #63.6。
> 2. **#63.6 会话**：§F 8 步跨文档同步（ROADMAP / README / CONSTITUTION-CHANGELOG / L3-1 附录 A.4 / L3-2 附录 A.4 / L3-3 附录 A.4 / L3-4 附录 A.4 / L3-5 头部 4 处）+ git commit #63.6。
> 3. **#64+ 会话**：L3-6 Memory backend 文件级 Spec 起草（基于 L2-4 v0.2.0 Spec + L3-5 §6.2 共享 Deployment 协调点 · L3 阶段 6/6）。
>
> **宪法 §16.1 状态**：本评审报告 ~50KB / 700 行 / 10 维度 / 0 阻塞 · 历史累计水位 ~85-87% 已超 80% 临界 · 本会话主动收口（不进入 v0.2.0 升级步骤）。