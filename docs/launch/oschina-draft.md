# OSCHINA：superteam-a2a v0.1.0

> **Submission target**: <https://www.oschina.net/question/add?type=news> 或 <https://my.oschina.net/admin/blogs>
>
> **Status**: ⏳ pending (maintainer action)

---

## 资讯标题

```
superteam-a2a v0.1.0 发布：Kubernetes 原生多 Agent 编排平台
```

## 资讯摘要

```
基于 Kubernetes + Google A2A 协议，支持 LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents 6 大框架互通。6 CRD · 单进程 backend · 50ms fail-closed admission · 474 测试全绿 · Apache 2.0
```

---

## 正文

superteam-a2a v0.1.0 今日正式发布。该项目是一个 Kubernetes 原生的多 Agent 编排运行时，目标是让 LangChain、AutoGen、CrewAI、Semantic Kernel、Strands、Smolagents 等 6 大 AI Agent 框架能够通过 Google A2A 协议互相发现和调用。

### 核心特性

**1. 6 个 Kubernetes CRD**

- `Agent`：单个 AI Agent
- `AgentSet`：可水平扩展的 Agent 集群
- `Workflow`：声明式 DAG（v0.5+ 实装）
- `KnowledgeScope`：4 级 scope（行业/组织/团队/项目）
- `KnowledgeItem`：BM25 可检索的知识条目
- `Memory`：Agent 经验记录

**2. A2A 协议运行时**

- `Agent Card`（`.well-known/agent.json`）
- `Message / Task / Artifact / Streaming`
- JSON-RPC 2.0 over HTTP/SSE
- 内置 DNS 风格服务发现

**3. 单进程 Knowledge + Memory backend**

Knowledge Service 与 Memory Service 共享同一个 Python 进程（kopf operator + Starlette ASGI），简化部署、降低延迟。镜像 ~150 MB。

**4. 50ms fail-closed admission webhook**

所有 Memory / Knowledge 写入都经过 admission 校验，50ms 内未完成则拒绝。实测 p95 = 28ms。

**5. 生产级安全**

- restricted Pod Security Standards
- 非 root UID 1000 + 只读根文件系统
- NetworkPolicy 默认拒绝 + 显式放行
- 双 Role RBAC + opt-in cert-manager mTLS

### 关键数据

- **474/474 测试 PASS**（2 秒）
- **62 PR merged**（自 2026-07-08）
- **8 个 workspace member**
- **Apache 2.0**

### 上手

```bash
git clone https://github.com/superteam-cn/superteam-a2a
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest
```

5 分钟 kind demo 见 CONTRIBUTING.md。

### 仓库

- <https://github.com/superteam-cn/superteam-a2a>
- <https://github.com/superteam-cn/superteam-a2a/releases/tag/v0.1.0>

### 后续规划

- **v0.5**：6 框架适配器全部实装
- **v1.0**：Workflow CRD + 多集群联邦

---

## OSCHINA 发布要点

- **资讯型而非教程型**：突出发布事实 + 关键数字
- **标题简洁**：OSCHINA 用户更关注标题和首段
- **时间**：周二或周三上午 9:00-10:00
- **标签**：kubernetes, python, ai, 开源
