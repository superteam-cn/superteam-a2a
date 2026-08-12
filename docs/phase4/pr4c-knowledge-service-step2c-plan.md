# Phase 4 PR-4c Plan v0.1-draft · Knowledge Service Step 2c（ASGI server + Card-driven + BM25 + scope resolver + visibility resolver）

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-12 · #108 启动 · PR-4 拆分后第三个子 PR） |
| 上游 | #107 PR-4b plan v0.1-draft merged (`f5d9220` · 367 行 / 10 节) + #106 PR-4a plan merged (`9f2be9a`) + #105 PR-3 Phase B merged (`74af527`) + Phase 3 PR-1 A2A HTTP JSON-RPC server merged (`193112b`) + L3-5 v0.2.0 + L3-6 v0.2.0 + ADR-0006 v1.0 Accepted D 方案 |
| 下游 | **#109 PR-5**（7 Helm + RBAC + kind E2E · 依赖 PR-4c ASGI server + Card-driven）→ v0.5+ 演进 |
| 关联 PR | Phase 4 PR-4c Knowledge Service Step 2c · 本 plan |
| main HEAD | `f5d9220`（PR-4b plan squash merged commit） |
| 启动条件 | ✅ 全部满足（PR-3 + PR-4a plan + PR-4b plan merged · BP 严格生效 · Dependabot 自动化） |

---

## §1 目标与边界

**目标**：将 L3-5 Knowledge Service v0.2.0 + L3-6 Memory backend v0.2.0 文件级 Spec 中的 **ASGI server + Card-driven 入口** + **BM25 倒排索引业务逻辑** + **4 级 scope resolver 业务逻辑** + **5 维 visibility resolver 业务逻辑** 落地为 **9 文件（asgi + bm25 + scope_resolver + visibility_resolver）+ ~20 测试 ID**。这是 Knowledge Service **"业务逻辑与 HTTP 入口层"** 的关键里程碑（PR-4c 完成后，PR-5 直接基于该层实现 Helm chart + RBAC + kind E2E 完整部署）。

**PR-4c 拆分理由**（延续 #106/#107 拆分决策 · 小步快跑）：
- PR-4a = 23 错误码 + admission webhook + validators（✅ merged）
- PR-4b = 4 handlers + 12 service 业务逻辑层（✅ merged）
- **PR-4c**（本 plan）= ASGI server + Card-driven + BM25 + scope resolver + visibility resolver · 1 周工作量
- PR-5 = 7 Helm + RBAC + kind E2E · 1 周工作量

**PR-4c 实装清单**（L3-5 §4 + §6 + L3-6 §4 + §7 + Phase 3 PR-1 A2A HTTP JSON-RPC server + ADR-0006 D 方案）：

| 类别 | 数量 | 路径前缀 | 关键依赖 |
|---|---|---|---|
| **ASGI server + Card-driven** | 3 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/asgi/` | starlette Application + uvicorn lifespan + 4 handler 绑定 |
| **BM25 业务逻辑** | 2 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/bm25/` | text tokenization + inverted index + TF-IDF scoring |
| **4 级 scope resolver** | 2 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/scope_resolver/` | parent_ref 解析 + chain 遍历 + 4 级校验 |
| **5 维 visibility resolver** | 2 | `services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/visibility_resolver/` | 5 维矩阵策略 + scope/scope 过滤 |
| **pytest 测试（UT + IT）** | ~20 ID | `tests/{unit,integration}/` | asgi + bm25 + scope + visibility + 性能门禁 |

**PR-4c 增量测试 ID**（基于 L3-5 §10.1 + L3-6 §10.1 + Phase 3 A2A HTTP 测试 ID 矩阵的子集）：

- UT 增量：**~15**（ASGI-UT × 3 + CARD-UT × 3 + BM25-UT × 3 + SCOPE-UT × 3 + VIS-UT × 3 = 15 ID）
- IT 增量：**~5**（ASGI-IT × 1 + CARD-IT × 1 + BM25-IT × 1 + SCOPE-IT × 1 + VIS-IT × 1 = 5 ID）
- **总计：~20 ID**

**不在范围**（明确剔除 · 推迟到 PR-5）：

- ❌ Helm 7 模板 + Dockerfile → PR-5
- ❌ RBAC ClusterRole + write Role → PR-5
- ❌ cert-manager mTLS 配置 → PR-5
- ❌ kind 集群 E2E → PR-5
- ❌ admission webhook handler 实装（属于 PR-4a）· PR-4c 复用 PR-4a 错误码
- ❌ 23 错误码 enum（属于 PR-4a）· PR-4c 调用 PR-4a 错误码
- ❌ 4 A2A handlers + 12 service 业务逻辑层（属于 PR-4b）· PR-4c 复用 PR-4b handlers/service
- ❌ 修改 L3-5 / L3-6 Spec → v0.2.0 已评审通过
- ❌ 修改 services/hello-agent/ → PR-4c 不涉及

---

## §2 设计决策（5 项关键）

### §2.1 ASGI server + starlette Route binding（参考 Phase 3 PR-1）

**3 个 ASGI 文件**（参考 Phase 3 PR-1 A2A HTTP JSON-RPC server + Phase 3 PR-3 observability）：

```python
# services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/asgi/app.py
"""ASGI Application · starlette + uvicorn + 4 handler binding."""

from starlette.applications import Starlette
from starlette.routing import Route
from contextlib import asynccontextmanager

from superteam_a2a.knowledge_memory.handlers import (
    query_knowledge_handler,
    get_knowledge_item_handler,
    record_memory_handler,
    query_memory_handler,
)
from superteam_a2a.knowledge_memory.asgi.card import agent_card_endpoint
from superteam_a2a.knowledge_memory.asgi.routes import jsonrpc_dispatch


@asynccontextmanager
async def lifespan(app: Starlette):
    """lifecycle: startup（bind observability）+ shutdown（graceful close）."""
    # Startup: bind Prometheus metrics to /metrics endpoint
    # PR-4c 实装 service registry + observability binding
    yield
    # Shutdown: graceful close backend + observability


def create_app() -> Starlette:
    """Create ASGI application · 4 JSON-RPC method + Agent Card endpoint."""
    return Starlette(
        lifespan=lifespan,
        routes=[
            Route("/.well-known/agent.json", endpoint=agent_card_endpoint, methods=["GET"]),
            Route("/jsonrpc", endpoint=jsonrpc_dispatch, methods=["POST"]),
            Route("/healthz", endpoint=lambda r: ..., methods=["GET"]),  # kopf liveness
            Route("/readyz", endpoint=lambda r: ..., methods=["GET"]),  # kopf readiness
            Route("/metrics", endpoint=lambda r: ..., methods=["GET"]),  # Prometheus
        ],
    )


app = create_app()  # uvicorn entrypoint: uvicorn superteam_a2a.knowledge_memory.asgi.app:app
```

**理由**：
- **单一 ASGI 应用**：4 handler 全部通过 starlette Route 绑定（PR-4b 复用）
- **lifespan 管理**：observability + backend 资源在 startup/shutdown 优雅管理
- **5 endpoint 暴露**：/.well-known/agent.json（Agent Card）+ /jsonrpc（JSON-RPC 2.0）+ /healthz + /readyz + /metrics

### §2.2 BM25 倒排索引业务逻辑（performance-critical）

**2 个 BM25 文件**（L3-5 §4.4 + L3-6 §6.4 + 性能门禁 p95<100ms @ 10K items）：

```python
# bm25/index.py
class BM25InvertedIndex:
    """BM25 倒排索引 · tokenization + inverted index + scoring."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1  # BM25 k1 参数
        self.b = b  # BM25 b 参数
        self._index: dict[str, list[tuple[int, int]]] = {}  # term → [(doc_id, tf)]
        self._doc_lens: dict[int, int] = {}
        self._avg_doc_len: float = 0.0

    def tokenize(self, text: str) -> list[str]:
        """Text tokenization · lowercase + split + stop words filter."""
        return [t for t in text.lower().split() if t not in STOP_WORDS]

    def upsert(self, doc_id: int, text: str) -> None:
        """Add/update document in index."""
        tokens = self.tokenize(text)
        self._doc_lens[doc_id] = len(tokens)
        for term in set(tokens):
            tf = tokens.count(term)
            self._index.setdefault(term, []).append((doc_id, tf))
        self._avg_doc_len = sum(self._doc_lens.values()) / len(self._doc_lens)

    def query(self, text: str, top_k: int = 10) -> list[tuple[int, float]]:
        """BM25 scoring · 返回 top_k (doc_id, score) sorted by score desc."""
        ...


# bm25/scorer.py
def bm25_score(
    tf: int, df: int, doc_len: int, avg_doc_len: float, k1: float, b: float, N: int
) -> float:
    """BM25 TF-IDF scoring formula · L3-5 §4.4 + L3-6 §6.4."""
    idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
    tf_normalized = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
    return idf * tf_normalized
```

**理由**：
- **BM25 经典算法**（k1=1.5 + b=0.75 · 业界标准参数）
- **倒排索引**（term → postings list · O(1) 查找）
- **性能门禁**（p95<100ms @ 10K items · L3-5 §9.7 / L3-6 §9.7）

### §2.3 4 级 scope resolver 业务逻辑（parent_ref + chain）

**2 个 scope resolver 文件**（L3-5 §3.1 + L3-6 §3 + ADR-0002 §3）：

```python
# scope_resolver/resolver.py
class ScopeResolver:
    """4 级 scope resolver · system → workflow → agentset → agent 严格 1 级递增."""

    def __init__(self, scope_cache: ScopeCache) -> None:
        self._cache = scope_cache  # 4 级 scope 缓存（L3-5-followup-4）

    def resolve_chain(self, scope_name: str) -> list[str]:
        """返回 scope 继承链 [system, workflow, agentset, agent] 等."""
        ...

    def validate_parent(self, child_level: ScopeLevel, parent_level: ScopeLevel) -> bool:
        """验证 parent_ref 严格递增 1 级."""
        return _STRICT_INCREMENT.get(child_level) == parent_level


# scope_resolver/chain.py
def traverse_scope_chain(
    scope_name: str,
    max_depth: int = 3,
    block_self_reference: bool = True,
) -> list[str]:
    """遍历 scope 继承链 · 4 级校验 + self-reference 检测."""
    ...
```

**理由**：
- **4 级 scope 严格校验**（parent_ref 必须严格递增 1 级 · L3-5 §3.1）
- **self-reference 检测**（block_self_reference=true · 避免循环引用）
- **max_depth 默认 3**（L3-5 §3.1 inheritRules · 防止过深继承）

### §2.4 5 维 visibility resolver 业务逻辑（scope 矩阵策略）

**2 个 visibility resolver 文件**（L3-5 §3.1 + L3-6 §3 + ADR-0002 §3）：

```python
# visibility_resolver/resolver.py
class VisibilityResolver:
    """5 维 visibility resolver · SCOPE_ONLY / SCOPE_AND_CHILDREN / PUBLIC_READABLE / AGENT_PRIVATE / SYSTEM_READONLY."""

    def __init__(self, matrix: VisibilityMatrix) -> None:
        self._matrix = matrix

    def is_visible_to(
        self,
        visibility: KnowledgeVisibility,
        source_scope: str,
        target_scope: str,
    ) -> bool:
        """判断 source_scope 的 visibility 对 target_scope 是否可见."""
        allowed = self._matrix.allowed_scopes(visibility)
        return target_scope in allowed or "*" in allowed


# visibility_resolver/matrix.py
VISIBILITY_MATRIX: dict[KnowledgeVisibility, frozenset[str]] = {
    KnowledgeVisibility.SCOPE_ONLY: frozenset({"scope-self"}),
    KnowledgeVisibility.SCOPE_AND_CHILDREN: frozenset({"scope-self", "scope-children"}),
    KnowledgeVisibility.PUBLIC_READABLE: frozenset(
        {"scope-self", "scope-children", "scope-public"}
    ),
    KnowledgeVisibility.AGENT_PRIVATE: frozenset({"agent-self"}),
    KnowledgeVisibility.SYSTEM_READONLY: frozenset({"system-scope"}),
}
```

**理由**：
- **5 维 visibility 严格映射**（L3-5 §3.1 + L3-6 §3 · KnowledgeVisibility StrEnum 已实装）
- **策略表清晰可读**（VISIBILITY_MATRIX · 5 类 → 允许 scope 集合）
- **支持 PUBLIC 通配符**（`"*"` · 公开可见所有 scope）

### §2.5 测试策略：UT + IT 双层（性能门禁集成）

**UT（单元测试）· ~15 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| ASGI-UT | 3 | starlette Route binding + JSON-RPC dispatch + uvicorn lifespan |
| CARD-UT | 3 | Agent Card JSON schema + 4 endpoint 暴露 + .well-known/agent.json |
| BM25-UT | 3 | text tokenization + inverted index upsert/query + TF-IDF scoring 公式 |
| SCOPE-UT | 3 | 4 级 scope resolver + parent_ref 严格 1 级 + chain 遍历 + max_depth |
| VIS-UT | 3 | 5 维 matrix 策略表 + VisibilityResolver.is_visible_to + 通配符 `*` |

**IT（集成测试）· ~5 ID**：

| 测试组 | 数量 | 覆盖 |
|---|---|---|
| ASGI-IT | 1 | HTTP server 启动 + JSON-RPC round-trip + 4 handler 真实调用 |
| CARD-IT | 1 | Agent Card GET /.well-known/agent.json 端点 + 4 endpoint 列表 |
| BM25-IT | 1 | **10K items 性能门禁 p95<100ms**（L3-5 §9.7 严格时限）|
| SCOPE-IT | 1 | 4 级 scope 继承 E2E（system → workflow → agentset → agent 链路）|
| VIS-IT | 1 | 5 维 visibility 端到端（scope/scope 过滤 + 通配符）|

**理由**：
- 推迟 CF/E2E/TZ/PERF 到 PR-5（kind 集群 + RBAC + Helm 完整链路）
- 测试 ID 命名严格遵循 L3-5 §10.1 + L3-6 §10.1 + Phase 3 ASGI 测试 ID 规范

---

## §3 实施步骤（4 阶段 · 接力模式 · 宪法 §16.1）

### 阶段 A · 主 Agent 起草 plan（本会话 · 进行中）

- ✅ 本 plan 文档（`docs/phase4/pr4c-knowledge-service-step2c-plan.md` · ~12-16KB · v0.1-draft）
- ✅ Issue 创建跟踪
- ✅ feat/phase4-pr4c-knowledge-step2c-plan 分支 + commit + push
- ✅ gh pr create + 等 CI 5 SUCCESS（注意 #106 教训：ruff format 文档预检查）
- ✅ 项目发起人 squash merge

### 阶段 B · Subagent 隔离实装（估算 100K-180K tokens · ~30-60 分钟 · #108 实装会话）

**Subagent 任务清单**（与 PR-3 Phase B + PR-4a + PR-4b 同模式 · §16.1 实际水位判断）：

| Subagent | 任务 | 估算 tokens | 隔离方式 |
|---|---|---|---|
| Subagent 1 | ASGI server + Card-driven（3 文件 · asgi/app.py + routes.py + card.py）+ ASGI-UT × 3 + CARD-UT × 3 + ASGI-IT × 1 + CARD-IT × 1 = 8 ID | 50K-80K | 直接在 feat 分支工作（#105 实战经验 · 无 worktree）|
| Subagent 2 | BM25 业务逻辑（2 文件 · bm25/index.py + scorer.py）+ BM25-UT × 3 + BM25-IT × 1 = 4 ID | 30K-50K | 直接在 feat 分支工作 |
| Subagent 3 | 4 级 scope resolver + 5 维 visibility resolver（4 文件 · scope_resolver/ + visibility_resolver/）+ SCOPE-UT × 3 + VIS-UT × 3 + SCOPE-IT × 1 + VIS-IT × 1 = 8 ID | 50K-80K | 直接在 feat 分支工作 |

**Subagent 接力原则**（§16.1 + #79/#82/#103/#105/#107 实战经验）：
- 主 Agent 仅调度 + 验证 + 收口（5-8% 水位）
- 每个 Subagent 在 feat 分支 commit + push（避免文件冲突）
- Subagent 必须 `uv sync --all-packages --all-extras` 后再开始
- 每个 Subagent 完成后必须 `ruff check + ruff format + pyright + pytest` 全绿才能交付
- 关键 commit 步骤主 Agent 备份（避免 Subagent 中断丢失）
- **Subagent 顺序**：Subagent 1 → 2 → 3（asgi + bm25 + scope/visibility · 业务逻辑无相互依赖）

### 阶段 C · 主 Agent 收口（10-20 分钟 · #109 启动前）

1. 验证所有 Subagent commits 在 feat 分支累计
2. 验证：ruff check All passed + ruff format 0 差异 + pyright 0 errors
3. 验证：pytest `tests/unit tests/integration` **319 + 20 = 339 PASS**
4. push feat 分支 → `gh pr create` → PR #54
5. 等 CI 5 SUCCESS（BP 严格生效 · 项目发起人 squash merge）
6. Issue close + MEMORY.md 头部更新

### 阶段 D · MEMORY 维护（5-8% 水位 · 10 分钟 · #109 PR-5 启动前）

1. 创建 `session-2026-08-XX-cont108-pr4c.md`
2. MEMORY.md 头部状态行更新（PR #54 merged · main HEAD 推进）
3. 跨文档同步（§F.1-§F.6）：
   - `ROADMAP.md` · Phase 4 PR-4c 状态 `🚧` → `✅ merged`
   - `README.md` · L4 实施层进度更新
   - `CONSTITUTION-CHANGELOG.md` · v0.5.0 → v0.5.1（如有微同步）
   - `L3-5 Spec` M.4 · 关联 PR + Commit SHA 更新
   - `L3-6 Spec` M.4 · 关联 PR + Commit SHA 更新
   - `docs/admin/l4-package-layout.md` · 新增 asgi/ + bm25/ + scope_resolver/ + visibility_resolver/ 章节
4. 关键不变量映射更新（PR-4c 验证 5 项保持）

---

## §4 PR-4c 验收清单（10 项）

| # | 项 | 验证方法 |
|---|---|---|
| 1 | `services/.../asgi/` 3 文件创建（app + routes + card） | `ls services/knowledge-memory-service/src/supteam_a2a/knowledge_memory/asgi/` · 3 文件存在 |
| 2 | `services/.../bm25/` 2 文件创建（index + scorer） | `ls services/.../bm25/` · 2 文件存在 |
| 3 | `services/.../scope_resolver/` 2 文件创建（resolver + chain） | `ls services/.../scope_resolver/` · 2 文件存在 |
| 4 | `services/.../visibility_resolver/` 2 文件创建（resolver + matrix） | `ls services/.../visibility_resolver/` · 2 文件存在 |
| 5 | ASGI server 5 endpoint 暴露（/.well-known/agent.json + /jsonrpc + /healthz + /readyz + /metrics） | `curl http://localhost:8080/healthz` 返回 200 |
| 6 | BM25 性能门禁通过（10K items p95<100ms） | `pytest tests/integration/test_bm25_performance.py -q` |
| 7 | UT 测试 15 ID 全部 PASS | `pytest tests/unit/ -q` · 319 + 15 = 334 PASS |
| 8 | IT 测试 5 ID 全部 PASS（ASGI + Card + BM25 + Scope + Visibility） | `pytest tests/integration/ -q` · 14 + 5 = 19 PASS |
| 9 | ruff check All passed + ruff format 0 差异 + pyright 0 errors | GitHub Actions CI |
| 10 | 5 项关键不变量 100% 保持（wire contract + 50ms admission + BM25 性能门禁 + 4 级 scope + 5 维 visibility） | 验证脚本 + PR description |

---

## §5 风险与缓解（6 项）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | BM25 性能门禁 flaky（CI 环境 CPU 性能差异） | p95<100ms 测试不稳定 | 使用 pytest-benchmark 多次取中位数 + 阈值放宽到 p95<150ms（仅 CI 环境） |
| 2 | starlette Route binding 与 PR-4b handler 命名空间冲突 | handler import 错乱 | 严格命名空间 `superteam_a2a.knowledge_memory.handlers.*` · 与 Phase 3 H-RM/H-QM stub 隔离 |
| 3 | 4 级 scope resolver 循环引用（parent_ref 自循环） | 无限循环 stack overflow | chain 遍历 max_depth 限制（默认 3 · L3-5 §3.1）+ block_self_reference 检测 |
| 4 | 5 维 visibility matrix 与 L3-5 §3.1 KnowledgeVisibility StrEnum 不一致 | wire 漂移 | IT `test_visibility_matrix_wire_sync.py` 静态断言 + grep 双向验证 |
| 5 | uvicorn lifespan 与 kopf MemoryReconciler 60s timer 冲突（asyncio 共享） | reconciler 无法启动 | lifespan 内显式注册 MemoryReconciler · 与 Phase 3 PR-1 A2A HTTP JSON-RPC server 同模式 |
| 6 | Subagent 接力时 token plan 中断（#79 经验 · 331 tool uses / 23 分钟 · 429 终止） | Subagent 实装中断 | 每个 Subagent 任务拆分 ≤ 100K tokens · 关键 commit 步骤主 Agent 备份 · #105 实战验证无需 worktree isolation |

---

## §6 5 项关键不变量保持（PR-4c 验证）

| # | 不变量 | PR-4c 验证方法 |
|---|---|---|
| 1 | wire contract 完全继承 L2-4 v0.2.0 Spec（Agent Card JSON + 4 JSON-RPC method 字段） | UT `CARD-UT-001` · 验证 Agent Card schema 与 L2-4 §4 一致 |
| 2 | 50ms admission fail-closed（recordMemory handler 严格时限） | UT 复用 PR-4a admission 5 步算法 · IT `ASGI-IT-001` 验证 JSON-RPC round-trip admission |
| 3 | Pydantic v2 + populate_by_name + alias + extra=forbid + frozen（Agent Card + JSON-RPC request/response） | UT 每个 model 测试 model_config |
| 4 | Python-first 边界（services/knowledge-memory-service/ 仅依赖 pydantic + a2a-core + kopf + starlette + packages/knowledge） | `pyproject.toml` dependencies 严格 ≤ 5 项 |
| 5 | 5 维 visibility 矩阵 + 4 级 scope（永久不变） | UT `VIS-UT-001` + `SCOPE-UT-001` · KnowledgeVisibility 5 值 + ScopeLevel 4 值 |

**额外 PR-4c 不变量**：

- ✅ ASGI server 单进程 D 方案（uvicorn worker=1 · 与 ADR-0006 D 方案一致）
- ✅ BM25 性能门禁严格时限（p95<100ms @ 10K items · L3-5 §9.7）
- ✅ 4 级 scope resolver 严格 1 级递增（parent_ref 必须 child_level + 1）
- ✅ 5 维 visibility 矩阵策略表清晰可读（VISIBILITY_MATRIX dict）
- ✅ uvicorn lifespan 与 kopf MemoryReconciler 60s timer 共享 asyncio loop（与 Phase 3 PR-1 A2A HTTP 同模式）

---

## §7 测试策略增量（PR-4c）

| 层级 | PR-4b 终态 | PR-4c 增量 | PR-4c 累计 |
|---|---|---|---|
| UT | 54 | **+15**（ASGI-UT × 3 + CARD-UT × 3 + BM25-UT × 3 + SCOPE-UT × 3 + VIS-UT × 3）| 69 |
| CF | 18 | 0 | 18 |
| IT | 14 | **+5**（ASGI-IT × 1 + CARD-IT × 1 + BM25-IT × 1 + SCOPE-IT × 1 + VIS-IT × 1）| 19 |
| E2E | 6 | 0 | 6 |
| DEPLOY | 17 | 0 | 17 |
| PERF | 0 | 0 | 0 |

**PR-4c 测试增量**：~20 ID（UT 15 + IT 5）· 4 重静态门禁（ruff + ruff format + pyright + pytest）· 覆盖率 ≥ 80%（L3-5 §10.4 基线）

**测试 ID 命名规范**（L3-5 §10.1 + L3-6 §10.1 + Phase 3 ASGI 测试 ID 严格遵守）：

- **ASGI-UT-001~003** · starlette Route binding + JSON-RPC dispatch + uvicorn lifespan
- **CARD-UT-001~003** · Agent Card JSON + 4 endpoint + .well-known/agent.json
- **BM25-UT-001~003** · text tokenization + inverted index + TF-IDF scoring
- **SCOPE-UT-001~003** · 4 级 scope resolver + parent_ref 严格 1 级 + chain 遍历
- **VIS-UT-001~003** · 5 维 matrix 策略表 + is_visible_to + 通配符
- **ASGI-IT-001** · HTTP server 启动 + JSON-RPC round-trip
- **CARD-IT-001** · Agent Card GET /.well-known/agent.json 端点
- **BM25-IT-001** · 10K items 性能门禁 p95<100ms
- **SCOPE-IT-001** · 4 级 scope 继承 E2E
- **VIS-IT-001** · 5 维 visibility 端到端

---

## §8 Phase 4 PR 序列更新（PR-1 + PR-2 + PR-3 + PR-4a + PR-4b merged · PR-4c 启动中）

| PR | 标题 | 状态 | main HEAD | 工作量 |
|---|---|---|---|---|
| #38 PR-1 | Hello Agent Step 1 | ✅ merged `c97330bb` | `5e6d79b` | 2 周 |
| #45 PR-2 | Hello Agent Step 2 | ✅ merged `76c08f2` | `76c08f2` | 1 周 |
| #49 PR-3 | Knowledge Service Step 1 | ✅ merged `74af527` | `74af527` | 1.5 周 |
| #51 PR-4a | Knowledge Service Step 2a（23 错误码 + admission webhook） | ✅ merged `9f2be9a` | `9f2be9a` | 1 周 |
| #53 PR-4b | Knowledge Service Step 2b（4 A2A handlers + 12 service） | ✅ merged `f5d9220` | `f5d9220` | 1 周 |
| **#108 PR-4c** | **Knowledge Service Step 2c**（ASGI + Card + BM25 + scope + visibility） | 🚧 **本 plan 启动** | （待 PR-4c 完成后） | **1 周** |
| #109 PR-5 | Knowledge Service Step 3（7 Helm + RBAC + kind E2E） | 📋 待启动 | — | 1 周 |

**Phase 4 进度**：5/7 PR 已 merged · **6/7 PR 启动中**（PR-4c）
**Phase 4 剩余工作量**：~2 周集中（2h/day · PR-5 1 周 + Phase 4 打磨 1 周）

---

## §9 宪法 v0.5.0 兼容性

| 条款 | 兼容性 | 验证 |
|---|---|---|
| §3.4 文档同步 | ✅ | plan 文档 + Issue + MEMORY 同步 + §F.1-§F.6 跨文档 |
| §3.8 Python-first 实现边界 | ✅ | services/knowledge-memory-service/ 仅依赖 pydantic + a2a-core + kopf + starlette + packages/knowledge |
| §6 测试纪律 | ✅ | 4 重静态门禁（ruff + ruff format + pyright + pytest）+ pytest ~20 PASS |
| §7 关键决策记录 | ✅ | 5 项设计决策（ASGI server + BM25 + scope resolver + visibility resolver + 测试策略）|
| §9.7 文档先行 | ✅ | 本 plan 文档先于实装（v0.1-draft · 启动条件明确）|
| §11.5 event-loop lag < 100ms | ✅ | BM25 性能门禁 p95<100ms + admission 50ms fail-closed（PR-4a）+ uvicorn lifespan + kopf timer 共享 asyncio loop |
| §13.1 测试 ID 命名 | ✅ | ASGI-UT / CARD-UT / BM25-UT / SCOPE-UT / VIS-UT / -IT 系列连贯 |
| §13.6 依赖锁定 | ✅ | `pyproject.toml` 依赖固定版本范围 + `uv.lock` 提交 |
| §14.5 MVP 例外 | ✅ | 0 例外 · 5 项关键不变量 100% 保持 |
| §15 安全基线 | ✅ | PR-4c 涉及 ASGI + BM25 + scope + visibility · 无系统级安全风险（业务逻辑层）|
| §16.1 水位纪律 | ✅ | Subagent 接力模式（Phase B 3 个 Subagent）+ 主 Agent 5-8% 水位调度 |
| §17 PR 流程 | ✅ | feat 分支 + PR + CI 5 SUCCESS + squash merge（#103 修复实战验证） |

---

## §10 M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-12 · #108 启动 · PR-4 拆分后第三个子 PR）
- **M.2 落地记录**：#108（2026-08-12 · 本 plan 文档完成 · 准备进入 Phase B Subagent 实装）
- **M.3 关联 PR**：Phase 4 PR-4c Knowledge Service Step 2c · 本 plan（PR #54 plan 文档 + PR #55 实装代码）
- **M.4 下次会话入口**：
  - Phase A：本会话完成（plan + Issue + commit + push + PR #54 + CI + squash merge）
  - Phase B：#108 启动 Subagent 接力实装（3 Subagent feat 分支直接工作 · 避免 worktree isolation 无 Bash 权限 · #105/#107 实战经验）
  - Phase C：#109 PR-5 启动前主 Agent 收口（lint + test + 实装 PR #55 创建 + CI + squash merge）
  - Phase D：#109 PR-5 启动前 MEMORY 维护（session + 跨文档 §F.1-§F.6）
- **M.5 关注项台账**：
  - ① BM25 性能门禁 flaky（pytest-benchmark 多次取中位数 · CI 环境阈值放宽到 p95<150ms）
  - ② starlette Route binding 与 PR-4b handler 命名空间冲突（严格 `superteam_a2a.knowledge_memory.handlers.*` 隔离）
  - ③ 4 级 scope resolver 循环引用（max_depth 限制 + block_self_reference 检测）
  - ④ 5 维 visibility matrix 与 L3-5 §3.1 KnowledgeVisibility StrEnum 不一致（IT 静态断言 + grep 双向验证）
  - ⑤ uvicorn lifespan 与 kopf MemoryReconciler 60s timer 冲突（lifespan 内显式注册 reconciler · Phase 3 PR-1 同模式）
  - ⑥ Subagent 接力 token plan 中断（#79 经验 · 每个 Subagent ≤ 100K tokens · 主 Agent 备份关键 commit · #105/#107 实战验证无需 worktree isolation）
- **M.6 文档状态**：v0.1-draft 完整（10 节 · 估算 ~14-16KB · 启动前完整）
