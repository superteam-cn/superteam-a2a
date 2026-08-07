# L4-Phase2 Spike Plan · §2 设计决策评审

| 字段 | 值 |
|---|---|
| 评审版本 | v0.1-draft 评审（2026-08-07） |
| 评审对象 | `docs/phase2/l4-phase2-spike-plan.md` §2（9 项设计决策）|
| 评审角度 | 合规性（L3-6 §1.2 5 项关键不变量）+ 架构一致性（ADR-0006 D 方案 + L1 v0.2.0 §4.1）+ 实施可行性 + 风险评估 + 遗漏识别 |
| 主 Agent 水位 | 5-8%（评审）· 不修改原 plan，仅追加评审意见 |
| 评审结论 | **8 项推荐方案可接受 · 1 项需讨论** + **6 项遗漏决策需补** |

---

## §0 评审摘要

**整体结论**：9 项设计决策的推荐方案 8 项可直接采纳 · 1 项需微调（§2.9 覆盖率门槛）· 6 项遗漏决策需补充到 plan（§2.10 ~ §2.15）。

**关键不变量验证**：所有 9 项决策与 L3-6 §1.2 line 100-106 5 项关键不变量 100% 兼容 · 与 ADR-0006 v1.0 Accepted D 方案 100% 兼容。

**建议行动**：
1. **立即可采纳**：§2.1 / §2.2 / §2.3 / §2.4 / §2.6 / §2.7 / §2.8
2. **微调后采纳**：§2.9（建议 ≥ 92% 而非 ≥ 90% · 与 9 关键模块基线 95% 的差距从 5pp 收窄到 3pp）
3. **需讨论**：§2.5（nightly schedule 时间是否合理 · GitHub Actions 排队时段分析）
4. **需补充**：§2.10 ~ §2.15 遗漏决策

---

## §1 逐项评审

### §1.1 §2.1 kind cluster 生命周期

| 项 | 评审 |
|---|---|
| **推荐方案** | per-session shared cluster + per-function namespace（uuid 后缀） |
| **评审结论** | ✅ **采纳** |
| **评审依据** | L3-6 §10.4 E2E 测试要求"真实 K8s 集群 + 60s reconcile + assert state" · per-session 是 PR CI 黄金分割点 · uuid 防 namespace 冲突 |
| **补充建议** | ① 加 `kind delete cluster --name e2e-${{ github.run_id }}` 后置清理（防 namespace 累积泄漏）· ② pytest-xdist worker 间用 `worker_id` 区分 namespace（如 `e2e-h-rm-it-001-{worker_id}-{uuid}`）· ③ Memory CRD 是 cluster-scoped，session apply 一次即可，function-scoped 仅清理 namespaced resources |

### §1.2 §2.2 LeaderElector 默认实现

| 项 | 评审 |
|---|---|
| **推荐方案** | InProcessLeaderElector 默认（Helm `leaderElection.backend=in_process`） |
| **评审结论** | ✅ **采纳** |
| **评审依据** | L3-6 §1.2 #1 单实例不变量 + ADR-0006 §4.1 D 方案 "单 Pod 单 Container 单进程 replicaCount=1" |
| **补充建议** | ① `values.schema.json` 显式声明 `leaderElection.backend` enum=["in_process", "k8s"] · 默认值 "in_process" ② K8sLeaseLeaderElector 实装后默认 export 但 `_build_memo()` 不挂载（仅当 `leaderElection.backend=k8s` 才挂载 · main.py 条件装配）③ Helm values 注释应明确说明"生产推荐 in_process；k8s 仅供多副本 spike 测试" |

### §1.3 §2.3 K8sLeaseLeaderElector 启用方式

| 项 | 评审 |
|---|---|
| **推荐方案** | Helm values `leaderElection.backend=k8s` 显式启用（运维 opt-in） |
| **评审结论** | ✅ **采纳** |
| **评审依据** | 生产安全原则（默认 in_process；运维显式选择） |
| **补充建议** | ① schema.json 交叉验证：`leaderElection.backend=k8s` 时 `replicaCount>=2`（单副本+leader election 无意义）· 反之 `replicaCount==1` 时 `leaderElection.backend` 强制 `in_process` ② k8s 模式下默认 Lease name `memory-reconciler-leader`（与 L3-6 §4.1 line 645 一致）+ namespace `superteam-a2a-system`（L3-6 §9.4）③ chart README 明确示例 values ④ **关键约束**：k8s 模式触发 admissionregistration.k8s.io RBAC → 必须先 PR-1 RBAC 修复完成才能启用 k8s 模式 |

### §1.4 §2.4 Lease 隔离策略

| 项 | 评审 |
|---|---|
| **推荐方案** | per-test Lease uuid（注入 `lease_name` 参数） |
| **评审结论** | ✅ **采纳** |
| **评审依据** | L3-6 §4.1 line 645 `memory-reconciler-leader` + §4.2 line 666-708 acquire/renew 协议 |
| **补充建议** | ① 测试 fixture 用 yield fixture（自动 cleanup · `kubectl delete lease -n superteam-a2a-system <test-uuid>`）· ② 共享 namespace `superteam-a2a-system` 下 per-test Lease uuid → 避免跨 test 干扰 · 不需 per-test namespace ③ 实际生产部署用单 Lease `memory-reconciler-leader`（uuid 仅测试）④ pytest fixture 设计模式：```python@pytest.fixtureasync def per_test_lease():     name = f"test-{uuid4().hex[:8]}"     yield name     # cleanup     await kube.delete_lease(name)``` |

### §1.5 §2.5 CI 集成策略

| 项 | 评审 |
|---|---|
| **推荐方案** | 新增 `e2e-envtest.yml` · manual workflow_dispatch + nightly schedule（不阻塞 PR CI） |
| **评审结论** | 🟡 **需讨论** |
| **评审依据** | L3-6 §10.4 E2E 测试设计 + 避免 5min+ 阻塞 PR review |
| **讨论点** | ① nightly cron `0 2 * * *` UTC（美东 22:00 · 北京 10:00）是否合理？GitHub Actions 排队高峰在 UTC 14:00-22:00（美西白天）· 02:00 是相对低谷但仍有排队可能 · 建议改 `30 1 * * *` UTC（错峰 +30 分钟）· ② e2e-envtest.yml 应有 `concurrency:` block（防多个 nightly 并发 · `cancel-in-progress: true`）· ③ `timeout-minutes: 15`（kind 30s + helm 60s + tests 120s = ~210s < 15min）· ④ `permissions:` block 最小权限（`contents: read` + `checks: write`）· ⑤ **关键**：e2e-envtest.yml 与 ci.yml 物理隔离（避免 ci.yml 引入 kind 依赖拖慢 PR CI）· ⑥ 是否需 `pull_request` 触发但限定 label `e2e`？（PR 标 e2e label 才跑）—— 当前 plan 仅 manual + nightly，建议**加 PR label 触发**作为第 3 触发条件 |

**调整后推荐**：
```yaml
on:
  workflow_dispatch:        # 手动
  schedule:
    - cron: '30 1 * * *'    # nightly UTC 01:30（错峰）
  pull_request:
    types: [labeled]        # 仅标 e2e label 时触发
```

### §1.6 §2.6 K8sBackend 是否引入

| 项 | 评审 |
|---|---|
| **推荐方案** | Phase 2 不引入 K8sBackend（沿用 InMemoryBackend + 真实 K8s Lease） |
| **评审结论** | ✅ **采纳** |
| **评审依据** | 范围控制原则（Phase 3 实装 K8sBackend · Phase 2 验证 leader 机制独立性） |
| **补充建议** | ① **核心断言**：leader spike 必须验证「leader pod 持 Lease 时 backend.put/get 正常 · 非 leader pod backend 操作被 reconciler 跳过」② spike 测试设计：在 kind cluster 中启动 2 个 pod，pod-A 持 Lease（leader）执行 reconcile · pod-B 非 leader 不执行 reconcile · 验证 pod-B 的 reconcile log 是空 ③ InMemoryBackend 是进程内 dict，多 pod 不共享 state → spike 仅验证 leader 选举机制本身，不验证 backend 状态共享 ④ K8sBackend 引入时机建议 v0.3+（OPEN-MEMORY-002 多副本 v0.5+ 决策通过后） |

### §1.7 §2.7 cert-manager 是否启用

| 项 | 评审 |
|---|---|
| **推荐方案** | Phase 2 默认禁用（`tls.enabled=false` Helm values） |
| **评审结论** | ✅ **采纳** |
| **评审依据** | 测试速度优先（cert-manager ~60s 阻塞）+ L3-6 §11.3 cert-manager 是生产要求但非 Phase 2 必需 |
| **补充建议** | ① `tls.enabled=false` 时 port 8443 不应 listen（避免无效监听端口 · main.py 条件判断）· ② A2A call 在 tls.enabled=false 下应走 http（httpx client 不传 cert · Phase 2 测试 fixture）· ③ E2E 测试 fixture 清晰说明两种模式（tls on / tls off）的配置和预期行为 ④ **可选**：Phase 2 末尾增加一个 IT 用 cert-manager（`tls.enabled=true` + minikube/kind cert-manager install）验证 mTLS 链路（确保 Phase 3+ 启用 cert-manager 时有回归测试） |

### §1.8 §2.8 RBAC §M-1.4 修复时机

| 项 | 评审 |
|---|---|
| **推荐方案** | Phase 2 PR-1（前置 PR） |
| **评审结论** | ✅ **强制采纳** · 不可调整 |
| **评审依据** | L3-6-review §M-1.4 line 358-376 + 不修则 K8sLeaseLeaderElector IT/E2E 跑不通（admissionregistration.k8s.io / authentication.k8s.io / authorization.k8s.io 3 apiGroups 缺失 → webhook + token review + subject access review 全部 403） |
| **补充建议** | ① PR-1 应加 `tests/conformance/test_rbac.py` 验证集合相等（**12 MEMORY_* 错误码不适用 · 应是 resources + verbs + apiGroups 集合**）· ② 修复同时 review Helm chart 的 NetworkPolicy（如存在）是否允许 admissionregistration API（默认 NetworkPolicy 可能 deny）· ③ **关键验证**：PR-1 之后本地 `helm template` + `helm lint` 必须通过 ⑤ ④ PR 描述引用 L3-6 §9.5 line 1331-1361 + L3-6-review §M-1.4 line 358-376 |

### §1.9 §2.9 测试覆盖率门槛

| 项 | 评审 |
|---|---|
| **推荐方案** | 新增 `k8s_lease_leader_elector` 模块 ≥ 90% 覆盖率 |
| **评审结论** | 🟡 **微调后采纳** · 建议 ≥ **92%** 而非 ≥ 90% |
| **评审依据** | L3-6 §10.4 line 1403 9 关键模块 ≥ 95% 覆盖率基线 · 90% 与 95% 差距 5pp（首次新增模块的合理但偏宽）· 92% 差距 3pp 更合理 |
| **补充建议** | ① pytest-cov 配置新增 coverage include pattern：`services/knowledge-memory-service/src/.../reconciler/k8s_lease_leader_elector.py` · ② 覆盖率验证脚本与 ruff/pyright 一起进 CI（如 `coverage run -m pytest tests/unit && coverage report --fail-under=92 ...`）· ③ 9 关键模块基线 ≥ 95% 保持（不退化）· ④ **关键**：不要为追求 100% 覆盖率而写无意义测试（如 `assert True`）· 真实代码路径覆盖即可 |

---

## §2 遗漏决策（评审发现 6 项）

### §2.10 MemoryReconciler 60s 周期 E2E 验证策略

**问题**：当前 plan §3.4 提到「短周期测试用 helm values 覆盖（仅测试环境）」但未明确决策 E2E 是否覆盖真实 60s 周期。

**建议**：
- **E2E 保留 60s**（验证生产真实周期 + apply_decay/reinforce 时间窗口正确）
- **IT 层新增**：用 `interval=5s` 覆盖 helm values 快速验证（PR-3 H-RM/H-QM IT 已涵盖）
- **明确 spec**：E2E 测试不覆盖 60s 内的事件触发（如 leader election 抢占），改用 IT 层 interval=5s

### §2.11 Mock K8s API vs 真实 envtest 选型

**问题**：当前 plan §3.3 提到「envtest 或 mock K8s API」未明确决策。

**建议**：
- **IT 层用 mock K8s API**（UT-like fast · 无外部依赖 · 与 UT 速度一致）
- **envtest 仅**（kind 集群 E2E 使用）
- **理由**：envtest binary 50MB 部署复杂 · mock K8s API 用 pytest fixture + AsyncMock 更轻量
- **测试分布**：UT（60%）+ IT mock K8s API（15%）+ E2E kind（10%）+ CF（5%）+ TZ（5%）+ DEPLOY/PERF（5%）

### §2.12 A2A protocol wire Phase 2 验证范围

**问题**：当前 plan 未提 A2A protocol wire（JSON-RPC over HTTPS）· L3-5 §4.3/§4.4 定义 recordMemory / queryMemory A2A call。

**建议**：
- H-RM-E2E-001 / H-QM-E2E-001 应通过 **A2A call** 验证（不是直连 service.record_memory_async）
- 测试 A2A JSON-RPC envelope + params + result/error 字段
- 验证 12 MEMORY_* 错误码在 A2A error 包装后正确映射（`error.code == -32101` 等）
- **新增 E2E 范围**：H-RM-E2E-001 / H-QM-E2E-001 覆盖 wire format + 业务逻辑两端

### §2.13 Phase 2 是否升级宪法版本

**问题**：当前宪法 v0.5.0 · Phase 2 引入 kind + e2e 是否触发宪法升级？

**建议**：
- **不升级**（Phase 2 是 spike 而非新架构决策）
- 引用宪法 v0.5.0 §14.5 MVP 例外窗口（ADR-0005 Accepted 同模式）
- Phase 2 收口时宪法 v0.5.0 兼容（仅追加 §M-5 spike 记录 · 无架构变更）
- **如 Phase 2 决定转 production**（非 spike）则触发宪法 v0.6.0 升级

### §2.14 Phase 2 测试基础设施升级

**问题**：当前 plan 未明确 top-level conftest.py 升级。

**建议**：
- top-level `tests/conftest.py` 加：
  - `event_loop_policy` fixture（pytest-asyncio 0.21+ 要求）
  - `reset_memo` fixture（每个 test 清理 `_build_memo()` memo 缓存）
  - `clock` fixture（提供 FakeClock 用于时间相关测试）
- `tests/unit/knowledge_memory/conftest.py` 加：
  - `in_memory_backend` fixture（共享 InMemoryBackend 实例 · 避免重复创建）
  - `mock_kopf_event` fixture（模拟 kopf event · 不需真实 kopf daemon）

### §2.15 Phase 2 与后续工作交接

**问题**：当前 plan 未明确 Phase 2 → Phase 3 的交接边界。

**建议**：
- Phase 2 收口时明确：
  - **Phase 3 入口**：K8sBackend 实装（OPEN-MEMORY-002 多副本 v0.5+ 决策通过后启动）
  - **Phase 2 留在 main 的资产**：5 PR 全部 merged · kind_cluster fixture 共享给后续 Phase 3 测试
  - **e2e-envtest.yml workflow 复用**：Phase 3+ e2e 测试统一走此 workflow
  - **k8s_lease_leader_elector.py 复用**：Phase 3 K8sBackend 实装时直接用此 leader election 机制
- **handoff 文档**：PR-5 收口时写 `docs/phase3-handoff.md`（11 节 · 类似 #72 handoff 模板）

---

## §3 决策摘要表

| # | 决策 | 推荐 | 评审结论 | 调整 |
|---|---|---|---|---|
| §2.1 | kind cluster 生命周期 | per-session shared + per-function namespace | ✅ 采纳 | 加 cleanup + worker_id |
| §2.2 | LeaderElector 默认 | InProcess | ✅ 采纳 | schema enum + 条件挂载 |
| §2.3 | K8sLease 启用方式 | Helm opt-in | ✅ 采纳 | schema 交叉验证 + chart README |
| §2.4 | Lease 隔离 | per-test uuid | ✅ 采纳 | yield fixture cleanup |
| §2.5 | CI 集成 | manual + nightly | 🟡 需讨论 | 加 PR label 触发 + 错峰 cron |
| §2.6 | K8sBackend 引入 | Phase 2 不引入 | ✅ 采纳 | 明确 leader spike 断言 |
| §2.7 | cert-manager 启用 | 默认禁用 | ✅ 采纳 | tls.enabled=false 行为明确 |
| §2.8 | RBAC §M-1.4 时机 | PR-1 前置 | ✅ 强制采纳 | 无调整 |
| §2.9 | 覆盖率门槛 | ≥ 90% | 🟡 微调 | 改 ≥ 92%（3pp vs 95%）|

**遗漏决策**：
- §2.10 MemoryReconciler 60s 周期 E2E vs IT 策略
- §2.11 Mock K8s API vs 真实 envtest 选型
- §2.12 A2A protocol wire Phase 2 验证范围
- §2.13 Phase 2 是否升级宪法版本
- §2.14 Phase 2 测试基础设施升级
- §2.15 Phase 2 → Phase 3 交接边界

---

## §4 关键不变量验证

L3-6 §1.2 line 100-106 5 项关键不变量 100% 保持：

- ✅ #1 同 Pod 第二进程 → 单进程：`leaderElection.backend=in_process` 默认 + `replicaCount=1`（§2.2/§2.3）
- ✅ #2 60s timer 不变：§2.10 E2E 保留 60s 验证生产真实周期
- ✅ #3 L3-5/L3-6 共享 Deployment：phase 2 不改 Helm chart 主结构
- ✅ #4 4 纯函数数学不变：K8sLeaseLeaderElector 不涉及算法
- ✅ #5 wire contract 不变：§2.12 A2A wire 验证范围保持 12 字段 wire

ADR-0006 v1.0 Accepted D 方案兼容性：
- ✅ 单进程架构：§2.2/§2.3 默认 in_process + opt-in k8s
- ✅ 5 关键不变量：100% 保持
- ✅ K8sLease 实装但不启用：§2.6 Phase 2 仅 spike + 验证

---

## §5 评审后建议 Phase 2 启动顺序

1. **采纳 §2.1 ~ §2.4 / §2.6 ~ §2.8**（直接采纳 · 无需调整）
2. **微调 §2.5**（加 PR label 触发 + 错峰 cron · 5 分钟调整）
3. **微调 §2.9**（≥ 92% 而非 ≥ 90% · 1 行调整）
4. **补充 §2.10 ~ §2.15**（6 项遗漏决策补到 plan · 主 Agent 写 patch · 5-10 分钟）
5. **plan v0.1-draft → v1.0 推荐**（项目发起人最终审批 · 决策 9+6 = 15 项）
6. **启动 PR-1 RBAC §M-1.4 修复**（前置 PR · 不可调整）

**预计 plan 完善时长**：~15 分钟（主 Agent）· 不需 Subagent 接力

---

## §6 评审签署

- **作者**：主 Agent（MiniMax-M3 via Claude Code）· 2026-08-07
- **评审对象**：`docs/phase2/l4-phase2-spike-plan.md` v0.1-draft
- **评审结论**：8 采纳 + 2 调整 + 6 遗漏补充
- **下一步**：项目发起人决策 §3 调整方案 · 主 Agent 写 plan v0.2-draft 补丁（采纳评审意见）· 然后启动 PR-1
- **不在范围**：plan §3-§7 详细评审（待 §1 §2 决策确定后再评审）