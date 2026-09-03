# Open Graph (Social Preview) Image Spec

> **Audience**: designer / maintainer with image tools
>
> **Status**: ⏳ pending creation — affects all Twitter / Facebook / LinkedIn / Slack link previews
>
> **Output**: `docs/launch/og-image.png` (also uploadable as GitHub repo "Social preview")
>
> **Reference**: [GitHub social preview docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-preview-image)

---

## Spec

- **Size**: 1280 × 640 px (2:1 aspect, recommended by GitHub)
- **Format**: PNG, sRGB, max 1 MB
- **Display contexts**:
  - GitHub repo social preview (replaces default avatar)
  - Twitter card image (when someone shares the repo URL)
  - Facebook / LinkedIn link preview
  - Slack unfurl
  - Discord embed
  - Open Graph meta tag (`<meta property="og:image">`)

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   superteam-a2a                                                  │
│   ────────────                                                   │
│                                                                  │
│   Multi-Framework Agent                          ┌─────────┐    │
│   Orchestration on Kubernetes                    │         │    │
│                                                  │  K8s    │    │
│   • 6 CRDs                                       │ wheel   │    │
│   • Google A2A protocol                          │   +     │    │
│   • 474 tests · Apache 2.0                       │  agent  │    │
│                                                  │  node   │    │
│                                                  └─────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Design elements

| Element | Spec |
|---|---|
| **Brand** | "superteam-a2a" in white, 72pt, top-left |
| **Underline** | horizontal rule under "superteam", 4px thick, cyan accent |
| **Tagline** | "Multi-Framework Agent Orchestration on Kubernetes" in white, 32pt, below brand |
| **Bullets** | 3-4 key features in white at 80% opacity, 24pt sans-serif |
| **K8s wheel** | 200px, cyan + green spokes, right-side |
| **Agent node** | small filled circle above the wheel, white |
| **Background** | dark gradient `#0F172A` (top-left) → `#1E293B` (bottom-right) |
| **Font** | Inter / IBM Plex Sans |

## Color palette

| Token | Hex | Use |
|---|---|---|
| Background top | `#0F172A` | dark slate |
| Background bottom | `#1E293B` | lighter slate |
| Brand white | `#F8FAFC` | "superteam-a2a", tagline |
| Accent cyan | `#22D3EE` | K8s wheel, underline, "a2a" |
| Accent green | `#10B981` | K8s wheel spokes |
| Subtle gray | `#94A3B8` | (optional) separator lines |

## Composition rules

1. **Left 2/3 = text**, right 1/3 = visual
2. **Brand name is largest element** — reads at thumbnail size
3. **No faces, no stock photos, no logos of other projects** (legal/safety)
4. **No emoji in the design itself** (renders inconsistently)
5. **Don't include the GitHub star count** (it changes; OG images are cached)

## Don'ts

- ❌ Don't use red / orange / yellow (warning vibes)
- ❌ Don't include URLs in the design (they become illegible at thumbnail)
- ❌ Don't add "new" / "release" badges (PH/HN already add their own)
- ❌ Don't include dates / version numbers (the image will be reused for v0.2+)
- ❌ Don't use stock photos or 3D renders

## Setup instructions

### GitHub social preview

1. Create `docs/launch/og-image.png` per spec
2. Open <https://github.com/superteam-cn/superteam-a2a/settings>
3. Click "Social preview" → "Upload an image"
4. Select `og-image.png`
5. Save

The image will appear:
- On the repo header (replaces the default avatar)
- In Twitter / Facebook / LinkedIn link previews
- In Slack / Discord embeds

### Open Graph meta tag

If you want to control the OG image independently of GitHub (e.g., for the docs site):

```html
<meta property="og:image" content="https://superteam-cn.github.io/superteam-a2a/og-image.png">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="640">
<meta property="og:title" content="superteam-a2a">
<meta property="og:description" content="Multi-Framework Agent Orchestration on Kubernetes, powered by Google A2A protocol">
<meta property="og:type" content="website">
```

Add to `docs/index.md` (mkdocs home page) or `docs/overrides/main.html` (mkdocs-material template override).

## Production checklist

- [ ] `docs/launch/og-image.png` (1280×640, ≤1 MB)
- [ ] Verify thumbnail at 200×100 — text still legible
- [ ] Verify in Twitter card validator: <https://cards-dev.twitter.com/validator>
- [ ] Verify in Facebook Sharing Debugger: <https://developers.facebook.com/tools/debug/>
- [ ] Upload to GitHub repo Settings → Social preview
- [ ] Add `<meta property="og:image">` to docs site (optional)

## Difference from cover-image-specs.md

| Asset | Size | Purpose | Where |
|---|---|---|---|
| `cover-ph.png` | 240×240 | Product Hunt | PH launch surface |
| `cover-devto.png` | 1000×420 | dev.to | dev.to article cover |
| `og-image.png` | 1280×640 | Open Graph | All social link previews |

The OG image is **largest** because it appears in the most contexts. Make this one first — it has the highest ROI.

---

<sub>Maintainer action: 1-2 hour creative session to produce og-image.png. Use any raster editor. Upload to GitHub Settings → Social preview.</sub>
