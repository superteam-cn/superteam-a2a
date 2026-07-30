# ADR-0006：L3-5 + L3-6 跨 container transport 选型（OPEN-MEMORY-001 关闭）

> **架构级 ADR**：本 ADR 关闭 L3-5 §6.2 + L3-6 §6.1 + §13.5 OPEN-MEMORY-001 共同标注的 L4 前唯一架构门禁——跨 container transport 选型。仅 supersede L3-5 v0.2.0 §6.2 + L3-6 v0.2.0 §6.1 + §6.3 + §9.10 中"同 Pod 内两个独立 Python 进程通过 in-process call 通信"的设计假设；wire contract（5+5 简化 schema / 12 字段完整版 / 12 MEMORY_* 错误码 / 4 纯函数 / 60s @kopf.timer / Leader Election / 4 级 scope / 5 维 visibility）与 L2-4 v0.2.0 Spec 业务语义继续有效。
>
> **执行门禁**：本 ADR 与宪法 v0.5.0 通过后，才能更新 L3-5 v0.2.1 + L3-6 v0.2.1；v0.2.1 评审通过后，才能修改 Helm values 共享 chart；Helm 通过后，才能进入 L4 实施层（packages/knowledge + packages/memory）。L4 开工前必须完成 kind spike 验证 transport 选型。

---

## §0 元数据

| 字段 | 值 |
|---|---|
| **编号** | ADR-0006 |
| **标题** | L3-5 + L3-6 跨 container transport 选型（OPEN-MEMORY-001 关闭） |
| **状态** | 🟡 **v0.1-draft 候选**（待 2026-07-30 #68 评审） |
| **日期** | 2026-07-30 |
| **决策者** | 项目发起人（CoderZhangfujiang） |
| **关联会话** | #68 |
| **上游约束** | L3-5 v0.2.0 §6.2 line 1488-1577 + L3-6 v0.2.0 §6.1+§6.4+§9.10+§13.5 + L1 v0.2.0 + 宪法 v0.5.0 |
| **supersede** | L3-5 v0.2.0 §6.2 共享 Deployment in-process function reference 假设 + L3-6 v0.2.0 §6.1+§6.3+§9.10 双进程拓扑（仅部署形态，不变更 wire contract） |
| **Superseded by** | 无 |
| **Related** | ADR-0003（Memory 设计）、ADR-0004（v0.1 范围）、ADR-0005（Python-first） |
| **Constitution** | v0.5.0（§3.4 分层严格 / §6 安全准入 / §7 可观测脱敏 / §9.7 质量门禁 / §13.1 设计先于实施） |

---

## §1 背景与问题

### 1.1 当前双进程架构与 in-process call 假设

L3-5 Knowledge Service 与 L3-6 Memory backend 共享同 Pod 内两个独立 Python 进程：

- **Container 1**：knowledge-service（port 8080 · Uvicorn 单 worker · A2A endpoint）
- **Container 2**：memory-backend（port 8081 · Uvicorn 单 worker · 60s @kopf.timer + Leader Election + 4 纯函数）

L3-5 v0.2.0 §6.2 line 1488-1577 与 L3-6 v0.2.0 §6.1 同时声明：

> **进程间通信机制**：**同一 Pod 内两个独立 Python 进程，通过共享内存或 in-process call 通信**（**不通过 HTTP**）。
>
> 方式 1（推荐）：Python in-process call（同 Pod 内直接 `import` + 调用 `async def` 函数）
> 优势：零网络延迟 + 零序列化开销 + 强类型（Protocol 约束）
> 限制：仅同 Pod 内有效；Container 1 与 Container 2 通过共享卷（emptyDir）共享 Python module 路径

**关键矛盾**：两个独立 Python 进程不能共享对象内存（`import` 不传递运行时对象）。`emptyDir` 仅可挂载文件系统 artifact，无法跨进程边界共享内存对象。

L3-6 v0.2.0 §6.1 已显式承认：

> 禁止 HTTP loopback。共享 emptyDir 只提供模块 artifact；两个独立 Python 进程不能共享对象内存，因此实际跨 container transport 若无法 direct import，必须在 L4 spike 前将部署修正为同进程或使用明确 IPC，并保持本 Protocol 语义。

**OPEN-MEMORY-001**（L3-6 §13.5 + L3-5 §13）共同标注 L4 前唯一架构门禁，必须先决定。

### 1.2 4 A2A method 跨进程调用需求

L3-5 的 4 A2A method handler 中，2 个委托 L3-6：

| L3-5 method | 委托目标 | L3-6 入口 |
|---|---|---|
| `a2a.recordMemory` | L3-6 §4 record_memory_async handler | `MemoryBackendInProcessService.record_memory_async` |
| `a2a.queryMemory` | L3-6 §4 query_memory_async handler | `MemoryBackendInProcessService.query_memory_async` |

跨进程调用必须保持以下契约（来自 L3-5 §6.2 line 1547-1550 + L3-6 §6.1 三条运行时规则）：

1. **`async def` 全异步**：所有 L3-6 export 函数为 `async def`；L3-5 调用必须 `await`
2. **异常透传**：L3-6 抛出的 `A2AError` / `AdmissionTimeoutError` 直接传播；L3-5 不 catch 并改 error code
3. **immutable 传递**：L3-5 传入 frozen/deep-copy snapshot；L3-6 不保存 caller mutable reference

### 1.3 12 MEMORY_* 错误码 wire 镜像

L3-6 v0.2.0 §8.1 + L3-5 v0.2.0 §8.2 共同锁定 12 个 MEMORY_* 错误码权威名（与 L2-4 v0.2.0 §9.1 零漂移）：

- `MEMORY_SCOPE_NOT_FOUND` -32101 / `MEMORY_INVALID_CONTENT` -32102 / `MEMORY_FORBIDDEN` -32103
- `MEMORY_QUERY_TOO_BROAD` -32104 / `MEMORY_ADMISSION_TIMEOUT` -32105 / `MEMORY_INTERNAL_ERROR` -32106
- `MEMORY_BACKEND_UNAVAILABLE` -32107 / `MEMORY_LOCK_CONTENTION` -32108 / `MEMORY_NOT_FOUND` -32109
- `MEMORY_ALREADY_EXISTS` -32110 / `MEMORY_INVALID_NAMESPACE` -32111 / `MEMORY_RATE_LIMITED` -32112

跨进程 transport 必须支持封闭错误码集合的透传（不可丢失 code/message/cause）。

### 1.4 50ms admission deadline 约束

L3-6 v0.2.0 §6.4 line 922-937 显式约束：

```python
monotonic_deadline = context.clock.monotonic() + 0.050
try:
    await asyncio.wait_for(
        admission_validator.validate_memory(memory),
        timeout=max(0.0, monotonic_deadline - context.clock.monotonic()),
    )
except asyncio.TimeoutError as exc:
    raise AdmissionTimeoutError("MEMORY_ADMISSION_TIMEOUT") from exc
```

**50ms admission deadline** 是硬门禁：跨进程 transport 必须满足 p99 < 50ms（最好 < 5ms 富余）。

### 1.5 5 维 visibility 矩阵 + 4 级 scope 继承

L3-5 v0.2.0 §3.3 + L3-6 v0.2.0 §3.3 共同锁定 5 维 visibility（scope-only / scope-and-children / agent-private / min_confidence / ttl_seconds）+ 4 级 scope（industry / organization / team / project）。跨进程 transport 必须保证 immutable snapshot 正确序列化。

### 1.6 in-process function reference 契约 3 规则

来自 L3-5 §6.2 line 1547-1550 + L3-6 §6.1：

1. **immutable 传递**：frozen/deep-copy snapshot；不保存 mutable reference
2. **显式失败**：全链 `async def` + exception propagation；不允许 None 表示 failure
3. **单调时钟**：deadline/timeout/idempotency window 使用同一 `Clock.monotonic()`

---

## §2 候选方案（5 方案对比，不允许排除）

### 2.1 决策矩阵（5 方案 × 7 维度）

| 维度 \ 方案 | A. UDS（AF_UNIX） | B. 共享 IPC namespace | C. 共享 mmap | D. 同进程 | E. HTTP loopback |
|---|---|---|---|---|---|
| **python anyio/asyncio 支持** | anyio.connect_unix / asyncio.open_unix_connection | anyio.process / asyncio 子进程 API | mmap module（同步，需异步 wrapper） | N/A（直接 import） | httpx.AsyncClient / aiohttp |
| **k8s 兼容** | emptyDir volume（medium: Memory） | Pod `shareProcessNamespace: true` | emptyDir volume（medium: Memory） | N/A（无 k8s 边界） | 已禁止（L3-6 §6.1） |
| **延迟（typical / p99）** | ~10μs / ~100μs | ~5μs / ~50μs（信号/pipe） | ~5μs / ~50μs（无锁读） | <1μs / <5μs（直接函数调用） | ~500μs / ~2ms（loopback HTTP） |
| **复杂度** | 中（socket 路径管理 + 文件权限） | 高（需修改 Helm shareProcessNamespace） | 高（序列化 + 内存布局 + 锁） | 极低（直接 import） | 低（已部署） |
| **运维** | 中（重启清空 socket 文件） | 中（Pod 级 namespace 共享） | 中（重启清空 + 内存布局验证） | 极低（无额外配置） | 中（端口占用） |
| **安全** | 高（文件权限 + 路径隔离） | 中（共享 namespace 风险） | 中（需锁 + 校验） | 最高（无 IPC 边界） | 低（loopback 易被旁路） |
| **12 错误码透传** | 中（需自定义序列化） | 高（直接 Exception 对象） | 低（仅 bytes 序列化） | 最高（直接 Exception 类） | 中（JSON 序列化 + code 镜像） |

### 2.2 候选方案详细描述

#### A. UDS（AF_UNIX）

**描述**：通过 Unix Domain Socket（AF_UNIX）跨 container 通信。Container 1 与 Container 2 共享 `emptyDir` volume 挂载到 `/var/run/superteam/`，memory-backend 在 `/var/run/superteam/memory.sock` 监听 SOCK_STREAM，knowledge-service 通过 `asyncio.open_unix_connection('/var/run/superteam/memory.sock')` 连接。

**实施要点**：
- Helm values：emptyDir volumeMount `/var/run/superteam` + env `IPC_SOCKET=/var/run/superteam/memory.sock`
- 自定义二进制协议或 MessagePack（12 MEMORY_* 错误码 + immutable DTO）
- 文件权限 0660 + 共享 UID/GID 65532:65532
- Socket 路径冲突保护（启动时 atomic mkdir + O_EXCL）

**优点**：
- 保留 L3-5 + L3-6 双进程架构独立性（Helm 9.10 双 container 拓扑不变）
- 未来扩展 sidecar / DaemonSet 容易
- ~10μs 延迟远低于 50ms admission deadline
- 文件权限 + 路径隔离提供安全边界

**缺点**：
- 需自定义序列化协议（12 MEMORY_* + Memory + QueryMemoryRequest DTO）
- 共享 volume 增加 Helm 复杂度（已在 L3-6 v0.2.0 §9.10 HELM-DEPLOY-002 预留）
- socket 文件需 cleanup（Pod restart）

#### B. 共享 runtime / IPC namespace

**描述**：Pod-level `shareProcessNamespace: true` + 共享内存 / 信号 / pipe / FIFO。Container 1 与 Container 2 在同一 Linux PID namespace 但仍为独立进程。

**实施要点**：
- Helm values：`spec.shareProcessNamespace: true` + 共享 `/dev/shm` 或自建 FIFO
- 通过 signal / pipe / shared memory 通信
- 需重新设计 IPC 协议（pipe message length + bytes）

**优点**：
- 最低延迟（~5μs，in-process file descriptor 传递）
- K8s native（无需 emptyDir）

**缺点**：
- ⚠️ **shareProcessNamespace 安全风险**：Container 1 与 Container 2 共享 PID namespace，可能导致信号注入（Container 1 可向 Container 2 PID 1 发送 SIGTERM）
- ⚠️ 违反最小权限原则（Constitution §6）
- Helm 改动大（Pod spec 顶层字段）
- 跨 namespace 调试复杂

#### C. 共享 mmap

**描述**：通过 mmap 共享内存文件（emptyDir volume 挂载 `/dev/shm/superteam-memory`）通信。Container 1 与 Container 2 共享同一 mmap region，通过 lock-free ring buffer 或 mutex 同步。

**实施要点**：
- Helm values：emptyDir volume（medium: Memory sizeLimit: 64Mi）+ mountPath `/dev/shm`
- 自研 mmap protocol（header + ring buffer + message body）
- 需文件锁（fcntl）或内存屏障同步

**优点**：
- 低延迟（~5μs，零拷贝）
- 大数据量吞吐高

**缺点**：
- ⚠️ 复杂度极高（内存布局、序列化、锁、内存屏障）
- 12 错误码 + immutable DTO 序列化困难
- 调试困难（无 wire trace）
- 重启一致性挑战（mmap region 状态恢复）

#### D. 同进程

**描述**：取消 L3-5 + L3-6 双进程架构，合并为单 Python 进程。`services/knowledge-service/` 与 `services/memory-backend/` 合并为 `services/knowledge-memory/`，单 Uvicorn worker 同时暴露 8080 (A2A) + 8081 (admin/healthz) 端口。

**实施要点**：
- Helm values：删除双 container deployment；合并为单 container
- uv workspace：合并 `packages/knowledge/` + `packages/memory/` 为 `packages/knowledge-memory/`
- ADR-0005 §13.1 uv workspace 布局调整
- L1 v0.2.0 §4.3 C-7 调整（合并 C-6 + C-7 为新 C-6）

**优点**：
- ✅ **消除 IPC 边界**：in-process function reference 契约直接落地（直接 `import` + 调用）
- ✅ **零序列化开销**：12 MEMORY_* 错误码直接 Exception 类传递
- ✅ **最低延迟**：<1μs（直接函数调用），50ms deadline 零风险
- ✅ **架构最简**：无需 Helm volumeMount / socket 路径管理
- ✅ **Card-driven 单实例天然适合**（L3-6 §1.1 已确认 replicaCount=1）
- ✅ **uv workspace 简化**：28 + 28 文件级契约合并
- ✅ **可观测性简单**：25 个指标同进程聚合，无跨进程 trace 关联复杂度

**缺点**：
- ⚠️ 失去 L3-5 + L3-6 双进程独立性（未来扩展 sidecar / DaemonSet 需重新设计）
- ⚠️ 单进程内存上限（10K Memory CRD 内存估算 < 100MB，python:3.12-slim RSS ~80MB；仍在 256Mi limit 内）
- ⚠️ v0.5+ 水平扩展需重新设计（但 v0.1 单实例已锁定，OPEN-MEMORY-002 已推迟到 v0.5+）

#### E. HTTP loopback

**描述**：通过 `httpx.AsyncClient` 调用 `http://127.0.0.1:8081/memory` 跨 container 通信。

**优点**：
- 实施最简单（httpx + JSON-RPC over HTTP）
- 与 L3-2 §6 A2AClient 同模式

**缺点**（关键）：
- ❌ **L3-5 v0.2.0 §6.2 + L3-6 v0.2.0 §6.1 明确禁止**
- ❌ 违反 in-process function reference 契约
- ❌ 50ms admission deadline 风险（HTTP loopback p99 ~2ms，富余度不足）
- ❌ 12 错误码 JSON 序列化复杂度（需 code 镜像 + 双倍映射）
- ❌ 端口占用 + 进程边界绕过的安全风险

### 2.3 禁止方案

**E（HTTP loopback）**：已被 L3-5 v0.2.0 §6.2 + L3-6 v0.2.0 §6.1 明确禁止，不再考虑。

---

## §3 决策建议

### 3.1 主推荐：D（同进程）

**理由 1：消除 IPC 边界**
L3-5 v0.2.0 §6.2 + L3-6 v0.2.0 §6.1 描述的"in-process function reference 契约"假设两个进程可共享对象内存，实际上 Python 跨进程不共享运行时对象。D 方案直接消除该矛盾：`import` + `async def record_memory_async(...)` 直接调用，契约与实现 100% 一致。

**理由 2：架构最简**
- 无 Helm volumeMount（删除 L3-6 §9.10 IPC_SOCKET env + emptyDir volumeMount）
- 无 socket 路径管理
- 无跨进程序列化协议
- 无 12 错误码 wire 镜像（直接 Exception 类传递）

**理由 3：Card-driven 单实例天然适合**
L3-6 v0.2.0 §1.1 已锁定：
- replicaCount=1（OPEN-MEMORY-002 推迟到 v0.5+）
- Card-driven 内部 service 暴露（0 A2A method）
- 单 Uvicorn worker + port 8081 cluster-internal

合并为单进程后，L3-6 的 60s @kopf.timer + Leader Election + 4 纯函数 + Clock Protocol + BM25 启动期全量重建全部在同一进程内运行，Card-driven 单实例语义保持不变。

**理由 4：50ms admission deadline 零风险**
- D 方案延迟 <1μs（直接函数调用），远低于 50ms deadline
- A 方案 ~10μs + 序列化开销仍 <1ms，富余 49ms
- E 方案（已禁止）~2ms p99，富余不足

**理由 5：uv workspace 简化**
ADR-0005 §13.1 定义的 `packages/knowledge/` + `services/knowledge-service/` + `packages/memory/` + `services/memory-backend/` 合并为：

```text
packages/
  knowledge-memory/                                   # 合并 packages/knowledge + packages/memory
    src/supteam_a2a/knowledge_memory/
services/
  knowledge-memory-service/                           # 合并 services/knowledge-service + services/memory-backend
    src/supteam_a2a/knowledge_memory_service/
    helm/templates/                                   # 单 container deployment
```

### 3.2 次推荐：A（UDS）

**理由 1：保留 L3-5 + L3-6 双进程独立性**
Helm values 已在 L3-6 v0.2.0 §9.10 HELM-DEPLOY-002 预留 IPC volume + env 三项；A 方案只需激活该配置即可。

**理由 2：未来扩展 sidecar / DaemonSet 容易**
L3-5 + L3-6 双进程架构允许 memory-backend 未来独立扩展为 DaemonSet（多 Pod 共享 BM25 index），无需重新设计。

**理由 3：UDS 性能足够**
~10μs p99 + 序列化 ~50μs 总开销 < 1ms，远低于 50ms admission deadline。

**代价**：
- Helm values 保留 emptyDir volumeMount `/var/run/superteam` + env `IPC_SOCKET=/var/run/superteam/memory.sock`（已在 v0.2.0 §9.10 预留）
- 需自定义二进制协议（MessagePack 或 Cap'n Proto）
- 12 MEMORY_* 错误码需序列化映射（code + name + cause chain）
- L3-5 调用方需实现 retry + reconnect + cleanup

### 3.3 不推荐

**B（共享 IPC namespace）**：
- ⚠️ **安全风险**：shareProcessNamespace 共享 PID namespace，可能导致信号注入
- ⚠️ 违反 Constitution §6 最小权限原则
- ⚠️ Helm 改动大（Pod spec 顶层字段）

**C（共享 mmap）**：
- ⚠️ 复杂度极高（内存布局、序列化、锁、内存屏障）
- ⚠️ 调试困难（无 wire trace）
- ⚠️ 重启一致性挑战
- ⚠️ 收益不抵成本（A 方案已足够）

**E（HTTP loopback）**：
- ❌ 已被 L3-5 §6.2 + L3-6 §6.1 明确禁止

---

## §4 决策结论（草案 · 待用户审批）

### 4.1 草案结论

**主推荐 D（同进程 · 取消 L3-5 + L3-6 双进程，合并为单 Python 进程）；备选 A（UDS）**

### 4.2 架构图对比

**当前双进程架构（L3-5 v0.2.0 §6.2 + L3-6 v0.2.0 §6.3）**：

```text
Knowledge Service Pod · replicaCount=1
├─ Container 1: knowledge-service :8080 (Uvicorn single worker)
│  ├─ A2A server (queryKnowledge/getKnowledgeItem/recordMemory/queryMemory)
│  ├─ admission_validator (@kopf.validation · 50ms fail-closed)
│  └─ MemoryBackendInProcessService client (assumed in-process call)
└─ Container 2: memory-backend :8081 (Uvicorn single worker)
   ├─ @kopf.timer(interval=60.0, id="memory-reconciler")
   ├─ Leader Election Lease (30s grace + 3x renew fail)
   ├─ 4 pure functions (apply_decay/reinforce/gc/promotion)
   ├─ Clock Protocol + RealClock + FakeClock
   ├─ BM25 启动期全量重建 + watch 增量
   └─ MemoryBackend Protocol export (assumed in-process)
```

**D 方案单进程架构（ADR-0006 推荐）**：

```text
Knowledge-Memory Service Pod · replicaCount=1
└─ Container 1: knowledge-memory-service :8080 (Uvicorn single worker)
   ├─ A2A server (queryKnowledge/getKnowledgeItem/recordMemory/queryMemory)
   ├─ admission_validator (@kopf.validation · 50ms fail-closed)
   ├─ @kopf.timer(interval=60.0, id="memory-reconciler")
   ├─ Leader Election Lease (30s grace + 3x renew fail)
   ├─ 4 pure functions (apply_decay/reinforce/gc/promotion)
   ├─ Clock Protocol + RealClock + FakeClock
   ├─ BM25 启动期全量重建 + watch 增量
   └─ MemoryBackend Protocol (直接 import + 调用)
       ↓
       in-process function reference (直接 async def 调用 · 0 序列化 · 0 网络延迟)
```

**A 方案 UDS 双进程架构（备选）**：

```text
Knowledge Service Pod · replicaCount=1
├─ Container 1: knowledge-service :8080
│  ├─ A2A server + admission_validator
│  └─ UDS client → /var/run/superteam/memory.sock
└─ Container 2: memory-backend :8081
   ├─ UDS server → /var/run/superteam/memory.sock (SOCK_STREAM)
   ├─ @kopf.timer + Leader Election + 4 pure functions + BM25
   └─ MemoryBackend Protocol export (via UDS + MessagePack 序列化)
       ↓
       IPC socket (AF_UNIX · ~10μs · MessagePack 序列化)
```

### 4.3 对 L3-5 / L3-6 / L1 / Helm / L4 实施的影响

| 影响文件 | 变更类型 | 变更内容 | 关联章节 |
|---|---|---|---|
| **L3-5 v0.2.1** | 微同步 | 删除 §6.2 line 1488-1577 共享 Deployment 协调点，改为 §6.X 单进程架构描述（直接 import memory_backend.record_memory_async） | §6.2 line 1488-1577 → §6.X |
| **L3-6 v0.2.1** | 微同步 | 删除 §6.1+§6.3 双进程拓扑，§9.10 简化为单 container 部署（删除 IPC_SOCKET env + emptyDir volumeMount） | §6.1 / §6.3 / §9.10 |
| **L3-6 §8** | 保持不变 | 12 MEMORY_* 错误码权威名 100% wire contract 不变（直接 Exception 类传递） | §8.1 |
| **L3-6 §9.5** | 保持不变 | read/write 双 Role 与 admissionregistration/authn/authz 扩展不变 | §9.5 |
| **L3-6 §9.7** | 保持不变 | PrometheusRule 8 alert + Memory × 2 告警规则不变（单进程 /metrics 聚合 25 个指标） | §9.7 |
| **L1 v0.2.0** | 微同步 | §4.3 C-6 + C-7 合并为新 C-6（Knowledge+Memory 合并） | §4.3 |
| **Helm values** | 删除 | `IPC_SOCKET` env + `ipc` emptyDir volumeMount 删除；`MEMORY_RECONCILER_INTERVAL` 改为进程内常量 | L3-6 §9.10 |
| **Helm deployment** | 重构 | 双 container 合并为单 container（knowledge-memory-service）；port 8080 对外 + port 8081 cluster-internal | L3-6 §9.2 + §9.10 |
| **uv workspace** | 重构 | ADR-0005 §13.1 packages/knowledge + services/knowledge-service + packages/memory + services/memory-backend 合并为 packages/knowledge-memory + services/knowledge-memory-service | ADR-0005 §13.1 |
| **L4 实施层** | 命名调整 | `packages/knowledge/` + `packages/memory/` → `packages/knowledge-memory/`；`services/knowledge-service/` + `services/memory-backend/` → `services/knowledge-memory-service/` | L4 实施 |

### 4.4 后续动作（D 方案确认后）

1. **D 方案用户审批**（OPEN-ADR-0006-001）
2. **L3-5 v0.2.1 微同步**：删除 §6.2 共享 Deployment 协调点
3. **L3-6 v0.2.1 微同步**：删除 §6.1+§6.3 双进程拓扑，简化 §9.10 Helm values
4. **L1 v0.2.0 微同步**：§4.3 C-6 + C-7 合并
5. **Helm values 调整**：删除 IPC volume + env 三项
6. **uv workspace 重构**（ADR-0005 §13.1 调整）
7. **L4 kind spike 验证**：单进程 deployment + 60s timer + Leader Election + 50ms admission deadline + 12 错误码透传
8. **OPEN-MEMORY-001 关闭**

---

## §5 不在 ADR-0006 范围

### 5.1 不变更 wire contract

- **CRD 字段**：Memory CRD 12 字段完整版（L3-6 §3.1 + L2-4 §3.4）+ Memory 5+5 简化 schema（L3-5 §3.3）wire 名/required/default/enum/format 全部不变
- **A2A method**：6 个 method（sendMessage/getTask/queryKnowledge/getKnowledgeItem/recordMemory/queryMemory）envelope 不变
- **错误码**：12 MEMORY_* 错误码（-32101~-32112）权威名不变
- **4 级 scope**：industry/organization/team/project 不变
- **5 维 visibility**：scope-only/scope-and-children/agent-private/min_confidence/ttl_seconds 不变

### 5.2 不变更 5 项关键不变量

L3-6 v0.2.0 §1.2 + L3-5 v0.2.0 §1.2 共同锁定的 5 项关键不变量全部保持：

1. **同 Pod 第二进程** → 单进程（L3-6 §1.2 #1 变为"同 Pod 单进程"，但 v0.1 单实例语义保持）
2. **60s @kopf.timer 周期不变**
3. **共享 Deployment** → 单 container Deployment（语义保持：同 Pod 单实例）
4. **4 纯函数数学永久不变**
5. **wire contract 完全继承 L2-4 v0.2.0 Spec**

### 5.3 不变更宪法

- **Constitution §3.4 分层严格**：L3-5 + L3-6 同属业务层（L1 §3.5.3），合并为单进程不违反分层
- **Constitution §6 安全准入**：单进程不降低 mTLS / RBAC / admission / fail-closed 要求
- **Constitution §7 可观测脱敏**：单进程 25 指标聚合不变
- **Constitution §9.7 质量门禁**：kind spike + conformance + benchmark 门禁不变
- **Constitution §13.1 设计先于实施**：本 ADR 通过后才能进入 L4

---

## §6 开放问题

| ID | 问题 | 状态 | 决策窗口 |
|---|---|---|---|
| OPEN-ADR-0006-001 | D（合并单进程）vs A（UDS 双进程）最终决策 | 🟡 v0.1-draft | 用户审批（#68） |
| OPEN-ADR-0006-002 | D 方案下 packages/knowledge + packages/memory 合并命名（packages/knowledge-memory vs packages/knowledge_with_memory vs 其他） | 🟡 | D 方案确认后（#68.x） |
| OPEN-ADR-0006-003 | D 方案下 MemoryReconciler 进程位置（knowledge 进程内 vs memory 进程内 · D 方案下合并为同一进程，60s timer 进程位置归属） | 🟡 | D 方案确认后（#68.x） |
| OPEN-ADR-0006-004 | A 方案下 socket 路径命名（/var/run/superteam/memory.sock vs /run/superteam/memory.sock vs 其他） | 🟡 | A 方案确认后 |
| OPEN-ADR-0006-005 | 错误码 EVENT 传播（D 方案下 K8s Events 3 enum（MemoryDecayApplied/MemoryGCCleaned/MemoryPromotionEligible）+ L3-5 2 enum（MemoryConflictDetected/MemoryConflictResolved）合并/分离） | 🟡 | D 方案确认后（#68.x） |
| OPEN-ADR-0006-006 | D 方案下 BM25 索引共享 dict（与 L3-5 §4.2 bm25_index.search 共享存储 · 同步/锁策略） | 🟡 | L4 实施（OPEN-L3-5-004） |
| OPEN-ADR-0006-007 | D 方案下 _SCOPE_CACHE（4096/TTL60s · L3-5 §6.1 + L3-5-followup-4）单进程 LRU 实现 | 🟡 | L4 实施（OPEN-L3-5-003） |

---

## 文档元数据 M.1-M.6

### M.1 版本与状态

| 字段 | 值 |
|---|---|
| 版本 | **v0.1-draft 候选**（#68 · 2026-07-30） |
| 状态 | 🟡 待用户审批（OPEN-ADR-0006-001） |
| 上游约束 | L3-5 v0.2.0 §6.2 line 1488-1577 + L3-6 v0.2.0 §6.1+§6.3+§9.10+§13.5 + L1 v0.2.0 + 宪法 v0.5.0 |
| supersede | L3-5 §6.2 + L3-6 §6.1/§6.3/§9.10 双进程拓扑假设（仅部署形态） |
| wire contract | 12 MEMORY_* 错误码 / 12 字段完整版 / 4 纯函数 / 60s timer / Leader Election 不变 |

### M.2 落地记录

| 日期 / 会话 | 增量 | 结果 |
|---|---|---|
| 2026-07-29 #63.5 | L3-5 v0.2.0 §6.2 line 1488-1577 共享 Deployment 协调点 + in-process function reference 假设落地 | L3-5 上游就绪 |
| 2026-07-30 #66 | L3-6 v0.2.0 §6.1 三条运行时规则 + §6.3 拓扑 + §9.10 HELM-DEPLOY-002 IPC volume + env 三项预留 | L3-6 上游就绪 |
| 2026-07-30 #67 | L3-6 v0.2.0 独立评审通过 · OPEN-MEMORY-001 标注为 L4 前唯一架构门禁 | OPEN-MEMORY-001 显式登记 |
| **2026-07-30 #68** | **ADR-0006 v0.1-draft 候选稿：5 方案决策矩阵 + 主推荐 D + 次推荐 A + 影响表 9 文件 + 7 开放问题** | **候选稿提交评审** |

### M.3 配套引用

- L3-5 Knowledge Service v0.2.0：`docs/spec/L3-file-specs/L3-knowledge-service.md`（**关键引用** · §6.2 line 1488-1577 共享 Deployment 协调点 + §9.9 共享 Helm chart）
- L3-6 Memory backend v0.2.0：`docs/spec/L3-file-specs/L3-memory-backend.md`（**关键引用** · §6.1+§6.3+§9.10+§13.5 OPEN-MEMORY-001 + §1.2 关键不变量 #1/#3）
- L1 Architecture v0.2.0：`docs/design/L1-architecture.md` §3.5.3 + §4.3 C-7
- L1 Spec v0.2.0：`docs/spec/L1-system-spec.md` §5.2.3 Memory YAML 示例
- L2-4 Knowledge/Memory Spec v0.2.0：`docs/spec/L2-module-specs/L2-knowledge-memory.md`（CRD 12 字段 + 4 method + §9.1 12 MEMORY_* 错误码权威名）
- L2-4 Knowledge/Memory Design v0.2.0：`docs/design/L2-modules/L2-knowledge-memory.md`
- ADR-0003 Memory 设计：`docs/adr/0003-memory-design.md`
- ADR-0005 Python-first：`docs/adr/0005-python-first-technology-stack.md` §3.4 + §6.2 + §13.1
- ADR-0004 v0.1 范围：`docs/adr/0004-v01-scope-extension-knowledge-and-memory.md`
- Constitution v0.5.0：`CONSTITUTION.md`（§3.4 / §6 / §7 / §9.7 / §13.1）

### M.4 下次会话固定入口

1. **ADR-0006 用户审批**（OPEN-ADR-0006-001）：D 方案确认后，进入 v0.2 → Accepted
2. **L3-5 v0.2.1 微同步**：删除 §6.2 line 1488-1577 共享 Deployment 协调点，改为单进程架构描述
3. **L3-6 v0.2.1 微同步**：删除 §6.1+§6.3 双进程拓扑；§9.10 Helm values 删除 IPC volume + env 三项；保留 12 MEMORY_* 错误码 + §9.5 read/write 双 Role + §9.7 PrometheusRule
4. **L1 v0.2.0 微同步**：§4.3 C-6 + C-7 合并为新 C-6
5. **Helm values 调整**：单 container deployment
6. **uv workspace 重构**：ADR-0005 §13.1 布局调整（packages/knowledge-memory + services/knowledge-memory-service）
7. **L4 kind spike**：单进程 deployment + 60s timer + Leader Election + 50ms admission deadline + 12 错误码透传验证
8. **OPEN-MEMORY-001 关闭**

### M.5 关注项台账（v0.1-draft 候选 · 评审待补充）

| 编号 | 关注项 | 状态 | 解决位置 |
|---|---|---|---|
| ADR-0006-followup-1 | ADR-0006 用户审批（D vs A） | 🟡 | OPEN-ADR-0006-001 |
| ADR-0006-followup-2 | L3-5 v0.2.1 §6.2 微同步（删除共享 Deployment 协调点） | 🟡 | #68.x |
| ADR-0006-followup-3 | L3-6 v0.2.1 §6.1/§6.3/§9.10 微同步（删除双进程拓扑 + IPC 配置） | 🟡 | #68.x |
| ADR-0006-followup-4 | L1 v0.2.0 §4.3 微同步（C-6 + C-7 合并） | 🟡 | #68.x |
| ADR-0006-followup-5 | Helm values 调整（单 container deployment） | 🟡 | #68.x |
| ADR-0006-followup-6 | uv workspace 重构（ADR-0005 §13.1 调整） | 🟡 | #68.x |
| ADR-0006-followup-7 | L4 kind spike 验证（单进程 transport） | 🟡 | L4 实施 |

### M.6 文档元数据

- **创建日期**：2026-07-30 #68
- **最后更新**：2026-07-30 #68（v0.1-draft 候选）
- **下次更新**：用户审批后 v0.1 → Accepted；L3-5 v0.2.1 + L3-6 v0.2.1 + L1 v0.2.0 + Helm + uv workspace 微同步
- **依赖完整性**：上游 L3-5 v0.2.0 + L3-6 v0.2.0 + L1 v0.2.0 + 宪法 v0.5.0 全部就绪
- **下游影响**：L3-5 v0.2.1 + L3-6 v0.2.1 + L1 v0.2.0 + Helm values + uv workspace（ADR-0005 §13.1）+ L4 实施层（packages/knowledge-memory + services/knowledge-memory-service）+ OPEN-MEMORY-001 关闭

---

> **签署**：本 ADR-0006 v0.1-draft 候选稿由 #68 起草（Subagent 1 隔离模式 A 研究-写作分离）。依据 [L3-5 Knowledge Service v0.2.0 §6.2 line 1488-1577](../../spec/L3-file-specs/L3-knowledge-service.md)、[L3-6 Memory backend v0.2.0 §6.1+§6.3+§9.10+§13.5](../../spec/L3-file-specs/L3-memory-backend.md)、[L1 Architecture v0.2.0 §3.5.3 + §4.3 C-7](../../design/L1-architecture.md)、[ADR-0003 Memory 设计](../../adr/0003-memory-design.md)、[ADR-0005 Python-first §3.4 + §6.2 + §13.1](../../adr/0005-python-first-technology-stack.md) 与 Constitution v0.5.0 编写。**当前 v0.1-draft 候选稿已具备用户审批条件；批准后 L3-5 v0.2.1 + L3-6 v0.2.1 + L1 微同步 + Helm values 调整 + uv workspace 重构 + L4 kind spike 验证 + OPEN-MEMORY-001 关闭**。