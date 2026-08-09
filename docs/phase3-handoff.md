# Phase 2 → Phase 3 交接文档

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-09）|
| 上游 | Phase 2 plan v1.0 推荐 `docs/phase2/l4-phase2-spike-plan.md` |
| 下游 | Phase 3 启动决策（K8sBackend 实装 · OPEN-MEMORY-002 多副本 v0.5+ 通过后启动）|
| 关联 PR | #17/#18/#19/#20/#21（Phase 1 5/5）+ #22/#23/#24（Phase 2 merged）+ #25（Phase 2 PR-4 open）+ PR-4.1 + PR-5 待启动 |

---

## §1 当前完成状态（Phase 2 收口）

Phase 2 spike 4/5 PR 完成（PR #22/#23/#24 merged + PR #25 open），main HEAD `b1556db` · 179/179 PASS。

| PR | 内容 | 状态 | 测试增量 |
|---|---|---|---|
| **#22** PR-1 RBAC §M-1.4 修复 | role_write 追加 admissionregistration/authentication/authorization 3 apiGroups | ✅ merged | +14（TEST-MEM RBAC 静态断言） |
| **#23** PR-2 K8sLeaseLeaderElector 完整实装 | 替换 stub · 192 PASS · 覆盖率 93.26% | ✅ merged | +13 |
| **#24** PR-3 H-RM/H-QM IT/CF stub 实装 | 4 ID 升级（H-RM-IT/CF + H-QM-IT/CF） | ✅ merged | +4 |
| **#25** PR-4 kind E2E spike 基础设施 | tests/e2e/ + e2e-envtest.yml + 5 E2E 测试 stub · LEADER-E2E-001 PASS · 5 skipped | 🟡 open | +1 PASS · 5 SKIPPED |
| **PR-4.1** chart 完整化（缺） | deployment.yaml + service.yaml + CRD + Dockerfile | ⏸ P0 跟进 | 启用 5 skipped |
| **PR-5** MEMORY + ADR 同步 | ADR-0006 §M-7 + L3-5/L3-6 §M.2 + ROADMAP + README + CONSTITUTION-CHANGELOG + 本文档 | ✅ done (#88) | 0 测试，纯文档 |

## §2 Phase 2 留在 main 的复用资产

| 资产 | 路径 | Phase 3 用途 |
|---|---|---|
| kind_cluster session fixture | `tests/e2e/conftest.py` | Phase 3 K8sBackend E2E 共享 |
| e2e_namespace function fixture | `tests/e2e/conftest.py` | Phase 3 K8sBackend E2E 共享 |
| per_test_lease fixture | `tests/e2e/conftest.py` | K8sLeaseLeaderElector 多副本测试 |
| e2e-envtest.yml workflow | `.github/workflows/e2e-envtest.yml` | Phase 3+ 所有 E2E 测试统一入口 |
| K8sLeaseLeaderElector 实装 | `services/knowledge-memory-service/src/.../reconciler/k8s_lease_leader_elector.py` | Phase 3 多副本支持直接复用 |
| LeaderElector Protocol + runtime_checkable | `reconciler/leader.py` | Phase 3 任何新 backend 复用 |
| InProcessLeaderElector（默认） | `reconciler/leader.py` | Phase 3 默认 backend 保持 in_process |

## §3 chart 缺口（PR-4.1 必前置 · #87 发现）

Helm chart 当前仅 RBAC 4 模板（`role_read.yaml` / `role_write.yaml` / `rolebinding.yaml` / `serviceaccount.yaml`），缺失 4 项关键资产：

| 缺失资产 | PR-4.1 待办 | 优先级 | 估计工作量 |
|---|---|---|---|
| `helm/knowledge-memory-service/crds/memory-crd.yaml` | 基于 `packages/operator/src/.../memory.py` Memory 模型反射生成 CRD schema | P0 | 30-45 min |
| `helm/knowledge-memory-service/templates/deployment.yaml` | kopf operator pod + replicas=1 + leaderElection backend env + resources 限制 | P0 | 30 min |
| `helm/knowledge-memory-service/templates/service.yaml` | port 8080 + /healthz + /readyz + /metrics | P0 | 15-20 min |
| `Dockerfile` | python:3.12-slim + uv + workspace install + kopf entrypoint | P0 | 20-30 min |

PR-4.1 完成后，启用 5 个 skipped E2E 测试（LEADER-E2E-002 + H-RM-E2E-001 + H-QM-E2E-001 + LIFECYCLE-E2E-001/002）。

## §4 Phase 3 入口决策点

Phase 3 启动决策由 `OPEN-MEMORY-002`（多副本 v0.5+）触发。决策清单：

1. **K8sBackend 实装**：替换 InMemoryBackend 为 CustomObjectsApi 直接操作 CRD（共享 InProcess + K8s 双 backend · Helm `backend=k8s` opt-in）
2. **多副本生产支持**：replicaCount > 1 + leaderElection.backend=k8s 默认（与 Phase 2 spike 形成连续性）
3. **vector DB backend 候选**（OPEN-MEMORY-003 v0.5+）：Milvus / Qdrant / pgvector · 5 维矩阵 + Memory 生命周期算法直接复用
4. **Memory PII 加密**（OPEN-MEMORY-004 安全评审后）：encryption-at-rest + cert-manager mTLS 启用
5. **Multi-cluster 同步**（OPEN-MEMORY-005 v1.0+）：跨 cluster memory 同步（暂不进入 Phase 3）

## §5 5 项关键不变量保持（ADR-0006 D 方案 + L3-6 §1.2）

| # | 不变量 | 状态 | Phase 3 保持要求 |
|---|---|---|---|
| 1 | 单 Pod 第二进程 → 单进程 | ✅ 100% | K8sBackend 引入后必须保持单进程 leader + 多副本 backend 共享 |
| 2 | 60s MemoryReconciler timer | ✅ 100% | K8sBackend reconcile 周期与 InProcess 保持一致 |
| 3 | L3-5/L3-6 共享 Deployment | ✅ 100% | Phase 3 不拆 deployment · 引入 K8sBackend = 加 config 而非新 pod |
| 4 | 4 纯函数数学不变 | ✅ 100% | K8sBackend 持久化路径不修改算法（apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion） |
| 5 | wire contract 不变（12 MEMORY_* 错误码） | ✅ 100% | TEST-MEM-051 集合相等静态断言持续 PASS |

## §6 测试策略（Phase 2 → Phase 3 增量）

| 层级 | Phase 2 终态 | Phase 3 增量 |
|---|---|---|
| UT（unit） | 60 测试 ID + K8s-LE 8 + RBAC 1 + H-RM/H-QM IT 4 | + K8sBackend mock 8-12 |
| CF（conformance） | wire DTO + RBAC + 12 错误码 | + K8sBackend wire 一致性 |
| TZ（time-travel） | FakeClock 注入 | 持续（K8sBackend 复用 FakeClock） |
| IT（integration） | mock K8s API | + K8sBackend envtest |
| E2E（end-to-end） | LEADER + LIFECYCLE + H-RM/H-QM（部分 skipped 等 PR-4.1） | + K8sBackend kind E2E（multi-pod 共享 backend 验证） |
| DEPLOY/PERF | helm template + promtool | + K8sBackend PERF 10K/50K 门禁验证（Phase 1 遗留） |

## §7 文档同步清单（已完成 · #88）

- ✅ ADR-0006 §M-6 + 新增 §M-7 Phase 2 spike 记录（PR #22-#25 + 5 项关键不变量 + Phase 3 边界）
- ✅ L3-5 §M.2 落地记录追加 #87 行
- ✅ L3-6 §M.2 落地记录追加 #87 行
- ✅ ROADMAP Phase 3 更新（L4-Phase1 5/5 + L4-Phase2 4/5 + chart 缺口 P0）
- ✅ README.md Project status 追加 L4 进度
- ✅ CONSTITUTION-CHANGELOG.md 追加 #88 行（L4-Phase1 5/5 + L4-Phase2 4/5 PR 不触发宪法修订）
- ✅ docs/phase3-handoff.md（本文档）

## §8 关键文件位置（Phase 3 实施参考）

| 文件 | 用途 |
|---|---|
| `docs/phase2/l4-phase2-spike-plan.md` | Phase 2 plan v1.0 推荐（24.5KB / 453 行 / §0-§7） |
| `docs/adr/0006-memory-transport.md` | ADR-0006 v1.0 Accepted D 方案（30.5KB） |
| `docs/spec/L3-file-specs/L3-memory-backend.md` | L3-6 v0.2.0 + v0.2.1（权威 · 5 项关键不变量 + reconcile 算法） |
| `docs/spec/L3-file-specs/L3-knowledge-service.md` | L3-5 v0.2.0 + v0.2.1（H-RM/H-QM handler 契约） |
| `services/knowledge-memory-service/src/.../reconciler/` | reconciler 模块（leader.py + k8s_lease_leader_elector.py + memory_reconciler.py + finalize.py） |
| `tests/e2e/conftest.py` | E2E fixtures（kind_cluster + namespace + lease） |
| `.github/workflows/e2e-envtest.yml` | E2E CI workflow |

## §9 Phase 3 启动检查清单

Phase 3 启动前必须完成：

- [ ] **PR-4.1 chart 完整化**（P0 · chart 缺口修复 · 预计 90-120 min）
- [ ] **PR-5 MEMORY + ADR 同步**（✅ 已完成 #88）
- [ ] **OPEN-MEMORY-002 决策通过**（多副本 v0.5+ · 文档化）
- [ ] **K8sBackend 设计评审**（Phase 3 plan v1.0 推荐 · 类似 Phase 2 plan 流程）
- [ ] **宪法 v0.5.0 兼容性确认**（§14.5 MVP 例外窗口内 · 如触发 v0.6.0 升级需提前文档化）

## §10 不在 Phase 3 范围

- 多副本生产 GA（OPEN-MEMORY-002 v0.5+ · 需额外测试 + 灰度策略）
- Vector DB backend（OPEN-MEMORY-003 · v0.5+ 独立启动）
- Memory PII 加密（OPEN-MEMORY-004 · 安全评审后）
- Multi-cluster 同步（OPEN-MEMORY-005 · v1.0+）
- 5 维矩阵扩展（如新增 agent-team 维度 · 需宪法 §2 修订）
- 12 MEMORY_* 错误码调整（需 ADR 触发）

## §11 风险与缓解（Phase 3 启动时关注）

| 风险 | 影响 | 缓解 |
|---|---|---|
| chart 缺口未修复 | Phase 3 E2E 全 skipped | PR-4.1 前置 · 必修复 |
| K8sBackend 引入破坏 4 纯函数 | 算法 regression | 严格遵循 prepare/bind/commit/rollback · 4 纯函数单元测试 ≥ 95% 覆盖率 |
| 多副本 backend 状态共享冲突 | 数据竞争 | leader election 强约束 + 30s grace + finalize 5 步顺序幂等 |
| Performance 10K/50K 门禁失败 | Phase 3 不达标 | Phase 1 遗留 · Phase 3 触发强制 PASS · K8sBackend 后端性能需 ≥ InProcess 70% |
| 宪法 §14.5 例外窗口失效（v1.0 发布） | Phase 3 必须升级宪法 | 提前 v0.6.0 升级 · 文档化 |
| Branch Protection 未启用 | CI 失败未阻断 merge · #81 pyright gap 重现 | 用户 web 端 admin · Phase 3 启动前完成 |

---

> **Phase 2 → Phase 3 交接就绪** · 2026-08-09 #88 · PR-4.1 是 Phase 3 启动的 P0 前置 · 项目发起人决策 PR-4.1 vs Phase 3 优先级