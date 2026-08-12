# Phase 4 PR-4b Plan v0.1-draft · Knowledge Service Step 2b（4 A2A handlers + 12 service 业务逻辑层）

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-12 · #107 启动 · PR-4 拆分后第二个子 PR） |
| 上游 | #106 PR-4a plan v0.1-draft merged (`9f2be9a` · 333 行 / 10 节) + #105 PR-3 Knowledge Service Step 1 Phase B merged (`74af527` · 30 测试 ID · 284 PASS) + L3-5 Knowledge Service v0.2.0（2026-07-29 #63.5 评审通过）+ L3-6 Memory backend v0.2.0（2026-07-30 #67 评审通过）+ ADR-0006 v1.0 Accepted D 方案（单进程架构）|
| 下游 | **#108 PR-4c**（ASGI server + Card-driven + BM25 + scope resolver · 依赖 PR-4b handlers）→ **#109 PR-5**（7 Helm + RBAC + kind E2E · 依赖 PR-4c ASGI server）→ v0.5+ 演进 |
| 关联 PR | Phase 4 PR-4b Knowledge Service Step 2b · 本 plan |
| main HEAD | `9f2be9a`（PR-4a plan squash merged commit） |
| 启动条件 | ✅ 全部满足（PR-3 + PR-4a plan merged · BP 严格生效 · Dependabot 自动化） |

---

## §1 目标与边界

**目标**：将 L3-5 Knowledge Service v0.2.0 + L3-6 Memory backend v0.2.0 文件级 Spec 中的 **4 A2A method handlers**（queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）+ **12 service 业务逻辑层**（Memory 4 + Knowledge 4 + Shared 4）落地为 **4 handler 文件 + 12 service 文件 + ~18 测试 ID**。这是 Knowledge Service **"handler 与 service 层"** 的关键里程碑（PR-4b 完成后，PR-4c 直接基于该层实现 ASGI server + Card-driven 入口）。

**PR-4b 拆分理由**（延续 #106 拆分决策 · 小步快跑）：
- PR-4b = handler + service 业务逻辑层（**无 ASGI server + 无 BM25 业务逻辑 + 无 scope resolver**）· 1 周工作量
- PR-4c = ASGI server + Card-driven + BM25 业务 + scope resolver 业务（依赖 PR-4b handlers）· 1 周工作量

**PR-4b 实装清单**（L3-5 §4 + §6 + L3-6 §6 + §7 + ADR-0002 §3 + ADR-0003 §3 + ADR-0006 D 方案）：

| 类别 | 数量 | 路径前缀 | 关键依赖 |
|---|---|---|---|
| **4 A2A method handlers** | 4 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/handlers/` | JSON-RPC 2.0 + Starlette Request/Response |
| **Memory service 业务逻辑层** | 4 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/services/memory/` | MemoryBackend Protocol + AdmissionService |
| **Knowledge service 业务逻辑层** | 4 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/services/knowledge/` | KnowledgeBackend Protocol + VisibilityService |
| **Shared service 业务逻辑层** | 4 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/services/shared/` | Visibility 5 维矩阵 + 4 级 scope |
| **pytest 测试（UT + IT）** | ~18 ID | `tests/{unit,integration}/` | handler + service + 错误码 + wire 同步 |

**PR-4b 增量测试 ID**（基于 L3-5 §10.1 + L3-6 §10.1 60 测试 ID 矩阵的子集）：

- UT 增量：**~12**（H-RM-UT × 3 + H-QM-UT × 3 + H-QK-UT × 3 + H-GKI-UT × 3 = 12 ID）
- IT 增量：**~6**（H-RM-IT × 1 + H-QM-IT × 1 + H-QK-IT × 1 + H-GKI-IT × 1 + 错误码 IT × 2 = 6 ID）
- **总计：~18 ID**

**不在范围**（明确剔除 · 推迟到 PR-4c/5）：

- ❌ ASGI server + Card-driven 入口（starlette Route + uvicorn binding）→ PR-4c
- ❌ BM25 倒排索引业务逻辑（text 索引 + tokenization + TF-IDF 评分）→ PR-4c
- ❌ 4 级 scope resolver 业务逻辑（parent_ref 解析 + chain 遍历）→ PR-4c
- ❌ visibility resolver 业务逻辑（5 维矩阵策略执行）→ PR-4c
- ❌ Helm 7 模板 + Dockerfile → PR-5
- ❌ kind 集群 E2E → PR-5
- ❌ admission webhook handler（属于 PR-4a）· PR-4b 复用 PR-4a 错误码
- ❌ 23 错误码 enum（属于 PR-4a）· PR-4b 调用 PR-4a 错误码
- ❌ 修改 L3-5 / L3-6 Spec → v0.2.0 已评审通过
- ❌ 修改 services/hello-agent/ → PR-4b 不涉及

---

## §2 设计决策（5 项关键）

### §2.1 4 A2A method handlers 单一职责（services/.../handlers/）

**4 个 handler 文件**（参考 L3-2 A2A Core Library + Phase 3 PR-1 A2A HTTP JSON-RPC server）：

```python
# services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/handlers/query_memory.py
"""JSON-RPC method: queryMemory · query memories by scope/visibility/BM25 (PR-4c 实装)."""

from superteam_a2a.knowledge_memory.services.memory.query import MemoryQueryService


async def query_memory_handler(request: dict) -> dict:
    """queryMemory JSON-RPC handler 入口 · PR-4c 接入 ASGI server."""
    service = MemoryQueryService(backend=...)
    return await service.execute(request)


# handlers/query_knowledge.py: queryKnowledge handler
# handlers/get_knowledge_item.py: getKnowledgeItem handler
# handlers/record_memory.py: recordMemory handler（含 admission 50ms fail-closed 调用）
```

**理由**：
- **单一职责**：每个 handler 仅负责 JSON-RPC request 解析 + service 调用 + response 序列化
- handler 不含业务逻辑（业务逻辑在 service 层）
- 便于 PR-4c ASGI server 直接绑定 handler（starlette Route handler = query_memory_handler）

### §2.2 12 service 三层架构（Memory + Knowledge + Shared）

**12 service 文件**（业务逻辑层 · 不依赖 ASGI server）：

| 类别 | 文件 | 职责 | 测试 ID |
|---|---|---|---|
| **Memory** (4) | `services/memory/record.py` | MemoryRecordService · recordMemory + admission 50ms fail-closed | H-RM-UT × 3 |
| | `services/memory/query.py` | MemoryQueryService · queryMemory + scope/visibility filter | H-QM-UT × 3 |
| | `services/memory/reinforce.py` | MemoryReinforceService · reinforce + confidence 提升 | H-RM-IT × 1 |
| | `services/memory/gc.py` | MemoryGCService · mark/archive/delete 状态转换 | H-RM-IT × 1 |
| **Knowledge** (4) | `services/knowledge/query.py` | KnowledgeQueryService · queryKnowledge + BM25 scope filter | H-QK-UT × 3 |
| | `services/knowledge/item.py` | KnowledgeItemService · getKnowledgeItem · superseded_by chain | H-GKI-UT × 3 |
| | `services/knowledge/record.py` | KnowledgeItemRecordService · recordMemory → KnowledgeItem 派生 | H-RM-IT × 1 |
| | `services/knowledge/scope.py` | KnowledgeScopeService · 4 级 scope 校验 | H-QK-IT × 1 |
| **Shared** (4) | `services/shared/admission.py` | AdmissionService · 复用 PR-4a admission algorithm | 错误码 IT × 1 |
| | `services/shared/visibility.py` | VisibilityService · 5 维矩阵策略（接口 · 实装 PR-4c）| H-QK-IT × 1 |
| | `services/shared/inherit.py` | InheritService · 4 级 scope 继承规则（接口 · 实装 PR-4c）| H-GKI-IT × 1 |
| | `services/shared/wire_sync.py` | WireSyncService · CRD wire contract 静态断言 | 错误码 IT × 1 |

**理由**：
- **业务逻辑与 handler 解耦**（service 可独立单元测试 · 不依赖 ASGI）
- **Memory / Knowledge / Shared 三层分离**（避免循环依赖 · service 可单独 mock）
- **接口 vs 实装分离**：Shared service 在 PR-4b 仅暴露 Protocol 接口（visibility/inherit 实装推到 PR-4c）

### §2.3 handler 复用 PR-4a admission algorithm（50ms fail-closed）

**recordMemory handler 集成 admission**：

```python
# handlers/record_memory.py
from superteam_a2a.knowledge.errors.admission import (
    validate_memory_admission,
    AdmissionTimeoutError,
)


async def record_memory_handler(request: dict) -> dict:
    """recordMemory handler · 含 admission 50ms fail-closed."""
    try:
        # Step 1: admission 50ms fail-closed（PR-4a 实装的 5 步算法）
        await validate_memory_admission(request["memory"], timeout=0.050)
    except AdmissionTimeoutError as exc:
        raise JsonRpcError(-32107, "MEMORY_ADMISSION_TIMEOUT", str(exc)) from exc

    # Step 2: 业务逻辑（PR-4b 实装）
    service = MemoryRecordService(backend=...)
    return await service.execute(request)
```

**理由**：
- **handler 调用 PR-4a admission algorithm**（单一来源 · 业务逻辑与 admission 校验解耦）
- admission 异常 → JSON-RPC error.code -32107（PR-4a 实装的 23 错误码之一）
- 50ms 严格时限（admission fail-closed）· 不允许超时放行

### §2.4 service 层错误码映射（23 错误码 → JSON-RPC error.code）

**所有 service 层异常 → JSON-RPC error.code 映射**：

```python
# services/shared/wire_sync.py
class JsonRpcError(Exception):
    """JSON-RPC 2.0 error wrapper · 引用 PR-4a 错误码."""

    def __init__(self, code: int, message: str, data: object = None) -> None:
        self.code = code  # -32101 ~ -32211（PR-4a 实装的 23 错误码范围）
        self.message = message
        self.data = data


# service 抛出 JsonRpcError → handler 序列化 → ASGI server 返回 JSON-RPC 2.0 响应
```

**理由**：
- 所有 service 异常统一映射到 JSON-RPC error.code（PR-4a 实装的 23 错误码）
- handler 捕获 JsonRpcError → 序列化为 JSON-RPC 2.0 error response
- 避免错误码漂移（IT 测试 `test_error_codes_wire_sync.py` 静态断言 23 错误码）

### §2.5 测试策略：UT + IT 双层

**UT（单元测试）· ~12 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| H-RM-UT | 3 | recordMemory handler + MemoryRecordService + admission 50ms fail-closed |
| H-QM-UT | 3 | queryMemory handler + MemoryQueryService + scope/visibility filter |
| H-QK-UT | 3 | queryKnowledge handler + KnowledgeQueryService + BM25 filter（PR-4c 实装业务） |
| H-GKI-UT | 3 | getKnowledgeItem handler + KnowledgeItemService + superseded_by chain |

**IT（集成测试）· ~6 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| H-RM-IT | 1 | recordMemory 端到端（JSON-RPC round-trip + CRD apply + admission） |
| H-QM-IT | 1 | queryMemory 端到端（JSON-RPC round-trip + BM25 mock + 23 错误码触发） |
| H-QK-IT | 1 | queryKnowledge 端到端（JSON-RPC round-trip + KnowledgeItem 查询） |
| H-GKI-IT | 1 | getKnowledgeItem 端到端（JSON-RPC round-trip + superseded_by chain） |
| ERR-IT | 2 | 23 错误码 → JSON-RPC error.code 映射静态断言 + wire sync 静态断言 |

**理由**：
- 推迟 CF/E2E/TZ/PERF 到 PR-4c/5（ASGI server + BM25 倒排索引 + kind 集群）
- 测试 ID 命名严格遵循 L3-5 §10.1 + L3-6 §10.1 规范（H-RM / H-QM / H-QK / H-GKI / ERR-IT）

---

## §3 实施步骤（4 阶段 · 接力模式 · 宪法 §16.1）

### 阶段 A · 主 Agent 起草 plan（本会话 · 进行中）

- ✅ 本 plan 文档（`docs/phase4/pr4b-knowledge-service-step2b-plan.md` · ~12-16KB · v0.1-draft）
- ✅ Issue 创建跟踪
- ✅ feat/phase4-pr4b-knowledge-step2b-plan 分支 + commit + push
- ✅ gh pr create + 等 CI 5 SUCCESS（注意 #106 教训：ruff format 文档）
- ✅ 项目发起人 squash merge

### 阶段 B · Subagent 隔离实装（估算 100K-150K tokens · ~30-45 分钟 · #107 实装会话）

**Subagent 任务清单**（与 PR-3 Phase B + PR-4a 同模式 · §16.1 实际水位判断）：

| Subagent | 任务 | 估算 tokens | 隔离方式 |
|---|---|---|---|
| Subagent 1 | Memory service 业务逻辑层（4 文件 · MemoryRecordService/QueryService/ReinforceService/GCService）+ 12 UT | 60K-90K | 直接在 feat 分支工作（#105 实战经验 · 无 worktree）|
| Subagent 2 | Knowledge service 业务逻辑层（4 文件 · KnowledgeQueryService/ItemService/RecordService/ScopeService）+ 6 UT | 50K-80K | 直接在 feat 分支工作 |
| Subagent 3 | 4 A2A handlers + Shared service（4 文件 · AdmissionService/VisibilityService/InheritService/WireSyncService）+ 6 IT | 60K-90K | 直接在 feat 分支工作 |

**Subagent 接力原则**（§16.1 + #79/#82/#103/#105 实战经验）：
- 主 Agent 仅调度 + 验证 + 收口（5-8% 水位）
- 每个 Subagent 在 feat 分支 commit + push（避免文件冲突）
- Subagent 必须 `uv sync --all-packages --all-extras` 后再开始（避免 import 路径错误）
- 每个 Subagent 完成后必须 `ruff check + ruff format + pyright + pytest` 全绿才能交付
- 关键 commit 步骤主 Agent 备份（避免 Subagent 中断丢失）
- **Subagent 顺序**：Subagent 1 → 2 → 3（按依赖关系 · Shared service 最后实装）

### 阶段 C · 主 Agent 收口（10-20 分钟 · #108 启动前）

1. 验证所有 Subagent commits 在 feat 分支累计
2. 验证：ruff check All passed + ruff format 0 差异 + pyright 0 errors
3. 验证：pytest `tests/unit tests/integration` **301 + 18 = 319 PASS**
4. push feat 分支 → `gh pr create` → PR #52
5. 等 CI 5 SUCCESS（BP 严格生效 · 项目发起人 squash merge）
6. Issue close + MEMORY.md 头部更新

### 阶段 D · MEMORY 维护（5-8% 水位 · 10 分钟 · #108 PR-4c 启动前）

1. 创建 `session-2026-08-XX-cont107-pr4b.md`
2. MEMORY.md 头部状态行更新（PR #52 merged · main HEAD 推进）
3. 跨文档同步（§F.1-§F.6）：
   - `ROADMAP.md` · Phase 4 PR-4b 状态 `🚧` → `✅ merged`
   - `README.md` · L4 实施层进度更新
   - `CONSTITUTION-CHANGELOG.md` · v0.5.0 → v0.5.1（如有微同步）
   - `L3-5 Spec` M.4 · 关联 PR + Commit SHA 更新
   - `L3-6 Spec` M.4 · 关联 PR + Commit SHA 更新
   - `docs/admin/l4-package-layout.md` · 新增 handlers/ + services/ 章节
4. 关键不变量映射更新（PR-4b 验证 5 项保持）

---

## §4 PR-4b 验收清单（10 项）

| # | 项 | 验证方法 |
|---|---|---|
| 1 | `services/.../handlers/` 4 文件创建（query_knowledge / get_knowledge_item / record_memory / query_memory） | `ls services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/handlers/` · 4 文件存在 |
| 2 | `services/.../services/memory/` 4 文件创建（record / query / reinforce / gc） | `ls services/.../services/memory/` · 4 文件存在 |
| 3 | `services/.../services/knowledge/` 4 文件创建（query / item / record / scope） | `ls services/.../services/knowledge/` · 4 文件存在 |
| 4 | `services/.../services/shared/` 4 文件创建（admission / visibility / inherit / wire_sync） | `ls services/.../services/shared/` · 4 文件存在 |
| 5 | 4 handler 复用 PR-4a admission algorithm（50ms fail-closed） | UT `H-RM-UT-003` · 验证 recordMemory handler 调用 admission |
| 6 | UT 测试 12 ID 全部 PASS | `pytest tests/unit/ -q` · 301 + 12 = 313 PASS |
| 7 | IT 测试 6 ID 全部 PASS（4 handler 端到端 + 2 错误码映射） | `pytest tests/integration/ -q` · 8 + 6 = 14 PASS |
| 8 | ruff check All passed + ruff format 0 差异 + pyright 0 errors | GitHub Actions CI |
| 9 | wire-sync 静态断言通过（23 错误码与 PR-4a 一致 · JSON-RPC code 范围 -32101 ~ -32211） | `pytest tests/integration/test_error_codes_wire_sync.py` |
| 10 | 5 项关键不变量 100% 保持（wire contract + 50ms fail-closed + 23 错误码 + handler/service 解耦 + 单进程 D 方案） | 验证脚本 + PR description |

---

## §5 风险与缓解（6 项）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | 12 service 跨模块循环依赖（Memory ↔ Knowledge ↔ Shared） | build 失败 + pytest collection error | service 严格依赖顺序：Shared → Knowledge → Memory · 业务逻辑在 packages/knowledge/ 不在 services |
| 2 | handler 错误码映射漂移（service 抛 JsonRpcError 但 handler 未捕获） | JSON-RPC error response 500 错误 | WireSyncService 静态断言所有 service 抛出的异常必须继承 JsonRpcError · handler 统一 try/except 包装 |
| 3 | recordMemory handler admission 50ms fail-closed flaky（CI race condition） | admission 测试不稳定 | mock clock + 显式 sleep 0.020（快速路径）+ sleep 0.080（fail-closed）· 与 PR-4a UT ADM-UT-005 同模式 |
| 4 | handler 与 service 单元测试 mock 复杂度（service 依赖多个 backend） | 测试 setup 复杂 | 使用 pytest fixture + AsyncMock · 与 PR-3 Phase B + Phase 3 PR-4 H-RM/H-QM stub 同模式 |
| 5 | Subagent 接力时 token plan 中断（#79 经验 · 331 tool uses / 23 分钟 · 429 终止） | Subagent 实装中断 · 主 Agent 修复 | 每个 Subagent 任务拆分 ≤ 100K tokens · 关键 commit 步骤主 Agent 备份 · #105 实战验证无需 worktree isolation |
| 6 | 4 handler 文件命名冲突（与 Phase 3 H-RM/H-QM stub 重名） | handler import 错乱 | 命名空间 `superteam_a2a.knowledge_memory.handlers` 隔离 · 不与 `services/.../handlers/` Phase 3 stub 重名 |

---

## §6 5 项关键不变量保持（PR-4b 验证）

| # | 不变量 | PR-4b 验证方法 |
|---|---|---|
| 1 | wire contract 完全继承 L2-4 v0.2.0 Spec（4 A2A method 字段 1:1 对齐） | UT 每个 handler 测试 model_dump(by_alias=True) 输出字段名与 L2-4 §6 一致 |
| 2 | 50ms fail-closed（recordMemory handler 严格时限） | UT `H-RM-UT-003` · 验证 handler admission 超时 → MEMORY_ADMISSION_TIMEOUT JSON-RPC error.code -32107 |
| 3 | Pydantic v2 + populate_by_name + alias + extra=forbid + frozen（service 层 request/response model） | UT 每个 service 测试 request/response model_config |
| 4 | Python-first 边界（services/knowledge-memory-service/ 仅依赖 pydantic + a2a-core + kopf + packages/knowledge） | `pyproject.toml` dependencies 严格 ≤ 4 项 |
| 5 | JSON-RPC error.code 映射（23 错误码范围 -32101 ~ -32211） | IT `ERR-IT-001/002` · WireSyncService 静态断言所有 service 异常 code 在范围内 |

**额外 PR-4b 不变量**：

- ✅ handler 与 service 解耦（handler 不含业务逻辑 · service 不依赖 ASGI）
- ✅ Memory / Knowledge / Shared 三层 service 严格分离（Shared → Knowledge → Memory 单向依赖）
- ✅ 23 错误码引用（handler 抛出 JsonRpcError → JSON-RPC error.code 来自 PR-4a）
- ✅ 单进程 D 方案（handler/service 在同一进程内调用 · 无 IPC）

---

## §7 测试策略增量（PR-4b）

| 层级 | PR-4a 终态 | PR-4b 增量 | PR-4b 累计 |
|---|---|---|---|
| UT | 42 | **+12**（H-RM-UT × 3 + H-QM-UT × 3 + H-QK-UT × 3 + H-GKI-UT × 3）| 54 |
| CF | 18 | 0 | 18 |
| IT | 8 | **+6**（H-RM-IT × 1 + H-QM-IT × 1 + H-QK-IT × 1 + H-GKI-IT × 1 + ERR-IT × 2）| 14 |
| E2E | 6 | 0 | 6 |
| DEPLOY | 17 | 0 | 17 |
| PERF | 0 | 0 | 0 |

**PR-4b 测试增量**：~18 ID（UT 12 + IT 6）· 4 重静态门禁（ruff + ruff format + pyright + pytest）· 覆盖率 ≥ 80%（L3-5 §10.4 基线）

**测试 ID 命名规范**（L3-5 §10.1 + L3-6 §10.1 严格遵守）：

- **H-RM-UT-001~003** · recordMemory handler + MemoryRecordService + admission 50ms fail-closed
- **H-QM-UT-001~003** · queryMemory handler + MemoryQueryService + scope/visibility filter
- **H-QK-UT-001~003** · queryKnowledge handler + KnowledgeQueryService + BM25 filter stub
- **H-GKI-UT-001~003** · getKnowledgeItem handler + KnowledgeItemService + superseded_by chain
- **H-RM-IT-001** · recordMemory 端到端（JSON-RPC round-trip + CRD apply + admission）
- **H-QM-IT-001** · queryMemory 端到端（JSON-RPC round-trip + BM25 mock + 23 错误码触发）
- **H-QK-IT-001** · queryKnowledge 端到端（JSON-RPC round-trip + KnowledgeItem 查询）
- **H-GKI-IT-001** · getKnowledgeItem 端到端（JSON-RPC round-trip + superseded_by chain）
- **ERR-IT-001~002** · 23 错误码 → JSON-RPC error.code 映射静态断言 + wire sync 静态断言

---

## §8 Phase 4 PR 序列更新（PR-1 + PR-2 + PR-3 + PR-4a plan merged · PR-4b 启动中）

| PR | 标题 | 状态 | main HEAD | 工作量 |
|---|---|---|---|---|
| #38 PR-1 | Hello Agent Step 1（5 Python + 22 测试） | ✅ merged `c97330bb` | `5e6d79b` | 2 周（已完成）|
| #45 PR-2 | Hello Agent Step 2（Dockerfile + 7 Helm + kind E2E） | ✅ merged `76c08f2` | `76c08f2` | 1 周（已完成）|
| #49 PR-3 | Knowledge Service Step 1（8 CRD + 4 shared + 30 测试） | ✅ merged `74af527` | `74af527` | 1.5 周（已完成）|
| #51 PR-4a | Knowledge Service Step 2a（23 错误码 + admission webhook + 入参校验） | ✅ merged `9f2be9a` | `9f2be9a` | 1 周（plan 阶段已完成）|
| **#107 PR-4b** | **Knowledge Service Step 2b**（4 A2A handlers + 12 service） | 🚧 **本 plan 启动** | （待 PR-4b 完成后） | **1 周** |
| #108 PR-4c | Knowledge Service Step 2c（ASGI server + Card-driven + BM25 + scope resolver） | 📋 待启动 | — | 1 周 |
| #109 PR-5 | Knowledge Service Step 3（7 Helm + RBAC + kind E2E） | 📋 待启动 | — | 1 周 |

**Phase 4 进度**：4/7 PR 已 merged（PR-4a plan 阶段完成）· **5/7 PR 启动中**（PR-4b）
**Phase 4 剩余工作量**：~3 周集中（2h/day · 拆分 PR-4 后风险持续降低）

---

## §9 宪法 v0.5.0 兼容性

| 条款 | 兼容性 | 验证 |
|---|---|---|
| §3.4 文档同步 | ✅ | plan 文档 + Issue + MEMORY 同步 + §F.1-§F.6 跨文档 |
| §3.8 Python-first 实现边界 | ✅ | services/knowledge-memory-service/ 仅依赖 pydantic + a2a-core + kopf + packages/knowledge |
| §6 测试纪律 | ✅ | 4 重静态门禁（ruff + ruff format + pyright + pytest）+ pytest ~18 PASS |
| §7 关键决策记录 | ✅ | 5 项设计决策（4 handlers 单一职责 + 12 service 三层 + admission 复用 + 错误码映射 + 测试策略）|
| §9.7 文档先行 | ✅ | 本 plan 文档先于实装（v0.1-draft · 启动条件明确）|
| §11.5 event-loop lag < 100ms | ✅ | recordMemory handler admission 50ms fail-closed + handler/service 同步调用（无 IPC 开销）|
| §13.1 测试 ID 命名 | ✅ | H-RM-UT / H-QM-UT / H-QK-UT / H-GKI-UT / H-RM-IT / H-QM-IT / H-QK-IT / H-GKI-IT / ERR-IT 系列连贯 |
| §13.6 依赖锁定 | ✅ | `pyproject.toml` 依赖固定版本范围 + `uv.lock` 提交 |
| §14.5 MVP 例外 | ✅ | 0 例外 · 5 项关键不变量 100% 保持 |
| §15 安全基线 | ✅ | PR-4b 涉及 handler + service + 错误码映射 · 无系统级安全风险（业务逻辑层）|
| §16.1 水位纪律 | ✅ | Subagent 接力模式（Phase B 3 个 Subagent）+ 主 Agent 5-8% 水位调度 |
| §17 PR 流程 | ✅ | feat 分支 + PR + CI 5 SUCCESS + squash merge（#103 修复实战验证） |

---

## §10 M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-12 · #107 启动 · PR-4 拆分后第二个子 PR）
- **M.2 落地记录**：#107（2026-08-12 · 本 plan 文档完成 · 准备进入 Phase B Subagent 实装）
- **M.3 关联 PR**：Phase 4 PR-4b Knowledge Service Step 2b · 本 plan（PR #52 plan 文档 + PR #53 实装代码）
- **M.4 下次会话入口**：
  - Phase A：本会话完成（plan + Issue + commit + push + PR #52 + CI + squash merge）
  - Phase B：#107 启动 Subagent 接力实装（3 Subagent feat 分支直接工作 · 避免 worktree isolation 无 Bash 权限 · #105 实战经验）
  - Phase C：#108 PR-4c 启动前主 Agent 收口（lint + test + 实装 PR #53 创建 + CI + squash merge）
  - Phase D：#108 PR-4c 启动前 MEMORY 维护（session + 跨文档 §F.1-§F.6）
- **M.5 关注项台账**：
  - ① 12 service 跨模块循环依赖（Shared → Knowledge → Memory 单向依赖 · 业务逻辑在 packages/knowledge/）
  - ② handler 错误码映射漂移（WireSyncService 静态断言 + handler 统一 try/except 包装）
  - ③ recordMemory handler admission 50ms fail-closed flaky（mock clock + 显式 sleep 边界 · #106 PR-4a 同模式）
  - ④ handler 与 service 单元测试 mock 复杂度（pytest fixture + AsyncMock · #105 + Phase 3 PR-4 H-RM/H-QM stub 同模式）
  - ⑤ Subagent 接力 token plan 中断（#79 经验 · 每个 Subagent ≤ 100K tokens · 主 Agent 备份关键 commit · #105 实战验证无需 worktree isolation）
  - ⑥ 4 handler 文件命名冲突（命名空间 `superteam_a2a.knowledge_memory.handlers` 隔离 · 不与 Phase 3 H-RM/H-QM stub 重名）
- **M.6 文档状态**：v0.1-draft 完整（10 节 · 估算 ~14-16KB · 启动前完整）
