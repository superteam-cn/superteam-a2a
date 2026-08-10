# L4-Phase3 PR-4 Plan v0.1-draft · H-RM/H-QM-E2E 实装

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-10 · #96 启动） |
| 上游 | PR-1 #30 ✅ + PR-2 #34 ✅ + PR-3 #35 ✅ + Phase 2 e2e-envtest.yml |
| 下游 | PR-5 文档同步（30 min · #97） |
| 关联 PR | Phase 2 #22-#28 + #29 hotfix · Phase 3 #30 (server) + #34 (K8sBackend) + #35 (metrics) + **#36 (H-RM/H-QM-E2E · PR-4 · 本 plan)** |
| main HEAD | `25b857c`（含 PR #35）|

---

## §1 目标与边界

**目标**：启用 Phase 2 留下的 2 个 skipped E2E 测试，从 `pytest.skip(...)` 替换为真实 A2A HTTP JSON-RPC round-trip 验证。

**3 E2E 子任务**：

| # | 测试 ID | 文件 | 现状 → 目标 |
|---|---|---|---|
| 1 | H-RM-E2E-001 | `tests/e2e/knowledge_memory/test_handle_record_memory.py` | skipped → 真实 apply + POST record |
| 2 | H-QM-E2E-001 | `tests/e2e/knowledge_memory/test_handle_query_memory.py` | skipped → 真实 apply 3 CR + POST query |

**不在范围**（明确剔除）：
- ❌ e2e-envtest.yml workflow 改动（Phase 2 PR-4.1.1 #90 已就绪 · 复用即可）
- ❌ 业务逻辑改动（Phase 1+ 全部已落地 · E2E 只验证 round-trip）
- ❌ 新增测试 ID（仅 unskip + 实装 · 不引入新边界）
- ❌ helm chart 改动（PR-1/2/3 已合并 · PR-4 仅消费）

---

## §2 设计决策（3 项 · 实装路径）

### §2.1 E2E 访问策略

**选项 A · port-forward + localhost**：
- ✅ kubectl port-forward 转发 Service 8080 → localhost:8080
- ✅ urllib 标准库（Phase 2 E2E 0 新增依赖）
- ✅ Service ClusterIP（port=8080 · targetPort=http）
- ❌ port-forward subprocess 进程管理（cleanup 必须可靠）

**选项 B · pod IP 直连**：
- ❌ pod IP 不稳定（rollout 重建）
- ❌ Service 是 ClusterIP，pod 直接访问绕过 Service selector 风险

**选项 C · in-cluster client-go**：
- ❌ 复杂 · 与 Phase 2 LIFECYCLE/LEADER E2E 不一致

**推荐**：A port-forward（与 Phase 2 LIFECYCLE/LEADER 测试同模式 · E2E 仅消费 Service）

### §2.2 Memory CR apply 模式

**复用 LIFECYCLE-E2E-001 模式**：
- 单一 `kubectl apply -f -` with inline YAML
- Memory CR spec 用 Phase 2 LIFECYCLE 一致的最小字段（scopeRef/agentRef/content/summary/confidence/decayDays）
- H-QM 额外 apply 3 个不同 spec 字段（scope/agent/industry 不同）

### §2.3 JSON-RPC 2.0 envelope

**严格遵循 PR-1 server.py 协议**：
- `{"jsonrpc": "2.0", "id": <str|int>, "method": "...", "params": {...}}`（method 编码到 URL `/jsonrpc/<method>` · 实际 server 仅用 params）
- response 200：`{"jsonrpc": "2.0", "result": {...}, "id": ...}` 或 `{"jsonrpc": "2.0", "error": {"code": ..., "message": ...}, "id": ...}`

**关键约束**（L3-6 §6.1 + PR-1 server.py）：
- params 必须用 K8s wire format（camelCase · `scopeRef` / `agentRef` / `decayDays`）
- Memory 顶层字段：metadata（name + namespace）+ spec
- 12 MEMORY_* 错误码 → JSON-RPC error.code 1:1 映射（测试只验 error.code == 0 即成功）

---

## §3 实装步骤（3 阶段 · 接力模式）

### 阶段 A · 分支与准备（主 Agent）

1. `git checkout -b feat/l4-phase3-pr4-h-rm-h-qm-e2e`（基于 main HEAD `25b857c`）
2. 创建 plan 文档（已完成 · 本文件）
3. 验证 LIFECYCLE/LEADER E2E 模式可复用（已确认）

### 阶段 B · Subagent 接力实装（主 Agent 调度 + Subagent 隔离 · 35-45 min）

**Subagent 任务**：
1. 改 `tests/e2e/knowledge_memory/test_handle_record_memory.py`：
   - 移除 `pytest.skip(...)` 块
   - 添加 `_ensure_helm_install()` helper（复用 test_memory_lifecycle.py 模式）
   - 添加 `_port_forward_service()` helper（kubectl port-forward subprocess）
   - 实装 H-RM-E2E-001 真实 round-trip：
     - apply Memory CR
     - kubectl wait 60s timer + observedGeneration >= 1
     - kubectl port-forward service 8080:8080
     - POST /jsonrpc/record_memory（wire format params）
     - 断言 response.error is None + result 字段有效
2. 改 `tests/e2e/knowledge_memory/test_handle_query_memory.py`：
   - 移除 `pytest.skip(...)` 块
   - 实装 H-QM-E2E-001 真实 round-trip：
     - apply 3 个不同 Memory CR（scopeRef/agentRef/industry 不同）
     - wait 60s timer（3 个 CR observedGeneration >= 1）
     - kubectl port-forward
     - POST /jsonrpc/query_memory with filters（scopeRef/agentRef）
     - 断言 response.result.memories 包含过滤子集
3. 更新 module docstring（H-RM/H-QM-E2E 状态从 "deferred to Phase 3" → "实装完成 PR-4"）
4. 添加 module-level `pytest.mark.e2e` 标记（已有 · 无需改）
5. 不改 e2e-envtest.yml（已支持 · 复用即可）

**Subagent 接力原则**（§16.1）：
- 主 Agent 仅调度 + 验证 + 收口
- Subagent 实装文件 + 单 commit push
- 主 Agent 收口：lint + pytest + ruff + pyright

### 阶段 C · 主 Agent 收口（验证 + commit + push + PR · 10 min）

1. **本地验证**（不依赖 cluster）：
   - `python -m uv run pytest tests/unit tests/conformance` → 期望 **241/241 PASS**
   - `python -m uv run ruff check .` → All checks passed
   - `python -m uv run ruff format --check .` → already formatted
   - `python -m uv run pyright .` → 0 errors / 既有 warnings
2. **commit message**（conventional commits）：
   ```
   feat(phase3): PR-4 H-RM/H-QM-E2E-001 真实实装（unskip + port-forward + JSON-RPC）
   ```
3. **push + PR**：
   - `git push -u origin feat/l4-phase3-pr4-h-rm-h-qm-e2e`
   - `gh pr create --title "feat(phase3): PR-4 H-RM/H-QM-E2E-001 真实实装" --body "..." --base main --head feat/l4-phase3-pr4-h-rm-h-qm-e2e --draft=false`
   - PR 编号预期 **#36**

---

## §4 验收清单（6 项）

1. **PR-4 commit** on `feat/l4-phase3-pr4-h-rm-h-qm-e2e` · commit message 含 PR-4 关键词
2. **test_handle_record_memory.py**：H-RM-E2E-001 移除 skip · 实装 apply + POST record + 验证 response
3. **test_handle_query_memory.py**：H-QM-E2E-001 移除 skip · 实装 apply 3 CR + POST query + 验证 filter
4. **本地 241/241 PASS**（基线 213 + PR-3 28 = 241）+ ruff 全绿 + pyright 0 errors
5. **5 项关键不变量 100% 保持**（单进程 / 60s timer / 共享 Deployment / 4 纯函数 / wire contract）
6. **PR #36 创建成功** · CI 8 项 check 全部 SUCCESS

---

## §5 风险与缓解（5 项）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | port-forward subprocess 残留（cleanup 失败） | 测试间互相干扰 | 严格 try/finally + subprocess.terminate + wait + kill -9 |
| 2 | JSON-RPC wire format 字段拼写错误（camelCase） | E2E 永远 ValidationError → -32602 | 复用 PR-1 单测 TEST-A2A 字段集合 · 参考 `tests/unit/knowledge_memory/api/` |
| 3 | kopf 60s timer E2E 慢（每次 60s+） | CI 跑 E2E 总时长超 15 min | e2e-envtest timeout-minutes=15 · E2E 仅在 labeled 触发 · 本地 + workflow 分离 |
| 4 | helm install rc=1 + port-forward 竞争 | 测试 flaky | port-forward 等 service 端口可连接（socket 探测） |
| 5 | H-QM 3 CR apply 后 60s timer race | 部分 CR 未 reconcile | 逐 CR kubectl wait observedGeneration >= 1 · timeout 120s |

---

## §6 5 项关键不变量保持（PR-4 验证）

| # | 不变量 | 验证方法 |
|---|---|---|
| 1 | 单进程（ADR-0006 D） | E2E 验证 helm install rc=1 · 单 pod · port-forward 到唯一 pod |
| 2 | 60s MemoryReconciler timer | E2E 验证 wait observedGeneration >= 1 timeout 120s · 60s + buffer |
| 3 | L3-5/L3-6 共享 Deployment | E2E 验证 deployment.yaml + service.yaml 完整 · 不新增 deployment |
| 4 | 4 纯函数数学不变 | PR-4 0 业务逻辑改动 · 仅 E2E 实装 · 4 纯函数单元测试覆盖 ≥ 95% |
| 5 | wire contract 不变（12 MEMORY_*） | PR-4 测试 JSON-RPC envelope 使用相同 wire 格式 · 错误码 0 = 成功 |

---

## §7 测试策略增量（PR-4）

| 层级 | Phase 3 PR-3 终态 | PR-4 增量 |
|---|---|---|
| UT | 85（JSON-RPC 4 + K8sBackend 8 + observability 4） | 0 |
| CF | 18（wire DTO + RBAC + 12 错误码 + JSON-RPC error 4） | 0 |
| IT | 24 | 0 |
| E2E | 35（LEADER 1 + LIFECYCLE 2 + skip 2 + 新增 ~30） | **+2**（H-RM-E2E-001 + H-QM-E2E-001 unskip） |
| DEPLOY/PERF | 5 | 0 |

**总测试增量**：PR-4 仅 unskip · +2 测试 ID 从 skipped → PASS

---

## §8 PR-4 启动检查清单

- [x] PR #30 (server) merged
- [x] PR #34 (K8sBackend) merged
- [x] PR #35 (25 metrics) merged
- [x] e2e-envtest.yml 完整（PR-4.1.1 #90 #91）
- [ ] PR-4 plan 文档（本文件 · 进行中）
- [ ] Subagent 接力实装（阶段 B · 35-45 min）
- [ ] 主 Agent 收口（阶段 C · 10 min）
- [ ] PR #36 创建

---

## M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-10 · #96 启动）
- **M.2 落地记录**：#96（2026-08-10 · PR-4 plan 文档完成 · 待阶段 B Subagent 接力）
- **M.3 关联 PR**：Phase 3 #30 + #34 + #35 + **#36 (PR-4 · 本 plan)**
- **M.4 下次会话入口**：#96 阶段 B Subagent 接力 → 阶段 C 主 Agent 收口 → #97 PR-5 文档同步
- **M.5 关注项台账**：
  - ① port-forward subprocess 清理（PR-4 收口前验证）
  - ② JSON-RPC wire format 字段一致性（PR-4 收口前 review）
  - ③ kopf 60s timer race（PR-4 收口前 per-CR observedGeneration 验证）
- **M.6 文档状态**：v0.1-draft 骨架稿（实装阶段 B 前完整 · 9 节 · ~12KB）

---

> **PR-4 启动就绪** · 2026-08-10 · 阶段 A 完成 · 阶段 B Subagent 接力启动