"""Conway mechanics only (handover sections 8 & 12).

Pure, Gradio-free, semantics-free toroidal Game of Life (B3/S23) with wraparound
modulo the board size. Works on a flat ``list[int]`` of length ``N*N`` (0 = dead,
1 = alive) plus the side length ``N``, so it is trivial to unit test.

The semantic layer (``semantics.py``) maps the structural births returned here onto
parent words; this module never touches words, colours, or tiers.
"""

from __future__ import annotations


def neighbor_indices(idx: int, n: int) -> list[int]:
    """The 8 toroidal neighbours of a flat index on an ``n x n`` board."""
    r, c = divmod(idx, n)
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr = (r + dr) % n
            cc = (c + dc) % n
            out.append(rr * n + cc)
    return out


def count_live_neighbors(grid: list[int], idx: int, n: int) -> int:
    """Number of live toroidal neighbours of ``idx``."""
    return sum(grid[j] for j in neighbor_indices(idx, n))


def step(grid: list[int], n: int) -> tuple[list[int], dict[int, list[int]], list[int]]:
    """Advance one generation under B3/S23.

    Returns ``(next_grid, births, deaths)`` where:
      - ``next_grid`` is the new flat alive array,
      - ``births`` maps each newly-born cell index to the list of its live-neighbour
        indices in scan order (each birth has exactly 3 by Conway's B3 rule),
      - ``deaths`` is the list of indices that died this step.
    """
    size = n * n
    nxt = [0] * size
    births: dict[int, list[int]] = {}
    deaths: list[int] = []

    for idx in range(size):
        live_nb = [j for j in neighbor_indices(idx, n) if grid[j]]
        cnt = len(live_nb)
        if grid[idx]:
            if cnt == 2 or cnt == 3:
                nxt[idx] = 1
            else:
                deaths.append(idx)
        elif cnt == 3:
            nxt[idx] = 1
            births[idx] = live_nb
    return nxt, births, deaths
