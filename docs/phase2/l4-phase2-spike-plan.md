# L4-Phase2 实施层 Spike Plan · v0.1-draft

| 字段 | 值 |
|---|---|
| 文档版本 | v0.1-draft（2026-08-07） |
| 上游 Spec 锁定版本 | L3-6 v0.2.0 + v0.2.1 + L3-5 v0.2.1 + ADR-0006 v1.0 Accepted + L1 v0.2.0 §4.1 |
| 5 项关键不变量来源 | L3-6 §1.2 line 100-106 |
| 主 Agent 水位 | 5-8%（writing）· Subagent 隔离调研（2026-08-07） |
| 计划周期 | 5 个 PR 串行 · PR-1 ~ PR-5 · 预计 3-5 周 |
| Phase 1 起点 | main HEAD `7eecf41`（PR #17/#18/#19/#20/#21 merged · 138/138 PASS） |

---

## §0 阅读指南

本文档为 L4-Phase2（kind K8s 集群 E2E envtest + K8sLeaseLeaderElector 实装 + H-RM/H-QM IT/CF/E2E stub 实装）实施层 Spike 计划。

**面向读者**：
- **项目发起人**（决策者）：§1（目标/不在范围）+ §2（9 项设计决策）+ §6（验收清单）
- **主 Agent / Subagent**（实施者）：§3（5 个 PR 详细步骤）+ §4（测试策略）+ §5（风险与缓解）
- **L3 评审者**（追溯者）：§A（追溯表）+ §B（关键不变量继承）

**§F 同步状态**：
- ROADMAP.md · README.md · CONSTITUTION-CHANGELOG.md → 待 PR-5 收口时同步
- L3-6 §M.2 落地记录 → 待 PR-5 追加 #83-#86 行
- ADR-0006 §M-5 → 待 PR-5 追加 Phase 2 spike 记录

---

## §1 目标与不在范围

### §1.1 Phase 2 目标

1. **K8sLeaseLeaderElector 完整实装**（继承 Phase 1 Protocol · 替换 stub · InProcess 行为对齐）
2. **H-RM/H-QM IT/CF/E2E stub 实装**（共 6 个测试 ID 升级：H-RM-IT-001 + H-RM-CF-001 + H-QM-IT-001 + H-QM-CF-001 + H-RM-E2E-001 + H-QM-E2E-001）
3. **kind cluster E2E envtest**（memory CRD apply → 60s reconcile → assert state · Memory lifecycle E2E）
4. **leader election spike**（验证 InProcess vs K8s 切换机制 · spike 用临时 replicaCount=2）

### §1.2 Phase 2 不在范围（明确剔除）

| 不在范围项 | 来源 | 重新进入条件 |
|---|---|---|
| K8sBackend 完整实装 | Phase 3 候选 | Phase 3 启动决策 |
| 多副本生产支持（replicaCount > 1） | OPEN-MEMORY-002 · v0.5+ 锁定 | v0.5+ 架构评审 |
| Vector DB backend | OPEN-MEMORY-003 · v0.5+ | v0.5+ 决策 |
| Memory PII 加密 | OPEN-MEMORY-004 · 安全评审后 | 安全评审触发 |
| Multi-cluster 同步 | OPEN-MEMORY-005 · v1.0+ | v1.0+ 决策 |
| Performance 10K/50K 门禁验证 | Phase 1 遗留 | Phase 3 触发强制 PASS |
| Helm chart 大改 | ADR-0006 D 方案 + Phase 1 已锁定单进程架构 | 仅通过 values 注入参数（PR-1 role_write.yaml + leaderElection.backend 字段） |
| L3-6 §1.2 5 项关键不变量变更 | 任何变更必须走 ADR | 不变（PR-5 验收） |

### §1.3 Phase 2 与遗留问题台账对照

| MEMORY 遗留 # | 描述 | Phase 2 处理 |
|---|---|---|
| ① | Branch Protection on main 未启用（P0 · web 端 admin） | 🟡 **不阻塞 Phase 2** · 但 e2e CI 失败不阻断 merge 风险同 #81 · 用户行动紧迫性升级 |
| ② | 0 个项目 label（P1 · gh CLI 32 labels） | 🟡 **不阻塞 Phase 2** · Phase 2 PR 无法打 e2e label（需 web 端 admin） |
| ④ | Phase 2 stub 集合（K8sLeaseLeaderElector + H-RM/H-QM IT/CF/E2E）| 🎯 **本计划主目标** |
| ⑤ | `_build_memo()` 最小集设计债务 | ✅ #82 PR #21 已关闭 |

---

## §2 设计决策（9 项 · 待项目发起人决策）

### §2.1 kind cluster 生命周期

- **推荐方案**：**per-session shared cluster + per-function namespace**（带 uuid 后缀）
- **备选 A**：per-test ephemeral cluster（完全隔离，慢 ~100s/test）
- **备选 B**：per-session shared cluster + namespace reset（快 5s，并行需 xdist 协调）
- **决策依据**：speed vs isolation trade-off · per-session + uuid 是 PR CI 黄金分割点
- **并行安全**：配合 `pytest --dist=loadfile` 防同 test 并行

### §2.2 LeaderElector 默认实现

- **推荐方案**：**InProcessLeaderElector**（保持 D 方案单进程默认 · Helm `leaderElection.backend=in_process`）
- **备选**：K8sLeaseLeaderElector 默认（违反 L3-6 §1.2 #1 单实例不变量）
- **决策依据**：ADR-0006 D 方案 + L3-6 §1.2 #1 同 Pod 第二进程 → 单进程

### §2.3 K8sLeaseLeaderElector 启用方式

- **推荐方案**：**Helm values `leaderElection.backend=k8s` 显式启用**（运维 opt-in）
- **备选**：代码层自动启用（违反生产安全原则）
- **决策依据**：生产安全（默认 in_process；运维显式选择 K8s 才能启用）
- **额外**：spike 测试通过覆盖 Helm values 临时切换 `leaderElection.backend=k8s` + `replicaCount=2`

### §2.4 Lease 隔离策略

- **推荐方案**：**per-test Lease**（注入 uuid lease_name · K8sLeaseLeaderElector 构造参数已支持）
- **备选**：共享 Lease（测试间 leader 互相干扰 · 仅 1 个测试可持有）
- **决策依据**：防止多测试并发时 leader 切换不确定性
- **实现约束**：K8sLeaseLeaderElector 构造参数已支持 `lease_name` 默认值（leader.py line 91）→ 仅需测试 fixture 注入 uuid 名

### §2.5 CI 集成策略

- **推荐方案**：**新增 `e2e-envtest.yml` workflow · 手动 workflow_dispatch + nightly schedule**（不阻塞 PR CI）
- **备选**：常规 PR CI 自动跑（避免 5min+ 阻塞 PR review）
- **决策依据**：避免 kind cluster 启动 30s + helm install 60s + 测试 60s+ 总开销阻塞 PR review
- **触发条件**：
  - `workflow_dispatch`（手动 · 项目发起人 / 评审者触发）
  - `schedule: cron: 0 2 * * *`（nightly UTC 02:00 · 美东 22:00 · 避开白天流量高峰）
  - **不**触发 PR push（避免阻塞）

### §2.6 K8sBackend 是否引入

- **推荐方案**：**Phase 2 不引入 K8sBackend**（沿用 InMemoryBackend + 真实 K8s Lease 验证 leader 机制）
- **备选**：Phase 2 引入 K8sBackend（范围扩张 · 引入 CustomObjectsApi 状态管理）
- **决策依据**：范围控制（Phase 3 实装 K8sBackend · Phase 2 验证 leader 机制独立性）

### §2.7 cert-manager 是否启用

- **推荐方案**：**Phase 2 默认禁用**（`tls.enabled=false` Helm values）
- **备选**：启用 cert-manager（~60s 证书颁发流程阻塞测试）
- **决策依据**：测试速度优先；IT/CF 测试使用 httpx + mTLS client cert fixture 验证，E2E 测试可后置证书验证

### §2.8 RBAC §M-1.4 修复时机

- **推荐方案**：**Phase 2 PR-1（前置 PR）**
- **备选**：延后到 PR-2/3/4 同期
- **决策依据**：**不修则 K8sLeaseLeaderElector IT/E2E 跑不通**（kind cluster apply 双 Role 必含 3 apiGroups：`admissionregistration.k8s.io` + `authentication.k8s.io` + `authorization.k8s.io`）

### §2.9 测试覆盖率门槛

- **推荐方案**：Phase 2 新增 `k8s_lease_leader_elector` 模块 **≥ 90%** 覆盖率
- **备选**：不强制
- **决策依据**：L3-6 §10.4 line 1403 9 关键模块 ≥ 95% 覆盖率基线（apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion / memory_reconciler / clock / memory_backend / admission / leader_election）· 新增 `k8s_lease_leader_elector` 是第 10 个关键模块 · ≥ 90% 是首次新增模块的合理门槛

---

## §3 实施步骤（5 个 PR 串行）

### §3.1 PR-1 RBAC §M-1.4 修复 · ~30 min · 5-8% 水位 · 无新测试

**目标**：修复 L3-6-review §M-1.4 关注项（RBAC write Role 缺 admissionregistration/authentication/authorization 3 个 apiGroups）· 不修则后续 PR-2~PR-4 leader election 跑不通。

**修改文件**：
- `helm/knowledge-memory-service/templates/rbac/role_write.yaml` —— 追加 3 rules：
  ```yaml
  - apiGroups: ["admissionregistration.k8s.io"]
    resources: ["validatingwebhookconfigurations"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["authentication.k8s.io"]
    resources: ["tokenreviews"]
    verbs: ["create"]
  - apiGroups: ["authorization.k8s.io"]
    resources: ["subjectaccessreviews"]
    verbs: ["create"]
  ```
- `tests/conformance/test_rbac.py`（新文件 · ~80 行）—— 静态断言 12 MEMORY_* + 双 Role + 7 apiGroups 集合相等

**验证**：
- `pytest tests/conformance/test_rbac.py` PASS
- `helm template` 渲染检查 7 apiGroups 规则到位
- 138/138 PASS 保持

**PR 描述**：引用 L3-6 §9.5 line 1331-1361 + L3-6-review §M-1.4 line 358-376

### §3.2 PR-2 K8sLeaseLeaderElector 完整实装 · ~60-90 min · 10-15% 水位 · 建议 Subagent 接力

**目标**：替换 `leader.py` 中 K8sLeaseLeaderElector stub → 完整实装，保持 Protocol 签名不变（`is_leader` + `try_acquire_or_renew`），与 InProcessLeaderElector 行为对齐。

**新增/修改文件**：
- `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/reconciler/k8s_lease_leader_elector.py`（新文件 · ~150 行）
  - 构造函数：`__init__(self, *, lease_name, namespace, holder_id, duration, renew_deadline, retry_period, kube_client)`
  - 5 方法：`is_leader()` 同步缓存 · `try_acquire_or_renew()` 异步 · `_read_lease()` · `_create_lease()` · `_update_lease()` · `_preempt_lease()`
  - 错误映射：ApiException 404 → create · 5xx → 1/2/4/8s backoff retry · 4xx → raise MemoryBackendError(MEMORY_INTERNAL_ERROR) · 429 → 尊重 Retry-After · CancelledError 透传
- `services/knowledge-memory-service/src/superteam_a2a/knowledge_memory/reconciler/leader.py` —— 删除 stub line 97-104，改 re-export from `k8s_lease_leader_elector`
- `pyproject.toml` —— 显式声明 `kubernetes_asyncio>=29.0.0`（已隐式依赖）
- `tests/unit/knowledge_memory/reconciler/test_k8s_lease_leader_elector.py`（新文件 · ~250 行）
  - K8sLeaseLeaderElector.try_acquire_or_renew 真实 Lease create（5-8 个 UT）
  - 抢占机制（holder A 持锁 → holder B 启动 → 失败 → A 让位 → B 成功）
  - renew 失败 → 30s grace → 让位
  - asyncio cancellation 清理
  - mock `kubernetes_asyncio.client.CoordinationV1Api`

**验证**：
- `pytest` 138+5~8 PASS in <0.6s
- `ruff check .` All passed
- `pyright .` 0 errors（warning 数量不增）
- LeaderElector Protocol `runtime_checkable` 兼容（conftest 已验证）

**PR 描述**：引用 L3-6 §4.1 line 644-645 + L2-4 §7.6 line 2359-2416 + InProcessLeaderElector 5 项不变量对齐

### §3.3 PR-3 H-RM/H-QM IT/CF stub 实装 · ~45-60 min · 8-10% 水位 · 可 Subagent 接力

**目标**：升级 Phase 1 留下的 4 个 stub 测试 ID（H-RM-IT-001 + H-RM-CF-001 + H-QM-IT-001 + H-QM-CF-001）· 不需 kind cluster，使用 envtest 或 mock K8s API。

**修改文件**：
- `tests/unit/knowledge_memory/handlers/test_handle_record_memory.py` line 170-186
  - H-RM-IT-001：envtest apply Memory CRD → kopf on.create 触发 → body Memory.model_validate → RecordMemoryRequest 字段映射验证
  - H-RM-CF-001：RecordMemoryRequest Pydantic schema vs L2-4 §6.4 wire spec · 集合相等断言（12 字段）
- `tests/unit/knowledge_memory/handlers/test_handle_query_memory.py` line 164-186
  - H-QM-IT-001：envtest apply CRD → 5 维 visibility 过滤验证（scopeRef / agentRef / industry / content 关键词 / confidence threshold）
  - H-QM-CF-001：QueryMemoryRequest vs L2-4 §6.5 wire · 集合相等断言

**新增 fixture**（如需）：
- `tests/unit/knowledge_memory/conftest.py` 新增 envtest fixture（可选；如不引入 envtest 则全部用 mock K8s API）

**验证**：
- `pytest` 138+4 PASS in <0.6s
- `ruff check .` All passed
- `pyright .` 0 errors

**PR 描述**：引用 L3-5 §4.3 line 1178（H-RM）+ §4.4 line 1289（H-QM）+ L2-4 §6.4/§6.5 wire

### §3.4 PR-4 kind E2E fixture + H-RM/H-QM E2E 实装 · ~90-120 min · 15-20% 水位 · 必须主 Agent 串行

**目标**：新增 kind cluster session fixture + 5-8 个 E2E 测试（leader spike + H-RM/H-QM E2E + Memory lifecycle）· 不在常规 PR CI 跑，仅 manual + nightly。

**新增文件**：
- `tests/e2e/__init__.py` + `tests/e2e/conftest.py`（session-scoped `kind_cluster` + function-scoped `e2e_namespace` + `kubeconfig`）
- `tests/e2e/knowledge_memory/__init__.py`
- `tests/e2e/knowledge_memory/test_leader_election.py`：
  - InProcessLeaderElector 默认 spike：MemoryReconciler 60s tick 验证（不需 kind）
  - K8sLeaseLeaderElector spike：kind cluster + 2 个临时 Pod + helm install 覆盖 replicaCount=2 + leaderElection.backend=k8s + apply Memory CRD + kill leader + 30s 内新 leader 接管
- `tests/e2e/knowledge_memory/test_handle_record_memory.py`：
  - H-RM-E2E-001：recordMemory A2A call → K8s API apply → effective_confidence 计算 → response
- `tests/e2e/knowledge_memory/test_handle_query_memory.py`：
  - H-QM-E2E-001：queryMemory A2A call → backend list → 5 维过滤 → response
- `tests/e2e/knowledge_memory/test_memory_lifecycle.py`：
  - apply Memory CRD → 60s timer tick → status.phase == "Bound" + observedGeneration set
  - delete Memory CRD → finalize 5 步 → status.phase == "Released" + finalizer removed

**修改文件**：
- `pyproject.toml` —— 新增 `pytest-kind`（评估后决定）+ `pytest-xdist`（如启用并行）
- `.github/workflows/e2e-envtest.yml`（新文件 · ~60 行）：
  ```yaml
  name: e2e-envtest
  on:
    workflow_dispatch:
    schedule:
      - cron: '0 2 * * *'  # nightly UTC 02:00
  jobs:
    e2e:
      runs-on: ubuntu-22.04
      steps:
        - uses: actions/checkout@v4
        - name: Install kind
          run: curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64 && chmod +x ./kind
        - name: Create kind cluster
          run: ./kind create cluster --name e2e-${{ github.run_id }} --image kindest/node:v1.30.0
        - name: Apply CRDs
          run: kubectl apply -f helm/knowledge-memory-service/crds/
        - name: Helm install
          run: helm install kmem helm/knowledge-memory-service/
        - name: Run e2e tests
          run: python -m uv run pytest tests/e2e/ -v --tb=short
        - name: Delete kind cluster
          if: always()
          run: ./kind delete cluster --name e2e-${{ github.run_id }}
  ```

**验证（本地）**：
- `kind create cluster` 成功（~30s）
- CRD apply 成功（~5s）
- Helm install 成功（~60s）
- E2E tests 5-8 PASS（~120s）
- **不**在 `pytest tests/` 默认 collection 内（`pytest tests/unit tests/conformance tests/integration` 不含 `tests/e2e/`）
- `pytest tests/e2e/ -v` 单独跑（需 kind cluster）

**PR 描述**：引用 L3-6 §4.3 line 666-708 reconcile 算法 + L2-4 §7.6 Lease 约束

### §3.5 PR-5 MEMORY + ADR 同步 · ~30-45 min · 5-8% 水位

**目标**：Phase 2 spike 落地记录 + 文档同步 · 不写新 ADR（Phase 2 是 spike 而非新架构决策）。

**修改文件**：
- `MEMORY.md` —— 状态行更新（PR #22/#23/#24/#25 + #86 新增）+ 4 session 文件索引（#83 main 同步 · #84 RBAC · #85 K8sLease · #86 H-RM/H-QM E2E + leader spike）
- `docs/adr/0006-memory-transport.md` §M-5 —— 追加 Phase 2 leader election spike 记录（InProcess 默认 + K8s opt-in）
- `docs/spec/L3-file-specs/L3-memory-backend.md` §M.2 —— 落地记录追加 #83-#86 行
- `docs/spec/L3-file-specs/L3-knowledge-service.md` §M.2 —— 落地记录追加 #83-#86 行
- `README.md` + `ROADMAP.md` + `CONSTITUTION-CHANGELOG.md` —— 微同步 Phase 2 状态

**验证**：
- 所有 session 文件存在
- MEMORY.md 状态行格式与 #82 一致
- ADR-0006 §M-5 与本文档 §2.3 决策一致

**PR 描述**：纯文档同步 · 无代码变更

---

## §4 测试策略（UT/IT/CF/E2E 分层）

### §4.1 Phase 2 测试分布

| 层级 | Phase 2 比例 | 工具 | 依赖 | Phase 2 新增 |
|---|---|---|---|---|
| **UT**（unit） | 60% | pytest + pytest-asyncio + freezegun + AsyncMock | 无外部 | K8sLeaseLeaderElector mock 5-8 个 |
| **CF**（conformance） | 5% | pytest + 静态断言 | 无外部 | RBAC 集合相等 + H-RM/H-QM wire 对齐 |
| **TZ**（time-travel） | 5% | pytest + freezegun | 无外部 | — |
| **IT**（integration） | 15% | pytest + mock kubernetes_asyncio + envtest | envtest bin (~50MB) | H-RM/H-QM IT 4 个 |
| **E2E**（end-to-end） | 10% | pytest + kind + helm + kubectl | kind binary (~150MB) + docker | leader spike + H-RM/H-QM E2E + lifecycle 5-8 个 |
| **DEPLOY/PERF** | 5% | pytest + helm template + promtool | helm + promtool | — |

### §4.2 Phase 2 测试 ID 总览

**继承 Phase 1 60 ID + 新增 ~13-20 ID**：

| 测试 ID 范围 | 层级 | 数量 | Phase 2 PR |
|---|---|---|---|
| TEST-MEM-001 ~ TEST-MEM-060 | UT/CF/TZ/IT/DEPLOY | 60 | Phase 1 已实装（PR #17-#21） |
| K8sLeaseLeaderElector UT（5-8 新 ID · 前缀 `K8S-LE-UT-`） | UT | 5-8 | PR-2 |
| RBAC CF（1 新 ID · `RBAC-CF-001`） | CF | 1 | PR-1 |
| H-RM-IT-001（升级 stub） | IT | 1 | PR-3 |
| H-RM-CF-001（升级 stub） | CF | 1 | PR-3 |
| H-QM-IT-001（升级 stub） | IT | 1 | PR-3 |
| H-QM-CF-001（升级 stub） | CF | 1 | PR-3 |
| H-RM-E2E-001（新增） | E2E | 1 | PR-4 |
| H-QM-E2E-001（新增） | E2E | 1 | PR-4 |
| Leader spike E2E（2 新 ID · `LEADER-E2E-001/002`） | E2E | 2 | PR-4 |
| Memory lifecycle E2E（2 新 ID · `LIFECYCLE-E2E-001/002`） | E2E | 2 | PR-4 |

**Phase 2 总计**：60 + 8 (K8s-LE) + 1 (RBAC) + 4 (H-RM/H-QM IT/CF) + 6 (H-RM/H-QM E2E + leader + lifecycle) = **79 个测试 ID**

### §4.3 测试命令矩阵

| 命令 | 范围 | 时长（预估） | CI 触发 |
|---|---|---|---|
| `pytest tests/unit tests/conformance tests/integration` | 138+13 ~ 151 PASS | ~0.5s | 常规 PR CI（ci.yml） |
| `pytest tests/e2e/` | 5-8 PASS | ~120s | manual + nightly（e2e-envtest.yml） |
| `pytest tests/` | 全部 79 | ~125s | 仅本地 + nightly |
| `ruff check .` + `ruff format --check .` + `pyright .` | lint | ~5s | 常规 PR CI |

---

## §5 风险与缓解（10 项）

| # | 风险 | 影响 | 缓解 | Phase |
|---|---|---|---|---|
| 1 | kind cluster 启动慢（30s+）+ helm install 60s+ | E2E 测试慢 | session-scoped cluster + namespace reset 5s；并行 xdist 防串行 | PR-4 |
| 2 | Lease 抢占竞争（多副本 spike 时） | 测试不稳定 | per-test Lease uuid 隔离 | PR-2/4 |
| 3 | envtest binary 与 kind cluster 行为差异 | IT/E2E 行为不一致 | **统一使用 kind**（废弃 envtest）+ 减少 IT 层依赖 | PR-3/4 |
| 4 | cert-manager TLS 流程复杂（~60s 颁发） | 测试慢 | `tls.enabled=false` Helm values 默认 | PR-4 |
| 5 | MemoryReconciler 60s 周期 E2E 慢 | E2E 测试 60s+ | 短周期测试用 helm values 覆盖（仅测试环境）· **生产 60s 不变** | PR-4 |
| 6 | K8sLeaseLeaderElector 实现 bug 导致 leader 切换时数据丢失 | 数据丢失 | 严格遵循 prepare/bind/commit/rollback（L3-6 §4.3 line 666-708）· 30s grace 内不写 status | PR-2 |
| 7 | **§M-1.4 RBAC 未修复导致 leader election 测试跑不通** | PR-2 阻塞 | **PR-1 提前修复（前置 PR）** | PR-1 |
| 8 | MemoryReconciler 在 kind 中跑 60s 真实 reconcile 触发 CRD 状态变化 | 测试不稳定 | 使用 FakeClock（ut 验证）+ 真实等待（e2e 验证）· 分离验证目标 | PR-4 |
| 9 | GitHub Actions runner 资源限制（4 CPU / 7GB RAM） | kind cluster 启动失败 | 限制 kind 节点数（1 control-plane + 0 worker）+ 资源 requests 调小 | PR-4 |
| 10 | Branch Protection 未启用（#76 已知 P0） | CI 失败未阻断 merge · 同 #81 pyright gap | Phase 2 完成后用户行动紧迫性升级（**不阻塞 Phase 2 但记录**） | 跨阶段 |

---

## §6 验收清单

### §6.1 PR-1 RBAC 修复

- [ ] `helm/knowledge-memory-service/templates/rbac/role_write.yaml` 含 7 apiGroups（5 + admissionregistration + authentication + authorization）
- [ ] `tests/conformance/test_rbac.py` PASS（12 MEMORY_* + 双 Role + 7 apiGroups 集合相等断言）
- [ ] `helm template` 渲染检查 7 apiGroups 规则到位

### §6.2 PR-2 K8sLeaseLeaderElector 实装

- [ ] K8sLeaseLeaderElector 完整实装（替换 stub）· 5-8 个 UT PASS
- [ ] LeaderElector Protocol 签名保持不变（runtime_checkable 验证）
- [ ] InProcessLeaderElector + K8sLeaseLeaderElector 行为对齐（同一组 conformance UT PASS）
- [ ] 138 + 5~8 = 143~146 pytest PASS in <0.6s · ruff 0 · pyright 0

### §6.3 PR-3 H-RM/H-QM IT/CF 实装

- [ ] H-RM-IT-001 + H-RM-CF-001 + H-QM-IT-001 + H-QM-CF-001 升级（替换 stub）· 4 PASS
- [ ] 138 + 4 = 142 pytest PASS

### §6.4 PR-4 kind E2E

- [ ] `tests/e2e/conftest.py` kind_cluster session fixture + e2e_namespace function fixture
- [ ] H-RM-E2E-001 + H-QM-E2E-001 实装（不在常规 CI 跑）
- [ ] leader election spike 实装（K8sLeaseLeaderElector + MemoryReconciler + 临时 replicaCount=2 spike）
- [ ] Memory lifecycle E2E（apply → 60s reconcile → assert · delete → finalize → assert）
- [ ] 5-8 E2E 测试 PASS · nightly workflow 稳定运行
- [ ] `.github/workflows/e2e-envtest.yml` 触发条件正确（manual + nightly，不阻塞 PR）

### §6.5 PR-5 MEMORY + ADR 同步

- [ ] MEMORY.md 状态行更新（PR #22/#23/#24/#25 + #86 新增）
- [ ] ADR-0006 §M-5 追加 Phase 2 spike 记录
- [ ] L3-6 §M.2 落地记录追加 #83-#86 行
- [ ] L3-5 §M.2 落地记录追加 #83-#86 行
- [ ] README.md / ROADMAP.md / CONSTITUTION-CHANGELOG.md 微同步

### §6.6 质量门禁（Phase 2 整体）

- [ ] **152~158 PASS**（138 Phase 1 + 8 K8s-LE + 1 RBAC + 4 H-RM/H-QM IT/CF + 6 E2E）
- [ ] ruff check All passed
- [ ] pyright 0 errors（warning 数量不增）
- [ ] 9 关键模块 ≥ 95% 覆盖率 + 新增 `k8s_lease_leader_elector` ≥ 90% 覆盖率
- [ ] 12 MEMORY_* 错误码 100% wire 一致（TEST-MEM-051 集合相等静态断言 PASS）
- [ ] **5 项关键不变量保持**（L3-6 §1.2 line 100-106）：
  - [ ] 单 Pod 第二进程 → 单进程
  - [ ] 60s timer 不变
  - [ ] L3-5/L3-6 共享 Deployment
  - [ ] 4 纯函数数学不变
  - [ ] wire contract 不变
- [ ] ADR-0006 v1.0 Accepted D 方案兼容性 100%
- [ ] §F 跨文档同步完成（ROADMAP / README / CONSTITUTION-CHANGELOG）

---

## §7 文档元数据

### §7.1 版本历史

| 版本 | 日期 | 作者 | 变更 |
|---|---|---|---|
| v0.1-draft | 2026-08-07 | 主 Agent（Subagent 隔离调研） | 初稿：9 项决策 + 5 PR 串行 + 10 风险 + 6 验收 |

### §7.2 关键引用

| 类型 | 引用 |
|---|---|
| 上游 Spec | L3-6 v0.2.0 + v0.2.1 / L3-5 v0.2.1 / L2-4 v0.2.0 / ADR-0006 v1.0 Accepted / L1 v0.2.0 §4.1 |
| 评审引用 | L3-6-review §M-1.4（RBAC）+ §M-1.5（Clock）+ §M-2.3（覆盖率映射） |
| 实施引用 | Phase 1 main HEAD `7eecf41`（PR #17/#18/#19/#20/#21 · 138/138 PASS） |
| 调研报告 | Subagent `a94e9944c377b6e54` · 2026-08-07 · ~30KB 输出（不在 git 内） |

### §7.3 关联文件

| 路径 | 用途 |
|---|---|
| `docs/spec/L3-file-specs/L3-memory-backend.md` | L3-6 权威（5 项不变量 + reconcile 算法 + RBAC 双 Role + 12 错误码 + Lease 约束） |
| `docs/spec/L3-file-specs/L3-knowledge-service.md` | L3-5 权威（H-RM/H-QM handler 契约 + D 方案部署） |
| `docs/spec/L2-module-specs/L2-knowledge-memory.md` | L2-4 上游（§7.6 RealLeaseLeader 参考 · wire 12 字段） |
| `docs/adr/0006-memory-transport.md` | ADR-0006 v1.0 Accepted D 方案（单进程架构） |
| `docs/design/L1-architecture.md` §4.1 | L1 C-6 + ~~C-7~~ 合并架构 |
| `docs/reviews/l3-6-memory-backend-spec-review.md` | L3-6 评审（5 关注项 + 4 建议项） |
| `docs/reviews/l3-5-knowledge-service-spec-review.md` | L3-5 评审 |

### §7.4 后续文档

| 文档 | 时机 |
|---|---|
| PR-2 描述（K8sLeaseLeaderElector 实装） | PR-2 提交时 |
| PR-4 描述（kind E2E 实装） | PR-4 提交时 |
| L3-6 §M.2 落地记录追加 | PR-5 提交时 |
| ADR-0006 §M-5 Phase 2 spike 记录 | PR-5 提交时 |
| MEMORY.md 状态行更新 | PR-5 提交时 |
| 4 个 session 文件（#83-#86） | 每个 PR 完成后 |

### §7.5 不在本文档范围

- 详细 reconcile 算法代码（仅引用 L3-6 §4.3 line 666-708）
- K8sBackend 实装（Phase 3 范围）
- 多副本生产支持（v0.5+ 范围）
- Vector DB backend（v0.5+ 范围）
- Helm chart 大改（Phase 2 不改）

### §7.6 签署

- **作者**：主 Agent（MiniMax-M3 via Claude Code）· 2026-08-07
- **调研**：Subagent 隔离 `a94e9944c377b6e54` · 41 tool uses · 7 分钟
- **状态**：v0.1-draft · 待项目发起人决策 9 项设计（§2）+ 启动 PR-1 RBAC 修复

---

> **计划就绪 · 等待启动**：本计划文档交付后进入 v1.0 推荐 → 项目发起人决策 9 项 → 启动 PR-1 RBAC 修复 → 串行 5 PR 收口