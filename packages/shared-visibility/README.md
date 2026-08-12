# superteam-a2a-shared-visibility

Shared visibility types and Protocol interfaces (PR-3 stub).

**Scope**: 4 modules exposing `Protocol` interfaces + re-exports of
CRD types from `superteam-a2a-knowledge`. No business logic — implementations
deferred to PR-4+.

**Modules**:
- `ScopeResolver` · 4-level scope chain resolution
- `VisibilityMatrix` · 5-dimensional visibility strategy
- `KnowledgeType` · re-export
- `ScopeInherit` · 4-level inheritance filtering

See `docs/spec/L3-file-specs/L3-knowledge-service.md` §10.2 and
`docs/spec/L3-file-specs/L3-memory-backend.md` §1.4.