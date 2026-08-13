# Phase 4 PR-4a Plan v0.2-draft · Knowledge Service Step 2a（11 KNOWLEDGE_* 错误码 + admission webhook @kopf.validation + 5 步算法 + 3 async validators）

> **2026-08-13 #111 修订要点**：与 #105 PR-3 已实装的现状对齐。
> ① 12 MEMORY_* 错误码已实装于 `services/.../backend/errors.py`（PR-3 Phase B）→ **删除** PR-4a 范围中的 12 MEMORY_*
> ② AdmissionValidatorImpl 最小集已实装（schema 校验 + 50ms timeout + `MEMORY_*` 异常透传）→ **保留** 该实装，PR-4a 升级为完整 L3-5 §5.2 5 步 + §5.3 4 步算法
> ③ PR-4a 实装 **11 KNOWLEDGE_* 错误码 enum**（L3-5 §8 权威表 -32008 ~ -32018）
> ④ PR-4a 实装 **`@kopf.validation` webhook handler**（`validate_knowledge_item` + `validate_memory` · L3-5 §5.1）
> ⑤ PR-4a 实装 **3 async Pydantic v2 model_validator**（content + confidence/decay + visibility/scope）
> ⑥ baseline **284 → 325 PASS**（#105 PR-3 Phase B +41 测试 ID）

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.2-draft**（2026-08-13 · #111 启动 · v0.1-draft → v0.2-draft 修订） |
| 上游 | #105 PR-3 Knowledge Service Step 1 Phase B merged (`74af527` · 30 测试 ID · 325 PASS) + #104 PR-3 plan merged (`ce76eaa`) + L3-5 Knowledge Service v0.2.0（2026-07-29 #63.5 评审通过 · 10 维度全 PASS）+ L3-6 Memory backend v0.2.0（2026-07-30 #67 评审通过）+ ADR-0006 v1.0 Accepted D 方案（单进程架构）|
| 下游 | **#107 PR-4b**（4 A2A handler + 12 service · 依赖 PR-4a KNOWLEDGE_* 错误码 + admission webhook）→ **#108 PR-4c**（ASGI server + Card-driven + BM25 + scope resolver · 依赖 PR-4b handlers）→ **#109 PR-5**（7 Helm + RBAC + kind E2E · 依赖 PR-4c ASGI server）→ v0.5+ 演进 |
| 关联 PR | Phase 4 PR-4a Knowledge Service Step 2a · 本 plan |
| main HEAD | `406aa5c`（#110 PR-5 plan v0.1-draft merged · PR-4 拆分 4 plan 全部 merged） |
| 启动条件 | ✅ 全部满足（PR-3 merged · BP 严格生效 · Dependabot 自动化 · ⑭⑮⑯⑰ 全部解决 · #111 修订与现状对齐）|

---

## §1 目标与边界

**目标（修订 v0.2-draft）**：将 L3-5 Knowledge Service v0.2.0 文件级 Spec 中的 **11 KNOWLEDGE_* 错误码 enum**（-32008 ~ -32018，L3-5 §8.1 权威表）+ **`@kopf.validation` admission webhook handler**（L3-5 §5.1 `validate_knowledge_item` + `validate_memory`）+ **5 步 admission 算法扩展**（L3-5 §5.2 content_hash 计算 + Memory K8s 查询）+ **3 async Pydantic v2 model_validator**（content + confidence/decay + visibility/scope）+ **4 步 scope_ref 父子循环检测**（L3-5 §5.3 BFS + max_depth=8）落地为 **3 个新模块 + 1 个 admission webhook handler + ~15 测试 ID**。

**为什么拆分 PR-4a**（按用户决策 2026-08-12 #106）：
- PR-4 原始范围 = 12 service + 4 A2A handler + 23 错误码 + ASGI server + Card-driven + admission webhook + BM25 + 4 级 scope resolver · **2 周工作量过大**
- 拆分后每个子 PR **1 周工作量**，**小步快跑**：
  - **PR-4a**（本 plan v0.2-draft）= **11 KNOWLEDGE_* + admission webhook + 5 步算法 + 3 validators** · 1 周
  - **PR-4b** = 4 A2A method handlers + 12 service · 1 周（依赖 PR-4a 错误码）
  - **PR-4c** = ASGI server + Card-driven + BM25 + scope resolver · 1 周（依赖 PR-4b handlers）
  - **PR-5** = 7 Helm + RBAC + kind E2E · 1 周（依赖 PR-4c ASGI server）

**PR-4a v0.2-draft 实装清单**（L3-5 §5 + §8 + L3-6 §6 + ADR-0002 §3 + ADR-0003 §3 + ADR-0006 D 方案）：

| 类别 | 数量 | 路径前缀 | 关键依赖 |
|---|---|---|---|
| **11 KNOWLEDGE_* 错误码 enum**（新增） | 11 | `packages/knowledge/src/supteam_a2a/knowledge/errors/codes.py` | IntEnum + JSON-RPC code -32008~-32018 + Retryable 矩阵 |
| **admission 5 步算法扩展**（升级 AdmissionValidatorImpl） | 1 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/handlers/admission_validator.py` | 已有最小集 · 升级为 content_hash + Memory K8s 查询 + 4 步 scope_ref 检测 |
| **入参校验**（新增） | 3 | `packages/knowledge/src/supteam_a2a/knowledge/validation/validators.py` | Pydantic v2 `@model_validator(mode="after")` + async |
| **admission webhook handler**（新增） | 2 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/admission/webhook.py` | `@kopf.validation` 装饰器 + 50ms fail-closed 装饰器 |
| **pytest 测试（UT + IT）** | ~15 ID | `tests/{unit,integration}/` | enum + admission + validators + webhook |

**已实装不重做（与 #105 PR-3 现状对齐）**：

- ✅ 12 MEMORY_* 错误码（`services/.../backend/errors.py` line 1-116）· 不在 PR-4a 范围
- ✅ AdmissionValidatorImpl 最小集（`services/.../handlers/admission_validator.py` line 1-91）· PR-4a **升级而非重写**
- ✅ `packages/knowledge/src/supteam_a2a/knowledge/__init__.py` regular package（与 L3-5 §5 期望一致）
- ✅ services/.../handlers/ kopf handler 模式（memory_handler.py 已用 `@kopf.on.create`）

**PR-4a v0.2-draft 增量测试 ID**（基于 L3-5 §5 + §8 + §10.1 测试矩阵）：

- UT 增量：**~12**（KNOW-UT × 5 + ADM-UT × 4 + VAL-UT × 3 = 12 ID）
- IT 增量：**~3**（ADM-IT × 3 = 3 ID）
- **总计：~15 ID**
- **baseline 325 → 340 PASS**（325 + 15 = 340）

**测试 ID 命名规范**：
- **KNOW-UT-001~005** · 11 KNOWLEDGE_* 错误码 enum 5 子项（JSON-RPC code 映射 · Retryable 矩阵 · wire 漂移静态断言）
- **ADM-UT-001~004** · admission 5 步算法（content_hash）+ 4 步 scope_ref 检测 + 50ms fail-closed 装饰器 + 错误码触发
- **VAL-UT-001~003** · 3 async validators（content + confidence/decay + visibility/scope）
- **ADM-IT-001~003** · admission webhook Kopf 集成 + 50ms fail-closed E2E + MEMORY_ADMISSION_TIMEOUT 触发

**不在范围**（明确剔除 · 推迟到 PR-4b/4c/5）：

- ❌ 4 A2A method handler（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）→ PR-4b
- ❌ 12 service（业务逻辑层）→ PR-4b
- ❌ ASGI server + Card-driven 入口 → PR-4c
- ❌ BM25 倒排索引 + 4 级 scope resolver 业务逻辑 + visibility resolver 业务逻辑 → PR-4c
- ❌ Helm 7 模板 + Dockerfile → PR-5
- ❌ kind 集群 E2E → PR-5
- ❌ 修改 packages/knowledge/crd/（PR-3 Phase B 已实装，PR-4a 仅新增 errors/ + validation/）
- ❌ 修改 L3-5 / L3-6 Spec → v0.2.0 已评审通过
- ❌ 重做 12 MEMORY_* 错误码（已实装于 backend/errors.py · #105 PR-3 Phase B）

---

## §2 设计决策（5 项关键 · v0.2-draft 修订）

### §2.1 11 KNOWLEDGE_* 错误码 enum 集中实现（packages/knowledge/errors/codes.py · 新增）

**11 个 KNOWLEDGE_* 错误码**（L3-5 §8.1 line 1808-1822 权威表 + L3-5 §5.1 line 1395 + L3-5 §5.2 line 1480）：

| wire 名（name） | JSON-RPC code | HTTP status | 含义 |
|---|---|---|---|
| `KNOWLEDGE_SCOPE_NOT_FOUND` | -32008 | 404 | Knowledge scope {scope_ref_name} was not found |
| `KNOWLEDGE_QUERY_TOO_LONG` | -32009 | 400 | Knowledge query length {actual} exceeds 512 |
| `KNOWLEDGE_INVALID_TYPE` | -32010 | 400 | Knowledge typeFilter {type} is not a valid enum value |
| `KNOWLEDGE_INTERNAL_ERROR` | -32011 | 500 | Knowledge service internal error |
| `KNOWLEDGE_ITEM_NOT_FOUND` | -32012 | 404 | Knowledge item {name} was not found |
| `KNOWLEDGE_VERSION_NOT_FOUND` | -32013 | 404 | Knowledge item {name} version {version} was not found |
| `KNOWLEDGE_FORBIDDEN` | -32014 | 403 | Knowledge {name} is not accessible to agent {agent_id} |
| `KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY` | -32015 | 400 | Knowledge {name} visibility=public-readable requires scope.level=industry |
| `KNOWLEDGE_AGENT_PRIVATE_V0_5_PLUS` | -32016 | 400 | Knowledge {name} visibility=agent-private is only supported in v0.5+ |
| `KNOWLEDGE_OWNER_KIND_FORBIDDEN` | -32017 | 400 | Knowledge {name} ownerRef.kind={kind} is forbidden (use Memory) |
| `KNOWLEDGE_ADMISSION_TIMEOUT` | -32018 | 503 | Knowledge admission exceeded 50ms |

**理由**：
- 严格遵循 L3-5 §8.1 权威名（**零漂移** · 与 L3-5 §5.1 / §5.2 / §5.3 引用一致）
- **IntEnum** 而非 StrEnum（与 PR-3 backend/errors.py IntEnum 模式一致 + JSON-RPC code 数值直接作为 enum value）
- 集中实现便于 PR-4b handler 引用 + IT 测试静态断言
- wire-sync 静态断言测试 `test_knowledge_error_codes_wire_sync.py` 校验 L3-5 §8.1 字段名集合 == codes.py enum 字段名集合（**零漂移**）

### §2.2 admission 5 步算法扩展（升级 AdmissionValidatorImpl · services/.../handlers/admission_validator.py）

**已有 AdmissionValidatorImpl 最小集**（#105 PR-3 Phase B · line 1-91）：
- 仅做 schema 校验（content keys ≤ 20 + decay_days ≤ 3650）
- 50ms timeout 通过 `asyncio.wait_for(timeout=timeout)` + `MemoryBackendError(MEMORY_ADMISSION_TIMEOUT)` 抛出
- 完整 L3-5 §5.2 5 步 + L3-6 §6.4 4 步算法尚未实装（需 K8s client）

**PR-4a v0.2-draft 升级**（L3-5 §5.2 line 1445-1491 + §5.3 line 1499+）：

```python
# services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/handlers/admission_validator.py
async def validate_ki_memory_mutex(ki: KnowledgeItem) -> AdmissionDecision:
    """L3-5 §5.2 5 步算法扩展（与 Phase 1 最小集共存 · #105 已实装）。"""
    # 1. 计算 content_hash（sha256 前 16 hex chars · 64 bit · wire 名一致）
    content_hash = hashlib.sha256(ki.spec.content.encode("utf-8")).hexdigest()[:16]

    # 2. K8s API 查询同 content_hash Memory（label selector · memory.superteam-a2a.io/v1alpha1）
    memories = await k8s.list_namespaced_custom_object(
        group="memory.superteam-a2a.io",
        version="v1alpha1",
        namespace=ki.spec.scope_ref.namespace,
        plural="memories",
        label_selector=f"superteam-a2a.io/contentHash={content_hash}",
    )

    # 3. 不存在 → 允许（短路）
    if not memories["items"]:
        return AdmissionDecision(allowed=True)

    # 4. 存在 + 同 agent_ref → supersede 允许
    for mem_raw in memories["items"]:
        if mem_raw["spec"].get("subject") == ki.metadata.labels.get("superteam-a2a.io/agent"):
            return AdmissionDecision(allowed=True, reason="same agent supersede")

    # 5. 存在 + 不同 agent → 拒绝（KNOWLEDGE_ITEM_NOT_FOUND -32012）
    raise KnowledgeAdmissionDecision(False, "KNOWLEDGE_ITEM_NOT_FOUND")
```

**理由**：
- **不重写** AdmissionValidatorImpl（#105 PR-3 已 merged · 兼容 PR-3 已写 8 个测试 `test_admission_validator.py`）
- 5 步算法作为 `KnowledgeMemoryMutexValidator` 新方法（与 AdmissionValidatorImpl 并列）
- K8s client 通过 `kopf.admission` 装饰器上下文获取（无需新增依赖）

### §2.3 入参校验 3 async validators（Pydantic v2 · packages/knowledge/validation/validators.py · 新增）

**3 个 async validator**（基于 L3-5 §5.1 入参校验要求）：

1. **AsyncContentValidator**：`MemorySpec.content` 字段数 ≤ 20 + 每个 value 字符串长度 ≤ 4096（与 AdmissionValidatorImpl 现有规则一致）
2. **AsyncConfidenceDecayValidator**：`confidence` × `decay_days` 数学一致性（confidence ≥ 0.9 时 decay_days ≤ 365；< 0.9 时 ≤ 3650）
3. **AsyncVisibilityScopeValidator**：`visibility` 与 `scope_ref.level` 一致性（`visibility=public-readable` → `scope.level=industry`；`visibility=agent-private` → `scope.level=agent` · L3-5 §8.1 KNOWLEDGE_PUBLIC_REQUIRES_INDUSTRY -32015 校验依据）

**理由**：
- Pydantic v2 `@model_validator(mode="after")` 异步校验（与 Pydantic v2 async API 兼容）
- validators.py 集中实现（packages/knowledge/validation/ · 与 errors/ 同级），便于 IT 测试 + PR-4b handler 复用
- 不阻塞 pytest（async pytest-asyncio 已配置 + #81 pyright gap 经验已应用 wire alias 修复）

### §2.4 admission webhook handler（services/knowledge-memory-service/admission/webhook.py · 新增）

**L3-5 §5.1 line 1382-1406 webhook 入口**（与 AdmissionValidatorImpl 并列）：

```python
# services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/admission/webhook.py
"""L3-5 §5.1 @kopf.validation admission webhook 入口（与 backend handler 同进程）。"""

from functools import wraps
import asyncio
import kopf

from superteam_a2a.knowledge_memory.handlers.admission_validator import (
    AdmissionValidatorImpl,
)


def fail_closed_50ms(coro):
    """L3-5 §5.1 50ms fail-closed 装饰器（admission 超时 → AdmissionDecision(allowed=False)）。"""

    @wraps(coro)
    async def wrapper(*args, **kwargs):
        try:
            return await asyncio.wait_for(coro(*args, **kwargs), timeout=0.050)
        except asyncio.TimeoutError:
            return AdmissionDecision(allowed=False, reason="admission timeout (>50ms)")

    return wrapper


@kopf.validation("knowledgeitem.create", "knowledgeitem.update")
@fail_closed_50ms
async def validate_knowledge_item(spec, **kwargs):
    """L3-5 §5.1 line 1382 KnowledgeItem admission webhook（互斥校验 + scope 校验）。"""
    ...


@kopf.validation("memory.create", "memory.update")
@fail_closed_50ms
async def validate_memory(spec, **kwargs):
    """L3-5 §5.1 line 1399 Memory admission webhook（互斥校验 + decay_days 边界）。"""
    ...
```

**理由**：
- 复用 AdmissionValidatorImpl（**不重写**）+ 调用 K8s client（headless kopf 注入）
- Kopf `@kopf.validation` 与 PR-3 Phase B 已实装的 `@kopf.on.create` 装饰器模式一致
- 50ms fail-closed 通过 `fail_closed_50ms` 装饰器（独立可复用）
- 错误码抛出用 `kopf.AdmissionError(KNOWLEDGE_ITEM_NOT_FOUND)`（L3-5 §5.1 line 1395）

### §2.5 测试策略：UT + IT 双层（v0.2-draft 修订）

**UT（单元测试）· ~12 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| KNOW-UT | 5 | 11 KNOWLEDGE_* 错误码 enum 值 + JSON-RPC code 映射 + Retryable 矩阵 + wire-sync 静态断言 + IntEnum 类型 |
| ADM-UT | 4 | 5 步算法（content_hash 计算 + Memory K8s 查询 + 同 agent supersede + 不同 agent 拒绝）+ 4 步 scope_ref 检测 + 50ms fail-closed 装饰器 + KNOWLEDGE_ITEM_NOT_FOUND 触发 |
| VAL-UT | 3 | AsyncContentValidator + AsyncConfidenceDecayValidator + AsyncVisibilityScopeValidator |

**IT（集成测试）· ~3 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| ADM-IT | 3 | admission webhook Kopf 集成 + 50ms fail-closed E2E + MEMORY_ADMISSION_TIMEOUT 错误码触发 |

**理由**：
- 推迟 CF/E2E/TZ/PERF 到 PR-4b/4c/5（handler 集成 + BM25 倒排索引 + 衰减穿越 + kind 集群）
- 测试 ID 命名严格遵循 L3-5 §10.1 + L3-6 §10.1 规范（KNOW-UT / ADM-UT / VAL-UT / ADM-IT）
- 不与已有测试 ID 重名（避开 L3-5 §5.1 line 1428-1437 ADM-UT × 5 + ADM-IT × 3 重叠 · PR-4a 新增 ADM-UT-006~009 + ADM-IT-004~006）

---

## §3 实施步骤（4 阶段 · 接力模式 · 宪法 §16.1）

### 阶段 A · 主 Agent 起草 plan（本会话 · 进行中）

- ✅ 本 plan 文档（`docs/phase4/pr4a-knowledge-service-step2a-plan.md` · ~12-16KB · v0.1-draft）
- ✅ Issue 创建跟踪
- ✅ feat/phase4-pr4a-knowledge-step2a-plan 分支 + commit + push
- ✅ gh pr create + 等 CI 5 SUCCESS（markdownlint + 文档门禁）
- ✅ 项目发起人 squash merge

### 阶段 B · Subagent 隔离实装（估算 100K-150K tokens · ~30-45 分钟 · #111 实装会话）

**Subagent 任务清单**（与 PR-3 Phase B 同模式 · §16.1 实际水位判断 · v0.2-draft 修订）：

| Subagent | 任务 | 估算 tokens | 隔离方式 |
|---|---|---|---|
| **Subagent 1** | `packages/knowledge/errors/codes.py` 11 KNOWLEDGE_* enum + `packages/knowledge/validation/validators.py` 3 async validators + KNOW-UT × 5 + VAL-UT × 3 + wire-sync × 1 = **~9 UT** | 60K-90K | worktree 不适用（feat 分支已隔离 · 直接主目录工作） |
| **Subagent 2** | `services/knowledge-memory-service/admission/webhook.py`（2 `@kopf.validation` + fail_closed_50ms 装饰器）+ 升级 `services/knowledge-memory-service/handlers/admission_validator.py` 5 步算法扩展 + ADM-UT × 4 + ADM-IT × 3 = **~7 测试** | 40K-60K | worktree 不适用（同上） |

**Subagent 接力原则**（§16.1 + #79/#82/#103/#105 实战经验）：
- 主 Agent 仅调度 + 验证 + 收口（5-8% 水位）
- 每个 Subagent 在 feat 分支 commit + push（避免文件冲突）
- Subagent 必须 `python -m uv sync --all-packages --all-extras` 后再开始（避免 import 路径错误）
- 每个 Subagent 完成后必须 `ruff check + ruff format + pyright + pytest` 全绿才能交付
- 关键 commit 步骤主 Agent 备份（避免 Subagent 中断丢失）
- **Subagent 1 必须等待 Subagent 2 完成后才能 push**（避免 webhook 文件未创建时 admission_validator.py import 错误）

### 阶段 C · 主 Agent 收口（10-20 分钟 · #112 PR-4b 启动前）

1. 验证所有 Subagent commits 在 feat 分支累计
2. 验证：ruff check All passed + ruff format 0 差异 + pyright 0 errors
3. 验证：pytest `tests/unit tests/integration` **325 + 15 = 340 PASS**（v0.2-draft 修订：284 + 17 = 301 → 325 + 15 = 340）
4. push feat 分支 → `gh pr create` → PR（v0.2-draft 修订：PR #50 → 实际 PR 编号）
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

## §4 PR-4a v0.2-draft 验收清单（10 项 · 与现状对齐）

| # | 项 | 验证方法 |
|---|---|---|
| 1 | `packages/knowledge/src/supteam_a2a/knowledge/errors/codes.py` 创建 · 11 KNOWLEDGE_* enum 完整 | `ls packages/knowledge/src/supteam_a2a/knowledge/errors/` · codes.py 存在 |
| 2 | `packages/knowledge/src/supteam_a2a/knowledge/validation/validators.py` 创建 · 3 async validators | `import AsyncContentValidator/AsyncConfidenceDecayValidator/AsyncVisibilityScopeValidator` 成功 |
| 3 | `services/knowledge-memory-service/admission/webhook.py` 创建 · `@kopf.validation` × 2 + `fail_closed_50ms` 装饰器 | `@kopf.validation` 装饰器存在 · 50ms fail-closed UT 验证 |
| 4 | `services/knowledge-memory-service/handlers/admission_validator.py` 升级 · 5 步算法扩展（content_hash + K8s 查询） | `import validate_ki_memory_mutex` 成功 · 5 步 UT 覆盖 |
| 5 | 11 KNOWLEDGE_* 错误码完整（-32008 ~ -32018） | `len(KnowledgeErrorCode) == 11` + wire-sync 静态断言 |
| 6 | UT 测试 12 ID 全部 PASS（KNOW-UT × 5 + ADM-UT × 4 + VAL-UT × 3） | `pytest tests/unit/ -q` · **340 PASS** |
| 7 | IT 测试 3 ID 全部 PASS（ADM-IT × 3 admission webhook Kopf 集成） | `pytest tests/integration/test_admission_webhook.py -q` · 3 PASS |
| 8 | ruff check All passed + ruff format 0 差异 + pyright 0 errors | GitHub Actions CI |
| 9 | wire-sync 静态断言通过（11 KNOWLEDGE_* 与 L3-5 §8.1 字段 1:1 对齐 · 0 漂移） | `pytest tests/integration/test_knowledge_error_codes_wire_sync.py` |
| 10 | 5 项关键不变量 100% 保持（wire contract + 50ms fail-closed + 5 步算法 + JSON-RPC code 映射 + 不重做 12 MEMORY_*） | 验证脚本 + PR description |

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

## §6 5 项关键不变量保持（PR-4a v0.2-draft 验证）

| # | 不变量 | PR-4a v0.2-draft 验证方法 |
|---|---|---|
| 1 | wire contract 完全继承 L3-5 §8.1 Spec（11 KNOWLEDGE_* 错误码零漂移） | IT `test_knowledge_error_codes_wire_sync.py` · 静态断言 L3-5 §8.1 line 1808-1822 错误码名集合 == `KnowledgeErrorCode` enum 字段名集合 |
| 2 | 50ms fail-closed（admission webhook 严格时限） | UT `ADM-UT-004`（装饰器超时测试）+ IT `ADM-IT-002` · mock asyncio + sleep 0.080 验证 fail-closed |
| 3 | Pydantic v2 + populate_by_name + alias + extra=forbid + frozen | UT 每个 validator 测试 model_config + extra=forbid |
| 4 | Python-first 边界（packages/knowledge/errors/ + validation/ 仅依赖 pydantic + asyncio） | `packages/knowledge/pyproject.toml` dependencies ≤ 2 项（已锁定 `pydantic>=2.10,<3`） |
| 5 | JSON-RPC code 映射（11 KNOWLEDGE_* enum → JSON-RPC code 范围 -32008 ~ -32018） | UT `KNOW-UT-002` · 静态断言所有错误码 JSON-RPC code 在 -32008 ~ -32018 范围内 |

**额外 PR-4a v0.2-draft 不变量**：

- ✅ `packages/knowledge/errors/` 与 `packages/knowledge/validation/` 严格分离（独立子包）
- ✅ `services/knowledge-memory-service/admission/webhook.py` 仅调用 `AdmissionValidatorImpl` + `KnowledgeMemoryMutexValidator`（**不重写** #105 PR-3 已实装的 `AdmissionValidatorImpl`）
- ✅ 测试 ID 命名严格遵循 L3-5 §10.1 + L3-6 §10.1（KNOW-UT / ADM-UT / VAL-UT / ADM-IT）+ 避开 L3-5 §5.1 line 1428-1437 已有的 `ADM-UT-001~005`（PR-4a 新增 `ADM-UT-006~009`）
- ✅ **不重做** 12 MEMORY_* 错误码（已实装于 `services/.../backend/errors.py` · #105 PR-3 Phase B）
- ✅ **不重写** `AdmissionValidatorImpl` 最小集（与 #105 PR-3 已 merged 测试兼容）

---

## §7 测试策略增量（PR-4a v0.2-draft 修订）

| 层级 | PR-3 Phase B 终态 | PR-4a v0.2-draft 增量 | PR-4a v0.2-draft 累计 |
|---|---|---|---|
| UT | 24 + 3 baseline = 27 | **+12**（KNOW-UT × 5 + ADM-UT × 4 + VAL-UT × 3）| 39 |
| CF | 18 | 0 | 18 |
| IT | 6 | **+3**（ADM-IT × 3）| 9 |
| E2E | 6 | 0 | 6 |
| DEPLOY | 17 | 0 | 17 |
| PERF | 0 | 0 | 0 |

**PR-4a v0.2-draft 测试增量**：~15 ID（UT 12 + IT 3）· 4 重静态门禁（ruff + ruff format + pyright + pytest）· 覆盖率 ≥ 80%（L3-5 §10.4 基线）

**测试 ID 命名规范**（L3-5 §10.1 + L3-6 §10.1 严格遵守 · 避开 L3-5 §5.1 line 1428-1437 已有的 `ADM-UT-001~005` + `ADM-IT-001~003`）：

- **KNOW-UT-001~005** · 11 KNOWLEDGE_* 错误码 enum 5 子项（IntEnum 值 + JSON-RPC code 映射 + Retryable 矩阵 + wire-sync 静态断言 + `code_name` 字符串相等）
- **ADM-UT-006~009**（避开 L3-5 §5.1 line 1429-1433 已有的 `ADM-UT-001~005`）· admission 5 步算法（content_hash 计算）+ 4 步 scope_ref 检测 + 50ms fail-closed 装饰器 + KNOWLEDGE_ITEM_NOT_FOUND 错误码触发
- **VAL-UT-001~003** · 3 async validators（content + confidence/decay + visibility/scope）
- **ADM-IT-004~006**（避开 L3-5 §5.1 line 1434-1437 已有的 `ADM-IT-001~003`）· admission webhook Kopf 集成 + 50ms fail-closed E2E + MEMORY_ADMISSION_TIMEOUT 错误码触发

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

## §10 M.1-M.6 元数据（v0.2-draft 修订）

- **M.1 版本**：v0.2-draft（2026-08-13 · #111 启动 · v0.1-draft → v0.2-draft 修订 · 与 #105 PR-3 已实装对齐）
- **M.2 落地记录**：#106（2026-08-12 · v0.1-draft plan 文档完成）+ #111（2026-08-13 · v0.2-draft 修订完成 · 准备进入 Phase B Subagent 实装）
- **M.3 关联 PR**：Phase 4 PR-4a Knowledge Service Step 2a · 本 plan（PR #51 plan 文档 v0.2-draft + PR #52 实装代码 v0.2-draft）
- **M.4 下次会话入口**：
  - Phase A：#111 完成（v0.2-draft plan 修订 + Issue + commit + push + 等 CI 5 SUCCESS + squash merge）
  - Phase B：#112 启动 Subagent 接力实装（Subagent 1 = codes.py + validators.py + KNOW-UT × 5 + VAL-UT × 3 · Subagent 2 = webhook.py + admission_validator.py 升级 + ADM-UT × 4 + ADM-IT × 3 · feat 分支直接工作 · 避免 worktree isolation 无 Bash 权限 · #105 实战经验）
  - Phase C：#113 PR-4b 启动前主 Agent 收口（ruff + ruff format + pyright + pytest 340 PASS · push feat 分支 · gh pr create → 实装 PR #52 → CI 5 SUCCESS · 项目发起人 squash merge）
  - Phase D：#113 PR-4b 启动前 MEMORY 维护（session-2026-08-13-cont111-pr4a-impl.md + §F.1-§F.6 跨文档同步）
- **M.5 关注项台账**：
  - ① uv workspace 跨包依赖循环（services 单向依赖 packages/knowledge · 业务逻辑在 packages/knowledge/）
  - ② Pydantic v2 `@model_validator(mode="after")` async API 兼容性（#81 pyright gap 经验 · 测试 fixtures 用 wire alias）
  - ③ wire 漂移（IT `test_knowledge_error_codes_wire_sync.py` 静态断言 + grep 双向验证 · 0 漂移）
  - ④ `asyncio.wait_for(timeout=0.050)` 在 CI 上 flaky（mock clock + 显式 sleep 边界测试 · `fail_closed_50ms` 装饰器隔离）
  - ⑤ Subagent 接力 token plan 中断（#79 经验 · 每个 Subagent ≤ 100K tokens · 主 Agent 备份关键 commit · #105 实战验证无需 worktree isolation）
  - ⑥ Kopf `@kopf.validation` 与 50ms fail-closed 兼容（显式 `fail_closed_50ms` 装饰器 + `kopf.AdmissionError` 抛出 · test mock 验证 50ms 内完成）
  - ⑦ **新增**：避开已有 `ADM-UT-001~005` + `ADM-IT-001~003` 测试 ID（L3-5 §5.1 line 1428-1437 已定义 · PR-4a 新增 `ADM-UT-006~009` + `ADM-IT-004~006`）
  - ⑧ **新增**：不重做 12 MEMORY_* 错误码（#105 PR-3 backend/errors.py 已 merged · 重复实装破坏兼容性）
  - ⑨ **新增**：不重写 AdmissionValidatorImpl 最小集（#105 PR-3 已 merged · 8 个 test_admission_validator.py 测试已 PASS · 升级而非重写）
- **M.6 文档状态**：v0.2-draft 完整（10 节 · 估算 ~14-16KB · 启动前完整 · 与 #105 PR-3 已实装对齐）
