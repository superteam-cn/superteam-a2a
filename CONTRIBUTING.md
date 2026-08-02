# Contributing to superteam-a2a

First of all — thank you for taking the time to contribute.

`superteam-a2a` 是 **spec-driven** 的多框架 Agent 编排平台：在 Kubernetes 上以 A2A protocol 桥接 LangChain / LlamaIndex / CrewAI / AutoGen 等异构 agent 框架，提供统一 CRD + 单一控制平面 + 可插拔 Adapter SDK。本仓库 L1-L3 文件级 Spec 已 100% 落地、L4 实施层已解锁（ADR-0006 v1.0 Accepted D 方案 · 2026-07-30），欢迎通过 PR 参与 v0.3.x 实施。

## 1. 项目定位

- **核心目标**：让任意 agent 框架在 K8s 上以"单 CRD + 单一控制平面 + 单一可观测"方式被编排。
- **当前阶段**：L4 Phase 1 MVP Core（uv workspace + 6 CRD + 单进程 KS+MEM + Hello Agent 冒烟）。
- **设计哲学**：spec-driven / kebab-case / 单原子 commit / 错误码零漂移 / 单进程优先。
- **可观察 / 可审计**：所有架构决策走 ADR（`docs/adr/`），所有宪法条款走 `docs/constitution/CONSTITUTION.md`，所有 Spec 评审走 `docs/reviews/`。

## 2. 代码风格

| 项        | 工具 / 约定                                   | 命令                          |
|-----------|-----------------------------------------------|-------------------------------|
| 格式化    | PEP 8 + ruff format（line-length=100）         | `uv run ruff format .`       |
| Lint      | ruff 0 error（E/F/W/I/UP/B/SIM/RUF 全开）      | `uv run ruff check .`        |
| 类型检查  | pyright strict mode（`pyrightconfig.json`）     | `uv run pyright`             |
| 包管理    | uv workspace（`uv.lock` 必须提交 · §9.7）       | `uv sync --all-extras`       |
| Python    | 3.11 / 3.12 双兼容（`pyproject.toml` `python`) | `uv python list`             |
| YAML      | 2 空格缩进 + yamllint                         | `yamllint .`                 |
| Markdown  | markdownlint（`markdownlint.json`）            | `markdownlint **/*.md`       |
| Helm      | helm lint                                     | `helm lint helm/<chart>`     |
| 命名      | kebab-case（文件 / 包 / CRD / 资源）          | —                             |
| 注释      | 中英双语 · 关键算法用中文，关键接口用英文      | —                             |
| Commit    | Conventional Commits                          | 见 §3                         |

## 3. Commit 规范

格式：`<type>(<scope>): <subject>`

### Type（前缀）

- `feat` — 新功能 / 新 CRD / 新 A2A method
- `fix` — 修复 bug
- `docs` — 仅文档（spec / ADR / 宪法 / README）
- `spec` — Spec 增删修（含 L1/L2/L3 段落）
- `arch` — 架构图 / 边界规则 / 部署拓扑
- `chore` — 杂项（依赖 / 工具链 / 配置）
- `ci` — CI / GitHub Actions
- `test` — 仅测试新增 / 修复
- `refactor` — 重构（不改变行为）
- `perf` — 性能优化
- `revert` — 回滚

### Scope（范围）

**框架级**（与 ADR 阶段对应 · 优先用于 spec/arch/docs）：

- `L1` · `L2` · `L3` · `L4` — 5 层 Spec/实施阶段
- `L2-1` … `L2-4` · `L3-1` … `L3-6` — 具体子模块
- `ADR-NNNN` — 引用具体 ADR（如 `ADR-0006`）
- `§F` — 跨文档同步步骤
- `§M-X.Y` — 评审关注项

**模块级**（L4 实施层代码变更 · 优先用于 feat/fix/test）：

- `operator` — Operator controller
- `a2a-core` — A2A protocol core
- `adapter` — Adapter SDK / framework adapter
- `knowledge-memory` — 单进程 KS+MEM service
- `hello` — Hello Agent
- `helm` — Helm chart
- `ci` · `deps` · `constitution` — 工具链

**Step 标识**（L4 实施步骤）：

- `l4-step1` … `l4-step9` — L4 实施层具体步骤

**历史兼容**：v0.0~v0.2 阶段 commit scope 多为 `L3-X` / `L1` / `§F` 格式（如 `L3-6 v0.2.0`），L4 阶段后逐步引入模块级 scope。新 commit 推荐**框架级 + 模块级**双标注（如 `feat(L4-step1, operator): 新增 BackendBinding CRD`）。

### Subject（标题）

- 中文 50 字内，英文 72 char 内
- 首字母小写，结尾无句号
- 用动词原形（"add" / "fix" / "升级" / "关闭"）
- 引用 issue：`Closes #123` / `Refs #456` / `Refs ADR-0006`

### 示例

```text
feat(operator): 新增 BackendBinding CRD schema（v1alpha1）
fix(a2a-core): 修复 retry-after 头解析时的 off-by-one
docs(L3-6): 升级 v0.2.1 单进程架构（ADR-0006 D 方案）
chore(deps): bump ruff to 0.6.0
ci: 新增 helm lint workflow
spec(L1): §4.1 C-6 + C-7 合并为 Knowledge-Memory Service
```

## 4. 分支策略

- `main` — 保护分支，所有变更经 PR 合入
- `feature/l4-step1` — L4 实施步骤 1（uv workspace + 6 CRD）
- `feature/l4-step2` ... `feature/l4-step7` — 后续步骤
- `feat/<name>` — 新功能（如 `feat/backend-binding-crd`）
- `fix/<issue>-<short-desc>` — bug 修复
- `docs/<topic>` — 仅文档
- `spec/<l1|l2|l3>-<topic>` — Spec 段落
- `arch/<topic>` — 架构 / ADR
- `chore/<topic>` — 杂项

**禁止**：直接 push `main` / 长生命周期分支（> 30 天）/ 含无关变更的混合分支。

## 5. PR 流程

1. **创建 feature 分支**（见 §4 命名）
2. **本地 CI 全绿**（`ruff` + `pyright` + `pytest` + `yamllint` + `markdownlint` + `uv lock --check`）
3. **填写 PR 模板**（`.github/PULL_REQUEST_TEMPLATE.md`）：Summary / What's Inside / ADR table / 不变量保持 / File-level 摘要 / Test Plan / Open Questions / Reference
4. **Draft → Ready for review**：Draft PR 用于早期反馈，CI 跑通后转 Ready
5. **CODEOWNERS 自动指派**：单人项目 = `@CoderZhangfujiang`
6. **评审**：spec / arch / breaking 变更需评审（`docs/reviews/` 模板 10 维度）
7. **Squash merge**：默认 squash，commit message 由 PR 标题生成
8. **自动删 head**：GitHub 端配置 `Automatically delete head branches`
9. **关闭关联 issue / OPEN-XXX**：commit message 含 `Closes #123` / `Refs OPEN-L1-002`

**PR 标题必须遵循 §3 Conventional Commits**（与 commit message 一致）。

## 6. 开发环境

```bash
# 1. 装 uv（一次）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. clone + 装依赖
git clone git@github.com:superteam-cn/superteam-a2a.git
cd superteam-a2a
uv sync --all-extras

# 3. 装 git hooks（pre-commit：ruff + pyright + yamllint + markdownlint）
uv run pre-commit install

# 4. 验证
uv run ruff check .
uv run pyright
uv run pytest tests/ -v
```

**环境变量**（`.envrc` 或 direnv）：

```bash
# OpenTelemetry（local dev）
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=superteam-a2a-dev
# structlog：JSON renderer in prod，console renderer in dev
export STRUCTLOG_RENDERER=console
```

**Python 版本**：用 `uv python install 3.11 3.12` 双版本，CI 在两个版本上跑（matrix）。

## 7. 测试

| 层          | 命令                                            | 覆盖率门禁    |
|-------------|-------------------------------------------------|---------------|
| unit        | `uv run pytest tests/unit/ -v`                  | ≥ 80%         |
| integration | `uv run pytest tests/integration/ -v`           | ≥ 70%         |
| e2e         | `uv run pytest tests/e2e/ -v --cluster=kind`    | 必跑          |
| spec        | `uv run pytest tests/spec/ -v`                  | 100% L3 段落 |
| lint        | `uv run ruff check .`                           | 0 error       |
| type        | `uv run pyright`                                | 0 error       |
| manifest    | `yamllint .`                                    | 0 error       |
| doc         | `markdownlint **/*.md`                          | 0 error       |
| lock        | `uv lock --check`                               | 一致          |

**测试 ID 命名**（与 L3 Spec 段落 1:1 对应）：

- `TEST-OPER-001` ... `TEST-OPER-NNN`（Operator 段落 N）
- `TEST-A2A-001` ... `TEST-A2A-NNN`
- `TEST-ADP-001` ... `TEST-ADP-NNN`
- `TEST-KS-001` ... `TEST-KS-NNN`
- `TEST-MEM-001` ... `TEST-MEM-060`（Memory 段落 60）
- `TEST-HELLO-001` ... `TEST-HELLO-NNN`
- `MTLS-IT-001` — mTLS 端到端（已废弃 · ADR-0006 D 方案后单进程无 MTLS 跨进程）
- `INTEG-001` ... `INTEG-NNN`

**L4 实施层冒烟**：

```bash
kind create cluster --name superteam-a2a-dev
uv run operator & uv run services/knowledge-memory-service &
uv run agents/hello &
uv run pytest tests/e2e/ -v --cluster=kind
kind delete cluster --name superteam-a2a-dev
```

## 8. ADR 决策机制

| 阶段          | 状态          | 评审维度 | 决策人       |
|---------------|---------------|----------|--------------|
| v0.1-draft    | 候选方案      | 5 候选 × 7 维度决策矩阵 | Subagent |
| v1.0 推荐    | 主 Agent 验收 | 10 维度全 PASS + 0 关注项 | 主 Agent |
| Accepted      | 实施门禁     | §14.5 MVP 例外可单点 / 否则 v0.1 → v1.0 → Accepted 三步走 | 项目发起人 |
| Superseded    | 归档         | 引用 superseding ADR | 项目发起人 |

**5 候选方案 + 7 维度决策矩阵**（ADR-0006 模板）：

1. 决策背景（背景 + 约束 + 不变量）
2. 候选方案（5 候选 · 每候选一段）
3. 决策矩阵（5×7 维度 · 含合规 / 复杂度 / 性能 / 可观测 / 可演进 / 风险 / 实施成本）
4. 决策结论（主推荐 + 备选 + 不推荐）
5. 影响清单（受影响的 L1/L2/L3 段落 + Helm + uv workspace）
6. 开放问题（OPEN-ADR-NNNN-001~005）

**§14.5 MVP 例外窗口**：当 L4 实施层已解锁但 ADR 处于 v0.1-draft 阶段时，主 Agent 可走"v0.1-draft → v1.0 推荐 → Accepted"加速路径（参考 ADR-0006 v0.1 → v1.0 单次评审）。

## 9. Issue 提交流程

本项目提供 3 类 Issue 模板（`.github/ISSUE_TEMPLATE/`）：

- **bug**：行为错误 / 崩溃 / 异常输出
- **feature**：新功能 / 新 CRD / 新 framework adapter
- **spec-deviation**：实现与 Spec 不一致（**spec-driven 项目核心模板**）

每类 issue 必须填齐模板字段（环境 / Spec 段落 / L4 Component），否则 reviewer 将退回。

## 10. Open Questions 编号规则

格式：`<DOMAIN>-<NNN>`

| Domain            | 范围                        | 例                          |
|-------------------|-----------------------------|-----------------------------|
| `L1`              | L1 架构层                  | `OPEN-L1-001`               |
| `L2`              | L2 模块层                  | `OPEN-L2-OPER-001`          |
| `L3`              | L3 文件层                  | `OPEN-L3-A2A-001`           |
| `MEMORY`          | Memory 后端                | `OPEN-MEMORY-001`           |
| `KS`              | Knowledge Service          | `OPEN-KS-001`               |
| `ADR-NNNN`        | ADR 内部开放问题            | `OPEN-ADR-0006-001`         |
| `CI`              | CI / GitHub Actions        | `OPEN-CI-001`               |

**生命周期**：`OPEN` → 关联 ADR / Spec 段落 → 关闭（commit message `Closes OPEN-XXX-NNN`）→ §M.5 关注项台账登记

**禁止**：自创前缀 / 复用已关闭 ID / 与 issue 号混淆。

## 11. §16.1 红线纪律

宪法 v0.5.0 §16.1 上下文窗口纪律：

- **1M 窗口 / 500K 红线**：单次会话实际水位严禁超 50%（≈ 500K tokens）
- **单文件 < 30KB**：写入文件不超过 30KB（避免触及 50% 临界）
- **水位判断**：以主 Agent 实际累计输入 + 工具输出 + 文件写入总和为准，不依赖工具自报

**Subagent 接力模式**（达到 30% 时切换）：

- **模式 A — 研究-写作分离**：主 Agent 调研 → Subagent 隔离写大文件 → 主 Agent 验证 commit
- **模式 B — 评审隔离**：Subagent 隔离评审 Spec / ADR → 主 Agent 收口
- **模式 C — Workflow 编排**：主 Agent 串多 Subagent（如 #64 L3-6 4 接力）

**单次会话推荐**：1-2 个 Subagent 接力。超 3 个 Subagent = 危险信号。

## 12. 关键不变量

违反任何一项的 PR 必须修复后才能合入：

- [ ] **wire contract** — API / CRD schema 向后兼容（additive only）或显式 BREAKING + 迁移路径
- [ ] **错误码零漂移** — 12 MEMORY_* 错误码与 L2-4 v0.2.0 §9.1 权威名 100% 一致（`-32101` ~ `-32112`）
- [ ] **单进程架构** — Knowledge + Memory 合并单进程（ADR-0006 D 方案 Accepted · 2026-07-30），禁止 IPC socket / 共享 volume / 跨进程 transport
- [ ] **uv workspace 结构** — `packages/*` + `services/*` + `agents/*` 三个顶层目录（ADR-0005 Python-first）
- [ ] **kebab-case 命名** — 文件 / 包 / CRD / 资源 / Helm release 全 kebab-case
- [ ] **单原子 commit** — 一个 commit = 一个原子变更（不与无关变更混在一起）
- [ ] **零直接落 main** — 所有变更经 feature 分支 + PR 流程
- [ ] **Spec 一致** — 任何 Spec 变更前先有 ADR / 评审；任何代码变更前先有 Spec 段落
- [ ] **可观测** — 关键路径有指标 + 日志（structlog JSON 8 字段 + OTel trace）
- [ ] **可测试** — 关键算法有 unit 测试 + 端到端有 integration 测试

## 13. 联系方式

- **Maintainer**：[@CoderZhangfujiang](https://github.com/CoderZhangfujiang)
- **Security**：见 [`SECURITY.md`](./SECURITY.md)（**严禁公开 issue 报告安全漏洞**）
- **Code of Conduct**：[`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md)（Contributor Covenant v2.1）

## License

By contributing, you agree that your contributions will be licensed under [Apache 2.0](./LICENSE).
