"""Gradio wiring only (handover section 10).

A single gr.Blocks page: three stacked bands (sky / grid / story) rendered as custom
SVG/HTML, plus a control strip. No landing page - the demo seed is planted and running
on load, so the first screen is the playable toy. All game logic lives in
life_core / semantics / model_backend / render / seed_patterns; this file only builds
the UI and connects events.

Run locally:  uv run python app.py
On HF Spaces:  this file is the app_file (see README.md frontmatter).
"""

from __future__ import annotations

from pathlib import Path

import gradio as gr

import config
from render import render_stage
from semantics import Game

_HERE = Path(__file__).parent
_CSS = (_HERE / "static" / "app.css").read_text(encoding="utf-8")
_HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=Cormorant+Garamond:wght@400;500;600&family=EB+Garamond:ital,wght@0,400;0,500;1,400"
    "&family=Spectral:ital,wght@0,400;0,500;1,400&family=Space+Grotesk:wght@400;500;600;700"
    '&family=JetBrains+Mono:wght@400;500&display=swap" />'
)

MOOD = "manuscript"  # fixed mood (no in-app switcher)
SPEED = 0.5  # generations per second (fixed)
TICK_INTERVAL = 1.0 / SPEED  # seconds per generation


def _running_timer(active: bool) -> gr.Timer:
    return gr.Timer(value=TICK_INTERVAL, active=active)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Mythogenesis", fill_height=True) as demo:
        game = gr.State()
        running = gr.State(False)

        with gr.Column(elem_id="myth-root"):
            stage = gr.HTML(render_stage(None), elem_id="stage-html")
            with gr.Row(elem_id="controls"):
                seed = gr.Textbox(
                    value=config.DEMO_SEED,
                    placeholder="type seed words…",
                    elem_classes=["seed-box"],
                    container=False,
                    scale=4,
                    lines=1,
                )
                plant_btn = gr.Button("Plant", elem_classes=["btn-primary"], scale=0)
                demo_btn = gr.Button("Plant demo", elem_classes=["btn-accent"], scale=0)
                step_btn = gr.Button("Step", scale=0)
                auto_btn = gr.Button("Auto-tick", scale=0)
                reset_btn = gr.Button("Reset", scale=0)

        tick = gr.Timer(value=TICK_INTERVAL, active=False)

        # ---- handlers --------------------------------------------------------------
        def on_load():
            g = Game()
            snap = g.seed(config.DEMO_SEED, is_demo=True)
            return g, render_stage(snap, MOOD), True, _running_timer(True), "Pause"

        def on_plant(g, text):
            g = g or Game()
            snap = g.seed(text or config.DEMO_SEED, is_demo=False)
            return g, render_stage(snap, MOOD), True, _running_timer(True), "Pause"

        def on_demo(g):
            g = g or Game()
            snap = g.seed(config.DEMO_SEED, is_demo=True)
            return (
                g,
                config.DEMO_SEED,
                render_stage(snap, MOOD),
                True,
                _running_timer(True),
                "Pause",
            )

        def on_step(g):
            g = g or Game()
            if not g.registry:
                g.seed(config.DEMO_SEED, is_demo=True)
            snap = g.step()
            return g, render_stage(snap, MOOD), False, gr.Timer(active=False), "Auto-tick"

        def on_toggle(g, run):
            g = g or Game()
            run = not run
            active = run and not g.ended
            return g, run, _running_timer(active), ("Pause" if active else "Auto-tick")

        def on_reset(g, text):
            g = g or Game()
            snap = g.seed(text or config.DEMO_SEED, is_demo=False)
            return g, render_stage(snap, MOOD), True, _running_timer(True), "Pause"

        def on_tick(g, run):
            if not g or not run or g.ended:
                return g, gr.skip(), run, gr.Timer(active=False), gr.skip()
            snap = g.step()
            if g.ended:
                return g, render_stage(snap, MOOD), False, gr.Timer(active=False), "Auto-tick"
            return g, render_stage(snap, MOOD), True, _running_timer(True), "Pause"

        # ---- wiring ----------------------------------------------------------------
        plant_io = [game, stage, running, tick, auto_btn]
        demo.load(on_load, None, plant_io)
        plant_btn.click(on_plant, [game, seed], plant_io)
        seed.submit(on_plant, [game, seed], plant_io)
        demo_btn.click(on_demo, [game], [game, seed, stage, running, tick, auto_btn])
        step_btn.click(on_step, [game], plant_io)
        auto_btn.click(on_toggle, [game, running], [game, running, tick, auto_btn])
        reset_btn.click(on_reset, [game, seed], plant_io)
        tick.tick(on_tick, [game, running], plant_io)

    return demo


if __name__ == "__main__":
    build_app().launch(css=_CSS, head=_HEAD)
