# Cover Image Specs — Phase 5 LAUNCH

> **Audience**: designer / maintainer with image tools
>
> **Status**: ⏳ pending creation — blocks 3 launch channels (Product Hunt, dev.to, Twitter quote-tweets)
>
> **Tools**: any raster editor (Figma / Sketch / GIMP / Photoshop / Inkscape / Canva)
>
> **Output**: PNG files committed to `docs/launch/`

---

## Asset 1: `cover-ph.png` — Product Hunt cover

### Spec

- **Size**: 240 × 240 px (square, required by PH)
- **Format**: PNG, sRGB, max 3 MB
- **Background**: subtle gradient (light → medium blue) or solid `#0F172A` (dark slate)
- **No text overlays** in the logo itself (PH adds its own title/description)

### Layout

```
┌──────────────────────────────┐
│                              │
│         superteam            │
│           ═══════            │
│         -a2a                 │
│                              │
│   [stylized K8s wheel icon]  │
│         + [agent node]       │
│                              │
│   "K8s · A2A · Apache 2.0"   │
│                              │
└──────────────────────────────┘
```

### Design elements

| Element | Spec |
|---|---|
| **Brand name** | "superteam" (white) + "-a2a" (cyan accent #22D3EE) |
| **Underline** | horizontal rule under "superteam" |
| **K8s icon** | 7-spoke wheel in cyan (#22D3EE), 80px diameter, centered |
| **Agent node** | small filled circle above the wheel, 12px diameter, white |
| **Tagline at bottom** | "K8s · A2A · Apache 2.0" in 11pt sans-serif, white at 70% opacity |
| **Font** | Inter / IBM Plex Sans / system sans |
| **Style** | flat, minimal, no shadows, no gradients on text |

### Color palette

| Token | Hex | Use |
|---|---|---|
| Background | `#0F172A` | dark slate |
| Accent cyan | `#22D3EE` | K8s icon, "-a2a" |
| Accent green | `#10B981` | (optional) agent node |
| Text white | `#F8FAFC` | "superteam", tagline |
| Subtle gray | `#94A3B8` | separator lines |

### Don'ts

- ❌ Don't use red, orange, or yellow (warning vibes)
- ❌ Don't include faces or photos
- ❌ Don't add extra text beyond what's listed
- ❌ Don't use stock photos or 3D renders
- ❌ Don't add borders or rounded corners (PH adds them)

---

## Asset 2: `cover-devto.png` — dev.to article cover

### Spec

- **Size**: 1000 × 420 px (2.38:1, recommended by dev.to)
- **Format**: PNG, sRGB, max 4 MB
- **Aspect**: wide hero image
- **Style**: clean, technical, slightly playful

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   superteam-a2a                            ╱─────╲             │
│   ────────────                            │       │            │
│                                          │  K8s   │            │
│   "Multi-Framework                      │ wheel  │            │
│    Agent Orchestration                  ╲───────╱             │
│    on Kubernetes"                                                 │
│                                                                │
│   [code snippet mockup]                  [A2A flow arrows]      │
│   kubectl get agentsets                  →  →  →                 │
│   NAME  FRAMEWORK  STATUS                                        │
│   lc-1  langchain  Running                                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Design elements

| Element | Spec |
|---|---|
| **Brand** | "superteam-a2a" in white, 48pt, top-left |
| **Tagline** | "Multi-Framework Agent Orchestration on Kubernetes" in cyan, 18pt, below brand |
| **K8s wheel** | 120px, cyan + green spokes, right side |
| **Code snippet** | 240×140, dark background `#1E293B`, mono font, top-right of center |
| **A2A arrows** | 3 right-arrows flowing right-to-left, between wheel and code snippet |
| **Background** | dark gradient `#0F172A` → `#1E293B` (top-left to bottom-right) |
| **Font** | Inter / IBM Plex Sans for prose, JetBrains Mono for code |

### Color palette

| Token | Hex | Use |
|---|---|---|
| Background top | `#0F172A` | dark slate |
| Background bottom | `#1E293B` | lighter slate |
| Code background | `#0F172A` | matches main bg |
| Code text | `#E2E8F0` | light gray |
| Code keywords | `#22D3EE` | cyan |
| Code strings | `#10B981` | green |
| Accent | `#22D3EE` | K8s wheel, arrows |

### Don'ts

- ❌ Don't include too much code (5-7 lines max)
- ❌ Don't use stock photos
- ❌ Don't include "before/after" comparisons
- ❌ Don't add a call-to-action button (dev.to adds one)
- ❌ Don't use emoji in the design itself

---

## Asset 3: `demo.gif` / `demo.mp4` — Twitter quote-tweet GIF

### Spec

- **Size**: 1280 × 720 px (16:9, HD)
- **Format**: GIF (Twitter-friendly) or MP4 (for blog embeds)
- **Length**: 30-60 seconds (looped GIF) or 60-90 seconds (MP4)
- **File size**: GIF max 15 MB / MP4 max 50 MB
- **Frame rate**: 15-24 fps for GIF / 30 fps for MP4

### Source

Per [`docs/launch/demo-video-script.md`](./demo-video-script.md) storyboard:

| Scene | Time | What to capture |
|---|---|---|
| 0:25-0:35 | 10s | `kind create cluster` + `helm install hello-agent` |
| 0:35-0:40 | 5s | `kubectl get agentsets` |
| 0:40-0:45 | 5s | `curl .well-known/agent.json | jq` |
| 0:45-0:55 | 10s | `curl -X POST /jsonrpc` A2A message |

Total GIF candidate: ~30 seconds (scenes 0:25-0:55).

### Recording workflow

```bash
# 1. Record terminal scenes
asciinema rec demo.cast --title "superteam-a2a demo"
# Run each command
# Ctrl-D or `exit` to end

# 2. Convert to GIF
docker run --rm -v $(pwd):/data asciinema/asciicast2gif \
  -s 1.0 -w 100 -h 30 demo.cast demo.gif

# 3. Or convert to MP4 (higher quality)
agg demo.cast demo.gif  # agg is the new asciicast2gif replacement
# Then ffmpeg:
ffmpeg -i demo.gif -c:v libx264 -pix_fmt yuv420p -movflags +faststart demo.mp4
```

### Don'ts

- ❌ Don't include voice-over in the GIF (GIFs are silent)
- ❌ Don't add background music (Twitter may mute)
- ❌ Don't make it longer than 60 seconds (Twitter cut-off)
- ❌ Don't use terminal themes that look like malware (avoid green-on-black)
- � Don't show errors or stack traces

### Recording environment

- **Terminal**: 24pt font, dark theme (Solarized Dark or One Dark)
- **Resolution**: 1920×1080 capture → downscale to 1280×720
- **Tool**: `asciinema` + `agg` (or `terminalizer`)
- **Cluster**: local `kind` cluster (5-min setup)

---

## Production checklist

- [x] `docs/launch/cover-ph.png` (240×240) — blocks Product Hunt
- [x] `docs/launch/cover-devto.png` (1000×420) — blocks dev.to
- [x] `docs/launch/demo.gif` (1280×720, 6 帧 storyboard 占位, 18s 循环) — blocks Twitter quote-tweets
- [ ] `docs/launch/demo.mp4` (1920×1080, 60-90s) — 待 maintainer 录制真实 demo 替换占位 (`bash scripts/record_demo.sh`)

After creation:

- [x] Run `file docs/launch/cover-ph.png` to verify size (240×240, 8.5KB)
- [x] Run `file docs/launch/cover-devto.png` to verify size (1000×420, 31KB)
- [ ] Run `file docs/launch/demo.mp4` to verify codec (待 asciinema 录制后)
- [x] Commit + push (commit `9f92701` · PR #71 · squash merged 2026-09-03)
- [ ] Update `submission-checklist.md` to mark "✅" for visual assets (本 §F 同步 commit)

---

## Maintenance

When the architecture changes:

- **System overview**: re-export from `docs/architecture/system-overview.md` (Mermaid → SVG via `mmdc`)
- **Single-process backend**: re-export from `docs/architecture/single-process-backend.md`
- **CRD relationships**: re-export from `docs/architecture/crd-relationships.md`
- **Demo video**: re-record per `docs/launch/demo-video-script.md` (scenes that change with each release)

Re-export script:

```bash
# Export all Mermaid diagrams to SVG
for f in docs/architecture/*.md; do
  mmdc -i "$f" -o "${f%.md}.svg"
done
```

---

<sub>Maintainer action: 2-3 hour creative session to produce 3 assets. Use any raster editor. Commit PNG/SVG files (not the editable source). Reference from launch channels.</sub>
