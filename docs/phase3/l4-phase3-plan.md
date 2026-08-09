# L4-Phase3 Plan v0.1-draft

| 字段 | 值 |
|---|---|
| 文档版本 | **v0.1-draft**（2026-08-09 · #91 启动） |
| 上游 | Phase 2 plan v1.0 推荐（已 closed）+ Phase 3 handoff v0.1-draft（已 closed）+ 8 个 L3 评审通过 |
| 下游 | Phase 3 4 候选实装 · OPEN-MEMORY-002（多副本 v0.5+）触发 · 项目发起人决策 4 项优先级 |
| 关联 PR | Phase 2 PR #22-#28 + #29 hotfix（28 merged）· Phase 3 PR-1~PR-5 待启动 |
| main HEAD | `672cb61`（含 PR #28 E2E unskip + PR #29 hotfix ruff format）|

---

## §1 目标与边界（Phase 3 4 候选）

| # | 实装 | 优先级 | OPEN-MEMORY | Phase 3 PR | 估计工作量 |
|---|---|---|---|---|---|
| 1 | **A2A HTTP JSON-RPC server**（recordMemory/queryMemory） | P0 前置 | -002 前置 | PR-1 | 60-90 min |
| 2 | K8sBackend 完整实装（替换 InMemoryBackend · CustomObjectsApi） | P1 | -002 | PR-2 | 90-120 min |
| 3 | 25 指标 ServiceMonitor 全量验证（chart §9.8 + Operator 真实输出） | P1 | -002 | PR-3 | 45-60 min |
| 4 | H-RM/H-QM-E2E-001 实装（kind + helm install + HTTP POST） | P1 | -002 依赖 | PR-4 | 45-60 min |
| 5 | Phase 3 文档同步（MEMORY + ADR + ROADMAP + CONSTITUTION） | P2 | - | PR-5 | 30 min |

**总工作量**：4.5-6 小时（按 2h/day = 3 天集中或 1 周分散）

**业务价值**：
- PR-1 解锁 H-RM/H-QM-E2E-001 + 提供 A2A 协议栈外部接口（其他 agent framework 调用入口）
- PR-2 解锁 K8sBackend 持久化（生产可用 · 不再依赖进程内存）
- PR-3 提供真实可观测性（Prometheus 25 指标 + 8 alerts 验证）
- PR-4 完整 Phase 2 5 skipped E2E 集合

---

## §2 设计决策（5 项关键 · 需用户/项目发起人评审）

### §2.1 A2A HTTP server 框架选型

- **选项 A · aiohttp**（kopf 1.44+ 内置 health_reporter 已用）：✅ 与 main.py 单进程一致（ADR-0006 D）· 0 新增依赖 · 但 aiohttp 仅用于 health endpoint，handler 集成需手写
- **选项 B · FastAPI + uvicorn**（行业标准）：✅ 自动 OpenAPI 文档 · async 友好 · 需新增 2 依赖 · 与 ADR-0006 D 单进程需验证（uvicorn 与 kopf event loop 集成）
- **选项 C · starlette**（FastAPI 底层 · 轻量）：✅ 轻量 · async 友好 · 0 OpenAPI · 与 kopf event loop 集成更可控

**推荐**：C starlette（最小依赖 + 与 kopf event loop 集成清晰 · OpenAPI 需求 P2 后置）

### §2.2 JSON-RPC 协议版本

- **JSON-RPC 2.0**（Google A2A 协议官方）：✅ 行业标准 · 与外部 agent framework 互通
- **A2A SDK 内置方法**：`recordMemory` + `queryMemory`（L3-6 §4.3 + §4.4 契约）

### §2.3 K8sBackend 持久化路径

- **CustomObjectsApi 直接操作 Memory CRD**（不引入新 CRD）：✅ 复用 Phase 1 PR-4.1 Memory CRD +12 字段 · 与 kopf reconcile 兼容 · 0 新 schema
- **替换 InMemoryBackend**：`backend=k8s` opt-in + `backend=in_process` 默认 · Helm values.yaml 切换

### §2.4 K8sBackend 并发模型

- **leader 独占写 + 非 leader read**（与 K8sLeaseLeaderElector 兼容）：✅ 单 leader 保证 reconcile 幂等 · 读路径可并行（queryMemory 不修改状态）
- **etcd watch + cache**（k8s client 内置）：✅ 复用 k8s-python-client informers · 30s 同步延迟可接受

### §2.5 25 指标 ServiceMonitor 验证策略

- **真实 Operator 输出 + Prometheus scrape**（kind cluster + helm install + prometheus operator）：✅ 生产等价 · 但需 prometheus operator 依赖
- **Mock Prometheus endpoint + 静态断言**（轻量）：✅ 0 依赖 · 但仅验证 metric 名称 + label，不验证 scrape 协议

**推荐**：真实 kind cluster（与 Phase 2 PR-4.1 + PR-4.1.1 复用）

---

## §3 PR 序列（4-5 串行 + 1 文档同步）

### PR-1 A2A HTTP JSON-RPC server（PRIORITY · 60-90 min · 启动）

- `services/knowledge-memory-service/src/.../api/server.py` 新文件：starlette app + JSON-RPC dispatcher
- `services/knowledge-memory-service/src/.../main.py` 修改：kopf.run 后启动 aiohttp 服务器（同一 event loop）
- 2 端点：`/jsonrpc/record_memory` + `/jsonrpc/query_memory`
- 测试：12 测试 ID（4 JSON-RPC envelope 验证 + 4 业务 round-trip + 4 错误传播）
- wire contract 不变（12 MEMORY_* 错误码 → JSON-RPC error.code 映射）
- PR 收口：lint / pytest / pyright / chart values.yaml livenessProbe 端口更新

### PR-2 K8sBackend 完整实装（90-120 min · 必前置 OPEN-MEMORY-002 决策）

- `services/knowledge-memory-service/src/.../backend/k8s_backend.py` 新文件：CustomObjectsApi wrapper
- `services/knowledge-memory-service/src/.../backend/in_memory_backend.py` 保持（默认 backend=in_process）
- helm values.yaml：新增 `backend` field（enum: in_process/k8s）
- 8-12 测试 ID（4 mock K8s API IT + 4 wire 一致性 + 4 round-trip）
- 不破坏 4 纯函数（apply_decay / apply_reinforce / gc_expired / is_eligible_for_promotion 数学不变）

### PR-3 25 指标 ServiceMonitor 全量验证（45-60 min）

- Operator 暴露 `/metrics` 端口（Prometheus client 库）
- 25 指标覆盖：reconcile / admission / query / leader / finalize / errors（按 L3-6 §9.8 metricRelabelings 5 命名空间）
- ServiceMonitor scrape 配置（helm values.yaml + cluster prometheus operator）
- E2E：kind cluster + helm install + Prometheus scrape + query 25 指标名称 + label

### PR-4 H-RM/H-QM-E2E-001 实装（45-60 min）

- 启用 PR-25 留下的 2 个 skipped E2E
- kind + helm install + HTTP POST `/jsonrpc/record_memory` + `/jsonrpc/query_memory`
- round-trip：apply Memory CR → POST record → query 结果包含 → POST query 验证
- 复用 Phase 2 e2e-envtest.yml（不动 workflow）

### PR-5 文档同步（30 min · 收口）

- MEMORY.md + #92-#96 session section
- ADR-0006 §M-7 Phase 2 → Phase 3 记录
- L3-5/L3-6 §M.2 落地记录 Phase 3 PR 序列
- ROADMAP Phase 3 5/5 完成
- CONSTITUTION-CHANGELOG Phase 3 PR 序列（**不触发宪法修订** · ADR-0006 D 方案 + Phase 3 plan v1.0 推荐）

---

## §4 验收清单（6 项）

1. **PR-1 完成**：A2A HTTP server 实装 + 12 测试 PASS + ruff/format/pyright 全绿
2. **PR-2 完成**：K8sBackend 完整实装 + 8-12 测试 PASS + helm `backend=k8s` smoke test
3. **PR-3 完成**：25 指标真实可观测 + ServiceMonitor scrape OK + 8 alerts 触发测试
4. **PR-4 完成**：H-RM-E2E-001 + H-QM-E2E-001 从 skipped → PASS
5. **5 项关键不变量 100% 保持**：单进程 / 60s timer / 共享 Deployment / 4 纯函数 / wire contract
6. **宪法 v0.5.0 §14.5 MVP 例外窗口兼容**：Phase 3 不触发 v0.6.0 升级（除非 multi-pod GA）

---

## §5 风险与缓解（10 项）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | starlette 与 kopf event loop 冲突 | PR-1 失败 | kopf 1.44+ aiohttp 集成已验证 · starlette 同 aiohttp loop 兼容 |
| 2 | K8sBackend 引入破坏 4 纯函数 | 算法 regression | 严格 InMemoryBackend → K8sBackend 一一对应 · 4 纯函数单元测试覆盖率 ≥ 95% |
| 3 | 25 指标 Operator 输出不全 | PR-3 部分验证失败 | L3-6 §9.8 锁定 25 指标清单 · 逐项 PR-3 验证 |
| 4 | H-RM/H-QM-E2E kind setup 复杂 | PR-4 拖延 | 复用 Phase 2 e2e-envtest.yml · 5-8 min kind setup 已成熟 |
| 5 | Branch Protection 未启用（已知 P0） | PR-2/3/4 CI 失败未阻断 | 项目发起人 web 端 admin · PR-1 启动前完成 |
| 6 | JSON-RPC error.code 映射错误 | wire contract 漂移 | TEST-MEM-051 集合相等静态断言持续 PASS · 错误码权威名 L2-4 §9.1 |
| 7 | K8sBackend 性能不达标 | Phase 3 不可用 | PERF 10K/50K 门禁 · K8sBackend ≥ InProcess 70% 性能 |
| 8 | Prometheus operator 依赖 | PR-3 部署复杂 | kind cluster 内置 kube-prometheus-stack · Helm chart 复用 |
| 9 | MemoryReconciler timer 与 K8sBackend 冲突 | PR-2 reconcile 失败 | 60s timer 保持 · leader 独占写 · finalize 5 步顺序幂等 |
| 10 | 宪法 v0.5.0 §14.5 例外窗口失效 | Phase 3 强制 v0.6.0 升级 | 提前文档化 · multi-pod GA 推迟至 v0.5 真正发布后 |

---

## §6 关键不变量保持（5 项 · ADR-0006 D 方案 + L3-6 §1.2）

| # | 不变量 | Phase 3 保持要求 |
|---|---|---|
| 1 | 单 Pod 第二进程 → 单进程 | A2A HTTP server + K8sBackend 同进程（k8s client + starlette 同 event loop） |
| 2 | 60s MemoryReconciler timer | K8sBackend reconcile 周期 60s 不变（与 InProcess 一致） |
| 3 | L3-5/L3-6 共享 Deployment | Phase 3 不拆 deployment · backend 切换仅 config |
| 4 | 4 纯函数数学不变 | K8sBackend 持久化路径不修改算法 |
| 5 | wire contract 不变（12 MEMORY_* 错误码） | TEST-MEM-051 集合相等静态断言持续 PASS |

---

## §7 测试策略增量（Phase 2 → Phase 3）

| 层级 | Phase 2 终态 | Phase 3 增量 |
|---|---|---|
| UT | 60 + K8s-LE 8 + RBAC 1 + H-RM/H-QM IT 4 = 73 | + JSON-RPC envelope 4 + K8sBackend mock 8 = 85 |
| CF | wire DTO + RBAC + 12 错误码 | + JSON-RPC error.code 映射 4 = 18 |
| TZ | FakeClock 注入 | 持续（PR-2 K8sBackend 复用 FakeClock） |
| IT | mock K8s API | + K8sBackend envtest + JSON-RPC round-trip 8 = 24 |
| E2E | LEADER + LIFECYCLE + H-RM/H-QM（部分 skipped） | + K8sBackend kind E2E + JSON-RPC E2E + 25 指标 scrape = 35 |
| DEPLOY/PERF | helm template + promtool | + K8sBackend PERF 10K/50K + 25 指标 scrape 验证 = 5 |

**总测试增量**：约 60 测试 ID（85-24-35-5 vs Phase 2 60+8+1+4=73）

---

## §8 不在范围（明确剔除 · Phase 3 边界）

- ❌ Multi-cluster 同步（OPEN-MEMORY-005 v1.0+）
- ❌ Vector DB backend（OPEN-MEMORY-003 v0.5+ 独立启动）
- ❌ Memory PII 加密（OPEN-MEMORY-004 安全评审后）
- ❌ 多副本生产 GA（OPEN-MEMORY-002 v0.5+ · 需额外测试 + 灰度策略）
- ❌ 5 维矩阵扩展（如新增 agent-team 维度 · 需宪法 §2 修订）
- ❌ 12 MEMORY_* 错误码调整（需 ADR 触发）

---

## §9 Phase 3 启动检查清单（启动前必做）

- [x] PR-4.1 chart 完整化（#27 ✅）+ PR-4.1.1 E2E unskip（#28 ✅）+ PR #29 hotfix ruff format（✅）
- [x] Phase 2 PR-5 MEMORY + ADR 同步（#88 ✅）
- [x] OPEN-MEMORY-002 决策通过（用户「合并 PR #29 + 启动 Phase 3」决策）
- [ ] **Branch Protection 启用**（必做 · P0 · PR-1 启动前完成 · 项目发起人 web 端 admin）
- [ ] K8sBackend 设计评审（项目发起人评审本 plan §2 + §3）
- [ ] 宪法 v0.5.0 §14.5 MVP 例外窗口兼容性确认（PR-5 收口前）

---

## §10 PR 启动决策（建议）

按用户 2h/天 + 单次会话 2h 限制，推荐 PR 启动顺序：

- **下一次会话（#92）**：PR-1 A2A HTTP JSON-RPC server（60-90 min · 单 session 可完成）
- **#93**：PR-2 K8sBackend（90-120 min · 可能需 Subagent 接力）
- **#94**：PR-3 25 指标（45-60 min · 单 session）
- **#95**：PR-4 H-RM/H-QM-E2E（45-60 min · 单 session · 可能需 BP 启用）
- **#96**：PR-5 文档同步（30 min · 收口）

---

## M.1-M.6 元数据

- **M.1 版本**：v0.1-draft（2026-08-09）
- **M.2 落地记录**：#91（2026-08-09 · Phase 3 启动决策 · PR #29 合并 + Phase 3 plan v0.1-draft）
- **M.3 关联 PR**：Phase 2 #22-#28 + #29 hotfix · Phase 3 PR-1~PR-5 待启动
- **M.4 下次会话入口**：#92 PR-1 A2A HTTP JSON-RPC server 实装（按本 plan §3 PR-1）
- **M.5 关注项台账**：
  - ① Branch Protection 未启用（必做 · 项目发起人 web 端 admin · PR-1 启动前）
  - ② starlette 与 kopf event loop 集成验证（PR-1 启动时 spike）
  - ③ K8sBackend 性能门禁 10K/50K（PR-2 收口前 PERF 验证）
  - ④ 25 指标 Operator 真实输出（PR-3 收口前逐项验证）
  - ⑤ H-RM/H-QM-E2E kind setup 复用（PR-4 收口前确认 e2e-envtest.yml 完整）
- **M.6 文档状态**：v0.1-draft 骨架稿（极简 9 节 · ~10KB · 待 #92 启动 PR-1 时补完细节）

---

> **Phase 3 启动就绪** · 2026-08-09 · PR-1 A2A HTTP server 是 Phase 3 第一步 · 项目发起人评审本 plan §2 5 项设计决策 + §3 PR 序列