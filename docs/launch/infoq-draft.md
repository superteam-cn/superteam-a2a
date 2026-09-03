# InfoQ：superteam-a2a v0.1.0

> **Submission target**: <https://www.infoq.cn/write> 或 投稿到 editors@infoq.com
>
> **Status**: ⏳ pending (maintainer action)
>
> **风格**: 行业分析 + 实践结合（InfoQ 编辑审核严格）

---

## 文章标题

```
从单进程到 6 CRD：用 Kubernetes 原生方式构建 AI Agent 平台的 superteam-a2a 实践
```

## 摘要（200 字以内）

```
superteam-a2a 是一个 Kubernetes 原生的多 Agent 编排运行时，目标是解决 LangChain / AutoGen / CrewAI 等 6 大 AI Agent 框架之间的互通难题。本文分享该项目在 6 周内从 0 到 v0.1.0 的实践，包括 6 CRD 设计、Knowledge + Memory 单进程架构、50ms fail-closed admission webhook 等关键技术决策，以及踩过的三个典型工程坑。
```

---

## 正文

### 行业背景：从单 Agent 到 Agent 集群

2024 年是 LLM 应用元年，2025 年开始进入「Agent 化」阶段。当单 Agent 能力成熟后，业务向「多 Agent 协作」演进 —— 规划 Agent 委派任务，研究 Agent 检索资料，编码 Agent 生成代码，审查 Agent 把关质量 —— 传统框架在「多 Agent 互通」层几乎空白：

- **协议真空**：LangChain 不能调用 AutoGen，CrewAI 不知道 Semantic Kernel 存在
- **运行时缺失**：没有 K8s 原生支持，没有服务发现、admission 控制、可观测性
- **协议碎片**：各家自研 RPC，跨框架集成成本极高

2025 年 Google 发布 [A2A（Agent-to-Agent）协议](https://github.com/google/A2A)，定义了 Agent Card、Message、Task、Artifact、Streaming 等核心类型，并采用 JSON-RPC 2.0 over HTTP/SSE。但 A2A 只规定了「协议层」，不规定「运行时层」。

**superteam-a2a 就是 A2A 的 Kubernetes 原生运行时实现。**

### 项目方法论：Spec-First + TDD

superteam-a2a 采用 [Spec-First + TDD](https://github.com/superteam-cn/superteam-a2a/blob/main/CONTRIBUTING.md) 的方法论：

1. **L1 架构 → L2 维度 → L3 文件 Spec → ADR**：所有架构决策先写 Spec，再实装
2. **宪法（CONSTITUTION.md v0.6.0）**：17 节架构法律，含 SOLID 6 原则、水位红线、PR 流程
3. **TDD 三层**：单元测试 + 集成测试 + 验收测试，共 474 个 ID
4. **4 重静态门禁**：ruff check / ruff format / pyright strict / pytest

### 架构设计：6 CRD

我们没有用单一 CRD 表达「Agent 平台」，而是拆成 6 个小而专的 CRD：

| CRD | 角色 |
|---|---|
| `Agent` | 单个 AI Agent |
| `AgentSet` | 水平扩展 Agent 集群 |
| `Workflow` | 声明式 DAG（v0.5+） |
| `KnowledgeScope` | 4 级 scope |
| `KnowledgeItem` | BM25 可检索条目 |
| `Memory` | Agent 经验记录 |

这符合 Kubernetes 「小而专」的设计哲学，也避免了单一巨型 CRD 带来的 schema 膨胀问题。

### 关键技术决策：单进程 Knowledge + Memory

最大的架构决策是 **Knowledge Service + Memory Service 共享一个 Python 进程**（[ADR-0006 v1.0](https://github.com/superteam-cn/superteam-a2a/blob/main/docs/adr/0006-memory-transport.md)）。

考虑过的方案：

| 方案 | 评估 |
|---|---|
| HTTP loopback | ❌ 每次调用 +50ms |
| 共享 mmap | � 脆弱、跨进程调试难 |
| 双 Pod + Redis | ❌ 最终一致性头疼 |
| **单进程（采纳）** | ✅ 简单、低延迟、单 leader election |

代价是镜像 ~150 MB（vs 80 MB），但换来：

- 单 Deployment、单 RBAC、单健康检查
- 无跨进程序列化
- MemoryBackend 抽象层支持 K8s Lease 领导者选举

### 关键技术决策：50ms fail-closed admission

所有 Memory / Knowledge 写入都经过 admission webhook 校验：

```python
async def validate_record(req: RecordRequest) -> Decision:
    try:
        async with timeout(50ms):
            # 1. Pydantic v2 校验
            # 2. kopf admission handler
            # 3. Mutex 检查
            # 4. visibility 矩阵检查
            return Decision.allow()
    except TimeoutError:
        return Decision.deny()  # fail-closed
```

实测 p95 = **28ms**，在预算内且有充足 headroom。

### 6 周实施数据

- **62 PR merged**
- **474/474 测试 PASS**（2 秒本地跑完）
- **~30,000 行 Python**（8 个 workspace member）
- **Apache 2.0**

### 三个工程坑

#### 坑 1：Windows + WSL2 + kind 文件系统

`C:\path\to\repo` 和 `/mnt/c/path/to/repo` 在 Python import 系统里**不是同一个路径**。修复方案：`os.path.realpath()` 规范化路径 + pre-commit hook 拒绝反斜杠。

#### 坑 2：typo path 影子目录

Subagent 写 60 个文件到 `services/foo/supteam_a2a/...`（少了 "er"），Windows bash 静默创建两个目录，typo 进了 git index，`pytest` 找不到任何文件。诊断用了一整天。教训：**永远传绝对路径给 Subagent，commit 前用 `git ls-files` 验证**。

#### 坑 3：admission webhook 延迟预算

以为 50ms 很宽松，实际在生产路径（Pydantic + kopf + 网络 + mutex）下 happy path 就要 25-35ms。50ms 仅留 ~15ms headroom。E2E 测试必须主动注入延迟验证。

### v0.1.0 还差什么

诚实清单：

- **框架适配器**：v0.1.0 仅 ship Hello Agent 参考实现。LangChain / AutoGen / CrewAI 适配器有 Spec 但没实装
- **Workflow CRD**：声明式 DAG 有 Spec 但没建
- **多集群联邦**：在路线图

### 对生态的启示

我们认为，多 Agent 编排平台的未来形态应该是：

1. **协议层**：A2A 是事实标准，无需重复造轮子
2. **运行时层**：K8s 是最佳载体，但需要「Agent 化」的 CRD 抽象
3. **数据层**：Knowledge + Memory 应该尽量内聚（单进程），避免分布式一致性陷阱
4. **安全层**：admission webhook + RBAC + NetworkPolicy 是底线，缺一不可
5. **可观测层**：25 个 Prometheus 指标 + 8 条告警规则，覆盖核心 SLO

### 加入

- **仓库**：<https://github.com/superteam-cn/superteam-a2a>
- **Release notes**：<https://github.com/superteam-cn/superteam-a2a/releases/tag/v0.1.0>
- **贡献指南**：<https://github.com/superteam-cn/superteam-a2a/blob/main/CONTRIBUTING.md>

—— CoderZhangfujiang（Zach Zhang）

---

## InfoQ 发布要点

- **审核严格**：InfoQ 编辑会看投稿，建议同时投递 `editors@infoq.com`
- **风格**：行业分析 + 实践结合，避免纯产品宣传
- **字数**：1500-3000 字为佳
- **配图**：架构图 + 关键决策对比表
- **作者署名**：带上「CoderZhangfujiang」GitHub 链接
- **时间**：周二或周三上午投递
