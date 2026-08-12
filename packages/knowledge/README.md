# superteam-a2a-knowledge

Knowledge Service CRD types — Pydantic v2 implementations of L3-5 Knowledge Service v0.2.0.

3 CRD types (`KnowledgeScope` + `KnowledgeItem` + `Memory`) + 5 auxiliary value objects
(`ScopeReference` + `SubjectReference` + `InheritRules` + `ItemReference` + `DecayState`)
+ 4 StrEnum (`ScopeLevel` + `ScopePhase` + `KnowledgeVisibility` + `SubjectKind` +
`KnowledgeType` + `ItemPhase` + `MemoryPhase` + `GCState`).

依据：
- L3-5 `docs/spec/L3-file-specs/L3-knowledge-service.md` §3.1-§3.3
- L2-4 `docs/spec/L2-module-specs/L2-knowledge-memory.md` §3.2-§3.4
- ADR-0002 知识管理设计 / ADR-0003 Memory 设计

wire YAML contract 与 Helm chart CRD 1:1 对齐。