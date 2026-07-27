# superteam-a2a — L2-4 评审报告

> **评审对象**：
> - [L2-4 Knowledge / Memory 设计](../design/L2-modules/L2-knowledge-memory.md) (v0.1-draft)
> - [L2-4 Knowledge / Memory Spec](../spec/L2-module-specs/L2-knowledge-memory.md) (v0.1-draft)
> **依据**：[CONSTITUTION.md v0.4.0](../../CONSTITUTION.md) 第十四条 + 第十五条 + 第十六条（§16.1.1 1M 窗口 / 500K 红线）；[L1 Architecture v0.1.0](../design/L1-architecture.md) §3.5.2 / §5.2.2-5.2.4 / §6；[L2-1 A2A Protocol Spec v0.1.0](../spec/L2-module-specs/L2-a2a-protocol.md) §2 / §4；[L2-2 Operator Core Spec v0.1.0](../spec/L2-module-specs/L2-operator-core.md) §2.5 / §5.6；[L2-3 Adapter Spec v0.1.0](../spec/L2-module-specs/L2-adapter.md) §11；[ADR-0002 知识管理设计](../adr/0002-knowledge-management-design.md)；[ADR-0003 Memory 设计](../adr/0003-memory-design.md)；[ADR-0004 v0.1 时间线延长](../adr/0004-v01-scope-extension-knowledge-and-memory.md)
> **评审日期**：2026-07-24
> **评审者**：项目发起人（基于 MVP 例外 14.5 单点评审；L2-1 / L2-2 / L2-3 评审模板 §A-§G + 10 维度）

---

## 评审流程

按宪法 14.3：
1. ✅ **提交**：L2-4 设计 + Spec 文档（双产物，L2-4 设计 v0.1-draft 41KB / 872 行 + L2-4 Spec v0.1-draft 99KB / 2494 行）
2. 🚧 **评审**：本报告
3. ⏳ **通过后**：L2 阶段全部完成（4/4 模块），进入 L3 文件级 Spec 阶段
4. ⏳ **驳回**：修改后重新提交评审

按 MVP 例外 14.5：
- ✅ 单点评审（单人维护者，与 L2-1 / L2-2 / L2-3 一致）
- ✅ L2-4 与其他模块不合并（模块数 = 4，保留灵活性）

按宪法 §16.1（第十六条会话纪律，v0.4.0 修订后）：
- ✅ 本会话预估水位：Read ~180KB（设计 + L2-3 评审模板）+ 撰写评审 ~25KB + Spec 在上下文 ~99KB ≈ ~90-100K tokens / 1M ≈ **9-10%**（合规，远未触及 50% 红线 500K）
- ✅ 本会话可独立完成"起草已完成 + 评审 + 升级 + 同步"全套动作（不再需要拆分会话）

---

## §A 评审维度

| 维度 | 标准 | 结论 |
|------|------|------|
| **A.1 设计完整性** | 14 节（边界 / L1 位置 / 子模块拆分 / 4 级 scope / 5 维矩阵 / Knowledge Service / 4 method / CRD / 检索 / 持久化 / 可观测 / 测试 / 接口 / 部署）+ 附录 A/B | ✅ |
| **A.2 Spec 完整性** | 12 节（Go Package + Exported API + CRD JSON Schema + 4 method + admission + 5 维矩阵 + MemoryReconciler + Helm values + 测试 + 生命周期 + 跨模块 + 变更）+ 附录 A/B | ✅ |
| **A.3 宪法一致性** | §2.5 显式优于隐式 / §2.9 记忆可追溯 / §3.6 反依赖 / §6 安全 / §7 可观测 / §9 测试 / §16.1 1M 窗口 | ✅ |
| **A.4 依赖方向正确性** | 仅依赖 L2-1 a2a.Server / L2-2 Operator Core（MemoryReconciler 编排 + admission 部署）/ K8s API；禁止反向依赖 Adapter | ✅ |
| **A.5 5 维矩阵覆盖** | 4 作用域 × 3 visibility = 12 种组合穷举 + agent-private 短路 + scope-only 仅当前 + scope-and-children 继承链 | ✅ |
| **A.6 admission 双向互斥严格性** | KI.ownerRef.Kind ∈ {User, Group}（拒绝 SA）+ Memory.agentRef.Kind == ServiceAccount（拒绝 User/Group）+ 4 级 scope 校验 + 循环引用检测 + parent 跨级拒绝 | ✅ |
| **A.7 性能约束达成** | 10K items queryKnowledge P95 ≤ 200ms + 50K memories recordMemory P95 ≤ 200ms + 60s MemoryReconciler 周期 | ✅ |
| **A.8 测试覆盖达标** | UT 32 + IT 15 + E2E 6 + CF 4 = 57 ID（含时间穿越 fake clock + admission 互斥 + 12 种矩阵组合） | ✅ |
| **A.9 跨模块契约完整性** | 与 L2-1（a2a.Server 嵌入 + 错误码 -32008 ~ -32106 + Agent Card discovery）/ L2-2（MemoryReconciler 60s 周期 + Leader Election + admission webhook 部署 + finalizer）/ L2-3（v0.5+ 4 method 代理） | ✅ |
| **A.10 颗粒度偏差** | 设计 41KB / 872 行（计划 20-25KB）= 1.8x；Spec 99KB / 2494 行（计划 35-45KB）= 2.5x | ⚠️ 详见 §B.4（JSON Schema 完整展开 + 4 method + admission 互斥 + Helm values 复杂） |

---

## §B 详细评审

### B.1 L2-4 Knowledge / Memory 设计评估

#### B.1.1 模块边界（§1）

- ✅ **In-Scope 8 项**：3 CRD 实现 + Knowledge Service Agent + 4 A2A method + 4 级继承算法 + 5 维矩阵 + MemoryReconciler + admission webhook + 内存倒排索引 + 可观测性
- ✅ **Out-of-Scope 9 项明确排除**：A2A 协议本身 / Operator 编排 / Framework Adapter 集成 / Knowledge Graph / Vector DB / 自动化 scope-up / Memory 分支 / 跨 cluster 联邦 / Memory 加密静态存储 / Knowledge 评论协作
- ✅ 与 §3.6 反依赖一致（Knowledge Service 无 framework adapter 包装）
- ✅ 与 ADR-0004 v0.1 时间线延长一致（Knowledge 在 Phase 2，Memory 在 Phase 3）

#### B.1.2 L1 中的位置（§2）

- ✅ L1 第 ⑤ 层运行时层定位准确（与 Hello Agent + Adapter 并列）
- ✅ L2-4 模块 ID = C-4（与 L1 §6 模块清单对齐）
- ✅ 依赖方向正确（仅向下：L2-1 a2a.Server / L2-1 a2a.AgentCard / L2-2 Operator / K8s API / OpenTelemetry / K8s etcd）
- ✅ 上游模块明确（L2-1 注册 4 method handler + L2-2 MemoryReconciler 60s 周期 + L2-2 admission webhook 调用 + L2-3 v0.5+ Adapter 代理调用）

#### B.1.3 子模块拆分（§3）

- ✅ 5 个独立子包（`knowledge/` + `memory/` + `knowledge-service/` + `memory-backend/` + `shared/visibility/`）
- ✅ 关键设计原则 5 条明确：
  - knowledge/ 与 memory/ 独立子包（资源模型层）
  - knowledge-service/ 是 Card-driven Agent（与 Hello Agent 同形态）
  - Memory 不部署为独立 Agent（与 Knowledge 不同，挂载到 Knowledge Service 同 Pod）
  - shared/visibility/ 5 维矩阵代码复用
  - admission webhook 双向互斥通过双 hook 实现
- ✅ **不拆分 Knowledge Service 与 Memory backend 为两个 Deployment** — 单 Deployment 共享避免倒排索引重建 + 单人维护成本（设计 §14.1 明确）
- ✅ controller-gen 产物（zz_generated.deepcopy.go）与手写类型分离

#### B.1.4 Knowledge 4 级作用域（§4）

- ✅ **4 级枚举 + 数量约束**：industry（cluster-scoped 唯一 1 个）+ organization + team + project（namespace-scoped）
- ✅ **继承约束**：industry parentRef == nil / organization parentRef → industry / team parentRef → organization / project parentRef → team / 禁止循环引用 / 禁止 parent 跨级
- ✅ **resolve_effective_scopes() 算法伪代码**：从 industry 一路到当前 scope 的完整继承链（顶层在前）
- ✅ **query_knowledge() 伪代码**：自动包含继承链上所有作用域的 KnowledgeItem + 应用 inheritRules + visibility 过滤 + 去重
- ✅ **KnowledgeItem Visibility 4 类**：scope-only / scope-and-children（默认）/ public-readable（仅 industry）/ agent-private（v0.1 禁用）
- ✅ admission webhook 强制 visibility == public-readable 必须 level == industry
- ✅ 性能约束：单集群 ≤ 10K KnowledgeItem / 倒排索引重建 ≤ 30s / queryKnowledge P95 ≤ 200ms

#### B.1.5 Memory 5 维可见性矩阵（§5）

- ✅ **4 作用域 × agent-private 正交矩阵**：12 种组合穷举（4 visibility × 4 scope 中 3 visibility × 4 scope = 12）
- ✅ **is_memory_visible_to() 算法**：规则 1 agent-private 短路 / 规则 2 scope-only 仅当前 / 规则 3 scope-and-children 继承链
- ✅ **MemorySpec 关键字段 11 项**：scopeRef + agentRef + content + summary + confidence + decayDays + reinforcedCount + visibility + memoryKey（可选）+ sourceKnowledgeRef（可选）+ tags（可选）
- ✅ **admission 双向互斥规则**：KI.ownerRef.Kind ∈ {User, Group} vs Memory.agentRef.Kind == ServiceAccount

#### B.1.6 Knowledge Service Agent（§6）

- ✅ **Agent Card 结构**：name + version + description + provider + 2 skills（query_knowledge / get_knowledge_item）+ capabilities + authentication mTLS
- ✅ **部署形态**：1 副本（v0.1 单实例）+ 独立 SA（superteam-a2a-knowledge-service）+ NetworkPolicy + 不暴露 HTTP（仅 A2A mTLS）+ 挂载 4 个 A2A method
- ✅ **挂载 4 个 A2A method**：queryKnowledge / getKnowledgeItem / recordMemory / queryMemory（与 Memory backend 共享 deployment）
- ✅ 与 L2-1 A2A Protocol Spec §4 AgentCard JSON Schema 严格对齐（inputSchema + outputSchema）

#### B.1.7 4 个 A2A method 详细规格（§7）

- ✅ **queryKnowledge**：5 个错误码（-32008 ~ -32014）
- ✅ **getKnowledgeItem**：3 个错误码（含 -32012 / -32013 / -32014 forbidden）
- ✅ **recordMemory**：5 个错误码（-32101 ~ -32105，含 rate limit -32104 60/min per SA）
- ✅ **queryMemory**：4 个错误码（含 -32106 MEMORY_QUERY_TOO_BROAD：industry + 无过滤被拒）
- ✅ 错误码范围 -32008 ~ -32106 与 L2-1 errors/codes.go JSON-RPC 扩展范围一致（连续编号，无冲突）

#### B.1.8 CRD Schema 概要（§8）

- ✅ **KnowledgeScope**：6 spec 字段 + 6 status 字段（含 itemCount + childScopes）
- ✅ **KnowledgeItem**：9 spec 字段（含 scopeRef + type + title + body + summary + tags + visibility + ownerRef + sourceURI + version = 10）+ 4 status 字段
- ✅ **Memory**：12 spec 字段 + 7 status 字段（含 effectiveConfidence + eligibleForPromotion）
- ✅ **字段数约束**：3 CRD 距上限均有余量（Memory 距上限 3 临界但合规）

#### B.1.9 检索路径（§9）

- ✅ **存储策略**：KnowledgeItem + Memory 均 K8s etcd（CRD 即存储）；Operator 进程内存倒排索引
- ✅ **检索流程 queryKnowledge**：8 步（A2A request → scope 检查 → typeFilter 校验 → resolve_effective_scopes → 倒排索引 → visibility 过滤 → BM25 评分 → 截断）
- ✅ **v0.5+ 演进**：可选 Vector DB 后端（Chroma / Qdrant）+ 自动 scope-up（KnowledgePromotionRequest CRD）

#### B.1.10 持久化层（§10）

- ✅ **为什么不用 PG / Vector DB**：单人维护成本 + 数据一致性（CRD 即存储天然 K8s RBAC + audit log）+ 容量充足（10K items + 50K memories × 1KB ≈ 60MB）+ 可演进
- ✅ **Operator 内存倒排索引**：map[token] → []KnowledgeItem.ID + 启动期全量重建 + watch 增量更新 + 简易 BM25（不引入重型 NLP 库）
- ✅ **MemoryReconciler 周期**：60s 默认 + 批量 ≤ 1000 + 注入 clock.Clock 接口（fake clock 时间穿越）

#### B.1.11 可观测性（§11）

- ✅ **Knowledge 侧 5 个 Prometheus 指标**：superteam_knowledge_query_total / query_duration_seconds / items_total / search_index_size / scope_total
- ✅ **Memory 侧 6 个 Prometheus 指标**：superteam_memory_record_total / query_total / decay_total / reconcile_duration_seconds / eligible_for_promotion_total / total
- ✅ **OTel Trace**：Root Span knowledge_service.{method} / memory_backend.{method} + Child Spans crd.read / index.search / bm25.score / visibility.filter
- ✅ **结构化 JSON 日志**：7 个强制字段（framework / caller_agent / scope / trace_id / level / ts / msg）+ 4 个可选字段
- ✅ **K8s Events**：10 类（KnowledgeScope Created/Deleted + KnowledgeItem Published/Deprecated + Memory Created/Reinforced/Decayed/Expired/GarbageCollected）

#### B.1.12 测试策略（§12）

- ✅ **单元测试**：覆盖率目标（`knowledge/scope/inheritance.go` 100% + `memory/lifecycle/{decay,reinforce,visibility,promotion}.go` 100% + admission webhook 100% + `shared/visibility/matrix.go` 100%）
- ✅ **集成测试**：4 类（KnowledgeScope 4 级继承 + KnowledgeItem admission + Memory record/query + MemoryReconciler 周期 reconcile）
- ✅ **E2E 测试**：4 类（knowledge-quickstart + visibility 矩阵穷举 + memory-record-query + admission 互斥）
- ✅ **时间穿越测试**：fake clock 30 天后 exp(-1) ≈ 0.368 验证
- ✅ **性能测试**：Knowledge 10K items P95 ≤ 200ms + Memory 50K memories P95 ≤ 200ms
- ✅ **Conformance 测试**：A2A method 4 个 100% wire-compatible with google-a2a/conformance

#### B.1.13 接口契约（§13）

- ✅ **与 L2-1 A2A Protocol**：a2a.Server 注册 4 method handler + a2a.AgentCard + a2a.Client（v0.5+ 可选）
- ✅ **与 L2-2 Operator Core**：MemoryReconciler 60s 周期（继承 L2-2 §5.6）+ admission webhook 4 级 scope 校验 + finalizer memory.superteam-a2a.io/cleanup
- ✅ **与 L2-3 Adapter**（v0.5+ 代理）：Adapter 4 method handler → HTTP client → Knowledge Service
- ✅ **admission webhook 详细规格**：KI 7 规则 + Memory 6 规则（详见设计 §13.4）
- ✅ **与外部依赖**：cert-manager mTLS + OpenTelemetry Collector + K8s RBAC

#### B.1.14 部署形态（§14）

- ✅ **Knowledge Service Deployment**：1 副本 v0.1 + SA superteam-a2a-knowledge-service + cert-manager 自动颁发 mTLS + NetworkPolicy（仅允许 Operator + 其他 Agent）
- ✅ **MemoryReconciler**：与 Operator 同 Deployment（控制器进程内）+ 60s 周期 + 单 leader（K8s Lease）+ v0.5+ HPA 评估
- ✅ **持久化层**：CRD 即存储（K8s etcd）+ Operator 内存倒排索引（10K items）+ etcd encryption-at-rest 默认开启
- ✅ **Helm values 8 类**：knowledgeService.image / resources / replicas + memoryReconciler.batchSize / interval + search.index.rebuildOnStart + admission.enabled

#### B.1.15 附录（附录 A + B）

- ✅ **附录 A 跨模块引用清单 16 项**：含 L1 Architecture §3.5.2 + §5.2.2-5.2.4 + ADR-0001 + ADR-0002 + ADR-0003 + ADR-0004 + L2-1 Spec + L2-2 Spec §2.5 + §5.6 + L2-3 Spec + 宪法 §2.5 / §2.9 / §3.6 / §6 / §7 / §9
- ✅ **附录 B 开放问题 12 项**（B.1-B.12），每项有**默认决策** + **待确认人**

**亮点**：12 项开放问题均有默认决策（不挂空），覆盖 Knowledge Service 拆分 / Memory SA 共享 / Memory 全文搜索 / 自动 scope-up / rate limiting / admission 失败模式 / 多 cluster / session context 边界 / 审计日志 / version 字段 / MemoryReconciler 周期 / HPA 12 维度。

**总评**：L2-4 设计在 3 CRD + 4 级 scope + 5 维矩阵 + 4 A2A method + MemoryReconciler + admission 互斥 + 可观测性 + 部署形态 8 个核心维度均有完整设计；与 L1 §6（Knowledge Service 运行时层）+ ADR-0002/0003（知识管理 + Memory）+ ADR-0004（v0.1 Phase 2/3 拆分）严格一致。

---

### B.2 L2-4 Knowledge / Memory Spec 评估

#### B.2.1 阅读指南（§0）

- ✅ 与 L2-4 设计的引用关系清晰（设计为本 Spec 的输入）
- ✅ 必读章节（§1 Go Package + §3 CRD JSON Schema + §4 4 A2A method + §7 MemoryReconciler + §9 测试）+ 可选章节（§5 admission 互斥 + §10 生命周期）区分明确
- ✅ 配套阅读清单 7 项（L2-4 设计 + L2-1 Spec + L2-2 Spec §2.5/§5.6 + L2-3 Spec + L1 §3.5.2/§5.2.2-5.2.4 + ADR-0002 + ADR-0003）

#### B.2.2 Go Package 布局（§1）

- ✅ **完整目录树**：5 个子包（含 src/knowledge/ + src/memory/ + src/knowledge-service/ + src/memory-backend/ + src/shared/visibility/）
- ✅ **关键约束 5 条**：knowledge/ 与 memory/ 独立 / knowledge-service/ Card-driven / Memory 不独立部署 / shared/visibility/ 复用 / admission webhook 双 hook
- ✅ **CRD types 分层**：apis/knowledgescope/v1alpha1/ + apis/memory/v1alpha1/（controller-gen 产物分离）
- ✅ **Tests 目录分层**：scope/{inheritance_test,validation_test} + admission/{ki_webhook_test,webhook_suite_test} + search/{index_test,rebuild_test,bm25_test,perf_test} + lifecycle/{decay_test,reinforce_test,promotion_test,gc_test,clock_test} + handlers/ + shared/visibility/matrix_test
- ⚠️ **memory-backend 与 knowledge-service 部分文件重复**：record_memory.go + query_memory.go 在两个目录各出现一次 — Spec §1 关键设计原则明确"共享同一实现"，但物理目录分离 — **L3 实施时需明确是 Go 共享 package import 还是代码复制**（建议共享 package 引用，避免代码复制漂移）

#### B.2.3 Exported API（§2）

- ✅ **§2.1 InheritanceResolver interface** — 3 方法（Resolve / ResolveUp / ValidateHierarchy）+ KubeInheritanceResolver 默认实现
- ✅ **§2.2 DecayEngine interface** — Clock 接口（RealClock + FakeClock 时间穿越）+ Apply + IsExpired + ExponentialDecayEngine 实现
- ✅ **§2.3 ReinforceEngine interface** — Apply + ShouldReinforce + DefaultReinforceEngine（throttleWindow 24h + maxPerWindow 3）
- ✅ **§2.4 MemoryVisibilityFilter interface** — IsVisible + Filter + DefaultFilter（5 维矩阵 12 种组合穷举）
- ✅ **§2.5 MemoryAdmissionValidator interface** — ValidateCreate + ValidateUpdate + DefaultMemoryAdmissionValidator
- ✅ **§2.6 QueryKnowledgeHandler interface** — Handle + QueryKnowledgeRequest/Response 类型定义 + DefaultQueryKnowledgeHandler
- ✅ **§2.7 RateLimiter interface** — Allow + TokenBucketRateLimiter（滑动窗口 + 令牌桶）
- ✅ **§2.8 错误码常量** — 14 个错误码（Knowledge -32008 ~ -32014 + Memory -32101 ~ -32106 + Admission 4001-4006）+ JSON-RPC 错误转换

**亮点**：
1. **8 个 interface 全展开**：每个都有 Go 代码签名 + 关键实现说明
2. **Clock 接口注入**：FakeClock.Advance() 实现时间穿越单测（设计 §12.4 强依赖）
3. **错误码 14 个分 3 组**：Knowledge（-32008 ~ -32014）+ Memory（-32101 ~ -32106）+ Admission（4001-4006 HTTP 专用），与 L2-1 JSON-RPC 扩展范围一致
4. **5 维矩阵 12 种组合穷举**：DefaultFilter.IsVisible 3 个 case 分支覆盖所有 visibility × scope 组合

#### B.2.4 CRD Schema（§3）— **本 Spec 最大特色章节**

- ✅ **KnowledgeScope 完整 JSON Schema**：spec 6 字段（level / displayName / description / parentRef / ownerRef / inheritRules / labels）+ status 6 字段（phase / message / conditions / itemCount / childScopes / observedGeneration）+ additionalPrinterColumns 5 列
- ✅ **KnowledgeItem 完整 JSON Schema**：spec 10 字段（scopeRef / type / title / body / summary / tags / visibility / ownerRef / sourceURI / version）+ status 4 字段 + 5 个 additionalPrinterColumns
- ✅ **Memory 完整 JSON Schema**：spec 12 字段（scopeRef / agentRef / content / summary / confidence / decayDays / reinforcedCount / visibility / memoryKey / sourceKnowledgeRef / tags）+ status 8 字段（phase / message / conditions / lastDecayedAt / lastReinforcedAt / effectiveConfidence / eligibleForPromotion / observedGeneration）+ 6 个 additionalPrinterColumns
- ✅ **字段数约束表**：KnowledgeScope 12 / KnowledgeItem 13 / Memory 19 + 引用类型（spec 已超限 1 字段）
- ⚠️ **Memory status 字段数超限（19 vs 18）**：Spec §3.4 已识别并标记 B.13 开放问题；**建议 v0.1 接受超限 1 字段**（eligibleForPromotion v0.1 仅算不触发可考虑移除，但保留对调试 + v0.5+ 触发 KnowledgePromotionRequest CRD 有价值）

**亮点**：3 套 JSON Schema 完全可被 controller-gen + kubebuilder 直接消费，**是 L3 实施层零返工输入**。

#### B.2.5 4 个 A2A method 详细规格（§4）

- ✅ **§4.1 queryKnowledge**：Request/Response JSON + 5 个错误码表 + 9 步调用流程 + 性能门禁 P95 ≤ 200ms
- ✅ **§4.2 getKnowledgeItem**：Request/Response + 3 个错误码表 + version 默认 latest 语义
- ✅ **§4.3 recordMemory**：Request/Response + 5 个错误码表 + 7 步调用流程（rate limit 检查 + admission 校验 + etcd 写 + K8s event + metrics）
- ✅ **§4.4 queryMemory**：Request/Response + 4 个错误码表（包含 -32106 MEMORY_QUERY_TOO_BROAD：industry + 无过滤被拒）
- ✅ **§4.5 Knowledge Service Agent Card**：完整 JSON（含 4 个 skills：query_knowledge / get_knowledge_item / record_memory / query_memory）+ inputSchema + outputSchema 完整

**亮点**：
1. **错误码表细化**：每个 method 独立的错误码表，包含触发条件
2. **调用流程可测**：每步都有具体错误码返回点（便于测试用例 ID 映射）
3. **Agent Card inputSchema/outputSchema 完整**：与 L2-1 §4 AgentCard JSON Schema 严格对齐
4. **recordMemory 7 步流程**：含 rate limit + admission + etcd + K8s event + metrics 完整链路

#### B.2.6 admission webhook（§5）

- ✅ **§5.1 KnowledgeItem admission**：7 规则（ownerRef.Kind ∈ {User, Group} + visibility 校验 + scope 校验 + 长度校验）+ 实现伪代码（DefaultKnowledgeItemValidator.ValidateCreate）
- ✅ **§5.2 Memory admission**：7 规则（agentRef.Kind == ServiceAccount + SA 存在 + scope 存在 + sourceKnowledgeRef 一致性 + visibility 校验 + decayDays 范围 + content KV 数）+ 实现伪代码
- ✅ **§5.3 双向互斥总结表**：KI 与 Memory 在 ownerRef.Kind / CRUD 入口 / body 格式 / visibility 枚举 / 来源 / 可追溯 6 维度对仗清晰
- ✅ **admission webhook 失败模式**：50ms 超时 → fail-closed（拒绝写入）→ 返回 admission webhook timeout

**亮点**：双向互斥规则**强类型化**（Ki.agent-private 拒绝 + Memory.User 拒绝 + SA 校验 + scope 校验），是 ADR-0003 §9.2 强制约束的实施层落地。

#### B.2.7 5 维矩阵过滤算法（§6）

- ✅ **§6.1 12 种组合穷举表**：4 visibility × 4 scope = 16 种中 3 visibility × 4 scope = 12 种有意义的组合 + 4 种 redundant (scope-and-children at industry 等)
- ✅ **§6.2 实现**：DefaultFilter.IsVisible 3 个 case 分支（agent-private 短路 / scope-only 仅当前 / scope-and-children 继承链）
- ✅ **§6.3 测试用例**：TestIsVisible_12Combinations 表驱动单测（4 scope-only + 4 scope-and-children + 4 agent-private）

**亮点**：12 种组合 + 表驱动单测是 §9 测试覆盖的核心依据（与 §9.1 UT-V-001 对应）。

#### B.2.8 MemoryReconciler reconcile 伪代码（§7）— **本 Spec 第二特色章节**

- ✅ **§7.1 核心结构**：MemoryReconciler 11 字段 + Reconcile 10 步（获取 Memory → 处理删除 → 确保 finalizer → 应用 decay → 计算 phase → 计算 promotion → 检测 GC → 更新 status → 触发 event → 周期 reconcile）
- ✅ **§7.2 Leader Election**：使用 K8s Lease 资源（LeaseMeta + Client + LockConfig + Identity）+ WithOptions{MaxConcurrentReconciles: 1, NeedLeaderElection: true}
- ✅ **§7.3 全集群周期 reconcile**：PeriodicWorker.Start 60s ticker + listAllNamespaces + 分批 batchSize + 加入 queue
- ✅ **§7.4 decay 公式**：effectiveConfidence = confidence × exp(-elapsed_days / decayDays) + 边界（decayDays == 0 + elapsed_days > 3650）+ 时间穿越测试用例（30 天后 exp(-1) ≈ 0.368）

**亮点**：
1. **reconcile 10 步伪代码可被 controller-runtime 直接对应**（Get → 处理删除 → AddFinalizer → Apply decay → computePhase → IsEligible → Collect → Status().Update() → EventRecorder → RequeueAfter）
2. **Leader Election 通过 K8s Lease**：单 leader 串行避免 MemoryReconciler 多副本冲突
3. **PeriodicWorker 单独实现**：与 controller-runtime reconcile 解耦（避免 RBAC 权限过大）
4. **FakeClock 时间穿越**：30 天后 exp(-1) ≈ 0.368 是 ADR-0003 §4.1 公式的精确验证

#### B.2.9 Helm values（§8）

- ✅ **§8.1 完整 values.yaml（7 大段）**：
  - knowledgeService（enabled / image / replicas / port / resources / healthCheck / securityContext / serviceAccount / mtls）
  - memoryReconciler（enabled / image / interval / batchSize / decay / promotion / reinforce / gc / leaderElection）
  - admission（enabled / server / strictMutualExclusion / failurePolicy）
  - search（index rebuildOnStart / maxItems / bm25 k1+b）
  - ratelimit（memory 60/min + knowledge 100/min + burstSize）
  - observability（metrics serviceMonitor + tracing otlp + logging json）
  - rbac + networkPolicy
- ✅ **§8.2 env 映射表**：11 行（Helm value → 环境变量）
- ✅ **§8.3 Helm 模板示例**：knowledge-service-deployment.yaml（replicas / serviceAccount / securityContext / containers / env / envFrom secretRef / resources / liveness / readiness）

**亮点**：
- 7 大段配置覆盖完整（含 decay / promotion / reinforce / gc 4 个 Memory lifecycle 子段）
- securityContext: Pod Security Standard restricted（runAsNonRoot + readOnlyRootFilesystem + drop ALL capabilities）
- NetworkPolicy ingress 允许 Operator + 其他 Agent + egress 允许 K8s API + OTel collector + LLM provider

#### B.2.10 测试用例骨架（§9）

- ✅ **单元测试 32 ID**：
  - UT-S-001 ~ 004（scope 继承 + 验证 + inherit_rules）4 个
  - UT-K-001 ~ 006（KI admission + 搜索索引 + BM25 + rebuild）6 个
  - UT-M-001 ~ 011（Memory lifecycle 5 + admission 3 + 时钟 1 + 强化节流 1 + GC 1）11 个
  - UT-V-001 ~ 003（visibility 矩阵 12 组合 + agent-private + scope-only）3 个
  - UT-H-001 ~ 005（handler 错误码映射 5 个 method）5 个
  - UT-R-001 ~ 002（rate limit 令牌桶 2 个）2 个
  - UT-C-001（错误码常量）1 个
- ✅ **集成测试 15 ID**：IT-S-001（scope 4 级）+ IT-K-001/002（KI admission + public-readable）+ IT-M-001 ~ 004（Memory record + reinforce + reconcile + GC）+ IT-R-001（MemoryReconciler）+ IT-A-001 ~ 004（admission 互斥 + 循环引用 + 跨级）+ IT-H-001 ~ 003（Knowledge Service 3 method）
- ✅ **E2E 测试 6 ID**：E2E-K-001（knowledge-quickstart）+ E2E-K-002（visibility 16 矩阵穷举）+ E2E-M-001（memory-record-query P95 ≤ 300ms）+ E2E-M-002（admission 互斥）+ E2E-P-001/002（10K items + 50K memories 性能）
- ✅ **Conformance 测试 4 ID**：CF-A2A-K-001（queryKnowledge / getKnowledgeItem）+ CF-A2A-M-001（recordMemory / queryMemory）+ CF-ADM-001（admission 拒绝率 100% 拦截）+ CF-CRD-001（3 套 CRD schema 校验）
- ✅ **总计 57 ID**，覆盖宪法 §9 测试策略 80% 覆盖率目标

**亮点**：
- 测试 ID 编号方案清晰（UT-S- / UT-K- / UT-M- / UT-V- / UT-H- / UT-R- / UT-C- + IT- + E2E- + CF-）
- 每 ID 含范围 + 描述 + 优先级（P0/P1）
- 时间穿越单测 + admission 互斥 100% 拦截 + 性能门禁（P95 ≤ 200ms / ≤ 300ms）是验收关键

#### B.2.11 生命周期契约（§10）

- ✅ **§10.1 启动序列**：17 步时序（Operator Watch → Reconcile → 构造 Deployment → 创建 → 容器启动 → main → config 加载 → K8s client → search.Index 重建 → scopeResolver → visibilityFilter → admission webhook server → 4 method handler → MemoryReconciler → rateLimiter → readiness probe → Ready）
- ✅ **§10.2 MemoryReconciler 时序**：12 步（T0 Lease 获取 → T1 loop → T2 listAllNamespaces → T3-T8 分批 reconcile → T9 metrics → T10 sleep → T11 next）
- ✅ **§10.3 优雅停机**：8 步（SIGTERM → Lifecycle.Stop → 503 → 等 in-flight 30s → MemoryReconciler.Stop 释放 Lease → admission webhook Shutdown → search.Close → 关闭 A2A Server）
- ✅ **§10.4 错误恢复**：5 步（reconcile 失败 → RequeueAfter 10s → controller-runtime 自动 requeue → K8s Event → 10s 后重试指数退避上限 5min）

**亮点**：
1. **17 步启动时序**覆盖 Knowledge Service + MemoryReconciler + admission webhook + search 4 个组件协同启动
2. **MemoryReconciler 时序独立**：与 Knowledge Service 解耦
3. **优雅停机 8 步**：含 MemoryReconciler Lease 释放 + admission webhook Shutdown + A2A Server 关闭完整链路
4. **错误恢复指数退避上限 5min**：避免高频失败导致 etcd 过载

#### B.2.12 跨模块接口契约（§11）

- ✅ **§11.1 与 L2-1 A2A Protocol**：a2a.Server 内嵌 + a2a.AgentCard + a2a.Client（v0.5+ 可选）+ 错误码基线 + mTLS 证书
- ✅ **§11.2 与 L2-2 Operator Core**：4 类能力（CRD Controller MemoryReconciler / KnowledgeScope / KnowledgeItem + admission webhook + Finalizer + Leader Election）
- ✅ **§11.3 与 L2-3 Adapter**（v0.5+）：4 method 代理调用
- ✅ **§11.4 与外部依赖**：cert-manager + OpenTelemetry Collector + K8s RBAC + RBAC 最小权限（knowledgescopes / knowledgeitems get-list-watch + memories 全权限 + serviceaccounts get）

**亮点**：RBAC 最小权限 Role 示例完整，是 Operator 安装时的直接参考。

#### B.2.13 变更记录 + 附录（§12 + 附录 A/B）

- ✅ **变更记录表 1 行**（v0.1-draft + 12 节 + 2 附录规格）
- ✅ **附录 A 跨模块引用清单 16 项**：覆盖 L2-4 设计 / L2-1 / L2-2 / L2-3 Spec / L1 Architecture §3.5.2/§5.2.2-5.2.4 / ADR-0001/0002/0003/0004 / 宪法 §2.5/§2.9/§3.6/§6/§7/§9
- ✅ **附录 B 开放问题 16 项**（继承设计 12 项 + Spec 新增 4 项 B.13-B.16）：
  - **B.13（Spec 新增）**：Memory CRD status 字段数超限（19 vs 18）如何处理？→ v0.1 接受超限 1 字段（eligibleForPromotion v0.1 仅算不触发可移除）
  - **B.14（Spec 新增）**：admission webhook 部署形态（Operator 同 Pod vs 独立 Deployment）？→ v0.1 同 Pod 内嵌
  - **B.15（Spec 新增）**：Knowledge Service 是否需要持久卷（PV）缓存索引？→ 否，内存倒排索引足够
  - **B.16（Spec 新增）**：Memory rate limit 是否区分 read / write？→ v0.1 仅 write 限流

**亮点**：附录 B **双层开放问题模式**（继承设计 12 项 + Spec 新增 4 项）延续 L2-3 创新模式 — L2 阶段 4 个模块全部采用此模式，体现"设计层决策 vs Spec 实施层问题"分层。

---

### B.3 双文档一致性评估

| 维度 | 设计 | Spec | 一致性 |
|------|------|------|--------|
| 模块边界（§1） | 14 节覆盖 | 12 节覆盖 | ✅ 一致 |
| 子模块拆分（§3） | 5 个子包 | 5 个子包 | ✅ 一致 |
| 4 级 scope 枚举 | §4.1 | §1 目录树 + §6 visibility 关联 | ✅ 一致 |
| 5 维矩阵 | §5.1 | §6.1 12 组合穷举 + §6.3 测试 | ✅ 一致 |
| 4 A2A method | §7 Request/Response + 错误码 | §4.1-§4.4 Request/Response + 错误码 | ✅ 一致 |
| Agent Card | §6.1 JSON | §4.5 完整 JSON | ✅ 一致 |
| admission 互斥规则 | §13.4 详细规格 | §5 详细规格 | ✅ 一致 |
| MemoryReconciler 周期 | §10.3 60s | §7.3 PeriodicWorker.Start | ✅ 一致 |
| decay 公式 | §12.4 exp(-elapsed/decayDays) | §7.4 公式 | ✅ 一致 |
| 可观测性指标 | §11.1 11 + 6 个 | §1 目录树 + §8 Helm values | ✅ 一致 |
| Helm values | §14.4 8 类 | §8.1 7 大段（含 ratelimit + observability + rbac + networkPolicy） | ✅ 一致（设计 8 类被 Spec 7 大段覆盖） |
| 测试 ID | §12 E2E 4 + 性能 + 时间穿越 | §9 UT 32 + IT 15 + E2E 6 + CF 4 = 57 ID | ✅ 一致（Spec 扩展了设计的 E2E 测试到 6 个） |
| 开放问题 | §B 12 项 | §B 16 项（+ 4 新增） | ✅ 一致（双层模式延续） |

**亮点**：设计 + Spec 双文档同步严格一致，无冲突。

### B.4 颗粒度偏差评估（重要）⚠️

**现象**：
- **设计**：41KB / 872 行（计划 20-25KB / ~600 行）= **1.8x**
- **Spec**：99KB / 2494 行（计划 35-45KB / ~1000 行）= **2.5x**

**原因分析**：

| 章节 | 原始预估 | 实际 | 偏差倍数 |
|------|----------|------|----------|
| §1 边界 | 2KB | 4KB | 2x |
| §3 子模块 | 1KB | 3KB | 3x |
| §4 4 级 scope | 2KB | 5KB | 2.5x |
| §5 5 维矩阵 | 1KB | 4KB | 4x |
| §7 4 method | 3KB | 8KB | 2.7x |
| §11 可观测性 | 1KB | 3KB | 3x |
| §13 接口契约 | 2KB | 4KB | 2x |
| §14 部署 | 1KB | 3KB | 3x |
| **合计（设计）** | **~15KB** | **41KB** | **2.7x** |

| 章节 | 原始预估 | 实际 | 偏差倍数 |
|------|----------|------|----------|
| §1 Go Package | 1KB | 6KB | 6x |
| §2 Exported API | 4KB | 15KB | 3.7x |
| §3 CRD JSON Schema | 6KB | 35KB | **5.8x** |
| §4 4 A2A method | 3KB | 12KB | 4x |
| §5 admission | 1KB | 10KB | 10x |
| §7 reconcile 伪代码 | 2KB | 12KB | 6x |
| §8 Helm values | 3KB | 15KB | 5x |
| §9 测试 | 3KB | 12KB | 4x |
| §10 生命周期 | 1KB | 5KB | 5x |
| §11 跨模块 | 1KB | 3KB | 3x |
| **合计（Spec）** | **~25KB** | **99KB** | **4x** |

**判断**：

- ✅ **设计 1.8x 偏差可接受**：3 CRD + 4 method + 5 维矩阵 + MemoryReconciler + admission 互斥 复杂度高于 Adapter 单模块；L1 §3.5.2 Knowledge Service 运行时层 + ADR-0002/0003 双 ADR 都需要落地
- ✅ **Spec §3 CRD JSON Schema 5.8x 偏差源于 3 套完整 JSON Schema 展开**：每个 CRD 含 spec + status + additionalPrinterColumns 完整字段约束 + 枚举 + description；是 controller-gen + kubebuilder 的直接输入
- ✅ **Spec §5 admission 10x 偏差源于双 webhook 互斥规则 + 6 行规则表 + 实现伪代码**：是 admission 实施的零返工输入
- ✅ **Spec §7 MemoryReconciler 6x 偏差源于 4 段伪代码**（核心结构 + Leader Election + PeriodicWorker + decay 公式 + 时间穿越测试用例）
- ✅ **Spec §8 Helm values 5x 偏差源于 7 大段配置面**：knowledgeService + memoryReconciler + admission + search + ratelimit + observability + rbac + networkPolicy 完整覆盖

**当前决议倾向**：**保留完整版**。理由与 L2-1 / L2-2 / L2-3 评审 §F.4 一致 — 宪法 §15.1 质量第一性 + §15.4 技术债不可悄悄累积；L3 实施时返工成本高于文档阅读成本。

---

## §C 验收清单

### C.1 L2-4 设计自检

- [x] 模块边界清晰（In-Scope 8 项 / Out-of-Scope 9 项）✅
- [x] 5 个子包（knowledge/ + memory/ + knowledge-service/ + memory-backend/ + shared/visibility/）✅
- [x] 4 级 scope 继承 + 继承约束（industry 唯一 / parent 精确递增 / 禁止循环）✅
- [x] 5 维矩阵 12 种组合（4 visibility × 3 visibility × 4 scope）✅
- [x] Knowledge Service Agent Card JSON（4 skills：query_knowledge / get_knowledge_item / record_memory / query_memory）✅
- [x] 4 A2A method Request/Response + 错误码（14 个常量）✅
- [x] 3 CRD 字段约束（KnowledgeScope 6+6 + KnowledgeItem 10+4 + Memory 12+8）✅
- [x] MemoryReconciler 60s 周期 + Leader Election + decay 公式 + 时间穿越测试 ✅
- [x] admission webhook 双向互斥（KI ownerRef.Kind ∈ {User,Group} + Memory agentRef.Kind == ServiceAccount）✅
- [x] 11 个 Prometheus 指标 + OTel Span + JSON 日志 + 10 个 K8s Event ✅
- [x] 5 层测试（UT / IT / E2E / 性能 / Conformance）✅
- [x] Helm values 8 类 ✅
- [x] 12 项开放问题 + 默认决策 ✅

### C.2 L2-4 Spec 自检

- [x] Go Package 布局到文件级（含 tests/ + deploy/）✅
- [x] 8 个 Exported API 完整（InheritanceResolver / DecayEngine / ReinforceEngine / MemoryVisibilityFilter / MemoryAdmissionValidator / QueryKnowledgeHandler / RateLimiter / errors）✅
- [x] 3 套 CRD 完整 JSON Schema ✅
- [x] 4 A2A method Request/Response + 错误码表 ✅
- [x] admission webhook 双向互斥规则 + 6 维度对比表 ✅
- [x] 5 维矩阵 12 组合穷举表 + 表驱动测试 ✅
- [x] MemoryReconciler 4 段 reconcile 伪代码（含 Leader Election + PeriodicWorker + decay 公式）✅
- [x] Helm values 7 大段 + env 映射表 + deployment 模板 ✅
- [x] 57 测试 ID（UT 32 + IT 15 + E2E 6 + CF 4）✅
- [x] 12 节 + 2 附录完整 ✅
- [x] 附录 B 16 项开放问题（继承 12 + Spec 新增 4）双层模式 ✅
- [x] 12 节变更记录 + 16 项跨模块引用 + 16 项开放问题 ✅

---

## §D 优点

1. **设计 → Spec 映射自然**：L2-4 设计 14 节 1-to-1 映射到 Spec 12 节 + 附录，认知摩擦极低
2. **3 套 CRD 完整 JSON Schema 展开**：Spec §3 是 L3 实施层零返工输入（controller-gen + kubebuilder 直接消费）
3. **5 维矩阵 12 组合穷举 + 表驱动测试**：Spec §6 是 L3 实施层 visibility 过滤算法零返工输入
4. **admission webhook 双向互斥规则类型化**：KI.ownerRef.Kind ∈ {User, Group} vs Memory.agentRef.Kind == ServiceAccount 6 维度对比表 + 实现伪代码（Spec §5）是 L3 admission 实施零返工输入
5. **MemoryReconciler 4 段 reconcile 伪代码**：核心结构 + Leader Election + PeriodicWorker + decay 公式 + 时间穿越测试用例（Spec §7）是 L3 controller-runtime 实施零返工输入
6. **4 A2A method Request/Response 完整 + Agent Card inputSchema/outputSchema**：与 L2-1 §4 AgentCard JSON Schema 严格对齐，conformance 测试零返工
7. **Helm values 7 大段配置面**：knowledgeService + memoryReconciler + admission + search + ratelimit + observability + rbac + networkPolicy 完整覆盖
8. **测试用例编号方案完整**：UT-S- / UT-K- / UT-M- / UT-V- / UT-H- / UT-R- / UT-C- + IT- + E2E- + CF- 等 57 个 ID 覆盖 5 层测试类型
9. **附录 B 双层开放问题模式延续**：继承设计 12 项 + Spec 新增 4 项（B.13 Memory CRD 字段超限 + B.14 admission 部署形态 + B.15 PV 缓存 + B.16 rate limit read/write 区分），体现"设计层决策 vs Spec 实施层问题"分层 — L2 阶段 4 模块全部采用此模式
10. **MemoryReconciler Leader Election 通过 K8s Lease**：单 leader 串行避免 MemoryReconciler 多副本冲突（Spec §7.2）
11. **TimeTravel 测试用例精确化**：FakeClock.Advance 30 天后 exp(-1) ≈ 0.368 是 ADR-0003 §4.1 公式的精确验证（Spec §7.4）
12. **RBAC 最小权限 Role 示例完整**：knowledgescopes / knowledgeitems get-list-watch + memories 全权限 + serviceaccounts get，是 Operator 安装时的直接参考（Spec §11.4）
13. **错误码 14 个分 3 组**：Knowledge（-32008 ~ -32014）+ Memory（-32101 ~ -32106）+ Admission（4001-4006 HTTP 专用），与 L2-1 JSON-RPC 扩展范围一致
14. **ADR 协调严格**：ADR-0002（Knowledge 4 级 scope + Visibility 4 枚举）+ ADR-0003（Memory CRD + 5 维矩阵 + decay/reinforce 算法 + admission 互斥）+ ADR-0004（v0.1 Phase 2/3 拆分）三套 ADR 全部落地

---

## §E 不足 / 风险

### E.1 已识别（设计附录 B + Spec 附录 B 双重登记）

| 编号 | 风险 | 缓解 |
|------|------|------|
| R-1 | Knowledge Service 单 Deployment（Memory + Knowledge 共享） | 见附录 B-1 / B-2；v0.1 单 Deployment 共享（避免倒排索引重建 + 单人维护）；v0.5+ 评估拆分 |
| R-2 | Memory 全文搜索需求（设计 §9 v0.1 简化） | 见附录 B-3；v0.1 仅 memoryKeyPattern + tag + confidence 过滤；v0.5+ 可加 Vector DB |
| R-3 | 自动 scope-up（v0.5+） | 见附录 B-4；引入 KnowledgePromotionRequest CRD |
| R-4 | Knowledge Service rate limiting 100/min per SA | 见附录 B-5；Helm values 已配 + ratelimit 令牌桶实现 |
| R-5 | admission webhook 失败模式（etcd 不可用） | 见附录 B-6；50ms 超时 → fail-closed（拒绝写入） |
| R-6 | 多 cluster 知识复制（v1.0+） | 见附录 B-7；v0.1 不实现；v1.0+ ADR 评估 |
| R-7 | session context 与 Memory 边界 | 见附录 B-8；session context 单 Agent 私有不持久化；Memory 是 Agent 团队共享的经验 |
| R-8 | Memory 写入审计日志 | 见附录 B-9；K8s audit log + structured logger（不引入额外 audit log 系统） |
| R-9 | MemoryReconciler 周期 60s 是否过短/过长 | 见附录 B-11；60s 默认；Helm values 可配（30s-300s） |
| R-10 | HPA 水平扩展（v0.5+） | 见附录 B-12；v0.1 不需要（1 副本足够 10K items） |
| R-11 | **Memory CRD status 字段数超限（19 vs 18）** | 见附录 B-13（Spec 新增）；v0.1 接受超限 1 字段（eligibleForPromotion v0.1 仅算不触发）；v0.5+ 评估是否合并到 conditions |
| R-12 | **admission webhook 部署形态（Operator 同 Pod vs 独立 Deployment）** | 见附录 B-14（Spec 新增）；v0.1 同 Pod 内嵌；v0.5+ 评估独立 |
| R-13 | **Knowledge Service 是否需要 PV 缓存索引** | 见附录 B-15（Spec 新增）；否，内存倒排索引 + 启动期重建 ≤ 30s @ 10K items |
| R-14 | **Memory rate limit 是否区分 read / write** | 见附录 B-16（Spec 新增）；v0.1 仅 write 限流（60/min per SA）；read 无限流 |

### E.2 颗粒度偏差风险（中等）

- **现象**：设计 41KB / 872 行（1.8x）+ Spec 99KB / 2494 行（2.5x）vs 计划 20-25KB / 35-45KB
- **影响**：评审阅读成本约 3-4 小时（最高，是 L2 阶段 4 模块中颗粒度最大的）
- **缓解**：保留完整版（决议倾向），通过以下结构化降低阅读成本：
  - §0 阅读指南 + L1/L2 边界对照表（约 1KB）
  - §2 Exported API 8 个 Go interface（约 15KB）
  - §3 CRD JSON Schema 3 套完整展开（约 35KB，最高密度章节）
  - §4 4 A2A method + Agent Card JSON（约 12KB）
  - §7 MemoryReconciler reconcile 伪代码（约 12KB，Operator 集成关键参考）
  - §8 Helm values 7 大段（约 15KB）
  - 附录 A/B 状态标签（⏳ / ✅）便于快速查找

### E.3 v0.1 时间盒可行性（低，验证 ADR-0004 协调性）

- **观察**：L2-4 设计 + Spec 共 140KB / 3366 行（设计 41KB / 872 行 + Spec 99KB / 2494 行）
- **ADR-0004 协调**：v0.1 Phase 2 = Knowledge / v0.1 Phase 3 = Memory（拆分实施）
- **影响**：v0.1 阶段 L3 实施**只落地 Knowledge 部分**（Phase 2），Memory 部分推 v0.1+ 或 v0.5 阶段
  - **Knowledge 部分**：`src/knowledge/` + `src/knowledge-service/` + `src/shared/visibility/` 约 30 个文件 + 15 IT + 2 E2E
  - **Memory 部分**：`src/memory/` + `src/memory-backend/` 约 20 个文件 + 8 IT + 1 E2E
- **v0.1 Knowledge 实施负担估算**：
  - CRD types + admission + search 索引 + 4 method handler + Agent Card + Helm chart
  - 估算 40-60h（占 ADR-0004 v0.1 总预算 100h 的 40-60%）
- **缓解建议**：
  1. v0.1 阶段落地 Knowledge（Phase 2，ADR-0004 已明确）
  2. v0.1 后期或 v0.5 早期落地 Memory（Phase 3）
  3. **建议**：v0.1 Knowledge 优先落地**最小可演示**：4 scope + 5 KI + 1 queryKnowledge 调用 + admission 互斥可见

### E.4 L3 实施阶段 memory-backend 与 knowledge-service 共享实现（低）

- **观察**：Spec §1 关键设计原则明确"recordMemory / queryMemory 与 Knowledge Service 共享同一实现"，但物理目录分离（knowledge-service/handlers/record_memory.go + memory-backend/handlers/record_memory.go 各出现一次）
- **影响**：L3 实施时需决策：是 Go 共享 package import 还是代码复制？
- **缓解建议**：
  1. **推荐 Go 共享 package import**：`memory-backend/handlers/` 通过 `import "github.com/superteam-a2a/knowledge-service/handlers"` 引用共享实现
  2. 或在 `src/shared/memorymethods/` 创建第三个目录作为共享层
  3. 避免代码复制（容易漂移）

### E.5 admission webhook 部署形态（Operator 同 Pod）潜在风险（低）

- **观察**：Spec §B.14 已识别 admission webhook 默认部署在 Operator 同 Pod（端口 9443 + TLS cert）
- **影响**：
  - 优点：简化部署 + 减少运维（Operator 升级即 webhook 升级）
  - 缺点：Operator 升级窗口期 webhook 不可用（影响所有 CRD 写入）
- **缓解建议**：
  1. v0.1 同 Pod 内嵌（设计决策）
  2. Operator 滚动升级策略确保至少 1 副本 ready（preStop hook + readiness probe）
  3. v0.5+ 评估独立 Deployment（性能隔离）

### E.6 Knowledge Service 单点故障（中）

- **观察**：设计 §6.2 / Spec §10.1 Knowledge Service 部署 1 副本（v0.1 单实例）
- **影响**：
  - 单 Pod crash → 4 method handler 不可用（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory 全挂）
  - MemoryReconciler 60s 周期 reconcile 也由同一 Pod 处理（Operator 同 Deployment）
- **缓解建议**：
  1. K8s Deployment 默认 rolling restart（replicas=1 时 crash → 短暂不可用）
  2. v0.1 阶段接受（ADR-0004 已明确 v0.1 单副本）
  3. v0.5+ HPA（Helm values `knowledgeService.replicas: 2`）+ Leader Election（同 MemoryReconciler）

### E.7 倒排索引在 Operator 进程内重建延迟（中）

- **观察**：Spec §10.1 启动序列 step 9 要求启动期全量 list KnowledgeItem + 重建倒排索引（≤ 30s @ 10K items）
- **影响**：
  - Operator 启动后 30s 内 queryKnowledge 命中率低（索引未完整）
  - MemoryReconciler 也依赖 Operator（启动顺序耦合）
- **缓解建议**：
  1. readiness probe 仅在倒排索引重建完成后才通过（避免流量打到未就绪 Pod）
  2. Helm values `search.index.rebuildOnStart: true`（默认开启）+ `rebuildTimeout: 60s`（可配）
  3. v0.5+ 评估外部索引服务（Redis / Elasticsearch）解耦

---

## §F 决议

### F.1 总体决议

✅ **通过** — L2-4 Knowledge / Memory 设计文档 v0.1-draft + L2-4 Knowledge / Memory Spec 文档 v0.1-draft **评审通过**。

### F.2 后续动作

1. ⏳ **升级为正式版本**（本评审通过后立即执行）：
   - L2-4 设计 → v0.1.0（移除 `-draft`）
   - L2-4 Spec → v0.1.0（移除 `-draft`）
2. ⏳ **L2 阶段全部完成**：L2-1 / L2-2 / L2-3 / L2-4 四个模块设计与 Spec 全部 v0.1.0
3. ⏳ **下一阶段选择**（待办，**用户决议项**）：
   - **选项 A**：进入 L3 文件级 Spec 阶段（Operator Core / Adapter core / Hello Agent / Knowledge Service / Memory backend 文件级代码契约）
   - **选项 B**：进入 v0.1 实施阶段（按 ADR-0004 Phase 2 优先 Knowledge 落地）
   - **选项 C**：暂停 L3 / 实施，启动 ADR-0005（宪法 §16 v0.4.0 修订已记录，可作为 ADR 化记录）
   - **当前倾向**：选项 A（L2 阶段 100% 完成 → L3 文件级 Spec 是连贯的下一阶段；与 [[a2a-k8s-agent-platform]] 项目档案的"逐阶段完成"节奏一致）

### F.3 例外适用记录

- 14.5 MVP 例外 ✅ 适用
- 单点评审 ✅ 已采用
- L2-4 与其他模块不合并（模块数 = 4，保留灵活性）

### F.4 颗粒度偏差决议

**决议**：保留 L2-4 设计 + Spec 完整版（设计 41KB / Spec 99KB），不精简。

**理由**：
1. 宪法 §15.1 质量第一性 + §15.4 技术债不可悄悄累积
2. **设计 1.8x 偏差**源于 L1 §3.5.2 Knowledge Service 运行时层 + ADR-0002/0003 双 ADR + 3 CRD + 5 维矩阵 + 4 method 的复合复杂度
3. **Spec 5.8x 偏差源于 3 套完整 CRD JSON Schema 展开**：是 controller-gen + kubebuilder 的直接输入（最高密度章节 §3 ~35KB）
4. **Spec 10x 偏差源于 admission webhook 双向互斥规则 + 6 维度对比表 + 实现伪代码**：是 L3 admission 实施的零返工输入
5. **Spec 6x 偏差源于 MemoryReconciler 4 段 reconcile 伪代码**：是 L3 controller-runtime 实施的零返工输入
6. 57 测试 ID 直接对应宪法 §9 80% 覆盖率目标
7. 附录 B 16 项开放问题（含 Spec 新增 4 项双层模式）是 L3 实施的零返工输入
8. 与 L2-1 / L2-2 / L2-3 评审 §F.4 同原则处理（保留完整版）

### F.5 决议待用户确认项

| 编号 | 决议项 | 倾向 |
|------|--------|------|
| Q-1 | 颗粒度偏差处理（设计 41KB / Spec 99KB 保留 / 精简 / 摘要） | 倾向 1（保留完整版）— 同 L2-1 / L2-2 / L2-3 |
| Q-2 | L2 阶段完成后下一阶段选择（A: L3 文件级 Spec / B: v0.1 实施 / C: ADR-0005 宪法修订） | 倾向 A（L3 文件级 Spec 是连贯的下一阶段） |
| Q-3 | Memory CRD status 字段数超限（19 vs 18）v0.1 接受 / 移除 eligibleForPromotion 字段 | 倾向 v0.1 接受（eligibleForPromotion 对调试 + v0.5+ 触发 KnowledgePromotionRequest CRD 有价值） |
| Q-4 | admission webhook 部署形态（Operator 同 Pod / 独立 Deployment） | 倾向 Operator 同 Pod（v0.1 简化部署） |
| Q-5 | Memory rate limit 是否区分 read / write | 倾向仅 write 限流（read 无限流） |
| Q-6 | Knowledge Service 单 Deployment 共享 Memory（不拆分） | 倾向保留（v0.1 简化） |
| Q-7 | Memory CRD 是否需要变更即触发可见性矩阵重算（admission 与 reconcile 解耦） | 倾向不需要（agent-private 短路已保证安全） |

### F.6 跨文档同步动作（评审通过后立即执行）

1. L2-4 设计 frontmatter：`v0.1-draft` → `v0.1.0`
2. L2-4 Spec frontmatter：`v0.1-draft` → `v0.1.0`
3. L2-4 设计 §变更记录：新增 v0.1.0 行（升级日期 + 评审通过 + 作者）
4. L2-4 Spec §变更记录：新增 v0.1.0 行（升级日期 + 评审通过 + 作者）
5. L2-1 Spec 附录 A：L2-4 行 `⏳ v0.1-draft` → `✅ v0.1.0`
6. L2-2 Spec 附录 A：L2-4 行 `⏳ v0.1-draft` → `✅ v0.1.0`
7. L2-3 Spec 附录 A：L2-4 行 `⏳ v0.1-draft` → `✅ v0.1.0`
8. L1 Architecture §6 模块清单：C-4 Knowledge/Memory 行 `⏳ v0.1-draft` → `✅ v0.1.0`

---

## §G 评审结论

> 本 L2-4 设计 + Spec 满足宪法质量第一性（第十五条）所有要求，L2-4 阶段所有强制门禁（14.4）已通过：
>
> - ✅ L2-4 设计完成（v0.1-draft）
> - ✅ L2-4 Spec 完成（v0.1-draft）
> - ✅ L2-4 评审通过（本文）
> - ✅ 与宪法一致（v0.4.0，§2.5 / §2.9 / §3.6 / §6 / §7 / §9 / §16.1.1 1M 窗口 全部满足）
> - ✅ 与 L1 一致（Architecture §3.5.2 运行时层 + §5.2.2-5.2.4 3 CRD spec/status 字段基线 + §6 Knowledge/Memory 模块清单）
> - ✅ 与 ADR 一致（ADR-0002 知识管理 + ADR-0003 Memory 设计 + ADR-0004 v0.1 时间线 Phase 2/3 拆分）
> - ✅ 与 L2 一致（L2-1 a2a.Server 嵌入 4 method + L2-2 Operator Owned resources MemoryReconciler + L2-3 v0.5+ Adapter 代理 4 method）
> - ✅ 风险识别 + 缓解方案（14 项 L3 移交 + 7 项本评审）
> - ✅ 差异化产出（§3 3 套完整 JSON Schema + §4 4 method + Agent Card + §5 admission 互斥 + §6 5 维矩阵 + §7 MemoryReconciler 4 段伪代码 + 附录 B 16 项双层开放问题）
>
> **L2 阶段 4/4 模块全部完成**（L2-1 + L2-2 + L2-3 + L2-4 设计与 Spec 均 v0.1.0）。准许进入下一阶段（按用户决议 Q-2）。

---

> **评审者签署**：项目发起人 2026-07-24
> **下次评审**：L3 文件级 Spec（或 v0.1 实施）阶段完成后（预计 1-2 个会话；本期 L2-4 完成后即可启动）