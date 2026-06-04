"""Seed cleaning and deterministic pattern placement (handover section 7).

Curated moving/oscillating patterns (glider, toad, beacon, LWSS, ...) placed near
the centre on collision courses, so the board opens with cross-pollination rather
than isolated cells drifting into empty space.

TODO (next session):
- parse_seed: lowercase, drop stopwords/punctuation, enforce SEED_MIN..SEED_MAX
- plant: partition words across pattern cell counts (repeat strong words to fill,
  never meaningless filler), place patterns, assign one word per live seed cell,
  register unique seed words as the pantheon
"""

from __future__ import annotations

# Cell-count of each curated pattern (handover section 7).
PATTERN_SIZES = {
    "glider": 5,
    "toad": 6,
    "beacon": 6,
    "lwss": 9,  # lightweight spaceship
}


def parse_seed(text: str) -> list[str]:
    """Clean seed text into a validated list of lowercase words."""
    raise NotImplementedError
