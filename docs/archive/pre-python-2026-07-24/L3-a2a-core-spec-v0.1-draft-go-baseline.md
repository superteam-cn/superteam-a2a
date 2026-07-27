# L3 文件级 Spec：A2A Core Library（通信层文件级）

> **⚠️ ADR-0005 supersede + 归档标记（2026-07-24）**：本 v0.1-draft Spec 文档**仅 supersede Go struct / Go package / Go HTTP server / Go JSON-RPC 实现条款**；wire contract（6 method envelope / 4 endpoint / 14 error code / Task FSM / mTLS / metric name）与 v0.1 业务语义**完全继续有效**。**本 Go draft 未评审**，依据 ADR-0005 §14.2 + Phase D 实施清单，**重写前必须先归档到 `docs/archive/pre-python-2026-07-24/`**（项目当前无 `.git` 历史，禁止直接覆盖丢失）。归档后原文作历史记录；Python L3-2 在 L2-1 Python v0.2 评审通过后重写。L1 v0.2.0 已于 2026-07-24 评审通过，依据 ADR-0005 Python-first 全栈迁移。
>
> **Python 重写入口**：依据 L1 v0.2.0 Architecture §7.5 + ADR-0005 §3.2 + §8，7 个 Go 子包 → Python 子包（`superteam_a2a.a2a.upstream` boundary + 4 个 extension router + standard method 通过 SDK）；Go HTTP server/net/http → ASGI + Uvicorn 单 worker；Go JSON-RPC handler → 官方 a2a-sdk envelope + Pydantic params/result 校验
>
> **层级**：L3 — 文件级 Spec
> **模块 ID**：C-2（A2A Core Library，见 L1 Architecture §6 模块清单）
> **代码位置**：`src/a2a/`（**v0.1-draft Go 路径，未评审 + 已废弃**）
> **版本**：v0.1-draft（2026-07-24 起草）+ ADR-0005 supersede 指针（2026-07-24）
> **状态**：⏳ v0.1-draft 起草中（**未评审**）+ ⚠️ 待归档 + 待 Python 重写
> **Go 基线**：Go 1.22+（**已废弃**）
> **协议基线**：A2A v0.3 核心子集 + JSON-RPC 2.0（**wire 不变，Python 通过官方 a2a-sdk 实现**）
> **上游约束**：[`docs/spec/L2-module-specs/L2-a2a-protocol.md`](../L2-module-specs/L2-a2a-protocol.md) v0.1.0（顶部已加 ADR-0005 supersede 指针）
> **本 Spec 目的**：将 L2-1 A2A Protocol 的 **7 个子包**、**6 个 v0.1 method**、**4 个 HTTP endpoint**、**Task 状态机**、**mTLS/SPIFFE 身份**、**Discovery/重试/熔断/P2C**、**错误模型**和**可观测性契约**落地为文件级 Go 代码契约。L4 实施者应能按本文件逐文件编码，无需重新做模块边界决策。
> **配套 Spec**：[L3-3 Adapter SDK](./L3-adapter-sdk.md)（待起草）/ [L3-4 Hello Agent](./L3-hello-agent.md)（待起草）/ [L3-5 Knowledge Service](./L3-knowledge-service.md)（待起草）/ [L3-6 Memory backend](./L3-memory-backend.md)（待起草）

---

## 0. 阅读指南

### 0.1 读者与必读路径

- **A2A Core 实施工程师**：§1 → §2 → §3-§8 → §10。
- **Adapter 实施工程师**：§1.3 → §5 → §9.2 → §11.1。
- **Operator / Workflow 实施工程师**：§6 → §9.1 → §11.2。
- **Knowledge / Memory 实施工程师**：§3.6 → §5.5 → §9.3 → §11.3。
- **Reviewer**：§1.2 决议、§4 错误与状态机、§7 安全、§10 测试矩阵、附录 B 开放问题。

### 0.2 规范词

- **必须（MUST）**：违反即与已评审上游设计冲突。
- **应（SHOULD）**：默认实现；偏离需在 PR 中解释。
- **可以（MAY）**：兼容扩展点，不属于 v0.1 验收门禁。
- 本文代码块是**签名契约**，允许 L4 调整私有 helper，但不得改变 exported API 语义。

### 0.3 明确不在本模块实现

- Agent 框架调用与事件翻译：L3-3 Adapter SDK。
- Agent 业务逻辑与 Hello Agent：L3-4。
- Knowledge 搜索、作用域继承、Memory 生命周期：L3-5 / L3-6。
- CRD reconcile、Deployment/Service/EndpointSlice 生命周期：L3-1 Operator Core。
- `a2a.cancelTask`、`a2a.subscribeTask`、SSE：v0.5+，本模块不得提前暴露。
- MCP：Agent ↔ Tool 协议，不得作为 A2A Core 依赖。

---

## 1. 模块边界、L3 决议与完整文件树

### 1.1 依赖方向

```text
Operator / Workflow ─┐
Adapter SDK ─────────┼──> src/a2a/{client,server,...} ──> HTTP/TLS/OTel/SPIFFE/K8s discovery
Knowledge Service ───┤
Memory backend ───────┘

禁止：src/a2a -> src/operator | src/adapter | src/knowledge | src/memory | 任意 Agent 框架
```

`types/` 和 `errors/` 是最低依赖层；`server/`、`client/` 可以依赖其余 A2A 子包，但 A2A Core 不得反向 import 业务模块。

### 1.2 L2 开放问题的 L3 决议

| ID | L2 开放问题 | L3 决议 | 理由 |
|----|-------------|---------|------|
| D-1 | Memory 代理模式如何落地 | A2A Core 只提供通用 `MethodHandler`、方法请求/响应类型与注册表；4 个 Knowledge/Memory handler 由 Knowledge Service 注册。A2A Core **不** import Operator/Memory | L2-4 已收敛为 Knowledge Service 与 Memory backend 同 Deployment；保持分层与无反依赖 |
| D-2 | Discovery 缓存如何失效 | `TTL=5min` 为强制兜底；提供 `Invalidate`/`InvalidateAll`；K8s 模式默认启动 EndpointSlice watch，Service/EndpointSlice 变化立即失效 | 同时保证最终一致与快速收敛 |
| D-3 | 限流粒度 | v0.1 保持 L2 默认：全 Server 令牌桶 `100 RPS / burst 200`；`PerKey=true` 时按 caller SPIFFE ID。按 Skill 限流延期 | 不改变已评审默认值，保留安全增强开关 |
| D-4 | SVID 刷新性能 | 启动时拉取一次，后台 `WatchUpdates`，通过原子快照热更新；请求路径不得同步 FetchSVID | 避免每 RPC 访问 Workload API |
| D-5 | Go 版本 | 锁定 Go 1.22+ | 与项目新建模块基线一致，可使用标准库增强且不背负旧版本兼容债 |
| D-6 | L2 配置项计数 | 以 L2 §3 表格为权威，共 **23 行配置项**；“22 项”是文案计数误差，不删除 identity socket 项 | 保持所有已定义 key |
| D-7 | `GetKnowledgeItem` wrapper 返回类型 | 返回 `*KnowledgeItem`；L2-1 §2.5 的 `*Message` 是签名笔误，L2-1 §4.4 与后续 L2-4 均规定结果是 KnowledgeItem | 以更具体、更新且跨文档一致的契约为准 |

### 1.3 完整文件树

```text
src/a2a/
├── go.mod                                  # module superteam-a2a.io/a2a；go 1.22
├── doc.go                                  # package a2a 模块说明 + 稳定性声明
├── config.go                               # 聚合 Config + LoadConfig
├── config_test.go                          # UT-CFG-01~07
├── internal/
│   └── testutil/
│       ├── clock.go                        # FakeClock，仅测试消费
│       ├── certs.go                        # 临时 CA/server/client cert
│       └── transport.go                    # deterministic RoundTripper
├── types/
│   ├── message.go                          # Message / Part / PartType / Role
│   ├── message_test.go                     # UT-T-01~07 + FZ-T-01
│   ├── task.go                             # Task / TaskStatus / Artifact
│   ├── task_test.go                        # UT-T-08~15
│   ├── agent_card.go                       # AgentCard / Skill / Provider
│   ├── agent_card_test.go                  # UT-T-16~22
│   ├── envelope.go                         # JSON-RPC Request / Response / ID
│   ├── envelope_test.go                    # UT-T-23~30 + FZ-T-02
│   ├── methods.go                          # 6 method 常量 + idempotency 元数据
│   ├── methods_task.go                     # SendMessage/GetTask params/result aliases
│   ├── methods_knowledge.go                # Knowledge request/result DTO
│   ├── methods_memory.go                   # Memory request/result DTO
│   ├── validate.go                         # Validate helpers + field violation
│   ├── validate_test.go                    # UT-T-31~39
│   ├── schema.go                           # go:embed + SchemaRegistry
│   ├── schema_test.go                      # UT-T-40~46
│   └── schemas/
│       ├── send_message.params.json
│       ├── send_message.result.json
│       ├── get_task.params.json
│       ├── task.result.json
│       ├── query_knowledge.params.json
│       ├── query_knowledge.result.json
│       ├── get_knowledge_item.params.json
│       ├── knowledge_item.result.json
│       ├── record_memory.params.json
│       ├── record_memory.result.json
│       ├── query_memory.params.json
│       ├── query_memory.result.json
│       └── common.defs.json
├── errors/
│   ├── codes.go                            # 5 标准码 + 9 A2A 域码
│   ├── error.go                            # A2AError + Is/WithData/Clone
│   ├── classify.go                         # Retryable + FromError + HTTP 映射
│   └── errors_test.go                      # UT-E-01~15
├── statemachine/
│   ├── task_fsm.go                         # FSM / transition table
│   └── task_fsm_test.go                    # UT-S-01~13
├── server/
│   ├── server.go                           # Server 生命周期 + graceful shutdown
│   ├── server_test.go                      # UT-SRV-01~07
│   ├── handler.go                          # JSON-RPC parse/validate/dispatch/respond
│   ├── handler_test.go                     # UT-SRV-08~20 + FZ-SRV-01
│   ├── registry.go                         # method registry + freeze
│   ├── registry_test.go                    # UT-SRV-21~25
│   ├── agent_card.go                       # Agent Card endpoint + ETag
│   ├── agent_card_test.go                  # UT-SRV-26~31
│   ├── health.go                           # /healthz /readyz
│   ├── health_test.go                      # UT-SRV-32~36
│   ├── tls.go                              # static cert / SPIFFE tls.Config
│   ├── tls_test.go                         # UT-SRV-37~42
│   └── middleware/
│       ├── chain.go                        # deterministic middleware chain
│       ├── auth.go                         # peer SVID extract + Authorize
│       ├── auth_test.go                    # UT-MW-01~07
│       ├── ratelimit.go                    # token bucket
│       ├── ratelimit_test.go               # UT-MW-08~13
│       ├── recovery.go                     # panic -> -32603
│       ├── recovery_test.go                # UT-MW-14~16
│       ├── trace.go                        # server span + trace context
│       ├── trace_test.go                   # UT-MW-17~22
│       ├── logging.go                      # 结构化访问日志
│       └── request_id.go                   # request/task/trace correlation
├── client/
│   ├── client.go                           # Client + Call + 6 typed wrappers
│   ├── client_test.go                      # UT-CLI-01~14
│   ├── transport.go                        # HTTP transport + JSON-RPC codec
│   ├── transport_test.go                   # UT-CLI-15~22
│   ├── discovery.go                        # Agent Card cache + resolver interface
│   ├── discovery_test.go                   # UT-CLI-23~34
│   ├── discovery_k8s.go                    # Service DNS + EndpointSlice resolver/watch
│   ├── discovery_k8s_test.go               # UT-CLI-35~43
│   ├── retry.go                            # idempotency gate + exponential backoff
│   ├── retry_test.go                       # UT-CLI-44~53
│   ├── circuitbreaker.go                   # closed/open/half-open
│   ├── circuitbreaker_test.go              # UT-CLI-54~61
│   ├── ratelimit.go                        # client-side limiter
│   ├── ratelimit_test.go                   # UT-CLI-62~66
│   ├── p2c.go                              # endpoint P2C
│   ├── p2c_test.go                         # UT-CLI-67~73
│   ├── trace.go                            # W3C traceparent injection
│   └── trace_test.go                       # UT-CLI-74~78
├── identity/
│   ├── spiffe.go                           # SPIFFEID parse/string/validation
│   ├── spiffe_test.go                      # UT-I-01~10
│   ├── workload.go                         # WorkloadClient + atomic SVID source
│   ├── workload_test.go                    # UT-I-11~18
│   ├── authorize.go                        # Authorizer interface + default rules
│   └── authorize_test.go                   # UT-I-19~28
├── observability/
│   ├── observer.go                         # Observer interface + provider lifecycle
│   ├── observer_test.go                    # UT-O-01~05
│   ├── metrics.go                          # 6 supteam_a2a_* 指标
│   ├── metrics_test.go                     # UT-O-06~13
│   ├── tracing.go                          # tracer + semantic attributes
│   ├── tracing_test.go                     # UT-O-14~20
│   └── logging.go                          # slog field constants/helpers
└── tests/
    ├── integration/
    │   ├── server_client_test.go            # IT-A2A-01~05
    │   ├── mtls_test.go                     # IT-A2A-06~09
    │   ├── discovery_test.go                # IT-A2A-10~12
    │   ├── observability_test.go            # IT-A2A-13~14
    │   └── memory_route_test.go             # IT-A2A-15（fake handler，不 import memory）
    ├── conformance/
    │   ├── envelope_test.go                 # CF-A2A-01~05
    │   ├── methods_test.go                  # CF-A2A-06~17
    │   └── errors_test.go                   # CF-A2A-18~22
    └── testdata/
        ├── cards/hello-agent.json
        ├── requests/*.json
        ├── responses/*.json
        └── malformed/*.json
```

**规模基线**：约 70 个 Go/JSON 文件；生产代码目标 4,000-6,000 行；单元覆盖率 ≥ 80%，`types/` / `errors/` / `statemachine/` ≥ 90%。

---

## 2. 根包与配置契约

### 2.1 `src/a2a/doc.go`

**职责**：声明模块定位、兼容性、非职责与稳定性。

```go
// Package a2a provides the protocol-neutral configuration surface for the
// superteam-a2a A2A v0.3 core implementation.
//
// Subpackages types and errors are stable public contracts in v0.1.
// Client and server APIs are pre-v1 compatible and may only add optional fields.
package a2a
```

### 2.2 `src/a2a/config.go`

```go
package a2a

type Config struct {
    Client        client.Config
    Server        server.Config
    Observability observability.Config
    Identity      identity.Config
}

type ConfigSource interface {
    Apply(ctx context.Context, cfg *Config) error
}

func DefaultConfig() Config
func LoadConfig(ctx context.Context, sources ...ConfigSource) (Config, error)
func (c Config) Validate() error
```

**加载顺序**：hardcoded default → ConfigMap `defaults/a2a` → env → flag。后加载覆盖先加载；空字符串仅在字段允许为空时才覆盖。

**23 项 key**：必须逐项保留 L2-1 Spec §3 的 key/env/default/range；不得重命名。实现时按以下分组映射：

- Client 11 项：timeout、max_retries、backoff 4 项、circuit breaker 3 项、discovery 2 项。
- Server 8 项：listen_addr、rate limit 3 项、TLS 4 项。
- Observability 3 项：OTLP endpoint、service name、metrics listen。
- Identity 1 项：SPIFFE socket。

**校验顺序**：类型解析 → 范围 → 跨字段约束。跨字段规则：

1. `spiffe_workload=false` 时 cert/key/clientCA 必须全部非空；开发模式可由显式 `InsecureDevMode=true` 例外。
2. `spiffe_workload=true` 时 identity socket 必须是 `unix://` URI。
3. `burst >= rps`；`backoff.max >= backoff.base`。
4. `circuit_breaker.half_open_probes <= threshold`。
5. 生产构建不得开启 `InsecureDevMode`。

**内部 helper**：`applyDefaults`、`applyEnv`、`parseDuration`、`validateTLSMode`、`validateRanges`。

---

## 3. `types/` — 公共协议类型与 Schema

### 3.1 `message.go`

```go
package types

type Role string
const (
    RoleUser  Role = "user"
    RoleAgent Role = "agent"
)

type PartType string
const (
    PartText PartType = "text"
    PartFile PartType = "file"
    PartData PartType = "data"
)

type Message struct {
    MessageID string         `json:"messageId"`
    Role      Role           `json:"role"`
    Parts     []Part         `json:"parts"`
    Metadata  map[string]any `json:"metadata,omitempty"`
    Timestamp time.Time      `json:"timestamp"`
}

type Part struct {
    Type     PartType `json:"type"`
    Text     string   `json:"text,omitempty"`
    FileURI  string   `json:"fileUri,omitempty"`
    MimeType string   `json:"mimeType,omitempty"`
    Data     []byte   `json:"data,omitempty"`
}

func (m Message) Validate() error
func (p Part) Validate() error
func (m Message) TraceParent() string
func (m *Message) SetTraceParent(value string)
```

**不变量**：

- `MessageID` 非空时必须为 UUID；新建消息使用 UUIDv7，解析兼容合法 UUID。
- `Parts` 至少 1 项；每个 Part 只能携带与 `Type` 对应的一个 payload。
- text：`Text` 必填；file：绝对 URI + 可选 MIME；data：非空 bytes + 推荐 MIME。
- `Metadata` 不得放凭证、私钥、SVID key；`traceparent` 必须通过 W3C parser 校验。
- 时间序列化统一 RFC3339Nano + UTC。

### 3.2 `task.go`

```go
package types

type TaskStatus string
const (
    TaskSubmitted TaskStatus = "submitted"
    TaskWorking   TaskStatus = "working"
    TaskCompleted TaskStatus = "completed"
    TaskFailed    TaskStatus = "failed"
    TaskCanceled  TaskStatus = "canceled" // 类型保留；v0.1 无公开 cancel method
)

type Task struct {
    TaskID    string            `json:"taskId"`
    Status    TaskStatus        `json:"status"`
    Messages  []Message         `json:"messages"`
    Artifacts []Artifact        `json:"artifacts,omitempty"`
    Error     *errors.A2AError  `json:"error,omitempty"`
    Metadata  map[string]any    `json:"metadata,omitempty"`
    CreatedAt time.Time         `json:"createdAt"`
    UpdatedAt time.Time         `json:"updatedAt"`
}

type Artifact struct {
    ArtifactID string `json:"artifactId"`
    Name       string `json:"name"`
    Parts      []Part `json:"parts"`
}

func (t Task) Validate() error
func (a Artifact) Validate() error
func (t Task) IsTerminal() bool
```

**不变量**：

- `TaskID` 必须 UUID；`CreatedAt <= UpdatedAt`。
- `failed` 必须有 `Error`；非 failed 不得有 `Error`。
- `completed` 必须有至少 1 条 agent message 或 1 个 artifact。
- `canceled` 仅用于向后兼容解析与未来状态机，v0.1 server 不产生该状态。
- Artifact 是协议类型的一部分，但 v0.1 不要求 Adapter 生成。

### 3.3 `agent_card.go`

```go
package types

type AgentCard struct {
    Name            string    `json:"name"`
    Description     string    `json:"description"`
    Version         string    `json:"version"`
    ProtocolVersion string    `json:"protocolVersion"`
    URL             string    `json:"url"`
    Skills          []Skill   `json:"skills"`
    InputModes      []string  `json:"inputModes"`
    OutputModes     []string  `json:"outputModes"`
    Capabilities    []string  `json:"capabilities,omitempty"`
    Provider        *Provider `json:"provider,omitempty"`
}

type Skill struct {
    ID          string   `json:"id"`
    Name        string   `json:"name"`
    Description string   `json:"description"`
    InputModes  []string `json:"inputModes"`
    OutputModes []string `json:"outputModes"`
    Examples    []string `json:"examples,omitempty"`
}

type Provider struct {
    Organization      string   `json:"organization,omitempty"`
    URL               string   `json:"url,omitempty"`
    AllowedNamespaces []string `json:"allowedNamespaces,omitempty"`
}

func (c AgentCard) Validate() error
func (c AgentCard) SupportsSkill(idOrName string) bool
func (c AgentCard) SupportsProtocol(constraint string) bool
func (c AgentCard) ETag() string
```

**验证**：name/skill ID 为 DNS-1123 kebab-case；description 禁止空值和宪法列出的营销词；version 为 semver；protocolVersion 必须满足 `[0.3.0,0.4.0)`；URL 必须 HTTPS（`localhost` 测试例外）；skills/inputModes/outputModes 非空且去重。

**ETag**：对 canonical JSON 做 SHA-256，返回带引号的完整 hex；不得使用 map 非确定序列化结果。

### 3.4 `envelope.go`

```go
package types

type RequestID struct {
    raw json.RawMessage
}

func NewStringID(v string) RequestID
func NewNumberID(v int64) RequestID
func NullID() RequestID
func (id RequestID) MarshalJSON() ([]byte, error)
func (id *RequestID) UnmarshalJSON([]byte) error
func (id RequestID) IsNotification() bool

type Request struct {
    JSONRPC string          `json:"jsonrpc"`
    Method  string          `json:"method"`
    Params  json.RawMessage `json:"params,omitempty"`
    ID      RequestID       `json:"id"`
}

type Response struct {
    JSONRPC string           `json:"jsonrpc"`
    Result  json.RawMessage  `json:"result,omitempty"`
    Error   *errors.A2AError `json:"error,omitempty"`
    ID      RequestID        `json:"id"`
}

func (r Request) Validate() error
func (r Response) Validate() error
func Success(id RequestID, result any) (Response, error)
func Failure(id RequestID, err error) Response
```

**约束**：

- 仅接受 JSON-RPC `"2.0"`；ID 仅 string/整数/null，不接受 object/array/bool/浮点。
- v0.1 Server 不接受 notification：null/缺失 ID 返回 `-32600`，避免无响应任务造成不可追踪调用。
- Response 的 Result/Error 必须二选一；失败时 HTTP 仍按 §5.3 映射。
- 单请求 body 上限默认 2 MiB；超过限制转换为 Invalid Request，不继续反序列化。

### 3.5 `methods.go`

```go
package types

const (
    MethodSendMessage      = "a2a.sendMessage"
    MethodGetTask          = "a2a.getTask"
    MethodQueryKnowledge   = "a2a.queryKnowledge"
    MethodGetKnowledgeItem = "a2a.getKnowledgeItem"
    MethodRecordMemory     = "a2a.recordMemory"
    MethodQueryMemory      = "a2a.queryMemory"
)

type MethodMeta struct {
    Name       string
    Idempotent bool
    Retryable  bool
    Capability string
}

func LookupMethod(name string) (MethodMeta, bool)
func BuiltinMethods() []MethodMeta
```

**方法元数据**：

| Method | Idempotent | 自动重试 | capability |
|--------|------------|----------|------------|
| sendMessage | 仅携带同一 `taskId` 时 | 是，需 taskId | `task-send` |
| getTask | 是 | 是 | `task-read` |
| queryKnowledge | 是（读取） | 是 | `knowledge-query` |
| getKnowledgeItem | 是 | 是 | `knowledge-get` |
| recordMemory | 否 | 否 | `memory-record` |
| queryMemory | 是 | 是 | `memory-query` |

> L2 设计 §7.2 的文字表述存在“queryKnowledge 黑名单/白名单”同句歧义；L2 最终意图和读取语义均指向白名单，本 L3 锁定为可重试。

### 3.6 `methods_*.go`

```go
// methods_task.go
type SendMessageParams struct {
    TaskID  string  `json:"taskId,omitempty"`
    Message Message `json:"message"`
    Skill   string  `json:"skill,omitempty"`
}
type GetTaskParams struct { TaskID string `json:"taskId"` }

// methods_knowledge.go
type QueryKnowledgeParams struct {
    Scope        string           `json:"scope,omitempty"`
    Query        string           `json:"query"`
    AgentPrivate bool             `json:"agentPrivate,omitempty"`
    MaxResults   int              `json:"maxResults,omitempty"`
    Filters      KnowledgeFilters `json:"filters,omitempty"`
}
type KnowledgeFilters struct {
    Tags          []string `json:"tags,omitempty"`
    MinConfidence *float64 `json:"minConfidence,omitempty"`
}
type KnowledgeResult struct { Items []KnowledgeItem `json:"items"`; Total int `json:"total"` }
type KnowledgeItem struct {
    ItemID string `json:"itemId"`; Scope string `json:"scope"`; Content string `json:"content"`
    Metadata map[string]any `json:"metadata,omitempty"`; UpdatedAt time.Time `json:"updatedAt"`
}
type GetKnowledgeItemParams struct { ItemID string `json:"itemId"` }

// methods_memory.go
type RecordMemoryParams struct {
    Content string `json:"content"`; Confidence float64 `json:"confidence,omitempty"`
    Tags []string `json:"tags,omitempty"`; DecayDays int `json:"decayDays,omitempty"`; Scope string `json:"scope,omitempty"`
}
type MemoryAck struct { MemoryID string `json:"memoryId"`; AcceptedAt time.Time `json:"acceptedAt"` }
type QueryMemoryParams struct {
    Query string `json:"query"`; MinConfidence float64 `json:"minConfidence,omitempty"`
    Scopes []string `json:"scopes,omitempty"`; MaxResults int `json:"maxResults,omitempty"`
}
type MemoryResult struct { Items []MemoryItem `json:"items"`; Total int `json:"total"` }
type MemoryItem struct {
    MemoryID string `json:"memoryId"`; AgentRef string `json:"agentRef"`; Content string `json:"content"`
    Confidence float64 `json:"confidence"`; Tags []string `json:"tags,omitempty"`
    CreatedAt time.Time `json:"createdAt"`; DecayAt *time.Time `json:"decayAt,omitempty"`
}
```

每个 Params/Result 类型必须有 `Validate() error`。Schema 的字段约束以 L2-1 Spec §4 为下限；若 L2-4 对 Knowledge/Memory 字段给出更严格约束，**更严格约束优先**，但不得改变 JSON 字段名。

### 3.7 `validate.go` 与 `schema.go`

```go
type FieldViolation struct { Field, Reason string }

type Validator interface { Validate() error }

func ValidateUUID(field, value string, required bool) error
func ValidateKebabCase(field, value string) error
func ValidateScope(field, value string, allowPrivate bool) error
func ValidateSemver(field, value string) error

type SchemaRegistry interface {
    ValidateParams(method string, raw json.RawMessage) error
    ValidateResult(method string, raw json.RawMessage) error
}

func NewEmbeddedSchemaRegistry() (SchemaRegistry, error)
```

- 使用 `//go:embed schemas/*.json`；启动时一次性编译 schema，失败则 `server.New` 返回错误。
- schema 错误统一转换为 `ErrInvalidParams.WithData({field, reason})`，不得泄露整个请求体。
- JSON Schema draft 固定 2020-12；禁止运行时网络拉取 `$ref`。

---

## 4. `errors/` 与 `statemachine/`

### 4.1 `errors/error.go` + `codes.go`

```go
package errors

type A2AError struct {
    Code    int            `json:"code"`
    Message string         `json:"message"`
    Data    map[string]any `json:"data,omitempty"`
    cause   error
}

func (e *A2AError) Error() string
func (e *A2AError) Unwrap() error
func (e *A2AError) Is(target error) bool
func (e *A2AError) Clone() *A2AError
func (e *A2AError) WithData(data map[string]any) *A2AError
func (e *A2AError) WithCause(cause error) *A2AError
```

**sentinel（语义和 code 不可修改）**：

```go
var (
    ErrParse             = New(-32700, "Parse error")
    ErrInvalidRequest    = New(-32600, "Invalid Request")
    ErrMethodNotFound    = New(-32601, "Method not found")
    ErrInvalidParams     = New(-32602, "Invalid params")
    ErrInternal          = New(-32603, "Internal error")
    ErrDiscovery         = New(-32001, "Discovery failure")
    ErrAuth              = New(-32002, "Authentication failure")
    ErrSkillNotFound     = New(-32003, "Skill not found")
    ErrTaskNotFound      = New(-32004, "Task not found")
    ErrRateLimited       = New(-32005, "Rate limit exceeded")
    ErrTimeout           = New(-32006, "Timeout")
    ErrKnowledgeScope    = New(-32010, "Knowledge scope violation")
    ErrMemoryVisibility  = New(-32011, "Memory visibility violation")
    ErrUpstreamK8s       = New(-32020, "Upstream K8s API error")
)
```

**并发安全**：sentinel 不得直接修改 Data/cause；`WithData` / `WithCause` 必须 clone。

### 4.2 `errors/classify.go`

```go
func New(code int, message string) *A2AError
func FromError(err error) *A2AError
func IsRetryable(err error) bool
func RetryAfter(err error) time.Duration
func HTTPStatus(err error) int
func Sanitize(err error, exposeInternal bool) *A2AError
```

| Code | 自动重试 | HTTP | 备注 |
|------|----------|------|------|
| -32700/-32600/-32602 | 否 | 400 | 客户端请求错误 |
| -32601 | 否 | 404 | method 不存在 |
| -32603 | 是（受 method 幂等门禁） | 500 | 外部响应固定消息，不泄露 cause |
| -32001 | 是 | 503 | discovery |
| -32002 | 否 | 403 | 已建立连接后的授权失败；TLS handshake 失败在 HTTP/JSON-RPC 之前终止 |
| -32003/-32004 | 否 | 404 | skill/task |
| -32005 | 否 | 429 | 返回 `Retry-After: 1` 供手动重试 |
| -32006 | 是（受幂等门禁） | 504 | timeout |
| -32010/-32011 | 否 | 403 | scope/visibility |
| -32020 | 是（受幂等门禁） | 503 | K8s upstream |

### 4.3 `statemachine/task_fsm.go`

```go
package statemachine

type FSM struct{}

func New(initial types.TaskStatus) (*FSM, error)
func (f *FSM) CanTransition(from, to types.TaskStatus) bool
func (f *FSM) Transition(task *types.Task, to types.TaskStatus, now time.Time) error
func IsTerminal(status types.TaskStatus) bool

var ErrInvalidTransition = errors.New("invalid task state transition")
```

**转换矩阵**：

| from \ to | submitted | working | completed | failed | canceled |
|-----------|-----------|---------|-----------|--------|----------|
| submitted | ✅ 同状态幂等 | ✅ | ❌ | ❌ | ❌ v0.1 |
| working | ❌ | ✅ 心跳 | ✅ | ✅ | ❌ v0.1 |
| completed | ❌ | ❌ | ✅ | ❌ | ❌ |
| failed | ❌ | ❌ | ❌ | ✅ | ❌ |
| canceled | ❌ | ❌ | ❌ | ❌ | ✅（仅解析兼容） |

`Transition` 必须更新 `UpdatedAt`，且不得修改 TaskID/CreatedAt/Messages；从 working 到 failed 前调用方必须先设置 Error，从 working 到 completed 前必须满足 Task Validate。

**幂等边界**：同 taskId 重试的“返回已有 Task”由业务 `MethodHandler` / TaskStore 实现；FSM 只保证状态不回退，不保存任务。

---

## 5. `server/` — HTTP 与 JSON-RPC Server SDK

### 5.1 `server/server.go`

```go
package server

type Config struct {
    ListenAddr       string
    TLS              TLSConfig
    AgentCard        types.AgentCard
    RateLimit        RateLimitConfig
    Middleware       []Middleware
    Observer         observability.Observer
    Authorizer       identity.Authorizer
    SchemaRegistry   types.SchemaRegistry
    ReadHeaderTimeout time.Duration // default 5s
    ReadTimeout       time.Duration // default 30s
    WriteTimeout      time.Duration // default 30s
    IdleTimeout       time.Duration // default 60s
    ShutdownTimeout   time.Duration // default 10s
    MaxBodyBytes      int64         // default 2 MiB
    InsecureDevMode   bool
}

type Server struct { /* private http.Server, registry, ready gate */ }

func New(cfg Config) (*Server, error)
func (s *Server) RegisterMethod(name string, handler MethodHandler) error
func (s *Server) Handler() http.Handler
func (s *Server) Start(ctx context.Context) error
func (s *Server) Shutdown(ctx context.Context) error
func (s *Server) SetReady(ready bool)
```

**生命周期**：

1. `New` 校验 Config/Card/TLS/schema；安装内建路由；registry 可注册。
2. `Start` 前冻结 registry；启动 observer/SVID watch；开始 HTTPS ListenAndServeTLS。
3. ctx cancel：ready=false → 等待 in-flight（最多 10s）→ Shutdown → flush traces。
4. 正常 ctx cancel 返回 nil；非 `http.ErrServerClosed` 错误原样返回。

### 5.2 `registry.go`

```go
// middleware.Handler/Func 是底层签名；server 仅做 type alias，避免
// server <-> server/middleware 的 Go import cycle。
type MethodHandler = middleware.Handler
type Middleware = middleware.Func
type RateLimitConfig = middleware.RateLimitConfig

type Registry interface {
    Register(name string, handler MethodHandler) error
    Lookup(name string) (MethodHandler, bool)
    Freeze()
}

var (
    ErrDuplicateMethod = errors.New("duplicate A2A method")
    ErrRegistryFrozen  = errors.New("A2A method registry frozen")
)
```

- 允许注册 6 个 builtin method 和 `x.<vendor>.<method>` 扩展。
- 禁止覆盖 builtin method；method 名必须匹配 `^(a2a|x\.[a-z0-9-]+)\.[A-Za-z][A-Za-z0-9]*$`。
- 注册并发安全；Start 后不可变，避免运行中 handler 竞态。

### 5.3 `handler.go`

**固定处理流水线**：

```text
HTTP method/path/content-type/body limit
  -> JSON parse
  -> Request.Validate
  -> builtin method check
  -> params JSON Schema
  -> middleware chain (request-id -> recovery -> auth -> rate-limit -> trace -> logging)
  -> MethodHandler
  -> result marshal + result schema
  -> Response + metrics/log/span
```

```go
func NewJSONRPCHandler(reg Registry, schemas types.SchemaRegistry, opts HandlerOptions) http.Handler

type HandlerOptions struct {
    MaxBodyBytes int64
    Observer     observability.Observer
    ExposeInternalErrors bool
}
```

**HTTP 契约**：

| 场景 | HTTP | JSON-RPC body |
|------|------|---------------|
| 成功 | 200 | result |
| JSON-RPC 解析/参数错误 | 400 | -32700/-32600/-32602 |
| method/task/skill 不存在 | 404 | -32601/-32003/-32004 |
| 未认证/未授权 | 401/403 | TLS handshake 失败可无 JSON body；授权失败 -32002 |
| 限流 | 429 | -32005 + Retry-After |
| 超时 | 504 | -32006 |
| 内部/上游不可用 | 500/503 | -32603/-32001/-32020 |

- `Content-Type` 接受 `application/json` 和 `application/json; charset=utf-8`。
- 一次 HTTP 仅一个 JSON-RPC request；batch array 在 v0.1 返回 -32600。
- panic 经 recovery 转 -32603；日志保存内部 cause，外部不返回堆栈。
- 响应必须带 `Cache-Control: no-store`；Card endpoint 例外。

### 5.4 `agent_card.go` + `health.go`

```go
type CardProvider interface { CurrentCard(context.Context) (types.AgentCard, error) }
func NewStaticCardProvider(card types.AgentCard) CardProvider
func AgentCardHandler(provider CardProvider) http.Handler

func HealthHandler() http.Handler
func ReadinessHandler(checks ...ReadinessCheck) http.Handler
type ReadinessCheck interface { Name() string; Ready(context.Context) error }
```

- Card：`GET /.well-known/agent.json`，`application/json`，支持 `ETag`/`If-None-Match` → 304，`Cache-Control: public,max-age=60`。
- `/healthz`：只反映进程可服务，明文 HTTP 仅绑定 Pod probe listener。
- `/readyz`：Card 有效、registry frozen、TLS/SVID 可用、业务 readiness 全通过才 200。
- probe listener 不得暴露在 Service A2A 端口的外部路径；Adapter 可将其绑定到 localhost/独立 probe port。

### 5.5 业务 handler 归属

A2A Core **不实现** 6 个 method 的业务语义，只提供协议入口：

| Method | handler 提供方 | L3 落点 |
|--------|----------------|---------|
| sendMessage/getTask | Adapter SDK | L3-3 `src/adapter/core/handlers/` |
| queryKnowledge/getKnowledgeItem | Knowledge Service | L3-5 `handlers/` |
| recordMemory/queryMemory | Knowledge Service 同 Pod 的 Memory backend | L3-5/L3-6 |

注册示例：

```go
srv.RegisterMethod(types.MethodSendMessage, adapterHandlers.SendMessage)
srv.RegisterMethod(types.MethodGetTask, adapterHandlers.GetTask)
srv.RegisterMethod(types.MethodQueryKnowledge, knowledgeHandlers.Query)
```

禁止在 `src/a2a/server/` 添加 `memory.go` 并直接 import Reconciler；L2-1 的“Memory middleware”在后续 L2-4 中已被“Knowledge Service handler + backend interface”收敛。

### 5.6 `server/tls.go`

```go
type TLSConfig struct {
    CertFile, KeyFile, ClientCAFile string
    SPIFFEWorkload bool
    MinVersion uint16 // default tls.VersionTLS13
}

func BuildTLSConfig(ctx context.Context, cfg TLSConfig, source identity.SVIDSource) (*tls.Config, error)
```

- 生产 TLS 最低 1.3；禁用 renegotiation；ClientAuth=`RequireAndVerifyClientCert`。
- 静态证书用 `GetCertificate` 的原子快照支持 reload；SPIFFE 使用 SVIDSource。
- 不记录证书原文/私钥；日志最多记录 trust domain、SPIFFE ID、expiry。

### 5.7 `server/middleware/`

**链顺序固定**：request ID → recovery → auth → rate limit → trace → logging → handler。自定义 middleware 插在 logging 与 handler 之间。

```go
package middleware

type Handler func(ctx context.Context, params json.RawMessage) (any, error)
type Func func(next Handler) Handler

type RateLimitConfig struct {
    RPS, Burst int
    PerKey bool
}

type Clock interface {
    Now() time.Time
}

func Chain(final Handler, middleware ...Func) Handler
func Auth(authorizer identity.Authorizer) Func
func RateLimit(cfg RateLimitConfig, clock Clock) Func
func Recovery(logger *slog.Logger) Func
func Trace(observer observability.Observer) Func
func Logging(logger *slog.Logger) Func

type RequestMeta struct {
    RequestID string
    Method    string
    Caller    identity.Caller
    TaskID    string
    TraceID   string
}

func RequestMetaFromContext(ctx context.Context) (RequestMeta, bool)
```

认证、request ID 与 trace middleware 必须把不可变 `RequestMeta` 写入 context；业务 handler 通过 `RequestMetaFromContext` 获取 caller SPIFFE 身份，禁止解析私有 context key。Caller 缺失时 Knowledge/Memory handler 必须 fail-closed。

`server.MethodHandler` 与 `server.Middleware` 分别是这两个类型的 alias；`server/middleware` **不得** import `server`，从结构上消除循环依赖。

`RateLimitConfig`：RPS=100、Burst=200、PerKey=false。PerKey key 为 caller SPIFFE ID；匿名/insecure-dev 使用 remote IP。不得以 taskId 作为 key，防止无限 key 内存增长。空闲 bucket 10 分钟清理。

---

## 6. `client/` — Discovery、调用、重试与负载均衡

### 6.1 `client/client.go`

```go
package client

type Config struct {
    Timeout        time.Duration
    MaxRetries     int
    Backoff        BackoffConfig
    CircuitBreaker CircuitBreakerConfig
    Discovery      DiscoveryConfig
    Observer       observability.Observer
    HTTPClient     *http.Client
    Limiter        *rate.Limiter
}

type Client struct { /* resolver, transport, retryer, breakers */ }

// L2-1 公共 DTO 名称保持为 type alias，底层规范类型集中在 types/。
type KnowledgeQuery = types.QueryKnowledgeParams
type KnowledgeResult = types.KnowledgeResult
type KnowledgeItem = types.KnowledgeItem
type MemoryRecord = types.RecordMemoryParams
type MemoryAck = types.MemoryAck
type MemoryQuery = types.QueryMemoryParams
type MemoryResult = types.MemoryResult
type MemoryItem = types.MemoryItem

func New(cfg Config) (*Client, error)
func (c *Client) Close(ctx context.Context) error

// Call 保留 L2-1 的底层公共签名。
func (c *Client) Call(ctx context.Context, target *AgentRef, method string, params any) (*types.Response, error)
// CallInto 是类型安全解码 helper；不替代 Call。
func (c *Client) CallInto(ctx context.Context, target *AgentRef, method string, params, out any) error

// SendMessage 保留 L2-1 签名并默认生成 UUIDv7 taskId，因而可安全重试。
func (c *Client) SendMessage(ctx context.Context, target *AgentRef, msg *types.Message) (*types.Task, error)
// SendMessageWithParams 供高级调用方显式控制 taskId/skill。
func (c *Client) SendMessageWithParams(ctx context.Context, target *AgentRef, p *types.SendMessageParams) (*types.Task, error)
func (c *Client) GetTask(ctx context.Context, target *AgentRef, taskID string) (*types.Task, error)
func (c *Client) QueryKnowledge(ctx context.Context, target *AgentRef, p *KnowledgeQuery) (*KnowledgeResult, error)
func (c *Client) GetKnowledgeItem(ctx context.Context, target *AgentRef, itemID string) (*KnowledgeItem, error)
func (c *Client) RecordMemory(ctx context.Context, target *AgentRef, p *MemoryRecord) (*MemoryAck, error)
func (c *Client) QueryMemory(ctx context.Context, target *AgentRef, p *MemoryQuery) (*MemoryResult, error)
```

**调用顺序**：输入 Validate → resolve/card capability → client limiter → circuit gate → P2C endpoint → trace inject → transport → response validate → retry classify → metrics。

- `Call` 返回经过 envelope 校验的原始 Response；`CallInto` 必须要求非 nil `out`，并将成功 result 解码到 out。
- wrapper 不接受 `map[string]any`，确保公共字段显式。
- Context deadline 与 Config.Timeout 取更早者；不得延长调用方 deadline。
- Client 可并发使用；Close 幂等。

### 6.2 `transport.go`

```go
type Transport interface {
    RoundTrip(ctx context.Context, endpoint *url.URL, req types.Request) (types.Response, error)
}

func NewHTTPTransport(client *http.Client, schemas types.SchemaRegistry) Transport
```

- POST 固定 `/a2a/jsonrpc`；Content-Type/Accept=`application/json`。
- 连接池：每 host max idle 10、idle timeout 90s；TLS handshake 10s。
- 非 2xx 仍尝试解析 A2AError；无合法 JSON-RPC body 时按 HTTP status 分类。
- response body 上限 4 MiB；读取后必须 Close。

### 6.3 `discovery.go`

```go
type AgentRef struct {
    Name, Namespace string
    Endpoint *url.URL // 非 nil 时跳过 K8s name resolve，但仍拉 Card
}

type ResolvedAgent struct {
    Ref       AgentRef
    Card      types.AgentCard
    Endpoints []Endpoint
    ExpiresAt time.Time
}

type Endpoint struct { URL *url.URL; Ready bool; Zone string }

type NameResolver interface {
    Resolve(ctx context.Context, ref AgentRef) (ResolvedAgent, error)
    Invalidate(ref AgentRef)
    InvalidateAll()
}

type DiscoveryConfig struct {
    CacheTTL time.Duration
    RefreshOnMiss bool
    DefaultNamespace string
    Resolver NameResolver
    WatchEndpoints bool // K8s resolver default true
}
```

**解析规则**：`https://<name>.<namespace>.svc.cluster.local:8080`；显式 endpoint 必须 HTTPS（测试 localhost 例外）。

**缓存算法**：

1. key=`namespace/name` 或 canonical explicit URL。
2. hit 且未过期直接返回；并发 miss 用 singleflight 合并。
3. 拉 Card 后校验 protocol/capability/URL；Card URL 若与发现 host 不同，只允许同 Service identity 或 allowlist。
4. EndpointSlice 只保留 Ready != false 且有 `a2a` port 的 endpoint。
5. watch 收到 add/update/delete，调用 Invalidate；watch 断线指数重连，TTL 仍保证最终刷新。
6. 缓存最大 1,000 entries；LRU 淘汰，防止恶意 name 导致无界增长。

### 6.4 `discovery_k8s.go`

```go
type K8sResolverConfig struct {
    Client kubernetes.Interface
    Namespace string
    PortName string // "a2a"
    Port int32      // 8080 fallback
    CardClient CardClient
}

type CardClient interface { Fetch(ctx context.Context, endpoint *url.URL) (types.AgentCard, error) }

func NewK8sResolver(cfg K8sResolverConfig) (NameResolver, error)
func (r *K8sResolver) Start(ctx context.Context) error
```

RBAC 只读：Services get/list/watch；EndpointSlices get/list/watch。不得读 Secret。集群外显式 endpoint 模式不初始化 client-go。

### 6.5 `retry.go`

```go
type BackoffConfig struct { Base time.Duration; Factor, Jitter float64; Max time.Duration }

type Timer interface {
    C() <-chan time.Time
    Stop() bool
}
type Clock interface {
    Now() time.Time
    NewTimer(time.Duration) Timer
}
type Rand interface {
    Float64() float64
    Intn(n int) int
}

type Retryer interface { Do(ctx context.Context, meta types.MethodMeta, hasIdempotencyKey bool, fn func(context.Context) error) error }
func NewRetryer(max int, cfg BackoffConfig, clock Clock, rand Rand) Retryer
```

**默认序列**：1s → 2s → 4s，±20% jitter，最多 3 次重试；总时间受 caller context 限制。

**重试门禁**：

```text
method meta Retryable
AND error IsRetryable
AND (method != sendMessage OR taskId 非空)
AND attempt < maxRetries
AND context 未取消
```

- -32005 不自动重试。
- `recordMemory` 永不自动重试，即使收到 -32603/-32020。
- endpoint TCP/TLS 失败可先做同轮 failover；每个 endpoint 最多一次，不占逻辑 maxRetries，但受总 deadline。
- 每次 retry 添加 span event，记录 attempt/code/backoff，不记录消息内容。

### 6.6 `circuitbreaker.go`

```go
type CircuitState uint8
const (CircuitClosed CircuitState = iota; CircuitHalfOpen; CircuitOpen)

type CircuitBreakerConfig struct { Threshold int; Window time.Duration; HalfOpenProbes int }
type CircuitBreaker interface {
    Allow(now time.Time) bool
    Success(now time.Time)
    Failure(now time.Time)
    State() CircuitState
}
```

key 为 `scheme://host:port`；5 次连续失败/10s → open；10s 后允许 1 次 half-open probe；成功 close，失败重新 open。业务 4xx、-32602、-32003/-32004 不计入失败；网络错误、5xx、-32001/-32006/-32020 计入。

### 6.7 `p2c.go`

```go
type LoadTracker interface { InFlight(endpoint Endpoint) int64 }
type Picker interface { Pick(endpoints []Endpoint) (Endpoint, error) }
func NewP2CPicker(load LoadTracker, rand Rand) Picker
```

- 0 endpoint → ErrDiscovery；1 endpoint 直接返回；≥2 均匀随机取 2 个不同 endpoint，选 in-flight 较低者，平局随机。
- Pick 后 transport 前 increment，defer decrement；不得用长期累计请求数替代当前 in-flight。
- 测试使用 deterministic Rand；生产使用并发安全 PRNG，不使用加密随机。

### 6.8 `ratelimit.go` 与 `trace.go`

客户端 limiter 在 discovery 前等待 token，等待受 context 控制；默认可关闭。`trace.go` 使用 OTel propagator 注入 HTTP header，同时在 Message metadata 中写 `traceparent` 以满足跨 Adapter 传播；已有合法 metadata 值时以当前 span context 为准并记录覆盖 event。

---

## 7. `identity/` — SPIFFE 身份与授权

### 7.1 `spiffe.go`

```go
package identity

type Config struct {
    SPIFFESocket string // default unix:///run/spiffe/sockets/agent.sock
}

type SPIFFEID struct { TrustDomain, Namespace, ServiceAccount, AgentName string }

func ParseSPIFFEID(raw string) (SPIFFEID, error)
func (id SPIFFEID) String() string
func (id SPIFFEID) Validate() error
func (id SPIFFEID) IsOperator() bool
```

固定格式：

```text
spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>/agent/<agent-name>
```

所有 path segment 必须 URL 解码后再做 DNS-1123 验证；拒绝额外 segment、空段、`..`、重复键。Operator 身份必须由明确 SA/AgentName allowlist 判定，不以包含 `operator` 子串判定。

### 7.2 `workload.go`

```go
type SPIFFESVID struct {
    Certificate tls.Certificate
    IDs []SPIFFEID
    ExpiresAt time.Time
}

type WorkloadClient interface {
    FetchSVID(context.Context) (*SPIFFESVID, error)
    WatchUpdates(context.Context) (<-chan *SPIFFESVID, error)
}

type SVIDSource interface {
    Current() (*SPIFFESVID, error)
    Start(context.Context) error
    Ready() bool
}

func NewWorkloadClient(socketPath string) WorkloadClient
func NewSVIDSource(client WorkloadClient, refreshBefore time.Duration) SVIDSource
```

SVIDSource 使用 `atomic.Pointer` 发布不可变快照；过期或距离过期小于 1 分钟时 readiness=false；watch 失败按 1/2/4/8/30s 重连，保留仍有效的最后 SVID。

### 7.3 `authorize.go`

```go
type Caller struct { SPIFFEID SPIFFEID; RemoteAddr net.Addr }
type Target struct {
    Namespace string
    AgentName string
    AllowedNamespaces []string
    ExternalAllowlist []string
}

type Authorizer interface { Authorize(context.Context, Caller, Target, string) error }
func NewDefaultAuthorizer(trustDomain string, operatorIDs []SPIFFEID) Authorizer
```

规则优先级：

1. trust domain 不匹配 → ErrAuth。
2. Operator 精确 SPIFFE ID → 全部 6 method。
3. 同 namespace Agent → 全部 6 method，但仍受 method capability/业务可见性检查。
4. 跨 namespace → target allowedNamespaces + NetworkPolicy 双重约束。
5. 外部身份 → external allowlist 精确匹配。
6. Knowledge scope / Memory visibility 由业务 handler 判定，分别返回 -32010/-32011；identity 层不得复制 5 维矩阵。

---

## 8. `observability/` — 指标、Trace 与日志

### 8.1 `observer.go`

```go
package observability

type Config struct { OTLPEndpoint, ServiceName, MetricsListen string }

type Observer interface {
    Tracer() trace.Tracer
    Meter() metric.Meter
    Metrics() *MetricsRegistry
    Shutdown(context.Context) error
}

func New(ctx context.Context, cfg Config, reg prometheus.Registerer) (Observer, error)
func Noop() Observer
```

`New` 不得修改全局 provider，除非调用方显式选择；便于 Operator/Adapter 统一管理 provider。重复注册 Prometheus collector 必须复用或返回可识别错误，禁止 panic。

### 8.2 `metrics.go`

必须定义且仅定义以下 L2 基线指标：

| 字段 | 指标 | 类型 | labels |
|------|------|------|--------|
| RPC | `supteam_a2a_rpc_total` | CounterVec | method,status,namespace |
| RPCDuration | `supteam_a2a_rpc_duration_seconds` | HistogramVec | method,namespace |
| RPCErrors | `supteam_a2a_rpc_errors_total` | CounterVec | method,code |
| ActiveTasks | `supteam_a2a_active_tasks` | GaugeVec | namespace,agent |
| DiscoveryFailures | `supteam_a2a_discovery_failures_total` | CounterVec | reason |
| CircuitState | `supteam_a2a_circuit_breaker_state` | GaugeVec | target |

**基数约束**：禁止 task_id、trace_id、pod IP、原始 URL 作为 label；target label 使用规范化 `namespace/name` 或受限 host，缓存淘汰时删除 gauge series。

### 8.3 `tracing.go`

```go
func StartClientSpan(ctx context.Context, tracer trace.Tracer, attrs RPCAttributes) (context.Context, trace.Span)
func StartServerSpan(ctx context.Context, tracer trace.Tracer, attrs RPCAttributes) (context.Context, trace.Span)
func RecordError(span trace.Span, err error)
```

Span 名：`a2a.{method}`。属性至少：`rpc.system=a2a`、`rpc.service`、`a2a.method`、`a2a.task_id`、`a2a.trace_id`、`a2a.namespace`、`a2a.from_agent`。task_id 可以是 span attribute，但不得是 Prometheus label。

### 8.4 `logging.go`

固定 slog keys：`method`、`task_id`、`trace_id`、`from_agent`、`to_agent`、`namespace`、`duration_ms`、`status_code`、`error_code`、`request_id`。

- INFO：完成的正常 RPC。
- WARN：4xx/域权限/限流。
- ERROR：5xx、panic、SVID/Discovery 系统失败。
- 禁止记录 Message content、Part data、Memory content、认证材料；debug 也只记录尺寸和哈希。

---

## 9. 六个 Method 的端到端协议映射

### 9.1 Method 路由总表

| Method | Params 类型 | Result 类型 | Server capability | 自动重试 |
|--------|-------------|-------------|-------------------|----------|
| `a2a.sendMessage` | `SendMessageParams` | `Task` | task-send | 有 taskId 才可 |
| `a2a.getTask` | `GetTaskParams` | `Task` | task-read | 是 |
| `a2a.queryKnowledge` | `QueryKnowledgeParams` | `KnowledgeResult` | knowledge-query | 是 |
| `a2a.getKnowledgeItem` | `GetKnowledgeItemParams` | `KnowledgeItem` | knowledge-get | 是 |
| `a2a.recordMemory` | `RecordMemoryParams` | `MemoryAck` | memory-record | 否 |
| `a2a.queryMemory` | `QueryMemoryParams` | `MemoryResult` | memory-query | 是 |

### 9.2 sendMessage / getTask 契约

- Client 未传 taskId 时可以发送，但 SDK 不得自动重试。
- 推荐 SDK 默认生成 UUIDv7 taskId，除非调用方显式禁用。
- Server handler 发现同 taskId：submitted/working/completed/failed 均返回现有 Task，不重复执行；payload hash 不同则 ErrInvalidParams，Data 含 `field=taskId`、`reason=idempotency key reused with different payload`。
- `skill` 非空时先用 Agent Card 检查，不存在返回 -32003。
- `getTask` 不存在返回 -32004；不得用空 Task 表示。

### 9.3 Knowledge / Memory 契约

- A2A Core 只做结构/schema/capability/authentication，业务 scope/visibility 由 Knowledge Service。
- `scope` 枚举：Knowledge 为 industry/organization/team/project；Memory 额外 private。
- query 长度 1-2048；maxResults 1-100，默认 10。
- recordMemory content 1-65536；confidence 0-1；tags ≤32；decayDays 0-3650；0 表示永不过期。
- `recordMemory` 的幂等/批处理不在 v0.1 协议中，禁止 SDK 隐式重放。

### 9.4 协议版本与兼容

- Card `protocolVersion="0.3"` 归一为 semver 0.3.0。
- Client 接受 `[0.3.0,0.4.0)`；其他版本返回 ErrDiscovery，Data 含 expected/actual。
- 可新增 optional JSON 字段；未知字段默认忽略并保留向前兼容。
- method 名、现有字段名、错误码语义不得修改；破坏性变更走 ADR + 至少一个 minor deprecation。

---

## 10. 测试文件映射与验收门禁

### 10.1 单元测试（共 271 ID）

| 范围 | ID | 数量 | P0 场景 |
|------|----|------|---------|
| config | UT-CFG-01~07 | 7 | 四层优先级、范围、TLS 跨字段 |
| types/message | UT-T-01~07 | 7 | discriminated union、traceparent、敏感 metadata |
| types/task | UT-T-08~15 | 8 | failed/error、completed output、时间顺序 |
| types/card | UT-T-16~22 | 7 | kebab、semver、protocol range、ETag |
| envelope | UT-T-23~30 | 8 | ID 三类型、batch 拒绝、result/error XOR |
| validate | UT-T-31~39 | 9 | UUID/scope/semver/field data |
| schema | UT-T-40~46 | 7 | 6 method schema + no remote refs |
| errors | UT-E-01~15 | 15 | errors.Is/As、clone、retry/HTTP/sanitize |
| FSM | UT-S-01~13 | 13 | 全合法/非法边、terminal、time update |
| server core | UT-SRV-01~42 | 42 | 生命周期、dispatch、Card、probe、TLS |
| middleware | UT-MW-01~22 | 22 | auth、bucket、panic、trace、顺序 |
| client | UT-CLI-01~78 | 78 | wrappers、codec、discovery、retry、CB、P2C、trace |
| identity | UT-I-01~28 | 28 | parse、atomic refresh、5 类授权 |
| observability | UT-O-01~20 | 20 | 注册、labels、span、shutdown |

> 表中分项合计以 ID 区间为准。L4 若拆分测试函数，必须保留 ID 作为 `t.Run` 名或注释，便于回溯 L2 测试骨架。

### 10.2 必须保留的 L2 测试映射

| L2 ID | L3 ID |
|-------|-------|
| UT-T-01~05 | UT-T-01/08/16/23/04（按类型重新编号） |
| UT-S-01~07 | UT-S-01~07 |
| UT-E-01~04 | UT-E-01~04 |
| UT-C-01~06 | UT-CLI-44~49、UT-CLI-62~66 |
| UT-I-01~04 | UT-I-01、UT-I-19~21 |
| IT-01~08 | IT-A2A-01~09、IT-A2A-15 |
| E2E-01~05 | E2E-A2A-01~05（见 §10.5） |

### 10.3 Fuzz 测试

| ID | 入口 | 不变量 |
|----|------|--------|
| FZ-T-01 | Part JSON | 不 panic；非法 union 必须拒绝 |
| FZ-T-02 | RequestID/envelope JSON | 不 panic；不接受 float/object/array/bool ID |
| FZ-SRV-01 | HTTP JSON-RPC body | 不 panic、不超 body limit、错误不泄露内部信息 |

Fuzz corpus 使用 `tests/testdata/malformed/`；CI PR 阶段每项 10s，nightly 5min。

### 10.4 集成与 Conformance（15 IT + 22 CF）

| ID | 场景 | 期望 |
|----|------|------|
| IT-A2A-01 | Server Card endpoint | 200 + valid Card + ETag |
| IT-A2A-02 | sendMessage happy path | submitted → working → completed |
| IT-A2A-03 | 同 taskId 同 payload | 返回已有 Task、不重复执行 |
| IT-A2A-04 | 同 taskId 不同 payload | -32602 |
| IT-A2A-05 | 6 method fake handler 路由 | params/result schema 均通过 |
| IT-A2A-06 | mTLS valid SVID | 成功 |
| IT-A2A-07 | invalid client cert | TLS 失败 |
| IT-A2A-08 | cross namespace denied | -32002 / 403 |
| IT-A2A-09 | SVID 热更新 | 新连接使用新证书，无重启 |
| IT-A2A-10 | Service + EndpointSlice discovery | Ready endpoints 可用 |
| IT-A2A-11 | EndpointSlice watch invalidation | 旧 endpoint 不再选择 |
| IT-A2A-12 | TTL/watch 断线兜底 | ≤ TTL 刷新 Card |
| IT-A2A-13 | traceparent client→server | 单 trace 父子 span |
| IT-A2A-14 | metrics | 6 指标出现且无高基数 label |
| IT-A2A-15 | queryMemory fake route | A2A Core 不 import memory 仍可完整路由 |

Conformance：CF-A2A-01~05 envelope、06~17 六 method params/result、18~22 标准错误码。上游 conformance 套件发布后以 adapter 方式接入，项目扩展 method 独立保留。

### 10.5 E2E（kind，由跨模块套件承载）

| ID | 场景 | 责任模块 |
|----|------|----------|
| E2E-A2A-01 | Hello Agent port-forward + sendMessage | L3-3/L3-4 |
| E2E-A2A-02 | AgentSet 3 副本 P2C | L3-1/L3-3 |
| E2E-A2A-03 | Card Discovery + Operator status | L3-1/L3-3 |
| E2E-A2A-04 | mTLS 失败归因 | L3-1/L3-3 |
| E2E-A2A-05 | recordMemory 全链路创建 CRD | L3-5/L3-6 |

### 10.6 性能与竞态门禁

- `go test -race ./...` 必须通过。
- benchmark：envelope encode/decode、schema validate、P2C、metrics hot path、SVID Current。
- v0.1 非硬 SLA 参考：1 KiB loopback RPC p95 < 10ms（不含业务）、Card cache hit < 100µs、P2C Pick < 10µs。
- 每次 RPC 常驻分配应在基准中记录；不得为达标绕过 validation/trace/auth。

---

## 11. 跨模块集成契约

### 11.1 Adapter SDK（L3-3）

Adapter：

1. 构造 AgentCard、Observer、Authorizer。
2. `server.New` 后注册 sendMessage/getTask；如为 Knowledge Service 再注册 4 个扩展业务 handler。
3. 将 Adapter framework callback 转为 Task 状态，不由 A2A Core 保存 Task。
4. 监听 8080 HTTPS；probe 使用独立 listener。
5. SIGTERM 先 readiness=false，再等待业务 Task 进入可恢复状态，最后 Shutdown。

### 11.2 Operator / Workflow（L3-1）

- Workflow 仅依赖 `client.Client` interface；测试注入 fake。
- Operator 使用特权 SPIFFE ID，但必须走同一 auth/trace/metric 路径。
- Agent Card reconcile 拉取逻辑可复用 `client.CardClient`，不得复制 TLS/validation。
- Operator 负责 Service/EndpointSlice 生命周期；A2A client 只读 watch。

### 11.3 Knowledge Service / Memory backend（L3-5/L3-6）

- Knowledge Service 同 Pod 注册 4 handler。
- Memory backend 通过 Go interface 被 handler 调用，但该 interface 定义在 Knowledge/Memory 模块，不在 A2A Core。
- scope/agent-private/审计/CRD 写入由业务层负责；A2A Core 只传播 caller SPIFFE ID、trace/task context。
- MemoryReconciler 不直接启动 A2A Server。

### 11.4 依赖清单

| 依赖 | 用途 | 约束 |
|------|------|------|
| Go stdlib `net/http`,`crypto/tls`,`log/slog`,`embed` | transport/server/config/schema | Go 1.22+ |
| OpenTelemetry Go | trace/metric | API 由调用方 provider 注入 |
| prometheus/client_golang | 6 指标 | 禁止全局重复注册 panic |
| spiffe-go | Workload API/SVID | 请求热路径只读原子快照 |
| client-go + discovery/v1 EndpointSlice | K8s discovery | 可选；显式 URL 模式不初始化 |
| x/sync/singleflight | cache miss 合并 | 防 discovery 惊群 |
| x/time/rate | token bucket | server/client limiter |
| JSON Schema 2020-12 实现 | params/result validation | schema 全本地 embed |

**禁止依赖**：Agent framework SDK、controller-runtime、MCP SDK、Knowledge/Memory/Operator 包。

---

## 12. L4 实施顺序与完成定义

### 12.1 推荐实现批次

1. **Batch A（协议纯类型）**：types + errors + statemachine + schemas。
2. **Batch B（最小可通信）**：server handler/registry/Card/health + client transport/wrappers。
3. **Batch C（可靠性）**：retry/circuit/P2C/discovery/cache/watch。
4. **Batch D（安全）**：identity/SVID/TLS/auth middleware。
5. **Batch E（可观测）**：trace/metrics/logging。
6. **Batch F（集成）**：Adapter fake + kind E2E + conformance。

每个 Batch 独立 PR，前一批测试通过后再进入下一批；不得以“后续补测试”跨批次。

### 12.2 Definition of Done

- [ ] 文件树中所有生产文件已实现或通过评审显式裁剪。
- [ ] 6 method typed wrapper + params/result schema 全部存在。
- [ ] 5 标准 + 9 扩展错误码及 HTTP/retry 映射测试通过。
- [ ] Task FSM 合法/非法转换全覆盖。
- [ ] 4 HTTP endpoint 可运行；JSON-RPC batch/SSE/cancel 未泄露。
- [ ] mTLS 双向认证 + SPIFFE 热更新 +授权规则通过。
- [ ] TTL + EndpointSlice watch + singleflight + LRU 有测试。
- [ ] 重试/熔断/P2C 在 race test 下通过。
- [ ] 6 个 Prometheus 指标和 OTel span 通过集成测试。
- [ ] 单元覆盖率门禁达标；fuzz/race/conformance/E2E 有可追踪结果。
- [ ] `go vet`、`golangci-lint`、依赖漏洞扫描通过。
- [ ] godoc 覆盖全部 exported symbols；README 示例不绕过 A2A。

---

## 13. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1-draft | 2026-07-24 | 初稿：约 70 文件；7 子包；6 method；4 HTTP endpoint；类型/schema/错误/FSM；Server/Client；Discovery/重试/熔断/P2C；SPIFFE/mTLS；6 指标；271 UT + 3 fuzz + 15 IT + 22 CF + 5 E2E 映射；关闭 L2-1 的 5 个开放问题 |

---

## 附录 A：跨文档引用清单

| 引用 | 位置 | 本 Spec 消费内容 | 状态 |
|------|------|-----------------|------|
| 项目宪法 | `CONSTITUTION.md` §2.1/2.3/2.4/2.6、§3.5-3.7、§4.1、§6.1、§7、§9、§14-16 | 协议优先、失败、安全、可观测、测试、设计门禁 | ✅ v0.4.0 |
| L1 Architecture | `docs/design/L1-architecture.md` §3.4/§6/§7/§8.2 | 通信层、C-2、端口、调用流 | ✅ v0.1.0 |
| L1 System Spec | `docs/spec/L1-system-spec.md` §5/§15 | A2A types、6 method、HTTP/error/schema | ✅ v0.1.0 |
| L2-1 Design | `docs/design/L2-modules/L2-a2a-protocol.md` | 7 子包、算法、身份、可观测 | ✅ v0.1.0 |
| L2-1 Spec | `docs/spec/L2-module-specs/L2-a2a-protocol.md` | exported API、23 配置行、schema、37 测试基线 | ✅ v0.1.0 |
| L2-1 Review | `docs/reviews/l2-1-a2a-protocol-review.md` | 10 维度结论、5 个 L3 移交项 | ✅ 通过 |
| L2-2 Operator | `docs/spec/L2-module-specs/L2-operator-core.md` | Workflow client、Agent Card reconcile | ✅ v0.1.0 |
| L2-3 Adapter | `docs/spec/L2-module-specs/L2-adapter.md` | Server 嵌入、6 handler 注册、8080 | ✅ v0.1.0 |
| L2-4 Knowledge/Memory | `docs/spec/L2-module-specs/L2-knowledge-memory.md` | 4 handler 最终归属、共享 Deployment | ✅ v0.1.0 |
| L3-1 Operator Core | `docs/spec/L3-file-specs/L3-operator-core.md` | Client 消费、Service/EndpointSlice、跨模块测试 | ⏳ v0.1-draft |

---

## 附录 B：开放问题（移交评审或 L4）

| ID | 问题 | 当前倾向 | 决策点 |
|----|------|----------|--------|
| B.1 | JSON Schema Go 实现库选型 | 选择完整支持 draft 2020-12、可离线编译、维护活跃者 | L4 首批依赖 PR，需记录版本与漏洞扫描 |
| B.2 | UUIDv7 库 vs 自实现 | 使用维护活跃的 UUID 库，不自写随机/时间位算法 | L4 Batch A |
| B.3 | 显式 external endpoint 的 Card URL 重定向策略 | 默认禁止跨 host，允许显式 allowlist | 安全评审 |
| B.4 | K8s resolver 是否默认 watch 全 namespace | 默认仅 client 所在 namespace；跨 namespace按需 watch | 性能/RBAC 评审 |
| B.5 | Card 缓存 1,000 entries 是否需配置化 | v0.1 常量；观测到压力后再暴露公共 key | L4 benchmark |
| B.6 | HTTP status 与 JSON-RPC “通常 200”兼容性 | 保持 L1 已定义的 HTTP 映射；conformance adapter 可提供 always-200 模式但默认关闭 | Conformance 接入时复核 |
| B.7 | `canceled` 类型保留是否会被误认为 v0.1 支持 | godoc/handler registry 双重标注；不提供 Cancel wrapper | L3 评审 |
| B.8 | probe 是否需要独立默认端口 | 由 Adapter/部署 Spec 决定；A2A Core 提供 Handler 不强占端口 | L3-3 |

> 以上问题均不阻塞本文件评审；任何改变公共 API、协议语义或安全默认值的决议必须回写本 Spec，必要时走 ADR。
