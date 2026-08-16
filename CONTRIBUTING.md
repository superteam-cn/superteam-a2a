# Contributing to superteam-a2a

🎉 First of all — thank you for taking the time to contribute. We're a young project (launched 2026-07-08, v0.1.0 shipped 2026-08-16) and the right contribution at the right moment can shape the API for everyone.

## 📜 Code of Conduct

This project adheres to the [Contributor Covenant v2.1](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold it.

## 🚦 Project status

**v0.1.0 is ready** (main HEAD `a8afdc3`, 466/466 tests PASS). We're now in **Phase 5 — Launch + Polish** (see [ROADMAP.md](./ROADMAP.md)).

This means: the **core protocol runtime is stable**. Breaking changes will only happen via a documented ADR. Most contributions now fall into one of:

- 🧩 **Framework adapters** (LangChain / AutoGen / CrewAI / Semantic Kernel / Strands / Smolagents) — see `docs/design/L2-modules/L2-adapter.md`
- 📚 **Documentation, examples, and tutorials**
- 🐛 **Bug reports and small fixes**
- ⚙️ **Workflow CRD** (declarative DAG) — see `docs/spec/L3-file-specs/`

If you want to influence the API surface, the best moment to file an issue is **before v0.5 ships**, where we expect one more breaking-change window.

## 🧭 Where to start

| You want to…                          | Start here                                                                 |
|---------------------------------------|----------------------------------------------------------------------------|
| Influence the API design              | Open an [issue with the `api-design` label](.github/ISSUE_TEMPLATE/api-design.md) |
| Report a bug                          | Open a [bug report](.github/ISSUE_TEMPLATE/bug_report.md)                  |
| Propose a feature                     | Open a [feature request](.github/ISSUE_TEMPLATE/feature_request.md)        |
| Build a new framework adapter         | Read `docs/design/L2-modules/L2-adapter.md` + `packages/adapter-sdk/`      |
| Add a workflow step type              | Read `docs/spec/L3-file-specs/L3-workflow.md` (when it lands)              |
| Improve docs                          | Pick anything in `docs/`                                                   |

## 🛠️ Local development setup

### Prerequisites

- **Python 3.12+** (we test against 3.12 in CI)
- **uv** ≥ 0.4.18 (Astral's Python package manager — [install](https://github.com/astral-sh/uv))
- **git** with submodule support
- **Docker** + **kind** (optional, only for E2E tests): `brew install kind docker` or see [kind docs](https://kind.sigs.k8s.io/)
- **Helm** ≥ 3.12 (optional, for chart validation): `brew install helm`

### First-time clone

```bash
git clone https://github.com/superteam-cn/superteam-a2a.git
cd superteam-a2a
uv sync --all-packages --all-extras    # ~30s, installs 8 workspace members
```

### Run the test suite

```bash
# Unit + integration (fast, ~2s, 466 tests)
uv run pytest --tb=short -q

# Unit only (faster, ~1s)
uv run pytest tests/unit -q

# Integration only
uv run pytest tests/integration -q

# E2E (requires kind cluster + docker)
uv run pytest tests/e2e -m e2e -v
```

### 4-gate static check (same as CI)

```bash
uv run ruff check .                      # lint
uv run ruff format --check .             # formatting
uv run pyright packages/ services/ tests/  # types
uv run pytest --tb=short -q               # tests
```

All four must pass before a PR can be merged.

### Run a local kind cluster with the Hello Agent

```bash
# 1. Spin up a cluster
kind create cluster --name superteam-a2a-dev

# 2. Build the Hello Agent image (multi-stage Dockerfile)
docker buildx build -t superteam-a2a/hello-agent:dev services/hello-agent/

# 3. Load it into kind
kind load docker-image superteam-a2a/hello-agent:dev --name superteam-a2a-dev

# 4. Install via Helm
helm install hello-agent helm/hello-agent/

# 5. Verify
kubectl get agentsets
kubectl port-forward svc/hello-agent 8080:8080 &
curl http://localhost:8080/.well-known/agent.json | jq
```

### Run a local kind cluster with the Knowledge Service

```bash
# Same as above but for the knowledge-memory-service chart
docker buildx build -t superteam-a2a/knowledge-memory-service:dev services/knowledge-memory-service/
kind load docker-image superteam-a2a/knowledge-memory-service:dev --name superteam-a2a-dev
helm install knowledge-memory-service helm/knowledge-memory-service/

# Apply a sample KnowledgeScope
kubectl apply -f examples/knowledge-scope-team.yaml

# Send an A2A record_memory request
curl -X POST http://localhost:8080/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"record_memory","params":{"scope":"team-x","content":"Project kickoff"}}'
```

## ✅ Pull request process

1. **Open an issue first** to discuss the change (especially for non-trivial work — adapters, new CRDs, breaking changes).
2. **Fork the repository** and create your branch from `main`. Branch name: `<type>/<short-description>` (e.g. `feat/langchain-adapter`, `fix/admission-timeout`).
3. **Make your changes**, following the coding conventions below.
4. **Run the 4-gate check** locally:
   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run pyright packages/ services/ tests/ && uv run pytest -q
   ```
5. **Commit using [Conventional Commits](https://www.conventionalcommits.org/)** — types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`. Reference the issue number in the commit body (`Refs #123` or `Closes #123`).
6. **Push to your fork** and open a PR with a clear description linking the issue.
7. **Wait for CI**: 4 workflows must pass — `Lint / Type-check / Test (Python 3.12)`, `CodeQL (python)`, `CodeQL (actions)`, `Release Drafter`.
8. **Squash merge**: A maintainer will squash-merge once the PR is approved and CI is green.

## 📋 Coding conventions

- **Python**: `ruff format` + `ruff check` (configured in `pyproject.toml`). No exceptions.
- **Type hints**: required for all new code. `pyright` is run in strict-ish mode.
- **Pydantic v2**: use `BaseModel` with `populate_by_name=True` and `extra="forbid"` for all wire-contract types (see `packages/knowledge/`).
- **Async**: prefer `async def` for I/O. Use the `kopf` operator pattern (see `services/knowledge-memory-service/`).
- **YAML / manifests**: 2-space indent. Validated by `helm lint` in CI.
- **Commit messages**: [Conventional Commits](https://www.conventionalcommits.org/) — `feat`, `fix`, `docs`, `refactor`, `test`, `chore`. Reference the issue.
- **Test naming**: `<COMPONENT>-<LAYER>-<NNN>` (e.g. `HELM-UT-001`, `E2E-002`). See `docs/spec/L3-file-specs/L3-knowledge-service.md §10` for the full naming scheme.

## 🏗️ Architecture cheat-sheet

If you're new to the codebase, read these in order:

1. [CONSTITUTION.md](./docs/adr/CONSTITUTION.md) — the 17-section architectural law
2. [docs/design/L1-architecture.md](./docs/design/L1-architecture.md) — the high-level view
3. [docs/admin/l4-package-layout.md](./docs/admin/l4-package-layout.md) — what lives where
4. [ADR-0006 v1.0](./docs/adr/0006-memory-transport.md) — why we chose single-process (D 方案)
5. [docs/reviews/l3-6-memory-backend-spec-review.md](./docs/reviews/l3-6-memory-backend-spec-review.md) — the latest design review

## 🙏 Reporting security issues

**Do not file public issues for suspected security vulnerabilities.** Email the maintainer at the address in [SECURITY.md](./SECURITY.md).

## License

By contributing, you agree that your contributions will be licensed under [Apache 2.0](./LICENSE).