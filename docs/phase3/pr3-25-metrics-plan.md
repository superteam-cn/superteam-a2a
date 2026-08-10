# Phase 3 PR-3 25 指标 ServiceMonitor 实装 Plan

> **目标**：实装 Operator `/metrics` 端口 + 25 指标（10 Memory 业务 + 15 L3-2 复用）+ ServiceMonitor scrape 真实可观测性验证
> **依据**：[L4-Phase3 plan v0.1-draft §3 PR-3](./l4-phase3-plan.md) + L3-6 §7 Observability + L3-2 §9.1 15 Prometheus 指标 + L3-6 §9.7 PrometheusRule + L3-6 §9.8 ServiceMonitor
> **分支**：`feat/l4-phase3-pr3-25-metrics`（已创建自 `8cab684`）
> **预计工作量**：45-60 min · Subagent 接力模式（与 #79/#80/#94 一致）
> **基线**：213/213 PASS in 1.11s · ruff 0 · pyright 0

---

## §1 关键参考

| 文件 | 用途 |
|---|---|
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/main.py` | 入口：需新增 `_run_metrics_server()` 与 `_amain()` 协调整合 |
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/api/server.py` | starlette app factory：需新增 `/metrics` GET route + `prometheus_client` 集成 |
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/observability/`（新） | 10 Memory 业务指标定义（Counter/Histogram/Gauge + labels） |
| `services/knowledge-memory-service/pyproject.toml` | 需新增 `prometheus-client>=0.20,<1` 依赖 |
| `helm/knowledge-memory-service/templates/servicemonitor.yaml` | 已有 `port: http` + `/metrics` + regex（5 命名空间）· 需验证/微调 |
| `helm/knowledge-memory-service/templates/prometheusrule.yaml` | 已有 8 alerts（与 25 指标对齐）· 需验证 metric name 精确匹配 |
| `helm/knowledge-memory-service/values.yaml` | `serviceMonitor.enabled` / `prometheusRule.enabled` / `service.targetPort` 8080 |
| `docs/spec/L3-file-specs/L3-memory-backend.md §7.1 line 1047-1060` | 10 Memory 业务指标权威表（name/type/labels/help/buckets） |
| `docs/spec/L3-file-specs/L3-a2a-core.md §9.1 line 1295-1309` | 15 L3-2 复用指标权威表（11 A2A + 4 Python runtime） |
| `docs/spec/L3-file-specs/L3-memory-backend.md §9.7 line 1385-1486` | PrometheusRule 8 alerts + labels 完整 YAML |
| `docs/spec/L3-file-specs/L3-memory-backend.md §9.8 line 1490-1507` | ServiceMonitor spec + metricRelabelings regex |
| `docs/spec/L3-file-specs/L3-memory-backend.md §10.2 line 1060` | `OBS-MEM-UT-001~010` 验证 + `OBS-MEM-IT-001` 验证 25 指标聚合 |

---

## §2 范围边界（明确）

### 在范围（PR-3 必做）

- ✅ **新增 `prometheus-client>=0.20,<1` 依赖**（pyproject.toml dependencies）
- ✅ **新增 `services/.../observability/` 子包**（4 文件 · ~150-200 行）：
  - `__init__.py`：公共 API surface（10 指标 + bind_metrics_to_app helper）
  - `metrics.py`：10 Memory 业务指标定义（Counter/Histogram/Gauge + 标签枚举）
  - `labels.py`：封闭枚举类（Phase/Result/GCState/Visibility/ScopeLevel/Validator/Method/PrincipalType）
  - `binding.py`：`bind_metrics_to_app(app: Starlette) -> None` — 注册 `/metrics` GET route（返回 `generate_latest()` 内容）
- ✅ **starlette `/metrics` 端口**（PR-1 已存在 starlette app）：
  - 复用 port 8080（D 方案单进程）
  - 新增 `Route("/metrics", metrics_endpoint, methods=["GET"])` 返回 `Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)`
- ✅ **10 业务指标 binding hook**（最小占位实现，PR-3 验证 25 指标可见）：
  - Counter/Histogram 在 module import 时实例化（prometheus_client 默认 REGISTRY）
  - Gauge 同理
  - **不实装 4 纯函数 + reconciler 中真实埋点**（仅定义指标 + 验证 `/metrics` 聚合可见）
  - **占位**：`superteam_memory_reconcile_total` + `superteam_memory_bm25_index_size` 在 `_build_memo()` 各 +1 调用一次（确保非空 metric）
- ✅ **helm values.yaml** 微同步：
  - `serviceMonitor.interval` + `serviceMonitor.scrapeTimeout` 已在（验证）
  - `prometheusRule.enabled` 已在（验证）
- ✅ **ServiceMonitor 模板** 微同步：
  - 当前 `metricRelabelings` regex 已包含 5 命名空间（`superteam_a2a_.*|superteam_knowledge_.*|superteam_memory_.*|python_.*|process_.*`）
  - **注**：当前是 5 命名空间 = `superteam_a2a_.*`（11 A2A）+ `superteam_knowledge_.*`（L3-5 0 指标，本服务无）+ `superteam_memory_.*`（10 Memory）+ `python_.*`（4 L3-2 实际是 `superteam_python_*` 但 L3-6 §9.8 仍叫 python_*）+ `process_.*`（python runtime 兜底）
  - **关键修复**：`python_.*` 应改为 `superteam_python_.*`（实际 L3-2 §9.1 line 1306-1309 名称是 `superteam_python_*`）
- ✅ **15-25 测试 ID**：
  - 10 单元测试（`OBS-MEM-UT-001~010`）：逐项验证 name/type/labels/help/buckets
  - 5 集成测试（`OBS-MEM-IT-001~005`）：
    - IT-001: `/metrics` 聚合 25 个指标（10 Memory + 11 A2A + 4 Python runtime）
    - IT-002: 无高基数 label（禁 `memory_name`/`service_account`/`scope_name`/`request_id`）
    - IT-003: ServiceMonitor regex 5 命名空间全部覆盖
    - IT-004: PrometheusRule 8 alerts metric name 精确匹配
    - IT-005: bind_metrics_to_app 单进程 / 跨进程隔离（无重复注册）
- ✅ **验证**：228-233/233 pytest PASS（基线 213 + 15 新增）· ruff/format/pyright 全绿
- ✅ **PR 创建**（draft=false）+ CI 8 项 check 全绿

### 不在范围（PR-3 边界外）

- ❌ reconciler / admission / index 中真实埋点（待 L4-Phase4 单独 PR · 25 指标 * 1 埋点 = 大工作量）
- ❌ K8sBackend 25 指标埋点（PR-2 已合并 · 真实持久化路径埋点待 Phase 4）
- ❌ Kind cluster + Prometheus operator E2E（PR-4 单独 · 本 PR 仅 helm template 验证）
- ❌ Performance PERF 10K/50K 门禁（Phase 4 单独）
- ❌ H-RM/H-QM-E2E（PR-4 单独）
- ❌ Multi-replica / sharding（OPEN-MEMORY-002 v0.5+）
- ❌ Vector DB backend（OPEN-MEMORY-003 v0.5+）
- ❌ Grafana dashboard JSON（PR-5 文档同步可选）
- ❌ 8 alerts 真实触发测试（kind + Prometheus + alertmanager · PR-4 或独立 PR）

---

## §3 设计决策（5 项关键）

### §3.1 `/metrics` 端口选择 — 复用 8080（D 方案单进程）

- **starlette app 新增 Route**（与 /healthz / /jsonrpc/* 同端口 8080）
- ✅ 0 端口新增 · 0 RBAC 变更 · 0 deployment template 变更
- ✅ ServiceMonitor 现有 `port: http` 自动发现
- ✅ 单一 ServiceMonitor scrape 25 指标（HELM-DEPLOY-007 验证项）
- ❌ 需 prometheus_client `generate_latest()` 在 starlette 同步路径执行（验证是否阻塞 event loop）

### §3.2 prometheus_client 集成模式

- **使用 prometheus_client 默认 REGISTRY**（单实例 · 适合单进程 D 方案）
- 模块 import 时即注册 10 指标
- `/metrics` 端点调用 `generate_latest()` 返回 bytes
- 优势：0 自定义 Collector · 0 线程安全顾虑 · 符合 prometheus_client 推荐模式
- 关键：测试用 `prometheus_client.REGISTRY` 快照断言（避免与全局状态耦合）

### §3.3 10 业务指标的 labels 封闭枚举

- **强类型枚举类**（StrEnum · 8 个 label 维度）：
  - `Phase = {"admit", "reconcile", "finalize"}`
  - `Result = {"success", "error", "conflict", "cancelled"}`
  - `GCState = {"expired", "archived", "superseded"}`
  - `Visibility = {"private", "team", "org", "industry"}`
  - `ScopeLevel = {"agent", "team", "org", "industry", "global"}`
  - `Validator = {"schema", "scope", "content", "rate"}`
  - `Method = {"record_memory", "query_memory"}`
  - `PrincipalType = {"service_account", "user", "agent"}`
- 强制调用方传枚举（label 值不通过 string 直接传）· 防止高基数 label
- L3-6 §7.1 line 1060 明确禁止 `memory_name`/`service_account`/`scope_name`/`request_id` 进入 label

### §3.4 ServiceMonitor metricRelabelings regex 修复

- **当前**（helm/knowledge-memory-service/templates/servicemonitor.yaml line 37）：
  ```yaml
  regex: 'superteam_a2a_.*|superteam_knowledge_.*|superteam_memory_.*|python_.*|process_.*'
  ```
- **问题**：`python_.*` 不匹配 `superteam_python_*`（L3-2 §9.1 line 1306-1309 实际是 `superteam_python_*`）
- **修复**：
  ```yaml
  regex: 'superteam_a2a_.*|superteam_knowledge_.*|superteam_memory_.*|superteam_python_.*|process_.*'
  ```
- 影响：4 个 Python runtime 指标当前会被 drop · 修复后纳入
- 5 命名空间 100% 覆盖：11 A2A + 0 L3-5（operator 内嵌业务） + 10 Memory + 4 Python + 0 process_*

### §3.5 PrometheusRule 8 alerts metric name 验证

- 当前 prometheusrule.yaml 引用：
  - `superteam_knowledge_query_latency_seconds_bucket` ✓
  - `superteam_knowledge_bm25_index_size` ⚠️（当前服务无此 metric · 待 Phase 4 L3-5 实装）
  - `superteam_knowledge_memory_conflict_total` ⚠️（同上）
  - `superteam_knowledge_admission_duration_seconds_bucket` ⚠️（同上）
  - `superteam_memory_reconcile_total` ✓（PR-3 定义）
  - `superteam_memory_reconcile_duration_seconds_bucket` ✓（PR-3 定义）
  - `up{job="knowledge-service"}` ✓
- **结论**：本 PR 仅验证 metric name 已注册（占位 metric，无值）· 真实触发待 Phase 4 业务埋点
- **不修改 PrometheusRule**（避免引入新 PR 范围）· 验证项 IT-004 仅断言 metric name 存在于 `/metrics` 输出

---

## §4 实施步骤（5 阶段）

### 阶段 A · Subagent 启动（5 min）

- 读取本 plan + §1 关键参考
- 验证环境：`python -m uv run pytest tests/unit tests/conformance` 应通过 213/213
- 验证 helm chart: `helm template ./helm/knowledge-memory-service --set serviceMonitor.enabled=true --set prometheusRule.enabled=true | grep -c "kind: ServiceMonitor"` 应 = 1

### 阶段 B · 10 指标定义 + observability 子包（20-25 min）

1. **新增 `prometheus-client>=0.20,<1` 依赖**（pyproject.toml dependencies）
   - `python -m uv lock` 更新 uv.lock

2. **新增 `observability/` 子包**（4 文件 · ~150-200 行）：
   - `__init__.py`：导出 10 指标 + `bind_metrics_to_app`
   - `labels.py`：8 个 StrEnum 封闭枚举
   - `metrics.py`：10 个 Counter/Histogram/Gauge 实例化（按 L3-6 §7.1 line 1047-1060 权威表）
   - `binding.py`：`bind_metrics_to_app(app: Starlette) -> None` — 注册 `/metrics` GET route
3. **关键**：Histogram bucket 严格按 L3-6 §7.1 buckets 列
   - reconcile_duration: `.005,.01,.025,.05,.1,.25,.5,1,2.5,5,10,30,50`
   - admission_duration: `.001,.0025,.005,.01,.025,.05,.1,.25,.5,1,2.5,5`
4. **占位埋点**（最小可观测性）：
   - 在 `_build_memo()` 中：
     - `MEMORY_RECONCILE_TOTAL.labels(phase="admit", result="success").inc()` 1 次
     - `MEMORY_PROMOTION_ELIGIBLE.labels(visibility="team").set(0)` 1 次
     - `MEMORY_BM25_INDEX_SIZE.labels(scope_level="agent").set(0)` 1 次
   - 保证 `/metrics` 输出非空（Counter `_total` + Gauge 值）

### 阶段 C · starlette `/metrics` 集成（10 min）

1. **更新 `services/.../api/server.py` `create_app()`**：
   - 新增 `Route("/metrics", metrics_endpoint, methods=["GET"])`
   - metrics_endpoint handler:
     ```python
     from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


     async def metrics_endpoint(request: Request) -> Response:
         return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
     ```
2. **导出 `metrics_endpoint` + `bind_metrics_to_app` 公共 API**
3. **PR-3 集成路径选择**（2 选 1）：
   - **方案 A**（推荐）：metrics_endpoint 直接定义在 server.py 内（与 healthz / jsonrpc_* 同一 file）
   - **方案 B**（备选）：bind_metrics_to_app 在 server.create_app 内部调用
   - **采用 A**（更显式 · 复用现有 Route 模式）

### 阶段 D · helm 模板微同步 + 测试（15-20 min）

1. **修复 `helm/knowledge-memory-service/templates/servicemonitor.yaml`**：
   - `regex` line 37: `python_.*` → `superteam_python_.*`
   - 注释更新：明确 5 命名空间（11 + 0 + 10 + 4 + 0 = 25 指标）
2. **验证 `helm/knowledge-memory-service/templates/prometheusrule.yaml`**：
   - 8 alerts metric name 与 25 指标集合对齐（不修改）
3. **新增 `tests/unit/knowledge_memory/observability/`**（3 文件 · ~300-400 行）：
   - `test_labels.py`：8 枚举封闭性测试（label 取值集合 = 固定）
   - `test_metrics.py`：10 单元测试（`OBS-MEM-UT-001~010`）：
     - name 精确匹配 L3-6 §7.1
     - type 正确（Counter/Histogram/Gauge）
     - labels 维度正确
     - help text 包含
     - histogram buckets 精确匹配
   - `test_binding.py`：5 集成测试（`OBS-MEM-IT-001~005`）：
     - IT-001: starlette TestClient GET /metrics → 200 + 25 指标
     - IT-002: labels 集合 = 封闭枚举（无高基数）
     - IT-003: ServiceMonitor regex 5 命名空间完整覆盖
     - IT-004: PrometheusRule 8 alerts metric name 在 /metrics 中
     - IT-005: 跨进程隔离（不修改全局 REGISTRY · 测试用独立 CollectorRegistry）
4. **新增 `tests/unit/knowledge_memory/api/test_metrics_endpoint.py`**（~50 行）：
   - `TEST-A2A-013`: GET /metrics → 200 + text/plain content type
   - `TEST-A2A-014`: GET /metrics 内容包含 `superteam_memory_reconcile_total` 等 10 个 name
   - `TEST-A2A-015`: GET /metrics 内容包含 `superteam_a2a_rpc_total` 等 L3-2 11 个 name

### 阶段 E · 验证 + PR（10-15 min）

1. **本地验证**：
   ```bash
   python -m uv run pytest tests/unit tests/conformance  # 期望 228-233/233 PASS
   python -m uv run ruff check .                          # All checks passed
   python -m uv run ruff format --check .                 # 全部 formatted
   python -m uv run pyright                                # 0 errors
   helm template ./helm/knowledge-memory-service --set serviceMonitor.enabled=true --set prometheusRule.enabled=true | grep -E "kind: (ServiceMonitor|PrometheusRule)"
   ```
2. **commit 收口**：
   ```bash
   git add -A
   git commit -m "feat(phase3): PR-3 25 指标 ServiceMonitor 实装 (#35)

   - observability/ 子包：10 Memory 业务指标（Counter/Histogram/Gauge）
   - starlette /metrics GET route：generate_latest() 返回 prometheus text format
   - 15 测试 ID（10 UT + 5 IT）· 验证 25 指标聚合 + labels 封闭性
   - ServiceMonitor regex 修复：python_.* → superteam_python_.*
   - 5 项关键不变量 100% 保持（单进程 / 60s timer / 共享 Deployment / 4 纯函数 / wire contract）
   - 228-233/233 PASS + ruff/format/pyright 全绿"
   ```
3. **push + 创建 PR**：
   ```bash
   git push -u origin feat/l4-phase3-pr3-25-metrics
   gh pr create --title "feat(phase3): PR-3 25 指标 ServiceMonitor 实装" --body "..." --base main
   ```
4. **报告**：PR URL + 测试结果 + 等待 CI 8 项 check + 项目发起人合并

---

## §5 5 项关键不变量保持（PR-3 范围）

| # | 不变量 | 保持要求 |
|---|---|---|
| 1 | 单进程（ADR-0006 D 方案）| /metrics 复用 starlette 8080 · 0 新增端口 · 0 新增进程 |
| 2 | 60s MemoryReconciler timer | /metrics 独立 endpoint · 不影响 reconciler 周期 |
| 3 | L3-5/L3-6 共享 Deployment | deployment.yaml 0 改动 · ServiceMonitor 1 行 regex 修复 |
| 4 | 4 纯函数数学不变 | pure.py 0 改动 · /metrics 仅埋点入口 |
| 5 | wire contract 不变 | 12 MEMORY_* 错误码 1:1 映射 · TEST-MEM-051 持续 PASS |

---

## §6 测试策略增量

| 层级 | Phase 3 PR-2 终态 | PR-3 增量 |
|---|---|---|
| UT | 97 + 15 (PR-2 K8sBackend) = 112 | + 10 (OBS-MEM-UT-001~010) + 3 (TEST-A2A-013~015) = 125 |
| CF | 26 + 4 (PR-2 contract) = 30 | + 5 (OBS-MEM-IT-001~005) = 35 |
| IT | 24 | + 0（mock 替代 envtest）|
| E2E | 35 (Phase 2) | + 0（PR-4 单独）|
| DEPLOY/PERF | 5 | + 0（PR-4 单独）|

**总测试增量**：18 测试 ID（PR-3）· 基线 213 → 228-233 PASS

---

## §7 Subagent 隔离建议

- **是否需要 worktree**：**否**（与 #80 #82 #94 一致 · 串行实装）
- **Subagent 类型**：general-purpose
- **隔离要求**：严格按 §4 阶段 B/C/D 执行 · 不修改 pure.py · 不修改 protocol.py · 不修改 reconciler · 不修改 admission
- **commit 前必传**：`git status` + `git diff --stat` 输出，确认文件范围匹配

---

## §8 收口验证（主 Agent）

1. 接收 Subagent commit 后 fast-forward 本地 feat/l4-phase3-pr3-25-metrics
2. 跑完整验证（pytest/ruff/format/pyright + helm template）
3. 推送 + 创建 PR
4. CI 8 项 check 等待 success
5. PR description 填写 + 项目发起人合并

---

## §9 风险与缓解

| # | 风险 | 缓解 |
|---|---|---|
| 1 | prometheus_client 引入新依赖 | 已加 `prometheus-client>=0.20,<1` · 与 starlette/uvicorn 无冲突 |
| 2 | starlette /metrics generate_latest() 阻塞 event loop | prometheus_client 是 C 扩展 + 内存读 · 微秒级 · 单进程 25 指标安全 |
| 3 | ServiceMonitor regex python_.* 漏匹配 | 修复为 `superteam_python_.*` · 阶段 D 步骤 1 |
| 4 | PrometheusRule 8 alerts metric 缺失 | 当前是占位 · 真实埋点 Phase 4 · PR-3 仅验证 metric name 注册 |
| 5 | 10 指标 labels 高基数 | 8 封闭 StrEnum · 强制类型检查 · 防止 string 注入 |
| 6 | 与 K8sBackend (PR-2) 协同 | K8sBackend 0 metrics 改动 · /metrics 独立 endpoint |
| 7 | 与 A2A HTTP (PR-1) 协同 | /metrics 复用 starlette 8080 · 0 端口新增 |
| 8 | Subagent 超时 | 阶段 B/C 必在 30 min 内 · 超时则主 Agent 收尾 |
| 9 | pyright 与 prometheus_client 类型 | prometheus_client 0.20+ 内含 py.typed · 0 errors 期望 |
| 10 | 25 指标聚合顺序不稳定 | prometheus_client 不保证顺序 · 测试用 set 断言 |

---

## §M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-10 · #95 启动）
- **M.2 落地记录**：#95（2026-08-10 · PR-3 启动 · Subagent 接力实装 25 指标）
- **M.3 关联 PR**：Phase 2 #22-#28 + #29 hotfix + Phase 3 #30-#34 + **#35 PR-3 25 指标 ServiceMonitor**（待启动）
- **M.4 下次会话入口**：#96 PR-4 H-RM/H-QM-E2E（45-60 min · 复用 PR-1 server + PR-2 K8sBackend + PR-3 metrics）
- **M.5 关注项台账**：
  - ① 25 指标 100% 可见（PR-3 收口前 IT-001 验证）
  - ② ServiceMonitor regex 修复（python_.* → superteam_python_.* · 阶段 D 步骤 1）
  - ③ PrometheusRule 8 alerts metric name 与 /metrics 对齐（IT-004 验证）
  - ④ 5 项关键不变量 100% 保持（pure.py 0 改动 + 12 MEMORY_* 不变）
  - ⑤ Branch Protection check 名 mismatch（⑭ · web 端 admin · PR-3 不依赖但收口后建议修复）
- **M.6 文档状态**：v0.1-draft 骨架稿（9 节 · ~12KB）
