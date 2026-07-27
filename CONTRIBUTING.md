# Contributing to superteam-a2a

🎉 First of all — thank you for taking the time to contribute. We're a young project (launched 2026-07-08) and the right contribution at the right moment can shape the API for everyone.

## 📜 Code of Conduct

This project adheres to the [Contributor Covenant v2.1](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold it.

## 🚦 Project status

We're currently in **pre-alpha**. The first preview (v0.1) targets the **A2A protocol > v0.3** and **Kubernetes > 1.28** with a minimal LangChain adapter. If you want to influence the API, **the best moment to file an issue is now, before v0.1 is shipped**.

## 🧭 Where to start

| You want to…                          | Start here                                                                 |
|---------------------------------------|----------------------------------------------------------------------------|
| Influence the API design              | Open an [issue with the `api-design` label](.github/ISSUE_TEMPLATE/api-design.md) |
| Report a bug                          | Open a [bug report](.github/ISSUE_TEMPLATE/bug_report.md)                  |
| Propose a feature                     | Open a [feature request](.github/ISSUE_TEMPLATE/feature_request.md)        |
| Build a new framework adapter         | Read [`docs/architecture.md`](./docs/architecture.md) (will land with v0.1)|
| Improve docs                          | Pick anything in [`docs/`](./docs)                                         |

## 🛠️ Local development setup

> Will be expanded when v0.1 lands. Until then, please open an issue before writing code so we can avoid wasted effort.

## ✅ Pull request process

1. Open an issue first to discuss the change (especially for non-trivial work).
2. Fork the repository and create your branch from `main`.
3. Run the test suite locally — instructions will land with v0.1.
4. Make sure your commit messages reference the issue (`#123`).
5. Open a PR with a clear description and a link to the issue.

## 📋 Coding conventions

- **Go**: standard `gofmt` + `golangci-lint` (will be defined at v0.1).
- **Python**: `ruff format` + `ruff check`.
- **YAML / manifests**: 2-space indent, run through `pre-commit` (config to be added at v0.1).
- **Commit messages**: [Conventional Commits](https://www.conventionalcommits.org/) — types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## 🙏 Reporting security issues

**Do not file public issues for suspected security vulnerabilities.** Email the maintainer at the address in [`SECURITY.md`](./SECURITY.md) (will be added at v0.1).

## License

By contributing, you agree that your contributions will be licensed under [Apache 2.0](./LICENSE).
