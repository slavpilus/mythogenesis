"""LLM calls and deterministic local fallback (handover section 9).

All provider-specific code (Hugging Face Inference API) stays behind these three
public functions. The app MUST run even with no working model by falling back to
deterministic local behaviour, so tests and Space startup never depend on the network.

Model: a single named <=32B model for births, narration, and epitaph.
Document the exact model ID and parameter count in README.md and SUBMISSION.md.

Config via environment:
- HF_TOKEN: Hugging Face token for the Inference API (optional; fallback used if absent)

TODO (next session):
- generate_births: batched call, strip code fences, parse + validate JSON
  (aligned length, lowercase single word, valid hex color), else inheritance/fallback
- narrate_step: one present-tense sentence, pinned voice
- write_epitaph: 3-5 line found poem on extinction/stabilization
- _fallback_* deterministic helpers used on any model failure
"""

from __future__ import annotations


def generate_births(batch: list[dict]) -> list[dict]:
    """Grow one child {word, color} per parent triple. Never raises; falls back."""
    raise NotImplementedError


def narrate_step(payload: dict) -> str:
    """Return exactly one present-tense sentence about the latest births/myths."""
    raise NotImplementedError


def write_epitaph(payload: dict) -> str:
    """Return a short found poem from the surviving words."""
    raise NotImplementedError
