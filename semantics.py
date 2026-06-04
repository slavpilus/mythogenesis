"""Registry, signatures, promotion, myths, story trimming (handover sections 5, 8).

Keeps the meaning layer independent of Conway mechanics and of Gradio.

TODO (next session, TDD per handover section 12):
- WordRecord registry keyed by word string
- duplicate-safe parent signature: tuple(sorted(parent_words))
- signature cache to avoid repeated model calls
- progeny credit (+1 per parent per birth) and tier recomputation
- myth pool: add/refresh TTL, decrement, evict expired, enforce MYTH_CAP
- rolling story window trim (keep newest STORY_WINDOW sentences)
- strongest-neighbour selection for inheritance fallback (config.TIER_RANK)
"""

from __future__ import annotations


def parent_signature(parent_words: list[str]) -> tuple[str, ...]:
    """Duplicate-preserving, orientation-independent signature for a birth.

    Uses tuple(sorted(...)) so ("fire","fire","smoke") stays distinct from
    ("fire","smoke","smoke") (handover section 4).
    """
    raise NotImplementedError
