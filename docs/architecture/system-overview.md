# System Overview — superteam-a2a

> **Audience**: launch readers, architecture reviewers, new contributors
>
> **Source**: [`docs/design/L1-architecture.md`](../design/L1-architecture.md) v0.2.0 — text-based ASCII art in §2.2
>
> **Status**: ✅ ready for use in README + docs site + launch channels

## High-level architecture

```mermaid
graph TB
    User["👤 User<br/>kubectl / Helm / Dashboard<br/>(future)"]
    
    subgraph K8s["☸️ Kubernetes Cluster"]
        subgraph Operator["� Operator Pod (Python · single process)"]
            Kopf["kopf reconcilers<br/>Agent / AgentSet / Workflow<br/>MemoryReconciler"]
            ASGI["Starlette ASGI<br/>JSON-RPC 2.0 over HTTP/SSE<br/>A2A endpoints"]
            KS["Knowledge Service<br/>BM25 + 4-level scope"]
            MS["Memory Service<br/>confidence + decay + reinforce"]
        end
        
        subgraph CRDs["📦 CRDs (6 v1alpha1)"]
            CRDA["Agent"]
            CRDAS["AgentSet"]
            CRDW["Workflow"]
            CRDKS["KnowledgeScope"]
            CRDKI["KnowledgeItem"]
            CRDM["Memory"]
        end
        
        KAPI["🗄️ K8s API / etcd"]
        
        subgraph Agents["🤖 Agent Pods"]
            HA["Hello Agent<br/>(reference)"]
            LA["LangChain Adapter<br/>(future)"]
            AA["AutoGen Adapter<br/>(future)"]
            CA["CrewAI Adapter<br/>(future)"]
        end
        
        NetPol["🔒 NetworkPolicy<br/>(default-deny + explicit allow)"]
    end
    
    Prom["📊 Prometheus<br/>25 metrics + 8 alerts"]
    ACM["🔐 cert-manager<br/>(opt-in mTLS)"]
    
    User -->|"apply YAML"| CRDs
    User -->|"helm install"| Operator
    CRDs -.->|"watch"| Kopf
    Kopf -->|"reconcile"| CRDs
    CRDs <-->|"CRUD"| KAPI
    
    HA -.->|"A2A JSON-RPC"| ASGI
    LA -.->|"A2A JSON-RPC"| ASGI
    AA -.->|"A2A JSON-RPC"| ASGI
    CA -.->|"A2A JSON-RPC"| ASGI
    
    ASGI --> KS
    ASGI --> MS
    ASGI -->|"admission<br/>50ms fail-closed"| KAPI
    
    Kopf -->|"metrics"| Prom
    ASGI -->|"metrics"| Prom
    
    ACM -.->|"cert"| ASGI
    NetPol -.->|"isolation"| Agents
    
    classDef operator fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef crd fill:#fff3e0,stroke:#e65100
    classDef agent fill:#f3e5f5,stroke:#4a148c
    classDef external fill:#e8f5e9,stroke:#1b5e20
    
    class Kopf,ASGI,KS,MS operator
    class CRDA,CRDAS,CRDW,CRDKS,CRDKI,CRDM crd
    class HA,LA,AA,CA agent
    class User,Prom,ACM external
```

## Key architectural properties

### 1. Single-process backend (ADR-0006 v1.0 D 方案)

The Operator Pod runs **one Python process** containing:
- kopf reconciler (CRD lifecycle management)
- Starlette ASGI app (A2A JSON-RPC endpoints)
- Knowledge Service (BM25 + scope resolver)
- Memory Service (confidence + decay + reinforce)

This was a deliberate architectural decision. See [`single-process-backend.md`](./single-process-backend.md) for details.

### 2. 6 CRDs

| CRD | Role |
|---|---|
| `Agent` | a single AI agent wrapped in a K8s resource |
| `AgentSet` | horizontally-scalable fleet of agents with shared config |
| `Workflow` | declarative DAG of agent steps (v0.5+) |
| `KnowledgeScope` | 4-level scope (industry / org / team / project) |
| `KnowledgeItem` | a piece of knowledge with BM25-retrievable content |
| `Memory` | agent experience record with confidence + decay + reinforce |

### 3. A2A protocol

All agent-to-agent communication goes through Google's A2A protocol:
- `Agent Card` published at `.well-known/agent.json`
- `Message`, `Task`, `Artifact`, `Streaming` types
- JSON-RPC 2.0 over HTTP/SSE
- DNS-style discovery across namespaces

See [`a2a-protocol-flow.md`](./a2a-protocol-flow.md) for the request flow.

### 4. Production-grade security

- **Pod Security**: restricted profile, non-root UID 1000, read-only rootfs
- **NetworkPolicy**: default-deny + explicit allow
- **RBAC**: dual Role (read + write with `admissionregistration.k8s.io`/`authentication.k8s.io`/`authorization.k8s.io`)
- **Admission webhook**: 50ms fail-closed (actual p95: 28ms)
- **cert-manager mTLS**: opt-in via `tls.enabled=true`

## Data flow

1. **User applies YAML** defining a CRD (e.g., `Agent`).
2. **kopf reconciler** picks up the event via K8s watch API.
3. **kopf** idempotently reconciles desired state (creates / updates / deletes child resources).
4. **Agent Pod** boots, registers itself, publishes `Agent Card` at `.well-known/agent.json`.
5. **Agent A** sends A2A message to **Agent B** via JSON-RPC 2.0.
6. **ASGI app** validates the request through **admission webhook** (50ms budget).
7. **Resolver** routes the request to **Agent B**'s pod via DNS-style discovery.
8. **Agent B** processes the message, returns `Task` or streams `Artifact` via SSE.
9. **Prometheus** scrapes metrics from the Operator + Agent pods (30s interval).

## Where this diagram appears

- [`README.md`](../../README.md) — top-level system context
- Launch channels: PH / HN / dev.to / Reddit / 掘金 — referenced as "architecture diagram"
- [`docs/adr/0006-memory-transport.md`](../adr/0006-memory-transport.md) — D 方案 rationale

## Rendering notes

- Mermaid renders natively in GitHub markdown + mkdocs-material
- For static export to SVG, use `mmdc -i system-overview.md -o system-overview.svg`
- Color scheme matches the docs site theme (light: `#e1f5ff`, dark: keep contrasts)
