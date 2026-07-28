# superteam-a2a — L3-3 Adapter SDK 文件级 Spec 评审报告

> **评审日期**：2026-07-28 · #58 会话
> **评审结论落地**：✅ 2026-07-29 已升级 [`L3-adapter-sdk.md` **v0.2.0**](../spec/L3-file-specs/L3-adapter-sdk.md)；**§M 关注项 4-9 六项已在本次 v0.2.0 PR 内同步修正**（详见该文档 §M.2 "#58 评审关注项处理台账"）；关注项 1-3 与 4 项建议项移交 v0.2.1 / L4 实施第一周。
> **评审对象**：[`docs/spec/L3-file-specs/L3-adapter-sdk.md` v0.2-draft-full](../spec/L3-file-specs/L3-adapter-sdk.md)（126KB / 2431 行 / 16 主章节 + 2 附录 · **评审时快照**；修正后 v0.2.0 为 148KB / 2770 行）
> **配套上游 Design**：[L2-3 Adapter Design v0.2.0 Python](../design/L2-modules/L2-adapter.md)（66KB / 1267 行 / 14 主章节 · 2026-07-26 #35 评审通过）
> **配套上游 Spec**：[L2-3 Adapter Spec v0.2.0 Python](../spec/L2-module-specs/L2-adapter.md)（114KB / 2705 行 / 14 节 + 2 附录 · 2026-07-26 #37 评审通过）
> **配套 L3 同级**：[L3-1 Operator Core 文件级 Spec v0.2.0](../spec/L3-file-specs/L3-operator-core.md)（2026-07-27 #49 §9 补完稿 + #56 评审）/ [L3-2 A2A Core 文件级 Spec v0.2.0](../spec/L3-file-specs/L3-a2a-core.md)（2026-07-28 #54 评审通过 · [评审报告](./l3-2-a2a-core-spec-review.md)）
> **评审人**：项目发起人（单点评审 · 宪法 §14.5 MVP 例外时间窗口内）
> **评审依据**：[`CONSTITUTION.md`](../../CONSTITUTION.md) v0.5.0 §3.7 Adapter SDK 边界 + §3.8 Python-first + §6 安全 + §7 可观测性 + §9.7 静态质量 + §13.1 uv workspace + §13.6 6 framework 矩阵 + §14.4 评审门禁 + §16 会话纪律；[ADR-0005 Python-first](../adr/0005-python-first-technology-stack.md) §3.3 Adapter SDK 模块映射 + §6 接口 + §7 安全 + §9.3 镜像策略 A + §10 可观测性 + §13.1 uv workspace + §13.2 静态门禁；[L1 Architecture v0.2.0](../design/L1-architecture.md) §3.5 适配层 + §4.3 C-3 模块 ID；[L1 Spec v0.2.0](../spec/L1-system-spec.md) §16 验收清单；[L2-3 Spec v0.2.0](../spec/L2-module-specs/L2-adapter.md) 全文（上游权威）
> **上一版评审**：无（L3-3 首次评审；v0.1-draft Go baseline 未评审，已归档至 `docs/archive/pre-python-2026-07-24/L2-adapter-spec-v0.1.0-go-baseline.md`）
> **参照模板**：[L3-2 A2A Core Spec 评审](./l3-2-a2a-core-spec-review.md)（18KB / 217 行 / §A-§P 16 节 / 10 维度 PASS）+ [L2-3 Adapter Spec Python 评审](./l2-3-adapter-spec-python-review.md)（53.5KB / 641 行 / §A-§P 10 维度 PASS）

---

## 评审概览

### 评审维度与结论

| 维度 | 评审范围 | 结论 |
|------|----------|------|
| **A. 文档完整性** | §0-§10 + 附录 A/B + 头部（版本/状态/supersede/上游约束/配套 Spec）+ 阅读指南 + public API surface + 35 Python 文件清单 + 12 Helm 模板 | ✅ PASS（伴发现 9 处内部不一致，详见 §M） |
| **B. 设计深度** | FrameworkAdapter Protocol（5 生命周期方法）+ AgentCardConverter Protocol + Pydantic v2 模型 + 4 层配置优先级 + Tenacity 5 类策略 + 错误传播 3 通道 + 6 framework 独立 metrics + 5 时序图 + 9 framework 字段映射矩阵 | ✅ PASS |
| **C. Python-first 硬约束** | ADR-0005 §3.3 / §6 / §7 / §9.3 / §10 / §13.1 / §13.2 / 宪法 §3.8 / §13.1 / §13.6 | ✅ PASS（伴发现 1 项 `ST-ADAPTER-BOUNDARY` Ruff 规则标注 "planned" 未落地，见 §M-2） |
| **D. wire contract 一致性** | 24 A2A 错误码（继承 L3-2 §10）+ 15 A2A 指标（复用 L3-2 §9）+ 7 AdapterError 错误码（-32001~-32007）+ 6 framework 名称 Literal + 4 层配置优先级 + FrameworkAdapter 5 方法签名 | ⚠️ **PASS-WITH-FINDINGS**（伴发现 5 处命名/枚举漂移，见 §M-1） |
| **E. 安全性** | 9 项敏感字段脱敏 + Pod Security Standard restricted + USER 1000:1000 + seccompProfile + NetworkPolicy + RBAC 最小权限 + ConfigMap/Secret Mount + 错误传播 3 通道 | ✅ PASS |
| **F. 可观测性** | 6 framework 独立 Prometheus 指标 + 4 复用 L3-2 §9 runtime 指标 + OTel 4 层 Span 结构 + structlog 7 强制字段 + 9 项敏感字段脱敏 | ✅ PASS |
| **G. 异步 / 单进程 / 资源** | 单进程模式（无 prometheus multiprocess）+ uv workspace 布局 + 6 framework 独立 PyPI 包 + entry_points 动态加载 + ConfigMap/Secret Mount + graceful shutdown 30s | ✅ PASS |
| **H. 错误模型 + Retryable 矩阵** | 7 AdapterError 子类 + RETRYABLE_MATRIX（4 True + 3 False）+ 5 类 Tenacity 策略 + map_framework_exception + propagate_error 3 通道 | ⚠️ **PASS-WITH-FINDINGS**（伴发现 §4.1 AdapterConfig.retry_strategy Literal 与 §8.2 retry.py VALID_STRATEGIES 命名不一致，见 §M-1.2） |
| **I. 测试策略 + ID 矩阵** | 6 层级金字塔（UT/IT/Conformance/E2E/Property/Golden）+ 187 测试 ID（§10.1 已自检加总）+ 44 文件镜像清单 + 6 重静态门禁 + ≥95% / ≥80% 覆盖率 | ✅ PASS（伴发现 §1.3.4 与 §10.1 测试 ID 总数 159 vs 187 偏差需在 PR 描述说明，见 §M-3） |
| **J. 颗粒度偏差 + 跨文档一致性** | 126KB / 2431 行 vs L3-1 Operator Core 3750 行 + L3-2 A2A Core 2808 行 同等级别 | ✅ PASS（伴发现 5 处跨文档命名/路径漂移，见 §M-1） |

**结论**：**L3-3 Adapter SDK 文件级 Spec v0.2-draft-full 通过评审（附 9 项内部发现需在 PR 描述或下个微同步中处理），具备升级 v0.2.0 条件**。0 阻塞项，9 关注项（见 §M），4 建议项（见 §M）。

---

## §A 文档完整性（PASS · 9 处内部发现）

- **头部 10 段齐全**：ADR-0005 supersede 标记 / 层级模块 ID / 代码位置 / 版本 / 状态 / 上游约束 / Python 重写入口 / 本 Spec 目的 / 配套 Spec / 文档元数据（§M 11 字段）。
- §0-§10 + 附录 A（6 子表 30 行）+ 附录 B（5 子表 49 行）全部落地，扫描全文 `占位` 关键词命中 6 处，全部为**业务语义描述**（如"占位测试""AdapterErrorCode 占位"），非遗留的"待补完"占位章节标记；`#56+ 补完` / `⚠️ 占位章节` 类临时标记已在本次会话清理为 0。
- §1.3.1 11 文件 SDK 清单与 §2.1 uv workspace 布局图一致；§1.3.2 6 framework 子包清单与 §5.3 24 文件级契约表对应；§7.1 4 文件 observability 子模块与 §10.4 测试文件镜像清单对应。
- 附录 A 6 子表（L1/L2-3/ADR/Constitution/配套 L3/归档）+ 附录 B 5 子表（架构部署/接口生命周期/错误处理/安全/可观测性测试）均完整展开，无省略。

**本评审发现并归类的 9 处内部不一致**（均在 §M 详细展开）：

| # | 位置 | 类型 | 严重度 |
|---|------|------|--------|
| 1 | §1.3.2 / §1.3.4 vs §5.3 | Framework 文件数 22 vs 24 | 关注 |
| 2 | §1.3.2 #15 SK 列路径 vs framework_name Literal | 子包路径 `adapter_sk` vs framework_name `"sk"` | 关注 |
| 3 | §3.2 framework_name Literal vs §7.2 metrics label vs §9.3 env var | "sk" vs "semantic_kernel" | 关注 |
| 4 | §4.1 AdapterConfig.retry_strategy Literal vs §8.2 retry.py VALID_STRATEGIES vs §1.4 不变量 row 5 | 5 类策略命名三处不一致 | 关注 |
| 5 | §2.4 metrics 名 vs §7.2 metrics 名 | `superteam_adapter_*` vs `supteam_adapter_*` | 关注 |
| 6 | L3-3 §1.2 vs L2-3 §1.3 public API | L3-3 缺失 `Adapter` / `AdapterErrorCode` / `create_retry_policy` / `Lifecycle` | 关注 |
| 7 | L3-3 §2.1 路径 vs L2-3 §2.1 路径 | `superteam_a2a` vs `supteam_a2a`（命名漂移） | 关注 |
| 8 | §B.2 row 12 Protocol 方法名 vs §3.2 实际定义 | 附录 B 列出 `list_agents/get_agent_card/send_message/get_task/cancel_task`，§3.2 定义 `load_agent/to_agent_card/from_agent_card/invoke/health_check` | 关注 |
| 9 | §9.4 image tag vs §3.5 VERSION_MATRIX | 5/6 framework image tag 版本号低于 min_version | 关注 |

**修正建议**：上述 9 项均为**关注项**而非阻塞项（不影响文档结构完整性，但实施时会导致运行时错误），建议在评审通过后的 v0.2.0 PR 描述中标注 "已知 9 项内部不一致，移交 L4 实施第一周修正"，并在 ROADMAP.md 中登记 L3-3-followup-1 ~ L3-3-followup-9 编号。

---

## §B 设计深度（PASS）

- **5 生命周期方法契约**（§3.2 FrameworkAdapter Protocol）：`load_agent` / `to_agent_card` / `from_agent_card` / `invoke` / `health_check`，duck typing（typing.Protocol + `@runtime_checkable`），不强制基类继承。
- **AgentCardConverter 双方法**（§3.2）：`framework_to_card_skill` + `card_skill_to_framework`，6 framework 各自实现 + 6 字段映射矩阵（§4.4）。
- **Pydantic v2 模型 4 类**（§4.1）：`AgentSpec` + `ToolSpec` + `AgentCard` + `AdapterConfig`，全部 `extra="forbid"` + 严格 wire shape 校验。
- **4 层配置优先级 merge**（§6.1）：CRD > env > sidecar file > defaults，每层覆盖只覆盖**显式**声明字段，6 类测试场景覆盖（§6.5）。
- **6 framework 动态加载**（§6.3）：通过 entry_points `superteam_a2a.frameworks` 注册，VERSION_MATRIX 6 framework 独立版本范围。
- **Tenacity 5 类策略**（§8.2）：`retry_network` / `retry_5xx` / `retry_rate_limit` / `retry_timeout` / `retry_framework`，含 jitter 全随机（0.5x-1.5x）+ compute_backoff + with_retry 装饰器 + RetryError 包装。
- **错误传播 3 通道**（§8.3 propagate_error）：structlog logger.error + Prometheus ERRORS_TOTAL + OTel Span Event `error.occurred`。
- **6 framework 独立 metrics**（§7.2）：7 个 `supteam_adapter_*` Prometheus 指标 + `setup_metrics()` 自定义 registry 注入 + 单进程模式（无 prometheus multiprocess）。
- **OTel 4 层 Span 结构**（§7.3）：`adapter.{framework}.{method}` Root → `framework.invoke` / `card.convert` / `framework.translate` Child + 4 Span Events（`tool.invoked` / `memory.read` / `memory.write` / `error.occurred`）。
- **5 生命周期时序图**（§3.3）：覆盖 resolve_framework / load_agent / to_agent_card / invoke / health_check，每张图标注断言点与测试 ID。
- **12 Helm 模板**（§9）：6 framework × (values.yaml 86 行 + deployment.yaml 124 行) + 4 共享模板（clusterrole + clusterrolebinding + networkpolicy + servicemonitor）。
- **§B.2 row 13 约束修正建议**：附录 B.2 row 13 称 AgentCardConverter Protocol 1 方法 `convert`，但 §3.2 定义为 2 方法 `framework_to_card_skill` + `card_skill_to_framework`（详见 §M row 8）。

---

## §C Python-first 硬约束（PASS · ADR-0005 §3.3 + §6 + §7 + §9.3 + §10 + §13.1 + §13.2 + 宪法 §3.8 + §13.6）

| 约束 | 落地位置 | 结论 |
|------|----------|------|
| `superteam_a2a.adapter.*` SDK 入口（不重命名） | §1.2 + §2.1 + 附录 B.1 #1 | ✅（伴发现 L2-3 上游使用 `supteam_a2a` 漂移，§M-1.7） |
| 业务层禁止 `import framework SDK`（Ruff `ST-ADAPTER-BOUNDARY`） | §1.2 + §10.2 + 附录 B.1 #5 | ⚠️ **PASS-WITH-FINDINGS**（Ruff 规则 §10.2 标注 `planned`，未实际实现；详见 §M-2） |
| uv workspace 布局（`packages/adapter-sdk/` + `adapters/{framework}/`） | §2.1 + §10.5 + 附录 B.1 #2 | ✅ |
| Python 3.12+ 精确下限 | §10.6 + 附录 B.1 #3 | ✅ |
| 6 framework 独立 base 镜像（策略 A · ADR-0005 §9.3） | §9 + §10.6 + 附录 B.1 #7 | ✅ |
| Dockerfile 多阶段（builder + runtime） | §10.6 + 附录 B.1 #8 | ✅ |
| USER 1000:1000 non-root + Pod Security Standard: restricted | §9.2 + §10.6 + 附录 B.1 #6/#9 | ✅ |
| ConfigMap + Secret 引用（不内嵌） | §9.2 + 附录 B.1 #10 | ✅ |
| 同进程 plugin / sidecar 双拓扑（`embedded` 切换） | §9.2 values.embedded + 附录 B.1 #11 | ✅ |
| 6 framework 名称不可变（typing.Literal 强制） | §3.2 FrameworkName + 附录 B.1 #1 | ✅ |

---

## §D wire contract 一致性（PASS-WITH-FINDINGS · 5 处命名/枚举漂移）

- **24 A2A 错误码**（继承 L3-2 §10）：`StandardRpcError` 5 + `ProjectRpcError` 19（A2A 域 6 + Knowledge 7 + Memory 6），L3-3 不重定义，仅消费。
- **7 AdapterError 错误码**（§1.4 + §B.3 #22）：`ADAPTER_CONFIG_ERROR` / `ADAPTER_AUTH_ERROR` / `ADAPTER_TIMEOUT_ERROR` / `ADAPTER_FRAMEWORK_ERROR` / `ADAPTER_VERSION_ERROR` / `ADAPTER_RETRYABLE_ERROR` / `ADAPTER_PERMANENT_ERROR`，数值 -32001 ~ -32007（与 L3-2 §10 错开）。
- **15 A2A Prometheus 指标**（复用 L3-2 §9）：11 `supteam_a2a_*` + 4 `supteam_python_*`，L3-3 不重定义。
- **6 framework 独立 metrics**（§7.2）：7 个 `supteam_adapter_*`（注意：L3-3 §2.4 表格误写为 `superteam_adapter_*`，详见 §M-1.5）。
- **4 层配置优先级**（§6.1）：与 L2-3 Spec §3.2 完全一致。
- **FrameworkAdapter 5 生命周期方法**（§3.2）：与 L2-3 Spec §3.1 完全一致。

**5 处命名/枚举漂移**（详见 §M）：

1. **§2.4 metrics 名 vs §7.2 metrics 名**：`superteam_adapter_load_total`（§2.4 row 1）vs `supteam_adapter_requests_total`（§7.2 line 1165）—— prefix 不一致。
2. **§4.1 vs §8.2 retry_strategy 枚举**：`["retry_network", "retry_timeout", "retry_5xx", "retry_429", "no_retry_4xx"]`（§4.1）vs `["retry_network", "retry_5xx", "retry_rate_limit", "retry_timeout", "retry_framework"]`（§8.2）—— 5 项策略名完全不重合。
3. **§1.4 不变量 row 5**：`["retry_network", "retry_timeout", "retry_5xx", "retry_429", "no_retry_4xx"]`—— 与 §4.1 一致，但与 §8.2 不一致。
4. **§3.2 framework_name Literal vs §7.2 metrics label vs §9.3 env var**：`["langchain", "autogen", "crewai", "sk", "strands", "smolagents"]`（§3.2）vs `["langchain", "autogen", "crewai", "semantic_kernel", "strands", "smolagents"]`（§7.2 line 1255）vs `["langchain", "autogen", "crewai", "semantic_kernel", "strands", "smolagents"]`（§9.3 line 1951）—— `"sk"` vs `"semantic_kernel"` 在 Protocol 与 observability/Helm 层不一致。
5. **§B.2 row 12 Protocol 方法名**：附录列出 `list_agents / get_agent_card / send_message / get_task / cancel_task`，但 §3.2 实际定义为 `load_agent / to_agent_card / from_agent_card / invoke / health_check`—— 附录 B 与正文不符。

---

## §E 安全性（PASS）

- **9 项敏感字段脱敏**（§7.4）：`api_key` / `token` / `password` / `secret` / `user_data` / `memory_content` / `knowledge_body` / `cert` / `private_key`，structlog processor `_redact_sensitive` 在 `_SENSITIVE_KEYS` 中按 key.lower() 匹配后替换为 `***REDACTED***`。
- **Pod Security Standard: restricted**（§9.2）：`runAsNonRoot: true` + `runAsUser: 1000` + `runAsGroup: 1000` + `readOnlyRootFilesystem: true` + `allowPrivilegeEscalation: false` + `capabilities.drop: ["ALL"]` + `seccompProfile.type: RuntimeDefault`。
- **USER 1000:1000 non-root**（§10.6）：`useradd --create-home --uid 1000 adapter` + `USER 1000:1000`。
- **NetworkPolicy 双向限制**（§9.5）：ingress port 8080 from namespaceSelector + egress 443 to kube-dns + 4317 to otel-collector + 7080 to localhost (agent 同 Pod)。
- **RBAC 最小权限**（§9.5 clusterrole.yaml）：仅 `adapters/events` + `adapters/status` + `coordination.k8s.io/leases`（Leader Election），verbs = get/list/watch/create/update/patch。
- **ConfigMap + Secret 引用**（§9.2）：`configMapRef: superteam-a2a-adapter-config` + `mtlsSecretRef: superteam-a2a-adapter-mtls`，两者均 readOnly mount。
- **错误传播 3 通道**（§8.3）：structlog + Prometheus + OTel，memory_content / knowledge_body 永不过普通日志（仅 OTel Span Event）。

---

## §F 可观测性（PASS）

- **6 framework 独立 Prometheus 指标**（§7.2）：`supteam_adapter_requests_total{framework,method,status}` + `supteam_adapter_request_duration_seconds{framework,method}` + `supteam_adapter_card_conversion_duration_seconds{framework}` + `supteam_adapter_framework_load_duration_seconds{framework}` + `supteam_adapter_errors_total{framework,error_code}` + `supteam_adapter_active_agents{framework}` + `supteam_adapter_golden_case_pass_total{framework,case_id}`。
- **label 基数约束**（§7.2 末段）：`trace_id` / `task_id` 永不过 metric label（仅 OTel Span attributes）；`result` label 仅 4 值；Histogram 自定义桶必须显式声明。
- **4 复用 L3-2 §9 runtime 指标**（§7.5）：`supteam_python_event_loop_lag_seconds` / `supteam_python_thread_offload_queue_depth` / `supteam_python_active_asyncio_tasks` / `supteam_python_gc_collections_total`，adapter-sdk **不重新注册**（避免重复注册冲突）。
- **OTel 4 层 Span 结构**（§7.3）：`adapter.{framework}.{method}` Root + 3 Child（`framework.invoke` / `card.convert` / `framework.translate`）+ 4 Span Events（`tool.invoked` / `memory.read` / `memory.write` / `error.occurred`）。
- **structlog 7 强制字段**（§7.4）：`framework` / `framework.version` / `adapter.version` / `method` / `task_id` / `agent.name` / `level`，通过 `bind_context()` 绑定到 contextvars。
- **单进程模式**（§7.2）：禁用 `PROMETHEUS_MULTIPROC_DIR`（测试用 mock registry 隔离）。

---

## §G 异步 / 单进程 / 资源（PASS）

- **单进程模式**（§7.2 + §C 引用 ADR-0005）：禁用 prometheus_client multiprocess mode（Uvicorn 1 worker）。
- **uv workspace 布局**（§2.1 + §10.5）：`packages/adapter-sdk/` 独立 PyPI + `adapters/{framework}/` 各自独立 PyPI + `helm/adapter-{framework}/` 各自独立 chart。
- **6 framework 独立 base 镜像**（§9 + §10.6）：`ghcr.io/superteam-a2a/adapter-{framework}:{tag}` 各自构建，framework SDK 与 adapter-sdk 仅复制 site-packages（不复制源码）。
- **entry_points 动态加载**（§6.3）：`pyproject.toml [project.entry-points."superteam_a2a.frameworks"]` 注册 `FrameworkAdapter` 实现。
- **ConfigMap/Secret Mount**（§9.2）：adapter-config + mtls-certs 两者均 readOnly。
- **graceful shutdown 30s**（§9.2）：`terminationGracePeriodSeconds: 30`（与 L3-1 §5 Leader Election grace period 一致）。

---

## §H 错误模型 + Retryable 矩阵（PASS-WITH-FINDINGS · §M-1.2 retry_strategy 枚举不一致）

- **7 AdapterError 子类**（§1.2 + §8.3 RETRYABLE_MATRIX）：`AdapterError` 基类 + `AdapterPermanentError` / `AdapterRetryableError` / `AdapterNonRetryableError` / `AdapterConfigError` / `AdapterAuthError` / `AdapterTimeoutError` / `AdapterFrameworkError` / `AdapterVersionError`。
- **RETRYABLE_MATRIX**（§8.3）：4 True（TIMEOUT / FRAMEWORK / RETRYABLE / 5xx）+ 3 False（CONFIG / AUTH / VERSION / PERMANENT）。
- **5 类 Tenacity 策略**（§8.2）：`retry_network` / `retry_5xx` / `retry_rate_limit` / `retry_timeout` / `retry_framework`，每类 backoff 计算 + jitter 0.5x-1.5x。
- **map_framework_exception**（§8.3）：httpx 异常 → AdapterError 子类映射（ConnectError/NetworkError → Retryable；TimeoutException → TimeoutError；HTTPStatusError 429 → Retryable；HTTPStatusError 4xx → NonRetryable；HTTPStatusError 5xx → Retryable；ImportError 含 version → VersionError；fallback → FrameworkError）。
- **propagate_error 3 通道**（§8.3）：structlog logger.error + Prometheus ERRORS_TOTAL.labels + OTel Span Event `error.occurred`。

**§M-1.2 retry_strategy 枚举不一致**：
- §4.1 AdapterConfig.retry_strategy Literal：`["retry_network", "retry_timeout", "retry_5xx", "retry_429", "no_retry_4xx"]`（5 项）
- §8.2 retry.py VALID_STRATEGIES：`{"retry_network", "retry_5xx", "retry_rate_limit", "retry_timeout", "retry_framework"}`（5 项完全不同命名）
- §1.4 不变量 row 5：与 §4.1 一致

**结论**：3 处枚举**完全不重合**——§4.1/§1.4 为一组，§8.2 为另一组。建议以 §1.4 + §4.1 为准（与 L2-3 Spec §10.4 命名一致），修改 §8.2 retry.py 与 RETRYABLE_MATRIX 的 strategy 名称。**非阻塞项**（实施时统一即可），但需在 PR 描述明确以谁为准。

---

## §I 测试策略 + ID 矩阵（PASS · §10.1 已自检加总）

- **6 层级金字塔**（§10.1）：UT（adapter-sdk 74 + framework 54 = 128）+ IT（44）+ Conformance（5）+ E2E（6）+ Property（4）+ Golden（0 待后续）= **187 测试 ID**。
- **§10.1 已自检加总**（v0.2 81 / v1.0 159 目标 + 28 项 L3-3 文件级细化）= 187 ✅，附录 B.5 #47 标"187 测试 ID（UT 128 + IT 44 + CF 5 + E2E 6 + PROP 4）"与 §10.1 矩阵加总一致。
- **44 文件镜像清单**（§10.4）：UT adapter-sdk 11 + framework 18 + IT 6 + conformance 1 + e2e 6 + property 1 + helm 1 = 44 ✅。
- **6 重静态门禁**（§10.2）：`uv sync --frozen` + `ruff format` + `ruff check` + `pyright --strict` + `bandit` + `pip-audit`，其中 `ST-ADAPTER-BOUNDARY` Ruff 规则标注 `planned`（详见 §M-2）。
- **覆盖率**（§10.3 + 附录 B.5 #48）：adapter-sdk ≥ 95% / framework ≥ 80%（继承 L2-3 §13.4）。

**§M-3 测试 ID 总数偏差说明**：§1.3.4 row 6 标"测试 ID ~159"，§10.1 标"187"，两处数字不一致。已在 §10.1 末尾 note 中明确说明偏差来自 L3-3 文件级细化（如 `test_redact_sensitive_9_keys` 等 9 项敏感字段单测），属合理偏差。**建议**在 v0.2.0 PR 描述中显式说明"159 → 187 +28 来自文件级细化"，并在 §1.3.4 表格底部加一行 "实际 §10.1 加总 = 187（含文件级细化 +28）"。

---

## §J 颗粒度偏差 + 跨文档一致性（PASS-WITH-FINDINGS · 5 处跨文档命名/路径漂移）

- **颗粒度**：126KB / 2431 行，对比 L3-1 Operator Core 3750 行 + L3-2 A2A Core 2808 行 同等级别（L3-3 因 6 framework 子包覆盖范围更广，文件数 35 vs L3-2 30）。颗粒度偏差属合理范围（约 0.87x）。
- **跨文档一致性**：附录 A 6 子表 30 行已列 10 类跨文档引用（L1/L2-3/ADR/Constitution/L3/归档），本评审抽样核对 5 条（L2-3 §1.3 public API、L2-3 §2.1 路径、ADR-0005 §3.3、Constitution §3.8、L3-2 §6 A2AClient），其中 3 条发现不一致（详见 §M-1）。

**5 处跨文档命名/路径漂移**（详见 §M）：

1. **L3-3 §1.2 public API vs L2-3 §1.3 public API**：L3-3 缺失 `Adapter` / `AdapterErrorCode` / `create_retry_policy` / `Lifecycle`，但 L2-3 §1.3 已列出这 4 项作为公共 API。
2. **L3-3 §2.1 路径 `superteam_a2a` vs L2-3 §2.1 路径 `supteam_a2a`**：命名漂移（按 grep 计数：L3-3 66 处中 59 处 `superteam` + 7 处 `supteam`；L2-3 59 处中 35 处 `supteam` + 24 处 `superteam`）。
3. **L3-3 §1.3.2 framework 子包路径 `adapter_{framework}` vs L2-3 §2.1 framework 子包路径 `adapters/{framework}`**：单数 vs 复数 + 下划线 vs 斜杠。
4. **L3-3 §3.5 LangChain image tag `v0.2.0-0.1.5-py3.12` vs §3.5 VERSION_MATRIX min_version `0.2.0`**：framework_version 0.1.5 < min_version 0.2.0，被 `_check_version_compatibility` 拒绝。
5. **L3-3 §9.4 AutoGen image tag `0.2.3` vs min `0.4.0` / CrewAI `0.65.0` vs min `0.80.0` / Semantic Kernel `1.15.0` vs min `1.30.0` / Smolagents `1.0.0` vs min `1.10.0`**：5/6 framework image tag 低于 min_version（仅 Strands 0.1.0 = min 0.1.0 通过）。

---

## §K 验收清单（§10.1 + §附录 B · 187 ID + 49 行追溯矩阵）

> 本节核验 L3-3 Spec §10.1 测试 ID 总计矩阵 + 附录 B 49 行追溯矩阵**结构完整性**（不是逐条勾选执行——187 ID 的实际勾选属于 L4 实施阶段 + CI 验证范畴）。

| 子节 | 条数 | 结构核验 | 结论 |
|------|------|----------|------|
| §10.1 测试 ID 总计矩阵 | 6 层级 / 187 ID | 与 §附录 B.5 #47 一致，加总自检正确 | ✅ PASS |
| §10.2 6 重静态门禁 | 6 项 | 覆盖 uv sync + ruff format/check + pyright + bandit + pip-audit | ✅ PASS（伴发现 `ST-ADAPTER-BOUNDARY` 标注 `planned`，详见 §M-2） |
| §10.3 测试工具链 | 5 命令 | 覆盖 UT/IT/CF/E2E/Property 5 层级 pytest 调用 | ✅ PASS |
| §10.4 测试文件镜像清单 | 44 文件 | 与 §10.1 187 ID 1:1 镜像 | ✅ PASS |
| §10.5 uv workspace 布局 | 11+24+12+4 文件树 | 与 §2.1 + §9 + §10.6 一致 | ✅ PASS |
| §10.6 Dockerfile 多阶段模板 | 6 framework × 1 模板 | 继承 L2-3 §8.1 策略 A | ✅ PASS |
| §10.7 §10 测试 ID 矩阵 | 30 ID | 覆盖 TOOL + HELM-RENDER + CF + PROP + E2E + COV + TOOL-CHAIN | ✅ PASS |
| 附录 A 6 子表 | 30 行 | L1/L2-3/ADR/Constitution/L3/归档 完整展开 | ✅ PASS |
| 附录 B.1 架构与部署 | 11 条 | ADR-0005 §3.3/§6/§7/§9.3/§13.1 + 宪法 §3.8/§13.1/§13.6 完整追溯 | ✅ PASS |
| 附录 B.2 接口与生命周期 | 10 条 | 5 Protocol 方法 + 6 framework 加载 + lifecycle + mTLS 完整追溯 | ⚠️ PASS-WITH-FINDINGS（row 12/13 方法名错误 + row 17 11 步启动序列未在 §3 落地，详见 §M row 8） |
| 附录 B.3 错误处理 | 10 条 | 7 错误码 + AdapterError 子类 + Retryable 矩阵 + Tenacity + 3 通道 + map_framework_exception 完整追溯 | ⚠️ PASS-WITH-FINDINGS（row 31 `to_jsonrpc_error` 方法未在 §3.2 / §8.3 落地，详见 §M row 8） |
| 附录 B.4 安全 | 10 条 | 9 项敏感字段脱敏 + Pod Security restricted + RBAC 最小权限 + NetworkPolicy 完整追溯 | ✅ PASS |
| 附录 B.5 可观测性与测试 | 8 条 | 6 framework 指标 + 4 复用指标 + OTel 4 层 + structlog 7 字段 + 187 ID + 6 重门禁 完整追溯 | ✅ PASS |

**验收清单执行结论**：§10 + 附录 B 结构自洽，187 ID + 44 文件镜像清单 + 6 重静态门禁 + 49 行追溯矩阵作为本次升级的凭证，但伴随 9 项内部不一致（详见 §M），需在 v0.2.0 PR 描述中显式说明或在 L4 实施第一周微同步修正。

---

## §L 优点（8 项）

1. **35 Python 文件 + 12 Helm 模板的完整文件级契约覆盖**：11 SDK + 24 framework + 4 observability + 12 helm = 51 文件级契约点，每个文件均给出**绝对路径 + 职责 + exported 符号 + 测试 ID 前缀**，L4 实施工程师打开 IDE 即可对照写代码。
2. **6 framework 名称不可变约束的多层强制**（§1.4 + §3.2 + §B.1）：typing.Literal + ruff format + 测试 SDK-PROT-003 + §10.4 framework 子包路径命名 + §9.3 env var 命名，5 层冗余约束防止 framework 名称被误改。
3. **§B.5 #49 Ruff 自定义规则 `ST-ADAPTER-BOUNDARY`** 的设计意图清晰（业务层禁 import framework SDK），虽实现未落地（`planned`），但规则描述 §10.2 已给出伪代码，L4 实施时按图实现即可。
4. **§10.6 Dockerfile 多阶段模板 + 每 framework 独立 base 镜像** 严格遵循 ADR-0005 §9.3 策略 A，framework SDK 仅复制 site-packages（不复制源码）减小镜像体积，且 USER 1000:1000 + HEALTHCHECK + 多 stage builder/runtime 完整落地。
5. **4 复用 L3-2 §9 runtime 指标**（§7.5）：明确"仅消费，不重新注册"，避免了与 L3-2 重复注册 Prometheus 指标的冲突，6 framework 各自的 7 个新指标与 4 个 L3-2 runtime 指标职责清晰（framework 业务 vs Python runtime）。
6. **错误传播 3 通道**（§8.3 propagate_error）：structlog + Prometheus + OTel 同步触发，且 `framework` + `error_code` 跨 3 通道保持一致（便于 Grafana 关联查询 + Loki 日志聚合 + Jaeger trace 关联）。
7. **6 framework 字段映射矩阵**（§4.4）：tool → skill / skill → tool + framework_specific 字段 6 行列展开，L4 实施 framework adapter 时直接照表实现 `AgentCardConverter` 即可。
8. **§10.1 测试 ID 总计矩阵的双向引用**：§1.3.4 表格给出"约 159"（继承 L2-3）+ §10.1 加总 187（包含文件级细化 +28），§10.1 末尾 note 明确说明偏差来源 + 附录 B.5 #47 标"187 测试 ID（UT 128 + IT 44 + CF 5 + E2E 6 + PROP 4）"形成三处交叉核验闭环，避免测试 ID 凭空编造。

---

## §M 不足 / 风险（9 关注项 + 4 建议项）

### 关注项 1：5 处命名/枚举漂移（PASS-WITH-FINDINGS · 实施时必须统一）

#### 1.1 Framework 子包路径 vs framework_name Literal

- **位置**：§1.3.2 row 15 Semantic Kernel 列路径为 `adapter_sk`（下划线连接），但 §3.2 FrameworkName Literal 为 `"sk"`（无下划线）
- **L2-3 上游参照**：L2-3 §2.1 framework 子包路径为 `adapters/{framework}/`（斜杠分隔 + 复数 adapters）
- **建议**：以 §3.2 Literal 为准，统一为 `adapter_sk`（路径）/ `"sk"`（Literal）/ `"semantic_kernel"`（observability/Helm metrics label）三层映射在 §1.3.2 表格中显式说明

#### 1.2 retry_strategy 枚举三处不一致

- **位置**：§4.1 AdapterConfig.retry_strategy Literal 与 §8.2 retry.py VALID_STRATEGIES + §1.4 不变量 row 5 命名完全不重合
  - §4.1: `["retry_network", "retry_timeout", "retry_5xx", "retry_429", "no_retry_4xx"]`
  - §8.2: `{"retry_network", "retry_5xx", "retry_rate_limit", "retry_timeout", "retry_framework"}`
  - §1.4 row 5: 与 §4.1 一致
- **建议**：以 §1.4 + §4.1 为准（与 L2-3 Spec §10.4 命名一致），修改 §8.2 VALID_STRATEGIES 为 §1.4 命名 + 补 `STRATEGY_NO_RETRY_4XX` 常量

#### 1.3 metrics prefix 不一致

- **位置**：§2.4 row 1 指标名为 `superteam_adapter_load_total`（`superteam_` prefix），但 §7.2 7 个指标定义全部用 `supteam_adapter_*`（`supteam_` prefix）
- **L3-2 上游参照**：L3-2 §9 15 指标用 `supteam_a2a_*` + `supteam_python_*` prefix
- **建议**：统一为 §7.2 `supteam_adapter_*` prefix（与 L3-2 一致），§2.4 表格全部更新；同步更新 §9.2 values 中 `supteam_a2a-adapter-config` ConfigMap 名称

#### 1.4 framework_name vs metrics label vs env var

- **位置**：§3.2 FrameworkName Literal 含 `"sk"`，但 §7.2 metrics label 取值（line 1255）和 §9.3 Deployment env var（line 1951）均使用 `"semantic_kernel"`
- **建议**：在 §3.2 Protocol 增加 `framework_label: Literal` 属性（区分 Protocol 名 `sk` 与 metrics/env 名 `semantic_kernel`），或统一为单一名称（推荐 `semantic_kernel`，避免与 SDK 名 `sklearn` 等冲突）

#### 1.5 package path 命名漂移（跨 L2-3 与 L3-3）

- **位置**：L3-3 §2.1 路径为 `superteam_a2a/adapter/`，L2-3 §2.1 路径为 `supteam_a2a/adapter/`（grep 计数 L3-3 中 `supteam` 7 处 + `superteam` 59 处；L2-3 中 `supteam` 35 处 + `superteam` 24 处）
- **建议**：以 ADR-0005 §13.1 + 宪法 §3.8 为准（统一为 `superteam_a2a`），更新 L2-3 Spec §2.1 全部路径引用，或明确声明 `supteam_a2a` 是 `superteam_a2a` 的别名（pyproject.toml `name = "superteam-a2a"` + `import superteam_a2a as supteam_a2a`）

### 关注项 2：`ST-ADAPTER-BOUNDARY` Ruff 规则标注 `planned` 未落地

- **位置**：§10.2 row 3 Ruff check 标注 "（含 ST-ADAPTER-BOUNDARY 自定义规则）"，§B.1 row 5 列为 MUST，但 §10.2 自定义规则伪代码块标注 "(planned)" 未实际实现
- **影响**：约束意图清晰但缺少实际拦截能力，业务层误 import framework SDK 不会被 CI 阻断
- **建议**：v0.2.0 PR 必须包含 ST-ADAPTER-BOUNDARY Ruff 插件实现（最小可用版本：基于 `flake8-no-implicit-concat` 扩展或 `ruff` `flake8-tidy-imports`），否则 §B.1 row 5 MUST 约束空挂

### 关注项 3：测试 ID 总数 159 vs 187 偏差已在 §10.1 自检但 §1.3.4 未交叉引用

- **位置**：§1.3.4 row 6 标"测试 ID ~159"，§10.1 标"187"
- **§10.1 末尾 note 已说明偏差**：来自 L3-3 文件级细化（如 `test_redact_sensitive_9_keys` 等 9 项敏感字段单测）
- **建议**：在 §1.3.4 row 6 末尾追加"（实际 §10.1 加总 = 187，含文件级细化 +28；详见 §10.1 note）"实现交叉引用闭环

### 关注项 4：§B.2 row 12 FrameworkAdapter Protocol 方法名错误

- **位置**：§B.2 row 12 列出"FrameworkAdapter Protocol 5 方法（list_agents / get_agent_card / send_message / get_task / cancel_task）"，但 §3.2 实际定义为 `load_agent / to_agent_card / from_agent_card / invoke / health_check`
- **影响**：附录 B 与正文严重不符，L4 实施照附录实现 Protocol 会失败
- **建议**：v0.2.0 PR 必须修正 §B.2 row 12 为 `load_agent / to_agent_card / from_agent_card / invoke / health_check`，与 §3.2 一致

### 关注项 5：§B.2 row 13 AgentCardConverter Protocol 方法数错误

- **位置**：§B.2 row 13 列"AgentCardConverter Protocol 1 方法（convert）"，但 §3.2 实际定义为 2 方法 `framework_to_card_skill` + `card_skill_to_framework`
- **建议**：v0.2.0 PR 必须修正 §B.2 row 13 为"AgentCardConverter Protocol 2 方法（framework_to_card_skill / card_skill_to_framework）"

### 关注项 6：§B.2 row 17 Lifecycle 11 步启动序列未在 §3 / §10 落地

- **位置**：§B.2 row 17 列"Lifecycle 11 步启动序列（MUST · ADR-0005 §6）"，但 §3 仅描述 5 生命周期方法时序图，§10 未列出 11 步启动序列
- **建议**：v0.2.0 PR 必须新增 §3.7 "Lifecycle 11 步启动序列"小节（11 步从 Protocol 加载 → entry_points 解析 → config 加载 → Adapter 实例化 → load_agent → to_agent_card → readiness probe 注入 → health_check 周期启动 → lifespan 启动 → listen → graceful shutdown），或删除 §B.2 row 17

### 关注项 7：§B.3 row 31 `AdapterError.to_jsonrpc_error` 方法未在 §3.2 / §8.3 落地

- **位置**：§B.3 row 31 列"AdapterError.to_jsonrpc_error 含 framework_error（MUST · ADR-0005 §10）"，但 §3.2 protocol.py 中 AdapterError 基类仅有 `framework` / `error_code` 属性，§8.3 errors_mapping 无 `to_jsonrpc_error` 方法
- **建议**：v0.2.0 PR 必须新增 `AdapterError.to_jsonrpc_error()` 方法契约（§3.2 protocol.py 末尾），或在 §8.3 errors_mapping.py 末尾新增 `to_jsonrpc_error(error) -> dict` 顶层函数

### 关注项 8：§9.4 image tag 与 §3.5 VERSION_MATRIX 5/6 framework 版本号不符

- **位置**：§9.4 6 framework image tag 中 5 项 framework_version 低于 §3.5 VERSION_MATRIX min_version：
  - LangChain: image `0.1.5` < min `0.2.0`
  - AutoGen: image `0.2.3` < min `0.4.0`
  - CrewAI: image `0.65.0` < min `0.80.0`
  - Semantic Kernel: image `1.15.0` < min `1.30.0`
  - Smolagents: image `1.0.0` < min `1.10.0`
  - Strands: image `0.1.0` = min `0.1.0` ✅
- **影响**：L4 实施时 `_check_version_compatibility` (§6.3) 会拒绝这些 image tag，启动报错
- **建议**：v0.2.0 PR 必须以 §3.5 VERSION_MATRIX 为准更新 §9.4 image tag（或更新 §3.5 min_version 至 image tag 中的版本号；推荐前者）

### 关注项 9：L3-3 public API surface 与 L2-3 §1.3 不一致（4 项缺失）

- **位置**：L3-3 §1.2 __all__ 列出 13 项（FrameworkAdapter + AgentCardConverter + AgentSpec + AgentCard + AdapterConfig + AdapterError + 7 子类），但 L2-3 §1.3 public API 额外包含 `Adapter`（Protocol）/ `AdapterErrorCode`（StrEnum）/ `create_retry_policy`（工厂）/ `Lifecycle`（生命周期类）
- **影响**：L2-3 上游 Spec 期望业务层可 import 这 4 项，但 L3-3 文件级 Spec 实际不交付
- **建议**：v0.2.0 PR 必须明确 4 项缺失符号的去向：
  - 选项 A：在 L3-3 §1.2 __all__ 中补齐 4 项（在 L4 实施时新增 `Adapter` Protocol / `AdapterErrorCode` StrEnum / `create_retry_policy` 工厂 / `Lifecycle` 类）
  - 选项 B：在 L3-3 §1.2 末尾新增"已知 L2-3 §1.3 列出但 L3-3 未落地的 4 项符号"清单，并在 §M.3 下一会话入口登记为 ADR-0005 修订事项

### 建议项（不影响本次升级，供 v0.2.1 参考）

1. §1.3.4 行数 L3-3 = "11 SDK + 22 framework = 33" 后续 §5.3 修正为 24 framework，但 §1.3.4 表格未同步，建议 v0.2.1 统一更新为 "11 SDK + 24 framework = 35"。
2. §7.2 metrics 中 `label_result` 取值 4 种（success/error/retry/rejected），但 §8.3 propagate_error 中 `result` 取值仅 3 种（success/error/unknown），建议 v0.2.1 统一为 4 种。
3. §10.4 framework import 路径 `supteam_a2a.adapter_langchain` 与 §2.1 §2.2 header `superteam_a2a.adapter_langchain` 不一致，建议 v0.2.1 统一为单一 prefix。
4. 附录 A.4 row 28 L3-4 Hello Agent "（待起草 · L4 实施前完成）"建议在 L3-4 启动时回填链接，闭环 §A.5 跨 L3 引用。

---

## §N 决议

**结论**：✅ **批准 L3-3 Adapter SDK 文件级 Spec 升级 v0.2.0**（附 9 项关注项需在 PR 描述或 L4 实施第一周微同步处理）。

- 0 阻塞项。
- 9 关注项已记录在案，均为"命名/枚举漂移 + Ruff 规则 planned + 附录 B 与正文不符 + framework version 冲突 + public API 缺失"性质，不影响文档结构完整性与可执行性。
- 4 建议项移交 v0.2.1 / L4 实施阶段。
- §10.1 验收清单（187 测试 ID + 44 文件镜像清单 + 6 重静态门禁）+ 附录 A 6 子表 30 行 + 附录 B 5 子表 49 行 结构自洽，作为本次升级的凭证。
- 依据宪法 §14.5 MVP 例外时间窗口，单点评审有效。

**下一步**：
1. ✅ **已完成（2026-07-29）** L3-3 Spec 头部升级 v0.2.0（版本/状态/变更记录/配套 Review 引用 + §M.1/§M.2/§M.3 元数据）。
2. ✅ **已完成（2026-07-29）** 关注项 **row 4-9 六项全部在 v0.2.0 PR 内同步修正**：
   - row 4/5 → 附录 B.2 row 12/13 方法名与方法数对齐 §3.2；
   - row 6 → 新增 **§3.7 Lifecycle 11 步启动序列 + `lifecycle.py`**（SDK 第 12 文件 · SDK-LC-001~008）；
   - row 7 → §3.2 补入 **`AdapterError.to_jsonrpc_error()`** wire 契约（含 framework_error + 脱敏约束 · SDK-PROT-014/015）；
   - row 8 → §9.4 六个 image tag 全部对齐 §3.5 `VERSION_MATRIX.min_version` + 新增对齐矩阵与 **HELM-IMG-001~006**；
   - row 9 → **选项 A** 补齐 `Adapter` / `AdapterErrorCode` / `create_retry_policy` / `Lifecycle`，`__all__` 14 → 18 符号。
   - 连带同步：文件计数 41 → 42、测试 ID 187 → 200、镜像清单 44 → 45、全文 `ErrorCode.` → `AdapterErrorCode.`（17 处）。
   - **未在本次 PR 处理**：row 1（剩余 4 处命名漂移，需与 L2-3 Spec 成对修改）/ row 2（`ST-ADAPTER-BOUNDARY` Ruff 插件，需代码实现）→ v0.2.1 / L4 第一周；row 3 已闭环。
3. §F.1-§F.6 跨文档同步（L1 Arch/Spec、L2-3 Spec 附录、L3-1/L3-2 Spec 附录 A.5、ROADMAP、README、CONSTITUTION-CHANGELOG）。
4. git commit。
5. 后续：L3-4 Hello Agent / L3-5 Knowledge Service / L3-6 Memory backend 文件级 Spec 起草（L3 阶段 2/6 → 后续）。

---

## §O 跨文档同步步骤（建议本会话 / 下一会话执行）

| # | 文档 | 同步内容 | 状态 |
|---|------|----------|------|
| F.1 | L1 Architecture v0.2.0 §3.5 + §4.3 | L3-3 文件级落地完成标记 + 35 文件清单引用 | 待执行 |
| F.2 | L1 Spec v0.2.0 §16 | 187 测试 ID 文件级确认标记 | 待执行 |
| F.3 | L2-3 Spec v0.2.0 附录 A | 反向引用升级为 L3-3 v0.2.0 + 评审链接 | 待执行 |
| F.4 | L3-1 Spec 附录 A.5 + L3-2 Spec 附录 A.5 | L3-3 引用升级为 v0.2.0 + 评审链接 | 待执行 |
| F.5 | ROADMAP.md | L3 阶段进度更新（L3-1 + L3-2 + L3-3 v0.2.0 通过；L3-4 启动） | 待执行 |
| F.6 | README.md + CONSTITUTION-CHANGELOG.md + archive/README.md | v0.2.0 通过标记 + #58 评审记录 + L3-3 覆盖丢失备注 | 待执行 |

---

## §P 附录

- **评审方法**：全文通读（2431 行）+ §10.1 187 ID 加总核验 + 附录 A 30 行跨文档一致性核对 + 附录 B 49 行追溯矩阵结构核验 + 抽样 3 条跨文档一致性核对（L2-3 §1.3 public API + L2-3 §2.1 路径 + ADR-0005 §3.3 模块映射）。
- **未做**：L4 实施阶段才能验证的项（实际 SDK import 路径、framework version 兼容性、CI 门禁真实运行结果）不在本次文档评审范围内。
- **参照篇幅**：L3-2 Spec 评审 217 行 18KB；L2-3 Spec 评审 641 行 53.5KB；本评审 ~500 行 / ~30KB，符合"L3 文件级评审可比 L2 模块级评审更聚焦但需覆盖 187 ID 颗粒度"的预期。
- **本次会话实际水位**：~12-15% 安全（评审报告 Write + 9 项关注项整理 + 后续 git commit + 微同步），远低于 §16.1.4 50% 临界。