# 知乎：superteam-a2a v0.1.0

> **Submission target**: <https://www.zhihu.com/pillar/create> 或 回答相关问题
>
> **建议路径**: 优先以「回答」形式发布到「如何构建生产级 AI Agent 编排平台？」「Kubernetes 上如何运行 AI Agent？」类问题；或直接发专栏文章
>
> **Status**: ⏳ pending (maintainer action)

---

## 文章标题（专栏）

```
从 0 到 v0.1.0：基于 Kubernetes 构建多 Agent 编排平台 superteam-a2a 的 6 周实践
```

## 文章标题（回答样式）

回答「**生产环境如何部署多个 AI Agent 让它们协作？**」类问题

---

## 正文

### 一、背景：为什么需要 Agent 编排？

2024 年以来，AI Agent 框架如雨后春笋：

- **LangChain**（最流行，生态最丰富）
- **AutoGen**（微软，多 Agent 对话）
- **CrewAI**（角色化协作）
- **Semantic Kernel**（微软企业级）
- **Strands**（AWS）
- **Smolagents**（HuggingFace）

每个框架都在**单 Agent 执行**这一层做到了极致。但当你需要**多个 Agent 协作** —— 规划 Agent 委派任务给研究 Agent，编码 Agent 交付给审查 Agent —— 你会发现：

1. **没有标准协议**：LangChain 不能直接调用 AutoGen，CrewAI 不知道 Semantic Kernel 存在
2. **没有 K8s 原生支持**：用 Deployment 跑 Agent？StatefulSet？Job？没有最佳实践
3. **没有服务发现**：Agent A 怎么知道 Agent B 在哪个 Pod？
4. **没有可观测性**：哪个 Agent 慢？哪个失败？
5. **没有 admission 控制**：恶意 Agent 想读 production scope 怎么办？
6. **没有共享记忆**：每个 Agent 都维护自己的上下文

### 二、为什么选 Google A2A 协议？

2025 年 Google 发布 [A2A（Agent-to-Agent）协议](https://github.com/google/A2A)，定义了：

- **Agent Card**：`.well-known/agent.json`，描述 Agent 能力（类似 OpenAPI）
- **Message / Task / Artifact / Streaming**：JSON-RPC 2.0 over HTTP/SSE
- **跨框架互操作**：理论上 LangChain 和 AutoGen 通过 A2A 可以对话

但 A2A 只定义了**协议**，没有定义**运行时**。谁来跑 Agent？怎么发现？怎么管？怎么监控？

**superteam-a2a 就是 A2A 的 Kubernetes 原生运行时。**

### 三、架构设计：6 CRD + 单进程 backend

我们定义了 6 个 CRD：

| CRD | 作用 |
|---|---|
| `Agent` | 单个 AI Agent |
| `AgentSet` | 可水平扩展的 Agent 集群 |
| `Workflow` | 声明式 DAG（v0.5+ 实装） |
| `KnowledgeScope` | 4 级 scope（行业/组织/团队/项目） |
| `KnowledgeItem` | 知识条目（BM25 检索） |
| `Memory` | Agent 经验记录（confidence + decay + reinforce） |

**关键决策**：Knowledge Service + Memory Service 跑在**同一个 Python 进程**里（[ADR-0006 v1.0 D 方案](https://github.com/superteam-cn/superteam-a2a/blob/main/docs/adr/0006-memory-transport.md)）。

考虑过的方案：

| 方案 | 拒绝理由 |
|---|---|
| HTTP loopback | 每次调用加 50ms 延迟 |
| 共享 mmap | 脆弱、难调试 |
| 双 Pod + Redis | 多一个移动部件，最终一致性 |
| **单进程（采纳）** | 单 Deployment、单 RBAC、单健康检查、单 leader election |

代价：镜像 ~150 MB（vs 80 MB）。值得。

### 四、关键技术点：admission webhook 50ms fail-closed

每次 Agent 写入 Memory 或 Knowledge，都要经过 admission webhook 校验：

- **Pydantic v2 校验**：~5ms
- **kopf admission handler**：~10ms
- **调用 K8s API 网络往返**：~5-15ms
- **Mutex 检查 + visibility 矩阵**：~3ms
- **总计**：~25-35ms（happy path）

50ms 留了 ~15ms 给突发流量。E2E 测试里要主动注入延迟验证。

实测 p95 = **28ms**，在预算内。

### 五、实施过程：6 周 62 PR

```
Week 1-2: 宪法 + L1/L2/L3 Spec 起草（ADR-0001 ~ ADR-0006）
Week 3-4: Phase 1-2 骨架代码（packages + uv workspace）
Week 5-6: Phase 3-4 实装（A2A server + Knowledge/Memory backend + Helm）
```

每个 PR 都过 4 重静态门禁：

1. **ruff check**（lint）
2. **ruff format**（format）
3. **pyright strict**（type check）
4. **pytest**（474/474 PASS）

PR 流程：feat 分支 → PR → CI 5 workflows SUCCESS → maintainer squash merge。

### 六、踩坑教训

#### 1. Windows + WSL2 + kind 文件系统

`C:\path\to\repo` 和 `/mnt/c/path/to/repo` 在 Python import 系统里**不是同一个路径**。用 `os.path.realpath()` 救场，加 pre-commit hook 拒绝反斜杠路径。

#### 2. typo path 影子目录

Subagent 把 60 个文件写到了 `services/foo/supteam_a2a/...`（少了 "er"）。Windows bash 安静地创建了两个目录，typo 路径进了 git index。`git status` 显示一切正常，但 `pytest` 一个文件都找不到。

**教训**：不要让 Subagent 通过相对路径写文件。永远传绝对路径，并在 commit 前用 `git ls-files` 验证。

#### 3. Admission webhook 的延迟预算

以为 50ms 很宽松，实际很紧。E2E 测试必须主动注入延迟验证，不能假设 happy path。

### 七、上手指南

```bash
git clone https://github.com/superteam-cn/superteam-a2a
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest  # 474 tests in ~2s

# 部署 Hello Agent 到本地 kind
kind create cluster --name superteam-a2a-dev
docker buildx build -t superteam-a2a/hello-agent:dev services/hello-agent/
kind load docker-image superteam-a2a/hello-agent:dev --name superteam-a2a-dev
helm install hello-agent helm/hello-agent/

kubectl get agentsets
```

5 分钟完整 demo 见 [CONTRIBUTING.md](https://github.com/superteam-cn/superteam-a2a/blob/main/CONTRIBUTING.md)。

### 八、后续规划

- **v0.5（Phase 5 LAUNCH）**：LangChain / AutoGen / CrewAI 适配器
- **v1.0（Phase 6）**：Workflow CRD + 5 框架适配器 GA + 多集群联邦
- **v1.0+**：可视化工作流编辑器

### 九、我想听你的意见

如果你：

- **维护某个 Agent 框架**：适配器 SDK 设计成 5-10 行集成。告诉我你想要什么？
- **是 K8s operator**：你的 admission webhook 延迟预算是多少？
- **在生产环境跑 Agent 集群**：你最想要的工作流原语是什么？

**仓库**：<https://github.com/superteam-cn/superteam-a2a>
**问题反馈**：<https://github.com/superteam-cn/superteam-a2a/issues>

—— CoderZhangfujiang（Zach Zhang）

---

## 知乎发布要点

- **优先级**：发**专栏文章**而不是回答问题（更可控、更容易被推荐）
- **避免硬广**：用「实践 + 教训」叙事，不直接说「快来用我们」
- **配图建议**：架构图 + kubectl get 输出 + 延迟 benchmark 截图
- **互动**：评论里回答具体技术问题（不要回避限制 —— 说清楚 v0.1.0 不包含什么）
- **时间**：周一或周二上午 10:00 发布（知乎算法对新文章有 24h 流量倾斜）
