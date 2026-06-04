"""Gradio wiring only (handover section 10).

Single gr.Blocks page, three stacked bands (sky / grid / story), with controls:
Seed textbox, Plant, Plant demo, Step, Auto-tick, Reset. No landing page - the
first screen is the playable toy.

Keep ALL game logic in life_core / semantics / model_backend / render / seed_patterns.
This file only builds the UI and connects events to that logic.

Run locally:  uv run python app.py
On HF Spaces:  this file is the app_file (see README.md frontmatter).

TODO (next session): build the Blocks UI and wire callbacks.
"""

from __future__ import annotations

import gradio as gr


def build_app() -> gr.Blocks:
    """Construct the Gradio Blocks app. TODO: implement the three-band UI."""
    with gr.Blocks(title="Mythogenesis") as demo:
        gr.Markdown("# Mythogenesis\n_A symbolic Game of Life where rules become folklore._")
        gr.Markdown("> Scaffold only - the playable toy is not implemented yet.")
    return demo


if __name__ == "__main__":
    build_app().launch()
