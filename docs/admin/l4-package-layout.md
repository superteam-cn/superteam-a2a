# L4 包布局（uv workspace）

> 📅 Last updated: **2026-08-14**（#113 Phase 4 PR-4b 完整实装收口）
> 维护：项目发起人
> 依据：ADR-0005 §13.1 + 宪法 v0.6.0 §3.8 + ADR-0006 v1.0 Accepted D 方案

## uv workspace members（2026-08-14 · Phase 4 PR-4b 后）

```
packages/
├── a2a-core/           # A2A Protocol types + extended 4 methods (L3-2 v0.2.0)
├── adapter-sdk/        # FrameworkAdapter Protocol + AgentCardConverter (L3-3 v0.2.0)
├── operator/           # Kopf handlers + 4 CRDs + MemoryReconciler (L3-1 v0.2.0)
├── knowledge/          # 8 CRD types Pydantic v2 (L3-5 v0.2.0) · Phase 4 PR-3 Step 1 ✅ + PR-4a Phase B (errors/codes.py + validation/validators.py) ✅
└── shared-visibility/  # 4 shared modules (与 L3-6 共享 visibility) · Phase 4 PR-3 Step 1 ✅

services/
├── knowledge-memory-service/  # L3-5 + L3-6 单进程服务 (ADR-0006 D 方案)
│   ├── src/supteam_a2a/knowledge_memory/
│   │   ├── backend/             # MemoryBackend Protocol + 5 implementations (PR-3 Phase B)
│   │   ├── api/                 # MemoryBackendInProcessService + 5 步契约 (Phase 1 Step 4)
│   │   ├── reconciler/          # MemoryReconciler 60s kopf.timer (Phase 1 Step 3)
│   │   ├── observability/       # 10 Memory 业务指标 (Phase 3 PR-3)
│   │   ├── admission/           # @kopf.on.validate webhook (PR-4a Phase B)
│   │   ├── handlers/            # kopf handlers (PR-4a) + JSON-RPC handlers (PR-4b Phase B) ✅
│   │   ├── services/            # 12 service 业务逻辑层 (PR-4b Phase A) ✅
│   │   │   ├── memory/          # MemoryRecordService/QueryService/ReinforceService/GCService
│   │   │   ├── knowledge/       # KnowledgeQueryService/ItemService/RecordService/ScopeService (Protocol stubs)
│   │   │   └── shared/          # AdmissionService/VisibilityService/InheritService/WireSyncService
│   │   └── main.py              # kopf 4 decorator 装配
└── hello-agent/               # Phase 4 PR-1 Hello Agent Step 1 + PR-2 Dockerfile + 8 Helm

agents/
└── hello/              # Phase 4 PR-1 Hello Agent 入口
```

## 依赖矩阵

| 包 | dependencies |
|---|---|
| `superteam-a2a-a2a-core` | `pydantic>=2.10,<3` |
| `superteam-a2a-adapter-sdk` | `pydantic>=2.10,<3` + `superteam-a2a-a2a-core` |
| `superteam-a2a-operator` | `pydantic>=2.10,<3` + `kubernetes-asyncio>=36.1.0,<37` + `kopf>=1.37,<2` |
| `superteam-a2a-knowledge` | `pydantic>=2.10,<3`（Python-first 边界 · 仅 1 项） |
| `superteam-a2a-shared-visibility` | `pydantic>=2.10,<3` + `superteam-a2a-knowledge`（仅 re-export） |

## Phase 4 PR-3 新增包（#49 squash merged @ `74af527` · 2026-08-12）

### `packages/knowledge/`（8 CRD types + 5 辅助类型）

- `knowledgescope.py` (KnowledgeScope + Spec + Status + SubjectKind + SubjectReference + KnowledgeVisibility)
- `knowledgeitem.py` (KnowledgeItem + Spec + Status + KnowledgeType + ItemPhase + DecayState)
- `memory_schema.py` (Memory + Spec + Status + MemoryPhase + GCState · 避免命名冲突)
- `scope_reference.py` (ScopeReference frozen)
- `item_reference.py` (ItemReference frozen)
- `inherit_rules.py` (InheritRules frozen)
- `scope_level.py` (ScopeLevel StrEnum · 4 类)
- `scope_phase.py` (ScopePhase StrEnum · 状态机)

**关键约束**：
- PEP 420 namespace package 模式（**无 superteam_a2a/__init__.py**）
- Pydantic v2 + populate_by_name + alias + extra=forbid + frozen
- 17 UT 测试 ID：KS-CRD-UT × 5 + KI-CRD-UT × 7 + MEM-CRD-UT × 5

### `packages/shared-visibility/`（4 shared modules）

- `scope_resolver.py` (ScopeResolver Protocol + ScopeError exception)
- `visibility_matrix.py` (VisibilityMatrix Protocol + 5 维策略表占位 + KnowledgeVisibility re-export)
- `knowledge_type.py` (KnowledgeType StrEnum re-export)
- `scope_inherit.py` (ScopeInherit Protocol + InheritRules re-export)

**关键约束**：
- PEP 420 namespace package 模式（superteam_a2a 顶层 namespace · shared 子包 regular）
- **仅 Protocol 接口 + re-export**（**不实现业务逻辑**——推迟到 PR-4）
- 7 UT 测试 ID：SV-SCOPE-UT × 2 + SV-VIS-UT × 2 + SV-KT-UT × 1 + SV-INH-UT × 2

## Phase 4 PR-4a 新增模块（#58 squash merged @ `834ced8` · 2026-08-13）

### `packages/knowledge/errors/`（11 KNOWLEDGE_* enum + 2 异常类 + helper）

- `codes.py` (KnowledgeErrorCode 11 enum + KnowledgeError 异常类 + REASON_HTTP_MAP + RETRYABLE_CODES + is_retryable + knowledge_error_data)
- `__init__.py` (re-export)

**关键约束**：
- 错误码范围 **-32008 ~ -32018**（与 L3-5 §8.1 line 1808-1822 零漂移）
- HTTP 状态映射 403/404/500/503 完整覆盖
- Retryable 矩阵（`KNOWLEDGE_INTERNAL_ERROR` + `KNOWLEDGE_ADMISSION_TIMEOUT`）

### `packages/knowledge/validation/`（3 Pydantic v2 validators）

- `validators.py` (ContentValidator + ConfidenceDecayValidator + VisibilityScopeValidator)

**关键约束**：
- @model_validator(mode="after") 同步校验（Pydantic v2 不支持 async model_validator）
- extra="forbid" + populate_by_name=True

### `services/knowledge-memory-service/.../admission/`（@kopf.on.validate webhook）

- `webhook.py` (fail_closed_50ms 装饰器 + @kopf.on.validate("knowledgeitem.create/update") + @kopf.on.validate("memory.create/update"))

### `services/knowledge-memory-service/.../handlers/` 新增

- `admission_validator.py` (AdmissionValidatorImpl + KnowledgeMemoryMutexValidator 5 步算法 + 4 步 scope_ref 父子循环检测)

## Phase 4 PR-4b 新增模块（#59 squash merged @ `f9b733f` · 2026-08-14 · 437 PASS）

### `services/knowledge-memory-service/.../services/`（12 service 业务逻辑层）

**Memory (4 文件 · 完整业务逻辑)**：

- `memory/record.py` (MemoryRecordService · 委托 InProcessService.record_memory_async · 5 步契约 + 50ms fail-closed 单一来源)
- `memory/query.py` (MemoryQueryService · 委托 InProcessService.query_memory_async · scope 预检 + confidence 后置过滤)
- `memory/reinforce.py` (MemoryReinforceService · backend.patch_status CAS + MEMORY_REINFORCE_TOTAL Counter)
- `memory/gc.py` (MemoryGCService · 状态机转换 patch_status + delete + MEMORY_GC_CLEANED_TOTAL Counter)

**Knowledge (4 文件 · Protocol stub · BM25 推 PR-4c)**：

- `knowledge/query.py` (KnowledgeQueryService · 返回空列表)
- `knowledge/item.py` (KnowledgeItemService · superseded_by chain stub)
- `knowledge/record.py` (KnowledgeItemRecordService · KnowledgeItem 派生 stub)
- `knowledge/scope.py` (KnowledgeScopeService · 复用 VisibilityScopeValidator + 4 级 scope 解析 stub)

**Shared (4 文件 · Admission 实装 + Visibility/Inherit Protocol + WireSync 实装)**：

- `shared/admission.py` (AdmissionService · 委托 AdmissionValidatorImpl · 50ms fail-closed)
- `shared/visibility.py` (VisibilityService · Protocol stub · 5 维矩阵策略推 PR-4c)
- `shared/inherit.py` (InheritService · Protocol stub · 4 级 scope 继承推 PR-4c)
- `shared/wire_sync.py` (WireSyncService · **完整实装** · assert_wire_sync_compliant + assert_json_rpc_code_range + to_json_rpc_error_code)

### `services/knowledge-memory-service/.../handlers/` 新增 4 JSON-RPC handler

- `record_memory.py` (含 admission 50ms fail-closed 调用)
- `query_memory.py` (scope/visibility filter)
- `query_knowledge.py` (BM25 scope filter stub)
- `get_knowledge_item.py` (superseded_by chain stub)

**关键约束**：
- handler 与 service 解耦（thin wrapper + DI · mock service 即可替换 · LSP 验证）
- ASGI server PR-4c 直接绑定 handler = record_memory_handler 等
- 12 UT 测试 ID（H-RM/QM/QK/GKI-UT-001~003）+ 6 IT 测试 ID（H-RM/QM/QK/GKI-IT-001 + ERR-IT-001/002）+ 补充测试 = 49 新增

## Python-first 边界（§3.8）

- 每个 workspace member `pyproject.toml` `requires-python = ">=3.12"`
- `packages/knowledge/` 仅依赖 `pydantic>=2.10,<3`（不依赖 operator / a2a-core）
- `packages/shared-visibility/` 仅依赖 `pydantic + packages/knowledge`（不反向 import 业务逻辑）
- 禁止跨包 `__init__.py` 创建（PEP 420 namespace 兼容性）

## 验证命令

```bash
# uv sync 全部 workspace members
python -m uv sync --all-packages --all-extras

# 完整测试（437 PASS · 2026-08-14 baseline · PR-4b merged）
python -m uv run --frozen pytest tests/unit tests/integration -q

# 4 重静态门禁
python -m uv run --frozen ruff check packages/ services/ agents/ tests/
python -m uv run --frozen ruff format --check packages/ services/ agents/ tests/
python -m uv run --frozen pyright packages/ services/ agents/ tests/
python -m uv run --frozen pytest tests/unit tests/integration
```

## 相关文档

- [ADR-0005 Python-first 技术栈](../adr/0005-python-first-technology-stack.md)
- [ADR-0006 Memory transport D 方案](../adr/0006-memory-transport.md)
- [宪法 v0.5.0 §3.8](../constitution/v0.5.0.md)
- [Phase 4 PR-3 plan](../phase4/pr3-knowledge-service-step1-plan.md)
- [L3-5 Knowledge Service Spec §3](../spec/L3-file-specs/L3-knowledge-service.md)
- [L3-6 Memory Backend Spec §3](../spec/L3-file-specs/L3-memory-backend.md)
