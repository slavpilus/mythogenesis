"""Seed cleaning and deterministic pattern placement (handover section 7).

Curated moving / oscillating Conway patterns placed near the centre on collision
courses, so the board opens with cross-pollination rather than isolated cells. A
methuselah (R-pentomino) near the centre sustains chaos for ~150+ generations while
oscillators and ships seed colour variety across the quadrants. Pure and Gradio-free.
"""

from __future__ import annotations

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "at",
    "is",
    "it",
    "with",
    "for",
    "by",
    "as",
    "be",
}

# Cell offsets (row, col) for each curated pattern.
PATTERNS = {
    "glider": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
    "toad": [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)],
    "beacon": [(0, 0), (0, 1), (1, 0), (2, 3), (3, 2), (3, 3)],
    "lwss": [(0, 0), (0, 3), (1, 4), (2, 0), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4)],
    "rpent": [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],
    "blinker": [(0, 0), (0, 1), (0, 2)],
}


def parse_seed(text: str) -> list[str]:
    """Lowercase, strip punctuation, drop stopwords and 1-letter tokens."""
    raw = []
    token = []
    for ch in (text or "").lower():
        if ch.isalpha():
            token.append(ch)
        else:
            if token:
                raw.append("".join(token))
                token = []
    if token:
        raw.append("".join(token))
    return [w for w in raw if w not in STOPWORDS and len(w) >= 2]


def place_pattern(
    grid: list[int], born: list[int], name: str, top: int, left: int, n: int, flip: bool = False
) -> list[int]:
    """Stamp a pattern onto ``grid`` (toroidal). Returns placed flat indices in order."""
    placed = []
    for r, c in PATTERNS[name]:
        rr = (top + r) % n
        cc = (left + (-c if flip else c)) % n
        idx = rr * n + cc
        grid[idx] = 1
        if born[idx] < 0:
            born[idx] = 0
        placed.append(idx)
    return placed


def demo_layout(grid: list[int], born: list[int], n: int, is_demo: bool) -> list[int]:
    """Place the curated opening layout. Returns live cell indices in placement order."""
    mid = n // 2
    cells: list[int] = []
    cells += place_pattern(grid, born, "rpent", mid - 2, mid - 2, n)
    cells += place_pattern(grid, born, "glider", mid - 16, mid - 16, n)
    cells += place_pattern(grid, born, "lwss", mid + 10, mid - 18, n)
    cells += place_pattern(grid, born, "toad", mid + 12, mid + 10, n)
    cells += place_pattern(grid, born, "beacon", mid - 14, mid + 12, n)
    if is_demo:
        cells += place_pattern(grid, born, "glider", mid + 14, mid + 14, n, flip=True)
    return cells
