# SegmentFault：superteam-a2a v0.1.0

> **Submission target**: <https://segmentfault.com/write>
>
> **Status**: ⏳ pending (maintainer action)

---

## 文章标题

```
superteam-a2a v0.1.0 发布：基于 K8s 的多 Agent 编排平台，支持 Google A2A 协议
```

## 标签

- Kubernetes
- Python
- 开源
- AI

## 分类

后端 / 云计算 / AI

---

## 正文

### 项目背景

随着 LangChain、AutoGen、CrewAI 等 AI Agent 框架的成熟，单 Agent 执行已经不再是难题。但当业务进入「多 Agent 协作」阶段 —— 规划 Agent 委派任务、研究 Agent 检索资料、编码 Agent 生成代码、审查 Agent 把关质量 —— 开发者面临的痛点越来越清晰：

- 框架之间没有标准通信协议
- 缺少 K8s 原生支持（Deployment vs StatefulSet？）
- 没有服务发现、admission 控制、共享记忆

**superteam-a2a** 是为了填补这块空白而生的开源项目 —— 一个 Kubernetes 原生的多 Agent 编排运行时。

### 核心架构

```
┌─────────────────────────────────────────┐
│           kubectl / Helm                │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────▼─────────┐
        │  AgentSet CRD     │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────────────────┐
        │  kopf operator (Python)       │
        │  + Starlette ASGI (JSON-RPC)  │
        │  ───────────────────────────  │
        │  Knowledge Service            │
        │  Memory Service               │
        │  (单进程, D 方案)              │
        └─────────┬─────────────────────┘
                  │
        ┌─────────▼─────────┐
        │  K8s API / etcd   │
        └───────────────────┘
```

### 关键技术决策

#### 决策 1：单进程 backend

Knowledge Service + Memory Service **共享一个 Python 进程**（[ADR-0006](https://github.com/superteam-cn/superteam-a2a/blob/main/docs/adr/0006-memory-transport.md)）。

| 方案 | 评估 |
|---|---|
| HTTP loopback | ❌ 每次 +50ms |
| 共享 mmap | ❌ 脆弱 |
| 双 Pod + Redis | ❌ 一致性复杂 |
| **单进程** | ✅ 简单可调 |

代价：镜像 ~150 MB。收益：单 Deployment、单 RBAC、单健康检查。

#### 决策 2：50ms fail-closed admission

所有 Memory / Knowledge 写入都经过 admission webhook 校验，50ms 内必须完成，否则拒绝（fail-closed）。

实测 p95 = **28ms**。

#### 决策 3：6 CRD 而非单一 CRD

将 Agent / AgentSet / Workflow / KnowledgeScope / KnowledgeItem / Memory 拆为 6 个 CRD，符合 K8s「小而专」的设计哲学。

### 6 周实施数据

| 指标 | 数值 |
|---|---|
| 测试 | 474/474 PASS |
| PR merged | 62 |
| Python 代码 | ~30,000 行（8 个 workspace member） |
| License | Apache 2.0 |
| CI workflows | 5（lint / type-check / test / CodeQL / dependabot） |

### 上手指南

```bash
git clone https://github.com/superteam-cn/superteam-a2a
cd superteam-a2a
uv sync --all-packages --all-extras
uv run pytest  # 474 tests in ~2s

# 部署到 kind
kind create cluster --name superteam-a2a-dev
docker buildx build -t superteam-a2a/hello-agent:dev services/hello-agent/
kind load docker-image superteam-a2a/hello-agent:dev --name superteam-a2a-dev
helm install hello-agent helm/hello-agent/

kubectl get agentsets
kubectl port-forward svc/hello-agent 8080:8080 &
curl http://localhost:8080/.well-known/agent.json | jq
```

完整文档：<https://superteam-cn.github.io/superteam-a2a/>

### v0.1.0 还差什么

| 缺失项 | 计划 |
|---|---|
| LangChain / AutoGen / CrewAI 适配器 | v0.5 |
| Workflow CRD（声明式 DAG） | v1.0 |
| 多集群联邦 | v1.0+ |

### 加入

- **仓库**：<https://github.com/superteam-cn/superteam-a2a>
- **贡献**：<https://github.com/superteam-cn/superteam-a2a/blob/main/CONTRIBUTING.md>
- **Issue**：<https://github.com/superteam-cn/superteam-a2a/issues>

---

## SegmentFault 发布要点

- **正文偏技术**：减少营销语言，多贴代码
- **配图**：架构图 + kubectl 输出 + benchmark 数据
- **标签**：4 个标签即可（不要堆 10 个）
- **评论互动**：SegmentFault 评论质量高，认真回答每个问题
- **时间**：周三或周四上午发布
