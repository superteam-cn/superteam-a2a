# L4 包布局（uv workspace）

> 📅 Last updated: **2026-08-12**（#105 Phase 4 PR-3 Phase B 完整实装）
> 维护：项目发起人
> 依据：ADR-0005 §13.1 + 宪法 v0.5.0 §3.8 + ADR-0006 v1.0 Accepted D 方案

## uv workspace members（2026-08-12）

```
packages/
├── a2a-core/           # A2A Protocol types + extended 4 methods (L3-2 v0.2.0)
├── adapter-sdk/        # FrameworkAdapter Protocol + AgentCardConverter (L3-3 v0.2.0)
├── operator/           # Kopf handlers + 4 CRDs + MemoryReconciler (L3-1 v0.2.0)
├── knowledge/          # 8 CRD types Pydantic v2 (L3-5 v0.2.0) · Phase 4 PR-3 Step 1 ✅
└── shared-visibility/  # 4 shared modules (与 L3-6 共享 visibility) · Phase 4 PR-3 Step 1 ✅

services/
├── knowledge-memory-service/  # L3-5 + L3-6 单进程服务 (ADR-0006 D 方案)
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

## Python-first 边界（§3.8）

- 每个 workspace member `pyproject.toml` `requires-python = ">=3.12"`
- `packages/knowledge/` 仅依赖 `pydantic>=2.10,<3`（不依赖 operator / a2a-core）
- `packages/shared-visibility/` 仅依赖 `pydantic + packages/knowledge`（不反向 import 业务逻辑）
- 禁止跨包 `__init__.py` 创建（PEP 420 namespace 兼容性）

## 验证命令

```bash
# uv sync 全部 workspace members
python -m uv sync --all-packages --all-extras

# 完整测试（284 PASS · 2026-08-12 baseline）
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
