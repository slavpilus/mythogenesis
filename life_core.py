"""Conway mechanics only (handover sections 8 & 12).

Pure, Gradio-free toroidal Game of Life so the core is unit-testable.
B3/S23 rules with wraparound modulo BOARD.

TODO (next session, TDD per handover section 12):
- count_live_neighbors with wraparound
- step(): apply B3/S23, return next grid + list of birth positions with parent words
- preserve duplicate parent identity via tuple(sorted(parents)) signatures (section 4)
"""

from __future__ import annotations


def count_live_neighbors(grid: list[list[dict]], row: int, col: int) -> int:
    """Count the 8 toroidal neighbours of (row, col) that are alive."""
    raise NotImplementedError


def step(grid: list[list[dict]]) -> tuple[list[list[dict]], list[dict]]:
    """Advance one generation.

    Returns (next_grid, births) where each birth records its position and the
    three live parent words (duplicates preserved, in a list of length 3).
    """
    raise NotImplementedError
