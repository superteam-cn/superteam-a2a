# ADR-0003: Memory 持久化记忆设计（Memory CRD + MemoryReconciler + 5 维可见性矩阵）

> **本 ADR 详细定义 v0.1 持久化记忆能力的全部设计**：Memory CRD 字段、5 维可见性矩阵（4 作用域 × agent-private 正交）、MemoryReconciler 的 decay/reinforce 算法、`a2a.recordMemory` / `a2a.queryMemory` 方法字段、与 KnowledgeItem 的边界约束。
>
> 本 ADR 在 [ADR-0002](0002-knowledge-management-design.md) 之后落地，**严格遵守 ADR-0002 已锁定的字段约束**（≤15 spec 字段、visibility 三选一不含 public-readable、admission 双向互斥规则）。
>
> **2026-07-24 实现栈说明**：本 ADR 的 Memory 字段、可见性矩阵与生命周期公式继续有效；Go struct / Controller 实现假设已由 [ADR-0005](0005-python-first-technology-stack.md) supersede，改由 Pydantic/Kopf/Python 实现。

---

## 状态

| 字段 | 值 |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-23 |
| **Deciders** | 项目发起人（CoderZhangfujiang） |
| **Reviewers** | 项目发起人（依据宪法 14.5 MVP 例外，单点评审） |
| **Supersedes** | 无 |
| **Superseded by** | [ADR-0005](0005-python-first-technology-stack.md)（仅 Go/实现栈条款；Memory 语义继续有效） |
| **Related** | [ADR-0001](0001-v1-scope-statement.md)（v1 范围 ✅）、[ADR-0002](0002-knowledge-management-design.md)（知识管理设计 ✅）、[ADR-0004](0004-v01-scope-extension-knowledge-and-memory.md)（v0.1 范围 ✅） |

---

## 背景（Context）

### 用户决策回顾（2026-07-23 锁定）

依据项目持久化 Memory `session-2026-07-23-knowledge-and-memory-decisions` 的 5 个关键决策中的 #3、#4：

3. **Memory 完整 5 维可见性** —— industry / organization / team / project 四级 + agent-private 正交
4. **Memory 全部进 v0.1** —— 不拆分 v0.1-core / v0.1-full

### 决策必要性

Memory 是与 Knowledge 互补的能力：
- **Knowledge** 是"人写的"（显性文档、runbook、API spec）
- **Memory** 是"Agent 写的"（任务执行中学到的经验、教训、模式）

没有 Memory，Agent 每次启动都从零开始；有了 Memory，Agent 团队可以**跨任务、跨会话**复用经验。Memory 是项目核心差异化能力之一。

### ADR-0002 已锁定的约束（本 ADR 必须遵守）

依据 [ADR-0002 §6.3](0002-knowledge-management-design.md) 边界判定规则：

- ✅ Memory `agentRef.Kind` 必须 == `ServiceAccount` —— User/Group 一律拒绝
- ✅ KnowledgeItem `ownerRef.Kind` ∈ {User, Group} —— ServiceAccount 一律拒绝
- ✅ Memory 写入时若引用 KnowledgeItem，必须校验存在
- ❌ 禁止 Agent 通过 `recordMemory` 写"看起来像 KnowledgeItem"的结构（schema 强校验）

依据 [ADR-0002 §3.2](0002-knowledge-management-design.md) visibility 枚举：

- Memory visibility 仅可使用其中 **3 个**：`scope-only` / `scope-and-children` / `agent-private`
- **不包含** `public-readable`（因为 Agent 生成的内容不能"全集群公开"）

### 关键术语区分（重申）

| 概念 | 来源 | 生命周期 | 可见性 |
|---|---|---|---|
| **KnowledgeItem** | 人工撰写 | 版本控制 + 显式废弃 | 4 级 + 4 个 visibility（含 public-readable） |
| **Memory**（本 ADR） | Agent 生成 | confidence + decay + reinforce | 5 维矩阵（4 作用域 × agent-private） |
| **会话上下文** | Agent 内部 | 单次会话 | 单 Agent 私有，**不进入持久化** |

---

## 决策（Decision）

### 决策 1：1 个 CRD + 1 个 Controller + 2 个 A2A method

#### 1.1 CRD + Controller 总览

| 资源 | API 版本 | 职责 |
|---|---|---|
| `Memory` | v1alpha1 | Agent 生成的持久化记忆单元 |
| `MemoryReconciler` | Controller | 自动 decay + 强化协调（**不**作为 Agent 暴露） |

**A2A method**：`a2a.recordMemory` / `a2a.queryMemory`

**特殊 Agent**：**无** —— Memory 是基础设施能力，**不**通过 Card-driven Agent 暴露（与 Knowledge Service 不同）

**理由**：
- Knowledge 是"按需查询"语义（Agent 主动去查）→ 需要 search/list 接口 → Card-driven Service 合理
- Memory 是"自然沉淀"语义（Agent 任务结束后自动写）→ 需要最小 API 表面 → 直接走 A2A method 即可
- MemoryReconciler 是后台 controller，不需要"被调用"，只需"被触发"

#### 1.2 不在 v0.1 范围（Out-of-Scope）

- ❌ 自动化 scope-up（v0.1 仅 reconcile 计算 score，不生成 KnowledgePromotionRequest）
- ❌ Memory 分支 / 快照（v0.1 覆盖更新，不保留历史版本）
- ❌ Memory 与 Vector DB 集成（v0.1 用 etcd + 简单字段索引，v0.5+ 再评估）
- ❌ 跨 cluster 联邦 Memory（v0.1 单 cluster，v1.0+ 范畴）
- ❌ Memory 加密静态存储（v0.1 明文 etcd，依赖 etcd 加密；v0.5+ 评估 per-Memory 加密）
- ❌ Memory 内容审核 / 敏感词过滤（v0.1 由 Agent 自身负责，v0.5+ 引入 policy CRD）

### 决策 2：Memory CRD 详细设计

#### 2.1 设计目标

- 显式建模"Agent 生成的经验"（不是文档）
- 强制挂载 KnowledgeScope（无 scope = 不允许，与 ADR-0002 一致）
- 强制 5 维可见性矩阵（4 scope × agent-private）
- 强制 lifecycle 字段（confidence + decay + reinforce）
- admission webhook 双向互斥（与 KnowledgeItem 区分）
- ≤15 spec 字段（ADR-0004 防过度设计约束）

#### 2.2 Spec 字段

```go
// Memory CRD spec
type MemorySpec struct {
    // ScopeRef 挂载的 KnowledgeScope 引用（必填）
    // +kubebuilder:validation:Required
    ScopeRef ScopeReference `json:"scopeRef"`

    // AgentRef 创建/拥有本 Memory 的 Agent（必填，ServiceAccount kind）
    // admission webhook 强制：Kind == "ServiceAccount"
    // +kubebuilder:validation:Required
    AgentRef AgentReference `json:"agentRef"`

    // Content 记忆内容（结构化 KV，非 Markdown）
    // 键值对集合，避免与 KnowledgeItem 的 body 混淆
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:MinProperties=1
    // +kubebuilder:validation:MaxProperties=20
    Content map[string]string `json:"content"`

    // Summary 简短描述（必填，用于人工浏览 / list）
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:MinLength=1
    // +kubebuilder:validation:MaxLength=256
    Summary string `json:"summary"`

    // Confidence 当前置信度（0.0 - 1.0）
    // 由 MemoryReconciler 自动 decay；recordMemory 可手动 reinforce
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:Minimum=0
    // +kubebuilder:validation:Maximum=1
    Confidence float64 `json:"confidence"`

    // DecayDays 衰减周期（天）
    // confidence 按 exp(-elapsed/decayDays) 衰减
    // 默认 30，<=0 表示不衰减
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:Minimum=0
    // +kubebuilder:validation:Maximum=3650
    DecayDays int32 `json:"decayDays"`

    // ReinforcedCount 强化次数（monotonically increasing）
    // 每次 a2a.recordMemory 命中同 memoryKey 时 +1
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:Minimum=0
    ReinforcedCount int32 `json:"reinforcedCount"`

    // Visibility 可见性（5 维矩阵实现）
    // 枚举：scope-only / scope-and-children / agent-private
    // 注意：**不包含** public-readable（与 ADR-0002 区分）
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:Enum=scope-only;scope-and-children;agent-private
    Visibility MemoryVisibility `json:"visibility"`

    // MemoryKey 去重键（可选，用于 reinforce 命中）
    // 同 (memoryKey, scopeRef, agentRef) 三元组视为同一记忆
    // +kubebuilder:validation:MaxLength=128
    MemoryKey string `json:"memoryKey,omitempty"`

    // SourceKnowledgeRef 引用的 KnowledgeItem（可选）
    // 当 Memory 是从某 KnowledgeItem 衍生时填写，建立可追溯链
    // +optional
    SourceKnowledgeRef *ItemReference `json:"sourceKnowledgeRef,omitempty"`

    // Tags 标签（可选，用于 list/filter）
    // +optional
    // +kubebuilder:validation:MaxItems=20
    Tags []string `json:"tags,omitempty"`
}

type AgentReference struct {
    // Name ServiceAccount 名（同 namespace 内）
    Name string `json:"name"`
    // Namespace ServiceAccount 所在 namespace（可选，默认同 Memory 所在 ns）
    // +optional
    Namespace string `json:"namespace,omitempty"`
}

type MemoryVisibility string
const (
    // MemoryVisibilityScopeOnly 仅当前作用域可见
    MemoryVisibilityScopeOnly MemoryVisibility = "scope-only"

    // MemoryVisibilityScopeAndChildren 当前作用域 + 所有子作用域可见
    MemoryVisibilityScopeAndChildren MemoryVisibility = "scope-and-children"

    // MemoryVisibilityAgentPrivate 仅 owner agent 可见（5 维矩阵的 agent-private 维度）
    MemoryVisibilityAgentPrivate MemoryVisibility = "agent-private"
)
```

**字段数：12 个（Spec）**（ADR-0004 约束 ≤15，达标，距上限 3）

#### 2.3 Status 字段

```go
type MemoryStatus struct {
    // Phase: Active | Decaying | Promotable | Expired | Error
    // Active: confidence >= 0.5
    // Decaying: 0.1 <= confidence < 0.5
    // Promotable: confidence >= 0.85 && reinforcedCount >= 5（v0.1 仅标记，v0.5+ 触发 PromotionRequest）
    // Expired: confidence < 0.1（自动删除标记）
    Phase MemoryPhase `json:"phase"`

    // Message 人类可读状态
    Message string `json:"message,omitempty"`

    // Conditions 标准 K8s conditions
    Conditions []metav1.Condition `json:"conditions,omitempty"`

    // LastDecayedAt 上次自动衰减时间
    LastDecayedAt *metav1.Time `json:"lastDecayedAt,omitempty"`

    // LastReinforcedAt 上次强化时间
    LastReinforcedAt *metav1.Time `json:"lastReinforcedAt,omitempty"`

    // EffectiveConfidence 当前有效置信度（含 decay）
    // 由 MemoryReconciler 每次 reconcile 时更新
    EffectiveConfidence float64 `json:"effectiveConfidence"`

    // EligibleForPromotion 是否符合 scope-up 条件
    // v0.1：仅计算并填充 status 字段，不触发实际 PromotionRequest
    // v0.5+：本字段为 true 时自动生成 KnowledgePromotionRequest CRD
    EligibleForPromotion bool `json:"eligibleForPromotion"`

    // ObservedGeneration
    ObservedGeneration int64 `json:"observedGeneration"`
}
```

#### 2.4 admission 校验规则（与 ADR-0002 双向互斥）

- ✅ `spec.agentRef.Kind` 必须 == `ServiceAccount`（来自 admission webhook 强制约束）

> **实现说明**：CRD 字段类型是 `AgentReference`（仅 Name + Namespace），`Kind` 由 schema 硬编码为 "ServiceAccount"。admission webhook 额外校验 SA 存在。

- ✅ `spec.agentRef.Name` 必须存在于其 `namespace`
- ✅ `spec.scopeRef` 必须存在（对应 KnowledgeScope CRD 实例存在）
- ✅ `spec.sourceKnowledgeRef` 若填写，KnowledgeItem 必须存在且 `scopeRef` == `spec.scopeRef`
- ✅ `spec.content` 必须非空（≥1 key-value pair）
- ✅ `spec.memoryKey` 若填写，**三元组** `(memoryKey, scopeRef, agentRef)` 在 cluster 内应唯一
- ❌ 禁止 `visibility == agent-private` 与 `agentRef == nil` 同时出现（强制 owner）
- ❌ 禁止 `decayDays > 3650`（防异常值）

### 决策 3：5 维可见性矩阵（4 作用域 × agent-private 正交）

#### 3.1 矩阵定义

Memory 可见性 = 4 级作用域继承 × agent-private 正交维度。

**4 级作用域继承**（继承自 [ADR-0002 §2.4](0002-knowledge-management-design.md) 4 级继承算法）：
- Memory 的 `scopeRef` 决定"主体可见范围"
- 子作用域成员可见父作用域 Memory（仅当 `visibility ∈ {scope-only, scope-and-children}`）
- agent-private 维度**短路**继承（不参与继承链）

**agent-private 正交维度**：
- `visibility == agent-private` 时，**仅 owner agent（agentRef）可见**
- 与 `scopeRef` 无关 —— 即使在 industry scope，agent-private 也仅 owner 可见

#### 3.2 可见性矩阵表

| visibility \ scope | industry | organization | team | project |
|---|---|---|---|---|
| `scope-only` | 仅 industry scope | 仅 org scope | 仅 team scope | 仅 project scope |
| `scope-and-children`（默认） | industry + 所有 org/team/project | org + 所有子 team/project | team + 所有子 project | 仅 project |
| `agent-private` | **仅 owner agent**（无视 scope） | **仅 owner agent** | **仅 owner agent** | **仅 owner agent** |

#### 3.3 可见性过滤算法

```python
def is_memory_visible_to(memory: Memory, caller_agent: str, caller_scope_chain: List[str]) -> bool:
    """判断 caller 是否可见 memory。"""
    # 规则 1：agent-private 短路
    if memory.spec.visibility == "agent-private":
        return memory.spec.agentRef.name == caller_agent

    # 规则 2：scope 继承判断
    # scope-and-children: memory.scope 在 caller 继承链上
    # scope-only: memory.scope == caller 当前 scope
    if memory.spec.visibility == "scope-only":
        return memory.spec.scopeRef.name == caller_scope_chain[-1]

    if memory.spec.visibility == "scope-and-children":
        return memory.spec.scopeRef.name in caller_scope_chain

    return False


def query_memory(scope: str, caller_agent: str, filters: dict) -> List[Memory]:
    """查询所有 caller 可见的 Memory。"""
    caller_chain = resolve_effective_scopes(scope)  # 来自 ADR-0002 §2.4
    all_memories = list_all_memories(filters)
    return [m for m in all_memories if is_memory_visible_to(m, caller_agent, caller_chain)]
```

### 决策 4：MemoryReconciler 算法

#### 4.1 控制器职责

MemoryReconciler 是**后台 Controller**（不是 Agent，不是用户直接调用对象），负责：

1. **每 N 秒 reconcile 所有 Memory**（N 默认 60s）
2. **计算 effectiveConfidence**（应用 decay 公式）
3. **更新 phase**（Active / Decaying / Promotable / Expired）
4. **触发 GC**：confidence < 0.1 → phase=Expired → reconcile 后删除
5. **填充 `eligibleForPromotion`**（v0.1 仅填充字段，不触发 PromotionRequest）

#### 4.2 decay 算法

```python
def apply_decay(memory: Memory, now: datetime) -> float:
    """计算当前 effectiveConfidence。"""
    if memory.spec.decayDays <= 0:
        return memory.spec.confidence  # 不衰减

    last_update = max(
        memory.status.lastDecayedAt or memory.metadata.creationTimestamp,
        memory.status.lastReinforcedAt or memory.metadata.creationTimestamp,
    )
    elapsed_days = (now - last_update).total_seconds() / 86400.0
    decay_rate = elapsed_days / memory.spec.decayDays
    effective = memory.spec.confidence * math.exp(-decay_rate)
    return max(0.0, min(1.0, effective))
```

**示例**：
- 初始 confidence = 1.0，decayDays = 30
- 30 天后：effective = 1.0 × exp(-1) ≈ 0.368
- 60 天后：effective = 1.0 × exp(-2) ≈ 0.135
- 90 天后：effective = 1.0 × exp(-3) ≈ 0.050 → < 0.1 → phase=Expired → GC

#### 4.3 reinforce 算法（响应 a2a.recordMemory 命中）

```python
def apply_reinforce(memory: Memory) -> Memory:
    """强化：confidence += 0.05（上限 1.0），reinforcedCount += 1。"""
    new_confidence = min(1.0, memory.spec.confidence + 0.05)
    new_count = memory.spec.reinforcedCount + 1
    now = metav1.Now()
    memory.spec.confidence = new_confidence
    memory.spec.reinforcedCount = new_count
    memory.status.lastReinforcedAt = &now
    memory.status.effectiveConfidence = new_confidence  # 重置衰减起点
    memory.status.lastDecayedAt = &now  # decay 重启
    return memory
```

**去重键逻辑**：
- `a2a.recordMemory` 请求带 `memoryKey` 时：
  - 查询同 `(memoryKey, scopeRef, agentRef)` 已存在 Memory → 命中 reinforce
  - 不存在 → 创建新 Memory
- `memoryKey` 为空时：每次 recordMemory 创建新 Memory（无 reinforce 概念）

#### 4.4 scope-up 触发条件（v0.1 仅计算，v0.5+ 实际触发）

```python
def is_eligible_for_promotion(memory: Memory) -> bool:
    """判断是否符合 scope-up 条件。"""
    if memory.spec.visibility != "scope-and-children":
        return False  # scope-only / agent-private 不参与 promote

    effective = memory.status.effectiveConfidence
    count = memory.spec.reinforcedCount

    return effective >= 0.85 and count >= 5
```

**v0.1 行为**：
- ✅ MemoryReconciler 计算并填充 `status.eligibleForPromotion = true/false`
- ❌ **不**生成 KnowledgePromotionRequest（v0.5+）
- ❌ **不**自动修改 scopeRef（v0.5+）

**v0.5+ 行为（不在 v0.1 范围）**：
- 增加 `KnowledgePromotionRequest` CRD
- Operator watch Memory `eligibleForPromotion == true` → 生成 PromotionRequest
- 审批后 Memory 的 scopeRef 被升级（保留 version 链）

#### 4.5 GC 策略

- `effectiveConfidence < 0.1` → phase=Expired
- phase=Expired 持续 7 天 → reconcile 删除（依赖 K8s finalizer 防误删）
- finalizer `memory.superteam-a2a.io/cleanup`：删除时清理关联资源（无，因为 Memory 不引用其他资源）

### 决策 5：A2A method 详细字段

#### 5.1 `a2a.recordMemory`

**Request**（A2A Message `data` 部分）：
```json
{
  "scope": "team-payments-platform",
  "content": {
    "pattern": "credit-card-refund-fail-retry-3x",
    "outcome": "success-after-2nd-retry",
    "duration": "8.5s"
  },
  "summary": "信用卡退款失败时，重试 3 次成功率最高（实测 80%）",
  "memoryKey": "credit-card-refund-retry-strategy",
  "visibility": "scope-and-children",
  "sourceKnowledgeRef": {
    "name": "refund-failure-handling",
    "scope": "team-payments-platform"
  },
  "tags": ["payments", "refund", "retry-strategy"]
}
```

**Response**：
```json
{
  "memoryId": "team-payments-platform/credit-card-refund-retry-strategy",
  "confidence": 0.55,
  "decayDays": 30,
  "phase": "Active",
  "reinforcedCount": 0,
  "effectiveConfidence": 0.55,
  "createdAt": "2026-07-23T15:30:00Z"
}
```

**错误码**：
- `MEMORY_SCOPE_NOT_FOUND` (404)
- `MEMORY_INVALID_CONTENT` (400, content 为空或 > 20 keys)
- `MEMORY_FORBIDDEN` (403, caller SA 不在允许列表)
- `MEMORY_RATE_LIMIT` (429, 同一 SA 每分钟最多 60 次 recordMemory)
- `MEMORY_INTERNAL_ERROR` (500)

#### 5.2 `a2a.queryMemory`

**Request**：
```json
{
  "scope": "team-payments-platform",
  "confidenceMin": 0.3,
  "memoryKeyPattern": "credit-card-*",
  "tagFilter": ["refund"],
  "maxResults": 20
}
```

**Response**：
```json
{
  "memories": [
    {
      "name": "team-payments-platform/credit-card-refund-retry-strategy",
      "scope": "team-payments-platform",
      "agent": "refund-analyzer",
      "summary": "信用卡退款失败时，重试 3 次成功率最高",
      "content": {
        "pattern": "credit-card-refund-fail-retry-3x",
        "outcome": "success-after-2nd-retry"
      },
      "confidence": 0.55,
      "effectiveConfidence": 0.42,
      "reinforcedCount": 2,
      "visibility": "scope-and-children",
      "phase": "Active",
      "age": "5d",
      "tags": ["payments", "refund"],
      "sourceKnowledgeRef": {
        "name": "refund-failure-handling"
      }
    }
  ],
  "totalCount": 7
}
```

**错误码**：
- `MEMORY_SCOPE_NOT_FOUND` (404)
- `MEMORY_FORBIDDEN` (403, agent-private Memory 不属于 caller)
- `MEMORY_QUERY_TOO_BROAD` (400, scope=industry + 无 tag/confidence 过滤，被拒以防全集群扫描)
- `MEMORY_INTERNAL_ERROR` (500)

### 决策 6：与 ADR-0002 的边界（admission webhook 实现）

#### 6.1 双向互斥规则（admission webhook 强制）

| 字段 | KnowledgeItem | Memory |
|---|---|---|
| `ownerRef.Kind` / `agentRef.Kind` | ∈ {User, Group} | == ServiceAccount |
| `visibility` 枚举 | scope-only / scope-and-children / public-readable / agent-private | scope-only / scope-and-children / agent-private |
| `body` / `content` 格式 | Markdown（≤64KB） | 结构化 KV（≤20 keys） |
| 生命周期管理 | 显式 `phase` + 手动版本 | confidence + decay + reinforce |
| CRUD 入口 | `kubectl apply` + A2A `query/get` | A2A `record/query` only（**不能** kubectl apply Memory） |

#### 6.2 admission webhook 实现

```python
def validate_knowledge_item(ki: KnowledgeItem, operation: str) -> List[str]:
    """KnowledgeItem validation。"""
    errors = []
    if ki.spec.ownerRef.kind not in ["User", "Group"]:
        errors.append("KnowledgeItem.ownerRef.kind must be User or Group (not ServiceAccount)")
    if ki.spec.visibility == "agent-private" and ki.spec.ownerRef.kind != "ServiceAccount":
        # Note: KnowledgeItem.agent-private requires SA, but ServiceAccount is rejected above
        # This is intentionally inconsistent — agent-private in Knowledge is reserved for future use
        # For v0.1, KnowledgeItem.visibility CANNOT be agent-private
        errors.append("KnowledgeItem.visibility cannot be agent-private in v0.1")
    if ki.spec.visibility == "public-readable":
        scope = get_scope(ki.spec.scopeRef.name)
        if scope.spec.level != "industry":
            errors.append("KnowledgeItem.visibility == public-readable requires scope.level == industry")
    return errors


def validate_memory(m: Memory, operation: str) -> List[str]:
    """Memory validation。"""
    errors = []
    # agentRef.kind 由 schema 硬编码为 ServiceAccount，无需校验
    # 但校验 SA 存在
    sa = get_service_account(m.spec.agentRef.name, m.spec.agentRef.namespace)
    if sa is None:
        errors.append(f"Memory.agentRef SA not found: {m.spec.agentRef.name}")
    # scope 存在
    if get_scope(m.spec.scopeRef.name) is None:
        errors.append(f"Memory.scopeRef not found: {m.spec.scopeRef.name}")
    # sourceKnowledgeRef 校验
    if m.spec.sourceKnowledgeRef:
        ki = get_knowledge_item(m.spec.sourceKnowledgeRef.name)
        if ki is None:
            errors.append(f"Memory.sourceKnowledgeRef KI not found: {m.spec.sourceKnowledgeRef.name}")
        if ki and ki.spec.scopeRef.name != m.spec.scopeRef.name:
            errors.append("Memory.sourceKnowledgeRef.scope must match Memory.scopeRef")
    # visibility 校验
    if m.spec.visibility == "agent-private" and not m.spec.agentRef.name:
        errors.append("Memory.visibility == agent-private requires agentRef.name")
    return errors
```

### 决策 7：v0.1 算法简化（关键约束）

#### 7.1 不引入的复杂度

- ❌ **不**实现"记忆压缩"（v0.5+ 范畴）
- ❌ **不**实现"记忆链接 / 图"（v0.5+ Knowledge Graph 范畴）
- ❌ **不**实现"记忆继承"（v0.1 scope 已通过 KnowledgeScope 继承，无需 Memory 自身再做）
- ❌ **不**实现"记忆分享"（v0.1 严格 5 维矩阵，v0.5+ 引入"信任链"分享）
- ❌ **不**实现"自动 reconcile 周期自适应"（v0.1 固定 60s）

#### 7.2 必须实现的最小集

- ✅ decay 公式：`confidence × exp(-elapsed/decayDays)`
- ✅ reinforce：`confidence += 0.05`，`reinforcedCount += 1`
- ✅ 5 维矩阵过滤（决策 3）
- ✅ admission 互斥校验（决策 6）
- ✅ effectiveConfidence 字段更新
- ✅ phase 状态机（Active / Decaying / Promotable / Expired）
- ✅ `eligibleForPromotion` 字段填充（不触发）
- ✅ GC：confidence < 0.1 → 删除（带 finalizer）

### 决策 8：容量与性能约束

- **单集群 Memory 上限**：50,000 条（超出拒绝创建）
- **etcd 占用估算**：50K × 平均 1KB = ~50MB（远低于 etcd 默认 8GB）
- **queryMemory P95 性能**：≤ 300ms @ 50K items
- **recordMemory P95 性能**：≤ 200ms（含 admission + reconcile 触发）
- **MemoryReconciler reconcile 周期**：60s（默认）
- **批量 reconcile**：单次 reconcile 最多处理 1,000 个 Memory，避免 API server 过载

### 决策 9：验收标准（v0.1 Memory 必须满足才发 Phase 3）

#### 9.1 功能完整性

- [ ] Memory CRD schema 注册成功（v1alpha1，12 spec 字段）
- [ ] MemoryReconciler 部署成功（Deployment，leader election）
- [ ] `a2a.recordMemory` 实现 + 命中 memoryKey 时正确 reinforce
- [ ] `a2a.queryMemory` 实现 + 5 维可见性矩阵过滤
- [ ] 12 spec 字段枚举全部校验（decayDays ≤ 3650, confidence 0-1 等）
- [ ] admission webhook 双向互斥规则生效（KI.OwnerRef.Kind vs Memory.AgentRef.Kind）
- [ ] effectiveConfidence 自动更新（通过 fake clock 测试）

#### 9.2 质量门禁（宪法 9.x）

- [ ] 单元测试覆盖率 ≥ **80%**（Memory Controller + A2A method）
- [ ] decay 算法数学正确性单测（exp 公式 + 边界值）
- [ ] reinforce 算法单测（含上限 1.0）
- [ ] 5 维矩阵过滤单测（4 scope × 3 visibility = 12 种组合）
- [ ] admission webhook 单测（KI ↔ Memory 互斥 + 边界）
- [ ] E2E 测试（kind）：Agent 写 Memory → 查询 → 命中 → reinforce → decay
- [ ] 性能测试：50K Memory recordMemory P95 ≤ 200ms

#### 9.3 安全门禁（宪法 6.x）

- [ ] Memory access 强制 mTLS（与其他 A2A method 一致）
- [ ] agent-private 强制 owner 检查（caller SA ≠ owner → 403）
- [ ] admission webhook 强制 Memory.agentRef SA 必须存在
- [ ] RBAC：`recordMemory` 仅允许 `create` on `memory` 资源；不暴露 `delete`
- [ ] Memory 内容大小限制（content ≤ 20 keys, summary ≤ 256 chars）

#### 9.4 可观测性门禁（宪法 7.x）

- [ ] Prometheus 指标（强制）：
  - `superteam_memory_record_total{scope, agent, result}`
  - `superteam_memory_query_total{scope, visibility, result}`
  - `superteam_memory_decay_total{phase_from, phase_to}`
  - `superteam_memory_reconcile_duration_seconds` (histogram)
  - `superteam_memory_eligible_for_promotion_total`
  - `superteam_memory_total{scope, phase}`
- [ ] 结构化日志：所有 record/query 记录 trace_id / caller_sa / scope / memory_key
- [ ] K8s Events：Memory 创建 / reinforce / decay 阶段变化 / GC 删除

#### 9.5 文档门禁（宪法 10.x）

- [ ] Memory CRD 完整 API 文档（自动生成 + 示例）
- [ ] 用户指南：`docs/guides/memory-quickstart.md`（Agent 写 memory → 查询 → reinforce 演示）
- [ ] 算法说明：`docs/design/memory-algorithm.md`（decay 数学公式 + 5 维矩阵示意）
- [ ] Runbook：`docs/runbooks/memory-faq.md`（decay 太快 / reinforce 不生效 / 5 维矩阵调试）

---

## 后果（Consequences）

### 正面

- ✅ **宪法一致**：与宪法 2.5（显式优于隐式）、2.6（向后兼容）、2.9（记忆可追溯 —— **本 ADR 是 2.9 的核心实现**）、6.x（安全）、7.x（可观测）全部对齐
- ✅ **字段数合规**：12 spec 字段，远低于 ≤15 约束（ADR-0004 防过度设计）
- ✅ **算法简单**：decay/reinforce 公式明确，单人 2h/天 在 4 周 Phase 3 内可完成
- ✅ **与 ADR-0002 边界清晰**：admission webhook 双向互斥规则消除歧义
- ✅ **5 维矩阵完整**：4 scope × agent-private 正交实现，支持用户决策 #3
- ✅ **可演进**：v0.1 仅计算 `eligibleForPromotion`，v0.5+ 触发 KnowledgePromotionRequest 即可
- ✅ **不暴露为 Agent**：Memory 是基础设施能力，不增加用户 Agent 数量（保持 2 个特殊 Agent）

### 负面

- ⚠️ **decay 公式过于简单**：exp 衰减可能在某些场景不符合实际（如某些记忆应长期保留）
- ⚠️ **reinforce 上限 1.0 可能过严**：高频使用的记忆不应 confidence=1.0 封顶
- ⚠️ **agent-private 误用风险**：caller SA 误配可能导致"看不到自己写的 memory"
- ⚠️ **无自动化 scope-up**：v0.1 优秀 Memory 需用户手动 `kubectl patch`，体验欠佳
- ⚠️ **queryMemory 无全文搜索**：仅支持 memoryKeyPattern + tagFilter + confidenceMin，不支持自由文本
- ⚠️ **MemoryReconciler 单点风险**：Deployment 1 副本（v0.5+ 水平扩展）
- ⚠️ **Memory 与 Knowledge 概念相似度高**：用户可能混淆（需文档澄清）

### 缓解措施

| 风险 | 缓解 |
|---|---|
| decay 公式过简 | 文档明示 + decayDays 可调（≤3650），用户可针对业务调整 |
| reinforce 上限 | 文档明示 + v0.5+ 评估改为 `confidence += 0.05 × (1 - confidence)` |
| agent-private 误用 | admission webhook 强制 agentRef.name 非空 |
| 无自动 scope-up | Phase 3 完成后即启动 ADR 起草 KnowledgePromotionRequest（v0.5） |
| 无全文搜索 | Phase 3 README 显式说明 + v0.5+ 评估 BM25 / Vector DB |
| Reconciler 单点 | Phase 3 完成后 Helm values 支持 replicas（默认 1） |
| 概念混淆 | 在 ADR-0002 §6.2 边界表已存在；本 ADR §6.1 双向互斥表重复强调 |

---

## 备选方案（Alternatives）

### A. Memory CRD + MemoryReconciler + 5 维矩阵 + 简化算法（**采纳**）

如本决策所述。

**采纳理由：**
- 与用户决策一致（5 维可见性 + Memory 全部进 v0.1）
- 严格遵守 ADR-0002 已锁定的字段约束（≤15 字段、visibility 三选一、admission 互斥）
- 单人 2h/天 在 4 周 Phase 3 内可完成
- 算法简单（exp decay + 加法 reinforce），无需外部依赖

### B. Memory 用 PostgreSQL + Vector DB 后端（**未采纳**）

**未采纳理由：**
- 引入外部依赖（PG / Chroma 部署运维）
- 违反 v0.1 简化原则（"无外部依赖"）
- Memory 与 KnowledgeItem 数据模型不一致，增加复杂度
- v0.5+ 可插拔设计（不在 v0.1 范围）

### C. Memory 沿用 Knowledge Service 暴露为 Agent（**未采纳**）

**未采纳理由：**
- Memory 是"自然沉淀"语义，Agent 主动查询场景少
- 增加一个特殊 Agent 数量（违反 ADR-0004 "2 个特殊 Agent" 锁定）
- Controller-only 设计更内聚
- A2A method 暴露仍走 Card-driven Agent 的方式（详见决策 1.1）

### D. Memory 暴露完整 CRUD（create / read / update / delete）（**未采纳**）

**未采纳理由：**
- Memory 是"自然沉淀"，不需要 update 语义（reinforce 即覆盖更新）
- delete 由 GC 自动管理，无需用户主动删除
- A2A method 仅 `record` / `query` 两个，最小 API 表面
- 避免"用户主动删除导致 lifecycle 混乱"

### E. Memory 启用 Agent-to-Agent 直传（**未采纳**）

**未采纳理由：**
- 违反宪法 2.1（协议优先）
- 违反宪法 2.9（记忆可追溯 —— 绕过 A2A 无法 trace）
- Memory 必须通过 recordMemory 走 MemoryReconciler reconcile 才能产生 status

### F. Memory 引入"信任链"分享（agent A 分享给 agent B）（**未采纳**）

**未采纳理由：**
- v0.1 严格 5 维矩阵（用户决策 #3）
- "信任链"是 v0.5+ 范畴
- 引入新概念会破坏 v0.1 简单性

---

## 决策依据（Rationale）

本决策选择 A（CRD + Reconciler + 5 维矩阵 + 简化算法），依据如下：

1. **用户决策优先**：用户已锁定"5 维可见性 + Memory 全部进 v0.1 + 二者兼具"，任何偏离都违反用户决策
2. **ADR-0002 约束继承**：本 ADR 必须遵守 ADR-0002 §6.3 admission 互斥规则 + §3.2 visibility 约束
3. **宪法 2.9 落地**：本 ADR 是宪法 v0.2.0 新增条款"记忆可追溯"的核心实现
4. **算法简单可验证**：exp 衰减 + 加法强化，数学明确，单测覆盖容易
5. **工作量可控**：1 个 CRD + 1 个 Controller + 2 个 method = ~4 周 Phase 3 工作量，符合预算
6. **可演进**：eligibleForPromotion 字段为 v0.5 自动化 scope-up 留接口；算法参数（decayDays, reinforce 增量）v0.5+ 可调

---

## 实施（Implementation）

### 立即（本会话内）

- [x] 本 ADR 落地（`docs/adr/0003-memory-design.md`）
- [x] ADR-0002 已落地（前置依赖）✅
- [ ] L1 Architecture 更新（+1 CRD + 1 Controller + 2 method）—— **依赖本 ADR 完成后**

### Phase 3 周期（第 15-18 周）

按 [ROADMAP.md](../../ROADMAP.md) 实施：

1. Memory CRD schema 定义（Go struct + 自动生成 CRD YAML）
2. MemoryReconciler（Deployment + RBAC + leader election + finalizer）
3. admission webhook（双向互斥 + Memory 专属校验）
4. A2A method 实现：`a2a.recordMemory` / `a2a.queryMemory`
5. decay 算法实现（exp 公式 + 边界处理）
6. reinforce 算法实现（memoryKey 去重 + 增量更新）
7. 5 维矩阵过滤实现（继承自 ADR-0002 §2.4 算法）
8. eligibleForPromotion 字段填充（v0.1 仅计算）
9. GC 实现（confidence < 0.1 → phase=Expired → 7 天后删除）
10. E2E 测试（kind + Agent 写 Memory → 查询 → 命中 → reinforce → decay）
11. 指标 + 日志 + Events 埋点
12. 文档（API 文档 + 用户指南 + 算法说明 + Runbook）

### v0.5.0 周期（非 v0.1 范围）

- `KnowledgePromotionRequest` CRD（自动化 scope-up）
- Memory 水平扩展（replicas 默认 ≥2）
- 评估 Vector DB / BM25 后端集成
- "信任链"分享评估

### v1.0.0 周期（非 v0.1 范围）

- Memory 字段集冻结（v1alpha1 → v1beta1 → v1）
- 6 framework adapters 集成 memory write skill
- 完整 Conformance 套件

---

## 参考（References）

- [CONSTITUTION.md](../../CONSTITUTION.md) v0.2.0
  - **第二条 9（记忆可追溯）—— 本 ADR 的宪法依据**
  - 第二条 1（协议优先 —— Memory 必须走 A2A）
  - 第二条 5（显式优于隐式）
  - 第二条 6（向后兼容是承诺）
  - 第三条 1（分层严格）
  - 第六条（安全规范）
  - 第七条（可观测性）
  - 第九条（测试策略）
  - 第十一条（版本管理 + Semver）
  - 第十四条 4（强门禁：本 ADR 属其后置）
  - 第十五条（质量第一性）
- [ADR-0001](0001-v1-scope-statement.md) v1 范围声明
- [ADR-0002](0002-knowledge-management-design.md) 知识管理设计（**前置依赖**，本 ADR 必须遵守其约束）
- [ADR-0004](0004-v01-scope-extension-knowledge-and-memory.md) v0.1 范围重定
- [ROADMAP.md](../../ROADMAP.md) Phase 3 任务清单
- [L1-architecture.md](../design/L1-architecture.md)（待更新：+1 CRD + 1 Controller + 2 method）
- [L1-system-spec.md](../spec/L1-system-spec.md)（待更新：CRD 字段 + 错误码 + 状态机）

---

## 签署

本 ADR 由项目发起人于 **2026-07-23** 批准生效（依据宪法 14.5 MVP 例外，单点评审）。