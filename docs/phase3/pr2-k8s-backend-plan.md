# Phase 3 PR-2 K8sBackend 实装 Plan

> **目标**：实装 `K8sBackend` 完整实现，替换 InMemoryBackend 作为可选生产 backend
> **依据**：[L4-Phase3 plan v0.1-draft §3 PR-2](./l4-phase3-plan.md) + L3-6 §5.7 MemoryBackend Protocol
> **分支**：`feat/l4-phase3-pr2-k8s-backend`（已创建自 `870c9f1`）
> **预计工作量**：90-120 min · Subagent 接力模式（与 #79/#80/#82 一致）

---

## §1 关键参考

| 文件 | 用途 |
|---|---|
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/backend/protocol.py` | MemoryBackend Protocol 6 抽象方法 + 5 项不变量 |
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/backend/in_memory.py` | InMemoryBackend 完整实装（**核心参考模板**） |
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/backend/types.py` | 6 个 Result 类型（Put/Get/Delete/List）+ BackendType/BackendHealth/BackendMetadata |
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/backend/pure.py` | 4 纯函数（**不修改 · 复用**） |
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/backend/errors.py` | MemoryErrorCode 12 个 + MemoryBackendError 异常 |
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/backend/memory.py` | Memory 顶层 CRD（API + spec + status） |
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/reconciler/k8s_lease_leader_elector.py` | K8s API 客户端使用模板（lazy import + 异常映射） |
| `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/main.py` | `_build_memo()` — 需在 backend 字段切换点新增 K8sBackend 选择 |
| `helm/knowledge-memory-service/values.yaml` | 需新增 `backend` enum (in_process/k8s) + K8sBackend 相关 config |

---

## §2 范围边界（明确）

### 在范围（PR-2 必做）
- ✅ `k8s_backend.py` 新文件（~250-300 行）—— CustomObjectsApi wrapper
- ✅ K8sBackend 类实现 6 抽象方法（put/get/delete/list/patch_status/health/metadata）
- ✅ 错误码 1:1 映射 K8s API 异常（K8sApiError → MemoryBackendError 12 码）
- ✅ 4 纯函数 `pure.py` **不修改**（必须保持数学不变 — §5.7 不变量 5）
- ✅ helm values.yaml 新增 `backend` 字段（enum: in_process/k8s，默认 in_process）
- ✅ main.py `_build_memo()` 根据 backend 字段选 backend 实现
- ✅ 8-12 测试 ID（4 mock K8s API IT + 4 wire 一致性 + 4 round-trip）
- ✅ 验证：199-203/203 pytest PASS（基线 191 + 8-12 新增）
- ✅ ruff/format/pyright 全绿
- ✅ backend selection logic 测试（_build_memo 单测）
- ✅ PR 创建（draft=false）+ CI 全绿

### 不在范围（PR-2 边界外）
- ❌ K8sBackend RBAC 权限（待 L4 Phase 4 单独 PR）— 仅在 helm values.yaml 注释标注
- ❌ CRD 12 字段 schema 校验增强（已在 operator/ 单独维护）
- ❌ Multi-replica / sharding（OPEN-MEMORY-002 v0.5+ 推迟）
- ❌ Vector DB backend（OPEN-MEMORY-003 v0.5+ 独立）
- ❌ K8sBackend 性能 PERF 验证（10K/50K · PR-5 文档同步后单独 PR）
- ❌ 25 指标 ServiceMonitor（PR-3 单独）
- ❌ H-RM/H-QM-E2E（PR-4 单独）

---

## §3 设计决策（5 项关键）

### §3.1 K8sBackend 用 CustomObjectsApi（不是专用 client）

- **CustomObjectsApi.create_namespaced_custom_object / get / list / patch**
- ✅ 复用 operator/ 已注册的 Memory CRD schema（无新 CRD）
- ✅ 与 kopf reconcile 兼容（kopf 写 CR → K8sBackend 读 CR · 同 API）
- ❌ 不能绕过 webhook（生产由 ValidatingAdmissionWebhook 校验）

### §3.2 list 使用 label selector 优化

- LIST 不拉全 namespace 所有 Memory CR（性能差）
- **Memory CR metadata.labels** 携带 `scope.industry / scope.org / scope.team / scope.project / agentRef.name`
- K8sBackend list 用 label selector 过滤
- L3-6 §3.2 ObjectMeta.labels 已支持（max 64）
- **关键**：record_memory_async 调用方需在 metadata.labels 写入这些标签

### §3.3 patch_status 用 strategic merge patch

- K8s API `patch_namespaced_custom_object_status` （带 `_status` 后缀）
- body 格式：strategic merge patch（merge key 自动）
- generation CAS：客户端先 get 读 resourceVersion → patch 携带 `metadata.resourceVersion` → K8s server 校验

### §3.4 错误码映射矩阵

| K8s API 状态 | MemoryErrorCode | retryable | 说明 |
|---|---|---|---|
| 404 (GET) | (返回 None，不算 MEMORY_*) | - | not found 由 handler 决定 |
| 409 (PUT 创建冲突) | MEMORY_INTERNAL_ERROR | True | 已存在需走 update |
| 404 (PUT 创建) | - | - | 走 create 路径 |
| 422 (validation) | MEMORY_INVALID_CONTENT | False | schema 错 |
| 403 (RBAC) | MEMORY_FORBIDDEN | False | 权限不足 |
| 429 (rate limit) | MEMORY_RATE_LIMIT | True | Retry-After 解析 |
| 5xx | MEMORY_INTERNAL_ERROR | True | 1/2/4/8s backoff |
| asyncio.TimeoutError | MEMORY_ADMISSION_TIMEOUT | True | 超时 |
| 其他 | MEMORY_INTERNAL_ERROR | False | unknown |

### §3.5 helm values.yaml `backend` field

```yaml
# helm/knowledge-memory-service/values.yaml
backend:
  # L4-Phase3 PR-2: MemoryBackend implementation
  # - in_process: dict-backed (default, dev/CI)
  # - k8s: CustomObjectsApi (production)
  type: in_process
  k8s:
    # 仅 type=k8s 时生效
    crdGroup: memory.superteam-a2a.io
    crdVersion: v1alpha1
    crdPlural: memories
    # K8sBackend list query timeout
    listTimeoutSeconds: 30
```

---

## §4 实施步骤（5 阶段）

### 阶段 A · Subagent 启动（5 min）
- 读取本 plan + §1 关键参考
- 验证环境：`python -m uv run pytest tests/unit tests/conformance` 应通过 191/191

### 阶段 B · K8sBackend 实装（40-50 min）
1. **新建 `k8s_backend.py`**（~250-300 行）
   - `class K8sBackend:` 实现 6 抽象方法
   - 内部 lazy init `kubernetes_asyncio.client.CustomObjectsApi`（借鉴 K8sLeaseLeaderElector._ensure_kube_client 模式）
   - 错误码映射：1 个内部 helper `_map_k8s_error(e: Exception) -> MemoryBackendError`
   - metadata 返回 BackendType.K8S（BackendType 需扩展）
   - import `pure` 模块的 4 纯函数（**必须复用 · 不重写**）
2. **扩展 `types.py`** BackendType enum
   - `K8S = "k8s"`（与 helm values 一致）
3. **更新 `__init__.py`** 导出 K8sBackend
4. **更新 `main.py`** `_build_memo()`
   - 读 helm value `BACKEND_TYPE` env var（K8s ConfigMap 注入）
   - `if backend == "k8s": return K8sBackend(...) else: return InMemoryBackend(...)`

### 阶段 C · Helm 集成（10 min）
1. **更新 `helm/knowledge-memory-service/values.yaml`**
   - 新增 `backend.type` + `backend.k8s` 字段
2. **更新 `helm/knowledge-memory-service/templates/deployment.yaml`**（如需 ConfigMap env var 注入）
   - `env: - name: BACKEND_TYPE valueFrom: configMapKeyRef: ...`

### 阶段 D · 测试（25-30 min）
1. **新建 `tests/unit/knowledge_memory/backend/test_k8s_backend.py`**（~300-400 行）
   - 使用 `unittest.mock.AsyncMock` mock CustomObjectsApi
   - 8-12 测试 ID（命名 `TEST-K8S-BE-001~012`）：
     - **mock K8s API IT（4）**：
       - TEST-K8S-BE-001: PUT 创建（201 → success）+ 不重复创建
       - TEST-K8S-BE-002: PUT 更新（200 → version 递增）
       - TEST-K8S-BE-003: GET 命中（200 → 返回 Memory）
       - TEST-K8S-BE-004: GET 未命中（404 → 返回 None）
     - **wire 一致性（4）**：
       - TEST-K8S-BE-005: 422 → MEMORY_INVALID_CONTENT 映射
       - TEST-K8S-BE-006: 403 → MEMORY_FORBIDDEN 映射
       - TEST-K8S-BE-007: 429 → MEMORY_RATE_LIMIT（retryable=True）
       - TEST-K8S-BE-008: 5xx → MEMORY_INTERNAL_ERROR（retryable=True）
     - **round-trip（4）**：
       - TEST-K8S-BE-009: put → get round-trip
       - TEST-K8S-BE-010: put → list 命中
       - TEST-K8S-BE-011: put → patch_status CAS 成功
       - TEST-K8S-BE-012: put → patch_status generation 不匹配 → MEMORY_INTERNAL_ERROR
2. **更新 `tests/unit/knowledge_memory/test_main_memo.py`**
   - 新增 test: backend=k8s → 返回 K8sBackend 实例
   - 新增 test: backend=in_process → 返回 InMemoryBackend 实例（已有）
3. **更新 `tests/conformance/test_memory_backend_contract.py`**（如存在）
   - K8sBackend 必须通过同一 contract suite（与 InMemoryBackend 等价行为）

### 阶段 E · 验证 + PR（15-20 min）
1. **本地验证**：
   ```bash
   python -m uv run pytest tests/unit tests/conformance  # 期望 199-203/203 PASS
   python -m uv run ruff check .                          # All checks passed
   python -m uv run ruff format --check .                 # 全部 formatted
   python -m uv run pyright                                # 0 errors
   ```
2. **commit 收口**：
   ```bash
   git add -A
   git commit -m "feat(phase3): PR-2 K8sBackend 完整实装 (#34)

   - K8sBackend CustomObjectsApi wrapper（6 抽象方法 + 12 错误码映射）
   - 复用 4 纯函数（pure.py 不修改 · §5.7 不变量 5）
   - helm values.yaml backend.type enum (in_process/k8s)
   - main.py _build_memo() 根据 env var 选择 backend
   - 8-12 测试 ID（4 mock K8s API IT + 4 wire + 4 round-trip）
   - 199-203/203 PASS + ruff/format/pyright 全绿
   - 5 项关键不变量 100% 保持"
   ```
3. **push + 创建 PR**：
   ```bash
   git push -u origin feat/l4-phase3-pr2-k8s-backend
   gh pr create --title "feat(phase3): PR-2 K8sBackend 完整实装" --body "..." --base main
   ```
4. **报告**：PR URL + 测试结果 + 等待 CI 8 项 check + 项目发起人合并

---

## §5 5 项关键不变量保持（PR-2 范围）

| # | 不变量 | 保持要求 |
|---|---|---|
| 1 | 单进程（ADR-0006 D 方案）| K8sBackend 同进程内 kopf + starlette + CustomObjectsApi · 0 IPC 边界 |
| 2 | 60s MemoryReconciler timer | K8sBackend 不影响 reconciler timer 周期（仅 storage 实现替换） |
| 3 | L3-5/L3-6 共享 Deployment | helm values.yaml 仅新增 backend config · deployment 模板不变 |
| 4 | 4 纯函数数学不变 | pure.py 0 改动 · K8sBackend 委托 pure.py 调用 |
| 5 | wire contract 不变 | 12 MEMORY_* 错误码 1:1 映射 K8s API 异常 · TEST-MEM-051 持续 PASS |

---

## §6 测试策略增量

| 层级 | Phase 3 PR-1 终态 | PR-2 增量 |
|---|---|---|
| UT | 73 + 12 (PR-1 JSON-RPC) = 85 | + 12 (K8sBackend mock 8 + backend selection 2 + list label selector 2) = 97 |
| CF | 18 + 4 (PR-1) = 22 | + 4 (K8sBackend contract suite) = 26 |
| IT | 24 | + 0（mock 替代 envtest） |
| E2E | 35 (Phase 2) | + 0（PR-4 单独） |
| DEPLOY/PERF | 5 | + 0（PR-5 单独） |

**总测试增量**：16 测试 ID（PR-2）

---

## §7 Subagent 隔离建议

- **是否需要 worktree**：**否**（与 #80 #82 一致 · 串行实装）
- **Subagent 类型**：general-purpose
- **隔离要求**：严格按 §4 阶段 B/C/D 执行 · 不修改 pure.py · 不修改 protocol.py
- **commit 前必传**：`git status` + `git diff --stat` 输出，确认文件范围匹配

---

## §8 收口验证（主 Agent）

1. 接收 Subagent commit 后 fast-forward 本地 feat/l4-phase3-pr2-k8s-backend
2. 跑完整验证（pytest/ruff/format/pyright）
3. 推送 + 创建 PR
4. CI 8 项 check 等待 success
5. PR description 填写 + 项目发起人合并

---

## §9 风险与缓解

| # | 风险 | 缓解 |
|---|---|---|
| 1 | K8sBackend 与 InMemoryBackend 行为差异 | 复用 pure.py · 4 纯函数数学不变 · contract suite 强制等价 |
| 2 | K8s API 错误码映射不完整 | 12 MEMORY_* 1:1 映射表 · 兜底 MEMORY_INTERNAL_ERROR |
| 3 | list label selector 性能 | 索引由 K8s API server 维护 · limit/offset 由 query 控制 |
| 4 | patch_status CAS 与 generation 不匹配 | 客户端先 get 读 generation → patch 携带期望值 → K8s 校验 |
| 5 | helm ConfigMap 注入 env var 失败 | 退化 in_process（默认） · K8sBackend 不可用不影响启动 |
| 6 | kubernetes_asyncio 依赖缺失 | service pyproject.toml 已含（如缺则补） |
| 7 | Subagent 超时 | 阶段 B/C 必在 60 min 内 · 超时则主 Agent 收尾 |

---

## §M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-10 · #94 启动）
- **M.2 落地记录**：#94（2026-08-10 · PR-2 启动 · Subagent 接力实装 K8sBackend）
- **M.3 关联 PR**：Phase 2 #22-#28 + #29 hotfix + Phase 3 #30-#33 + **#34 PR-2 K8sBackend**（待启动）
- **M.4 下次会话入口**：#95 PR-3 25 指标（45-60 min · 沿用任一 backend）
- **M.5 关注项台账**：
  - ① K8sBackend list label selector 性能（PR-2 收口前 benchmark）
  - ② 8-12 测试 ID 100% 覆盖（PR-2 收口前验证）
  - ③ helm values.yaml backend 字段与 main.py env var 注入一致性
  - ④ 5 项关键不变量 100% 保持（pure.py 0 改动）
  - ⑤ Branch Protection check 名 mismatch（⑭ · web 端 admin · PR-2 不依赖但收口后建议修复）
- **M.6 文档状态**：v0.1-draft 骨架稿（9 节 · ~10KB）
