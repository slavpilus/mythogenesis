"""SVG / HTML rendering for the three-band UI (handover section 10).

Pure functions (snapshot in, HTML string out) ported from the design handoff's
React/SVG components, adapted to Gradio's server-render model: each generation the
whole stage HTML is rebuilt, so only cells born this generation carry the newborn
flash and only just-risen myths carry the ascension entrance.

Bands: sky (crystallized memory) / grid (live ecosystem) / story (leaky memory).
Default mood is "manuscript" with the "glyphs" sky treatment, matching where the
design landed.
"""

from __future__ import annotations

import html

import model_backend as mb

N = 64

# tier opacity on the board
_TIER_OPACITY = {"mundane": 0.82, "story": 0.92, "legend": 1.0, "myth": 1.0, "pantheon": 1.0}


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


# --------------------------------------------------------------------------------------
# Grid band
# --------------------------------------------------------------------------------------
def _tier_stroke(tier: str) -> tuple[str, float]:
    """Glow-ladder stroke (the design's default tier style)."""
    if tier == "story":
        return "rgba(255,255,255,.14)", 0.06
    if tier == "legend":
        return "var(--accent)", 0.13
    if tier in ("myth", "pantheon"):
        return "var(--gold)", 0.17
    return "none", 0.0


def render_grid(snap: dict | None, glow: float = 0.5, cell_gap: float = 0.3) -> str:
    if not snap:
        return (
            '<svg class="grid-svg" viewBox="0 0 64 64" preserveAspectRatio="xMidYMid meet"></svg>'
        )

    grid, words, born = snap["grid"], snap["words"], snap["born"]
    registry = snap["registry"]
    gen = snap["generation"]
    inset = cell_gap / 2
    size = 1 - cell_gap
    rx = min(0.12, size / 2)

    cells: list[str] = []
    glows: list[str] = []
    for idx, alive in enumerate(grid):
        if not alive:
            continue
        r, c = divmod(idx, N)
        word = words[idx] or ""
        rec = registry.get(word, {"color": "#9aa0a6", "tier": "mundane"})
        tier = rec["tier"]
        color = rec["color"]
        stroke, sw = _tier_stroke(tier)
        opacity = _TIER_OPACITY.get(tier, 1.0)
        flash = " cell-born" if born[idx] == gen and gen > 0 else ""
        style = f"opacity:{opacity}"
        if stroke != "none":
            style += f";stroke:{stroke};stroke-width:{sw}"
        cells.append(
            f'<rect class="cell{flash}" x="{c + inset:.3f}" y="{r + inset:.3f}" '
            f'width="{size:.3f}" height="{size:.3f}" rx="{rx:.3f}" fill="{color}" style="{style}">'
            f"<title>{_esc(word)}  ·  {tier}</title></rect>"
        )
        hi = tier in ("myth", "pantheon")
        mid = tier == "legend"
        if hi or mid:
            s = 2.0 if hi else 1.5
            gfill = "var(--gold)" if hi else color
            gop = (0.5 if hi else 0.32) * glow
            glows.append(
                f'<rect x="{c + 0.5 - s / 2:.3f}" y="{r + 0.5 - s / 2:.3f}" width="{s:.3f}" '
                f'height="{s:.3f}" rx="{s / 2:.3f}" style="fill:{gfill};opacity:{gop:.3f}"/>'
            )

    defs = (
        '<defs><filter id="cellGlow" x="-120%" y="-120%" width="340%" height="340%">'
        '<feGaussianBlur stdDeviation="0.7" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/></feMerge></filter></defs>'
    )
    glow_g = f'<g filter="url(#cellGlow)">{"".join(glows)}</g>'
    return (
        '<svg class="grid-svg" viewBox="0 0 64 64" preserveAspectRatio="xMidYMid meet">'
        f"{defs}{glow_g}<g>{''.join(cells)}</g></svg>"
    )


# --------------------------------------------------------------------------------------
# Sky band
# --------------------------------------------------------------------------------------
def _starfield(count: int = 64) -> list[dict]:
    """Deterministic background stars (LCG seeded 1337, matching the design)."""
    s = 1337
    out = []
    for _ in range(count):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        x = (s / 0x7FFFFFFF) * 100
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        y = (s / 0x7FFFFFFF) * 100
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        rr = 0.1 + (s / 0x7FFFFFFF) * 0.35
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        o = 0.05 + (s / 0x7FFFFFFF) * 0.3
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        dur = 3 + (s / 0x7FFFFFFF) * 5
        out.append({"x": x, "y": y, "r": rr, "o": o, "dur": dur})
    return out


_STARS = _starfield()


def _layout_pantheon(words: list[str]) -> list[dict]:
    n = len(words)
    out = []
    for i, w in enumerate(words):
        h = mb.hash_str(w + "|p")
        x = 24 + (i / (n - 1)) * 62 if n > 1 else 50
        y = 33 + (h % 6)
        out.append({"word": w, "x": x, "y": y})
    return out


def _layout_myths(pool: list[dict], ttl: int = 20) -> list[dict]:
    n = len(pool)
    out = []
    for i, m in enumerate(pool):
        h = mb.hash_str(m["word"] + "|m")
        x = 12 + (i / (n - 1)) * 76 if n > 1 else 50
        y = 56 + (h % 16)
        out.append(
            {
                "word": m["word"],
                "color": m["color"],
                "ttl": m["ttl"],
                "k": max(0.0, m["ttl"] / ttl),
                "x": x,
                "y": y,
            }
        )
    return out


def render_sky(snap: dict | None) -> str:
    pantheon = snap["pantheon"] if snap else []
    myths = snap["myth_pool"] if snap else []
    risen = {a["word"] for a in (snap["ascensions"] if snap else [])}
    pan = _layout_pantheon(pantheon)
    myth = _layout_myths(myths)

    bg = _STARS[:34]
    star_svg = "".join(
        f'<circle class="star-twinkle" cx="{b["x"]:.2f}" cy="{b["y"]:.2f}" r="{b["r"]:.2f}" '
        f'fill="var(--ink)" style="--tw:{b["o"]:.3f};--twdur:{b["dur"]:.1f}s;opacity:{b["o"]:.3f}"/>'
        for b in bg
    )
    sky_svg = (
        '<svg class="sky-svg" viewBox="0 0 100 100" preserveAspectRatio="none">'
        '<defs><filter id="skyGlow" x="-300%" y="-300%" width="700%" height="700%">'
        '<feGaussianBlur stdDeviation="1.1"/></filter></defs>'
        f"{star_svg}</svg>"
    )

    labels = []
    for p in pan:
        labels.append(
            f'<div class="sky-name pantheon glyph" style="left:{p["x"]:.2f}%;top:{p["y"]:.2f}%">'
            f"{_esc(p['word'])}</div>"
        )
    for m in myth:
        k = m["k"]
        op = 0.32 + 0.68 * k
        fs = 14 + 9 * k
        rise = " just-risen" if m["word"] in risen else ""
        labels.append(
            f'<div class="sky-name myth glyph{rise}" style="left:{m["x"]:.2f}%;top:{m["y"]:.2f}%;'
            f'opacity:{op:.3f};font-size:{fs:.1f}px">{_esc(m["word"])}</div>'
        )
    if not myths:
        labels.append(
            '<div class="sky-hint">no myths yet — a word that spawns enough descendants will rise here</div>'
        )

    return (
        '<div class="wordmark"><h1>Mythogenesis</h1><p>rules become folklore</p></div>'
        '<div class="sky-legend">'
        '<div class="row">gods you planted <span class="kd god"></span></div>'
        '<div class="row">myths risen from the board, fading <span class="kd myth"></span></div>'
        "</div>"
        f"{sky_svg}"
        f'<div class="sky-labels">{"".join(labels)}</div>'
    )


# --------------------------------------------------------------------------------------
# Story band
# --------------------------------------------------------------------------------------
def _swatch(snap: dict, word: str, fallback: str = "#888") -> str:
    rec = snap["registry"].get(word)
    return rec["color"] if rec else fallback


def render_story(snap: dict | None) -> str:
    if not snap:
        return ""
    story = snap["story"]
    visible = story[-9:]
    fresh = snap.get("line") is not None
    lines = []
    for i, line in enumerate(visible):
        is_last = i == len(visible) - 1
        cls = "line" + (" fresh" if (is_last and fresh) else "")
        lines.append(f'<p class="{cls}">{_esc(line)}</p>')
    prose = f'<div class="prose"><div class="prose-inner">{"".join(lines)}</div></div>'

    births = snap["births"]
    tick_html = '<div class="ticker"><span class="op">the board is still</span></div>'
    if births:
        best = max(
            births, key=lambda b: snap["registry"].get(b["child"], {"progeny": 0})["progeny"]
        )
        parts = []
        for i, p in enumerate(best["parents"]):
            col = _swatch(snap, p)
            parts.append(
                f'<span class="sw" style="background:{col};color:{col}"></span><span>{_esc(p)}</span>'
            )
            if i < len(best["parents"]) - 1:
                parts.append('<span class="op">+</span>')
        parts.append('<span class="arrow">→</span>')
        parts.append(
            f'<span class="sw" style="background:{best["color"]};color:{best["color"]}"></span>'
        )
        parts.append(f'<span class="child">{_esc(best["child"])}</span>')
        tick_html = f'<div class="ticker fresh">{"".join(parts)}</div>'

    chips = (
        f'<div class="chip">gen <b>{snap["generation"]}</b></div>'
        f'<div class="chip">live <b>{snap["live"]}</b></div>'
        f'<div class="chip myth">myths <b>{len(snap["myth_pool"])}</b></div>'
        f'<div class="chip">calls <b>{snap["model_calls"]}</b></div>'
    )
    side = (
        '<div class="story-side">'
        f'<div><div class="ticker-label">latest birth</div>{tick_html}</div>'
        f'<div><div class="chips-label">transparency</div><div class="chips">{chips}</div></div>'
        "</div>"
    )
    return prose + side


# --------------------------------------------------------------------------------------
# Full stage
# --------------------------------------------------------------------------------------
def render_stage(
    snap: dict | None, mood: str = "manuscript", glow: float = 0.5, cell_gap: float = 0.3
) -> str:
    ended = bool(snap and snap.get("ended"))
    epitaph = ""
    if ended and snap["story"]:
        epitaph = "".join(f"<div>{_esc(seg)}</div>" for seg in snap["story"][-1].split(" / "))
    veil = (
        f'<div class="ended-veil{" on" if ended else ""}">'
        f"{f'<div class=epi>{epitaph}</div>' if ended else ''}</div>"
    )
    return (
        f'<div id="stage" data-mood="{_esc(mood)}" style="--glow-mult:{glow}">'
        f'<div class="band sky">{render_sky(snap)}</div>'
        f'<div class="band grid-band"><div class="grid-wrap">{render_grid(snap, glow, cell_gap)}</div></div>'
        f'<div class="band story" data-layout="wide">{render_story(snap)}</div>'
        f"{veil}"
        "</div>"
    )
