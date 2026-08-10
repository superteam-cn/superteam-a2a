# Phase 4 PR-1 Plan v0.1-draft · Hello Agent 完整实装

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-10 · #98 启动） |
| 上游 | Phase 3 4/4 PR merged（#30/#34/#35/#36）+ L3-4 v0.2.0 Spec (#61) + L3-2 a2a-core v0.2.0 (#54) |
| 下游 | Phase 4 PR-2~PR-5（Hello Agent Step 2 + Knowledge Service Step 1/2/3） |
| 关联 PR | Phase 4 PR-1 Hello Agent Step 1 · 本 plan（#98 启动） |
| main HEAD | `8d94464`（PR #37 merged）|

---

## §1 目标与边界

**目标**：实装 Hello Agent（Phase 4 第一个里程碑 · v0.1.0-beta 第一步）。

**5 文件级契约**（L3-4 v0.2.0 §1 + §2）：

| 文件 | 行数 | 关键依赖 |
|---|---|---|
| `__init__.py` | 8 | 仅导出 `app: ASGIApp` |
| `agent.py` | 50 | a2a-sdk `AgentExecutor` + `DefaultRequestHandler` + `anyio.to_thread.run_sync` |
| `card.py` | 40 | a2a-sdk `AgentCard/AgentCapabilities/AgentSkill` + `@lru_cache` |
| `observability.py` | 80 | prometheus-client + structlog + 双探针 + /metrics |
| `_internals.py` | 60 | test fixture + helper（仅包内 import）|

**7 Helm 模板**（L3-4 §5 + §9.9）：
- `Chart.yaml` + `values.yaml` + `values.schema.json`
- `templates/deployment.yaml`（单实例 + 双探针 + restricted SecurityContext）
- `templates/configmap.yaml`（5 env 注入）
- `templates/serviceaccount.yaml`（`automountServiceAccountToken: false`）
- `templates/networkpolicy.yaml`（ingress 同 namespace + egress DNS + 8080）
- `templates/servicemonitor.yaml`（interval 30s + honorLabels true）

**25 ID 测试**（L3-4 §10 + 6 层级金字塔镜像规则）：
- UT 11：HELLO-AGENT-001~005 + HELLO-CARD-001 + HELLO-OBS-001~003 + HELLO-INT-001~002
- DEPLOY 12：HELLO-DOCKER-001 + HELLO-HELM-001~007 + HELLO-DEPLOY-001~003
- E2E 3：HELLO-E2E-001~003（kind + helm + sendMessage → pong）

**不在范围**（明确剔除）：
- ❌ Dockerfile + Helm 模板实装（PR-2 Hello Agent Step 2 范围）
- ❌ Knowledge Service 实装（PR-3~PR-5 范围）
- ❌ Framework adapter 接入（v0.5+ 范围）
- ❌ 修改 L3-4 Spec（v0.2.0 已评审通过）

---

## §2 设计决策（5 项关键）

### §2.1 业务逻辑最简化

**Hello Agent 行为**：收到 A2A `sendMessage` → 返回固定字符串 `"pong"` · 无 LLM 依赖 · 无外部 framework。

**理由**：v0.1.0-beta 第一里程碑只需验证"A2A Agent 能跑通完整链路"（AgentCard + sendMessage + Task + Artifact + Stream placeholder）· LLM 集成推迟到 PR-2 之后。

### §2.2 单进程 ASGI server

**FastAPI + uvicorn**（与 L3-2 a2a-core 一致）：
- `agent.py: app = FastAPI(...)` 顶层导出
- uvicorn 在 main.py 中启动（参考 `services/knowledge-memory-service/src/.../main.py`）
- 与 kopf 共 event loop（D 方案 · ADR-0006 v1.0 Accepted）· 但 Hello Agent **无 kopf**（无 CRD reconcile · 纯 A2A server）

### §2.3 _task_store 单实例

`agent.py:_task_store: dict` 模块单例 + `_MAX_STORED_TASKS = 1024` FIFO 轮转。

**理由**：单进程架构下无需 Redis（OPEN-HELLO-002 已登记 v0.5+ 演进）。

### §2.4 observability 4 指标

L3-4 §9.7 锁定的 4 Python runtime 指标（与 L3-5 §9.7 15+5 = 20 指标区分）：
- `python_gc_objects_collected_total`（prometheus_client 默认）
- `process_cpu_seconds_total`
- `process_resident_memory_bytes`
- `process_open_fds`

**双探针**：`/healthz`（liveness）+ `/readyz`（readiness）+ `/metrics`（Prometheus scrape）· 端口 8080 共享。

### §2.5 测试 6 层级金字塔镜像

**UT 11 ≥ 90% 覆盖率** + **DEPLOY 12 镜像 helm + Dockerfile** + **E2E 3 kind + helm + sendMessage** · 与 L3-4 §10 测试策略 100% 一致。

---

## §3 实施步骤（3 阶段 · 接力模式）

### 阶段 A · 主 Agent 分支与计划（本次会话 · 已完成）

- ✅ git checkout main + pull --ff-only（HEAD `8d94464`）
- ✅ Subagent 调研 L3-4 + L3-5 Spec 完整画像
- ✅ 创建 6 项目 labels（phase1~4 + e2e + memory）
- ✅ 文档化 Branch Protection 修正指南（⑭ · 项目发起人 web 端 admin）
- 🚧 编写本 plan 文档（进行中）

### 阶段 B · Subagent 接力实装 PR-1（35-60 min · 本次会话后半段）

**Subagent 任务**：实装 5 Python 文件 + 25 ID 测试 + pyright/ruff 全绿 + commit + push

**Subagent 接力原则**（§16.1）：
- 主 Agent 仅调度 + 验证 + 收口
- Subagent 实装文件 + 验证 + commit
- 主 Agent 收口：push + gh pr create

### 阶段 C · 主 Agent 收口（10 min · 本次会话末尾）

1. push + gh pr create → PR #38
2. 等 CI 6 项 check 全绿（项目发起人手动合并 · ⑭ Branch Protection mismatch）
3. MEMORY.md 维护 + 启动 #99 入口

---

## §4 PR-1 验收清单（6 项）

1. ✅ 5 Python 文件创建（agent/card/observability/_internals/__init__）+ 25 ID 测试
2. ✅ uv workspace 配置（pyproject.toml + dependencies）
3. ✅ 241+N PASS（基线 241 + PR-1 新增 ~25 测试 ID）
4. ✅ ruff check All passed + ruff format OK + pyright 0 errors
5. ✅ 5 项关键不变量 100% 保持（Card-driven 单实例 + Python-first 边界 + observability 4 指标 + wire contract 12 MEMORY_* + 单进程 8080 端口）
6. ✅ PR #38 创建 + CI 6 项 check 5 SUCCESS + 1 SKIPPED

---

## §5 风险与缓解（5 项）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | a2a-sdk 上游 API 变更 | `AgentExecutor` / `DefaultRequestHandler` 接口变更 | uv.lock pin + dependabot 监控（ADR-0005 §13.6）|
| 2 | `_task_store` 单进程 race | 多 worker 部署时数据丢失 | L3-4 强约束 `replicaCount: 1` · Helm schema enum 强校验 |
| 3 | observability 4 指标命名漂移 | 与 L3-5 15+5 指标重名 | 严格使用 prometheus_client 默认 + 4 进程指标 · 不自定义 label |
| 4 | 双探针 + /metrics 端口共享 8080 | starlette ASGI path 冲突 | `Route("/healthz"...)` + `Route("/readyz"...)` + `Route("/metrics"...)` 显式注册 |
| 5 | Branch Protection ⑭ mismatch | CI 失败不阻断 merge | 项目发起人 web 端 admin · docs/admin/branch-protection-fix.md 已写 |

---

## §6 5 项关键不变量保持（PR-1 验证）

| # | 不变量 | 验证方法 |
|---|---|---|
| 1 | Card-driven 单实例 | Helm `values.schema.json: replicaCount.enum: [1]` 强约束 |
| 2 | Python-first 边界（无 framework 依赖） | pyproject.toml 仅依赖 a2a-sdk + fastapi + uvicorn + prometheus-client + structlog + opentelemetry |
| 3 | observability 4 指标 | observability.py 严格 4 指标 · pytest 验证 |
| 4 | wire contract 12 MEMORY_* | Hello Agent 不涉及 MEMORY_*（独立 Agent）· 0 错误码定义 |
| 5 | 单进程 8080 端口 | kopf 不使用（Hello Agent 纯 A2A server）· starlette ASGI 端口 8080 独占 |

---

## §7 测试策略增量（PR-1）

| 层级 | Phase 3 终态 | PR-1 增量 |
|---|---|---|
| UT | 85 | **+11**（HELLO-AGENT/CARD/OBS/INT） |
| CF | 18 | 0 |
| IT | 24 | 0 |
| E2E | 5（LEADER/LIFECYCLE/H-RM/H-QM）| **+3**（HELLO-E2E-001~003）|
| DEPLOY | 5 | **+12**（HELLO-DOCKER-001 + HELLO-HELM-001~007 + HELLO-DEPLOY-001~003）|
| PERF | 0 | 0 |

**PR-1 测试增量**：~25 ID / 6 层级金字塔镜像规则 / 4 重静态门禁 · 覆盖率 ≥ 90%

---

## §8 Phase 4 全 PR 序列（5 PR · 后续会话）

| PR | 标题 | 工作量 | 会话 |
|---|---|---|---|
| **#98 PR-1** | **Hello Agent Step 1**（5 Python + 25 测试） | 2 周 | 本会话 #98 |
| #99 PR-2 | Hello Agent Step 2（Dockerfile + 7 Helm + kind E2E） | 1 周 | #99 |
| #100 PR-3 | Knowledge Service Step 1（8 CRD types + 4 shared + 测试） | 1.5 周 | #100 |
| #101 PR-4 | Knowledge Service Step 2（12 service + 4 A2A handler + 23 错误码） | 2 周 | #101 |
| #102 PR-5 | Knowledge Service Step 3（7 Helm + RBAC + kind E2E） | 1 周 | #102 |

**Phase 4 总工作量**：~3700 行 / 5 PR / 6-8 周集中（2h/day）· 与用户选项 A 完全一致。

---

## M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-10 · #98 启动）
- **M.2 落地记录**：#98（2026-08-10 · 6 labels 创建 + branch-protection-fix 文档化 + L3-4/L3-5 调研完成 + PR-1 plan 文档完成）
- **M.3 关联 PR**：Phase 4 PR-1 Hello Agent Step 1 · 本 plan（PR #38 待启动）
- **M.4 下次会话入口**：#98 阶段 B Subagent 接力实装 → 阶段 C 主 Agent 收口 → #99 PR-2 Hello Agent Step 2（Dockerfile + 7 Helm 模板）
- **M.5 关注项台账**：
  - ① ⑭ Branch Protection mismatch（项目发起人 web 端 admin · docs/admin/branch-protection-fix.md）
  - ② a2a-sdk 上游 API 变更（ADR-0005 §13.6 pin + dependabot）
  - ③ _task_store 单进程 race（L3-4 `replicaCount: 1` schema enum 强约束）
- **M.6 文档状态**：v0.1-draft 骨架稿（实装前完整 · 8 节 · ~14KB）

---

> **PR-1 启动就绪** · 2026-08-10 · 阶段 A 完成 · 阶段 B Subagent 接力启动