# ADR-0002: 知识管理能力设计（KnowledgeScope / KnowledgeItem / Knowledge Service）

> **本 ADR 详细定义 v0.1 知识管理能力的全部设计**：CRD 字段、A2A method 字段、4 级作用域继承算法、Knowledge Service Agent Card、跨级共享机制、与 Memory 的边界。
>
> 本 ADR 在 ADR-0001（v1 范围）之后落地，**在 ADR-0003（Memory 设计）之前落地**——因为 Memory 需要引用 KnowledgeScope 与 KnowledgeItem 的字段（详见本 ADR §6 边界）。
>
> **2026-07-24 实现栈说明**：本 ADR 的 CRD、作用域、A2A method 与 Knowledge 语义继续有效；Go struct / 自动生成实现假设已由 [ADR-0005](0005-python-first-technology-stack.md) supersede，改由 Pydantic/Python 实现。

---

## 状态

| 字段 | 值 |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-23 |
| **Deciders** | 项目发起人（CoderZhangfujiang） |
| **Reviewers** | 项目发起人（依据宪法 14.5 MVP 例外，单点评审） |
| **Supersedes** | 无 |
| **Superseded by** | [ADR-0005](0005-python-first-technology-stack.md)（仅 Go/实现栈条款；Knowledge 语义继续有效） |
| **Related** | [ADR-0001](0001-v1-scope-statement.md)（v1 范围 ✅）、[ADR-0004](0004-v01-scope-extension-knowledge-and-memory.md)（v0.1 范围 ✅）、[ADR-0003](0003-memory-design.md)（Memory 设计，待写） |

---

## 背景（Context）

### 用户决策回顾（2026-07-23 锁定）

依据项目持久化 Memory `session-2026-07-23-knowledge-and-memory-decisions` 的 5 个关键决策：

1. **第 5 大基础能力 = 知识管理**（含持久化记忆）—— 在原 4 项之外新增
2. **知识管理 = 二者兼具（统一抽象）** —— runtime 知识 + 系统文档统一为 KnowledgeItem，`type` 字段区分
3. **Memory 完整 5 维可见性** —— industry / organization / team / project 四级 + agent-private 正交
4. **Memory 全部进 v0.1**
5. **v0.1 交付期 12 周 → 20 周**

### 决策必要性

知识管理是项目的**核心差异化能力**。若不在 v0.1 即落地完整设计：
- Agent 之间无法共享项目上下文（每次重启都从零开始）
- 显性文档（runbook / API spec / 架构图）没有统一存储
- 与 AutoGen / CrewAI 等"框架自带记忆"形成对比时缺乏壁垒

同时，**知识管理 ≠ Memory**——两者必须清晰分离，否则会出现"什么都是记忆"的设计混乱。

### 关键术语区分

| 概念 | 来源 | 生命周期 | 可见性 |
|---|---|---|---|
| **KnowledgeItem** | 人工撰写（人 / 工具） | 版本控制 + 显式废弃 | 4 级作用域 + 可选 agent-private |
| **Memory** | Agent 生成（任务执行） | confidence + decay + reinforce | 5 维矩阵（4 作用域 × agent-private） |
| **会话上下文** | Agent 内部（runtime） | 单次会话 / 单次任务 | 单 Agent 私有，**不进入持久化** |

---

## 决策（Decision）

### 决策 1：2 个 CRD + 1 个特殊 Agent + 2 个 A2A method

#### 1.1 CRD 总览

| CRD | API 版本 | 职责 |
|---|---|---|
| `KnowledgeScope` | v1alpha1 | 4 级作用域的命名空间 + 继承关系 |
| `KnowledgeItem` | v1alpha1 | 显性知识的最小单元（文档 / runbook / 模板 / etc.） |

**特殊 Agent**：`Knowledge Service`（Card-driven，无 framework adapter，CRD-driven）

**A2A method**：`a2a.queryKnowledge` / `a2a.getKnowledgeItem`

#### 1.2 不在 v0.1 范围（Out-of-Scope）

- ❌ Knowledge Graph / 知识图谱（推 v0.5+）
- ❌ 自动 scope-up（v0.1 手动 `kubectl patch`，v0.5+ 引入置信度阈值）
- ❌ Knowledge 版本分支 / merge（用 `version` 字段 + 显式废弃，不做 Git 化）
- ❌ Knowledge 全文搜索引擎（v0.1 用 K8s etcd 查询 + 内存倒排；v0.5+ 引入 Vector DB 可选）
- ❌ Knowledge 评论 / 协作（用 K8s audit log + GitOps 流程替代）
- ❌ Knowledge 与外部系统的 webhook 同步（v0.5+）

### 决策 2：KnowledgeScope CRD 详细设计

#### 2.1 设计目标

- 显式建模 4 级作用域（industry / organization / team / project）
- 支持父子引用 + 继承链验证
- 防止循环引用 + 防止孤儿
- 不假设实际 K8s namespace 1:1（允许一个 K8s namespace 内多个 scope）

#### 2.2 Spec 字段

```go
// KnowledgeScope CRD spec
type KnowledgeScopeSpec struct {
    // Level 是 4 级作用域的枚举（必填）
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:Enum=industry;organization;team;project
    Level ScopeLevel `json:"level"`

    // DisplayName 人类可读名（必填）
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:MinLength=1
    // +kubebuilder:validation:MaxLength=64
    DisplayName string `json:"displayName"`

    // Description 作用域说明（可选）
    // +kubebuilder:validation:MaxLength=512
    Description string `json:"description,omitempty"`

    // ParentRef 父作用域引用（可选，根作用域无父）
    // 必须满足：parent.level = current.level - 1（按枚举顺序）
    // +optional
    ParentRef *ScopeReference `json:"parentRef,omitempty"`

    // OwnerRef 负责人引用（必填，用于 audit + 权限）
    // +kubebuilder:validation:Required
    OwnerRef SubjectReference `json:"ownerRef"`

    // InheritRules 继承规则（可选，默认全继承）
    // 控制哪些 type 的 KnowledgeItem 从父作用域流向本作用域
    // +optional
    InheritRules *InheritRules `json:"inheritRules,omitempty"`

    // Labels 任意标签（可选，用于检索）
    // +optional
    Labels map[string]string `json:"labels,omitempty"`
}

type ScopeLevel string
const (
    ScopeLevelIndustry      ScopeLevel = "industry"
    ScopeLevelOrganization  ScopeLevel = "organization"
    ScopeLevelTeam          ScopeLevel = "team"
    ScopeLevelProject       ScopeLevel = "project"
)

type ScopeReference struct {
    // Name 引用的 KnowledgeScope 名（同 namespace 内）
    Name string `json:"name"`
}

type SubjectReference struct {
    // Kind: User | Group | ServiceAccount
    Kind string `json:"kind"`
    Name string `json:"name"`
}

type InheritRules struct {
    // IncludeTypes 白名单（仅这些 type 从父级继承），空 = 全部
    // +optional
    IncludeTypes []KnowledgeType `json:"includeTypes,omitempty"`

    // ExcludeTypes 黑名单（从父级继承时排除）
    // +optional
    ExcludeTypes []KnowledgeType `json:"excludeTypes,omitempty"`
}
```

**字段数：6 个（Spec）+ 3 个引用类型**（符合 ADR-0004 防过度设计约束）

#### 2.3 Status 字段

```go
type KnowledgeScopeStatus struct {
    // Phase: Pending | Active | Error | Deleting
    Phase ScopePhase `json:"phase"`

    // Message 人类可读状态描述
    Message string `json:"message,omitempty"`

    // Conditions 标准 K8s conditions
    Conditions []metav1.Condition `json:"conditions,omitempty"`

    // ItemCount 本作用域直接挂载的 KnowledgeItem 数（不含继承）
    ItemCount int32 `json:"itemCount"`

    // ChildScopes 直接子作用域数
    ChildScopes int32 `json:"childScopes"`

    // ObservedGeneration 用于 reconcile 幂等
    ObservedGeneration int64 `json:"observedGeneration"`
}
```

#### 2.4 4 级继承算法（伪代码）

```python
def resolve_effective_scopes(scope_name: str) -> List[str]:
    """返回从最顶层（industry）到当前 scope 的完整继承链。

    用于查询时，自动包含所有父作用域的可见 KnowledgeItem。
    """
    chain = []
    current = get_scope(scope_name)
    while current is not None:
        chain.insert(0, current.name)  # 从顶层往下排
        if current.spec.parentRef is None:
            break
        current = get_scope(current.spec.parentRef.name)
    return chain


def query_knowledge(scope_name: str, type_filter: List[str], tag_filter: List[str]) -> List[KnowledgeItem]:
    """查询时自动包含继承链上所有作用域的 KnowledgeItem。

    继承规则：
    - InheritRules.IncludeTypes 非空 → 仅继承这些 type
    - InheritRules.ExcludeTypes 非空 → 排除这些 type
    - 都为空 → 全部继承
    - 继承冲突（同名 type 不同内容）→ KnowledgeItem.version 大的优先
    """
    effective_scopes = resolve_effective_scopes(scope_name)
    results = []

    for s in effective_scopes:
        scope = get_scope(s)
        items = list_knowledge_items_in_scope(s, type_filter, tag_filter)
        for item in items:
            # 应用继承规则
            if not is_inherit_allowed(scope, item):
                continue
            # 可见性过滤（详见决策 3）
            if not check_visibility(scope_name, item):
                continue
            results.append(item)

    # 去重：同 ID 保留最新 version
    return dedupe_by_id_keep_latest(results)
```

#### 2.5 校验规则（admission webhook）

- ✅ `project` 作用域必须有 `parentRef` 指向 `team`
- ✅ `team` 作用域必须有 `parentRef` 指向 `organization`
- ✅ `organization` 作用域必须有 `parentRef` 指向 `industry`
- ✅ `industry` 作用域 **必须** `parentRef == nil`
- ✅ `parentRef` 引用的 scope level 必须恰好高一级
- ❌ 禁止循环引用（A.scope.parentRef → B && B.scope.parentRef → A）
- ❌ 禁止父引用跨 namespace（v0.1 简化：所有 KnowledgeScope 在同一 namespace，或显式 `cluster-scope` 标记）

#### 2.6 集群作用域 vs 命名空间作用域

v0.1 简化：
- `industry` scope：cluster-scoped（**必须** cluster scope，因为整个集群共享）
- `organization` / `team` / `project`：namespace-scoped

**约束**：cluster-scoped `industry` scope **只允许 1 个实例**（避免多 industry 混淆）。后续若需多 industry，需走 ADR 扩展。

### 决策 3：KnowledgeItem CRD 详细设计

#### 3.1 设计目标

- 统一抽象显性知识：runtime 知识（API spec / 架构图）+ 系统文档（runbook / FAQ）
- 强制挂载到 KnowledgeScope（无 scope = 不允许）
- 支持 type 枚举（强 schema，禁 dynamic）
- 可见性规则显式（4 级 × agent-private 5 维矩阵的 Knowledge 侧）

#### 3.2 Spec 字段

```go
type KnowledgeItemSpec struct {
    // ScopeRef 挂载的作用域引用（必填）
    // +kubebuilder:validation:Required
    ScopeRef ScopeReference `json:"scopeRef"`

    // Type 知识类型枚举（必填，禁 dynamic）
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:Enum=document;runbook;api-spec;architecture;faq;best-practice;template;contract;troubleshooting;glossary;other
    Type KnowledgeType `json:"type"`

    // Title 标题（必填）
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:MinLength=1
    // +kubebuilder:validation:MaxLength=128
    Title string `json:"title"`

    // Body 知识正文（Markdown）
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:MinLength=1
    // +kubebuilder:validation:MaxLength=65536  // 64KB 上限
    Body string `json:"body"`

    // Summary 简短摘要（可选，用于搜索结果展示）
    // +kubebuilder:validation:MaxLength=512
    Summary string `json:"summary,omitempty"`

    // Tags 标签（可选，用于检索）
    // +optional
    // +kubebuilder:validation:MaxItems=20
    Tags []string `json:"tags,omitempty"`

    // Visibility 可见性（必填）
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:Enum=scope-only;scope-and-children;public-readable;agent-private
    Visibility KnowledgeVisibility `json:"visibility"`

    // OwnerRef 创作者引用（必填）
    // +kubebuilder:validation:Required
    OwnerRef SubjectReference `json:"ownerRef"`

    // SourceURI 原始来源 URI（可选）
    // +kubebuilder:validation:MaxLength=2048
    SourceURI string `json:"sourceURI,omitempty"`

    // Version 版本号（必填，从 1 开始单调递增）
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:Minimum=1
    Version int32 `json:"version"`

    // SupersededBy 指向新版本的 KnowledgeItem（可选，用于废弃链）
    // +optional
    SupersededBy *ItemReference `json:"supersededBy,omitempty"`

    // ExpiryDate 过期时间（可选，过期自动 phase=Expired）
    // +optional
    ExpiryDate *metav1.Time `json:"expiryDate,omitempty"`

    // RelatedItems 关联的其他 KnowledgeItem（可选，用于交叉引用）
    // +optional
    // +kubebuilder:validation:MaxItems=50
    RelatedItems []ItemReference `json:"relatedItems,omitempty"`
}

type KnowledgeType string
const (
    KnowledgeTypeDocument       KnowledgeType = "document"
    KnowledgeTypeRunbook        KnowledgeType = "runbook"
    KnowledgeTypeAPISpec        KnowledgeType = "api-spec"
    KnowledgeTypeArchitecture   KnowledgeType = "architecture"
    KnowledgeTypeFAQ            KnowledgeType = "faq"
    KnowledgeTypeBestPractice   KnowledgeType = "best-practice"
    KnowledgeTypeTemplate       KnowledgeType = "template"
    KnowledgeTypeContract       KnowledgeType = "contract"
    KnowledgeTypeTroubleshooting KnowledgeType = "troubleshooting"
    KnowledgeTypeGlossary       KnowledgeType = "glossary"
    KnowledgeTypeOther          KnowledgeType = "other"
)

type KnowledgeVisibility string
const (
    // ScopeOnly 仅当前作用域可见（不下传）
    VisibilityScopeOnly KnowledgeVisibility = "scope-only"

    // ScopeAndChildren 当前作用域 + 所有子作用域可见（默认）
    VisibilityScopeAndChildren KnowledgeVisibility = "scope-and-children"

    // PublicReadable 整个集群可读（用于 industry-scope 的"行业知识"）
    VisibilityPublicReadable KnowledgeVisibility = "public-readable"

    // AgentPrivate 仅创建者 agent 可见（5 维矩阵的 agent-private 维度）
    VisibilityAgentPrivate KnowledgeVisibility = "agent-private"
)
```

**字段数：12 个（Spec）**（ADR-0004 约束 ≤15，达标）

#### 3.3 Status 字段

```go
type KnowledgeItemStatus struct {
    // Phase: Draft | Published | Deprecated | Expired | Error
    Phase ItemPhase `json:"phase"`

    // Message 人类可读状态
    Message string `json:"message,omitempty"`

    // Conditions 标准 K8s conditions
    Conditions []metav1.Condition `json:"conditions,omitempty"`

    // SearchIndexed 是否已建立搜索索引
    SearchIndexed bool `json:"searchIndexed"`

    // LastQueriedAt 最近查询时间（用于热度排序）
    LastQueriedAt *metav1.Time `json:"lastQueriedAt,omitempty"`

    // QueryCount30d 近 30 天查询次数（用于 LRU 缓存淘汰）
    QueryCount30d int32 `json:"queryCount30d"`

    // ObservedGeneration
    ObservedGeneration int64 `json:"observedGeneration"`
}
```

#### 3.4 可见性规则（决策 3.2 与 Memory 5 维矩阵的 Knowledge 侧）

| Visibility 值 | 可见范围 | 与 Memory agent-private 的关系 |
|---|---|---|
| `scope-only` | 当前 scope 直接成员 | ❌ 不参与 agent-private |
| `scope-and-children`（默认） | 当前 + 子 scope | ❌ 不参与 agent-private |
| `public-readable` | 整个集群所有 scope | ❌ 不参与 agent-private |
| `agent-private` | 创建者 agent + 当前 scope | ✅ 是 5 维矩阵的"agent-private"维度在 Knowledge 侧的对偶 |

**约束**：
- `agent-private` visibility **必须** `OwnerRef.Kind == ServiceAccount`（agent 才有"私有"概念）
- `public-readable` 仅允许 `ScopeRef.Level == industry`（避免团队知识外泄）

### 决策 4：Knowledge Service Agent Card 设计

#### 4.1 设计目标

Knowledge Service 是**特殊 Agent**，与其他 Agent 同等待遇——通过 A2A 协议被调用，而非直连 CRD。这保证了"所有 Agent 调用都走 A2A"的宪法 2.1 一致性。

#### 4.2 Agent Card

```json
{
  "name": "superteam-a2a.knowledge-service",
  "version": "0.1.0",
  "description": "Internal knowledge service for superteam-a2a. Provides free-text query and item retrieval across the 4-level scope hierarchy.",
  "provider": {
    "organization": "superteam-a2a",
    "url": "https://github.com/CoderZhangfujiang/superteam-a2a"
  },
  "skills": [
    {
      "id": "query_knowledge",
      "name": "Query Knowledge",
      "description": "Free-text search over KnowledgeItems with scope/type/tag filters. Returns ranked item references.",
      "inputSchema": {
        "type": "object",
        "required": ["scope", "query"],
        "properties": {
          "scope": {
            "type": "string",
            "description": "KnowledgeScope name to query within (inherits parent scopes automatically)"
          },
          "query": {
            "type": "string",
            "description": "Free-text query (1-512 chars)"
          },
          "typeFilter": {
            "type": "array",
            "items": {"type": "string", "enum": ["document","runbook","api-spec","architecture","faq","best-practice","template","contract","troubleshooting","glossary","other"]}
          },
          "tagFilter": {
            "type": "array",
            "items": {"type": "string"}
          },
          "maxResults": {
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
            "default": 10
          }
        }
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "items": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": {"type": "string"},
                "scope": {"type": "string"},
                "type": {"type": "string"},
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "version": {"type": "integer"},
                "relevanceScore": {"type": "number", "minimum": 0, "maximum": 1}
              }
            }
          },
          "totalCount": {"type": "integer"}
        }
      }
    },
    {
      "id": "get_knowledge_item",
      "name": "Get Knowledge Item",
      "description": "Retrieve full KnowledgeItem body by name + version.",
      "inputSchema": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": {"type": "string", "description": "KnowledgeItem name"},
          "version": {"type": "integer", "description": "Specific version (default: latest)"}
        }
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "scope": {"type": "string"},
          "type": {"type": "string"},
          "title": {"type": "string"},
          "body": {"type": "string"},
          "tags": {"type": "array"},
          "version": {"type": "integer"},
          "sourceURI": {"type": "string"},
          "ownerRef": {"type": "object"},
          "relatedItems": {"type": "array"}
        }
      }
    }
  ],
  "capabilities": {
    "streaming": false,
    "pushNotifications": false,
    "stateTransitionHistory": false
  },
  "authentication": {
    "schemes": ["mtls"]
  }
}
```

#### 4.3 部署形态

- **Deployment**：1 副本（v0.1 单实例，水平扩展推 v0.5+）
- **ServiceAccount**：独立 SA（不是 default）
- **NetworkPolicy**：仅允许 Operator + 其他 Agent 调用
- **不暴露 HTTP**：仅 A2A mTLS（cert-manager 颁发）

### 决策 5：A2A method 详细字段

#### 5.1 `a2a.queryKnowledge`

**Request**（A2A Message `data` 部分）：
```json
{
  "scope": "team-payments-platform",
  "query": "如何处理信用卡退款失败？",
  "typeFilter": ["runbook", "troubleshooting"],
  "tagFilter": ["payments", "refund"],
  "maxResults": 10
}
```

**Response**：
```json
{
  "items": [
    {
      "name": "refund-failure-handling",
      "scope": "team-payments-platform",
      "type": "runbook",
      "title": "信用卡退款失败处理流程",
      "summary": "针对 3 种常见退款失败场景的处理步骤...",
      "version": 3,
      "relevanceScore": 0.92
    }
  ],
  "totalCount": 7
}
```

**错误码**：
- `KNOWLEDGE_SCOPE_NOT_FOUND` (404)
- `KNOWLEDGE_QUERY_TOO_LONG` (400, max 512 chars)
- `KNOWLEDGE_INVALID_TYPE` (400, not in enum)
- `KNOWLEDGE_INTERNAL_ERROR` (500)

#### 5.2 `a2a.getKnowledgeItem`

**Request**：
```json
{
  "name": "refund-failure-handling",
  "version": 3
}
```

**Response**：
```json
{
  "name": "refund-failure-handling",
  "scope": "team-payments-platform",
  "type": "runbook",
  "title": "信用卡退款失败处理流程",
  "body": "## 场景 1: ...\n## 场景 2: ...",
  "tags": ["payments", "refund", "credit-card"],
  "version": 3,
  "sourceURI": "https://wiki.example.com/refund-failure-handling",
  "ownerRef": {"kind": "User", "name": "alice"},
  "relatedItems": [
    {"name": "refund-api-spec", "scope": "team-payments-platform"}
  ]
}
```

**错误码**：
- `KNOWLEDGE_ITEM_NOT_FOUND` (404)
- `KNOWLEDGE_VERSION_NOT_FOUND` (404)
- `KNOWLEDGE_FORBIDDEN` (403, agent-private 且 caller ≠ owner)

### 决策 6：Knowledge 与 Memory 的边界

#### 6.1 设计原则

- **Knowledge 是"人写的"**：人工撰写、版本控制、显式废弃
- **Memory 是"Agent 写的"**：任务执行中生成、confidence + decay + reinforce
- **两者必须显式区分**，禁止把 Memory 当 Knowledge（违反宪法 2.5）

#### 6.2 详细边界表

| 维度 | KnowledgeItem | Memory |
|---|---|---|
| **来源** | 人（User / Group） | Agent（ServiceAccount） |
| **必填字段** | `scopeRef` / `type` / `title` / `body` / `visibility` / `version` | `scopeRef` / `agentRef` / `confidence` / `decayDays` / `content` |
| **生命周期** | 显式 `phase`（Draft/Published/Deprecated/Expired） | 自动 decay + 手动 reinforce |
| **CRUD 入口** | `kubectl apply` + A2A `query/get` | A2A `recordMemory` / `queryMemory` + MemoryReconciler 自动 decay |
| **可见性** | 4 级作用域 + 4 个 visibility 值 | 5 维矩阵（4 作用域 × agent-private 正交） |
| **Body 格式** | Markdown（≤64KB） | 结构化 KV（content + metadata） |
| **版本控制** | 显式 `version` 字段 | 不版本化（覆盖更新） |
| **关系** | KnowledgeItem 可引用 Memory 作为 `relatedItems` | Memory 可引用 KnowledgeItem 作为 source |

#### 6.3 边界判定规则（admission webhook）

- ✅ `KnowledgeItem.OwnerRef.Kind` ∈ {User, Group} —— ServiceAccount 一律拒绝
- ✅ `Memory.AgentRef.Kind` == ServiceAccount —— User/Group 一律拒绝
- ✅ Memory 写入时若引用 KnowledgeItem，校验 KnowledgeItem 存在
- ❌ 禁止 Agent 通过 `recordMemory` 写"看起来像 KnowledgeItem"的结构（schema 强校验）

### 决策 7：跨级共享（Scope-up）机制 — v0.1 简化版

#### 7.1 现状

Agent 在 `project` scope 总结的经验，需要"升级"到 `team` / `organization` / `industry` 才能被其他团队复用。

#### 7.2 v0.1 简化机制（**手动**）

- 不引入自动化 scope-up
- 用户通过 `kubectl patch knowledgeitem ...` 手动修改 `spec.scopeRef.name`
- KnowledgeItem 的版本号保留（同一内容跨级共享不重置版本）

```bash
# 示例：将 project 知识升级到 team
kubectl patch knowledgeitem refund-failure-handling -n project-checkout \
  --type=merge \
  -p '{"spec":{"scopeRef":{"name":"team-payments-platform"}}}'
```

#### 7.3 为什么不自动化

- 自动化需要 confidence 阈值 + 审批流程（v0.5+ 引入）
- v0.1 单人维护，手动更可控
- 自动化增加 CRD 字段（approval / approvedBy），违反"≤15 字段"约束

#### 7.4 v0.5+ 规划（非 v0.1 范围）

- 增加 `KnowledgePromotionRequest` CRD
- 自动化规则：Memory `confidence ≥ 0.85` AND `reinforcedCount ≥ 5` 自动生成 promotion request
- 审批：Owner 审批后 scope-up

### 决策 8：搜索实现

v0.1 简化：
- **存储**：所有 KnowledgeItem 直接存 K8s etcd（CRD 即存储）
- **检索**：Operator 内存倒排索引 + 简单 BM25 评分（**不引入外部搜索引擎**）
- **容量上限**：单集群 ≤ 10,000 KnowledgeItem（超出则拒绝创建，提示升级到 v0.5+ Vector DB）
- **重启代价**：Operator 重启后重建倒排索引（预计 ≤ 30s for 10K items）

**v0.5+ 规划**：
- 可选 Vector DB 后端（Chroma / Qdrant）
- Operator 实现 vector backend 接口
- 用户在 Helm values 选择

### 决策 9：验收标准（v0.1 Knowledge 必须满足才发 Phase 2）

#### 9.1 功能完整性

- [ ] 2 个 CRD schema 注册成功（v1alpha1）
- [ ] KnowledgeScope 4 级继承算法单测覆盖
- [ ] KnowledgeItem 12 字段枚举全部校验
- [ ] Knowledge Service 部署成功 + mTLS 证书自动颁发
- [ ] Agent 通过 A2A 调用 `queryKnowledge` / `getKnowledgeItem` 成功
- [ ] 可见性矩阵（4 visibility × 4 scope）8 种组合全部单测覆盖

#### 9.2 质量门禁（宪法 9.x）

- [ ] 单元测试覆盖率 ≥ **80%**（KnowledgeScope Controller + KnowledgeItem Controller）
- [ ] E2E 测试（kind 集群）：创建 scope → 创建 item → agent 查询 → 拿到结果
- [ ] admission webhook 单测（4 级继承校验 + 循环引用检测）
- [ ] 搜索性能测试：10K items 查询 P95 ≤ 200ms

#### 9.3 安全门禁（宪法 6.x）

- [ ] Knowledge Service mTLS 强制开启
- [ ] `agent-private` visibility 强制 owner 检查（caller ≠ owner 返回 403）
- [ ] `public-readable` 仅允许 industry scope（webhook 拦截）
- [ ] NetworkPolicy：Knowledge Service 仅接受 Operator + 其他 Agent

#### 9.4 可观测性门禁（宪法 7.x）

- [ ] Prometheus 指标（强制）：
  - `superteam_knowledge_query_total{scope, type, result}`
  - `superteam_knowledge_query_duration_seconds` (histogram)
  - `superteam_knowledge_items_total{scope, type, phase}`
  - `superteam_knowledge_search_index_size`
- [ ] 结构化日志：所有 query / get 记录 trace_id / caller_agent / scope / item_name
- [ ] K8s Events：KnowledgeScope 创建 / 删除；KnowledgeItem 创建 / 废弃 / 过期

#### 9.5 文档门禁（宪法 10.x）

- [ ] KnowledgeScope + KnowledgeItem 完整 API 文档（自动生成 + 示例）
- [ ] Knowledge Service Agent Card JSON 提交到 `examples/knowledge-service-card.json`
- [ ] 用户指南：`docs/guides/knowledge-quickstart.md`（5 分钟创建 scope + item + agent 查询）
- [ ] Runbook：`docs/runbooks/knowledge-faq.md`（常见问题：scope 继承 / visibility / 跨级共享）

---

## 后果（Consequences）

### 正面

- ✅ **宪法一致**：与宪法 2.5（显式优于隐式）、2.6（向后兼容）、2.9（记忆可追溯——Knowledge 是 Memory 的基础）全部对齐
- ✅ **范围显式**：v0.1 Knowledge 边界明确，2 个 CRD + 1 个特殊 Agent + 2 个 method 清晰
- ✅ **Memory 基础就位**：本 ADR 落定后，ADR-0003（Memory）可直接引用 KnowledgeScope / KnowledgeItem
- ✅ **手动 scope-up 降低风险**：v0.1 不引入自动化，避免"自动升级错误知识"风险
- ✅ **搜索实现简单**：内存倒排 + BM25，避免引入 Vector DB 的运维复杂度

### 负面

- ⚠️ **etcd 容量压力**：10K KnowledgeItem × 64KB = ~640MB etcd 占用（etcd 默认 8GB 配额，仍有余量但需监控）
- ⚠️ **手动 scope-up 不可持续**：v0.5 之前若项目增长，需提前规划 KnowledgePromotionRequest CRD
- ⚠️ **agent-private 复杂度**：Knowledge 与 Memory 都有"agent-private"概念，可能引起混淆（需文档澄清）
- ⚠️ **Operator 单点**：Knowledge Service v0.1 单实例部署，水平扩展需 v0.5+（违反宪法 2.8 资源可控的部分精神）
- ⚠️ **全文搜索能力有限**：BM25 不支持语义检索，Agent 找不到近义词（v0.5+ Vector DB 解决）

### 缓解措施

| 风险 | 缓解 |
|---|---|
| etcd 容量 | Operator 监控 etcd 容量 + 10K 上限硬卡 + 文档提示 |
| 手动 scope-up | Phase 2 完成后即启动 ADR 起草 KnowledgePromotionRequest |
| agent-private 混淆 | 文档单独章节 + 在 CRD `Description` 字段明示区别 |
| 单点部署 | Phase 2 完成后 Helm values 支持 replicas（默认 1，但可手动调） |
| BM25 局限 | Phase 2 README 显式说明（"v0.1 仅支持关键词检索，v0.5+ 引入语义检索"） |

---

## 备选方案（Alternatives）

### A. 4 级作用域 + 内存 BM25（**采纳**）

如本决策所述。

**采纳理由：**
- 与用户决策一致（4 级 + agent-private + 二者兼具）
- 单人 2h/天 在 4 周 Phase 2 内可完成
- 搜索实现简单，无外部依赖

### B. 5 级作用域（增加 `personal` 在 `project` 之下）—— **未采纳**

**未采纳理由：**
- 违反 ADR-0004 锁定的 4 级 + agent-private 正交方案
- "personal" 知识本质上属于 agent-private 维度，无需独立级别
- 增加 1 级让 CRD 字段（level 枚举 + 继承算法）复杂度上升

### C. Vector DB 一开始就集成（**未采纳**）

**未采纳理由：**
- 增加外部依赖（Chroma / Qdrant 部署运维）
- 违反 v0.1 简化原则（"无外部依赖"）
- v0.1 用户量小，BM25 足够
- v0.5+ 接口抽象后可插拔

### D. Knowledge Graph / 实体关系建模（**未采纳**）

**未采纳理由：**
- 与宪法 2.5（显式优于隐式）冲突——动态 schema 倾向
- 单人维护成本极高（Neo4j / 推理引擎）
- v0.1 用户场景不明确（无社区需求验证）
- v0.5+ 视需求决定

### E. Knowledge Item 无 type 枚举，自由 body 字段（**未采纳**）

**未采纳理由：**
- 违反宪法 2.5（显式优于隐式）
- 无法做类型化检索
- Agent 集成时需大量类型探测逻辑

---

## 决策依据（Rationale）

本决策选择 A（4 级作用域 + 内存 BM25），依据如下：

1. **用户决策优先**：用户已锁定"4 级 + agent-private 正交 + 二者兼具 + 全部进 v0.1"，任何偏离都违反用户决策
2. **宪法一致性**：与宪法 2.5 / 2.6 / 2.9 / 14.4 强门禁全部对齐
3. **工作量可控**：2 个 CRD + 1 个特殊 Agent + 2 个 method + 内存搜索 = ~4 周工作量，符合 Phase 2 预算
4. **可演进**：所有字段在 v1.0.0 之前可自由调整（14.5 MVP 例外），到 v0.5 再迭代 Vector DB / Graph
5. **避免外部依赖**：符合用户"无运维负担"偏好（DevOps 长板但项目本体应轻量）

---

## 实施（Implementation）

### 立即（本会话内）

- [x] 本 ADR 落地（`docs/adr/0002-knowledge-management-design.md`）
- [ ] ADR-0003 Memory 设计（依赖本 ADR 的 KnowledgeScope / KnowledgeItem 字段定义）

### Phase 2 周期（第 11-14 周）

按 [ROADMAP.md](../../ROADMAP.md) 实施：

1. KnowledgeScope CRD + KnowledgeItem CRD schema 定义（Go struct + 自动生成 CRD YAML）
2. KnowledgeScope Controller + KnowledgeItem Controller（reconcile 幂等）
3. Knowledge Service 部署清单（Deployment + Service + SA + NetworkPolicy + cert-manager Certificate）
4. A2A method 实现：`a2a.queryKnowledge` / `a2a.getKnowledgeItem`
5. 内存倒排索引 + BM25 评分（Operator 启动时重建）
6. admission webhook（4 级继承校验 + 循环引用检测 + Knowledge/Memory 边界）
7. Helm chart values：`knowledge.enabled: true` / `knowledge.replicas: 1` / `knowledge.maxItems: 10000`
8. E2E 测试（kind + hello-agent + knowledge-query 演示）
9. 指标 + 日志 + Events 埋点
10. 文档（API 文档 + 用户指南 + Runbook）

### v0.5.0 周期（非 v0.1 范围）

- KnowledgePromotionRequest CRD（自动化 scope-up）
- Vector DB 后端接口（可选 Chroma / Qdrant）
- Knowledge Service 水平扩展

### v1.0.0 周期（非 v0.1 范围）

- Knowledge Service 1+ replicas 默认开启
- Knowledge 全字段集冻结
- 6 framework adapters 集成 knowledge query skill

---

## 参考（References）

- [CONSTITUTION.md](../../CONSTITUTION.md) v0.2.0
  - 第二条 5（显式优于隐式）
  - 第二条 6（向后兼容是承诺）
  - 第二条 9（记忆可追溯）—— Knowledge 是 Memory 的基础
  - 第三条 1（分层严格）
  - 第六条（安全规范）
  - 第七条（可观测性）
  - 第九条（测试策略）
  - 第十一条（版本管理 + Semver）
  - 第十四条 4（强门禁：本 ADR 属其前置）
  - 第十五条（质量第一性）
- [ADR-0001](0001-v1-scope-statement.md) v1 范围声明
- [ADR-0004](0004-v01-scope-extension-knowledge-and-memory.md) v0.1 范围重定
- [ROADMAP.md](../../ROADMAP.md) Phase 2 任务清单
- [L1-architecture.md](../design/L1-architecture.md)（待更新：+2 CRD + 1 特殊 Agent + 2 method）
- [L1-system-spec.md](../spec/L1-system-spec.md)（待更新：CRD 字段 + 错误码 + 状态机）

---

## 签署

本 ADR 由项目发起人于 **2026-07-23** 批准生效（依据宪法 14.5 MVP 例外，单点评审）。