Title: 6 周从 0 到 v0.1.0：基于 K8s 的多 Agent 编排平台 superteam-a2a 实战

Body:

## 背景

如果你在生产环境跑过 AI Agent，一定踩过这些坑：

- 框架擅长跑**单个** Agent，但多个 Agent 之间交接任务（规划 → 编码 → 审查）没有标准协议
- LangChain 不能直接调用 AutoGen，CrewAI 不知道 Semantic Kernel 存在
- 没有 K8s 原生支持 —— 用 Deployment 跑 Agent？还是 StatefulSet？
- 没有服务发现 —— Agent A 怎么知道 Agent B 在哪？
- 没有可观测性 —— 哪个 Agent 慢？哪个失败？
- 没有 admission 控制 —— 恶意 Agent 想读 production 作用域怎么办？
- 没有共享记忆 —— 每个 Agent 都维护自己的上下文

**superteam-a2a** 是为了解决这些问题而生的项目。

## 核心特性

基于 Kubernetes 原语实现：

- **6 个 CRD**：`Agent`、`AgentSet`、`Workflow`、`KnowledgeScope`、`KnowledgeItem`、`Memory`
- **Google A2A 协议**：`Agent Card`（`.well-known/agent.json`）、`Message`、`Task`、`Artifact`、`Streaming`
- **跨命名空间服务发现**：DNS 风格的解析器
- **层次化知识管理**：4 级 scope（行业/组织/团队/项目）+ BM25 倒排索引
- **持久化记忆**：confidence + decay + reinforce 生命周期 + 5 维可见性矩阵
- **admission webhook 50ms fail-closed**：每次 record/query 都在 50ms 内完成 scope + mutex + visibility 校验
- **生产级安全**：restricted Pod Security Standards + 非 root UID 1000 + NetworkPolicy 默认拒绝 + cert-manager mTLS（可选）+ 双 Role RBAC

## 关键架构决策：单进程 D 方案

最大的决策是 **Knowledge Service + Memory Service 跑在同一个 Python 进程里**（ADR-0006 v1.0 D 方案）。

考虑过的方案：

| 方案 | 拒绝理由 |
|---|---|
| HTTP loopback | 每次调用加 50ms 延迟，没有架构收益 |
| 共享 mmap | 脆弱，难调试 |
| 两个 Pod + Redis | 多一个移动部件，最终一致性头疼 |
| **单进程（采纳）** | 单 Deployment、单 RBAC、单健康检查、单 leader election（需要时） |

代价：镜像 ~150 MB vs 80 MB。值得。

## 实测数字

- **466/466 测试 PASS**（2 秒本地跑完）
- **62 PR merged**（2026-07-08 启动至今）
- **Phase 4 8/8 PR 全部 ship**（v0.1.0 在 2026-08-16 发布）
- Apache 2.0
- 单二进制，无外部依赖（除了可选的 Prometheus / cert-manager）

## 上手指南

```bash
git clone https://github.com/superteam-cn/superteam-a2a
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest   # 2 秒跑完 466 个测试

# 部署 Hello Agent 到本地 kind
kind create cluster --name superteam-a2a-dev
docker buildx build -t superteam-a2a/hello-agent:dev services/hello-agent/
kind load docker-image superteam-a2a/hello-agent:dev --name superteam-a2a-dev
helm install hello-agent helm/hello-agent/

kubectl get agentsets
# NAME           FRAMEWORK   STATUS    DISCOVERED
# hello-agent    hello       Running   0

kubectl port-forward svc/hello-agent 8080:8080 &
curl http://localhost:8080/.well-known/agent.json | jq
```

## 踩过的坑（写给后来人）

### 1. admission webhook 的延迟预算

我以为 50ms fail-closed 很宽松，实际上：

- Pydantic v2 校验：~5ms
- kopf admission handler 调用：~10ms
- 调用 K8s API 网络往返：~5-15ms
- Mutex 检查 + visibility 矩阵：~3ms
- 总计：~25-35ms（happy path）

50ms 留了 ~15ms 给突发流量。E2E 测试里要主动注入延迟验证。

### 2. Windows + WSL2 + kind 的文件系统陷阱

Windows + WSL2 + 本地 kind 集群，三层文件系统互相打架。`C:\path\to\repo` 和 `/mnt/c/path/to/repo` 在 Python import 系统里**不是**同一个路径。用 `os.path.realpath()` 救场，加 pre-commit hook 拒绝反斜杠路径。

### 3. typo path 影子目录

Subagent 把 60 个文件写到了 `services/foo/supteam_a2a/...`（少了 "er"）而不是 `services/foo/superteam_a2a/...`。Windows bash 安静地创建了两个目录，typo 路径进了 git index。`git status` 显示一切正常，但 `pytest` 一个文件都找不到，诊断用了一整天。

教训：**不要让 Subagent 通过相对路径写文件。永远传绝对路径，并在 commit 前用 `git ls-files` 验证。**

## v0.1.0 → v1.0 还差什么

- **框架适配器**：v0.1.0 只 ship Hello Agent 参考实现。LangChain / AutoGen / CrewAI 适配器有 Spec 但没实装。SDK 设计成每个框架只需 5-10 行集成代码。
- **Workflow CRD**：声明式 DAG 有 Spec 但没建。
- **多集群联邦**：在路线图上。

## 加入

- **仓库**：https://github.com/superteam-cn/superteam-a2a
- **贡献指南**：CONTRIBUTING.md（4 重静态门禁 · kind 演示）
- **Issue**：https://github.com/superteam-cn/superteam-a2a/issues

如果你在生产环境跑 Agent 集群，我想听听你的 admission webhook 延迟预算是多少。如果你维护 LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents，适配器 SDK 设计成 5-10 行集成 —— 告诉我你想要什么。

—— CoderZhangfujiang (Zach Zhang)