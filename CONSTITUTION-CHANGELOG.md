# superteam-a2a 宪法修订日志

> 记录本项目宪法（`CONSTITUTION.md`）的所有修订历史。
> 任何宪法修改必须先在本文件记录，再合并到 `CONSTITUTION.md` 附录 C。

---

## 修订记录

| 日期 | 版本 | 变更类型 | 变更范围 | 决策人 | ADR |
|------|------|----------|----------|--------|-----|
| 2026-07-23 | v0.1.0-draft → v0.1.0 | 正式批准 | 仅元数据（版本号、生效日期、签署、版本历史条目），无条款实质性变更 | 项目发起人 | — |
| 2026-07-23 | v0.1.0 | **14.5 例外时间窗口明确** | MVP 例外 14.5 适用区间明确为 **v0.1.0（含）→ v1.0.0（不含）**；v1.0.0 发布后全部例外自动失效 | 项目发起人 | — |
| 2026-07-23 | v0.1.0 → v0.2.0 | 新增条款 | 第二条新增 2.9 款"记忆可追溯"（Memory Traceability）：4 级作用域 + agent-private 正交维度 + confidence / decay / scope 三项强制字段 | 项目发起人 | ADR-0004 |
| 2026-07-23 | v0.2.0 → v0.3.0 | 新增条款 | 新增第十六条"会话与上下文管理"（Session & Context Continuity）：50% 上下文水位红线 + 保存-暂停-交接三步动作 + 与第十五条 / 2.9 的关系 | 项目发起人 | — |
| 2026-07-24 | v0.3.0 → v0.4.0 | 条款修订（MINOR） | 第十六条 §16.1 修订——明确模型上下文窗口基线 = 1M tokens、50% 红线 = 500K tokens、新增 §16.1.3"按实际水位判断"执行细则（4 项累加估算方法）、§16.1.4 典型水位参照表（含 6 个典型场景）；修正未明确窗口基线导致的误判风险 | 项目发起人 | — |
| 2026-07-24 | v0.4.0 → v0.5.0 | 架构条款修订（MINOR） | 依据 ADR-0005：新增 §3.8 Python-first 实现边界；平台自有代码锁定 Python 3.12+；§9 改为 pytest/async/Hypothesis/kind + Ruff/Pyright/Bandit/pip-audit；§10 改为 Python docstring；§13 上游维护改为 A2A Python SDK/Kopf/Kubernetes async client；§14 L3 注释例外改为 Python；§15 类型检查红线改为 Pyright strict/Ruff | 项目发起人 | ADR-0005 |
| 2026-07-24 | L2-1 v0.2.0 Python 通过 | **不触发宪法修订** | L2-1 A2A Protocol Python 重写 + 评审通过（10 维度全 PASS）；L1 Architecture + Spec 跨文档同步（F.1/F.2/F.3）完成；**§3.8 Python-first 实现边界**已通过 L2-1 实战验证；**§9.7 静态质量 + §13.6 维护 A2A Python SDK**已通过 L3-2 上游歧义收敛（D-1~D-7） | 项目发起人 | ADR-0005 + L2-1 评审 |
| 2026-07-24 | L2-2 v0.2.0 Python 通过 | **不触发宪法修订** | L2-2 Operator Core Python 重写 + 评审通过（10 维度全 PASS · 0 阻塞项 · 80KB / 1583 行）；L1 + L2-1/L2-3/L2-4 Spec 跨文档同步（§F.1-§F.6 全部 6 步）完成；**§3.8 Python-first** + **§9.7 静态质量 + §9 单元测试 ≥ 80% 覆盖 + §6 mTLS + §7 可观测性 + §13 SDK 维护**全部通过 L2-2 实战验证（Kopf + kubernetes_asyncio + Pydantic v2 + structlog + OTel + cert-manager 集成）；Spec v0.2-draft Python 待下次会话独立起草 | 项目发起人 | ADR-0005 + L2-2 评审 |
| 2026-07-28 | L3-2 A2A Core v0.2.0 通过 | **不触发宪法修订** | L3-2 A2A Core Library 文件级 Spec 落地（156KB / 2808 行 → v0.2.0 2852 行 / 160KB；7 子包 + 4 extension router + mTLS + ASGI server + Discovery/Client + async offload + 24 错误码 + 15 指标 + 9 Helm 模板 + 276 测试 ID / 21 组文件级映射）+ 评审（217 行 / 20KB / §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项）+ L1 Arch/L1 Spec/L2-1/L3-1/ROADMAP 跨文档同步完成；**§3.8 Python-first 边界**（`a2a.upstream` / Ruff ST-A2A-BOUNDARY）+ **§6 mTLS**（CertHotReloader 原子替换）+ **§7 可观测性**（15 指标 11+4 + structlog + OTel）+ **§9.7 静态质量**（5 重 gate）+ **§13.6 上游追踪**（a2a-sdk pin + 三级升级）全部通过 L3-2 实战验证；Go baseline 1.0 已归档（62KB / 1446 行 / 未评审） | 项目发起人 | ADR-0005 + L3-2 评审 |
| 2026-07-27 | **L2-4 v0.2.0 Python 通过**（**L2 阶段 4/4 完成**） | **不触发宪法修订** | L2-4 Knowledge/Memory Python 重写 + 评审通过（[#43 评审](docs/reviews/l2-4-knowledge-memory-spec-python-review.md) §A-§P 10 维度全 PASS · 0 阻塞项 · 3 关注项 · 4 建议项 · 194.6KB / 4152 行 / 16 主章节 + 2 附录 + §16 元数据 / 60 测试 ID + 30 验收点 + 22 开放问题）；L1 Architecture + Spec + L2-3 附录 A + ROADMAP + README + CONSTITUTION-CHANGELOG 跨文档同步（§F.1-§F.6 全部 6 步）完成；**§3.8 Python-first** + **§6 admission 双向互斥** + **§7 可观测性（17 Prometheus + OTel + structlog + K8s Events）** + **§9 静态质量（8 项门禁）** + **§11.5 event-loop lag < 100ms** 全部通过 L2-4 实战验证（3 Pydantic v2 CRD + typing.Protocol + Kopf @kopf.timer + Leader Election Lease + anyio.to_thread.run_sync + Clock Protocol + FakeClock + cert-manager TLS + admission 50ms fail-closed + 4 A2A method handler + 5 维矩阵 + 4 级 scope 继承 + 23 错误码 StrEnum + BM25 InvertedIndex + decay/reinforce/GC/promotion 数学）；**L2 阶段 4/4 全部完成**（L2-1 + L2-2 + L2-3 + L2-4 全部 v0.2.0 Python 评审通过；Python 化 100%） | 项目发起人 | ADR-0005 + L2-4 评审 |
| 2026-07-23 | v0.1.0-draft | 初稿 | 全 15 articles + 3 appendices（参考 AgentCompany 宪法 v0.1.3-draft 适配） | 项目发起人 | — |

---

## v0.5.0 Python-first 修订（已批准）

> **2026-07-24 项目发起人批准；依据 [ADR-0005](docs/adr/0005-python-first-technology-stack.md)**

本次修订只改变平台自有实现语言与对应质量工具，不改变 6 CRD、6 A2A method、Kubernetes/A2A/mTLS/可观测性/Knowledge/Memory 公共契约。

- 新增 §3.8：平台自有实现使用 Python 3.12+；第三方 Agent Runtime 继续语言无关。
- §9：pytest + async test + Hypothesis + kind；新增 Ruff/Pyright/Bandit/pip-audit/lockfile 门禁。
- §10：public API 使用 Python docstring + 严格类型签名。
- §13：维护 A2A Python SDK、Kopf、Kubernetes Python/async client 兼容性。
- §14：MVP L3 注释例外改为类型签名 + docstring + `# Why:`。
- §15：禁止关闭或降低 Pyright strict / Ruff。
- 回滚：任何核心模块偏离 Python、引入第二核心语言或降低公共契约，必须新建 ADR。

---

## 14.5 例外时间窗口（已明确）

> **2026-07-23 项目发起人批准**

- **例外生效区间**：自 `v0.1.0` 起（含），至 `v1.0.0` 发布前（不含）
- **例外撤销触发**：`v1.0.0` 发布当日全部例外自动失效
- **适用于 14.5 条款全部三项例外**：
  - L1 + L2 设计可合并（若模块数 ≤ 3）
  - L3 Spec 可由代码注释替代
  - 评审可单点（但 PR 描述必须明确"单点评审"理由）
- **不适用于**：质量第一性（第十五条）、安全规范（第六条）、可观测性（第七条）、API 向后兼容（2.6）—— 这些条款无例外
- **变更历史**：本条目作为 14.5 例外时间窗口的正式记录，与 v0.1.0 元数据变更同批生效

---

## 修订规范

### 必须记录的内容
- 版本号变更
- 变更类型（初稿 / 正式批准 / 修订类型 / 修订范围）
- 决策人
- 关联 ADR（若涉及）

### 修订流程
1. 提议者开启 Issue 或 Discussion，描述修订动机
2. 维护者团队评审（lazy consensus + binding vote）
3. 通过后：
   - 修改 `CONSTITUTION.md` 顶部版本号
   - 在 `CONSTITUTION.md` 附录 C 追加一行
   - 在本文件（同 `CONSTITUTION-CHANGELOG.md`）追加一行
4. 涉及条款变更的，必须同时在 `docs/adr/NNNN-constitution-amendment.md` 创建 ADR

### 版本号规则
- **MAJOR**：条款修订或新增条款（破坏性变更）
- **MINOR**：非破坏性条款修订（增补、措辞优化）
- **PATCH**：仅元数据修订（版本号、生效日期、引用更正）
- 初稿阶段可在版本号后追加 `-draft` 后缀，正式批准时移除

---

## 待修订事项

> 当前没有待修订的事项。

未来若需要修订，请在本节记录"提议中"的修订，并在合并后归入"修订记录"表。
