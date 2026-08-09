# Session #87 — Phase 2 PR-4 kind E2E spike 基础设施 + chart 缺口发现（2026-08-09）

## 概述

主 Agent（5-8% 水位）· 本会话起点：MEMORY.md #86 stale（仅记录到 #83 + Phase 1 5/5）· 用户指令「继续推进项目」。

**关键发现 3 项**：
1. **MEMORY.md 大幅 stale** — 实际已 merged PR #22 (RBAC) + #23 (K8sLease 192 PASS) + #24 (H-RM/H-QM stubs)，main HEAD `b1556db`，179/179 PASS。本会话起点本地 main 落后 2 commits，fast-forward 后同步。
2. **orphan 分支回归** — `feat/l4-phase2-step2-k8s-lease-leader-elector` 含 commit 193343a，表面声称 K8sLease 覆盖率 93% + create-429 重试修复（+14 tests · 192 PASS），但 diff 实际**把 PR #24 的 H-RM-IT-001 / H-RM-CF-001 / H-QM-IT-001 / H-QM-CF-001 真实测试降级为 `assert True` stub**（典型脏 cherry-pick regression）· 用户决策：直接丢弃整个分支。
3. **Helm chart 严重不完整** — Phase 2 plan §3.4 假设 chart 完整，但实际仅 RBAC 4 模板，缺失 deployment.yaml / service.yaml / CRD / Dockerfile · Phase 2 PR-4 无法按原计划实装 · 用户决策：Path A 诚实化 PR-4（基础设施 + skip 机制）。

**本会话交付**：
- ✅ PR #25 创建：`feat/l4-phase2-step4-kind-e2e`（8 files · 546 insertions）
  - `tests/e2e/__init__.py` + `tests/e2e/knowledge_memory/__init__.py`（namespace）
  - `tests/e2e/conftest.py`（session-scoped kind_cluster + function-scoped e2e_namespace + per_test_lease + CLI 检测 fixtures + chart_status 完整性检查）
  - `tests/e2e/knowledge_memory/test_leader_election.py`（LEADER-E2E-001 PASS · LEADER-E2E-002 SKIPPED）
  - `tests/e2e/knowledge_memory/test_handle_record_memory.py`（H-RM-E2E-001 SKIPPED）
  - `tests/e2e/knowledge_memory/test_handle_query_memory.py`（H-QM-E2E-001 SKIPPED）
  - `tests/e2e/knowledge_memory/test_memory_lifecycle.py`（LIFECYCLE-E2E-001/002 SKIPPED）
  - `.github/workflows/e2e-envtest.yml`（workflow_dispatch + nightly cron '30 1 * * *' UTC + pull_request labeled 'e2e' triggers · concurrency cancel-in-progress · timeout-minutes 15 · kind v0.24.0 + helm v3.16.0 + kubectl 安装）

## 决策路径

**Q1: orphan 分支处置？** → 用户选 A: 直接丢弃整个分支（推荐）
**Q2: PR-4 启动？** → 用户选 A: 启动 PR-4（推荐）
**Q3: chart 缺口处理？** → 用户选 Path A: 诚实化 PR-4 = 基础设施 + 跳过机制（推荐）

## 关键文件清单

| 文件 | 状态 |
|---|---|
| `tests/e2e/conftest.py` | 254 行 · session kind_cluster fixture + 4 CLI detection fixtures + chart_status |
| `tests/e2e/knowledge_memory/test_leader_election.py` | 85 行 · 2 tests（1 PASS + 1 SKIPPED）|
| `tests/e2e/knowledge_memory/test_handle_record_memory.py` | 36 行 · 1 test SKIPPED |
| `tests/e2e/knowledge_memory/test_handle_query_memory.py` | 30 行 · 1 test SKIPPED |
| `tests/e2e/knowledge_memory/test_memory_lifecycle.py` | 52 行 · 2 tests SKIPPED |
| `.github/workflows/e2e-envtest.yml` | 122 行 · CI workflow |

## 验证结果

```
pytest                  → 179 PASS (默认 testpaths 不含 tests/e2e)
pytest tests/e2e/ -v    → 1 passed (LEADER-E2E-001), 5 skipped (chart 缺口)
ruff check .            → All checks passed
ruff format --check .   → 134 files already formatted
pyright .               → 0 errors / 693 warnings (warning 数与 main baseline 持平)
```

## LEADER-E2E-001 修复

初始预期 `is_leader() == True`（错了）· 实际 `InProcessLeaderElector.__init__` 设 `_is_leader = False`，必须先调用 `await try_acquire_or_renew()` 才成为 leader · 修复后测试验证 acquire + renew idempotent 行为。

## 后续 PR-4.1（chart 完整化 · P0 跟进项）

按 PR #25 描述保留清单：
1. `helm/knowledge-memory-service/crds/memory-crd.yaml`（基于 `packages/operator/src/.../memory.py` Memory 模型反射生成 CRD schema）
2. `helm/knowledge-memory-service/templates/deployment.yaml`（kopf operator pod + replicas=1 + leaderElection backend env）
3. `helm/knowledge-memory-service/templates/service.yaml`（port 8080 + /healthz + /readyz + /metrics）
4. `Dockerfile`（python:3.12-slim + uv + workspace install + kopf entrypoint）
5. 启用当前 5 个 skipped 测试 + MEMORY.md 更新

## 下一里程碑

PR #25 等 CI 5 workflows 通过 · 项目发起人评审 Path A 决策 · 启动 PR-4.1（chart 完整化）或评估 Phase 3 优先级。