# superteam-a2a — L1 系统契约规格

> **层级**: L1（系统级 Spec）
> **版本**: **v0.2.0**（Python 重写，ADR-0005 触发；2026-07-24 评审通过）
> **状态**: ✅ **已评审通过**（依据 [`docs/reviews/l1-python-stack-migration-review.md`](../reviews/l1-python-stack-migration-review.md) 2026-07-24；10 维度全 PASS）
> **配套设计**: [`docs/design/L1-architecture.md`](../design/L1-architecture.md)（**v0.2.0** 同日同步评审通过）
> **配套评审**: [`docs/reviews/l1-python-stack-migration-review.md`](../reviews/l1-python-stack-migration-review.md)（✅ 2026-07-24）
> **依据**: [`CONSTITUTION.md`](../../CONSTITUTION.md) **v0.5.0**（§3.8 Python-first + §9.7 Python 静态质量 + §10.3 docstring + §13.6 维护 A2A Python SDK/Kopf）
> **设计输入**：[ADR-0001](../adr/0001-v1-scope-statement.md)（v1 范围）/ [ADR-0002](../adr/0002-knowledge-management-design.md)（知识管理）/ [ADR-0003](../adr/0003-memory-design.md)（Memory）/ [ADR-0004](../adr/0004-v01-scope-extension-knowledge-and-memory.md)（v0.1 范围）/ [ADR-0005](../adr/0005-python-first-technology-stack.md)（**Python-first 实现栈**）
> **supersedes**: v0.1.0 Go baseline（[`docs/reviews/l1-review-architecture.md`](../reviews/l1-review-architecture.md) 2026-07-23 通过；**仅 supersede Go struct / kubebuilder annotation / controller-runtime 实现条款；wire contract 与业务语义完全继续有效**）
> **MVP 例外**: §14.5 适用（v0.1.0 → v1.0.0）

---

## 0. 阅读指南

本文档定义 `superteam-a2a` 的 **L1 系统契约**：CRD Schema / API 端点 / 错误模型 / 状态机 / 资源默认值 / Helm values schema。**不**解释"为什么"（设计意图见 [`L1-architecture.md`](../design/L1-architecture.md)）。

**读者**：L2 模块设计者、CRD 字段作者、API 客户端实现者、评审者。

**Python 实现关键变化**（与 v0.1 Go baseline 对照）：

| 维度 | v0.1 Go | v0.2 Python |
|------|---------|-------------|
| **类型层** | Go struct | Pydantic v2 `BaseModel`（strict / alias 保留 wire camelCase） |
| **字段校验** | `+kubebuilder:validation:` 注解 | `pydantic.Field(...)`（`ge`/`le`/`min_length`/`max_length`/`pattern`/`Literal`） |
| **CRD 生成** | kubebuilder controller-gen | `build/gen_crds.py`（Pydantic JSON Schema → Kubernetes OpenAPI v3） |
| **Status 写回** | `r.Status().Update()` | `kopf.adopt(status_patch=...)` |
| **Admission webhook** | controller-runtime webhook | `@kopf.on.validate` 或独立 ASGI webhook server（详见 L2-2 Spec） |
| **JSON Schema** | OpenAPI v3 由 controller-gen 生成 | JSON Schema 2020-12 → OpenAPI v3 确定性生成（CI 验证无 diff） |

> **wire contract 锁定**：所有 CRD YAML、A2A JSON-RPC envelope、错误码、Agent Card path、Task FSM、metrics name 完全不变（依据 ADR-0005 §4）。

---

## 1. CRD 通用约定（Python 实现）

### 1.1 API Group 与版本

| 字段 | 值 |
|------|-----|
| **Group** | `superteam-a2a.io` |
| **v0.1 版本** | `v1alpha1` |
| **v0.5 版本** | `v1beta1` |
| **v1.0 版本** | `v1` |

### 1.2 资源命名

- **Kind**：`PascalCase`（如 `Agent`、`AgentSet`、`Workflow`、`KnowledgeScope`、`KnowledgeItem`、`Memory`）
- **资源名**：`camelCase`（如 `agent`、`agentSet`、`workflow`、`knowledgeScope`、`knowledgeItem`、`memory`）
- **CR 名**：`kebab-case`（如 `hello-agent`、`echo-fleet`、`refund-failure-handling`、`team-payments-platform`）
- **KnowledgeItem / Memory 内容键名**：`snake_case`（如 `retry_count`、`confidence_score`）
- **Python 业务层属性**：snake_case（如 `agent_spec.framework`），通过 Pydantic `alias` 与 wire YAML camelCase 双向映射（ADR-0005 §5.1）

### 1.3 通用字段

所有 CRD 必须包含（wire YAML 不变；Python 实现见 §2-§13 各 spec）：

```yaml
spec:
  # 业务字段
  ...

  # 通用字段（所有 v0.1 CRD 共享）
  imagePullSecrets: []      # optional, image pull secrets
  serviceAccountName: ""   # optional, default: <cr-name>-sa
  podSecurityContext: {}   # optional
  securityContext: {}     # optional
  nodeSelector: {}         # optional
  affinity: {}             # optional
  tolerations: []          # optional
  priorityClassName: ""   # optional
```

### 1.4 通用 Status

```yaml
status:
  phase: "Pending"     # Pending / Available / Failed / Unknown
  observedGeneration: 1
  conditions:
    - type: "Ready"
      status: "True"   # True / False / Unknown
      lastTransitionTime: "2026-07-24T10:00:00Z"
      reason: "AllChecksPass"
      message: "Agent is ready"
  endpoints: []        # controller 填入
  lastUpdated: "2026-07-24T10:00:00Z"
```

**Python 实现**（`superteam_a2a.operator.models.common`，全部 CRD 共享）：

```python
# 示意，详见 L2-2 / L3-1 Spec
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class Phase(str, Enum):
    PENDING = "Pending"
    AVAILABLE = "Available"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class ConditionStatus(str, Enum):
    TRUE = "True"
    FALSE = "False"
    UNKNOWN = "Unknown"


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = Field(min_length=1, max_length=64)
    status: ConditionStatus
    last_transition_time: datetime = Field(alias="lastTransitionTime")
    reason: str = Field(min_length=1, max_length=128)
    message: str = Field(max_length=1024)


class BaseStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phase: Phase
    observed_generation: int = Field(alias="observedGeneration", ge=0)
    conditions: list[Condition] = Field(default_factory=list)
    last_updated: datetime | None = Field(None, alias="lastUpdated")
```

### 1.5 Condition 类型

| Type | 含义 |
|------|------|
| `Ready` | 资源可用 |
| `Progressing` | 进行中 |
| `Degraded` | 降级运行 |
| `Reconciled` | 最近一次 reconcile 成功 |

### 1.6 wire alias 单向原则（ADR-0005 §5.1）

- wire YAML 字段名 = camelCase（K8s / A2A 约定）
- Python 业务层属性名 = snake_case（PEP 8）
- Pydantic v2 `populate_by_name=True` + `Field(alias="...")` 双向映射
- 序列化输出默认 wire 格式（camelCase）；业务层内部使用 snake_case
- 时间字段一律 timezone-aware UTC（`datetime.now(timezone.utc)`）

---

## 2. Agent CRD

### 2.1 AgentSpec（wire YAML 不变 · Python 实现）

**wire YAML**（与 v0.1 一致）：
```yaml
spec:
  framework: langchain        # 必填, langchain|autogen|crewai|sk|strands|smolagents|custom
  version: "0.1.0"            # 必填, Agent Card 版本
  image: "ghcr.io/me/my-langchain-agent:0.1.0"
  imagePullPolicy: IfNotPresent
  resources: { requests: {...}, limits: {...} }
  card:                       # 必填
    name: "hello-agent"
    description: "..."
    skills: [...]
    inputModes: ["text"]
    outputModes: ["text"]
    version: "0.1.0"
    protocolVersion: "0.3"
  adapter:                    # 必填
    image: "..."
    port: 8080
  config:                     # optional, 框架特定配置
    raw: {...}
  timeout: 600                # 秒, default 600
  maxRetries: 3               # default 3
  replicas: 1                 # default 1
```

**Python Pydantic 表达**（`packages/operator/src/superteam_a2a/operator/models/agent.py`）：

```python
# 示意，完整 Spec 在 L2-2 / L3-1
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Framework(str, Enum):
    LANGCHAIN = "langchain"
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    SK = "sk"
    STRANDS = "strands"
    SMOLAGENTS = "smolagents"
    CUSTOM = "custom"


class ImagePullPolicy(str, Enum):
    IF_NOT_PRESENT = "IfNotPresent"
    ALWAYS = "Always"
    NEVER = "Never"


class ResourceRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requests: dict[str, str] = Field(min_length=1)  # {"cpu": "100m", "memory": "256Mi"}
    limits: dict[str, str] = Field(min_length=1)


class AgentCardSpec(BaseModel):
    """Agent Card（wire shape 不变；a2a-sdk 标准类型优先复用）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str = Field(pattern=r"^[a-z][a-z0-9-]*[a-z0-9]$", max_length=64)
    description: str = Field(min_length=1, max_length=512)
    url: HttpUrl | None = None
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    protocol_version: str = Field(alias="protocolVersion", min_length=1, max_length=16)
    skills: list["AgentSkillSpec"] = Field(min_length=1, max_length=50)
    input_modes: list[str] = Field(alias="inputModes", min_length=1)
    output_modes: list[str] = Field(alias="outputModes", min_length=1)
    metadata: dict[str, str] | None = Field(default=None, max_length=64)


class AgentSkillSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z][a-z0-9-]*[a-z0-9]$", max_length=64)
    description: str = Field(min_length=1, max_length=512)
    examples: list[str] | None = Field(default=None, max_length=10)


class AdapterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    image: str
    port: int = Field(8080, ge=1, le=65535)
    image_pull_policy: ImagePullPolicy | None = Field(None, alias="imagePullPolicy")
    resources: ResourceRequirements | None = None
    env: list[dict] | None = None  # EnvVar K8s type
    args: list[str] | None = None


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw: dict | None = None  # 透传框架特定配置


class AgentSpec(BaseModel):
    """Agent CRD Spec（wire alias 保留 YAML camelCase）。"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    framework: Framework
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    image: str
    image_pull_policy: ImagePullPolicy | None = Field(None, alias="imagePullPolicy")
    resources: ResourceRequirements
    card: AgentCardSpec
    adapter: AdapterConfig
    config: RuntimeConfig | None = None
    timeout: int = Field(600, ge=1, le=3600)
    max_retries: int = Field(3, ge=0, le=10, alias="maxRetries")
    replicas: int = Field(1, ge=1, le=100)
```

### 2.2 AdapterConfig（wire YAML 不变）

完整 spec 见 §2.1 `AdapterConfig` Pydantic 定义。

### 2.3 RuntimeConfig（wire YAML 不变）

完整 spec 见 §2.1 `RuntimeConfig` Pydantic 定义。

### 2.4 AgentStatus（wire YAML 不变）

**wire shape**（与 v0.1 一致）：
```yaml
status:
  phase: "Available"
  observedGeneration: 1
  conditions: [...]
  endpoints:
    - type: "a2a"
      url: "https://hello-agent:8080"
      port: 8080
      ready: true
  agentCard: {...}   # Operator 抓取后填入
  replicas: 1
  readyReplicas: 1
  lastUpdated: "2026-07-24T10:00:00Z"
```

**Python 表达**：
```python
class Endpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = Field(pattern=r"^(a2a|health)$")
    url: HttpUrl
    port: int = Field(ge=1, le=65535)
    ready: bool


class AgentStatus(BaseStatus):
    endpoints: list[Endpoint] = Field(default_factory=list)
    agent_card: AgentCardSpec | None = Field(None, alias="agentCard")
    replicas: int = Field(ge=0)
    ready_replicas: int = Field(0, ge=0, alias="readyReplicas")
```

### 2.5 验证规则

| 字段 | 规则 | Python Pydantic 校验 |
|------|------|----------------------|
| `spec.framework` | enum: `langchain` / `autogen` / `crewai` / `sk` / `strands` / `smolagents` / `custom` | `Framework` enum |
| `spec.version` | SemVer 2.0.0 | `Field(pattern=r"^\d+\.\d+\.\d+$")` |
| `spec.image` | 合法 Docker 引用 | 字符串校验（在 admission webhook 验证 image ref） |
| `spec.resources` | 必须包含 `requests` 与 `limits` | `ResourceRequirements` required fields |
| `spec.card.name` | kebab-case，正则 `^[a-z][a-z0-9-]*[a-z0-9]$` | `Field(pattern=...)` |
| `spec.card.skills` | 至少 1 项 | `Field(min_length=1)` |
| `spec.card.inputModes` | 至少包含 `text` | `Field(min_length=1)` |
| `spec.adapter.port` | 1-65535 | `Field(ge=1, le=65535)` |
| `spec.timeout` | 1-3600（秒） | `Field(ge=1, le=3600)` |
| `spec.maxRetries` | 0-10 | `Field(ge=0, le=10)` |
| `spec.replicas` | 1-100 | `Field(ge=1, le=100)` |

---

## 3. AgentSet CRD

### 3.1 AgentSetSpec（wire YAML 不变 · Python 实现）

**wire YAML**（与 v0.1 一致）：
```yaml
spec:
  template:
    metadata: {...}
    spec: { ... }   # 完整 AgentSpec
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: "25%"
      maxSurge: "25%"
  updateStrategy:
    type: RollingUpdate
    partition: 0
```

**Python 表达**（关键类型；完整 Spec 在 L2-2 / L3-1）：
```python
class AgentTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metadata: dict | None = None  # K8s ObjectMeta
    spec: "AgentSpec"


class RollingUpdateAgentSet(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    max_unavailable: str | int | None = Field("25%", alias="maxUnavailable")
    max_surge: str | int | None = Field("25%", alias="maxSurge")


class AgentSetStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = Field("RollingUpdate", pattern=r"^(RollingUpdate|Recreate)$")
    rolling_update: RollingUpdateAgentSet | None = Field(None, alias="rollingUpdate")


class AgentSetUpdateStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = Field("RollingUpdate", pattern=r"^(RollingUpdate|OnDelete)$")
    partition: int | None = Field(None, ge=0)


class AgentSetSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    template: AgentTemplate
    replicas: int = Field(1, ge=0, le=100)
    strategy: AgentSetStrategy | None = None
    update_strategy: AgentSetUpdateStrategy | None = Field(None, alias="updateStrategy")
```

### 3.2 AgentSetStatus（wire YAML 不变）

```python
class AgentSetStatus(BaseStatus):
    replicas: int = Field(ge=0)
    ready_replicas: int = Field(0, ge=0, alias="readyReplicas")
    available_replicas: int = Field(0, ge=0, alias="availableReplicas")
    updated_replicas: int = Field(0, ge=0, alias="updatedReplicas")
```

### 3.3 验证规则

- `spec.replicas`: 0-100
- `spec.strategy.type`: enum (`RollingUpdate` / `Recreate`)
- `spec.template.spec`: 必须包含完整 Agent 必填字段（递归 Pydantic 校验）

---

## 4. Workflow CRD

### 4.1 WorkflowSpec（wire YAML 不变 · Python 实现）

**wire YAML**（与 v0.1 一致）：
```yaml
spec:
  tasks:
    - id: "fetch"
      agent: "github-reader"
      dependsOn: []
      inputs: { repo: "...", ref: "main" }
      inputsFrom: []
      outputs: ["files"]
      timeout: 300
      maxRetries: 1
      condition: ""
  timeout: 1800
  ttlSecondsAfterFinished: 86400
  maxRetries: 1
  inputs: {...}
  outputs: {...}
  agentResolution: "exact"  # exact | capability
```

**Python 表达**（关键类型；完整 Spec 在 L2-2 / L3-1）：
```python
class TaskInputRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str = Field(alias="taskId", min_length=1, max_length=64)
    output: str = Field(min_length=1, max_length=64)
    as_: str = Field(alias="as", min_length=1, max_length=64)


class WorkflowTask(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*[a-z0-9]$", max_length=64)
    agent: str | None = Field(None, min_length=1, max_length=128)
    agent_set: str | None = Field(None, alias="agentSet", min_length=1, max_length=128)
    depends_on: list[str] = Field(default_factory=list, alias="dependsOn", max_length=64)
    inputs: dict[str, str] | None = None
    inputs_from: list[TaskInputRef] | None = Field(None, alias="inputsFrom")
    outputs: list[str] | None = None
    timeout: int | None = Field(None, ge=1, le=3600)
    max_retries: int | None = Field(None, ge=0, le=10, alias="maxRetries")
    condition: str | None = Field(None, max_length=512)


class WorkflowSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    tasks: list[WorkflowTask] = Field(min_length=1, max_length=500)
    timeout: int = Field(1800, ge=1, le=7200)
    ttl_seconds_after_finished: int = Field(86400, ge=0, le=604800, alias="ttlSecondsAfterFinished")
    max_retries: int = Field(1, ge=0, le=10, alias="maxRetries")
    inputs: dict[str, str] | None = None
    outputs: dict[str, str] | None = None
    agent_resolution: str = Field("exact", pattern=r"^(exact|capability)$", alias="agentResolution")

    @field_validator("tasks")
    @classmethod
    def validate_dag(cls, tasks: list[WorkflowTask]) -> list[WorkflowTask]:
        """无环 / ID 唯一 / 依赖存在 / 无自依赖（在 handler 中也可调用纯函数）。"""
        ids = {t.id for t in tasks}
        if len(ids) != len(tasks):
            raise ValueError("task ids must be unique")
        for t in tasks:
            if t.id in t.depends_on:
                raise ValueError(f"task {t.id} cannot depend on itself")
            for dep in t.depends_on:
                if dep not in ids:
                    raise ValueError(f"task {t.id} depends on unknown task {dep}")
        # 简化版环检测（Kahn / DFS 在 WorkflowValidator 单独函数）
        return tasks
```

### 4.2 WorkflowStatus（wire YAML 不变）

```python
class TaskStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    phase: str  # Pending|Running|Succeeded|Failed|Skipped|Timeout
    started_at: datetime | None = Field(None, alias="startedAt")
    completed_at: datetime | None = Field(None, alias="completedAt")
    outputs: dict[str, str] | None = None
    error: str | None = None
    attempts: int = Field(0, ge=0)


class WorkflowStatus(BaseStatus):
    started_at: datetime | None = Field(None, alias="startedAt")
    completed_at: datetime | None = Field(None, alias="completedAt")
    task_statuses: dict[str, TaskStatus] | None = Field(None, alias="taskStatuses")
    message: str | None = None
```

### 4.3 验证规则

- `spec.tasks`: ≥ 1, DAG 无环（`WorkflowValidator.validate_dag`）
- `spec.tasks[].id`: kebab-case, regex `^[a-z][a-z0-9-]*[a-z0-9]$`, 唯一
- `spec.tasks[].agent` / `agentSet`: 至少 1（`model_validator` 互斥）
- `spec.tasks[].dependsOn`: 必须引用同 workflow 的任务 ID；依赖必须无环
- `spec.tasks[].timeout`: 1-3600
- `spec.tasks[].maxRetries`: 0-10
- `spec.timeout`: 1-7200
- `spec.ttlSecondsAfterFinished`: 0-604800 (7 天)

### 4.4 DAG 校验（Python `WorkflowValidator` 纯函数）

Controller 在 reconcile 阶段（`@kopf.on.create` handler）调用 `WorkflowValidator.validate_dag()`：

1. **无环**：DAG 必须是无环有向图（Kahn's algorithm 或 DFS）
2. **依赖存在**：所有 `dependsOn` 引用的任务 ID 存在
3. **无自依赖**：`task.dependsOn` 不能包含自身
4. **无重复 ID**：任务 ID 在 workflow 内唯一
5. **输入合法**：所有 `inputsFrom` 引用的输出存在

校验失败 → 状态 `Failed` + K8s Event `WorkflowValidationFailed`。

---

## 5. A2A 协议（基于官方 a2a-sdk）

### 5.1 协议版本

- **v0.1 实现**：A2A v0.3 核心子集
  - 复用官方：`Agent Card` / `Message` / `Task` / `Artifact` / 标准 JSON-RPC envelope
  - 项目扩展：4 个 method 通过 `superteam_a2a.a2a.upstream` 边界注册
- **v0.5 扩展**：SSE Streaming
- **v1.0 完整**：参考 google-a2a/A2A 完整规范

### 5.2 Agent Card（wire JSON 不变 · 服务于 `/.well-known/agent.json`）

```json
{
  "name": "hello-agent",
  "description": "Echoes any input message",
  "url": "https://hello-agent.default.svc:8080",
  "version": "0.1.0",
  "protocolVersion": "0.3",
  "skills": [
    { "name": "echo", "description": "Returns the input message as-is" }
  ],
  "inputModes": ["text"],
  "outputModes": ["text"]
}
```

**Python 实现**：直接复用官方 `a2a.types.AgentCard`；项目不重新定义（ADR-0005 §3.2 + §5）。

### 5.3 Message（wire JSON 不变）

```json
{
  "role": "user",
  "parts": [{"type": "text", "text": "Hello, agent!"}],
  "contextId": "ctx-123",
  "taskId": "task-456",
  "metadata": {"traceparent": "00-abc123-def456-01"}
}
```

**Python 实现**：`from a2a.types import Message, Part`（官方 SDK）。

### 5.4 Task（wire JSON 不变）

```json
{
  "id": "task-456",
  "status": {"state": "completed", "message": "Optional status message"},
  "messages": [...],
  "artifacts": []
}
```

**Python 实现**：`from a2a.types import Task, TaskStatus, Artifact`（官方 SDK）。

### 5.5 JSON-RPC 端点

**请求** `POST /a2a/jsonrpc`：
```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "method": "a2a.sendMessage",
  "params": {"id": "task-456", "message": {"role": "user", "parts": [...]}}
}
```

**响应**：
```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "result": {"id": "task-456", "status": {"state": "completed"}, "messages": [...]}
}
```

**错误**：
```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "error": {
    "code": -32600,
    "message": "Invalid request",
    "data": {"detail": "missing message.role"}
  }
}
```

**Python 实现**：官方 `a2a.server.A2AServer` 处理 envelope；4 个项目扩展 method 在 `superteam_a2a.a2a.upstream` 注册 router。

### 5.6 JSON-RPC Methods（v0.1 共 6 个 + v0.5+ 2 个）

| Method | 来源 | Params | Result | 服务方 | 状态 |
|--------|------|--------|--------|--------|------|
| `a2a.sendMessage` | 官方 SDK | `{id, message}` | `Task` | 任意 Agent | v0.1 |
| `a2a.getTask` | 官方 SDK | `{id}` | `Task` | 任意 Agent | v0.1 |
| `a2a.queryKnowledge` | 项目扩展 | `{scope, query, typeFilter?, tagFilter?, maxResults?}` | `{items[], totalCount}` | **Knowledge Service** | **v0.1（ADR-0002 §5.1）** |
| `a2a.getKnowledgeItem` | 项目扩展 | `{name, version?}` | `KnowledgeItem` | **Knowledge Service** | **v0.1（ADR-0002 §5.2）** |
| `a2a.recordMemory` | 项目扩展 | `{scope, content, summary, memoryKey?, visibility, sourceKnowledgeRef?, tags?}` | `{memoryId, confidence, decayDays, phase, reinforcedCount, effectiveConfidence, createdAt}` | **MemoryReconciler 间接** | **v0.1（ADR-0003 §5.1）** |
| `a2a.queryMemory` | 项目扩展 | `{scope, confidenceMin?, memoryKeyPattern?, tagFilter?, maxResults?}` | `{memories[], totalCount}` | **MemoryReconciler 间接** | **v0.1（ADR-0003 §5.2）** |
| `a2a.cancelTask` | 官方 SDK | `{id}` | `Task` | 任意 Agent | v0.5+ |
| `a2a.subscribeTask` | 官方 SDK | `{id}` | Stream<Task> | 任意 Agent | v0.5+ (SSE) |

**4 个项目扩展 method 的完整 Pydantic Schema 见 §15（新增章节）**。

### 5.7 JSON-RPC 错误码（wire 不变 · 与 v0.1 完全一致）

**通用错误码**：

| Code | 含义 | HTTP Status |
|------|------|-------------|
| -32700 | Parse error | 400 |
| -32600 | Invalid Request | 400 |
| -32601 | Method not found | 404 |
| -32602 | Invalid params | 422 |
| -32603 | Internal error | 500 |
| -32001 | Task not found | 404 |
| -32002 | Task timeout | 504 |
| -32003 | Task cancelled | 410 |
| -32004 | Unauthorized | 401 |
| -32005 | Forbidden | 403 |
| -32006 | Rate limit | 429 |

**Knowledge 错误码**（ADR-0002 §5）：

| Code | 含义 | HTTP Status |
|------|------|-------------|
| -32400 | `KNOWLEDGE_SCOPE_NOT_FOUND` | 404 |
| -32401 | `KNOWLEDGE_ITEM_NOT_FOUND` | 404 |
| -32402 | `KNOWLEDGE_VERSION_NOT_FOUND` | 404 |
| -32403 | `KNOWLEDGE_QUERY_TOO_LONG` | 400 |
| -32404 | `KNOWLEDGE_INVALID_TYPE` | 400 |
| -32405 | `KNOWLEDGE_FORBIDDEN`（agent-private + caller ≠ owner） | 403 |
| -32406 | `KNOWLEDGE_INTERNAL_ERROR` | 500 |

**Memory 错误码**（ADR-0003 §5）：

| Code | 含义 | HTTP Status |
|------|------|-------------|
| -32500 | `MEMORY_SCOPE_NOT_FOUND` | 404 |
| -32501 | `MEMORY_INVALID_CONTENT`（content 空或 > 20 keys） | 400 |
| -32502 | `MEMORY_FORBIDDEN`（agent-private + caller ≠ owner） | 403 |
| -32503 | `MEMORY_RATE_LIMIT`（同 SA 每分钟 > 60 recordMemory） | 429 |
| -32504 | `MEMORY_QUERY_TOO_BROAD`（scope=industry + 无过滤） | 400 |
| -32505 | `MEMORY_INTERNAL_ERROR` | 500 |

**与 L2-1 一致性**：
- ✅ 本表（11 通用 + 7 KNOWLEDGE_* + 6 MEMORY_* = 24 个错误码）与 [L2-1 Spec v0.2.0 §8.4](../spec/L2-module-specs/L2-a2a-protocol.md) Retryable 矩阵**完全一致**（含 Retryable 列与 HTTP Status 映射）
- ✅ wire contract 不变（错误码 + name 字符串 + HTTP Status）；Python 实现由 L2-1 Spec 负责（`superteam_a2a.a2a.errors` 子包 + Pydantic enum）

---

## 6. REST 端点（Python ASGI · 沿用 v0.1 路径）

### 6.1 Operator Metrics

| 路径 | 方法 | 用途 | 响应 |
|------|------|------|------|
| `/metrics` | GET | Prometheus metrics | `text/plain; version=0.0.4` |
| `/healthz` | GET | Liveness | 200 / 503 |
| `/readyz` | GET | Readiness | 200 / 503 |

**Python 实现**：`prometheus-client` `make_asgi_app()` + Starlette mount。

### 6.2 Adapter REST

| 路径 | 方法 | 用途 | 响应 |
|------|------|------|------|
| `/.well-known/agent.json` | GET | Agent Card | 200 `application/json` |
| `/a2a/jsonrpc` | POST | JSON-RPC 2.0 | 200 `application/json` |
| `/a2a/events` | GET | SSE Stream | 200 `text/event-stream` (v0.5) |
| `/healthz` | GET | Health | 200 / 503 |
| `/readyz` | GET | Readiness | 200 / 503 |

### 6.3 健康检查响应（wire JSON 不变）

```json
{
  "status": "ok",
  "version": "0.1.0",
  "commit": "abc123",
  "uptimeSeconds": 3600
}
```

---

## 7. 状态机（与 v0.1 完全一致）

### 7.1 Agent 状态

```
Pending ──▶ Available ──▶ (Failed) ──▶ Unknown
   │            │              ↑
   └────────────┴──────────────┘
        (reconcile 重试)
```

| Phase | 含义 |
|-------|------|
| `Pending` | CRD 创建未处理完 |
| `Available` | Pod Ready + Agent Card 抓取成功 |
| `Failed` | Pod NotReady 超过阈值 |
| `Unknown` | Controller 无法判断（CRD 缺失等） |

### 7.2 Workflow 状态

```
Pending ──▶ Running ──▶ Succeeded
              │  │
              │  └──▶ Failed
              │  │
              │  └──▶ Timeout
              │
              └──▶ (Cancelled, v0.5+)
```

### 7.3 Task 状态

| Phase | 含义 |
|-------|------|
| `Pending` | 等待依赖 |
| `Running` | 正在执行 |
| `Succeeded` | 成功完成 |
| `Failed` | 失败（重试耗尽） |
| `Skipped` | 因上游失败而跳过 |
| `Timeout` | 任务超时 |

### 7.4 KnowledgeScope 状态（ADR-0002 §2.3）

| Phase | 含义 |
|-------|------|
| `Pending` | CRD 创建未处理完 / admission 校验中 |
| `Active` | 校验通过，可挂载 KnowledgeItem |
| `Error` | admission 拒绝 / parentRef 失效 / 循环引用检测 |
| `Deleting` | finalizer 清理中 |

### 7.5 KnowledgeItem 状态（ADR-0002 §3.3）

| Phase | 含义 |
|-------|------|
| `Draft` | 创建中 / 内容未确认 |
| `Published` | 可被 queryKnowledge / getKnowledgeItem 检索 |
| `Deprecated` | supersededBy 指向新版本，旧版本仅可读 |
| `Expired` | 超过 expiryDate 自动转换 |
| `Error` | admission 拒绝 / scope 不存在 / body 校验失败 |

### 7.6 Memory 状态（ADR-0003 §2.3 + §4.2）

| Phase | 触发条件 | 含义 |
|-------|---------|------|
| `Active` | `effectiveConfidence >= 0.5` | 健康，可被 queryMemory 命中 |
| `Decaying` | `0.1 <= effectiveConfidence < 0.5` | 衰减中，仍可读但热度下降 |
| `Promotable` | `effectiveConfidence >= 0.85 && reinforcedCount >= 5 && visibility == scope-and-children` | **v0.1 仅标记字段值**，不触发 PromotionRequest |
| `Expired` | `effectiveConfidence < 0.1` | 7 天宽限期后自动 GC |
| `Error` | admission 拒绝 / scope 缺失 / agentRef SA 不存在 | 创建失败 |

**Python 状态机实现**：纯函数 `compute_memory_phase(memory: Memory, now: datetime) -> MemoryPhase`，被 `MemoryReconciler`（`@kopf.timer` handler）调用（ADR-0005 §6.3 CPU offload）。

---

## 8. 错误模型（与 v0.1 一致）

### 8.1 错误分类

| 类别 | 描述 | Python 实现处理 |
|------|------|-----------------|
| **Validation** | CRD 字段校验失败 | Pydantic `ValidationError` → Kopf 拒绝 reconcile, emit Event |
| **Reconcile** | Controller 内部错误 | Kopf `kopf.HandlersError` → 重试（指数退避） |
| **A2A RPC** | Agent 间调用失败 | `httpx` + `tenacity` 重试，超过 maxRetries → 任务失败 |
| **Task** | 任务执行失败 | 重试 → 任务失败 |
| **System** | 系统级故障（K8s API 不可用等） | 暂停 reconcile, emit Event |

### 8.2 错误响应格式（wire JSON 不变）

```json
{
  "kind": "AgentError",
  "apiVersion": "superteam-a2a.io/v1alpha1",
  "metadata": { "name": "hello-agent", "namespace": "default" },
  "code": "A2A_RPC_FAILED",
  "message": "RPC call failed",
  "detail": {
    "agent": "hello-agent",
    "method": "a2a.sendMessage",
    "rpcCode": -32004,
    "retryAttempt": 2
  },
  "timestamp": "2026-07-24T10:00:00Z"
}
```

### 8.3 错误代码清单（与 v0.1 一致）

| Code | 含义 | 引入版本 |
|------|------|----------|
| `CRD_INVALID` | CRD 字段校验失败 | v0.1 |
| `CRD_NOT_FOUND` | 引用的 CRD 不存在 | v0.1 |
| `K8S_API_ERROR` | K8s API 调用失败 | v0.1 |
| `IMAGE_PULL_FAILED` | 镜像拉取失败 | v0.1 |
| `POD_NOT_READY` | Pod 长时间未就绪 | v0.1 |
| `A2A_RPC_FAILED` | A2A RPC 调用失败 | v0.1 |
| `A2A_TIMEOUT` | A2A RPC 超时 | v0.1 |
| `A2A_AUTH_FAILED` | mTLS 认证失败 | v0.1 |
| `AGENT_CARD_INVALID` | Agent Card 字段违规 | v0.1 |
| `AGENT_CARD_FETCH_FAILED` | Agent Card 抓取失败 | v0.1 |
| `WORKFLOW_DAG_INVALID` | DAG 校验失败 | v0.1 |
| `WORKFLOW_TIMEOUT` | Workflow 超时 | v0.1 |
| `WORKFLOW_TASK_FAILED` | Task 失败 | v0.1 |
| `ADAPTER_UNAVAILABLE` | Adapter 不可用 | v0.1 |
| `RESOURCE_QUOTA_EXCEEDED` | 资源配额超限 | v0.1 |
| `COST_BUDGET_EXCEEDED` | 成本预算超限 | v0.1 |
| `KNOWLEDGE_SCOPE_NOT_FOUND` | KnowledgeScope 不存在 | **v0.1（ADR-0002）** |
| `KNOWLEDGE_ITEM_NOT_FOUND` | KnowledgeItem 不存在 | **v0.1（ADR-0002）** |
| `KNOWLEDGE_VERSION_NOT_FOUND` | 指定 version 不存在 | **v0.1（ADR-0002）** |
| `KNOWLEDGE_QUERY_TOO_LONG` | query > 512 chars | **v0.1（ADR-0002）** |
| `KNOWLEDGE_INVALID_TYPE` | type 不在 11 枚举内 | **v0.1（ADR-0002）** |
| `KNOWLEDGE_FORBIDDEN` | agent-private + caller ≠ owner | **v0.1（ADR-0002）** |
| `KNOWLEDGE_INTERNAL_ERROR` | Knowledge Service 内部错误 | **v0.1（ADR-0002）** |
| `KNOWLEDGE_MAX_ITEMS_EXCEEDED` | cluster > 10K KnowledgeItems | **v0.1（ADR-0002 §8）** |
| `MEMORY_SCOPE_NOT_FOUND` | KnowledgeScope 不存在 | **v0.1（ADR-0003）** |
| `MEMORY_INVALID_CONTENT` | content 空或 > 20 keys | **v0.1（ADR-0003）** |
| `MEMORY_FORBIDDEN` | agent-private + caller ≠ owner | **v0.1（ADR-0003）** |
| `MEMORY_RATE_LIMIT` | 同 SA 每分钟 > 60 次 | **v0.1（ADR-0003）** |
| `MEMORY_QUERY_TOO_BROAD` | scope=industry + 无过滤 | **v0.1（ADR-0003）** |
| `MEMORY_INTERNAL_ERROR` | MemoryReconciler 内部错误 | **v0.1（ADR-0003）** |
| `MEMORY_AGENT_REF_INVALID` | agentRef SA 不存在 | **v0.1（ADR-0003）** |
| `MEMORY_MAX_ITEMS_EXCEEDED` | cluster > 50K Memory | **v0.1（ADR-0003 §8）** |

---

## 9. 资源默认值（与 v0.1 一致）

### 9.1 Operator

| 资源 | request | limit |
|------|---------|-------|
| CPU | 100m | 1000m |
| Memory | 256Mi | 1Gi |

### 9.2 Adapter

| 资源 | request | limit |
|------|---------|-------|
| CPU | 50m | 500m |
| Memory | 64Mi | 256Mi |

### 9.3 Agent

| 资源 | request | limit |
|------|---------|-------|
| CPU | 100m | 1000m |
| Memory | 256Mi | 1Gi |

### 9.4 任务 / Workflow

| 项 | 默认值 |
|----|--------|
| Agent timeout | 600s |
| Agent max retries | 3 |
| Workflow timeout | 1800s |
| Workflow max retries | 1 |
| Workflow TTL | 86400s (24h) |
| Agent task max_tokens | 50000 |
| Workflow max_tokens | 200000 |
| Workflow max_cost_usd | 5 |

### 9.5 Helm Chart 默认值（与 v0.1 一致 + Python 镜像块）

```yaml
# values.yaml
operator:
  replicaCount: 1
  image:
    repository: ghcr.io/superteam-a2a/operator
    tag: "0.2.0"
    pullPolicy: IfNotPresent
  resources:
    requests: { cpu: 100m, memory: 256Mi }
    limits:   { cpu: 1000m, memory: 1Gi }
  # v0.2 新增：Python 工具链与监控配置
  python:
    runtime: "python:3.12-slim"   # 仅文档标注；实际镜像由 Dockerfile 固定
    workers: 1                    # 强制单 worker
    eventLoopLagThresholdMs: 50   # event-loop lag 告警阈值

knowledgeService:
  replicaCount: 1
  image:
    repository: ghcr.io/superteam-a2a/knowledge-service
    tag: "0.2.0"
  resources:
    requests: { cpu: 200m, memory: 512Mi }
    limits:   { cpu: 1500m, memory: 2Gi }
  memoryReconciler:
    intervalSeconds: 60            # kopf.timer interval
    batchSize: 1000                # 单次 batch reconcile 上限
    gcGraceDays: 7                 # Expired → GC 宽限

resources:
  default:
    requests: { cpu: 100m, memory: 256Mi }
    limits:   { cpu: 1000m, memory: 1Gi }
  adapter:
    requests: { cpu: 50m, memory: 64Mi }
    limits:   { cpu: 500m, memory: 256Mi }

cost:
  agent:
    maxTokens: 50000
    maxDurationSec: 600
    maxRetries: 3
  workflow:
    maxTokens: 200000
    maxCostUsd: 5
    maxDurationSec: 1800
    maxRetries: 1

namespace:
  create: true
  name: superteam-a2a-system
```

---

## 10. 配置 Schema（Helm values.schema.json · 与 v0.1 兼容 + Python 块）

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["operator", "resources", "cost"],
  "properties": {
    "operator": {
      "type": "object",
      "properties": {
        "replicaCount": { "type": "integer", "minimum": 1, "maximum": 5 },
        "resources": { "$ref": "#/definitions/resources" },
        "python": {
          "type": "object",
          "properties": {
            "runtime": { "type": "string", "pattern": "^python:3\\.12" },
            "workers": { "type": "integer", "const": 1 },
            "eventLoopLagThresholdMs": { "type": "integer", "minimum": 10, "maximum": 1000 }
          }
        }
      }
    },
    "knowledgeService": {
      "type": "object",
      "properties": {
        "replicaCount": { "type": "integer", "minimum": 1, "maximum": 5 },
        "resources": { "$ref": "#/definitions/resources" },
        "memoryReconciler": {
          "type": "object",
          "properties": {
            "intervalSeconds": { "type": "integer", "minimum": 10, "maximum": 3600 },
            "batchSize": { "type": "integer", "minimum": 100, "maximum": 10000 },
            "gcGraceDays": { "type": "integer", "minimum": 1, "maximum": 30 }
          }
        }
      }
    },
    "resources": {
      "type": "object",
      "properties": {
        "default": { "$ref": "#/definitions/resources" },
        "adapter": { "$ref": "#/definitions/resources" }
      }
    },
    "cost": {
      "type": "object",
      "properties": {
        "agent": {
          "type": "object",
          "properties": {
            "maxTokens": { "type": "integer", "minimum": 1000 },
            "maxDurationSec": { "type": "integer", "minimum": 1 },
            "maxRetries": { "type": "integer", "minimum": 0, "maximum": 10 }
          }
        },
        "workflow": {
          "type": "object",
          "properties": {
            "maxTokens": { "type": "integer", "minimum": 1000 },
            "maxCostUsd": { "type": "number", "minimum": 0.01 },
            "maxDurationSec": { "type": "integer", "minimum": 1 },
            "maxRetries": { "type": "integer", "minimum": 0, "maximum": 10 }
          }
        }
      }
    }
  },
  "definitions": {
    "resources": {
      "type": "object",
      "required": ["requests", "limits"],
      "properties": {
        "requests": {
          "type": "object",
          "required": ["cpu", "memory"],
          "properties": {
            "cpu": { "type": "string", "pattern": "^([0-9]+m?|[0-9]+\\.[0-9]+)$" },
            "memory": { "type": "string", "pattern": "^[0-9]+(Mi|Gi)$" }
          }
        },
        "limits": {
          "type": "object",
          "required": ["cpu", "memory"],
          "properties": {
            "cpu": { "type": "string", "pattern": "^([0-9]+m?|[0-9]+\\.[0-9]+)$" },
            "memory": { "type": "string", "pattern": "^[0-9]+(Mi|Gi)$" }
          }
        }
      }
    }
  }
}
```

---

## 11. KnowledgeScope CRD（ADR-0002 §2 · wire + Pydantic）

### 11.1 KnowledgeScopeSpec（wire YAML 不变）

```yaml
apiVersion: superteam-a2a.io/v1alpha1
kind: KnowledgeScope
metadata:
  name: team-payments-platform
spec:
  level: team                      # industry / organization / team / project
  displayName: "Payments Platform Team"
  description: "..."
  parentRef:
    name: org-payments             # 必填：team → organization
  ownerRef:
    kind: Group
    name: payments-platform-leads
  inheritRules:
    includeTypes: ["runbook", "faq", "best-practice"]
    excludeTypes: ["draft"]
  labels:
    domain: payments
```

**字段数：6 spec**（ADR-0004 防过度设计约束 ≤15）

**Python Pydantic 表达**：
```python
class ScopeLevel(str, Enum):
    INDUSTRY = "industry"
    ORGANIZATION = "organization"
    TEAM = "team"
    PROJECT = "project"


class ScopeReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)


class SubjectReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str = Field(pattern=r"^(User|Group|ServiceAccount)$")
    name: str = Field(min_length=1, max_length=128)


class InheritRules(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include_types: list[str] | None = Field(None, alias="includeTypes", max_length=11)
    exclude_types: list[str] | None = Field(None, alias="excludeTypes", max_length=11)


class KnowledgeScopeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    level: ScopeLevel
    display_name: str = Field(alias="displayName", min_length=1, max_length=64)
    description: str | None = Field(None, max_length=512)
    parent_ref: ScopeReference | None = Field(None, alias="parentRef")
    owner_ref: SubjectReference = Field(alias="ownerRef")
    inherit_rules: InheritRules | None = Field(None, alias="inheritRules")
    labels: dict[str, str] | None = None
```

### 11.2 KnowledgeScopeStatus（wire 不变）

```python
class ScopePhase(str, Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    ERROR = "Error"
    DELETING = "Deleting"


class KnowledgeScopeStatus(BaseStatus):
    message: str | None = None
    item_count: int = Field(0, ge=0, alias="itemCount")
    child_scopes: int = Field(0, ge=0, alias="childScopes")
```

### 11.3 验证规则（admission webhook 强制 · Python 实现）

| 字段 | 规则 | Python 实现 |
|------|------|-------------|
| `spec.level` | enum: `industry` / `organization` / `team` / `project` | `ScopeLevel` enum |
| `spec.level == industry` | `spec.parentRef == nil` | `model_validator` |
| `spec.level == organization` | `spec.parentRef.name` 必须存在且 `level == industry` | admission webhook |
| `spec.level == team` | `spec.parentRef.name` 必须存在且 `level == organization` | admission webhook |
| `spec.level == project` | `spec.parentRef.name` 必须存在且 `level == team` | admission webhook |
| `spec.parentRef` | 引用的 scope 不能是自身；禁止循环引用 | admission webhook |
| `spec.ownerRef.kind` | enum: `User` / `Group` / `ServiceAccount` | `SubjectReference.kind` enum |
| `spec.displayName` | 1-64 chars | `Field(min_length=1, max_length=64)` |
| `spec.description` | 0-512 chars | `Field(max_length=512)` |

**作用域命名空间约束**：
- `industry` scope：**cluster-scoped**（整个集群共享），最多 1 个实例
- `organization` / `team` / `project` scope：**namespace-scoped**

---

## 12. KnowledgeItem CRD（ADR-0002 §3 · wire + Pydantic）

### 12.1 KnowledgeItemSpec（wire YAML 不变）

```yaml
apiVersion: superteam-a2a.io/v1alpha1
kind: KnowledgeItem
metadata:
  name: refund-failure-handling
spec:
  scopeRef: { name: team-payments-platform }
  type: runbook
  title: "..."
  body: |
    Markdown body, ≤ 64KB
  summary: "..."
  tags: ["payments", "refund"]
  visibility: scope-and-children
  ownerRef:
    kind: User
    name: alice
  sourceURI: "https://..."
  version: 3
  supersededBy: { name: refund-failure-handling-v4 }
  expiryDate: "2027-01-01T00:00:00Z"
  relatedItems:
    - { name: refund-api-spec }
```

**字段数：12 spec**（ADR-0004 约束 ≤15）

**Python Pydantic 表达**：
```python
class KnowledgeType(str, Enum):
    DOCUMENT = "document"
    RUNBOOK = "runbook"
    API_SPEC = "api-spec"
    ARCHITECTURE = "architecture"
    FAQ = "faq"
    BEST_PRACTICE = "best-practice"
    TEMPLATE = "template"
    CONTRACT = "contract"
    TROUBLESHOOTING = "troubleshooting"
    GLOSSARY = "glossary"
    OTHER = "other"


class KnowledgeVisibility(str, Enum):
    SCOPE_ONLY = "scope-only"
    SCOPE_AND_CHILDREN = "scope-and-children"
    PUBLIC_READABLE = "public-readable"
    AGENT_PRIVATE = "agent-private"


class ItemReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    scope: str | None = Field(None, max_length=128)


class KnowledgeItemSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scope_ref: ScopeReference = Field(alias="scopeRef")
    type: KnowledgeType
    title: str = Field(min_length=1, max_length=128)
    body: str = Field(min_length=1, max_length=65536)  # ≤ 64KB
    summary: str | None = Field(None, max_length=512)
    tags: list[str] | None = Field(None, max_length=20)
    visibility: KnowledgeVisibility
    owner_ref: SubjectReference = Field(alias="ownerRef")
    source_uri: str | None = Field(None, alias="sourceURI", max_length=2048)
    version: int = Field(ge=1)
    superseded_by: ItemReference | None = Field(None, alias="supersededBy")
    expiry_date: datetime | None = Field(None, alias="expiryDate")
    related_items: list[ItemReference] | None = Field(None, alias="relatedItems", max_length=50)
```

### 12.2 KnowledgeItemStatus（wire 不变）

```python
class ItemPhase(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    DEPRECATED = "Deprecated"
    EXPIRED = "Expired"
    ERROR = "Error"


class KnowledgeItemStatus(BaseStatus):
    message: str | None = None
    search_indexed: bool = Field(False, alias="searchIndexed")
    last_queried_at: datetime | None = Field(None, alias="lastQueriedAt")
    query_count_30d: int = Field(0, ge=0, alias="queryCount30d")
```

### 12.3 验证规则

| 字段 | 规则 | Python 实现 |
|------|------|-------------|
| `spec.scopeRef.name` | 必须存在对应 KnowledgeScope | admission webhook |
| `spec.type` | enum: 11 个值 | `KnowledgeType` enum |
| `spec.title` | 1-128 chars | `Field(min_length=1, max_length=128)` |
| `spec.body` | 1-65536 chars（≤64KB Markdown） | `Field(min_length=1, max_length=65536)` |
| `spec.summary` | 0-512 chars | `Field(max_length=512)` |
| `spec.tags` | 0-20 items | `Field(max_length=20)` |
| `spec.visibility` | enum: 4 个值 | `KnowledgeVisibility` enum |
| `spec.ownerRef.kind` | **enum: `User` / `Group`**（admission 强制禁止 `ServiceAccount`，与 Memory 互斥） | admission webhook |
| `spec.version` | ≥ 1 | `Field(ge=1)` |
| `spec.sourceURI` | 0-2048 chars | `Field(max_length=2048)` |
| `spec.relatedItems` | 0-50 items | `Field(max_length=50)` |
| `spec.expiryDate` | 未来时间（若填） | admission webhook |

**admission webhook 强制规则**：
- ❌ `visibility == agent-private` 且 `ownerRef.kind == ServiceAccount` —— **KnowledgeItem 不允许 agent-private**（v0.1）
- ❌ `visibility == public-readable` 且 `spec.scopeRef.level != industry` —— public-readable 仅限 industry scope
- ❌ `body` 超过 64KB 拒绝

---

## 13. Memory CRD（ADR-0003 §2 · wire + Pydantic）

### 13.1 MemorySpec（wire YAML 不变）

```yaml
apiVersion: superteam-a2a.io/v1alpha1
kind: Memory
metadata:
  name: team-payments-platform/credit-card-refund-retry-strategy
spec:
  scopeRef: { name: team-payments-platform }
  agentRef:
    name: refund-analyzer
  content:
    pattern: "credit-card-refund-fail-retry-3x"
    outcome: "success-after-2nd-retry"
    duration: "8.5s"
  summary: "信用卡退款失败时，重试 3 次成功率最高"
  confidence: 0.55
  decayDays: 30
  reinforcedCount: 2
  visibility: scope-and-children
  memoryKey: "credit-card-refund-retry-strategy"
  sourceKnowledgeRef:
    name: refund-failure-handling
  tags: ["payments", "refund"]
```

**字段数：12 spec**（ADR-0004 约束 ≤15）

**Python Pydantic 表达**：
```python
class MemoryVisibility(str, Enum):
    SCOPE_ONLY = "scope-only"
    SCOPE_AND_CHILDREN = "scope-and-children"
    AGENT_PRIVATE = "agent-private"  # 注意：3 枚举，无 public-readable


class AgentReference(BaseModel):
    """schema 硬编码 ServiceAccount（admission 强制）。"""

    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    namespace: str | None = Field(None, max_length=64)


class MemorySpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scope_ref: ScopeReference = Field(alias="scopeRef")
    agent_ref: AgentReference = Field(alias="agentRef")
    content: dict[str, str] = Field(min_length=1, max_length=20)  # 1-20 keys
    summary: str = Field(min_length=1, max_length=256)
    confidence: float = Field(ge=0.0, le=1.0)
    decay_days: int = Field(alias="decayDays", ge=0, le=3650)
    reinforced_count: int = Field(alias="reinforcedCount", ge=0)
    visibility: MemoryVisibility
    memory_key: str | None = Field(None, alias="memoryKey", max_length=128)
    source_knowledge_ref: ItemReference | None = Field(None, alias="sourceKnowledgeRef")
    tags: list[str] | None = Field(None, max_length=20)
```

### 13.2 MemoryStatus（wire 不变）

```python
class MemoryPhase(str, Enum):
    ACTIVE = "Active"
    DECAYING = "Decaying"
    PROMOTABLE = "Promotable"
    EXPIRED = "Expired"
    ERROR = "Error"


class MemoryStatus(BaseStatus):
    message: str | None = None
    last_decayed_at: datetime | None = Field(None, alias="lastDecayedAt")
    last_reinforced_at: datetime | None = Field(None, alias="lastReinforcedAt")
    effective_confidence: float = Field(0.0, ge=0.0, le=1.0, alias="effectiveConfidence")
    eligible_for_promotion: bool = Field(False, alias="eligibleForPromotion")
```

### 13.3 验证规则

| 字段 | 规则 | Python 实现 |
|------|------|-------------|
| `spec.scopeRef.name` | 必须存在对应 KnowledgeScope | admission webhook |
| `spec.agentRef.name` | 必须存在对应 ServiceAccount | admission webhook |
| `spec.agentRef.namespace` | 若填，必须是有效 namespace 名 | K8s API 校验 |
| `spec.content` | 1-20 个 key-value pair | `Field(min_length=1, max_length=20)` |
| `spec.summary` | 1-256 chars | `Field(min_length=1, max_length=256)` |
| `spec.confidence` | 0.0-1.0 | `Field(ge=0.0, le=1.0)` |
| `spec.decayDays` | 0-3650 | `Field(ge=0, le=3650)` |
| `spec.reinforcedCount` | ≥ 0 | `Field(ge=0)` |
| `spec.visibility` | enum: 3 个值（**不包含 public-readable**） | `MemoryVisibility` enum |
| `spec.memoryKey` | 0-128 chars | `Field(max_length=128)` |
| `spec.sourceKnowledgeRef.scope` | 必须等于 `spec.scopeRef.name`（admission 强制同 scope） | admission webhook |
| `spec.tags` | 0-20 items | `Field(max_length=20)` |

**admission webhook 强制规则**（与 ADR-0002 §6.3 双向互斥）：
- ❌ `agentRef` schema 硬编码 ServiceAccount（双重校验：K8s type validation + admission）
- ❌ `visibility == agent-private` 且 `agentRef.name == ""` —— 禁止
- ❌ `sourceKnowledgeRef` 指向的 KnowledgeItem 不存在 —— 拒绝

**finalizer**：`memory.superteam-a2a.io/cleanup` —— GC 阶段保护（Kopf `@kopf.on.finalize`）

---

## 14. 5 维可见性矩阵 + 算法（wire 语义不变 · Python 实现）

### 14.1 4 级作用域继承算法

```python
async def resolve_effective_scopes(
    scope_name: str, k8s: kubernetes_asyncio.client.CoreV1Api
) -> list[KnowledgeScope]:
    """返回从最顶层（industry）到当前 scope 的完整继承链（异步）。"""
    chain: list[KnowledgeScope] = []
    current: KnowledgeScope | None = await k8s.get_knowledge_scope(scope_name)
    while current is not None:
        chain.insert(0, current)
        if current.spec.parent_ref is None:
            break
        current = await k8s.get_knowledge_scope(current.spec.parent_ref.name)
    return chain
```

**复杂度**：O(深度)，最坏 4 层

### 14.2 Knowledge 可见性过滤（4 种 visibility）

| visibility \ scope | industry | organization | team | project |
|---|---|---|---|---|
| `scope-only` | 仅 industry scope | 仅 org scope | 仅 team scope | 仅 project scope |
| `scope-and-children` | industry + 所有子 | org + 所有子 | team + 所有子 | 仅 project |
| `public-readable` | 整个集群 | ❌ 不允许 | ❌ 不允许 | ❌ 不允许 |
| `agent-private`（v0.1 禁用） | — | — | — | — |

**Knowledge 查询算法**：
```python
async def query_knowledge(
    scope: str,
    query: str,
    type_filter: list[KnowledgeType] | None = None,
    tag_filter: list[str] | None = None,
    max_results: int = 10,
) -> list[KnowledgeItemSummary]:
    chain = await resolve_effective_scopes(scope, k8s)
    results = []
    for s in chain:
        items = await list_knowledge_items_in_scope(s, type_filter, tag_filter)
        for item in items:
            if not is_inherit_allowed(s, item):
                continue
            if not check_knowledge_visibility(scope, item):
                continue
            results.append(item)
    deduped = dedupe_by_id_keep_latest(results)
    scored = await bm25_score(deduped, query)  # anyio.to_thread.run_sync if needed
    return scored[:max_results]
```

### 14.3 Memory 5 维可见性矩阵（4 scope × agent-private 正交）

| visibility \ scope | industry | organization | team | project |
|---|---|---|---|---|
| `scope-only` | 仅 industry scope | 仅 org scope | 仅 team scope | 仅 project scope |
| `scope-and-children`（默认） | industry + 所有子 | org + 所有子 | team + 所有子 | 仅 project |
| `agent-private` | **仅 owner agent** | **仅 owner agent** | **仅 owner agent** | **仅 owner agent** |

**注意**：Memory 不可使用 `public-readable`（与 KnowledgeItem 互斥）

**Memory 可见性算法**：
```python
def is_memory_visible_to(
    memory: Memory, caller_agent: str, caller_scope_chain: list[KnowledgeScope]
) -> bool:
    # 规则 1：agent-private 短路
    if memory.spec.visibility == MemoryVisibility.AGENT_PRIVATE:
        return memory.spec.agent_ref.name == caller_agent
    # 规则 2：scope 继承
    if memory.spec.visibility == MemoryVisibility.SCOPE_ONLY:
        return memory.spec.scope_ref.name == caller_scope_chain[-1].name
    if memory.spec.visibility == MemoryVisibility.SCOPE_AND_CHILDREN:
        return memory.spec.scope_ref.name in [s.name for s in caller_scope_chain]
    return False


async def query_memory(
    scope: str,
    caller_agent: str,
    confidence_min: float | None = None,
    memory_key_pattern: str | None = None,
    tag_filter: list[str] | None = None,
    max_results: int = 20,
) -> list[Memory]:
    caller_chain = await resolve_effective_scopes(scope, k8s)
    all_memories = await list_all_memories(confidence_min, memory_key_pattern, tag_filter)
    visible = [m for m in all_memories if is_memory_visible_to(m, caller_agent, caller_chain)]
    return visible[:max_results]
```

**完整组合表**（4 scope × 3 visibility = 12 种）：

| # | visibility | scope | 可见范围 |
|---|---|---|---|
| 1 | scope-only | industry | industry scope 直接成员 |
| 2 | scope-only | organization | org scope 直接成员 |
| 3 | scope-only | team | team scope 直接成员 |
| 4 | scope-only | project | project scope 直接成员 |
| 5 | scope-and-children | industry | industry + 所有 org + 所有 team + 所有 project |
| 6 | scope-and-children | organization | org + 所有 team + 所有 project |
| 7 | scope-and-children | team | team + 所有 project |
| 8 | scope-and-children | project | project（无子） |
| 9 | agent-private | industry | 仅 owner agent（无视 scope） |
| 10 | agent-private | organization | 仅 owner agent |
| 11 | agent-private | team | 仅 owner agent |
| 12 | agent-private | project | 仅 owner agent |

### 14.4 decay 算法（数学公式 · wire 不变）

```python
import math
from datetime import datetime, timezone


def apply_decay(memory: Memory, now: datetime) -> float:
    if memory.spec.decay_days <= 0:
        return memory.spec.confidence
    last_update = max(
        memory.status.last_decayed_at or memory.metadata.creation_timestamp,
        memory.status.last_reinforced_at or memory.metadata.creation_timestamp,
    )
    elapsed_days = (now - last_update).total_seconds() / 86400.0
    decay_rate = elapsed_days / memory.spec.decay_days
    effective = memory.spec.confidence * math.exp(-decay_rate)
    return max(0.0, min(1.0, effective))
```

**公式**：`effectiveConfidence = confidence × exp(-elapsed_days / decayDays)`

**边界值**：
- `decayDays == 0` → 不衰减，effective = confidence
- `elapsed_days == 0` → effective = confidence
- `elapsed_days == decayDays` → effective = confidence × e⁻¹ ≈ confidence × 0.368
- `elapsed_days == 2 × decayDays` → effective ≈ confidence × 0.135
- `elapsed_days == 3 × decayDays` → effective ≈ confidence × 0.050（< 0.1 → phase=Expired）

**示例**（confidence=1.0, decayDays=30）：
| 天数 | effective | phase |
|---|---|---|
| 0 | 1.000 | Active |
| 15 | 0.607 | Active |
| 30 | 0.368 | Decaying |
| 60 | 0.135 | Decaying |
| 90 | 0.050 | Expired（7 天后 GC） |

### 14.5 reinforce 算法

```python
def apply_reinforce(memory: Memory, now: datetime) -> Memory:
    new_confidence = min(1.0, memory.spec.confidence + 0.05)
    new_count = memory.spec.reinforced_count + 1
    memory.spec.confidence = new_confidence
    memory.spec.reinforced_count = new_count
    memory.status.last_reinforced_at = now
    memory.status.effective_confidence = new_confidence  # decay 重启
    memory.status.last_decayed_at = now
    return memory
```

**关键不变量**：
- `reinforcedCount` **单调递增**（admission 强制）
- `confidence <= 1.0`（reinforce 上限）
- reinforce 同时重启 decay 时钟（`lastDecayedAt = now`）

**去重键逻辑**：
- `recordMemory` 带 `memoryKey` 时：
  - 查询同 `(memoryKey, scopeRef, agentRef)` 三元组
  - 存在 → reinforce
  - 不存在 → 创建新 Memory
- `memoryKey == ""` → 每次 recordMemory 创建新 Memory（无 reinforce）

### 14.6 eligibleForPromotion 触发条件（v0.1 仅计算）

```python
def is_eligible_for_promotion(memory: Memory) -> bool:
    return (
        memory.spec.visibility == MemoryVisibility.SCOPE_AND_CHILDREN
        and memory.status.effective_confidence >= 0.85
        and memory.spec.reinforced_count >= 5
    )
```

**v0.1 行为**：仅计算并填充 `status.eligible_for_promotion`，**不触发** KnowledgePromotionRequest（v0.5+ 范畴）。

### 14.7 Memory batch reconcile 性能（Python 特定）

- 单次 reconcile ≤ 1000 items（`asyncio.Semaphore(1000)` 控制并发）
- `apply_decay` 是纯函数；批量计算通过 `anyio.to_thread.run_sync(partial(apply_decay, ...))` offload 到线程池
- 线程池固定容量（默认 8 workers），超过排队由 `thread_offload_queue_depth` 指标监控

---

## 15. A2A Method 详细 Schema（v0.1 · wire 不变 · Python Pydantic）

> **对应 L2 模块**：✅ **L2-1 A2A Protocol v0.2.0**（Python 重写 · 2026-07-24 评审通过；4 个项目扩展 method 由 L2-1 Spec v0.2.0 §8 文件级契约负责，详见 [`docs/spec/L2-module-specs/L2-a2a-protocol.md`](./L2-module-specs/L2-a2a-protocol.md) + [评审](../reviews/l2-1-a2a-protocol-review.md)）

### 15.1 `a2a.queryKnowledge`（ADR-0002 §5.1）

**Request**（A2A Message `data`）：
```json
{
  "scope": "team-payments-platform",
  "query": "如何处理信用卡退款失败？",
  "typeFilter": ["runbook", "troubleshooting"],
  "tagFilter": ["payments", "refund"],
  "maxResults": 10
}
```

**Python Pydantic Schema**：
```python
class QueryKnowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scope: str = Field(min_length=1, max_length=128)
    query: str = Field(min_length=1, max_length=512)
    type_filter: list[KnowledgeType] | None = Field(None, alias="typeFilter", max_length=11)
    tag_filter: list[str] | None = Field(None, alias="tagFilter", max_length=20)
    max_results: int | None = Field(10, alias="maxResults", ge=1, le=50)


class KnowledgeItemSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    scope: str
    type: KnowledgeType
    title: str
    summary: str | None = None
    version: int = Field(ge=1)
    relevance_score: float = Field(ge=0.0, le=1.0, alias="relevanceScore")


class QueryKnowledgeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[KnowledgeItemSummary]
    total_count: int = Field(ge=0, alias="totalCount")
```

**错误码**：`KNOWLEDGE_SCOPE_NOT_FOUND` / `KNOWLEDGE_QUERY_TOO_LONG` / `KNOWLEDGE_INVALID_TYPE` / `KNOWLEDGE_INTERNAL_ERROR`

### 15.2 `a2a.getKnowledgeItem`（ADR-0002 §5.2）

**Request**：
```json
{ "name": "refund-failure-handling", "version": 3 }
```

**Python Schema**：
```python
class GetKnowledgeItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    version: int | None = Field(None, ge=1)


# Response：直接复用 KnowledgeItem（含 body / tags / sourceURI / ownerRef / relatedItems）
class GetKnowledgeItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item: KnowledgeItem  # 完整详情
```

**错误码**：`KNOWLEDGE_ITEM_NOT_FOUND` / `KNOWLEDGE_VERSION_NOT_FOUND` / `KNOWLEDGE_FORBIDDEN`

### 15.3 `a2a.recordMemory`（ADR-0003 §5.1）

**Request**：
```json
{
  "scope": "team-payments-platform",
  "content": {"pattern": "...", "outcome": "...", "duration": "8.5s"},
  "summary": "...",
  "memoryKey": "credit-card-refund-retry-strategy",
  "visibility": "scope-and-children",
  "sourceKnowledgeRef": { "name": "refund-failure-handling" },
  "tags": ["payments", "refund"]
}
```

**Python Schema**：
```python
class RecordMemoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scope: str = Field(min_length=1, max_length=128)
    content: dict[str, str] = Field(min_length=1, max_length=20)
    summary: str = Field(min_length=1, max_length=256)
    memory_key: str | None = Field(None, alias="memoryKey", max_length=128)
    visibility: MemoryVisibility
    source_knowledge_ref: ItemReference | None = Field(None, alias="sourceKnowledgeRef")
    tags: list[str] | None = Field(None, max_length=20)


class RecordMemoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    memory_id: str = Field(alias="memoryId", min_length=1, max_length=192)
    confidence: float = Field(ge=0.0, le=1.0)
    decay_days: int = Field(alias="decayDays", ge=0, le=3650)
    phase: MemoryPhase
    reinforced_count: int = Field(alias="reinforcedCount", ge=0)
    effective_confidence: float = Field(alias="effectiveConfidence", ge=0.0, le=1.0)
    created_at: datetime = Field(alias="createdAt")
```

**错误码**：`MEMORY_SCOPE_NOT_FOUND` / `MEMORY_INVALID_CONTENT` / `MEMORY_FORBIDDEN` / `MEMORY_RATE_LIMIT` / `MEMORY_INTERNAL_ERROR`

### 15.4 `a2a.queryMemory`（ADR-0003 §5.2）

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

**Python Schema**：
```python
class QueryMemoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    scope: str = Field(min_length=1, max_length=128)
    confidence_min: float | None = Field(None, alias="confidenceMin", ge=0.0, le=1.0)
    memory_key_pattern: str | None = Field(None, alias="memoryKeyPattern", max_length=128)
    tag_filter: list[str] | None = Field(None, alias="tagFilter", max_length=20)
    max_results: int | None = Field(20, alias="maxResults", ge=1, le=100)


class MemorySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str
    scope: str
    agent: str
    summary: str
    content: dict[str, str]
    confidence: float
    effective_confidence: float = Field(alias="effectiveConfidence")
    reinforced_count: int = Field(alias="reinforcedCount", ge=0)
    visibility: MemoryVisibility
    phase: MemoryPhase
    age: str  # human-readable, e.g. "5d"
    tags: list[str] | None = None
    source_knowledge_ref: ItemReference | None = Field(None, alias="sourceKnowledgeRef")


class QueryMemoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    memories: list[MemorySummary]
    total_count: int = Field(ge=0, alias="totalCount")
```

**错误码**：`MEMORY_SCOPE_NOT_FOUND` / `MEMORY_FORBIDDEN` / `MEMORY_QUERY_TOO_BROAD` / `MEMORY_INTERNAL_ERROR`

---

## 16. Prometheus 指标（与 v0.1 一致 + Python runtime 4 个新指标）

> **对应 L2 模块**（指标归属）：
> - **§16.1 Operator / §16.3 Agent / §16.4 Workflow / §16.5 Knowledge / §16.6 Memory / §16.7 Python runtime** — 由对应 L2 模块负责（C-1 Operator / C-2 A2A Core / C-3 Adapter SDK / 等）
> - **§16.2 A2A 指标** — ✅ **L2-1 A2A Protocol v0.2.0**（Python 重写 · 2026-07-24 通过；metric name 与 L2-1 Spec v0.2.0 §9.1 完全一致，详见 [`docs/spec/L2-module-specs/L2-a2a-protocol.md`](./L2-module-specs/L2-a2a-protocol.md)）

**命名规范**：`superteam_<component>_<metric>_<unit>_<suffix>`

### 16.1 Operator 指标（与 v0.1 一致）

> **对应 L2 模块**：✅ **L2-2 Operator Core v0.2.0**（Python 重写 · 2026-07-24 评审通过；11 个 Operator metric name 与 L2-2 Spec v0.2-draft §10.1 完全一致，详见 [`docs/design/L2-modules/L2-operator-core.md`](../design/L2-modules/L2-operator-core.md) + [评审](../reviews/l2-2-operator-core-python-review.md)）
> **对应 L3 文件级**：✅ **L3-1 Operator Core 文件级 Spec v0.2.0**（2026-07-28 #56 评审通过 · 11 Operator + 4 Python runtime metric name 与 L3-1 Spec v0.2.0 §7.1.2 完全一致，详见 [`docs/spec/L3-file-specs/L3-operator-core.md`](./L3-file-specs/L3-operator-core.md) + [评审](reviews/l3-1-operator-core-spec-review.md)）

| 指标名 | 类型 | Labels | 含义 |
|--------|------|--------|------|
| `superteam_operator_reconcile_total` | Counter | `crd`, `result` | reconcile 调用总数 |
| `superteam_operator_reconcile_duration_seconds` | Histogram | `crd` | reconcile 延迟 |
| `superteam_operator_leader_election` | Gauge | — | 0/1 是否当前 leader |

### 16.2 A2A 指标（与 v0.1 一致）

| 指标名 | 类型 | Labels | 含义 |
|--------|------|--------|------|
| `superteam_a2a_rpc_total` | Counter | `agent`, `method`, `status` | A2A RPC 调用 |
| `superteam_a2a_rpc_duration_seconds` | Histogram | `agent`, `method` | RPC 延迟 |
| `superteam_a2a_active_streams` | Gauge | — | 活跃 SSE 流 |

### 16.3 Agent 指标（与 v0.1 一致）

| 指标名 | 类型 | Labels | 含义 |
|--------|------|--------|------|
| `superteam_agent_pod_resource_usage` | Gauge | `agent`, `resource` | Pod 资源使用 |
| `superteam_agent_token_total` | Counter | `agent`, `model`, `type` | Token 消耗 |
| `superteam_agent_invocations_total` | Counter | `agent`, `result` | 调用总数 |

### 16.4 Workflow 指标（与 v0.1 一致）

| 指标名 | 类型 | Labels | 含义 |
|--------|------|--------|------|
| `superteam_workflow_active` | Gauge | `namespace` | 活跃 workflow 数 |
| `superteam_workflow_duration_seconds` | Histogram | `workflow` | workflow 延迟 |
| `superteam_workflow_tasks_total` | Counter | `workflow`, `status` | task 执行数 |

### 16.5 Knowledge 指标（ADR-0002 §9.4）

| 指标名 | 类型 | Labels | 含义 |
|--------|------|--------|------|
| `superteam_knowledge_query_total` | Counter | `scope`, `type`, `result` | queryKnowledge 调用 |
| `superteam_knowledge_query_duration_seconds` | Histogram | `scope`, `type` | 延迟 |
| `superteam_knowledge_items_total` | Gauge | `scope`, `type`, `phase` | KnowledgeItem 总数 |
| `superteam_knowledge_search_index_size` | Gauge | — | 倒排索引条目数 |

### 16.6 Memory 指标（ADR-0003 §9.4）

| 指标名 | 类型 | Labels | 含义 |
|--------|------|--------|------|
| `superteam_memory_record_total` | Counter | `scope`, `agent`, `result` | recordMemory 调用 |
| `superteam_memory_query_total` | Counter | `scope`, `visibility`, `result` | queryMemory 调用 |
| `superteam_memory_decay_total` | Counter | `phase_from`, `phase_to` | 状态机迁移 |
| `superteam_memory_reconcile_duration_seconds` | Histogram | — | reconcile 延迟 |
| `superteam_memory_eligible_for_promotion_total` | Counter | `scope` | eligible 字段填充 |
| `superteam_memory_total` | Gauge | `scope`, `phase` | Memory 总数 |

### 16.7 Python runtime 新增指标（v0.2 新增 · ADR-0005 §10）

| 指标名 | 类型 | Labels | 含义 |
|--------|------|--------|------|
| `superteam_python_event_loop_lag_seconds` | Histogram | `component` | event loop 阻塞检测 |
| `superteam_python_thread_offload_queue_depth` | Gauge | `pool` | anyio 线程池队列深度 |
| `superteam_python_active_asyncio_tasks` | Gauge | — | 活跃 asyncio task 数 |
| `superteam_python_gc_collections_total` | Counter | `generation` | GC 触发计数 |

> **关键约束**（ADR-0005 §10）：Python runtime 指标**不重定义既有指标语义**，仅作为 Python 部署特有的可观测增强。

### 16.8 必含字段（结构化日志 · `structlog`）

所有 Knowledge / Memory 相关日志必须包含：
- `trace_id`
- `caller_agent`（Knowledge 调用方 SA 名 / Memory owner SA 名）
- `scope`
- `memory_key`（Memory）或 `item_name`（Knowledge）
- `event` / `level` / `timestamp`（`structlog` 标准）

---

## 17. 验收清单（v0.2 · Python-first · 扩展 §17）

> L1 v0.2 Spec 被认定为"通过"必须满足

### 17.1 业务语义（与 v0.1 Go baseline 完全一致）

- [x] 所有 CRD 字段有 Pydantic BaseModel 定义（wire alias 保留 camelCase）
- [x] **6 个 CRD 字段有 Pydantic 定义**（Agent / AgentSet / Workflow / KnowledgeScope / KnowledgeItem / Memory）
- [x] 所有 CRD 字段有验证规则（`Field(...)` 约束 + admission webhook）
- [x] **每个 CRD spec 字段数 ≤ 15**（ADR-0004 防过度设计）
- [x] **3 个新 CRD 的 admission webhook 校验规则完整**（Knowledge ↔ Memory 双向互斥）
- [x] DAG 校验规则明确（`WorkflowValidator.validate_dag` 纯函数 + Kahn/DFS）
- [x] A2A 协议 JSON 结构可解析（官方 a2a-sdk 标准类型）
- [x] **6 个 A2A method 的完整 Pydantic Schema**（含 4 个项目扩展：queryKnowledge / getKnowledgeItem / recordMemory / queryMemory）
- [x] JSON-RPC 错误码与 HTTP 状态码映射完整
- [x] **错误码包含 KNOWLEDGE_*（7 个）+ MEMORY_*（6 个）**
- [x] 状态机清晰（Agent / Workflow / Task / KnowledgeScope / KnowledgeItem / Memory）
- [x] 错误模型完整（响应格式 + 错误代码）
- [x] 资源默认值完整（含 **Knowledge Service + MemoryReconciler 共享 Deployment**）
- [x] Helm values schema 完整（含 **operator.python + knowledgeService.memoryReconciler 配置块**）
- [x] **5 维可见性矩阵 Python 实现 + 12 种组合表**（详见 §14）
- [x] **decay/reinforce 算法 Python 实现 + 边界值**（详见 §14）
- [x] **10 个新 Prometheus 指标 + 4 个 Python runtime 新指标**（详见 §16）

### 17.2 Python-first 硬约束（ADR-0005 + 宪法 v0.5.0）

- [x] **wire contract 与 v0.1 完全一致**（YAML / JSON 字段名、错误码、Agent Card path、Task FSM、metric name）
- [x] **Pydantic v2 strict**（禁止未解释 `Any` 穿过公共边界）
- [x] **wire alias 单向原则**（§1.6）：camelCase wire + snake_case Python
- [x] **官方 a2a-sdk 复用 + compatibility adapter**（`superteam_a2a.a2a.upstream` 边界）
- [x] **async-first**：K8s I/O / A2A HTTP / webhook / OTel exporter 全部 async
- [x] **CPU offload**：`anyio.to_thread.run_sync` 用于 BM25 / batch decay / 重计算
- [x] **单进程原则**：Uvicorn 单 worker / 单 event loop（Helm values `python.workers: 1` 强制）
- [x] **timezone-aware UTC**：所有 datetime 字段一律 `datetime.now(timezone.utc)`
- [x] **Pydantic → JSON Schema 2020-12 → CRD OpenAPI v3** 确定性生成（CI 验证无 diff）
- [x] **uv.lock 必须提交**；CI 使用 `uv sync --frozen`
- [x] **Python 静态门禁**（CI 必跑）：Ruff format/lint + Pyright strict + Bandit + pip-audit
- [x] **Python 镜像双层扫描**：Bandit + pip-audit + Trivy + Cosign
- [x] **Python 镜像非 root + read-only rootfs + drop all capabilities**
- [x] **撤销既有类型注解中的 Go 字眼**（无 `+kubebuilder:validation:` 残留；类型层不再出现 `map[string]string` Go 风格注释）

### 17.3 与其他文档一致性

- [x] 与 L1 Architecture v0.2.0 一致
- [x] 与宪法 v0.5.0 无冲突（§3.8 / §9.7 / §10.3 / §13.6）
- [x] 与 5 个 ADR 一致（ADR-0001 / 0002 / 0003 / 0004 / 0005）
- [x] MVP 例外 §14.5 显式声明（v0.1 阶段适用）

---

## 附录 A: 术语表

| 术语 | 定义 |
|------|------|
| **A2A** | Agent-to-Agent Protocol，Google 主推的 Agent 通信协议 |
| **MCP** | Model Context Protocol，Anthropic 主推的 Agent-Tool 连接协议 |
| **Adapter** | superteam-a2a 与各 Agent 框架之间的薄薄一层（`typing.Protocol` 实现） |
| **Agent Card** | A2A 协议规定的 Agent 能力描述 JSON（官方 `a2a-sdk.AgentCard`） |
| **AgentSet** | 同质 Agent 集群 CRD（类似 Deployment for Agents） |
| **Workflow** | 多 Agent 协作的 DAG 编排 CRD |
| **Operator** | Python + Kopf 实现的 Kubernetes Operator |
| **Kopf** | Python Kubernetes Operator 框架 |
| **`kubernetes_asyncio`** | K8s 官方 Python 客户端的 asyncio 适配 |
| **官方 a2a-sdk** | google-a2a/a2a-python 仓库提供的 A2A Python SDK |
| **compatibility adapter** | 项目自有层与官方 SDK 之间的边界（`superteam_a2a.a2a.upstream`） |
| **CRD** | Custom Resource Definition，自定义资源 |
| **Pydantic v2** | Python 类型 + 校验基础；CRD/JSON Schema 单一来源 |
| **uv** | Astral 提供的 Python workspace + lock 工具 |
| **Sidecar** | 与 Agent 同 Pod 部署的 Adapter 容器 |
| **DAG** | 有向无环图 |
| **JSON-RPC** | JSON-RPC 2.0 协议 |
| **traceparent** | W3C Trace Context header |
| **RBAC** | K8s Role-Based Access Control |
| **mTLS** | Mutual TLS（Python `ssl.SSLContext` + URI SAN SPIFFE） |
| **SPIFFE** | Secure Production Identity Framework for Everyone |
| **distroless** | 极简 Docker 基础镜像 |
| **cosign** | OCI 签名工具 |
| **SemVer** | 语义化版本 |
| **MVP** | Minimum Viable Product |
| **ASGI / Uvicorn** | Python 异步 HTTP 服务器；单 worker / 单 event loop |
| **Tenacity** | Python 重试库 |
| **`anyio.to_thread.run_sync`** | 阻塞 CPU 工作 offload 到线程池 |
| **`structlog`** | Python 结构化日志库 |
| **JSON Schema 2020-12** | Pydantic 默认输出；转 Kubernetes OpenAPI v3 |

---

## 附录 B: 兼容性矩阵

| 组件 | v0.1.0 (Go) | v0.2.0 (Python) | v0.5.0 | v1.0.0 |
|------|-------------|------------------|--------|--------|
| Agent CRD | v1alpha1 | **v1alpha1（wire 不变）** | v1beta1 | v1 |
| AgentSet CRD | v1alpha1 | **v1alpha1（wire 不变）** | v1beta1 | v1 |
| Workflow CRD | v1alpha1 | **v1alpha1（wire 不变）** | v1beta1 | v1 |
| KnowledgeScope CRD | v1alpha1 | **v1alpha1（wire 不变）** | v1beta1 | v1 |
| KnowledgeItem CRD | v1alpha1 | **v1alpha1（wire 不变）** | v1beta1 | v1 |
| Memory CRD | v1alpha1 | **v1alpha1（wire 不变）** | v1beta1 | v1 |
| A2A Protocol | v0.3 core | **v0.3 core（wire 不变）** | v0.3 + SSE | v0.3 full |
| A2A method 数 | 6 | **6（含 4 项目扩展，wire 不变）** | 8 | 完整 |
| K8s | 1.28+ | **1.28+** | 1.29+ | 1.30+ |
| Operator 实现 | Go 1.22+ | **Python 3.12+ / Kopf** | — | — |
| A2A Core 实现 | 自研 Go | **官方 a2a-sdk + adapter** | — | — |
| Adapter 实现 | Go | **Python** | — | — |
| 类型层 | Go struct | **Pydantic v2 strict** | — | — |
| Helm | 3.12+ | **3.12+** | 3.14+ | 3.16+ |
| Prometheus | 2.45+ | **2.45+** | 2.50+ | 2.55+ |
| OTel | 1.27+ | **OTel Python SDK** | — | — |
| 静态门禁 | go vet / golangci-lint | **Ruff / Pyright strict / Bandit / pip-audit** | — | — |
| 镜像基线 | distroless | **`python:3.12-slim` 多阶段** | — | — |
| 性能目标 | Go 1.22+ 基线 | **Python 性能预算表（§11.5）** | — | — |

---

## 附录 C: 与 L1 Architecture 对应

| L1 Spec 章节 | L1 Architecture 章节 |
|--------------|----------------------|
| §1 CRD 通用约定 | §3.3 资源模型层 |
| §2 Agent CRD | §5 CRD 模型 |
| §3 AgentSet CRD | §5 CRD 模型 |
| §4 Workflow CRD | §5 CRD 模型 |
| §11 KnowledgeScope CRD | §3.3 资源模型层 + §5.4 |
| §12 KnowledgeItem CRD | §3.3 资源模型层 + §5.4 |
| §13 Memory CRD | §3.3 资源模型层 + §5.4 |
| §5 A2A 协议 | §7 A2A 协议集成 |
| §6 REST 端点 | §4 通信层 |
| §7 状态机 | §3.2 编排层 |
| §8 错误模型 | §8 数据流 / 失败处理 |
| §9 资源默认值 | §11 资源模型 |
| §10 Helm schema | §12 部署架构 |
| §14 5 维可见性矩阵 + 算法 | §3.4 + ADR-0002 §2.4 + ADR-0003 §3 |
| §15 A2A Method 详细 JSON Schema | §7.4 + ADR-0002 §5 + ADR-0003 §5 |
| §16 Prometheus 指标 | §9.1 + ADR-0002 §9.4 + ADR-0003 §9.4 |
| **§16.7 Python runtime 指标**（v0.2 新增） | **§3.6 横切关注点 + ADR-0005 §10** |

---

> **状态**：✅ **v0.2.0 已评审通过**（2026-07-24，依据 [`docs/reviews/l1-python-stack-migration-review.md`](../reviews/l1-python-stack-migration-review.md) §A-§F + ADR-0005 + 宪法 v0.5.0；10 维度全 PASS + 35 项验收清单全部勾选）
> **supersedes**：v0.1.0 Go baseline（仅 supersede Go struct / kubebuilder annotation / controller-runtime reconcile 实现条款；wire contract 与业务语义继续有效）
> **下一步**：✅ L2-1 v0.2.0（2026-07-24）→ ✅ L2-2 v0.2.0（2026-07-25）→ ✅ L2-3 v0.2.0（2026-07-26）→ ✅ L2-4 v0.2.0（2026-07-27 #43）→ 归档 L3 Go draft → 重写 Python L3 → 初始化 uv workspace → L4 实现
> **L2 阶段进度**：✅ **L2-4/4 完成**（L2-1 + L2-2 + L2-3 + L2-4 全部 v0.2.0 Python 评审通过；§11-§14 wire contract 与 [L2-4 Spec v0.2.0](./L2-module-specs/L2-knowledge-memory.md) §3 Pydantic v2 CRD 严格一致）
> **评审者**：项目发起人（基于单人维护者 + MVP 例外 14.5 单点评审）
> **变更摘要**（2026-07-24 · v0.1 → v0.2 增量）：
> - **wire 锁定**：所有 CRD YAML / A2A JSON / 错误码 / 状态机 / metric name 完全不变
> - **类型层**：Go struct + `+kubebuilder:validation:` → **Pydantic v2 BaseModel + `Field(...)` + `populate_by_name` + alias**
> - **CRD 生成**：kubebuilder controller-gen → **Pydantic JSON Schema 2020-12 → 确定性 OpenAPI v3**
> - **Status 写回**：controller-runtime → **Kopf `@kopf.adopt(status_patch=...)`**
> - **A2A**：自研 Go + envelope → **官方 a2a-sdk + 项目 extension router（4 method）**
> - **HTTP**：net/http → **ASGI + Uvicorn 单 worker**
> - **HTTP client**：→ **httpx.AsyncClient**
> - **错误码**：新增 §5.7 + §8.3 错误码表（含 13 个 KNOWLEDGE_* + MEMORY_*）
> - **新增** §1.6 wire alias 单向原则（camelCase wire + snake_case Python + timezone-aware UTC）
> - **新增** §3.5 Pydantic 完整示例（AgentCard / Framework / AgentSpec 等）
> - **新增** §9.5 Helm values Python 镜像块（operator.python + knowledgeService.memoryReconciler）
> - **新增** §10 values.schema.json Python 块（runtime / workers / eventLoopLagThresholdMs）
> - **新增** §13.1 MemorySpec 完整 Pydantic
> - **新增** §14.7 Memory batch reconcile 性能（Python Semaphore + anyio offload）
> - **新增** §15 完整 Pydantic Schema（4 个项目扩展 method 的 Request/Response）
> - **新增** §16.7 Python runtime 4 个新指标 + §16.8 structlog 必含字段
> - **新增** §17.2 Python-first 硬约束验收清单（13 项）
> - **新增** 附录 B 兼容性矩阵 v0.2.0 (Python) 列 + 附录 C Architecture 章节映射