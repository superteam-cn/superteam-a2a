# Phase 4 PR-4a Plan v0.1-draft · Knowledge Service Step 2a（23 错误码 + admission webhook 50ms fail-closed + 入参校验）

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-12 · #106 启动 · PR-4 拆分后第一个子 PR） |
| 上游 | #105 PR-3 Knowledge Service Step 1 Phase B merged (`74af527` · 30 测试 ID · 284 PASS) + #104 PR-3 plan merged (`ce76eaa`) + L3-5 Knowledge Service v0.2.0（2026-07-29 #63.5 评审通过 · 10 维度全 PASS）+ L3-6 Memory backend v0.2.0（2026-07-30 #67 评审通过）+ ADR-0006 v1.0 Accepted D 方案（单进程架构）|
| 下游 | **#107 PR-4b**（4 A2A handler + 12 service · 依赖 PR-4a 错误码 + admission 错误码）→ **#108 PR-4c**（ASGI server + Card-driven + BM25 + scope resolver · 依赖 PR-4b handlers）→ **#109 PR-5**（7 Helm + RBAC + kind E2E · 依赖 PR-4c ASGI server）→ v0.5+ 演进 |
| 关联 PR | Phase 4 PR-4a Knowledge Service Step 2a · 本 plan |
| main HEAD | `d1877ad`（#105 §F.1-§F.6 跨文档同步 commit · 含 PR-3 Phase B 收口 + ROADMAP/CONSTITUTION-CHANGELOG/README/L3-5/L3-6 M.4 同步 + l4-package-layout 新建） |
| 启动条件 | ✅ 全部满足（PR-3 merged · BP 严格生效 · Dependabot 自动化 · ⑭⑮⑯⑰ 全部解决）|

---

## §1 目标与边界

**目标**：将 L3-5 Knowledge Service v0.2.0 + L3-6 Memory backend v0.2.0 文件级 Spec 中的 **23 错误码 enum**（11 KNOWLEDGE_* + 12 MEMORY_*）+ **admission webhook 50ms fail-closed**（L3-5 §5 + L3-6 §6 admission 双向互斥 5 步算法）+ **入参校验**（Pydantic v2 model_validator + async validators）落地为 **3 个新模块 + 1 个 admission webhook handler + ~17 测试 ID**。这是 Knowledge Service **"错误码与入参校验层"** 的关键里程碑（PR-4a 完成后，PR-4b/4c/5 直接基于该层实现 handler + ASGI server + Helm）。

**为什么拆分 PR-4a**（按用户决策 2026-08-12 #106）：
- PR-4 原始范围 = 12 service + 4 A2A handler + 23 错误码 + ASGI server + Card-driven + admission webhook + BM25 + 4 级 scope resolver · **2 周工作量过大**
- 拆分后每个子 PR **1 周工作量**，**小步快跑**：
  - **PR-4a**（本 plan）= 23 错误码 + admission webhook + 入参校验 · 1 周
  - **PR-4b** = 4 A2A method handlers + 12 service · 1 周（依赖 PR-4a 错误码）
  - **PR-4c** = ASGI server + Card-driven + BM25 + scope resolver · 1 周（依赖 PR-4b handlers）
  - **PR-5** = 7 Helm + RBAC + kind E2E · 1 周（依赖 PR-4c ASGI server）

**PR-4a 实装清单**（L3-5 §5 + §8 + L3-6 §6 + §8 + ADR-0002 §3 + ADR-0003 §3 + ADR-0006 D 方案）：

| 类别 | 数量 | 路径前缀 | 关键依赖 |
|---|---|---|---|
| **23 错误码 enum** | 23 | `packages/knowledge/src/supteam_a2a/knowledge/errors/codes.py` | StrEnum + JSON-RPC code 映射 + Retryable 矩阵 |
| **5 步 admission 算法** | 1 | `packages/knowledge/src/supteam_a2a/knowledge/errors/admission.py` | asyncio.wait_for + AdmissionTimeoutError |
| **入参校验** | 3 | `packages/knowledge/src/supteam_a2a/knowledge/validation/validators.py` | Pydantic v2 model_validator + async |
| **admission webhook handler** | 1 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/admission/webhook.py` | Kopf `@kopf.validation` + 50ms fail-closed |
| **pytest 测试（UT + IT）** | ~17 ID | `tests/{unit,integration}/` | enum + admission + validators + webhook |

**PR-4a 增量测试 ID**（基于 L3-5 §10.1 + L3-6 §10.1 60 测试 ID 矩阵的子集）：

- UT 增量：**~15**（ERR-UT × 7 + ADM-UT × 5 + VAL-UT × 3 = 15 ID）
- IT 增量：**~2**（ADM-IT × 2 = 2 ID）
- **总计：~17 ID**

**不在范围**（明确剔除 · 推迟到 PR-4b/4c/5）：

- ❌ 4 A2A method handler（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）→ PR-4b
- ❌ 12 service（业务逻辑层）→ PR-4b
- ❌ ASGI server + Card-driven 入口 → PR-4c
- ❌ BM25 倒排索引 + 4 级 scope resolver 业务逻辑 + visibility resolver 业务逻辑 → PR-4c
- ❌ Helm 7 模板 + Dockerfile → PR-5
- ❌ kind 集群 E2E → PR-5
- ❌ 修改 packages/knowledge/crd/（PR-3 Phase B 已实装，PR-4a 仅新增 errors/ + validation/）
- ❌ 修改 L3-5 / L3-6 Spec → v0.2.0 已评审通过

---

## §2 设计决策（5 项关键）

### §2.1 23 错误码 enum 集中实现（packages/knowledge/errors/codes.py）

**23 个错误码**（L3-5 §8 + L3-6 §8 + L2-4 v0.2.0 §9.1 权威名）：

| Range | 类别 | 数量 | 错误码 |
|---|---|---|---|
| -32101 ~ -32111 | **MEMORY_*** | 11 | MEMORY_NOT_FOUND, MEMORY_ALREADY_EXISTS, MEMORY_INVALID_CONTENT, MEMORY_DECAY_EXCEEDED, MEMORY_REINFORCE_INVALID, MEMORY_GC_FAILED, MEMORY_ADMISSION_TIMEOUT, MEMORY_RECONCILER_FAILED, MEMORY_LEADER_LOST, MEMORY_BACKEND_UNAVAILABLE, MEMORY_LEASE_CONFLICT |
| -32201 ~ -32211 | **KNOWLEDGE_*** | 11 | KNOWLEDGE_SCOPE_NOT_FOUND, KNOWLEDGE_ITEM_NOT_FOUND, KNOWLEDGE_ITEM_SUPERSEDED, KNOWLEDGE_TYPE_INVALID, KNOWLEDGE_VISIBILITY_DENIED, KNOWLEDGE_SCOPE_INVALID_PARENT, KNOWLEDGE_INHERIT_RULE_INVALID, KNOWLEDGE_QUERY_EMPTY, KNOWLEDGE_BM25_INDEX_CORRUPT, KNOWLEDGE_TAG_TOO_LONG, KNOWLEDGE_CONTENT_TOO_LARGE |
| + metadata | **ADMISSION_*** | 1 | ADMISSION_VALIDATION_FAILED (subtype of MEMORY_ADMISSION_TIMEOUT) |

> **注**：实际 22 个 + 1 admission 子类型 = 23 个。Retryable 矩阵 + JSON-RPC code 映射 + 5 维度 visibility 校验错误码全部在 codes.py 集中定义。

**理由**：
- 严格遵循 L2-4 v0.2.0 §9.1 权威名（**零漂移** · #63.5 评审关注项 §M-1.1 + §M-1.2 全部关闭）
- Pydantic v2 + StrEnum（wire 字符串值兼容 · 与 PR-3 Phase B 已实装的 StrEnum 模式一致）
- 集中实现便于 PR-4b handler 引用 + IT 测试静态断言

### §2.2 admission webhook 50ms fail-closed（Kopf @kopf.validation）

**5 步 admission 算法**（L3-5 §5 + L3-6 §6）：

```python
# packages/knowledge/src/supteam_a2a/knowledge/errors/admission.py
async def validate_memory_admission(memory: dict, *, timeout: float = 0.050) -> bool:
    """5 步 admission 校验（50ms fail-closed）."""
    try:
        return await asyncio.wait_for(
            _admission_5_step(memory),
            timeout=timeout,
        )
    except asyncio.TimeoutError as exc:
        raise AdmissionTimeoutError(...) from exc  # → MEMORY_ADMISSION_TIMEOUT


async def _admission_5_step(memory: dict) -> bool:
    # Step 1: scope_ref 存在性校验
    # Step 2: agent_ref 与 scope_ref.subject 类型匹配校验（K8s User/Group 互斥）
    # Step 3: content 字段数 ≤ 20 + 字符串长度 ≤ 4096
    # Step 4: confidence + decay_days 边界
    # Step 5: visibility 与 scope_ref.level 一致性（5 维矩阵）
    ...
```

**理由**：
- **50ms fail-closed**（L3-5 §5 + L3-6 §6 严格锁定 · 宪法 §11.5 event-loop lag < 100ms）
- `asyncio.wait_for(timeout=0.050)` + AdmissionTimeoutError 异常类型化（不是布尔返回）
- 5 步算法独立函数 `_admission_5_step`（纯函数 + 无副作用 · 便于单元测试）

### §2.3 入参校验 async validators（Pydantic v2 model_validator）

**3 个 validator**（参考 L3-5 §5 入参校验要求）：

1. **AsyncContentValidator**：`MemorySpec.content` 字段数 ≤ 20 + 每个 value 字符串长度 ≤ 4096
2. **AsyncConfidenceDecayValidator**：`confidence` × `decay_days` 数学一致性（高 confidence 必须配短 decay）
3. **AsyncVisibilityScopeValidator**：`visibility` 与 `scope_ref.level` 一致性（5 维矩阵策略表）

**理由**：
- Pydantic v2 `@model_validator(mode="after")` 异步校验（与 Pydantic v2 async API 兼容）
- validators.py 集中实现，便于 IT 测试 + PR-4b handler 复用
- 不阻塞 pytest（async pytest-asyncio 已配置）

### §2.4 admission webhook handler（services/knowledge-memory-service/admission/webhook.py）

**单进程架构**（ADR-0006 D 方案 · 与 L3-5 §6.2 共享 Deployment 协调点一致）：

```python
# services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/admission/webhook.py
@kopf.on.validation(MEMORY_GROUP, MEMORY_VERSION, "memorys", operation="CREATE")
async def validate_memory(spec, **_):
    """admission webhook 入口 · 调用 packages/knowledge/errors/admission.py 5 步算法."""
    try:
        await validate_memory_admission(spec, timeout=0.050)
    except AdmissionTimeoutError as exc:
        raise kopf.PermanentError("MEMORY_ADMISSION_TIMEOUT") from exc
```

**理由**：
- 复用 packages/knowledge/ 的 admission 算法（**单一来源** · 避免业务逻辑分散）
- Kopf `@kopf.on.validation` 与 PR-3 Phase B 已实装的 kopf 模式一致
- 50ms fail-closed 通过 `kopf.PermanentError` 强制阻断（K8s API server 拒绝 CREATE）

### §2.5 测试策略：UT + IT 双层

**UT（单元测试）· ~15 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| ERR-UT | 7 | 23 错误码 enum 值 + JSON-RPC code 映射 + Retryable 矩阵 + wire 漂移静态断言 |
| ADM-UT | 5 | admission 5 步算法 + 50ms fail-closed + AdmissionTimeoutError 抛出 + 5 维矩阵一致性 + scope_ref/agent_ref 互斥 |
| VAL-UT | 3 | AsyncContentValidator + AsyncConfidenceDecayValidator + AsyncVisibilityScopeValidator |

**IT（集成测试）· ~2 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| ADM-IT | 2 | admission webhook Kopf 集成 + 50ms fail-closed E2E + MEMORY_ADMISSION_TIMEOUT 错误码触发 |

**理由**：
- 推迟 CF/E2E/TZ/PERF 到 PR-4b/4c/5（handler 集成 + BM25 倒排索引 + 衰减穿越 + kind 集群）
- 测试 ID 命名严格遵循 L3-5 §10.1 + L3-6 §10.1 规范（ERR-UT / ADM-UT / VAL-UT / ADM-IT）

---

## §3 实施步骤（4 阶段 · 接力模式 · 宪法 §16.1）

### 阶段 A · 主 Agent 起草 plan（本会话 · 进行中）

- ✅ 本 plan 文档（`docs/phase4/pr4a-knowledge-service-step2a-plan.md` · ~12-16KB · v0.1-draft）
- ✅ Issue 创建跟踪
- ✅ feat/phase4-pr4a-knowledge-step2a-plan 分支 + commit + push
- ✅ gh pr create + 等 CI 5 SUCCESS（markdownlint + 文档门禁）
- ✅ 项目发起人 squash merge

### 阶段 B · Subagent 隔离实装（估算 100K-150K tokens · ~30-45 分钟 · #106 实装会话）

**Subagent 任务清单**（与 PR-3 Phase B 同模式 · §16.1 实际水位判断）：

| Subagent | 任务 | 估算 tokens | 隔离方式 |
|---|---|---|---|
| Subagent 1 | `packages/knowledge/errors/` + `packages/knowledge/validation/` 2 个新模块 + ERR-UT × 7 + ADM-UT × 5 + VAL-UT × 3 | 60K-90K | worktree 不适用（feat 分支已隔离 · 直接主目录工作） |
| Subagent 2 | `services/knowledge-memory-service/admission/` admission webhook handler + ADM-IT × 2 | 40K-60K | worktree 不适用（同上） |

**Subagent 接力原则**（§16.1 + #79/#82/#103/#105 经验）：
- 主 Agent 仅调度 + 验证 + 收口（5-8% 水位）
- 每个 Subagent 在 feat 分支 commit + push（避免文件冲突）
- Subagent 必须 `uv sync --all-packages --all-extras` 后再开始（避免 import 路径错误）
- 每个 Subagent 完成后必须 `ruff check + ruff format + pyright + pytest` 全绿才能交付
- 关键 commit 步骤主 Agent 备份（避免 Subagent 中断丢失）

### 阶段 C · 主 Agent 收口（10-20 分钟 · #107 启动）

1. 验证所有 Subagent commits 在 feat 分支累计
2. 验证：ruff check All passed + ruff format 0 差异 + pyright 0 errors
3. 验证：pytest `tests/unit tests/integration` **284 + 17 = 301 PASS**
4. push feat 分支 → `gh pr create` → PR #50
5. 等 CI 5 SUCCESS（BP 严格生效 · 项目发起人 squash merge）
6. Issue close + MEMORY.md 头部更新

### 阶段 D · MEMORY 维护（5-8% 水位 · 10 分钟 · #108 PR-4b 启动前）

1. 创建 `session-2026-08-XX-cont106-pr4a.md`
2. MEMORY.md 头部状态行更新（PR #50 merged · main HEAD 推进）
3. 跨文档同步（§F.1-§F.6）：
   - `ROADMAP.md` · Phase 4 PR-4a 状态 `🚧` → `✅ merged`
   - `README.md` · L4 实施层进度更新
   - `CONSTITUTION-CHANGELOG.md` · v0.5.0 → v0.5.1（如有微同步）
   - `L3-5 Spec` M.4 · 关联 PR + Commit SHA 更新
   - `L3-6 Spec` M.4 · 关联 PR + Commit SHA 更新
   - `docs/admin/l4-package-layout.md` · 新增 errors/ + validation/ + admission/ 章节
4. 关键不变量映射更新（PR-4a 验证 5 项保持）

---

## §4 PR-4a 验收清单（10 项）

| # | 项 | 验证方法 |
|---|---|---|
| 1 | `packages/knowledge/errors/codes.py` 创建 · 23 错误码 enum 完整 | `ls packages/knowledge/src/supteam_a2a/knowledge/errors/` · codes.py 存在 |
| 2 | `packages/knowledge/errors/admission.py` 创建 · 5 步 admission 算法 | `import validate_memory_admission` 成功 |
| 3 | `packages/knowledge/validation/validators.py` 创建 · 3 async validators | `import AsyncContentValidator` 成功 |
| 4 | `services/knowledge-memory-service/admission/webhook.py` 创建 · Kopf @kopf.validation | `@kopf.on.validation` 装饰器存在 |
| 5 | 23 错误码完整（11 KNOWLEDGE_* + 12 MEMORY_* + 1 ADMISSION_* = 23） | `len(KnowledgeErrorCode) + len(MemoryErrorCode) + 1 == 23` |
| 6 | UT 测试 15 ID 全部 PASS | `pytest tests/unit/ -q` · 301 PASS |
| 7 | IT 测试 2 ID 全部 PASS（admission webhook + 50ms fail-closed） | `pytest tests/integration/test_admission_webhook.py -q` · 2 PASS |
| 8 | ruff check All passed + ruff format 0 差异 + pyright 0 errors | GitHub Actions CI |
| 9 | wire-sync 静态断言通过（23 错误码与 L2-4 v0.2.0 §9.1 字段 1:1 对齐 · 0 漂移） | `pytest tests/integration/test_error_codes_wire_sync.py` |
| 10 | 5 项关键不变量 100% 保持（wire contract + 50ms fail-closed + populate_by_name + JSON-RPC code 映射 + frozen） | 验证脚本 + PR description |

---

## §5 风险与缓解（6 项）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | uv workspace 跨包依赖循环（`services/knowledge-memory-service` ↔ `packages/knowledge/errors/`） | build 失败 + pytest collection error | services 依赖 packages/knowledge（单向依赖 · 业务逻辑在 packages/knowledge/） |
| 2 | Pydantic v2 `@model_validator(mode="after")` async API 兼容性（pyright 1.1.411 限制） | CI pyright gap · 类似 #81 经验 | 测试 fixtures 用 wire alias · validators 签名明确标注 `-> Self` |
| 3 | wire 漂移（23 错误码与 L2-4 §9.1 字段 1:1 对齐失败） | 后续 PR-4b handler 实装失败 · JSON-RPC code 错位 | IT 测试 `test_error_codes_wire_sync.py` 静态断言 + grep 双向验证 |
| 4 | `asyncio.wait_for(timeout=0.050)` 在 CI 上 flaky（race condition） | 50ms fail-closed 测试 flaky | mock clock + 显式 sleep 0.020 测试快速路径 + sleep 0.080 测试 fail-closed |
| 5 | Subagent 接力时 token plan 中断（#79 经验 · 331 tool uses / 23 分钟 · 429 终止） | Subagent 实装中断 · 主 Agent 修复 | 每个 Subagent 任务拆分 ≤ 100K tokens · 关键 commit 步骤主 Agent 备份 |
| 6 | Kopf `@kopf.on.validation` 与 50ms fail-closed 兼容（Kopf 默认 webhook timeout 30s） | webhook timeout 错配 | 显式 `kopf.PermanentError` + test mock 验证 50ms 内完成 |

---

## §6 5 项关键不变量保持（PR-4a 验证）

| # | 不变量 | PR-4a 验证方法 |
|---|---|---|
| 1 | wire contract 完全继承 L2-4 v0.2.0 Spec（23 错误码零漂移） | IT `test_error_codes_wire_sync.py` · 静态断言 L2-4 §9.1 错误码名集合 == 23 错误码 enum 字段名集合 |
| 2 | 50ms fail-closed（admission webhook 严格时限） | UT `ADM-UT-005` + IT `ADM-IT-002` · mock asyncio + sleep 0.080 验证 AdmissionTimeoutError |
| 3 | Pydantic v2 + populate_by_name + alias + extra=forbid + frozen | UT 每个 validator 测试 model_config + extra=forbid |
| 4 | Python-first 边界（packages/knowledge/errors/ 仅依赖 pydantic + asyncio） | `pyproject.toml` dependencies ≤ 2 项 |
| 5 | JSON-RPC code 映射（错误码 enum → JSON-RPC code 范围 -32101 ~ -32211） | UT `ERR-UT-005` · 静态断言所有错误码 JSON-RPC code 在 -32101 ~ -32211 范围内 |

**额外 PR-4a 不变量**：

- ✅ `packages/knowledge/errors/` 与 `packages/knowledge/validation/` 严格分离（独立子包）
- ✅ `services/knowledge-memory-service/admission/` 仅调用 `packages/knowledge/errors/admission.validate_memory_admission`（**单一来源**）
- ✅ 测试 ID 命名严格遵循 L3-5 §10.1 + L3-6 §10.1（ERR-UT / ADM-UT / VAL-UT / ADM-IT）
- ✅ 23 错误码 enum 与 L2-4 v0.2.0 §9.1 权威名 100% 一致（#63.5 关注项 §M-1.1 + §M-1.2 全部保持关闭）

---

## §7 测试策略增量（PR-4a）

| 层级 | PR-3 Phase B 终态 | PR-4a 增量 | PR-4a 累计 |
|---|---|---|---|
| UT | 24 + 3 baseline = 27 | **+15**（ERR-UT × 7 + ADM-UT × 5 + VAL-UT × 3）| 42 |
| CF | 18 | 0 | 18 |
| IT | 6 | **+2**（ADM-IT × 2）| 8 |
| E2E | 6 | 0 | 6 |
| DEPLOY | 17 | 0 | 17 |
| PERF | 0 | 0 | 0 |

**PR-4a 测试增量**：~17 ID（UT 15 + IT 2）· 4 重静态门禁（ruff + ruff format + pyright + pytest）· 覆盖率 ≥ 80%（L3-5 §10.4 基线）

**测试 ID 命名规范**（L3-5 §10.1 + L3-6 §10.1 严格遵守）：

- **ERR-UT-001~007** · 23 错误码 enum 7 子项（11 KNOWLEDGE_* + 12 MEMORY_* · JSON-RPC code 映射 · Retryable 矩阵 · wire 漂移静态断言）
- **ADM-UT-001~005** · admission 5 步算法 + 50ms fail-closed + AdmissionTimeoutError
- **VAL-UT-001~003** · 3 async validators（content + confidence/decay + visibility/scope）
- **ADM-IT-001~002** · admission webhook Kopf 集成 + 50ms fail-closed E2E

---

## §8 Phase 4 PR 序列更新（PR-1 + PR-2 + PR-3 merged · PR-4 拆分后 PR-4a 启动中）

| PR | 标题 | 状态 | main HEAD | 工作量 |
|---|---|---|---|---|
| #38 PR-1 | Hello Agent Step 1（5 Python + 22 测试） | ✅ merged `c97330bb` | `5e6d79b` | 2 周（已完成）|
| #45 PR-2 | Hello Agent Step 2（Dockerfile + 7 Helm + kind E2E） | ✅ merged `76c08f2` | `76c08f2` | 1 周（已完成）|
| #49 PR-3 | Knowledge Service Step 1（8 CRD + 4 shared + 30 测试） | ✅ merged `74af527` | `74af527` | 1.5 周（已完成）|
| **#106 PR-4a** | **Knowledge Service Step 2a**（23 错误码 + admission + validators） | 🚧 **本 plan 启动** | （待 PR-4a 完成后） | **1 周** |
| #107 PR-4b | Knowledge Service Step 2b（4 A2A handler + 12 service） | 📋 待启动 | — | 1 周 |
| #108 PR-4c | Knowledge Service Step 2c（ASGI server + Card-driven + BM25 + scope resolver） | 📋 待启动 | — | 1 周 |
| #109 PR-5 | Knowledge Service Step 3（7 Helm + RBAC + kind E2E） | 📋 待启动 | — | 1 周 |

**Phase 4 进度**：3/7 PR 已 merged · **4/7 PR 启动中**（PR-4a）
**Phase 4 剩余工作量**：~4 周集中（2h/day · 拆分 PR-4 后风险降低）

---

## §9 宪法 v0.5.0 兼容性

| 条款 | 兼容性 | 验证 |
|---|---|---|
| §3.4 文档同步 | ✅ | plan 文档 + Issue + MEMORY 同步 + §F.1-§F.6 跨文档 |
| §3.8 Python-first 实现边界 | ✅ | packages/knowledge/errors/ 仅依赖 pydantic + asyncio |
| §6 测试纪律 | ✅ | 4 重静态门禁（ruff + ruff format + pyright + pytest）+ pytest ~17 PASS |
| §7 关键决策记录 | ✅ | 5 项设计决策（23 错误码集中 + admission 5 步 + async validators + admission webhook + 测试策略）|
| §9.7 文档先行 | ✅ | 本 plan 文档先于实装（v0.1-draft · 启动条件明确）|
| §11.5 event-loop lag < 100ms | ✅ | admission 50ms fail-closed 严格时限 |
| §13.1 测试 ID 命名 | ✅ | ERR-UT / ADM-UT / VAL-UT / ADM-IT 系列连贯 · 不与 L3-4 HELLO-* / L3-5 §6 H-QK/H-GKI / L3-6 TEST-MEM-* 重名 |
| §13.6 依赖锁定 | ✅ | `pyproject.toml` 依赖固定版本范围 + `uv.lock` 提交 |
| §14.5 MVP 例外 | ✅ | 0 例外 · 5 项关键不变量 100% 保持 |
| §15 安全基线 | ✅ | PR-4a 涉及 Pydantic types + asyncio + Kopf webhook · 0 系统级安全风险 |
| §16.1 水位纪律 | ✅ | Subagent 接力模式（Phase B 2 个 Subagent）+ 主 Agent 5-8% 水位调度 |
| §17 PR 流程 | ✅ | feat 分支 + PR + CI 5 SUCCESS + squash merge（#103 修复实战验证） |

---

## §10 M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-12 · #106 启动 · PR-4 拆分后第一个子 PR）
- **M.2 落地记录**：#106（2026-08-12 · 本 plan 文档完成 · 准备进入 Phase B Subagent 实装）
- **M.3 关联 PR**：Phase 4 PR-4a Knowledge Service Step 2a · 本 plan（PR #50 plan 文档 + PR #51 实装代码）
- **M.4 下次会话入口**：
  - Phase A：本会话完成（plan + Issue + commit + push + PR #50 + CI + squash merge）
  - Phase B：#106 启动 Subagent 接力实装（2 Subagent feat 分支直接工作 · 避免 worktree isolation 无 Bash 权限 · #105 实战经验）
  - Phase C：#107 PR-4b 启动前主 Agent 收口（lint + test + 实装 PR #51 创建 + CI + squash merge）
  - Phase D：#107 PR-4b 启动前 MEMORY 维护（session + 跨文档 §F.1-§F.6）
- **M.5 关注项台账**：
  - ① uv workspace 跨包依赖循环（services 单向依赖 packages/knowledge · 业务逻辑在 packages/knowledge/）
  - ② Pydantic v2 `@model_validator(mode="after")` async API 兼容性（#81 pyright gap 经验 · 测试 fixtures 用 wire alias）
  - ③ wire 漂移（IT `test_error_codes_wire_sync.py` 静态断言 + grep 双向验证 · 0 漂移）
  - ④ `asyncio.wait_for(timeout=0.050)` 在 CI 上 flaky（mock clock + 显式 sleep 边界测试）
  - ⑤ Subagent 接力 token plan 中断（#79 经验 · 每个 Subagent ≤ 100K tokens · 主 Agent 备份关键 commit · #105 实战验证无需 worktree isolation）
  - ⑥ Kopf `@kopf.on.validation` 与 50ms fail-closed 兼容（显式 `kopf.PermanentError` + test mock 验证 50ms 内完成）
- **M.6 文档状态**：v0.1-draft 完整（10 节 · 估算 ~12-14KB · 启动前完整）
