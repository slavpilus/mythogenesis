"""SVG / HTML rendering for the three-band UI (handover section 10).

Pure rendering helpers (string in, HTML/SVG string out) so they stay testable and
independent of Gradio wiring.

TODO (next session):
- render_grid: inline SVG, one fixed-size <rect> per cell (size independent of word
  length), word in <title> for native hover, tier styling, newborn flash
- render_sky: pantheon as fixed bright stars, myths as dimming stars by TTL
- render_story: rolling prose + birth ticker (e.g. "fire + fire + smoke -> ash")
  + generation/live-count/myth-count/model-call-count readout
"""

from __future__ import annotations


def render_grid(grid: list[list[dict]], registry: dict) -> str:
    """Return inline SVG for the board."""
    raise NotImplementedError
