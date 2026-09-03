#!/usr/bin/env python3
"""
generate_launch_assets.py — Phase 5 LAUNCH 视觉资产生成器

按 docs/launch/{og-image-spec,cover-image-specs,demo-video-script}.md 规格
用 PIL 生成 4 个视觉资产：
  1. og-image.png     1280x640   (GitHub social preview + Twitter/FB/LinkedIn/Slack/Discord)
  2. cover-ph.png      240x240   (Product Hunt)
  3. cover-devto.png  1000x420   (dev.to article)
  4. demo.gif         1280x720   (Twitter quote-tweets, ≤60s loop)

设计语言统一: dark slate #0F172A → #1E293B 渐变 · 青色 #22D3EE accent ·
绿色 #10B981 二级 accent · 白色 #F8FAFC 文字 · Segoe UI 字体 (Windows fallback)
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ----- constants --------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "docs" / "launch"

# color palette (per spec)
BG_TOP = "#0F172A"  # dark slate
BG_BOTTOM = "#1E293B"  # lighter slate
BRAND_WHITE = "#F8FAFC"
ACCENT_CYAN = "#22D3EE"
ACCENT_GREEN = "#10B981"
SUBTLE_GRAY = "#94A3B8"
CODE_BG = "#0F172A"
CODE_TEXT = "#E2E8F0"

# Windows fonts (Inter / IBM Plex Sans / JetBrains Mono not installed;
# Segoe UI is the closest sans-serif on Windows)
FONT_SANS = "C:/Windows/Fonts/segoeui.ttf"
FONT_SANS_BOLD = "C:/Windows/Fonts/seguisb.ttf"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"
FONT_FALLBACK = "C:/Windows/Fonts/arial.ttf"


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Try requested font, fall back to Arial, then PIL default."""
    for candidate in [path, FONT_FALLBACK]:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


# ----- gradient background (numpy-accelerated) --------------------------------


def gradient_bg(
    width: int, height: int, c1_hex: str, c2_hex: str, direction: str = "diagonal"
) -> Image.Image:
    """Linear gradient. direction: 'diagonal' | 'vertical' | 'horizontal'."""
    try:
        import numpy as np

        c1 = np.array(hex_to_rgb(c1_hex), dtype=np.float32)
        c2 = np.array(hex_to_rgb(c2_hex), dtype=np.float32)
        if direction == "diagonal":
            y, x = np.mgrid[0:height, 0:width]
            t = (x + y) / (width + height - 2)
        elif direction == "vertical":
            t = np.linspace(0, 1, height, dtype=np.float32).reshape(-1, 1)
            t = np.broadcast_to(t, (height, width)).copy()
        else:  # horizontal
            t = np.linspace(0, 1, width, dtype=np.float32).reshape(1, -1)
            t = np.broadcast_to(t, (height, width)).copy()
        arr = c1 * (1 - t[..., None]) + c2 * t[..., None]
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, "RGB")
    except ImportError:
        # fallback: per-pixel (slow but works)
        c1 = hex_to_rgb(c1_hex)
        c2 = hex_to_rgb(c2_hex)
        img = Image.new("RGB", (width, height))
        px = img.load()
        for y in range(height):
            for x in range(width):
                if direction == "diagonal":
                    t = (x + y) / (width + height - 2)
                elif direction == "vertical":
                    t = y / max(1, height - 1)
                else:
                    t = x / max(1, width - 1)
                px[x, y] = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        return img


# ----- decorative helpers -----------------------------------------------------


def draw_k8s_wheel(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    spoke_color: str = ACCENT_CYAN,
    hub_color: str = ACCENT_GREEN,
    line_width: int | None = None,
) -> None:
    """7-spoke K8s-style helm wheel: outer ring + 7 radial spokes + inner hub."""
    if line_width is None:
        line_width = max(2, radius // 14)

    # outer ring (slightly darker)
    outer_r = radius
    draw.ellipse(
        [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r],
        outline=spoke_color,
        width=line_width,
    )

    # 7 spokes radiating from center, first pointing up (north)
    n_spokes = 7
    spoke_inner = radius // 4  # don't draw through hub
    for i in range(n_spokes):
        angle = math.radians(-90 + i * (360 / n_spokes))
        x_end = cx + outer_r * math.cos(angle)
        y_end = cy + outer_r * math.sin(angle)
        x_start = cx + spoke_inner * math.cos(angle)
        y_start = cy + spoke_inner * math.sin(angle)
        # alternate cyan/green spokes for visual rhythm
        col = spoke_color if i % 2 == 0 else hub_color
        draw.line([(x_start, y_start), (x_end, y_end)], fill=col, width=line_width)

    # inner hub: filled circle with cyan ring
    hub_r = radius // 3
    draw.ellipse(
        [cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r],
        fill=BG_TOP,
        outline=spoke_color,
        width=max(2, line_width),
    )


def draw_agent_node(
    draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int = 6, color: str = BRAND_WHITE
) -> None:
    """Small filled circle = 'agent node' above the K8s wheel."""
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
    # subtle outer halo
    halo = radius + 4
    draw.ellipse(
        [cx - halo, cy - halo, cx + halo, cy + halo],
        outline=color,
        width=1,
    )


def draw_text_aa(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    anchor: str | None = None,
) -> None:
    """Anti-aliased text render (PIL default for FreeType fonts)."""
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


# ==============================================================================
# Asset 1: og-image.png (1280 x 640)
# ==============================================================================


def gen_og_image() -> Image.Image:
    w, h = 1280, 640
    img = gradient_bg(w, h, BG_TOP, BG_BOTTOM, "diagonal")
    draw = ImageDraw.Draw(img, "RGBA")

    # left 2/3 = text, right 1/3 = visual
    # ----- brand block (top-left) -----
    f_brand = load_font(FONT_SANS_BOLD, 72)
    f_underline_h = 4  # 4px thick
    draw_text_aa(draw, (80, 130), "superteam", f_brand, BRAND_WHITE)
    # underline under "superteam" only
    bbox = draw.textbbox((80, 130), "superteam", font=f_brand, anchor="lt")
    ul_y = bbox[3] + 12
    # measure "superteam" width and add "-a2a" cyan
    f_a2a = load_font(FONT_SANS_BOLD, 72)
    sup_w = draw.textlength("superteam", font=f_brand)
    a2a_x = 80 + int(sup_w) + 14
    draw_text_aa(draw, (a2a_x, 130), "-a2a", f_a2a, ACCENT_CYAN)
    # underline only under "superteam"
    draw.rectangle([80, ul_y, 80 + int(sup_w), ul_y + f_underline_h], fill=ACCENT_CYAN)

    # ----- tagline -----
    f_tag = load_font(FONT_SANS, 30)
    draw_text_aa(draw, (80, 250), "Multi-Framework Agent Orchestration on K8s", f_tag, BRAND_WHITE)

    # ----- 3 bullets -----
    f_bul = load_font(FONT_SANS, 24)
    bullets = [
        "•  6 CRDs · 474 tests · Apache 2.0",
        "•  Google A2A protocol (JSON-RPC 2.0)",
        "•  LangChain / CrewAI / AutoGen / custom",
    ]
    for i, b in enumerate(bullets):
        draw_text_aa(draw, (96, 340 + i * 44), b, f_bul, BRAND_WHITE)

    # ----- K8s wheel (right side) -----
    wheel_cx, wheel_cy, wheel_r = 1020, 320, 190
    draw_k8s_wheel(draw, wheel_cx, wheel_cy, wheel_r)
    # agent node above wheel
    draw_agent_node(draw, wheel_cx, wheel_cy - wheel_r - 30, radius=14)

    return img


# ==============================================================================
# Asset 2: cover-ph.png (240 x 240) — Product Hunt
# ==============================================================================


def gen_cover_ph() -> Image.Image:
    w, h = 240, 240
    img = gradient_bg(w, h, BG_TOP, BG_BOTTOM, "diagonal")
    draw = ImageDraw.Draw(img, "RGBA")

    # ----- brand (centered, compact) -----
    f_brand = load_font(FONT_SANS_BOLD, 26)
    sup_w = int(draw.textlength("superteam", font=f_brand))
    a2a_w = int(draw.textlength("-a2a", font=f_brand))
    gap = 4
    total_w = sup_w + gap + a2a_w
    x_start = (w - total_w) // 2
    y_brand = 36
    draw_text_aa(draw, (x_start, y_brand), "superteam", f_brand, BRAND_WHITE)
    draw_text_aa(draw, (x_start + sup_w + gap, y_brand), "-a2a", f_brand, ACCENT_CYAN)
    # underline under "superteam"
    bbox = draw.textbbox((x_start, y_brand), "superteam", font=f_brand, anchor="lt")
    ul_y = bbox[3] + 4
    draw.rectangle([x_start, ul_y, x_start + sup_w, ul_y + 2], fill=ACCENT_CYAN)

    # ----- K8s wheel (center) -----
    wheel_cx, wheel_cy, wheel_r = w // 2, 138, 56
    draw_k8s_wheel(draw, wheel_cx, wheel_cy, wheel_r, line_width=3)
    # agent node above
    draw_agent_node(draw, wheel_cx, wheel_cy - wheel_r - 12, radius=5)

    # ----- tagline at bottom -----
    f_tag = load_font(FONT_SANS, 11)
    tagline = "K8s · A2A · Apache 2.0"
    tw = int(draw.textlength(tagline, font=f_tag))
    draw_text_aa(draw, ((w - tw) // 2, h - 24), tagline, f_tag, BRAND_WHITE)

    return img


# ==============================================================================
# Asset 3: cover-devto.png (1000 x 420) — dev.to article
# ==============================================================================


def gen_cover_devto() -> Image.Image:
    w, h = 1000, 420
    img = gradient_bg(w, h, BG_TOP, BG_BOTTOM, "diagonal")
    draw = ImageDraw.Draw(img, "RGBA")

    # ----- brand top-left -----
    f_brand = load_font(FONT_SANS_BOLD, 48)
    draw_text_aa(draw, (60, 60), "superteam-a2a", f_brand, BRAND_WHITE)
    # cyan underline under "superteam"
    sup_w = int(draw.textlength("superteam", font=f_brand))
    bbox = draw.textbbox((60, 60), "superteam", font=f_brand, anchor="lt")
    draw.rectangle([60, bbox[3] + 6, 60 + sup_w, bbox[3] + 10], fill=ACCENT_CYAN)

    # ----- tagline -----
    f_tag = load_font(FONT_SANS, 18)
    draw_text_aa(
        draw, (60, 130), "Multi-Framework Agent Orchestration on Kubernetes", f_tag, ACCENT_CYAN
    )

    # ----- code snippet (left-center) -----
    code_x, code_y, code_w, code_h = 60, 200, 380, 140
    # rounded rect bg
    draw.rounded_rectangle(
        [code_x, code_y, code_x + code_w, code_y + code_h],
        radius=6,
        fill=CODE_BG,
        outline=SUBTLE_GRAY,
        width=1,
    )
    # terminal-style prompt
    f_mono = load_font(FONT_MONO, 14)
    lines = [
        ("$ kubectl get agentsets", CODE_TEXT),
        ("NAME       FRAMEWORK    STATUS", SUBTLE_GRAY),
        ("lc-1       langchain    Running", ACCENT_GREEN),
        ("ca-1       crewai       Running", ACCENT_GREEN),
        ("ag-1       autogen      Pending", ACCENT_CYAN),
    ]
    for i, (line, color) in enumerate(lines):
        draw_text_aa(draw, (code_x + 14, code_y + 14 + i * 22), line, f_mono, color)

    # ----- A2A flow arrows (middle, right of code) -----
    f_arrow = load_font(FONT_SANS_BOLD, 36)
    arrow_y = code_y + code_h // 2
    for i in range(3):
        ax = 470 + i * 36
        draw_text_aa(draw, (ax, arrow_y - 18), "→", f_arrow, ACCENT_CYAN)

    # ----- K8s wheel (right side, bigger) -----
    wheel_cx, wheel_cy, wheel_r = 820, 210, 110
    draw_k8s_wheel(draw, wheel_cx, wheel_cy, wheel_r, line_width=5)
    draw_agent_node(draw, wheel_cx, wheel_cy - wheel_r - 24, radius=9)

    return img


# ==============================================================================
# Asset 4: demo.gif (1280 x 720, storyboard placeholder)
# ==============================================================================


def _demo_storyboard_card(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    frame_num: int,
    total_frames: int,
    scene_title: str,
    scene_subtitle: str,
    terminal_lines: list[tuple[str, str]],
) -> None:
    """Render one storyboard card on top of img."""
    w, h = img.size
    # terminal-style dark bg overlay (most of the screen)
    margin = 40
    term_x, term_y = margin, margin + 100
    term_w, term_h = w - 2 * margin, h - 2 * margin - 100
    draw.rounded_rectangle(
        [term_x, term_y, term_x + term_w, term_y + term_h],
        radius=10,
        fill=CODE_BG,
        outline=SUBTLE_GRAY,
        width=2,
    )

    # window chrome (3 dots)
    for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        draw.ellipse(
            [term_x + 16 + i * 22, term_y + 16, term_x + 28 + i * 22, term_y + 28],
            fill=c,
        )

    # title bar
    f_title = load_font(FONT_SANS, 14)
    title_text = scene_title
    draw_text_aa(draw, (term_x + 100, term_y + 16), title_text, f_title, SUBTLE_GRAY)

    # subtitle above terminal
    f_sub = load_font(FONT_SANS, 28)
    draw_text_aa(draw, (margin, margin), scene_subtitle, f_sub, BRAND_WHITE)
    f_sub2 = load_font(FONT_SANS, 16)
    draw_text_aa(
        draw,
        (margin, margin + 50),
        f"scene {frame_num + 1}/{total_frames}",
        f_sub2,
        SUBTLE_GRAY,
    )

    # terminal content
    f_mono = load_font(FONT_MONO, 22)
    line_h = 30
    # vertical center the lines
    total_lines_h = len(terminal_lines) * line_h
    y_start = term_y + (term_h - total_lines_h) // 2
    for i, (line, color) in enumerate(terminal_lines):
        draw_text_aa(
            draw,
            (term_x + 24, y_start + i * line_h),
            line,
            f_mono,
            color,
        )


def gen_demo_frames() -> list[Image.Image]:
    """6 storyboard frames telling the demo flow."""
    w, h = 1280, 720
    scenes = [
        (
            "01 / cluster",
            "kind create cluster",
            [
                ("$ kind create cluster --name superteam-a2a-demo", CODE_TEXT),
                ("Creating cluster 'superteam-a2a-demo' ...", SUBTLE_GRAY),
                ("[OK] Control plane node ready", ACCENT_GREEN),
                ("[OK] CNI installed", ACCENT_GREEN),
                ("[OK] Cluster ready in 42s", ACCENT_GREEN),
            ],
        ),
        (
            "02 / install",
            "helm install hello-agent",
            [
                ("$ helm install hello-agent helm/hello-agent/", CODE_TEXT),
                ("NAME: hello-agent", SUBTLE_GRAY),
                ("LAST DEPLOYED: 2026-09-03 09:42:01.234", SUBTLE_GRAY),
                ("NAMESPACE: default", SUBTLE_GRAY),
                ("STATUS: deployed", ACCENT_GREEN),
                ("REVISION: 1", SUBTLE_GRAY),
            ],
        ),
        (
            "03 / agentsets",
            "kubectl get agentsets",
            [
                ("$ kubectl get agentsets", CODE_TEXT),
                ("NAME     FRAMEWORK     STATUS    AGE", SUBTLE_GRAY),
                ("lc-1     langchain     Running   12s", ACCENT_GREEN),
                ("ca-1     crewai        Running   12s", ACCENT_GREEN),
                ("ag-1     autogen       Running   12s", ACCENT_GREEN),
            ],
        ),
        (
            "04 / discover",
            "curl /.well-known/agent.json",
            [
                ("$ curl -s hello-agent/.well-known/agent.json | jq", CODE_TEXT),
                ("{", SUBTLE_GRAY),
                ('  "name": "hello-agent",', CODE_TEXT),
                ('  "framework": "langchain",', CODE_TEXT),
                ('  "skills": ["echo", "translate", "summarize"],', ACCENT_CYAN),
                ('  "version": "0.1.0"', CODE_TEXT),
                ("}", SUBTLE_GRAY),
            ],
        ),
        (
            "05 / invoke",
            "A2A JSON-RPC message",
            [
                ("$ curl -X POST hello-agent/jsonrpc \\", CODE_TEXT),
                ('    -d \'{"jsonrpc":"2.0","method":"message/send",', CODE_TEXT),
                ('         "params":{"message":{"role":"user",', CODE_TEXT),
                ('                   "parts":[{"text":"hello"}]}},\'', CODE_TEXT),
                ('         "id":"1"}"', CODE_TEXT),
                ('{"jsonrpc":"2.0","result":{"message":{...}},"id":"1"}', ACCENT_GREEN),
            ],
        ),
        (
            "06 / scale",
            "kubectl scale",
            [
                ("$ kubectl scale agentset lc-1 --replicas=5", CODE_TEXT),
                ("agentset.agent.superteam-a2a/lc-1 scaled", SUBTLE_GRAY),
                ("$ kubectl get agentsets", CODE_TEXT),
                ("NAME     FRAMEWORK    STATUS    REPLICAS", SUBTLE_GRAY),
                ("lc-1     langchain    Running   5/5", ACCENT_GREEN),
                ("ca-1     crewai       Running   1/1", ACCENT_GREEN),
            ],
        ),
    ]

    frames = []
    for idx, (title, subtitle, lines) in enumerate(scenes):
        img = gradient_bg(w, h, BG_TOP, BG_BOTTOM, "diagonal")
        draw = ImageDraw.Draw(img, "RGBA")

        # add subtle grid pattern in background
        grid_color = (255, 255, 255, 8)  # very low alpha
        for gx in range(0, w, 80):
            draw.line([(gx, 0), (gx, h)], fill=grid_color, width=1)
        for gy in range(0, h, 80):
            draw.line([(0, gy), (w, gy)], fill=grid_color, width=1)

        # overlay logo top-right
        f_brand = load_font(FONT_SANS_BOLD, 24)
        draw_text_aa(draw, (w - 220, 24), "superteam-a2a", f_brand, ACCENT_CYAN)

        _demo_storyboard_card(img, draw, idx, len(scenes), title, subtitle, lines)
        frames.append(img)
    return frames


# ==============================================================================
# Main
# ==============================================================================


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[1/4] Generating og-image.png (1280x640) ...")
    og = gen_og_image()
    og.save(OUT_DIR / "og-image.png", "PNG", optimize=True)
    print(f"      -> {OUT_DIR / 'og-image.png'}  ({og.size[0]}x{og.size[1]})")

    print("[2/4] Generating cover-ph.png (240x240) ...")
    ph = gen_cover_ph()
    ph.save(OUT_DIR / "cover-ph.png", "PNG", optimize=True)
    print(f"      -> {OUT_DIR / 'cover-ph.png'}  ({ph.size[0]}x{ph.size[1]})")

    print("[3/4] Generating cover-devto.png (1000x420) ...")
    devto = gen_cover_devto()
    devto.save(OUT_DIR / "cover-devto.png", "PNG", optimize=True)
    print(f"      -> {OUT_DIR / 'cover-devto.png'}  ({devto.size[0]}x{devto.size[1]})")

    print("[4/4] Generating demo.gif (1280x720, 6 frames x 3s loop = 18s) ...")
    frames = gen_demo_frames()
    # each frame held 3 seconds → 18s loop (well within Twitter 60s cut-off)
    durations = [3000] * len(frames)
    frames[0].save(
        OUT_DIR / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(
        f"      -> {OUT_DIR / 'demo.gif'}  ({frames[0].size[0]}x{frames[0].size[1]}, {len(frames)} frames)"
    )

    print()
    print("All 4 visual assets generated.")
    print("Next steps:")
    print("  - Review each asset, give iteration feedback (colors/layout/text)")
    print("  - For demo.gif: asciinema capture script in scripts/record_demo.sh")
    print("  - When satisfied: git add docs/launch/*.png docs/launch/*.gif && commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
