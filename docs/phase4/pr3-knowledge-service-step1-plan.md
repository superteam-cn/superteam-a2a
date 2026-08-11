# Phase 4 PR-3 Plan v0.1-draft · Knowledge Service Step 1（8 CRD types + 4 shared 模块 + 测试）

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-11 · #104 启动）|
| 上游 | #103 PR-2 Hello Agent Step 2 完整收口（PR #45 squash merge `76c08f2` · 14/14 测试 PASS · 5 SUCCESS CI）+ L3-5 Knowledge Service v0.2.0（2026-07-29 #63.5 评审通过 · 10 维度全 PASS）+ L3-6 Memory backend v0.2.0（2026-07-30 #67 评审通过）+ ADR-0006 v1.0 Accepted D 方案（单进程架构）|
| 下游 | Phase 4 PR-4（Knowledge Service Step 2 · 12 service + 4 A2A handler + 23 错误码）+ PR-5（Knowledge Service Step 3 · 7 Helm + RBAC + kind E2E）+ v0.5+ 演进 |
| 关联 PR | Phase 4 PR-3 Knowledge Service Step 1 · 本 plan |
| main HEAD | `76c08f2`（PR #45 squash merge commit · 4 历史 feat 分支 commit 收口）|
| 启动条件 | ✅ 全部满足（PR-1 + PR-2 merged · BP 严格生效 · Dependabot 自动化 · ⑭⑮⑯⑰ 全部解决）|

---

## §1 目标与边界

**目标**：将 L3-5 Knowledge Service v0.2.0 文件级 Spec 中的 **3 CRD types（KnowledgeScope / KnowledgeItem / Memory schema）+ 5 辅助类型** 与 **4 shared 模块（与 L3-6 共享的 visibility 矩阵 + 4 级 scope 继承 + KnowledgeType 枚举）** 落地为 **8 CRD type 文件 + 4 shared 模块文件 + 完整 pytest 测试**。这是 Knowledge Service **"领域模型层"** 的关键里程碑（PR-3 完成后，PR-4/5 直接基于该层实现 handler + Helm）。

**PR-3 实装清单**（L3-5 §1.4 + §3 + ADR-0002 §3 + ADR-0003 §3）：

| 类别 | 数量 | 路径前缀 | 关键依赖 |
|---|---|---|---|
| **3 CRD types** | 3 | `packages/knowledge/src/supteam_a2a/knowledge/crd/` | Pydantic v2 + Field + populate_by_name + alias |
| **5 辅助类型** | 5 | `packages/knowledge/src/supteam_a2a/knowledge/crd/` | frozen BaseModel + StrEnum |
| **4 shared 模块** | 4 | `packages/shared-visibility/src/supteam_a2a/shared/visibility/` | 5 维矩阵 + 4 级 scope + KnowledgeType |
| **pyproject.toml × 2** | 2 | `packages/{knowledge,shared-visibility}/` | uv workspace + ruff + pyright |
| **pytest 测试（UT + IT）** | ~25 ID | `tests/{unit,integration}/knowledge*/` | CRUD + 边界 + error path |

**PR-3 增量测试 ID**（基于 L3-5 §10.1 60 测试 ID 矩阵的子集）：

- UT 增量：**~20**（KS-CRD-UT × 5 + KI-CRD-UT × 7 + MEM-CRD-UT × 5 + SV-SCOPE-UT × 2 + SV-VIS-UT × 2 + SV-KT-UT × 1 + SV-INH-UT × 2 = ~24 ID）
- IT 增量：**~6**（KS-CRD-IT × 2 + KI-CRD-IT × 2 + MEM-CRD-IT × 1 + wire-sync IT × 1 = ~6 ID）

**PR-3 测试增量合计**：~30 ID（UT 24 + IT 6）· 4 重静态门禁（ruff check + ruff format + pyright + pytest）。

**不在范围**（明确剔除 · 推迟到 PR-4/PR-5）：

- ❌ 4 A2A method handler（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）— 推迟到 PR-4
- ❌ ASGI server + Card-driven 入口 — 推迟到 PR-4
- ❌ admission webhook 双向互斥 + cert-manager TLS + 50ms fail-closed — 推迟到 PR-4
- ❌ BM25 倒排索引 + 4 级 scope resolver + visibility resolver — 推迟到 PR-4（仅在 shared 模块中暴露类型接口 + 策略表占位）
- ❌ MemoryReconciler 60s kopf.timer — 已由 L4-Phase2 PR-1 实装（PR #17 merged）· PR-3 不重复实现
- ❌ 23 错误码 enum — 推迟到 PR-4
- ❌ Helm 7 模板 + Dockerfile — 推迟到 PR-5
- ❌ 修改 `services/knowledge-memory-service/` — PR-3 不涉及
- ❌ 修改 L3-5 Spec — v0.2.0 已评审通过

---

## §2 设计决策（5 项关键）

### §2.1 新增 `packages/knowledge/` + `packages/shared-visibility/` uv workspace 包

**新增 2 个 uv workspace 包**：

| 包名 | 路径 | 职责 |
|---|---|---|
| `superteam-a2a-knowledge` | `packages/knowledge/` | 3 CRD types Pydantic v2 + 5 辅助类型 + 18 spec + 19 status 字段 |
| `superteam-a2a-shared-visibility` | `packages/shared-visibility/` | 5 维 visibility 矩阵 + 4 级 scope 继承 + KnowledgeType 枚举（与 L3-6 共享）|

**理由**：
- 严格遵循 ADR-0005 §13.1 uv workspace 布局（与 `a2a-core` / `adapter-sdk` / `operator` 同模式）
- `knowledge` 包为 Knowledge Service 领域模型层（仅 Pydantic types + 静态方法）
- `shared-visibility` 包为 L3-5/L3-6 共享 visibility 逻辑层（避免循环依赖）
- 0 系统级依赖（仅 `pydantic>=2,<3` + `python-dateutil>=2.9`）

### §2.2 8 CRD types 文件拆分

**3 主 CRD types**（L3-5 §3）：

| 文件 | 字段数 | wire alias 数 | 测试 ID |
|---|---|---|---|
| `knowledgescope.py` | 6 spec + 6 status + 7 嵌套类型 = ~20 类型 | 9 个 alias | KS-CRD-UT × 5 + KS-CRD-IT × 2 |
| `knowledgeitem.py` | 7 spec + 7 status + 6 嵌套类型 = ~20 类型 | 5 个 alias | KI-CRD-UT × 7 + KI-CRD-IT × 2 |
| `memory_schema.py` | 5 spec + 5 status + 5 嵌套类型 = ~15 类型 | 4 个 alias | MEM-CRD-UT × 5 + MEM-CRD-IT × 1 |

**5 辅助类型文件**（按 L3-5 §1.4 文件清单）：

| 文件 | 类型 | 用途 |
|---|---|---|
| `scope_reference.py` | `ScopeReference` (frozen BaseModel) | KnowledgeScope.parentRef + KnowledgeItem.scopeRef 共享引用 |
| `item_reference.py` | `ItemReference` (frozen BaseModel) | KnowledgeItem.supersededBy + Memory.sourceKnowledgeRef 共享引用 |
| `inherit_rules.py` | `InheritRules` (frozen BaseModel) | KnowledgeScope.inheritRules 4 级 scope 继承过滤规则 |
| `scope_level.py` | `ScopeLevel` (StrEnum) | 4 级 scope 枚举（agent/agentset/workflow/system）|
| `scope_phase.py` | `ScopePhase` (StrEnum) | KnowledgeScope.status.phase 状态机 |

**理由**：
- 3 主 CRD 文件保持 L3-5 §3 完整 Pydantic schema（便于直接落地）
- 5 辅助类型独立文件便于跨 CRD 复用 + 测试隔离
- 与 L3-1 Operator Core v0.2.0 §3 的 CRD 拆分模式一致（Agent / AgentSet / Workflow 各自独立文件）

### §2.3 4 shared 模块（与 L3-6 共享）

**`packages/shared-visibility/src/supteam_a2a/shared/visibility/`**：

| 文件 | 暴露 API | 测试 ID |
|---|---|---|
| `scope_resolver.py` | `ScopeResolver` Protocol + `ScopeError` exception + 4 级 scope 解析接口 | SV-SCOPE-UT × 2 |
| `visibility_matrix.py` | `VisibilityMatrix` Protocol + 5 维矩阵策略表占位 + `KnowledgeVisibility` re-export | SV-VIS-UT × 2 |
| `knowledge_type.py` | `KnowledgeType` StrEnum re-export（从 packages/knowledge 导入） | SV-KT-UT × 1 |
| `scope_inherit.py` | `ScopeInherit` Protocol + `InheritRules` re-export + 4 级继承过滤接口 | SV-INH-UT × 2 |

**理由**：
- 与 L3-6 §1.4 `packages/shared/visibility/` 同模式（避免后续 PR-4/5 合并时循环依赖）
- PR-3 仅暴露 **Protocol 接口 + 类型 re-export**（**不实现业务逻辑**——业务逻辑推迟到 PR-4）
- Protocol 占位便于后续 PR-4 在 `services/knowledge-service/` 实现具体类（dependency inversion）

### §2.4 Pydantic v2 + populate_by_name + alias 双向映射

**3 主 CRD types 严格遵循 5 项 wire contract**（L3-5 §3 + L2-4 v0.2.0 §3.7）：

1. 所有时间字段 `AwareDatetime`（UTC）
2. 枚举用 `StrEnum`（wire 字符串值兼容）
3. 不可变 value object 加 `frozen=True`（SubjectReference / ScopeReference / AgentReference / ItemReference / InheritRules / TaskReference）
4. `populate_by_name=True` + `alias` 实现 wire camelCase ↔ Pythonic snake_case 单向映射
5. `extra="forbid"` 严格模式（与 K8s API server strict 校验一致）

**理由**：
- wire contract 完全继承 L2-4 v0.2.0 Spec（PR-3 不引入 wire 漂移）
- Pydantic v2 `populate_by_name=True` 允许 Python 测试用 snake_case 字段（更 Pythonic）
- `alias` 保留 wire 端 camelCase（与 K8s API server convention 一致）
- `extra="forbid"` 拒绝额外字段（避免 typo 静默通过）

### §2.5 测试策略：UT + IT 双层

**UT（单元测试）· ~24 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| KS-CRD-UT | 5 | KnowledgeScopeSpec 6 字段 + SubjectReference frozen + ScopeReference frozen + InheritRules + KnowledgeVisibility enum |
| KI-CRD-UT | 7 | KnowledgeItemSpec 7 字段 + KnowledgeType 4 类 + ItemReference frozen + DecayState 嵌套 + superseded_by 链 + tags 长度 + ItemPhase 状态机 |
| MEM-CRD-UT | 5 | MemorySpec 5 字段 + MemoryPhase 5 态 + GCState 4 态 + decay_days 边界 + effective_confidence 衰减公式纯函数 |
| SV-SCOPE-UT | 2 | ScopeResolver Protocol + ScopeError exception |
| SV-VIS-UT | 2 | VisibilityMatrix Protocol + KnowledgeVisibility re-export |
| SV-KT-UT | 1 | KnowledgeType re-export（4 类 wire 字符串值）|
| SV-INH-UT | 2 | ScopeInherit Protocol + InheritRules re-export |

**IT（集成测试）· ~6 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| KS-CRD-IT | 2 | `model_json_schema()` 确定性（`sort_keys=True` + x-kubernetes-* extensions）+ CRD YAML round-trip |
| KI-CRD-IT | 2 | 同上 + 7 status 字段映射 + superseded_by 链 wire 同步 |
| MEM-CRD-IT | 1 | 同上 + 5+5 status 字段 + 衰减公式常量 wire 校验 |
| wire-sync IT | 1 | 3 CRD × L2-4 v0.2.0 Spec §3 字段 1:1 对齐（grep + 静态断言）|

**理由**：
- UT 覆盖所有 Pydantic 字段校验 + 状态机 + 不可变性 + 双向映射
- IT 覆盖 schema 生成确定性 + wire sync（避免 PR-3 引入 wire 漂移）
- 推迟 CF/E2E/TZ/PERF 到 PR-4（handler 集成 + BM25 倒排索引 + 衰减穿越 + kind 集群）
- 测试 ID 命名严格遵循 L3-5 §10.1 规范（KS-CRD / KI-CRD / MEM-CRD / SV-*）

---

## §3 实施步骤（4 阶段 · 接力模式 · 宪法 §16.1）

### 阶段 A · 主 Agent 起草 plan（本会话 · 进行中）

- ✅ 本 plan 文档（`docs/phase4/pr3-knowledge-service-step1-plan.md` · ~12-16KB · v0.1-draft）
- ✅ Issue #46 创建跟踪
- 🚧 feat/phase4-pr3-knowledge-service-step1 分支 + commit + push
- 🚧 PR #46 创建 + 等 CI 5 SUCCESS（markdownlint + 文档门禁）
- 🚧 项目发起人 squash merge

### 阶段 B · Subagent 隔离实装（估算 200K-400K tokens · ~45-90 分钟 · #105）

**Subagent 任务清单**（与 PR-2 阶段 B 同模式 · §16.1 实际水位判断）：

| Subagent | 任务 | 估算 tokens | 隔离方式 |
|---|---|---|---|
| Subagent 1 | `packages/knowledge/` 包骨架 + pyproject.toml + 8 CRD types 文件实装 + KS/KI/MEM-CR D UT 测试（24 ID） | 100K-150K | worktree 隔离 |
| Subagent 2 | `packages/shared-visibility/` 包骨架 + pyproject.toml + 4 shared 模块实装 + SV-* UT 测试（7 ID） | 50K-80K | worktree 隔离 |
| Subagent 3 | 3 IT 测试文件（CRD schema 确定性 + YAML round-trip + wire-sync 静态断言） | 40K-60K | worktree 隔离 |
| Subagent 4（可选）| 文档同步（§F.1-§F.6） + L3-5 Spec 附录 A 关联更新 | 30K-50K | worktree 隔离 |

**Subagent 接力原则**（§16.1 + #79 / #103 经验）：
- 主 Agent 仅调度 + 验证 + 收口（5-8% 水位）
- 每个 Subagent 在 **独立 worktree** 中实装（避免文件冲突）
- Subagent 完成后回到主分支 → 主 Agent 合并 + 验证
- Subagent 必须 `uv sync --all-packages --all-extras` 后再开始（避免 import 路径错误）
- 每个 Subagent 完成后必须 `ruff check + ruff format + pyright + pytest` 全绿才能交付

### 阶段 C · 主 Agent 收口（10-20 分钟 · #106）

1. fast-forward main（所有 Subagent commit 合并）
2. 验证：ruff check All passed + ruff format 0 差异 + pyright 0 errors
3. 验证：pytest `tests/unit tests/integration/knowledge*` **~30/30 PASS**
4. `git checkout -b feat/phase4-pr3-knowledge-service-step1`（**实装分支** · 与 plan PR #46 分开）
5. push 实装分支 → `gh pr create` → PR #47
6. 等 CI 5 SUCCESS（BP 严格生效 · 项目发起人 squash merge 或 Dependabot bypass）
7. Issue #46 close + MEMORY.md 头部更新

### 阶段 D · MEMORY 维护（5-8% 水位 · 10 分钟 · #107）

1. 创建 `session-2026-08-XX-cont104-pr3-knowledge-crd.md`
2. MEMORY.md 头部状态行更新（PR #47 merged · main HEAD 推进）
3. 跨文档同步（§F.1-§F.6）：
   - `ROADMAP.md` · Phase 4 6/6 PR 完成进度更新
   - `README.md` · Knowledge Service 部分更新（领域模型层）
   - `CONSTITUTION-CHANGELOG.md` · v0.5.0 → v0.5.1（如有微同步）
   - `L3-5 Spec` 附录 A · 关联 PR + Commit SHA 更新
   - `L3-6 Spec` 附录 A · 关联 packages/shared-visibility/ 引用更新
   - `docs/admin/l4-package-layout.md` · 新增 packages/knowledge + packages/shared-visibility 章节
4. 关键不变量映射更新（PR-3 验证 5 项保持）

---

## §4 PR-3 验收清单（10 项）

| # | 项 | 验证方法 |
|---|---|---|
| 1 | `packages/knowledge/` 包创建（pyproject.toml + 8 CRD type 文件 + `__init__.py`） | `ls packages/knowledge/src/supteam_a2a/knowledge/crd/` · 8 文件存在 |
| 2 | `packages/shared-visibility/` 包创建（pyproject.toml + 4 shared 模块 + `__init__.py`） | `ls packages/shared-visibility/src/supteam_a2a/shared/visibility/` · 4 文件存在 |
| 3 | 3 主 CRD types 完整（KnowledgeScope + KnowledgeItem + Memory schema） | 18 spec + 19 status 字段 · 与 L2-4 v0.2.0 §3 字段 1:1 对齐 |
| 4 | 5 辅助类型完整（ScopeReference + ItemReference + InheritRules + ScopeLevel + ScopePhase） | 5 frozen BaseModel / StrEnum · 在 8 CRD 文件中正确引用 |
| 5 | 4 shared 模块 Protocol 接口定义（ScopeResolver + VisibilityMatrix + KnowledgeType + ScopeInherit） | 4 Protocol + 2 exception + 1 re-export |
| 6 | UT 测试 ~24 ID 全部 PASS | `pytest tests/unit/knowledge*/` · 24/24 PASS |
| 7 | IT 测试 ~6 ID 全部 PASS（schema 确定性 + YAML round-trip + wire-sync） | `pytest tests/integration/knowledge*/` · 6/6 PASS |
| 8 | ruff check All passed + ruff format 0 差异 + pyright 0 errors | GitHub Actions CI |
| 9 | wire-sync 静态断言通过（3 CRD × L2-4 §3 字段 1:1 对齐 · 0 漂移） | `pytest tests/integration/test_wire_sync.py` |
| 10 | 5 项关键不变量 100% 保持（wire contract + 4 纯函数 + frozen + populate_by_name + extra=forbid） | 验证脚本 + PR description |

---

## §5 风险与缓解（6 项）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | uv workspace 跨包依赖循环（`shared-visibility` ↔ `knowledge`） | build 失败 + pytest collection error | `shared-visibility` 仅 re-export + Protocol 接口；不允许反向 import `knowledge` |
| 2 | Pydantic v2 `populate_by_name=True` + pyright 字段类型推导不一致（PR #20 经验） | CI pyright gap · 41 errors | 测试 fixtures 严格使用 wire alias（camelCase）· 避免 snake_case kwargs |
| 3 | wire 漂移（3 CRD × L2-4 §3 字段 1:1 对齐失败） | 后续 PR-4 handler 实装失败 · 23 错误码错位 | IT 测试 `test_wire_sync.py` 静态断言 + grep 双向验证 |
| 4 | `model_json_schema()` 推导非确定性（`sort_keys=False`） | CRD YAML git diff 噪声 | 显式 `model_json_schema()` 调用 + `sort_keys=True` + `x-kubernetes-*` 扩展注入测试 |
| 5 | Subagent 接力时 token plan 中断（#79 经验 · 331 tool uses / 23 分钟 · 429 终止） | Subagent 实装中断 · main Agent 修复 | 每个 Subagent 任务拆分 ≤ 100K tokens · 关键 commit 步骤主 Agent 备份 |
| 6 | `frozen=True` + `populate_by_name=True` 组合在 Pydantic v2 某些版本的 copy() 行为差异 | 测试 fixture copy() 失败 | UT 测试仅用 `model_validate()` 不用 `copy()` · 或在 fixture 中显式 `model_copy(update=...)` |

---

## §6 5 项关键不变量保持（PR-3 验证）

| # | 不变量 | PR-3 验证方法 |
|---|---|---|
| 1 | wire contract 完全继承 L2-4 v0.2.0 Spec（18 spec + 19 status 字段永久不变） | IT `test_wire_sync.py` · 静态断言 L2-4 §3 字段名集合 == 3 CRD 字段名集合 |
| 2 | Pydantic v2 + populate_by_name + alias + extra=forbid + frozen | UT 每个 CRD type 测试 model_config + extra=forbid + frozen 实例不可变 |
| 3 | 5 维 visibility 矩阵 + 4 级 scope（agent/agentset/workflow/system）永久不变 | UT `KS-CRD-UT-005` KnowledgeVisibility enum + `KS-CRD-UT-001` ScopeLevel enum 序列化 |
| 4 | Python-first 边界（packages/knowledge 仅依赖 pydantic + python-dateutil，0 系统级依赖） | `pyproject.toml` dependencies 仅 2 项 · ruff check `import` 规则 |
| 5 | wire sync 矩阵（3 CRD × L2-4 v0.2.0 §3 字段 1:1 对齐） | IT 静态断言 · grep 双向验证 · 0 漂移 |

**额外 PR-3 不变量**（uv workspace 层级）：

- ✅ `packages/knowledge` 与 `packages/shared-visibility` 严格分离（无循环依赖）
- ✅ `shared-visibility` 仅暴露 Protocol 接口 + 类型 re-export（**不实现业务逻辑**——推迟到 PR-4）
- ✅ 测试文件镜像规则（每个 production `src/.../*.py` 有同职责 `tests/unit/.../test_*.py`）
- ✅ `populate_by_name=True` + `alias` 双向映射（PR-3 严格使用 wire alias 测试 fixtures · 避免 #81 pyright gap）

---

## §7 测试策略增量（PR-3）

| 层级 | PR-2 终态 | PR-3 增量 | PR-3 累计 |
|---|---|---|---|
| UT | 22 | **+24**（KS/KI/MEM-CR D UT × 17 + SV-* UT × 7）| 46 |
| CF | 18 | 0 | 18 |
| IT | 24 | **+6**（KS/KI/MEM-CR D IT × 5 + wire-sync IT × 1）| 30 |
| E2E | 6 | 0 | 6 |
| DEPLOY | 17 | 0 | 17 |
| PERF | 0 | 0 | 0 |

**PR-3 测试增量**：~30 ID（UT 24 + IT 6）· 4 重静态门禁（ruff + ruff format + pyright + pytest）· 覆盖率 ≥ 80%（L3-5 §10.4 基线）

**测试 ID 命名规范**（L3-5 §10.1 严格遵守）：

- **KS-CRD-UT-001~005** · KnowledgeScope schema 5 子项
- **KI-CRD-UT-001~007** · KnowledgeItem schema 7 子项
- **MEM-CRD-UT-001~005** · Memory schema 5 子项
- **SV-SCOPE-UT-001~002** · ScopeResolver Protocol 2 子项
- **SV-VIS-UT-001~002** · VisibilityMatrix Protocol 2 子项
- **SV-KT-UT-001** · KnowledgeType re-export 1 子项
- **SV-INH-UT-001~002** · ScopeInherit Protocol 2 子项
- **KS-CRD-IT-001~002** · KnowledgeScope schema 确定性 + round-trip
- **KI-CRD-IT-001~002** · KnowledgeItem schema 确定性 + round-trip
- **MEM-CRD-IT-001** · Memory schema 确定性 + round-trip + 衰减公式常量
- **wire-sync-IT-001** · 3 CRD × L2-4 §3 字段 1:1 对齐 + 0 漂移

---

## §8 Phase 4 PR 序列更新（PR-1 + PR-2 已 merged · PR-3 启动中）

| PR | 标题 | 状态 | main HEAD | 工作量 |
|---|---|---|---|---|
| #98 PR-1 | Hello Agent Step 1（5 Python + 22 测试） | ✅ merged `c97330bb` | `5e6d79b` | 2 周（已完成）|
| #99 PR-2 | Hello Agent Step 2（Dockerfile + 7 Helm + kind E2E） | ✅ merged `76c08f2` | `76c08f2` | 1 周（已完成）|
| **#104 PR-3** | **Knowledge Service Step 1**（8 CRD + 4 shared + ~30 测试） | 🚧 **本 plan 启动** | （待 PR-3 完成后） | **1.5 周** |
| #102 PR-4 | Knowledge Service Step 2（12 service + 4 A2A handler + 23 错误码） | 📋 待启动 | — | 2 周 |
| #102 PR-5 | Knowledge Service Step 3（7 Helm + RBAC + kind E2E） | 📋 待启动 | — | 1 周 |

**Phase 4 进度**：2/5 PR 已 merged · **3/5 PR 启动中**（本 plan）
**Phase 4 剩余工作量**：~4.5 周集中（2h/day）

---

## §9 宪法 v0.5.0 兼容性

| 条款 | 兼容性 | 验证 |
|---|---|---|
| §3.4 文档同步 | ✅ | plan 文档 + Issue #46 + MEMORY 同步 + §F.1-§F.6 跨文档 |
| §6 测试纪律 | ✅ | 4 重静态门禁（ruff + ruff format + pyright + pytest）+ pytest ~30 PASS |
| §7 关键决策记录 | ✅ | 5 项设计决策（uv workspace 拆分 + 8 CRD 文件拆分 + 4 shared + Pydantic v2 配置 + UT/IT 双层）|
| §9.7 文档先行 | ✅ | 本 plan 文档先于实装（v0.1-draft · 启动条件明确）|
| §13.1 测试 ID 命名 | ✅ | KS-CRD/KI-CRD/MEM-CRD/SV-* 系列连贯 · 不与 L3-4 HELLO-* / L3-5 §6 H-QK/H-GKI/H-RM/H-QM / L3-6 TEST-MEM-* 重名 |
| §13.6 依赖锁定 | ✅ | `pyproject.toml` 依赖固定版本范围 + `uv.lock` 提交 |
| §14.5 MVP 例外 | ✅ | 0 例外 · 5 项关键不变量 100% 保持 |
| §15 安全基线 | ✅ | PR-3 仅涉及 Pydantic types · 0 网络/进程/文件系统依赖 · 0 安全风险 |
| §16.1 水位纪律 | ✅ | Subagent 接力模式（Phase B 4 个 Subagent 隔离 worktree）+ 主 Agent 5-8% 水位调度 |

---

## §10 M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-11 · #104 启动）
- **M.2 落地记录**：#104（2026-08-11 · Issue #46 创建 + 本 plan 文档完成 · 准备进入 Phase B Subagent 实装）
- **M.3 关联 PR**：Phase 4 PR-3 Knowledge Service Step 1 · 本 plan（PR #46 plan 文档 + PR #47 实装代码）
- **M.4 下次会话入口**：
  - Phase A：本会话完成（plan + Issue #46 + commit + push + PR #46 + CI + squash merge）
  - Phase B：#105 启动 Subagent 接力实装（4 Subagent worktree 隔离）
  - Phase C：#106 主 Agent 收口（lint + test + 实装 PR #47 创建 + CI + squash merge）
  - Phase D：#107 MEMORY 维护（session + 跨文档 §F.1-§F.6）
- **M.5 关注项台账**：
  - ① uv workspace 跨包循环依赖（`shared-visibility` 仅 Protocol + re-export · 避免反向 import）
  - ② Pydantic v2 `populate_by_name=True` + pyright 兼容性（PR #20 经验 · 测试 fixtures 用 wire alias）
  - ③ wire 漂移（IT `test_wire_sync.py` 静态断言 + grep 双向验证 · 0 漂移）
  - ④ `model_json_schema()` 推导非确定性（`sort_keys=True` + x-kubernetes-* 扩展注入测试）
  - ⑤ Subagent 接力 token plan 中断（#79 经验 · 每个 Subagent ≤ 100K tokens · 主 Agent 备份关键 commit）
  - ⑥ `frozen=True` + `populate_by_name=True` + `copy()` 行为差异（Pydantic v2 · 仅用 `model_validate()` 不用 `copy()`）
- **M.6 文档状态**：v0.1-draft 完整（10 节 · 估算 ~14KB · 启动前完整）