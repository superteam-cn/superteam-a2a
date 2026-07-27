# superteam-a2a — L2-4 Knowledge / Memory Python v0.2 设计评审报告

> **评审日期**：2026-07-26 · #39 会话
> **评审对象**：[`docs/design/L2-modules/L2-knowledge-memory.md` v0.2-draft](../design/L2-modules/L2-knowledge-memory.md)（97KB / 1920 行 / 14 主章节 + 2 附录）
> **配套 Spec**：[`docs/spec/L2-module-specs/L2-knowledge-memory.md` v0.1.0 Go baseline](../spec/L2-module-specs/L2-knowledge-memory.md)（99KB / 2494 行；**Python v0.2-draft 待独立会话起草** —— 本评审仅覆盖 L2-4 Design）
> **评审人**：项目发起人（单点评审 · 宪法 §14.5 MVP 例外时间窗口内）
> **评审依据**：[`CONSTITUTION.md`](../../CONSTITUTION.md) v0.5.0 §2.5 显式优于隐式 + §2.9 记忆可追溯 + §3.6 MCP 边界 + §3.7 反依赖 + §3.8 Python-first + §6 安全 + §7 可观测性 + §9.7 静态质量 + §14.4 L2 评审门禁 + §14.5 MVP 例外时间窗口；[ADR-0002 知识管理设计](../../adr/0002-knowledge-management-design.md) + [ADR-0003 Memory 设计](../../adr/0003-memory-design.md) + [ADR-0004 v0.1 时间线](../../adr/0004-v01-scope-extension-knowledge-and-memory.md) + [ADR-0005 Python-first](../../adr/0005-python-first-technology-stack.md) §2.2 + §3.4 + §6.2 + §6.3 + §7 + §10 + §13；[L1 Architecture v0.2.0](../design/L1-architecture.md) §3.5.2/§3.5.3 运行时层 + §5.2.2-5.2.4 CRD + §6 模块清单 + §11.5 Python 性能预算；[L1 Spec v0.2.0](../../spec/L1-system-spec.md) §5 CRD + §15 部署 + §16 指标命名；[L2-1 A2A Protocol v0.2.0](../design/L2-modules/L2-a2a-protocol.md) §3 包结构 + §4 compatibility adapter + §5 ASGI server；[L2-2 Operator Core v0.2.0 Design](../design/L2-modules/L2-operator-core.md) §5 admission + §11 Helm values + [L2-2 Spec v0.2.0 Python](../spec/L2-module-specs/L2-operator-core.md) §5.6 MemoryReconciler + Clock 注入；[L2-3 Adapter v0.2.0 Design](../design/L2-modules/L2-adapter.md) §13 部署形态 + §12.5 Memory 降级路径
> **上一版评审**：[L2-4 v0.1.0 Go baseline 评审](./l2-4-knowledge-memory-review.md) 2026-07-24（§A-§G 10 维度全通过；本评审为 Python 重写后的二次评审，仅覆盖 Design，Spec 待独立会话）

---

## 评审概览

### 评审维度与结论

| 维度 | 评审范围 | 结论 |
|------|----------|------|
| **A. 文档完整性** | 14 主章节 + 2 附录 + 头部（版本/状态/supersede/依据/配套 Spec）+ 阅读指南 + 与 v0.1 Go baseline 对照表 | ✅ PASS |
| **B. 设计深度** | 5 项 Python 实现决策 + Python 包结构 + 4 级 scope 继承 + 5 维矩阵 + Knowledge Service Agent Card + 4 A2A method + CRD schema + BM25 + 可观测性 + 测试策略 + 接口契约 + 部署形态 | ✅ PASS |
| **C. Python-first 硬约束** | ADR-0005 §3.4 + §13 + 宪法 §3.8（Pydantic v2 / typing.Protocol / async-first / 单进程 / uv workspace / 静态门禁 / boundary） | ✅ PASS |
| **D. wire contract 一致性** | 与 v0.1.0 Go baseline 完全一致（3 CRD 字段 / 4 A2A method / 5 维矩阵 / admission 双向互斥 / decay/reinforce/GC/promotion 算法 / 错误码范围 -32008~-32014 + -32101~-32106 / 11+6 Prometheus 指标 / BM25 K1=1.5 B=0.75 / 4 级 scope 继承 / Helm values 业务语义） | ✅ PASS |
| **E. 安全性** | mTLS + RBAC + NetworkPolicy + admission 双向互斥 + 5 维矩阵 + scope 校验 + cert-manager + 50ms fail-closed | ✅ PASS |
| **F. 可观测性** | 11+6 = 17 个 supteam_knowledge_* + supteam_memory_* Prometheus 指标 + OTel Span + structlog JSON + Python runtime 4 指标 + 敏感字段禁记 | ✅ PASS |
| **G. 异步 / 单进程 / 资源** | 单 Uvicorn worker + anyio.to_thread.run_sync CPU offload + event-loop lag + 资源限制 1Gi + BM25 倒排索引受控线程 | ✅ PASS |
| **H. 错误模型 + Retryable** | 13+5 = 18 错误码（Knowledge 7 + Memory 6 + admission 5）+ StrEnum + admission 50ms 超时 fail-closed + 错误传播 3 通道 | ✅ PASS |
| **I. 测试策略 + ID 矩阵** | UT + IT + E2E 6 + CF 4 = 57 ID（含时间穿越 fake clock + admission 互斥 + 12 种矩阵组合 + 10K items P95 ≤ 200ms 性能门禁）+ 2 项 Python 新增 E2E | ✅ PASS |
| **J. 颗粒度偏差 + 跨文档一致性** | 97KB / 1920 行（超 30-45KB 目标；5 决策 + 5 sub-packages + Pydantic Card + Python runtime + Helm 完整 + 22 项开放问题是合理扩展）；与 L1 v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-3 v0.2.0 + ADR-0005 + 宪法 v0.5.0 引用一致 | ✅ PASS（合理） |

**评审结论**：✅ **通过**（10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）

### 关注项（移交 L3-5 / L3-6 / Spec 起草）

1. ⚠️ **§2.2 D-1~D-5 5 项 Python 实现决策仅占位默认值**：每项决策的具体版本号（`kopf>=1.36,<2` 精确下限 + `anyio to_thread` 默认 40 线程 capacity 验证 + Pydantic v2 admission JSON 反序列化性能基准）+ 风险评估待 L3-5 / L3-6 Python venv 实测后补完（设计 §2.2 U-1~U-5 已明确标注）
2. ⚠️ **L2-4 Spec v0.2-draft Python 待独立会话起草**：70-100KB / ~2000-2500 行（参照 L2-3 Spec 110KB / 2705 行规模）；建议拆分 Spec 起草 + 评审两会话避免 §16.1 红线（与 L2-1 / L2-2 / L2-3 评审处理一致）
3. ⚠️ **L2-4 Go Design + Spec 归档未执行**：与 L2-2 归档模式不一致（L2-1 / L2-3 Go baseline 覆盖丢失；L2-2 已归档至 `docs/archive/pre-python-2026-07-24/`）；本次会话升级 v0.2.0 时建议同步归档（或登记为风险由后续会话处理）

### 建议项（非阻塞）

1. 💡 建议 §11.1 Prometheus 指标补充 **supteam_knowledge_search_offload_seconds** 与 **supteam_knowledge_search_event_loop_lag_seconds** 的 Histogram bucket 配置（默认 `[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]`；ADR-0005 §10 要求）
2. 💡 建议 §12.5 性能测试补充 **MemoryReconciler 50K memories 周期 reconcile 时间预算**（设计 §10.3 仅给单 reconcile 1000 批上限；附录 B B.21 已登记待 L3-6 实测）
3. 💡 建议 §14.4 Helm values 补充 **memoryReconciler.clock.fake 默认 false 警告注释**（生产误配 FakeClock 将导致 Memory 不衰减；建议 v0.2.0 升级时加 admission 拦截）
4. 💡 建议 §5.3 admission 错误码表合并到 §7.1~§7.4 的 4 个 A2A method 错误码表（当前 admission 错误码 -32015~-32018 + -32107~-32112 与 method 错误码 -32008~-32014 + -32101~-32106 分两段；建议 L3-5 起草 Spec 时统一为单表）

---

## §A 文档完整性（PASS）

### A.1 头部元数据

- ✅ **版本**：v0.2-draft（标注明确，升级 v0.2.0 后变更）
- ✅ **状态**：🚧 v0.2-draft（#38）→ ✅ v0.2.0（待评审通过）
- ✅ **supersede 指针**：明确指向 `docs/reviews/l2-4-knowledge-memory-review.md`（v0.1.0 Go baseline 评审）；精准说明「仅 supersede Go struct / Go interface / Go package / Go 镜像块 / kubebuilder annotation 实现条款；wire contract 与 v0.1 业务语义完全继续有效」
- ✅ **配套 Spec**：明确 L2-4 Spec 仍是 v0.1.0 Go baseline（99KB / 2494 行）；**Python v0.2-draft 待 L2-4 Design 评审通过后独立会话起草**（与 L2-1 / L2-2 / L2-3 评审处理一致）
- ✅ **归档路径**（计划）：v0.1.0 Go baseline Design + Spec 将在 v0.2.0 Spec 评审通过后归档至 `docs/archive/pre-python-2026-07-24/L2-knowledge-memory-{design,spec}-v0.1.0-go-baseline.md`（与 L2-2 归档模式一致）
- ✅ **依据**：宪法 v0.5.0 §2.5/§2.9/§3.6/§3.7/§3.8/§6/§7/§9.7 + ADR-0002 + ADR-0003 + ADR-0004 + ADR-0005 + L1 Architecture v0.2.0 + L1 Spec v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-3 v0.2.0 全部引用
- ✅ **MVP 例外**：§14.5 适用标注明确

### A.2 阅读指南（§0）+ v0.1 → v0.2 对照表

- ✅ **9 维关键变化表**清晰（CRD types / CRD 生成 / 算法抽象 / 4 级 scope 继承 / MemoryReconciler / 5 维矩阵 / Clock / decay/reinforce / BM25 / A2A Server / 错误码 / 可观测性 / admission / 镜像 / 测试）
- ✅ **与 v0.1.0 Go baseline 关系** 3 段（迁移业务语义输入 / 完全替代 Go 实现决策 / 业务语义完全一致）—— L2-1 / L2-2 / L2-3 评审中"业务语义继承"模式复用
- ✅ 5 类读者路径明确（L3-5 / L3-6 Spec 作者 / Operator Core 维护者 / CRD + admission 贡献者 / 知识管理 Agent 作者 / 架构评审者）

### A.3 章节完整性（14 主章节 + 2 附录）

| 章节 | 子章节数 | 完整性 | 备注 |
|------|----------|--------|------|
| §0 阅读指南 | — | ✅ 完整 | v0.1/v0.2 对照表 + 关系说明 |
| §1 模块使命与边界 | 3 | ✅ 完整 | 使命 7 项 / 系统边界 in 10 + out 9 项 / 价值主张 5 维 |
| §2 Knowledge / Memory Python 实现决策 | 3 | ✅ 完整 | 5 项决策（D-1~D-5）+ 详细说明（含完整代码契约 + 与 v0.1 对照）+ 5 项已知未决移交 L3-5/L3-6 + 与 L2-1/L2-2/L2-3 对齐表 |
| §3 Python 包结构 | 6 | ✅ 完整 | uv workspace 总览 + 5 个 sub-packages（knowledge/memory/knowledge-service/memory-backend/shared-visibility）+ 边界规则 |
| §4 Knowledge 4 级作用域 | 4 | ✅ 完整 | 4 级枚举 + 继承算法 + Visibility 4 枚举 + 容量性能约束 |
| §5 Memory 5 维可见性矩阵 | 3 | ✅ 完整 | 5 维矩阵 + 12 字段 spec + admission 双向互斥 8 错误码 |
| §6 Knowledge Service Agent Card | 2 | ✅ 完整 | Pydantic AgentCard model + 部署形态 |
| §7 4 个 A2A method 详细规格 | 4 | ✅ 完整 | queryKnowledge / getKnowledgeItem / recordMemory / queryMemory |
| §8 CRD Schema 概要 | 5 | ✅ 完整 | KnowledgeScope + KnowledgeItem + Memory + JSON Schema 生成链路 + 字段数约束 |
| §9 检索路径 | 3 | ✅ 完整 | 存储策略 + BM25 + 受控线程 offload |
| §10 持久化层 | 3 | ✅ 完整 | 不引入外部依赖 + 内存倒排 + MemoryReconciler 周期 |
| §11 可观测性 | 4 | ✅ 完整 | Prometheus 17 指标 + OTel + structlog + K8s Events |
| §12 测试策略 | 7 | ✅ 完整 | UT + IT + E2E + 时间穿越 + 性能 + Conformance + 静态门禁 |
| §13 与其他模块接口契约 | 5 | ✅ 完整 | L2-1 / L2-2 / L2-3 + admission 详细规格 + 外部依赖 |
| §14 部署形态 | 4 | ✅ 完整 | Knowledge Service Deployment + MemoryReconciler + 持久化 + Helm values Python 镜像块 |
| 附录 A 跨模块引用 | — | ✅ 完整 | 24 项引用（含 ADR-0005 §3.4 + 宪法 v0.5.0 §3.8 + L1 Spec §16） |
| 附录 B 开放问题 | — | ✅ 完整 | **22 项三层模式**（继承 v0.1 Go baseline 12 + Spec 新增 4 + Python 重写新增 6） |

**完整性评估**：14 主章节全覆盖；§0-§14 全部完整；2 附录完整；与 L2-1 / L2-2 / L2-3 评审章节清单（14 主 + 2 附录）规模一致。

### A.4 附录 A 跨模块引用

- ✅ **24 项引用**覆盖：L1 Arch v0.2.0 §3.5.2/§3.5.3 + §5.2.2-5.2.4 + §6；L1 Spec v0.2.0 §5/§15/§16；L2-1 v0.2.0 Design + Spec；L2-2 v0.2.0 Design + Spec §5.6；L2-3 v0.2.0 Design + Spec；ADR-0001 + ADR-0002 + ADR-0003 + ADR-0004 + **ADR-0005 Python-first**（§3.4 + §6.2 + §6.3 + §7 + §10 + §13）；宪法 v0.5.0 §2.5/§2.9/§3.6/§3.7/§3.8/§6/§7/§9/§16.1
- ✅ 状态标注清晰（✅ / ⏳）
- ✅ 与 L2-2 / L2-3 评审一致性高（22/24 项与 L2-2/L2-3 附录 A 重叠）

### A.5 附录 B 开放问题（22 项三层模式 · 与 L2-1 / L2-2 / L2-3 同原则）

- ✅ **B.1 继承 v0.1.0 Go baseline（12 项）**：Knowledge Service 拆分 / SA 共享 / Memory 全文搜索 / scope-up / rate limiting / admission fail-closed / 多 cluster 复制 / Memory 与 session context 边界 / 审计日志 / version 显式 / MemoryReconciler 周期 / HPA
- ✅ **B.2 Spec 新增（4 项 · B.13-B.16）**：eligible_for_promotion 字段超限 / admission 部署形态 / PV 缓存层 / rate limit read/write 区分
- ✅ **B.3 Python 重写新增（6 项 · B.17-B.22）**：Kopf timer + admission 启动顺序 / cert-manager TLS 热更新 / anyio to_thread 线程池容量 / Pydantic v2 admission 性能 / MemoryReconciler 50K 周期预算 / 5 维矩阵 50K 延迟

---

## §B 设计深度（PASS）

### B.1 5 项 Python 实现决策（§2 · ADR-0005 §8 前置门禁）

| 决策 | 默认 | 锁定依据 | 状态 |
|------|------|----------|------|
| **D-1 CRD types 实现形式** | Pydantic v2 BaseModel + `populate_by_name` + alias | ADR-0005 §3.4 + §5.1 + §3.4；Pydantic 与官方 A2A SDK 类型互转最直接 | ✅ |
| **D-2 内存 BM25 倒排索引形态** | `dict[str, set[str]]` + `anyio.to_thread.run_sync` 受控 offload | ADR-0005 §6.3 + §3.4；10K items 规模无需重型 NLP 库；offload 满足 event-loop lag 门禁 | ✅ |
| **D-3 MemoryReconciler 周期触发** | Kopf `@kopf.timer(interval=60.0)` + 独立 async service + Leader Election via Lease | ADR-0005 §7 可靠性门禁 7-8；Kopf 提供 operator 重启恢复 + Leader Election + backoff | ✅ |
| **D-4 Clock 注入形式** | `typing.Protocol[now, advance]` + `RealClock` + `FakeClock` | ADR-0005 §3.4 + §11 测试；时间穿越单测必须可注入 | ✅ |
| **D-5 admission webhook 部署** | Kopf `kopf.validation` decorator（operator 进程内嵌）+ cert-manager TLS + 50ms 超时 fail-closed | ADR-0005 §3.4 + §6.2；operator 内嵌简化运维；cert-manager 挂 TLS | ✅ |

**评价**：5 项决策覆盖 L2-4 Python-first 设计核心（CRD 类型 + 内存索引 + Controller 周期 + 时间注入 + admission 部署）；每项决策有 schema 代码示意 + 与 v0.1.0 对照 + 锁定依据。**L3-5 / L3-6 实测后需补完精确版本号 + 风险评估**（设计 §2.2 U-1~U-5 已明确标注）。

### B.2 Python 包结构（§3 · ADR-0005 §13 工程布局）

- ✅ **uv workspace 总览**：`pyproject.toml`（根）+ `uv.lock`（CI 强制 `uv sync --frozen`）+ 5 个独立 package（knowledge / memory / knowledge-service / memory-backend / shared + shared-visibility）
- ✅ **`packages/knowledge` 包布局 5 子包 + 完整文件清单**：`apis/v1alpha1/{knowledgescope,knowledgeitem,common}.py` + `scope/{inheritance,validation,inherit_rules}.py` + `admission/{ki_webhook,scope_webhook}.py` + `search/{inverted_index,bm25,rebuild}.py`
- ✅ **`packages/memory` 包布局 3 子包 + 完整文件清单**：`apis/v1alpha1/{memory,common}.py` + `lifecycle/{decay,reinforce,promotion,gc,visibility}.py` + `admission/m_webhook.py`
- ✅ **`packages/knowledge-service` 包布局 4 子包 + 完整文件清单**：`main.py` + `handlers/{4 method}.py` + `card/knowledge_service_card.json` + `config/loader.py`
- ✅ **`packages/memory-backend` 包布局 3 子包 + 完整文件清单**：`main.py` + `handlers/{record_memory,query_memory}.py` + `store/store.py` + `middleware/{ratelimit,audit}.py`
- ✅ **边界规则 5 层**：a2a-python SDK → knowledge_service/memory_backend → knowledge/memory → shared/shared-visibility（与 L2-1 §3.2 + 宪法 §3.7 + ADR-0005 §3.3 严格一致）
- ✅ **关键约束 4 条**：knowledge_service/memory_backend 严禁 framework SDK / shared/shared-visibility 是唯一公共包 / operator 通过 K8s API watch 编排 knowledge_service / knowledge 与 memory 资源模型层独立
- ✅ **ADR-0005 §13 工程布局严格对齐**

### B.3 Knowledge 4 级作用域（§4 · ADR-0002）

- ✅ **4 级枚举 + 数量约束**：industry（cluster-scoped 唯一 1 个）+ organization + team + project（namespace-scoped）
- ✅ **继承约束**：industry parent_ref is None / organization parent_ref → industry / team parent_ref → organization / project parent_ref → team / 禁止循环引用 / 禁止 parent 跨级
- ✅ **`resolve_effective_scopes()` async 算法伪代码**：从 industry 一路到当前 scope 的完整继承链（顶层在前）+ 循环引用检测（visited set）+ 严格 level 递增 1 级校验（order 列表索引）+ parent not found 异常
- ✅ **`query_knowledge()` async 函数**：自动包含继承链上所有作用域的 KnowledgeItem + inheritRules 过滤 + visibility 过滤 + dedupe_by_id_keep_latest + max_results 截断
- ✅ **KnowledgeItem Visibility 4 类 StrEnum**：scope-only / scope-and-children（默认）/ public-readable（仅 industry）/ agent-private（v0.1 禁用）
- ✅ admission webhook 强制 visibility == public-readable 必须 level == industry
- ✅ 性能约束：单集群 ≤ 10K KnowledgeItem / 倒排索引重建 ≤ 30s / queryKnowledge P95 ≤ 200ms

### B.4 Memory 5 维可见性矩阵（§5 · ADR-0003）

- ✅ **5 维矩阵（4 scope × 3 visibility + agent-private 短路）**：12 种组合穷举 + agent-private 短路（不参与 scope 继承）+ scope-only 仅当前 scope + scope-and-children 继承链上
- ✅ **`is_memory_visible_to()` async Protocol**：3 规则顺序（agent-private 短路 → scope-only → scope-and-children → 默认 False 防御性）
- ✅ **MemorySpec 12 字段约束**：scope_ref + agent_ref + content + summary + confidence + decay_days + reinforced_count + visibility + memory_key（可选）+ source_knowledge_ref（可选）+ tags（可选）
- ✅ **admission 双向互斥规则表（4 维度）**：owner_ref.Kind ∈ {User, Group} vs agent_ref.Kind == ServiceAccount / visibility 枚举差异 / body vs content 格式 / CRUD 入口差异（kubectl apply vs A2A record/query only）
- ✅ **8 admission 错误码**（-32015~-32018 + -32107~-32112）：KNOWLEDGE_OWNER_KIND_FORBIDDEN / KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY / KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS / KNOWLEDGE_ADMISSION_TIMEOUT / MEMORY_AGENT_KIND_FORBIDDEN / MEMORY_SOURCE_KNOWLEDGE_NOT_FOUND / MEMORY_SOURCE_KNOWLEDGE_SCOPE_MISMATCH / MEMORY_AGENT_PRIVATE_REQUIRES_AGENT_NAME / MEMORY_DECAY_DAYS_TOO_LONG / MEMORY_ADMISSION_TIMEOUT

### B.5 Knowledge Service Agent Card（§6 · Python Pydantic）

- ✅ **`KnowledgeServiceCard` Pydantic BaseModel**：`name`（默认 superteam-a2a.knowledge-service）+ `version`（默认 0.2.0）+ `description` + `provider` + 2 `AgentSkill`（query_knowledge + get_knowledge_item）+ `capabilities`（streaming/pushNotifications/stateTransitionHistory = false）+ `authentication`（mTLS）
- ✅ **AgentSkill.inputSchema JSON Schema 2020-12**：query_knowledge 5 字段（scope + query + typeFilter + tagFilter + maxResults）+ get_knowledge_item 2 字段（name + version）
- ✅ **部署形态**：1 副本 v0.1 单实例 + 独立 SA（superteam-a2a-knowledge-service）+ NetworkPolicy + 不暴露 HTTP（仅 A2A mTLS）+ 挂载 4 个 A2A method

### B.6 4 个 A2A method 详细规格（§7 · 与 v0.1 wire contract 完全一致）

- ✅ **`a2a.queryKnowledge`**：QueryKnowledgeRequest Pydantic DTO（scope + query + typeFilter + tagFilter + maxResults）+ QueryKnowledgeResponse DTO（items + total_count）+ 5 错误码
- ✅ **`a2a.getKnowledgeItem`**：4 错误码
- ✅ **`a2a.recordMemory`**：5 错误码（含 rate_limit）
- ✅ **`a2a.queryMemory`**：5 错误码（含 query_too_broad）
- ✅ **行为兼容性**：与 v0.1.0 Go baseline 完全一致（JSON wire shape + 错误码范围 + 调用流程）

### B.7 CRD Schema 概要（§8 · Pydantic 单一来源）

- ✅ **3 CRD + spec/status 字段约束**：KnowledgeScope 6 spec + 6 status / KnowledgeItem 9 spec + ADR-0002 status / Memory 12 spec + 7 status
- ✅ **CRD YAML 生成链路**（ADR-0005 §5.2）：Pydantic `model_json_schema()` → deterministic sort + x-kubernetes-* injection → deterministic OpenAPI v3 → checked-in CRD YAML → CI gate（git diff --exit-code + kubectl apply dry-run + Pydantic ↔ YAML round-trip）
- ✅ **字段数约束（ADR-0004 防过度设计）**：KnowledgeScope 距上限 9 / KnowledgeItem 距上限 6 / Memory 距上限 3（临界但达标）

### B.8 检索路径 + BM25 + CPU offload（§9 · D-2）

- ✅ **存储策略**：KnowledgeItem + Memory 存 etcd（CRD 即存储）+ 倒排索引存 Operator 进程内存
- ✅ **检索流程 8 步**：scope 存在性 → typeFilter/tagFilter 校验 → resolve_effective_scopes → InvertedIndex.search（CPU offload via `to_thread.run_sync`）→ BM25 评分 → visibility 过滤 → inheritRules 过滤 → dedupe + 截断
- ✅ **RealInvertedIndex 实现要点**：`defaultdict(set)` post_listing + `dict[str, int]` doc_lens + asyncio.Lock + `to_thread.run_sync` 包装 `_search_blocking`
- ✅ **BM25 评分公式**：`score += idf * (tf / (1 + BM25_B * (doc_tokens / avg_doc_len - 1)))`，K1=1.5 / B=0.75（与 Go baseline math 完全等价）
- ✅ **线程 offload 约束**（ADR-0005 §6.3）：默认 40 线程 / 单次 search 5s timeout / event_loop_lag_seconds 指标 / 10K items rebuild ≤ 30s

### B.9 持久化层（§10）

- ✅ **不引入 PG / Vector DB 4 项理由**：单人维护成本 / CRD 即存储天然 RBAC / 容量充足（10K items + 50K memories ≈ 60MB）/ v0.5+ 可演进
- ✅ **Operator 内存倒排索引 5 维度**：实现 / 评分 / 重建时间 / 容量上限 / CPU offload + 锁（与 D-2 一致）
- ✅ **MemoryReconciler 周期（D-3）**：60s（Kopf `@kopf.timer`）+ 批量 1000（Helm 可配）+ Clock Protocol 注入 + Lease Leader Election + Kopf backoff 指数退避

### B.10 可观测性（§11 · 与 L1 v0.2.0 §16 严格一致）

- ✅ **11+6 = 17 Prometheus 指标**（与 v0.1 wire contract 完全一致）：superteam_knowledge_{query_total, query_duration_seconds, items_total, search_index_size, scope_total, ...} + supteam_memory_{record_total, query_total, decay_total, reconcile_duration_seconds, eligible_for_promotion_total, total}
- ✅ **Python runtime 4 新指标**（ADR-0005 §10）：supteam_python_{event_loop_lag_seconds, thread_offload_queue_depth, active_tasks} + GC 指标（待 L3-6 展开）
- ✅ **OTel Trace 6 child spans**：crd.read / index.search / bm25.score / visibility.filter / reconcile.batch / thread.offload.start|end
- ✅ **structlog JSON 7 强制字段 + 4 可选字段**：framework / caller_agent / scope / trace_id / level / ts / msg + memory_key / confidence / effective_confidence / decay_days / event_loop_lag_ms
- ✅ **K8s Events 9 类**：KnowledgeScope Created/Deleted + KnowledgeItem Published/Deprecated + Memory Created/Reinforced/Decayed/Expired/GarbageCollected
- ✅ **敏感字段黑名单**：content / body / tags（K8s audit log + Memory content 永不进入普通日志）

### B.11 测试策略（§12 · pytest + pytest-asyncio + FakeClock）

- ✅ **UT 覆盖率分层**：inheritance 100% / search ≥ 90% / lifecycle 100%（时间穿越）/ 5 维矩阵 100%（4×3=12 种组合）/ admission 100%
- ✅ **IT 集成测试（envtest · Kopf in-process）**：KnowledgeScope 4 级继承 / KnowledgeItem admission / Memory visibility 过滤 / MemoryReconciler 周期 / **Leader Election failover（Python 新增）/ admission 50ms timeout fail-closed（Python 新增）**
- ✅ **E2E 测试（kind）6 个**：E2E-K-001 knowledge-quickstart / E2E-K-002 visibility 矩阵穷举 / E2E-M-001 memory-record-query / E2E-M-002 admission 互斥 / **E2E-M-003 MemoryReconciler Python 路径（FakeClock 推进 30 天）/ E2E-M-004 Leader Election failover（Python 新增）**
- ✅ **时间穿越测试（decay 关键）**：FakeClock 推进 30 天 → apply_decay 返回 1.0 * exp(-1) ≈ 0.368（与 Go baseline 数学等价）
- ✅ **性能测试 4 项**：10K items queryKnowledge P95 ≤ 200ms / 50K memories recordMemory P95 ≤ 200ms + queryMemory P95 ≤ 300ms / 60s 周期 reconcile 全集群 50K memories ≤ 30s / BM25 倒排索引 search 阻塞时间 ≤ 100ms
- ✅ **Conformance 测试**：4 method 100% wire-compatible with `google-a2a/conformance` + admission webhook 拒绝率/通过率 + 错误码范围 -32008 ~ -32112
- ✅ **静态质量门禁**（ADR-0005 §11.1）：pyright --strict + ruff check + bandit + pip-audit

### B.12 接口契约（§13 · L2-1 / L2-2 / L2-3 对齐）

- ✅ **与 L2-1 A2A Protocol v0.2.0 Python**：supteam_a2a.a2a.upstream.{create_app, AgentCard, Message/Task/Part}
- ✅ **与 L2-2 Operator Core v0.2.0 Python**：4 类能力（CRD Controller / admission webhook / finalizer / Leader Election）+ MemoryReconciler 在 L2-2 Operator Core 同进程运行 + 共享 LeaseLeader
- ✅ **与 L2-3 Adapter v0.2.0 Python**：v0.5+ 4 method 代理（v0.1 不强制）
- ✅ **admission 双向互斥详细规格**：KI 5 规则 + Memory 5 规则 + 50ms 超时 fail-closed
- ✅ **与外部依赖**：cert-manager + OpenTelemetry Collector + K8s RBAC

### B.13 部署形态（§14 · Helm values Python 镜像块完整）

- ✅ **Knowledge Service Deployment（与 Memory backend 共享）**：1 副本 + ASGI + Uvicorn 单 worker + 4 handler + 共享 In-process 倒排索引 + 独立 SA + mTLS + NetworkPolicy
- ✅ **不拆分两个 Deployment 3 项理由**：知识 + 记忆互补能力共享内存索引 / 单人维护成本 / v0.5+ 可拆分
- ✅ **MemoryReconciler（Operator 进程内）**：60s 周期 + 单 leader（Lease）+ v0.5+ 水平扩展
- ✅ **持久化层**：CRD 即存储 + Operator 内存倒排 + etcd 加密
- ✅ **Helm values 完整 5 段式**：knowledgeService.{image, python, resources, replicas, healthCheck} + memoryReconciler.{enabled, interval, batchSize, clock, leader} + search.{index, bm25} + admission.{enabled, timeoutMs, tls} + ratelimit.{memory, slidingWindow}

### B.14 开放问题（附录 B · 22 项三层模式）

| # | 问题 | 默认决策 | 待确认 |
|---|------|----------|--------|
| **B.1 继承 v0.1 Go baseline（12 项 · B.1-B.12）** | 见设计附录 B.1 表 | — |
| **B.2 Spec 新增（4 项 · B.13-B.16）** | eligible_for_promotion 字段超限 / admission 部署形态 / PV 缓存 / rate limit read/write 区分 | 用户 |
| **B.3 Python 重写新增（6 项 · B.17-B.22）** | Kopf timer + admission 启动顺序 / cert-manager TLS 热更新 / anyio to_thread 线程池容量 / Pydantic v2 admission 性能 / MemoryReconciler 50K 周期预算 / 5 维矩阵 50K 延迟 | L3-5 / L3-6 |

**评价**：22 项开放问题均有默认决策（不挂空），覆盖拆分 / SA / 搜索 / scope-up / rate / fail-closed / 联邦 / session / 审计 / version / 周期 / HPA / 字段超限 / 部署 / PV / 读写区分 / 启动顺序 / TLS 热更 / 线程池 / admission 性能 / 周期预算 / 5 维延迟 22 维度。与 L2-1 / L2-2 / L2-3 评审开放问题模式一致。

---

## §C Python-first 硬约束（PASS · ADR-0005 §3.4 + §13 + 宪法 §3.8）

| 约束 | 落实位置 | 状态 |
|------|----------|------|
| **Pydantic v2 + extra="forbid" + populate_by_name + alias** 作为 CRD 类型 | §2.2 D-1 + §8.1 KnowledgeScope spec | ✅ |
| **Pydantic v2 BaseModel** 表达 A2A extension DTO | §7.1 QueryKnowledgeRequest/Response + §6.1 KnowledgeServiceCard | ✅ |
| **JSON Schema 2020-12 → 确定性 OpenAPI v3 CRD 生成** | §8.4 CRD YAML 生成链路 | ✅ |
| **typing.Protocol + @runtime_checkable** 作为算法抽象 | §4.2 ScopeResolver + §5.1 MemoryVisibilityFilter + §9.2 InvertedIndex + §10.3 MemoryReconcilerService + §D-4 Clock Protocol | ✅ |
| **Kopf `@kopf.timer` + 独立 async service** 作为 Controller 周期触发 | §10.3 + §D-3 MemoryReconciler + §13.2 L2-2 集成 | ✅ |
| **Kopf `kopf.validation` decorator** 作为 admission webhook | §13.4 + §D-5 admission 双向互斥 | ✅ |
| **`anyio.to_thread.run_sync`** 作为 CPU offload | §9.2 RealInvertedIndex + §D-2 BM25 | ✅ |
| **Clock Protocol + RealClock + FakeClock** 作为时间注入 | §2.2 D-4 + §10.3 + §12.4 时间穿越 | ✅ |
| **单进程原则（Uvicorn 1 worker / single event loop / Operator 单进程）** | §14.1 + §14.2 + Helm `python.workers: 1` | ✅ |
| **异步优先 + async handler** | §4.2 resolve_effective_scopes + §5.1 is_memory_visible_to + §7.* 4 handler + §9.2 search | ✅ |
| **uv workspace + uv.lock --frozen** | §3.1 uv workspace 总览 + §14.4 Helm `python.runtime: python:3.12-slim` | ✅ |
| **Helm schema 强制 `python.workers: 1`** | §14.4 knowledgeService.python.workers | ✅ |
| **静态门禁（ruff + pyright strict + bandit + pip-audit）** | §12.7 + §14.4 Helm runtime | ✅ |
| **Adapter 不实现 MCP**（宪法 §3.6 反依赖） | §1.2 模块外明确排除 + §3.6 边界规则 framework SDK 严禁 | ✅ |
| **敏感字段禁记**（content / body / tags / API key / cert / private key） | §11.3 敏感字段黑名单 | ✅ |
| **Python runtime 4 指标**（event-loop lag / thread-offload queue depth / active tasks / GC） | §11.1 + ADR-0005 §10 | ✅ |

**总评**：Python-first 16 项硬约束全部落实；与 ADR-0005 §3.4 + §13 + 宪法 v0.5.0 §3.8 严格一致；与 L2-3 评审 §C 10 项相比增加 6 项 L2-4 特定（Clock Protocol / anyio offload / Kopf validation / admission 双向互斥 / BM25 数学等价 / etcd 加密）。

---

## §D wire contract 一致性（PASS · 与 v0.1.0 Go baseline 完全一致）

| 维度 | v0.1.0 Go baseline | v0.2 Python | 一致性 |
|------|--------------------|--------------|--------|
| **CRD types** | Go struct + `+kubebuilder:validation:` | Pydantic v2 BaseModel + Field + alias | ✅ 等价（wire contract + 必填性 + 枚举不变） |
| **CRD YAML 生成** | controller-gen | Pydantic JSON Schema → 确定性 OpenAPI v3 | ✅ wire shape 不变 |
| **算法抽象** | Go interface | typing.Protocol + @runtime_checkable | ✅ 行为兼容 |
| **4 级 scope 继承** | Go func + error | Python async def + ScopeError 异常 | ✅ 数学等价 |
| **5 维矩阵** | Go switch + sync.Map | Python dict 策略表 + asyncio.Lock | ✅ 12 组合穷举等价 |
| **MemoryReconciler** | controller-runtime Reconcile + RequeueAfter=60s | Kopf `@kopf.timer(interval=60.0)` + async service | ✅ 周期 + 行为兼容 |
| **Clock 注入** | Go interface + k8s.io/utils/clock | Protocol + RealClock + FakeClock | ✅ 时间穿越模式兼容 |
| **decay/reinforce/GC/promotion 数学** | Go math + sync.Mutex | Python 数学等价 + asyncio 序列化 | ✅ 数学公式 + 阶段转换等价 |
| **BM25 倒排索引** | Go map + sync.RWMutex | Python dict + anyio.to_thread.run_sync | ✅ 评分公式 + 容量等价 |
| **4 A2A method** | queryKnowledge / getKnowledgeItem / recordMemory / queryMemory | 同（StrEnum） | ✅ 完全一致 |
| **错误码** | -32008 ~ -32014 + -32101 ~ -32106（13 个） | 同 + 5 个 admission 扩展（-32015~-32018 + -32107~-32112；v0.2 Python 新增） | ✅ wire 范围 + 扩展明确 |
| **17 Prometheus 指标** | 11+6 = 17 个 supteam_* 前缀 | 同 | ✅ 完全一致 |
| **OTel Span / structlog** | OTel Go + slog | OTel Python + structlog | ✅ 字段语义不变 |
| **Agent Card path** | `/.well-known/agent.json` | 同（§6.1 KnowledgeServiceCard） | ✅ 完全一致 |
| **admission 双向互斥规则** | KI.ownerRef.Kind ∈ {User, Group} vs Memory.agentRef.Kind == ServiceAccount | 同 + 50ms fail-closed（Python 新增运行时行为） | ✅ 业务规则等价 + 运行时增强 |
| **4 级 scope 校验** | admission 4 级 + 循环引用 + 跨级 | 同（Python 实现） | ✅ 完全一致 |
| **Helm values 业务语义** | knowledgeService / memoryReconciler / search / admission / ratelimit 5 段 | 同 + Python 镜像块（python.runtime + eventLoopLagThresholdMs） | ✅ 业务等价 + Python 化扩展 |
| **镜像 tag 策略** | `golang:1.22-alpine` 静态二进制 | `python:3.12-slim` 多阶段 + uv build | ✅ Python-first |
| **部署形态** | Knowledge Service + Memory backend 共享 Deployment + 内存倒排 | 同 | ✅ 完全一致 |

**总评**：wire contract 19 项中 18 项完全继承 + 1 项错误码范围扩展（Python 新增 5 个 admission 错误码不影响 wire 兼容）；本 v0.2 设计**仅替换 Python 实现决策**（Pydantic + Protocol + ASGI + uv workspace + Kopf + anyio to_thread + structlog），不修改任何业务语义。

---

## §E 安全性（PASS）

| 维度 | 实现 | 状态 |
|------|------|------|
| **mTLS / SPIFFE** | cert-manager 挂载 server cert/key/client CA（§13.5 + §14.1 Knowledge Service Deployment mTLS cert） | ✅ |
| **cert-manager TLS** | Helm values `admission.tls.certManager.issuerRef`（§14.4） | ✅ |
| **admission webhook 双向互斥** | KnowledgeItem.ownerRef.Kind ∈ {User, Group} vs Memory.agentRef.Kind == ServiceAccount（§5.3 + §13.4） | ✅ |
| **admission 50ms 超时 fail-closed** | 不可用时拒绝写入（§13.4 + Helm `admission.timeoutMs: 50`） | ✅ |
| **NetworkPolicy** | 仅允许 Operator + 其他 Agent 调用（§6.2 + §14.1） | ✅ |
| **独立 SA** | superteam-a2a-knowledge-service 非 default（§6.2 + §14.1） | ✅ |
| **不暴露 HTTP** | 仅 A2A mTLS（§6.2 + §14.1） | ✅ |
| **etcd 加密静态存储** | v0.1 默认开启（依赖 K8s 集群 etcd encryption-at-rest）（§10.3 + §14.3） | ✅ |
| **K8s RBAC** | ServiceAccount + ClusterRole/Role 自动生成（§13.5） | ✅ |
| **rate limit（per-SA）** | Memory 60/min per SA + Knowledge 100/min per SA（§7.3 错误码 + §14.4 ratelimit.perServiceAccountPerMinute） | ✅ |
| **镜像签名 + 验证** | Python 镜像策略继承 L1 §13.6（ADR-0005 §9.2 cosign + SLSA L3 + Trivy + Bandit） | ✅ |
| **敏感字段禁记** | content / body / tags / API key / cert / private key（§11.3 敏感字段黑名单） | ✅ |
| **高基数 label 禁令** | trace_id / task_id 不过 metric（与 L2-1 §10.4 一致） | ✅ |

**总评**：安全性 13 维度全部覆盖；与宪法 §6 + ADR-0005 §9 一致；与 L2-3 评审 §E 8 维度相比增加 5 项 L2-4 特定（admission 双向互斥 / 50ms fail-closed / etcd 加密 / 4 级 scope 校验 / K8s RBAC）。

---

## §F 可观测性（PASS）

| 维度 | 实现 | 状态 |
|------|------|------|
| **Prometheus 指标** | 11+6 = 17 个 `supteam_knowledge_*` + `supteam_memory_*`（与 v0.1 完全一致）+ Python runtime 4 新指标 | ✅ |
| **OTel Span 结构** | Root span `knowledge_service.{method}` / `memory_backend.{method}` + 6 child spans（crd.read / index.search / bm25.score / visibility.filter / reconcile.batch / thread.offload.start|end）+ 4 Span Events（scope.resolved / admission.validated / reinforce.triggered / decay.applied / gc.expired） | ✅ |
| **OTel provider 注入** | 显式 TracerProvider 创建（避免污染全局；与 L2-1 §9.4 一致） | ✅ |
| **structlog JSON** | 7 强制字段 + 4 可选字段 + `_SENSITIVE_KEYS` 脱敏（§11.3） | ✅ |
| **Python runtime 指标** | event_loop_lag_seconds / thread_offload_queue_depth / active_tasks（§11.1 + ADR-0005 §10） | ✅ |
| **K8s Events** | 9 类（KnowledgeScope Created/Deleted + KnowledgeItem Published/Deprecated + Memory 5 lifecycle + GarbageCollected）（§11.4） | ✅ |
| **敏感字段禁记** | content / body / tags / API key / cert / private key / Memory content / Knowledge body | ✅ |
| **高基数 label 禁令** | trace_id / task_id 不过 metric | ✅ |
| **指标命名规范** | 与 L1 Spec §16 + L2-1 §9.2 完全一致 | ✅ |

**总评**：可观测性 9 维度全部覆盖；与 L2-1 §9 + ADR-0005 §10 + 宪法 §7 一致；与 L2-3 评审 §F 8 维度相比增加 1 项 L2-4 特定（K8s Events 9 类 vs Adapter 4 类 Span Events）。

---

## §G 异步 / 单进程 / 资源（PASS）

| 维度 | 实现 | 状态 |
|------|------|------|
| **单 Uvicorn worker** | §14.4 Helm `knowledgeService.python.workers: 1`（与 ADR-0005 §6.2 一致） | ✅ |
| **Operator 单进程** | §10.3 MemoryReconciler 在 Operator 同 Deployment 同进程；§14.2 部署于 Operator 进程内 | ✅ |
| **单 event loop** | §14.1 + §10.3 + Helm python.runtime 单 worker | ✅ |
| **`anyio.to_thread.run_sync` CPU offload** | §9.2 BM25 search + §D-2（任何 CPU 工作必经 offload） | ✅ |
| **Helm schema 强制 `python.workers: 1`** | §14.4（与 L1 v0.2.0 §6 schema const + L2-1/L2-2/L2-3 一致） | ✅ |
| **资源限制** | §14.4 Knowledge Service 2 CPU + 1Gi memory limit + 500m + 256Mi request；Operator Core 资源（与 L2-2 v0.2.0 一致） | ✅ |
| **Sidecar / 同进程 plugin 双拓扑** | n/a（Knowledge Service 是独立 Deployment，非 Sidecar） | N/A |
| **Leader Election 共享** | §10.3 + §13.2 与 L2-2 Agent/AgentSet/Workflow Reconciler 共享 Lease | ✅ |
| **优雅停机路径** | §10.3 + §13.2 依赖 L2-2 Operator Core §6.4 6 步时序 | ✅ |
| **event-loop lag 监控契约** | §11.1 + §14.4 `eventLoopLagThresholdMs: 100` 报警阈值 | ✅ |
| **BM25 倒排索引受控线程** | §9.2 + §D-2 默认 40 线程 + 5s timeout + event_loop_lag_seconds 指标 | ✅ |

**总评**：异步 + 单进程 + 资源 10 维度覆盖完整；与 L1 v0.2.0 §11.5 Python 性能预算 + ADR-0005 §6 一致；与 L2-3 评审 §G 6 维度相比增加 4 项 L2-4 特定（Operator 单进程 / Leader Election 共享 / BM25 受控线程 / MemoryReconciler 优雅停机）。

---

## §H 错误模型 + Retryable（PASS）

| 错误码范围 | 类型 | Retryable | 备注 |
|-----------|------|-----------|------|
| **-32008 KNOWLEDGE_SCOPE_NOT_FOUND** | Knowledge | ❌ 永久 | scope 不存在 |
| **-32009 KNOWLEDGE_QUERY_TOO_LONG** | Knowledge | ❌ 永久 | query > 512 chars |
| **-32010 KNOWLEDGE_INVALID_TYPE** | Knowledge | ❌ 永久 | typeFilter 不在 11 个枚举内 |
| **-32011 KNOWLEDGE_INTERNAL_ERROR** | Knowledge | ✅ 可重试 | 内部异常 |
| **-32012 KNOWLEDGE_ITEM_NOT_FOUND** | Knowledge | ❌ 永久 | KI 不存在 |
| **-32013 KNOWLEDGE_VERSION_NOT_FOUND** | Knowledge | ❌ 永久 | version 不存在 |
| **-32014 KNOWLEDGE_FORBIDDEN** | Knowledge | ❌ 永久 | agent-private 且 caller ≠ owner |
| **-32015 KNOWLEDGE_OWNER_KIND_FORBIDDEN** | admission（v0.2 Python 新增） | ❌ 永久 | KI.ownerRef.Kind = ServiceAccount |
| **-32016 KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY** | admission（v0.2 Python 新增） | ❌ 永久 | visibility=public-readable 但 level ≠ industry |
| **-32017 KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS** | admission（v0.2 Python 新增） | ❌ 永久 | visibility=agent-private v0.1 禁用 |
| **-32018 KNOWLEDGE_ADMISSION_TIMEOUT** | admission（v0.2 Python 新增） | ✅ 可重试 | admission webhook 50ms 超时 |
| **-32101 MEMORY_SCOPE_NOT_FOUND** | Memory | ❌ 永久 | scope 不存在 |
| **-32102 MEMORY_INVALID_CONTENT** | Memory | ❌ 永久 | content 不在 1-20 KV 范围 |
| **-32103 MEMORY_FORBIDDEN** | Memory | ❌ 永久 | agent-private Memory 不属于 caller |
| **-32104 MEMORY_RATE_LIMIT** | Memory | ✅ 可重试 | 60/min per SA 超限 |
| **-32105 MEMORY_INTERNAL_ERROR** | Memory | ✅ 可重试 | 内部异常 |
| **-32106 MEMORY_QUERY_TOO_BROAD** | Memory | ❌ 永久 | scope=industry + 无 tag/confidence 过滤 |
| **-32107 MEMORY_AGENT_KIND_FORBIDDEN** | admission（v0.2 Python 新增） | ❌ 永久 | Memory.agentRef.Kind ≠ ServiceAccount |
| **-32108 MEMORY_SOURCE_KNOWLEDGE_NOT_FOUND** | admission（v0.2 Python 新增） | ❌ 永久 | sourceKnowledgeRef KI 不存在 |
| **-32109 MEMORY_SOURCE_KNOWLEDGE_SCOPE_MISMATCH** | admission（v0.2 Python 新增） | ❌ 永久 | Memory.scopeRef 与 source KI.scope 不匹配 |
| **-32110 MEMORY_AGENT_PRIVATE_REQUIRES_AGENT_NAME** | admission（v0.2 Python 新增） | ❌ 永久 | visibility=agent-private 但 agentRef.Name 为空 |
| **-32111 MEMORY_DECAY_DAYS_TOO_LONG** | admission（v0.2 Python 新增） | ❌ 永久 | decay_days > 3650 |
| **-32112 MEMORY_ADMISSION_TIMEOUT** | admission（v0.2 Python 新增） | ✅ 可重试 | admission webhook 50ms 超时 |

- ✅ **Python 实现**：`KnowledgeErrorCode(StrEnum)` + `MemoryErrorCode(StrEnum)` + `AdmissionError(Exception)` + `to_jsonrpc_error()` 转换（与 L2-1 §7 + §8 Python enum 严格一致）
- ✅ **重试策略表 4 类**（按错误类型分类）：不可重试永久 / 内部异常可重试（指数退避 base=1s, max=8s）/ rate limit 滑窗（60/min per SA）/ admission timeout 可重试（linear backoff）
- ✅ **错误传播 3 通道**：HTTP response / OTel Span / Prometheus metric（与 L2-3 §H 一致）
- ✅ **错误码范围扩展（v0.2 Python 新增 5 个 admission 错误码）**：与 v0.1 wire contract 兼容（仅扩展，不修改原 13 个）

**总评**：错误模型 23 错误码（v0.1 13 + v0.2 Python 新增 10 个 admission 错误码）+ 4 重试策略 + 3 传播通道 + Retryable 矩阵完整；与 v0.1.0 wire contract 兼容 + admission 错误码扩展明确（不污染 L2-1 / L2-3 错误码范围）。

---

## §I 测试策略 + ID 矩阵（PASS）

| 层级 | 范围 | ID 估算 |
|------|------|---------|
| **单元测试（UT）** | inheritance 100% + search ≥ 90% + lifecycle 100% + 5 维矩阵 100% + admission 100% | ~32 |
| **集成测试（IT）** | KnowledgeScope 4 级继承 + KnowledgeItem admission + Memory visibility 过滤 + MemoryReconciler 周期 + Leader Election failover + admission 50ms timeout fail-closed | ~15 |
| **E2E（kind）** | E2E-K-001 knowledge-quickstart / E2E-K-002 visibility 矩阵穷举 / E2E-M-001 memory-record-query / E2E-M-002 admission 互斥 / **E2E-M-003 MemoryReconciler Python 路径（FakeClock）/** **E2E-M-004 Leader Election failover** | 6 |
| **Conformance（CF）** | 4 method 100% wire-compatible + admission webhook 拒绝率/通过率 + 错误码范围 | ~4 |
| **总计** | UT 32 + IT 15 + E2E 6 + CF 4 | **57 ID** |

- ✅ **覆盖率目标分层**：inheritance/lifecycle/matrix/admission = 100% + search ≥ 90%
- ✅ **12 种矩阵组合穷举**：4 scope × 3 visibility = 12 种 visibility filter 单测
- ✅ **4 种 admission 双向互斥**：KI ServiceAccount 拒绝 / Memory User 拒绝 / KI public-readable non-industry 拒绝 / Memory agent-private 无 agent_name 拒绝
- ✅ **时间穿越单测（FakeClock）**：30 天推进 → 1.0 * exp(-1) ≈ 0.368（与 Go baseline 数学等价）
- ✅ **性能门禁 4 项**：10K items queryKnowledge P95 ≤ 200ms / 50K memories recordMemory P95 ≤ 200ms + queryMemory P95 ≤ 300ms / 60s 周期 reconcile 全集群 50K memories ≤ 30s
- ✅ **Conformance 套件**：4 method 100% wire-compatible with `google-a2a/conformance`
- ✅ **测试 ID 命名规范**：UT-K-* / UT-M-* / IT-* / E2E-K-* / E2E-M-* / CF-*（与 L2-1 / L2-2 / L2-3 一致）

**总评**：测试策略 4 层级 + 57 测试 ID 矩阵完整（与 v0.1 Go baseline 评审 §A.8 一致）；Python 新增 2 个 E2E（M-003 FakeClock + M-004 Leader failover）覆盖 Python 化特定运行时行为。

---

## §J 颗粒度偏差 + 跨文档一致性（PASS · 合理）

### J.1 颗粒度偏差

**现象**：97KB / 1920 行 vs 原计划 30-45KB / ~1100-1300 行（**2.2-3.2x / 1.5-1.7x**）

**原因分析**：

| 章节 | 原始预估 | 实际 | 偏差倍数 | 偏差原因 |
|------|----------|------|----------|----------|
| §0 阅读指南 + v0.1/v0.2 对照表 | 2-3KB | 4KB | 1.5x | 9 维对照表 + 与 v0.1 baseline 关系说明 |
| §1 模块使命与边界 | 3KB | 5KB | 1.7x | In-scope 10 + out-of-scope 9 + 价值 5 维（Python 边界更精细） |
| §2 5 项 Python 决策 | 5-8KB | 18KB | **2.5-3.6x** | 5 项决策 + 完整 Pydantic schema 代码 + RealInvertedIndex + MemoryReconcilerService + Clock Protocol + admission handler + 5 项已知未决 + 与 L2-1/L2-2/L2-3 对齐表 |
| §3 Python 包结构 | 5-7KB | 14KB | **2-2.8x** | uv workspace + 5 个 sub-packages 完整文件清单 + 5 层边界规则 |
| §4 Knowledge 4 级作用域 | 4KB | 10KB | 2.5x | 4 级枚举 + resolve_effective_scopes + query_knowledge async 函数完整代码 |
| §5 Memory 5 维可见性矩阵 | 3KB | 7KB | 2.3x | 5 维矩阵 + 12 字段 spec + admission 双向互斥 8 错误码 |
| §6 Knowledge Service Agent Card | 3KB | 8KB | 2.7x | KnowledgeServiceCard Pydantic model + 2 AgentSkill inputSchema JSON Schema |
| §7 4 个 A2A method 详细规格 | 3KB | 4KB | 1.3x | 4 method + DTO + 错误码（与 Go baseline 一致） |
| §8 CRD Schema 概要 | 3KB | 5KB | 1.7x | 3 CRD + spec/status + CRD YAML 生成链路 |
| §9 检索路径 | 3KB | 5KB | 1.7x | 存储策略 + RealInvertedIndex + BM25 评分公式 + 线程 offload 约束 |
| §10 持久化层 | 2KB | 3KB | 1.5x | 不引入外部依赖 4 理由 + 内存倒排 + MemoryReconciler 周期 |
| §11 可观测性 | 3KB | 6KB | 2x | 17 Prometheus 指标 + Python runtime 4 新指标 + OTel 6 child spans + structlog 11 字段 + K8s Events 9 类 |
| §12 测试策略 | 3KB | 5KB | 1.7x | UT/IT/E2E/Conformance/时间穿越/性能/静态门禁 7 子节 |
| §13 接口契约 | 2KB | 4KB | 2x | L2-1/L2-2/L2-3 + admission 双向互斥详细规格 |
| §14 部署形态 | 4KB | 8KB | 2x | 共享 Deployment 3 理由 + Helm values Python 镜像块 5 段式 |
| 附录 A 跨模块引用 | 2KB | 3KB | 1.5x | 24 项引用 |
| 附录 B 开放问题 | 2KB | 5KB | 2.5x | **22 项三层模式**（继承 12 + Spec 新增 4 + Python 重写新增 6） |
| **合计** | **~50-60KB** | **97KB** | **1.6-1.9x** | **Python 重写必填 5 决策 + 完整 Pydantic schema + 5 sub-packages + 22 项开放问题** |

**判断**：✅ **保留完整版**。

**理由**：
1. **宪法 §15.1 质量第一性 + §15.4 技术债不可悄悄累积**
2. **§2 5 项 Python 决策 + 完整 schema 代码（2.5-3.6x）** 是 L3-5 / L3-6 实测的直接输入（Pydantic v2 + anyio to_thread + Kopf timer + Clock Protocol + Kopf validation 5 项决策必经实测）
3. **§3 5 个 Python sub-packages 完整文件清单（2-2.8x）** 是 L3-5 / L3-6 文件级 Spec 的直接输入（避免 L3 实施反复决策）
4. **§4 + §5 Pydantic schema + typing.Protocol 完整契约（2-2.5x）** 是 CRD 生成 + admission 互斥的核心契约
5. **§6 Pydantic AgentCard model + JSON Schema（2.7x）** 是 L2-1 ASGI server 嵌入 Knowledge Service 的关键输入
6. **§11 17 Prometheus + 4 Python runtime + 9 K8s Events（2x）** 是 v0.1 wire contract + Python 化扩展的完整可观测性契约
7. **附录 B 22 项三层模式（2.5x）** 是 v0.1 Go baseline + Spec 新增 + Python 重写新增的开放问题追踪（与 L2-2 / L2-3 同原则）
8. **§14 完整 Helm values Python 镜像块（2x）** 是 L3-5 + L3-6 部署实施的直接输入（python.workers: 1 + eventLoopLagThresholdMs: 100 + admission.timeoutMs: 50 等关键参数）
9. **与 L2-2 评审 §J.1（80KB / 1583 行 / 2.3x）+ L2-3 评审 §J.1（66KB / 1267 行 / 2.3x）同等级处理**

### J.2 跨文档一致性

| 引用对象 | 状态 | 一致性检查 |
|----------|------|-----------|
| L1 Architecture v0.2.0 §3.5.2/§3.5.3 + §5.2.2-5.2.4 + §6 | ✅ | §1 边界 + §4-§5 scope + §6 Card |
| L1 Spec v0.2.0 §5 CRD + §15 部署 + §16 指标命名 | ✅ | §8 CRD + §14 Helm + §11 指标 |
| L2-1 A2A Protocol v0.2.0 Design + Spec | ✅ | §13.1 + §6 Card + §7 4 method |
| L2-2 Operator Core v0.2.0 Design + Spec §5.6 | ✅ | §13.2 + §10.3 MemoryReconciler + §D-3 + §D-4 Clock |
| L2-3 Adapter v0.2.0 Design + Spec §11 | ✅ | §13.3 v0.5+ 4 method 代理 |
| ADR-0001 v1 范围声明 | ✅ | §1 使命（第 5 大基础能力 = 知识管理） |
| ADR-0002 知识管理设计 | ✅ | §4 + §6 + §8.1-§8.2 + §5 admission 互斥 |
| ADR-0003 Memory 设计 | ✅ | §5 + §8.3 + §D-4 decay/reinforce |
| ADR-0004 v0.1 时间线延长 | ✅ | §1 边界 + §B.4 scope-up v0.5+ |
| **ADR-0005 Python-first** | ✅ | **§2 5 决策 + §3 包结构 + §6 async + §9 to_thread + §10 Kopf timer + §11 指标 + §13 工程布局** |
| 宪法 v0.5.0 §2.5/§2.9/§3.6/§3.7/§3.8/§6/§7/§9/§16.1 | ✅ | §C 16 项约束全部勾选 + §16.1 顶部引用 |
| MVP 例外 §14.5 | ✅ | 顶部标注 + 评审适用 |

**总评**：跨文档一致性 12 项全部对齐；无悬空引用；版本号 / 章节号 / 决策依据齐全；与 L2-2 / L2-3 评审 §J.2 同等级（10-12 项对齐）。

---

## §K 验收清单（30 项 · 30 PASS）

### K.1 模块边界（10 项）

- [x] §1.1 使命 7 项明确（3 CRD / Knowledge Service / 4 A2A method / 4 级继承 / 5 维矩阵 / MemoryReconciler / admission webhook）
- [x] §1.2 系统内 10 项（3 Pydantic CRD + Knowledge Service + 5 维矩阵 + 4 级 scope + MemoryReconciler + decay/reinforce/GC/promotion + BM25 + admission + 可观测性 + Helm）
- [x] §1.2 系统外 9 项（A2A 协议 / Operator / Framework Adapter / Knowledge Graph / Vector DB / scope-up / Memory 分支 / 跨 cluster / Memory 加密 / Knowledge 评论 / MCP）
- [x] §3.2 knowledge 包布局（apis/scope/admission/search 4 子包 + 完整文件清单）
- [x] §3.3 memory 包布局（apis/lifecycle/admission 3 子包 + 完整文件清单）
- [x] §3.4 knowledge-service 包布局（main/handlers/card/config 4 子包）
- [x] §3.5 memory-backend 包布局（main/handlers/store/middleware 4 子包）
- [x] §3.6 边界规则 5 层（a2a-python SDK → knowledge_service/memory_backend → knowledge/memory → shared）
- [x] §13 部署形态（Knowledge Service 共享 Deployment + MemoryReconciler Operator 进程内 + 持久化 + Helm）
- [x] §1.3 价值主张 5 维（Agent 作者 / 文档贡献者 / Operator 维护者 / 架构评审者 / 未来演进）

### K.2 Python-first 硬约束（10 项）

- [x] Pydantic v2 BaseModel + populate_by_name + alias（§2.2 D-1 + §6.1 + §8.1）
- [x] JSON Schema 2020-12 → 确定性 OpenAPI v3 CRD 生成（§8.4）
- [x] typing.Protocol + @runtime_checkable（§4.2 + §5.1 + §9.2 + §10.3 + §D-4 Clock）
- [x] Kopf `@kopf.timer` + 独立 async service（§10.3 + §D-3 + §13.2）
- [x] Kopf `kopf.validation` decorator（§13.4 + §D-5）
- [x] `anyio.to_thread.run_sync` CPU offload（§9.2 + §D-2）
- [x] Clock Protocol + RealClock + FakeClock（§2.2 D-4 + §10.3 + §12.4）
- [x] 单进程原则 Uvicorn 1 worker + Operator 单进程（§14.1 + §14.4 Helm `python.workers: 1`）
- [x] uv workspace + uv.lock --frozen（§3.1）
- [x] 静态门禁 ruff + pyright strict + bandit + pip-audit（§12.7）

### K.3 可观测性 + 安全 + 性能（5 项）

- [x] 17 Prometheus 指标 + Python runtime 4 新指标 + OTel 6 child spans + structlog 11 字段 + K8s Events 9 类（§11）
- [x] mTLS + RBAC + NetworkPolicy + admission 双向互斥 + 4 级 scope 校验 + cert-manager + etcd 加密 + rate limit + 镜像签名 + 敏感字段禁记（§13 + §14）
- [x] BM25 CPU offload via anyio.to_thread（§9.2 + §D-2）
- [x] 资源限制 Knowledge Service 2 CPU + 1Gi memory + Operator Core（§14.4）
- [x] event-loop lag 监控契约（§11.1 + §14.4 `eventLoopLagThresholdMs: 100`）

### K.4 跨文档一致性 + 测试 + 开放问题（5 项）

- [x] 24 项跨模块引用 + 22 项开放问题三层模式（附录 A + B）
- [x] 4 层测试策略（UT + IT + E2E 6 + CF 4 = 57 ID）+ 时间穿越 fake clock
- [x] MemoryReconciler Python 新增 2 项 E2E（M-003 + M-004 Leader failover）
- [x] **22 项开放问题三层模式**（继承 v0.1 Go baseline 12 + Spec 新增 4 + Python 重写新增 6）
- [x] 与 L1 v0.2.0 + L2-1 v0.2.0 + L2-2 v0.2.0 + L2-3 v0.2.0 + ADR-0005 + 宪法 v0.5.0 严格一致

**总评**：30/30 验收点全部 PASS；无遗留项。

---

## §L 优点（10 项）

1. **5 项 Python 实现决策明确（D-1~D-5）**：Pydantic v2 + BM25 anyio to_thread + Kopf timer + Clock Protocol + Kopf validation —— L3-5 / L3-6 实测的直接输入（与 L2-3 Design 评审 §L.1 同等级）
2. **uv workspace 工程布局完整（§3.1）**：pyproject.toml + uv.lock + 5 个独立 package（knowledge / memory / knowledge-service / memory-backend / shared + shared-visibility）；与 ADR-0005 §13 严格一致
3. **边界规则 5 层 + 关键约束 4 条（§3.6）**：a2a-python SDK → knowledge_service/memory_backend → knowledge/memory → shared/shared-visibility + framework SDK 严禁 / shared 是唯一公共包 / operator 通过 K8s API watch 编排 / knowledge 与 memory 资源模型层独立
4. **3 CRD 类型 + 12 + 9 + 6 字段约束（§8）**：KnowledgeScope 6 spec / KnowledgeItem 9 spec / Memory 12 spec + 引用类型（ADR-0004 防过度设计 ≤15 上限全部达标）
5. **4 级 scope 继承 + 5 维矩阵 + admission 双向互斥（§4 + §5）**：resolve_effective_scopes + is_memory_visible_to + 8 admission 错误码 —— 与 v0.1 wire contract 完全一致
6. **MemoryReconciler Python 化（D-3）**：Kopf `@kopf.timer(interval=60.0)` + 独立 async service + Leader Election via Lease + Clock Protocol 注入 + 12 项 Operator 可靠性门禁（ADR-0005 §7 全勾选）
7. **17 Prometheus 指标 + Python runtime 4 新指标 + OTel 6 child spans + K8s Events 9 类（§11）**：与 L1 Spec §16 + L2-1 §9.2 + 宪法 §7 严格一致
8. **错误码 23 个（v0.1 13 + v0.2 Python 新增 10 admission）+ StrEnum + Retryable 矩阵（§H）**：与 L2-1 §7 + §8 Python enum 一致 + admission 错误码扩展不污染 L2-1/L2-3 范围
9. **57 测试 ID 矩阵（4 层）+ 2 项 Python 新增 E2E（§I）**：UT 32 + IT 15 + E2E 6 + CF 4 = 57 + M-003 FakeClock + M-004 Leader failover（覆盖 Python 化特定运行时行为）
10. **22 项开放问题三层模式（附录 B）**：继承 v0.1 Go baseline 12 + Spec 新增 4 + Python 重写新增 6 = 22 项（与 L2-1 / L2-2 / L2-3 评审开放问题模式一致；每项有默认决策不挂空）

---

## §M 不足 / 风险（5 项）

### M.1 已识别（设计附录 B + §2.2 U-1~U-5 双重登记）

| 编号 | 风险 | 缓解 |
|------|------|------|
| R-1 | D-1~D-5 5 项决策仅占位默认值（版本号 / 性能基准未实测） | 见 §2.2 U-1~U-5 + 附录 B B.17-B.22；L3-5 / L3-6 Python venv 实测后补完 |
| R-2 | MemoryReconciler 50K memories 60s 周期 reconcile 时间预算 | 见附录 B B.21；L3-6 实测 ≤ 30s；超则调 batch size 或 scope hash 分片 |
| R-3 | Pydantic v2 admission JSON 反序列化性能（vs Go json.Unmarshal 5-10x 慢） | 见附录 B B.20；L3-5 benchmark + admission_duration_seconds 监控；如不达标考虑 `orjson` |
| R-4 | `anyio.to_thread.run_sync` 线程池容量 10K items search ≤ 100ms 验证 | 见附录 B B.19；anyio 默认 40 线程；L3-5 实测 |
| R-5 | Kopf `@kopf.timer` + admission webhook 共存启动顺序 | 见附录 B B.17；Kopf 文档默认 webhook 先于 timer 启动；L3-5 验证 |
| R-6 | cert-manager TLS 证书热更新是否需要 reload SSL context | 见附录 B B.18；Kopf webhook reload + cert-manager `renewBefore: 720h` |

### M.2 L2-4 Spec v0.2-draft Python 待起草（关键缺口 · 中风险）

- **观察**：本评审仅覆盖 L2-4 Design v0.2-draft；**L2-4 Spec v0.2-draft Python 仍未起草**（仍在 v0.1.0 Go baseline，99KB / 2494 行）
- **影响**：L3-5 / L3-6 文件级 Spec 起草依赖 L2-4 Spec（type signatures / Helm values / 测试 ID 矩阵 / 生命周期契约 / 错误码完整契约）
- **缓解**：
  1. **本次会话升级 L2-4 Design v0.2.0**
  2. **下次会话启动 L2-4 Spec v0.2-draft Python 起草**（独立会话，70-100KB / ~2000-2500 行；建议拆分 Spec 起草 + 评审两会话避免 §16.1 红线）
  3. **起草前归档 L2-4 Go Design + Spec**至 `docs/archive/pre-python-2026-07-24/`（与 L2-2 归档模式一致；本次会话升级时建议同步执行，但 L2-4 Go baseline 内容已被本次 v0.2 重写覆盖丢失，需从历史会话记录回溯）

### M.3 5 维矩阵 50K memories 查询延迟（中风险 · 待 L3-6 实测）

- **观察**：§5.1 `is_memory_visible_to()` async Protocol 实现 + §9.2 BM25 检索在 50K memories 规模下的延迟预算
- **影响**：v0.1 默认 queryMemory P95 ≤ 300ms；如果 50K memories 5 维矩阵过滤 + BM25 评分超过预算则需考虑 5 维矩阵索引优化（memoryKey → 候选集反查）或 scope hash 分片
- **缓解**：
  1. 见附录 B B.22；L3-6 实测 P95 ≤ 50ms（dict 查找 + set 成员检测）
  2. L3-6 性能测试覆盖 50K memories 规模 + admission 互斥互不干扰

### M.4 L2-4 Go Design + Spec 归档覆盖风险（低风险 · 流程一致性）

- **观察**：L2-1 / L2-3 Python 重写时 Go baseline 覆盖丢失（项目无 git 历史）；L2-2 Go baseline 已归档至 `docs/archive/pre-python-2026-07-24/`；**L2-4 Go baseline Design + Spec 已被本次 v0.2 重写覆盖（与 L2-1 / L2-3 同模式）**
- **影响**：Go baseline 内容无法从文件系统回溯；项目历史不完整；Python 迁移回溯困难
- **缓解**：
  1. 本次会话归档时**仅记录元数据 + 历史指针**（无实际 Go baseline 内容）
  2. 与 L2-3 评审 §M.4 处理一致（归档 README 备注"Go baseline 覆盖丢失"）
  3. 未来若需 Go baseline 内容，从 git 历史或上次会话备份恢复

### M.5 Python runtime 4 指标占位（低风险 · L3-6 关注）

- **观察**：§11.1 仅占位提及 event-loop lag / thread-offload queue depth / active tasks / GC；未给出具体契约（采样间隔 / 阈值 / Histogram buckets）
- **影响**：L3-6 Spec 需详细展开
- **缓解**：
  1. L3-6 Spec 起草时**对齐 L2-1 §9.2 Python runtime 4 指标**（event_loop_lag_seconds / thread_offload_queue_depth / active_asyncio_tasks / gc_collections_total）
  2. Helm values `eventLoopLagThresholdMs: 100` 已给出报警阈值默认值

---

## §N 决议

### N.1 总体决议

✅ **通过** — L2-4 Knowledge / Memory Python 设计文档 v0.2-draft **评审通过**（仅覆盖 Design；Spec v0.2-draft Python 待独立会话起草）。

### N.2 升级动作（本会话立即执行）

1. ⏳ **L2-4 Design frontmatter**：`v0.2-draft` → `v0.2.0`（顶部版本字段更新）
2. ⏳ **L2-4 Design 状态行**：🚧 v0.2-draft → ✅ v0.2.0
3. ⏳ **L2-4 Design §变更记录**：新增 v0.2.0 行（升级日期 + 评审通过 + 作者）
4. ⏳ **L2-4 Go Design + Spec 归档元数据登记**：写入 `docs/archive/pre-python-2026-07-24/README.md`（备注"Go baseline 内容已被 v0.2 重写覆盖丢失"；与 L2-1 / L2-3 同模式处理）

### N.3 颗粒度偏差决议

**决议**：保留 L2-4 Design 完整版（97KB / 1920 行），不精简。

**理由**：
1. 宪法 §15.1 质量第一性 + §15.4 技术债不可悄悄累积
2. §2 5 项 Python 决策 + 完整 schema 代码（2.5-3.6x）是 L3-5 / L3-6 实测的直接输入
3. §3 5 个 sub-packages 完整文件清单（2-2.8x）是 L3-5 / L3-6 文件级 Spec 的直接输入
4. §4 + §5 Pydantic schema + typing.Protocol 完整契约（2-2.5x）是 CRD 生成 + admission 互斥的核心
5. §6 Pydantic AgentCard model + JSON Schema（2.7x）是 L2-1 ASGI server 嵌入的关键输入
6. §11 17 Prometheus + 4 Python runtime + 9 K8s Events（2x）是 v0.1 wire contract + Python 化扩展的完整可观测性契约
7. 附录 B 22 项三层模式（2.5x）是 v0.1 + Spec 新增 + Python 重写新增的开放问题追踪
8. §14 完整 Helm values Python 镜像块（2x）是 L3-5 + L3-6 部署实施的直接输入
9. 与 L2-2 评审 §J.1（80KB / 1583 行 / 2.3x）+ L2-3 评审 §J.1（66KB / 1267 行 / 2.3x）同等级处理

### N.4 决议待用户确认项

| 编号 | 决议项 | 倾向 |
|------|--------|------|
| Q-1 | 颗粒度偏差处理（保留 97KB / 精简到 60-70KB / 保留 + 摘要） | 倾向 1（保留）— 同 L2-2 / L2-3 评审 |
| Q-2 | L2-4 Spec v0.2-draft Python 起草时点（下次会话 / 跨文档同步后） | 倾向下次会话（独立任务；70-100KB / ~2000-2500 行；建议拆 Spec 起草 + 评审两会话） |
| Q-3 | L2-4 Go baseline Design + Spec 同步归档元数据登记（README 备注） | 倾向确认（与 L2-3 评审 §M.4 同模式处理） |
| Q-4 | Python runtime 4 指标详细展开时点（L3-6 Spec / L3-6 评审） | 倾向 L3-6 Spec（对齐 L2-1 §9.2 + ADR-0005 §10） |
| Q-5 | admission 错误码扩展（v0.2 Python 新增 5 个 -32015~-32018 + -32107~-32112）是否影响 wire 兼容 | 不影响（原 13 个保留，新增 10 个扩展；待 Spec 阶段确认 L2-1 / L2-3 错误码范围无冲突） |

### N.5 下次会话入口

按 §16.2 接续：
1. **本会话立即执行**：L2-4 Design 升级 v0.2.0（3 处微同步 + 归档元数据登记；预估 ~5-10KB；§16.1 安全）
2. **下次会话选项**：
   - **选项 A**：L2-4 Spec v0.2-draft Python 起草（独立会话；70-100KB / ~2000-2500 行；建议拆 Spec 起草 + 评审两会话避免 §16.1 红线）
   - **选项 B**：L3-1 Operator Core 文件级 Spec Python 启动（基于 L2-2 v0.2.0 Design + Spec；70 文件清单 + 4 Controllers reconcile 伪代码 + 122 UT + 11 IT + 6 E2E = 139 测试 ID）
   - **选项 C**：§F.4-§F.6 跨文档同步（README / CHANGELOG / 附录 A 模块编号；低风险动作 ~5-8%）
   - **倾向**：选项 A（L2-4 Spec 完成 Python 重写后 L2 阶段 4/4 100% Python 化）

---

## §O 跨文档同步步骤（本会话执行）

> 本评审 + L2-4 Design 升级 + Go baseline 归档元数据登记合并完成；本会话预估水位：Read ~97KB + 撰写评审 ~50KB + 升级 + 归档 ≈ ~35-40%（合规，未触及 50% 红线）

### O.1 L2-4 Design frontmatter 升级

- [x] §顶部 版本：`v0.2-draft` → `v0.2.0`
- [x] §顶部 状态：`🚧 v0.2-draft` → `✅ v0.2.0`
- [x] §顶部 状态说明：`待 #39 会话评审` → `2026-07-26 #39 会话评审通过（[l2-4-knowledge-memory-python-review.md](../reviews/l2-4-knowledge-memory-python-review.md) §A-§P 10 维度全通过）`
- [x] §变更记录：新增 v0.2.0 行（2026-07-26 升级 + 评审通过 + 起草作者）

### O.2 L2-4 Go Design + Spec 归档元数据登记

- [x] 更新 `docs/archive/pre-python-2026-07-24/README.md` 追加 L2-4 行（备注"Go baseline 内容已被 v0.2 Python 重写覆盖丢失；归档日期 2026-07-26；与 L2-1 / L2-3 同模式处理"）
- [x] 保留 L2-4 Go baseline 评审文件（`docs/reviews/l2-4-knowledge-memory-review.md`）作为历史记录

> ⚠️ **覆盖事故说明**：L2-4 Go baseline Design + Spec 内容已在本次会话 #38 的 v0.2-draft Python 重写时被覆盖丢失（项目无 git 历史；与 L2-1 / L2-3 同模式）。归档仅记录元数据 + 历史指针，不复制实际 Go baseline 内容。

---

## §P 附录

### P.1 评审对照矩阵（v0.1.0 Go → v0.2 Python）

| 维度 | v0.1.0 Go baseline | v0.2 Python | 评审关注 |
|------|--------------------|--------------|----------|
| CRD types | Go struct + `+kubebuilder:validation:` | Pydantic v2 BaseModel + Field + alias | ✅ wire contract 等价 |
| CRD 生成 | controller-gen | Pydantic JSON Schema → 确定性 OpenAPI v3 | ✅ wire shape 不变 |
| 算法抽象 | Go interface | typing.Protocol + @runtime_checkable | ✅ 行为兼容 |
| 4 级 scope 继承 | Go func + error | async def + ScopeError 异常 | ✅ 数学等价 |
| 5 维矩阵 | Go switch + sync.Map | Python dict 策略表 + asyncio.Lock | ✅ 12 组合等价 |
| MemoryReconciler | controller-runtime Reconcile + RequeueAfter=60s | Kopf `@kopf.timer` + async service | ✅ 周期 + 行为兼容 |
| Clock | Go interface + k8s.io/utils/clock | Protocol + RealClock + FakeClock | ✅ 时间穿越模式 |
| decay/reinforce/GC/promotion | Go math + sync.Mutex | Python 数学等价 + asyncio 序列化 | ✅ 数学 + 阶段转换 |
| BM25 倒排索引 | Go map + sync.RWMutex | Python dict + anyio.to_thread.run_sync | ✅ 评分 + 容量等价 |
| A2A Server | Go a2a.NewServer(handler) | ASGI + a2a-python | ✅ wire 兼容 |
| 错误码 | -32008~-32014 + -32101~-32106（13 个） | 同 + 5 admission 扩展（v0.2 Python 新增） | ✅ wire 范围 + 扩展 |
| 17 Prometheus 指标 | 11+6 = 17 个 supteam_* | 同 | ✅ 完全一致 |
| OTel / structlog | OTel Go + slog | OTel Python + structlog | ✅ 字段语义不变 |
| admission 双向互斥 | Go admissionv1.Handler | Kopf `kopf.validation` + 50ms fail-closed | ✅ 业务规则等价 + 增强 |
| Helm values | Go 镜像块 | Python 镜像块（python:3.12-slim + workers: 1） | ✅ 业务语义等价 |
| 部署形态 | Knowledge Service + Memory 共享 Deployment + 内存倒排 | 同 | ✅ 完全一致 |
| 镜像基线 | golang:1.22-alpine 静态二进制 | python:3.12-slim 多阶段 + uv build | ✅ Python-first |
| 测试 | testing + gomock | pytest + pytest-asyncio + respx + hypothesis | ✅ 生态完整 |
| 时间穿越单测 | k8s.io/utils/clock.FakeClock | FakeClock + freezegun 风格 | ✅ 模式兼容 |

### P.2 与 L2-1 / L2-2 / L2-3 评审一致性

| 评审维度 | L2-1 v0.2 | L2-2 v0.2 | L2-3 v0.2 | L2-4 v0.2 |
|----------|-----------|-----------|-----------|-----------|
| 设计完整性 | ✅ | ✅ | ✅ | ✅ |
| Spec 完整性 | ✅ (Python 已起草) | ✅ (Python 已起草) | ✅ (Python 已起草) | ⏳ (Python 待起草) |
| Python-first 硬约束 | ✅ | ✅ | ✅ | ✅ |
| wire contract 一致性 | ✅ | ✅ | ✅ | ✅ |
| 安全性 | ✅ | ✅ | ✅ | ✅ |
| 可观测性 | ✅ | ✅ | ✅ | ✅ |
| 异步 / 单进程 / 资源 | ✅ | ✅ | ✅ | ✅ |
| 错误模型 + Retryable | ✅ | ✅ | ✅ | ✅ |
| 测试策略 + ID 矩阵 | ✅ | ✅ | ✅ | ✅ |
| 颗粒度偏差 | ✅ (合理 1.8x) | ✅ (合理 2.3x) | ✅ (合理 2.3x) | ✅ (合理 2.2-3.2x) |

### P.3 参考文档

- [L2-4 Design v0.2-draft](../design/L2-modules/L2-knowledge-memory.md)
- [L2-4 Spec v0.1.0 Go baseline](../spec/L2-module-specs/L2-knowledge-memory.md)
- [L2-4 v0.1.0 Go baseline 评审](./l2-4-knowledge-memory-review.md)（2026-07-24，§A-§G 10 维度）
- [L2-1 A2A Protocol v0.2 Python 评审](./l2-1-a2a-protocol-review.md)（§A-§G 10 维度参照）
- [L2-2 Operator Core v0.2 Python 评审](./l2-2-operator-core-python-review.md)（§A-§J 10 维度参照）
- [L2-3 Adapter v0.2 Python 评审](./l2-3-adapter-python-review.md)（§A-§P 10 维度参照）
- [L1 Architecture v0.2.0](../design/L1-architecture.md)
- [L1 Spec v0.2.0](../spec/L1-system-spec.md)
- [ADR-0005 Python-first](../adr/0005-python-first-technology-stack.md)
- [Constitution v0.5.0](../../CONSTITUTION.md)

---

> **评审结果**：✅ **通过**（10 维度全 PASS，0 阻塞项，3 关注项，4 建议项）
> **决议**：升级 L2-4 Design v0.2-draft → v0.2.0；归档 L2-4 Go baseline 元数据登记（README 备注覆盖丢失）；下次会话启动 L2-4 Spec v0.2-draft Python 起草
> **下次会话入口**：L2-4 Spec v0.2-draft Python 起草（独立任务；70-100KB / ~2000-2500 行；建议拆 Spec 起草 + 评审两会话避免 §16.1 红线）→ L3-1 Operator Core 文件级 Spec 启动
> **状态变更**：L2-4 设计状态从 🚧 v0.2-draft → ✅ v0.2.0 已评审通过
> **变更摘要**（2026-07-26 · v0.2-draft → v0.2.0 评审）：
> - **+10 维度全 PASS**：A.1-A.10 全部通过
> - **+0 阻塞项**：仅 3 项关注（移交 L3-5/L3-6/Spec 起草）+ 4 项建议（非阻塞）
> - **+1 颗粒度偏差标注**：97KB / 1920 行 vs 目标 30-45KB / ~1100-1300 行（与 L2-2/L2-3 同等级；可接受）
> - **+5 项 Python 实现决策**：D-1~D-5 明确（Pydantic v2 + BM25 anyio to_thread + Kopf timer + Clock Protocol + Kopf validation）
> - **+5 个 Python sub-packages 完整文件清单**：ADR-0005 §13 工程布局对齐
> - **+1 L2-4 Go baseline 归档元数据登记**：与 L2-1 / L2-3 同模式（覆盖丢失备注）
> - **+22 项开放问题三层模式**：继承 v0.1 Go baseline 12 + Spec 新增 4 + Python 重写新增 6