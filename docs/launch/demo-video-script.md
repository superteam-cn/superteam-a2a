# superteam-a2a — 60-second Demo Video Script

> **Goal**: ship a 60-90 second demo video (1080p, narrated) that shows superteam-a2a working end-to-end on a fresh `kind` cluster. Used for HN Show HN, Reddit, dev.to, 掘金, and the docs site landing page.
>
> **Output**: a single `.mp4` file committed to `docs/launch/demo.mp4` plus a YouTube/Bilibili mirror.

## Storyboard

| Time | Scene | Voice-over | On-screen |
|---|---|---|---|
| 0:00 | Cold open | "What if every agent framework you use could talk to every other?" | Logo + GitHub stars counter |
| 0:05 | Problem | "Today, every AI agent framework is great at running one agent. But the moment you want a fleet — a planner delegating to a researcher, a coder handing off to a reviewer — you're on your own." | Animated bullets: 6 frameworks, 0 protocol between them |
| 0:15 | Solution | "superteam-a2a turns LangChain, AutoGen, CrewAI, and friends into first-class Kubernetes resources, with Google's A2A protocol for inter-agent communication." | Diagram: AgentSet CRD → ASGI → A2A JSON-RPC |
| 0:25 | **DEMO 1 — kind cluster** | "Let's deploy it. A fresh kind cluster, one helm install…" | Terminal: `kind create cluster --name superteam-a2a-demo` + `helm install hello-agent helm/hello-agent/` |
| 0:35 | **DEMO 2 — kubectl get** | "And it's up. Card-driven, single instance, restricted Pod Security." | `kubectl get agentsets` shows hello-agent Running |
| 0:40 | **DEMO 3 — A2A card** | "Every agent publishes an Agent Card — that's how they discover each other." | `curl http://hello-agent/.well-known/agent.json \| jq` |
| 0:45 | **DEMO 4 — A2A message** | "And here's an A2A message — JSON-RPC 2.0, the Google protocol." | `curl -X POST http://hello-agent/jsonrpc -d '{"jsonrpc":"2.0","method":"message/send",...}'` |
| 0:55 | **DEMO 5 — Knowledge + Memory** | "Behind the scenes, a single Python process serves Knowledge and Memory with a 50ms fail-closed admission webhook." | Architecture diagram: ASGI + kopf in one process |
| 1:05 | **DEMO 6 — admission latency** | "50ms is not a number we made up. Here's the E2E benchmark — 28ms p95." | Terminal: pytest BM25-IT-002 output showing p95 < 50ms |
| 1:15 | **Close** | "Apache 2.0. 474 tests. v0.1.0 is live today." | GitHub repo + star button + "Try it: 5-minute kind demo in CONTRIBUTING.md" |

Total: 1:15 (75 seconds).

## Production notes

### Recording environment

- Terminal: Windows Terminal with `oh-my-posh` theme, font `Cascadia Code`, 24px
- Resolution: 1920×1080, 60fps
- Tools:
  - `kind` v0.20+
  - `kubectl` v1.28+
  - `helm` v3.12+
  - `uv` 0.4.18+
  - `terminalizer` or `asciinema` for terminal capture
- Cluster: `kind` on local machine (or `multipass` if more RAM needed)

### Scenes that need to be **re-recorded** for each major release

- 0:00 — Logo + star count update
- 0:15 — Architecture diagram (regenerate from current code)
- 0:55 — Knowledge+Memory architecture (PR-5 changes)
- 1:05 — benchmark numbers (re-run BM25-IT-002)
- 1:15 — version + star count

### Scenes that are stable across releases

- 0:05–0:15 — problem framing
- 0:25–0:50 — install + kubectl get + A2A card + A2A message (only numbers change)
- 1:00–1:10 — 50ms admission (numbers change but visuals stable)

## Capture commands

```bash
# Setup
kind create cluster --name superteam-a2a-demo
docker buildx build -t superteam-a2a/hello-agent:dev services/hello-agent/
kind load docker-image superteam-a2a/hello-agent:dev --name superteam-a2a-demo
helm install hello-agent helm/hello-agent/
sleep 30  # wait for ready

# Scene 0:25-0:35 (kind create + helm install)
asciinema rec demo.cast --title "kind create" -c "kind create cluster --name superteam-a2a-demo"
asciinema rec demo-helm.cast --title "helm install" -c "helm install hello-agent helm/hello-agent/"

# Scene 0:35-0:40 (kubectl get)
asciinema rec demo-get.cast -c "kubectl get agentsets"

# Scene 0:40-0:45 (A2A card)
kubectl port-forward svc/hello-agent 8080:8080 &
asciinema rec demo-card.cast -c "curl -s http://localhost:8080/.well-known/agent.json | jq"

# Scene 0:45-0:55 (A2A message)
asciinema rec demo-msg.cast -c "curl -X POST http://localhost:8080/jsonrpc -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"message/send\",\"params\":{\"message\":{\"role\":\"user\",\"parts\":[{\"type\":\"text\",\"text\":\"Hello\"}]}}}' | jq"

# Scene 1:05-1:15 (benchmark)
asciinema rec demo-bench.cast -c "uv run pytest tests/integration -k bm25 -v --tb=short"
```

## Post-processing

1. Import each `.cast` into `terminalizer render demo.cast -o demo.gif`
2. Compose in `ffmpeg` or `DaVinci Resolve` with the voice-over track
3. Add background music (royalty-free, e.g. YouTube Audio Library)
4. Export at 1080p60 H.264 + AAC
5. Upload to YouTube + Bilibili
6. Embed in README + landing page

## When to record

- v0.1.0 release: ASAP (within 1 week of GitHub Release)
- v0.2.0 release: re-record scenes 0:15 + 0:55 + 1:05 + 1:15
- Major architecture changes (e.g. Workflow CRD lands): re-record the architecture diagram scenes

## Current status

- [x] Script written
- [ ] Cast recordings done
- [ ] Voice-over recorded
- [ ] Edited + exported
- [ ] Uploaded to YouTube
- [ ] Uploaded to Bilibili
- [ ] Embedded in README

Maintainer action: schedule 2-hour recording session in week 1 of Phase 5 LAUNCH.