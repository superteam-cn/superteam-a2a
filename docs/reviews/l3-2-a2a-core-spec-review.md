# superteam-a2a — L3-2 A2A Core Library 文件级 Spec 评审报告

> **评审日期**：2026-07-28 · #54 会话
> **评审对象**：[`docs/spec/L3-file-specs/L3-a2a-core.md` v0.2-draft-full](../spec/L3-file-specs/L3-a2a-core.md)（156KB / 2808 行 / 16 主章节 + 2 附录）
> **配套上游 Spec**：[L2-1 A2A Protocol Spec v0.2.0](../spec/L2-module-specs/L2-a2a-protocol.md)（72KB / 1919 行；2026-07-24 #22 评审通过）
> **配套上游 Design**：[L2-1 A2A Protocol Design v0.2.0](../design/L2-modules/L2-a2a-protocol.md)（44KB / 981 行；2026-07-24 #20 落地）
> **配套 L3 同级**：[L3-1 Operator Core 文件级 Spec v0.2-draft-full](../spec/L3-file-specs/L3-operator-core.md)（3750 行；2026-07-27 #49 §9 补完稿）
> **评审人**：项目发起人（单点评审 · 宪法 §14.5 MVP 例外时间窗口内）
> **评审依据**：[`CONSTITUTION.md`](../../CONSTITUTION.md) v0.5.0 §3.8 Python-first + §6 mTLS + §7 可观测性 + §9.7 静态质量 + §13.6 上游追踪 + §14.4 评审门禁 + §16 会话纪律；[ADR-0005 Python-first](../adr/0005-python-first-technology-stack.md) §3.2 + §6 + §8 + §9.1 + §13.1 + §13.6；[L1 Architecture v0.2.0](../design/L1-architecture.md) §3.4 通信层 + §4.1 C-2；[L1 Spec v0.2.0](../../spec/L1-system-spec.md) §5 + §15 + §16；[L2-1 Spec v0.2.0](../spec/L2-module-specs/L2-a2a-protocol.md) 全文（上游权威）
> **上一版评审**：无（L3-2 首次评审；v0.1-draft Go baseline 未评审，已归档至 `docs/archive/pre-python-2026-07-24/`）
> **参照模板**：[L2-3 Adapter Spec Python 评审](./l2-3-adapter-spec-python-review.md)（53.5KB / 641 行 / §A-§P）+ [L3-1 Operator Core Spec §9 验收清单](../spec/L3-file-specs/L3-operator-core.md)（30 条 + 277 ID）

---

## 评审概览

### 评审维度与结论

| 维度 | 评审范围 | 结论 |
|------|----------|------|
| **A. 文档完整性** | §0-§15 + 附录 A/B + 头部（版本/状态/supersede/上游约束/配套 Spec）+ 阅读指南 + public API surface + 30 文件清单 | ✅ PASS |
| **B. 设计深度** | 7 子包 + 4 extension router Pydantic schema + mTLS/SPIFFE + ASGI server + Discovery/Client + async offload + 24 错误码 + 15 指标 + 上游追踪 + 测试策略 + Helm values + 4 张生命周期时序图 | ✅ PASS |
| **C. Python-first 硬约束** | ADR-0005 §3.2/§6/§8/§9.1/§13.1（`a2a.upstream` boundary + Uvicorn 单 worker + anyio offload + uv workspace + mTLS 强制 + Ruff ST-A2A-BOUNDARY） | ✅ PASS |
| **D. wire contract 一致性** | 与 v0.1.0 Go baseline + L2-1 Spec v0.2.0 完全一致（camelCase / RFC 3339 / 24 错误码数字 / Task FSM / 15 metric name） | ✅ PASS |
| **E. 安全性** | mTLS 强制 + TLSv1_3 + CERT_REQUIRED + SPIFFE URI SAN + 私钥 mode 0600 + ClusterRole 最小权限 + NetworkPolicy + 容器加固 | ✅ PASS |
| **F. 可观测性** | 15 Prometheus 指标（11 A2A + 4 runtime）+ OTel 显式 provider + structlog 6 字段 + 敏感字段脱敏 | ✅ PASS |
| **G. 异步 / 单进程 / 资源** | Uvicorn 1 worker + anyio.to_thread.run_sync CPU offload + httpx 连接池 + RateLimit + CircuitBreaker + P2C | ✅ PASS |
| **H. 错误模型 + Retryable** | 24 错误码 IntEnum（5+6+7+6）+ METHOD_IDEMPOTENT 表 + Retry 退避 + CircuitBreaker 3 状态 | ✅ PASS |
| **I. 测试策略 + ID 矩阵** | 6 层级金字塔 + 276 测试 ID（21 组文件级映射，与 §14.2 一致） | ✅ PASS |
| **J. 颗粒度偏差 + 跨文档一致性** | 156KB / 2808 行 vs L3-1 3750 行同等级别；文件级粒度合理 | ✅ PASS（有偏差说明） |

**结论**：**L3-2 A2A Core 文件级 Spec v0.2-draft-full 通过评审，具备升级 v0.2.0 条件**。0 阻塞项，3 关注项（见 §M），4 建议项（见 §M）。

---

## §A 文档完整性（PASS）

- 头部 10 段齐全：ADR-0005 supersede 标记 / 层级模块 ID / 代码位置 / 版本 / 状态 / Python 栈基线 / wire contract 不变性 / 上游约束 / 本 Spec 目的 / 配套 Spec。
- §0-§15 + 附录 A + 附录 B 全部落地，扫描全文 `占位` 关键词命中 15 处，全部为**业务语义描述**（如"占位类""cancelTask 占位 v0.5+"），非遗留的"待补完"占位章节标记；`#53+ 补完` / `⚠️ 占位章节` 类临时标记已在本次会话（#54）清理为 0。
- §1.3 文件清单（30 Python + 9 Helm + 30 测试文件镜像）与 §2.3 逐子包展开一致；测试 ID 前缀分布表在 §1.3 与 §11.2 两处重复出现但数字一致（交叉核验：`UT-T-01~22` = 22、`UT-E-01~15` = 15、`UT-SRV+MW` = 34、`UT-CLI-*` = 65、`UT-EXT-*` = 22、`UT-MT-*` = 18、`UT-OB-*` = 30、`UT-UT-*` = 10，UT 类合计 216，加 IT 15 + CF 22 + E2E 5 + CT 5 + PROP 5 + HTTP 8 = 60，总计 276 ✅）。
- 附录 A 5 子表（L1/L2/ADR+宪法/配套 L3/归档）+ 附录 B 6 子表（架构/接口/可见性/安全/性能/可观测性测试）均完整展开，无省略。

**本次评审前修正**：会话内发现并修正了 §11.2 测试 ID 汇总表旧值 105（与逐文件枚举 276 冲突）、3 处遗留"§11.4 占位"引用（该节已存在）、§1.1 边界表对 276 ID 的误导性描述（"不创造新测试 ID"）。修正记录见 spec 头部变更记录 v0.2-draft-full #53-#54。

---

## §B 设计深度（PASS）

- **7 子包完整契约**：`server/` 4 middleware + lifespan；`client/` A2AClient + Retry + CircuitBreaker + Discovery + P2C + AgentCardCache；`extensions/` ExtensionRouter Protocol + 4 router 占位 + `discover_routers`；`mtls/` SSLContext + SPIFFE + CertHotReloader；`observability/` metrics + tracing + logging + event_loop；`utils/` offload；`_internal/` 私有 wire helper。
- **4 扩展 method Pydantic v2 schema**：QueryKnowledge / GetKnowledgeItem / RecordMemory / QueryMemory 请求响应共 8 model，字段级约束（`extra="forbid"` 隐含、`idempotency_key` 必填校验、`scope_level` 枚举）。
- **mTLS/SPIFFE**：`build_server_ssl_context` + `extract_spiffe_id` + `validate_spiffe_id` + `CertHotReloader`（原子替换 + 失败回退）四段完整契约，与 L3-1 admission webhook 的 TLS 实现（§4）明确边界隔离（互不共享 context，附录 B.4 U-12 决策记录）。
- **4 张生命周期时序图**（§13.1-§13.4）覆盖 startup / steady state / graceful shutdown / cert reload，每张图都标注了断言点 + 测试 ID，可直接作为 L4 集成测试脚本依据。
- **Helm values 9 模板完整展开**（§12）：deployment 双端口三探针 + service + secret-tls cert-manager 注解 + networkpolicy + prometheusrule + servicemonitor + rbac；Pydantic `A2aCoreConfig` 与 `values.schema.json` 的一致性校验点已在 §14.3 #9 列出。

---

## §C Python-first 硬约束（PASS · ADR-0005 §3.2 + §6 + §8 + §9.1 + §13.1 + 宪法 §3.8）

| 约束 | 落地位置 | 结论 |
|------|----------|------|
| `a2a.upstream` 唯一 SDK import 入口 | §1.2 + §1.4 + 附录 B.1 | ✅ |
| 业务层禁止 `import a2a`（Ruff `ST-A2A-BOUNDARY`） | §1.2 + §11.4 | ✅ |
| Uvicorn `--workers 1` 单进程原则 | §5 + §12 + 附录 B.1 | ✅ |
| `anyio.to_thread.run_sync` CPU offload + `CapacityLimiter` | §7 + 附录 B.5 | ✅ |
| uv workspace 布局（`packages/a2a-core/src/superteam_a2a/a2a/`） | §2.1 + 附录 B.1 | ✅ |
| mTLS 强制（无明文回退） | §4 + 附录 B.4 | ✅ |
| Python 3.12+ 精确下限（收敛 U-2） | §11.4 + §15.1 | ✅ |
| 静态门禁 5 重（ruff/pyright strict/bandit/pip-audit/interrogate） | §11.4 + §14.3 #19 | ✅ |

---

## §D wire contract 一致性（PASS · 与 v0.2.0 Design + v0.1.0 Go baseline 完全一致）

- 6 method wire shape（`sendMessage` / `getTask` / `queryKnowledge` / `getKnowledgeItem` / `recordMemory` / `queryMemory`）与 4 endpoint 路径全部继承 L2-1 Spec §3/§6，未改名未改路径。
- **24 错误码**（标准 5 + A2A 域 6 + Knowledge 7 + Memory 6）在 §8.2 落地为 `StandardRpcError` + `ProjectRpcError` 双 IntEnum，数字与 L1 Spec §5.7 + v0.1.0 Go baseline 一致；contract test（`CT-A2A-01~05`）锁定 wire shape。
- **15 Prometheus 指标**（11 `superteam_a2a_*` + 4 `superteam_python_*`）核验：metric name 全部符合 Prometheus 命名规范，与 L2-1 Spec §9.1 的 11 个基线指标逐一对照一致，4 个新增（`cert_reload_failures_total` / `extension_router_dispatch_total` / `request_body_bytes` / `response_body_bytes`）在 §15.2 S-3 已确认为"新增而非改名"，不破坏 wire contract。
- `a2a.cancelTask` / `a2a.subscribeTask` / SSE 占位符未提前暴露（§1.4 + §3.5 + §14.1 D 维度已核验）。

---

## §E 安全性（PASS）

- mTLS：`TLSv1_3` + `CERT_REQUIRED` + 私钥 mode 0600 校验，缺失证书触发 `MtlsConfigError` + readiness=false（§4 + §14.1 C 维度）。
- SPIFFE：URI SAN 解析 + trust_domain 校验，不匹配 → 401（§4 + `UT-MT-07~12`）。
- 证书热更新：原子替换 + 失败回退旧 context + 指标上报（§4.3 + `UT-MT-13~18` + `IT-A2A-06~09`）。
- 最小权限：ClusterRole 仅 `endpointslices` + `services` read-only（§12 + 附录 B.4）。
- 容器加固：`python:3.12-slim` + 非 root uid=65532 + drop ALL capabilities（§11.4 + §14.3 #17）。
- 敏感字段脱敏：`api_key` / `memory_content` 禁入日志（§9 + `UT-OB-24/25`）。

---

## §F 可观测性（PASS）

- 15 指标（11 A2A + 4 runtime）在 §9.1 完整展开 + label 基数约束（§9.1 末段）。
- OTel 显式 provider 注入避免测试污染全局（§9.2 + `UT-OB-14/15`）。
- structlog 6 必含字段 + JSON 格式 + trace_id 注入（§9 + `UT-OB-21~26`）。
- event loop lag 监控 + thread offload queue depth（4 runtime 指标之二，§7.3 + `UT-OB-12/13/27~30`）。

---

## §G 异步 / 单进程 / 资源（PASS）

- Uvicorn 单 worker + K8s HPA 伸缩（§5 + §12，非 worker 内多并发）。
- httpx 连接池 `max_connections=100` + `timeout=30s` 默认值（§6，调优移交 L4 §15.3 P-1）。
- RateLimit token bucket 100 RPS + burst 200（§5 middleware，多副本全局限流推迟 v0.5+ §15.3 P-5）。
- CircuitBreaker `failure_threshold=5` + P2C 负载选择（§6 + `UT-CLI-54~73`）。
- graceful shutdown drain < 30s，readiness 先置 false 再逆序 stop（§13.3 + `UT-SRV-35/36`）。

---

## §H 错误模型 + Retryable（PASS）

- 24 错误码 `StandardRpcError` + `ProjectRpcError` 双 IntEnum（§8.2），wire shape 示例（§8.1）与 contract test 锁定一致。
- `METHOD_IDEMPOTENT` 表（§6）明确 `recordMemory` 需 `idempotencyKey` 才可重试，与 ADR-0003 §6 一致。
- RetryPolicy 退避计算 + jitter + `should_retry` 决策矩阵（§6 + `UT-CLI-44~53`）覆盖 DO_RETRY / DO_NOT_RETRY / METHOD_NOT_IDEMPOTENT 三态。

---

## §I 测试策略 + ID 矩阵（PASS）

- 6 层级金字塔（UT/Property/HTTP mock/SDK compat/Integration/E2E）占比分配合理（§11.1）。
- **276 测试 ID** 分 21 组映射到具体测试文件（§11.2.1-§11.2.21），本次评审逐文件核验加总 = 276，与 §14.2 验收表一致（详见 §A 修正记录）。
- conformance 套件接入流程（§11.3）+ 静态门禁 5 重（§11.4）+ 性能预算占位（§11.5）齐全。

---

## §J 颗粒度偏差 + 跨文档一致性（PASS · 合理）

- **颗粒度**：156KB / 2808 行，对比 L3-1 Operator Core 3750 行（同为文件级 Spec，L3-1 因 4 Controller + admission + Leader Election + Memory 5 大子模块更重）；L3-2 7 子包规模适中，颗粒度偏差属合理范围（约 0.75x，同一数量级）。
- **跨文档一致性**：§14.5 已列 10 条跨文档核验点（L1 Arch/Spec + L2-1/L2-2/L2-3/L2-4 Spec + ADR-0002/0003/0005 + L3-1 双向引用），本评审抽样核对 3 条（L2-1 wire contract、ADR-0003 Memory 错误码、L3-1 mTLS 边界隔离）均一致。

---

## §K 验收清单（§14 82 条硬验收 + 276 ID）

> 本节核验 L3-2 Spec §14 自身给出的验收清单**结构完整性**（不是逐条勾选执行——82 条硬验收 + 276 ID 的实际勾选属于 L4 实施阶段 + CI 验证范畴，此处评审的是清单本身是否可执行、口径是否自洽）。

| 子节 | 条数 | 结构核验 | 结论 |
|------|------|----------|------|
| §14.1 §A-§G 10 维度 | 34 | 每条均标注"对应位置"精确到章节号，可直接映射评审 §A-§H | ✅ PASS |
| §14.2 测试 ID 验收 | 21 组 / 276 ID | 与 §11.2 逐文件枚举加总一致（本评审核验，见 §A） | ✅ PASS |
| §14.3 部署与文档交付 | 20 | 覆盖指标/日志/Helm/RBAC/镜像/CI 门禁，无空泛表述 | ✅ PASS |
| §14.4 上游追踪 | 8 | 覆盖 pin/三级升级/contract 阻断/SDK 追踪责任，对应宪法 §13.6 | ✅ PASS |
| §14.5 跨文档一致性 | 10 | 覆盖 L1/L2 全部 4 个模块 + ADR-0002/0003/0005 + L3-1 | ✅ PASS |
| §14.6 评审与归档 | 10 | 覆盖评审报告/升级/归档/git/跨文档同步/ROADMAP/README/CHANGELOG/会话纪律 | ✅ PASS |
| §14.7 ACCEPT-A2A-* 不变量 | 8 | 命名规则与 L3-1 `ACCEPT-` 前缀一致，编号连续无跳号异常 | ✅ PASS |

**验收清单执行结论**：§14 结构自洽，可作为 L3-2 Spec 升级 v0.2.0 的唯一凭证，本次评审据此批准升级（见 §N 决议）。

---

## §L 优点（8 项）

1. **wire contract 三层锁定**：v0.1.0 Go baseline 业务语义 + L2-1 Spec v0.2.0 模块契约 + L3-2 文件级实现契约三层引用链清晰，任何字段修改都能追溯到权威来源。
2. **276 测试 ID 的可追溯性**：每个 ID 精确绑定到具体测试文件路径 + 行为断言一句话，L4 实施时无需猜测测试意图。
3. **§15 三层开放问题模式**：区分"继承上游未定项"/"本 Spec 起草新发现"/"Python 落地新增"，收敛状态用图例（✅/🟡/⬜/🔵）一眼可辨，优于简单列表。
4. **mTLS 与 L3-1 admission webhook TLS 的边界决策**（U-12）：明确两套 TLS 实现不共享 context，避免了隐性耦合。
5. **附录 B 6 子表的强度分级**（MUST/SHOULD/MAY）：让 L4 实施者清楚哪些约束不可协商。
6. **§13 生命周期时序图 + 测试矩阵不变性声明**：明确"本节只映射已有测试，不新增 ID"，避免测试基线来源歧义。
7. **§1.4 关键不变量清单**：8 条✅列表把最容易被违反的约束前置到模块开头，降低实施出错概率。
8. **v0.5+ 演进路线（§15.4）**：把明确推迟的 5 项（cancelTask/SSE、多副本限流、Agent Card 条件请求、SPIFFE Workload API、多架构镜像）集中列出，避免散落在各处造成"是否要做"的反复讨论。

---

## §M 不足 / 风险（3 关注项 + 4 建议项）

### 关注项（不阻塞 v0.2.0，需在评审记录中留痕）

1. **`_internal/_wire.py` 职责边界未最终确定**（§15.2 S-4）：若 L4 读 SDK 源码后发现该子包与 SDK envelope 逻辑重复，删除该子包会影响 §1.3 文件清单的"30 文件"基线数字，需在 L4 实施时同步更新本 Spec 或在 PR 中说明偏差。
2. **U-1/U-3/U-6/U-9/U-11/U-13 共 6 项仍为 🟡 部分收敛**（§15.1）：均依赖 L4 装环境后实测（`OPEN-A2A-001~006`），本 Spec 已给出兜底方案（如 U-6 的 Mount 挂载策略），风险可控但建议 L4 实施第一周优先跑通这 6 项以避免后期返工。
3. **P-1/P-2/P-4/P-6 共 4 项性能/集成参数为默认值待压测**（§15.3）：httpx 连接池、CPU offload 容量、证书 reload 阈值、router 启动顺序耦合，均给了合理默认但未经压测验证，建议在 §11.5 性能预算章节补充压测计划（目前为占位）。

### 建议项（不影响本次升级，供 v0.2.1 参考）

1. §11.5 性能预算目前仍是占位小节（继承 L2-1 Spec §11.5），建议 v0.2.1 补充具体压测脚本和基线数字。
2. §1.3 与 §11.2 两处测试 ID 前缀分布表内容重复，建议后续版本让 §1.3 简化为"参见 §11.2"以减少双处维护成本。
3. 附录 A.4 配套 L3 引用中 L3-3/L3-4/L3-5/L3-6 均为"待起草"，建议在这些文档起草后回填链接（非本次评审阻塞项）。
4. §15.3 P-5（多副本限流推迟 v0.5+）建议在 ROADMAP.md 中显式登记，避免遗忘。

---

## §N 决议

**结论**：✅ **批准 L3-2 A2A Core Library 文件级 Spec 升级 v0.2.0**。

- 0 阻塞项。
- 3 关注项已记录在案，均为"给出兜底方案 + 待 L4 实测确认"性质，不影响文档本身的完整性与自洽性。
- 4 建议项移交 v0.2.1 / L4 实施阶段。
- §14 验收清单（82 条硬验收 + 276 测试 ID）结构自洽，作为本次升级的唯一凭证。
- 依据宪法 §14.5 MVP 例外时间窗口，单点评审有效。

**下一步**：
1. L3-2 Spec 头部升级 v0.2.0（版本/状态/变更记录/配套 Review 引用）。
2. §F.1-§F.6 跨文档同步（L1 Arch/Spec、L2-1 Spec 附录、L3-1 Spec 附录 A.4、ROADMAP、README、CONSTITUTION-CHANGELOG）。
3. git commit。
4. 后续：L3-3 Adapter SDK / L3-4 Hello Agent / L3-5 Knowledge Service / L3-6 Memory backend 文件级 Spec 起草（L3 阶段 2/6 → 后续）。

---

## §O 跨文档同步步骤（本会话执行）

| # | 文档 | 同步内容 | 状态 |
|---|------|----------|------|
| F.1 | L1 Architecture v0.2.0 §3.4 | L3-2 文件级落地完成标记 | 待执行 |
| F.2 | L1 Spec v0.2.0 §16 | 15 指标 metric name 文件级确认标记 | 待执行 |
| F.3 | L2-1 Spec v0.2.0 附录 A | 反向引用升级为 L3-2 v0.2.0 | 待执行 |
| F.4 | L3-1 Spec 附录 A.4 | L3-2 引用升级为 v0.2.0 + 评审链接 | 待执行 |
| F.5 | ROADMAP.md | L3 阶段进度更新（L3-2 完成） | 待执行 |
| F.6 | README.md + CONSTITUTION-CHANGELOG.md | v0.2.0 通过标记 | 待执行 |

---

## §P 附录

- 评审方法：全文通读 + §11.2 逐文件 ID 加总核验 + §14 结构自洽性核验 + 抽样 3 条跨文档一致性核对。
- 未做：L4 实施阶段才能验证的项（实际 SDK 兼容性、压测数据、CI 门禁真实运行结果）不在本次文档评审范围内。
- 参照篇幅：L2-3 Spec 评审 641 行 53.5KB；本评审 约 350 行，符合"L3 文件级评审可比 L2 模块级评审更聚焦"的预期（L3-1 尚无独立评审报告，L3-2 为 L3 阶段首份评审）。
