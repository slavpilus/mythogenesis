"""Conway core tests (handover section 12). Pure, no Gradio or network."""

import life_core


def make_grid(coords, n):
    grid = [0] * (n * n)
    for r, c in coords:
        grid[r * n + c] = 1
    return grid


def live_set(grid, n):
    return {(i // n, i % n) for i, v in enumerate(grid) if v}


def step_n(grid, n, times):
    for _ in range(times):
        grid, _, _ = life_core.step(grid, n)
    return grid


def test_blinker_oscillates_period_2():
    n = 8
    horizontal = {(3, 3), (3, 4), (3, 5)}
    grid = make_grid(horizontal, n)

    after1, _, _ = life_core.step(grid, n)
    assert live_set(after1, n) == {(2, 4), (3, 4), (4, 4)}  # rotated to vertical

    after2 = step_n(grid, n, 2)
    assert live_set(after2, n) == horizontal  # period 2


def test_glider_translates_diagonally_every_4_steps():
    n = 20
    glider = {(5, 6), (6, 7), (7, 5), (7, 6), (7, 7)}
    grid = make_grid(glider, n)
    after4 = step_n(grid, n, 4)
    assert live_set(after4, n) == {(r + 1, c + 1) for (r, c) in glider}


def test_glider_wraps_across_edge_intact():
    n = 8
    # placed at the bottom-right so a (1,1) shift wraps both edges
    glider = {(5, 6), (6, 7), (7, 5), (7, 6), (7, 7)}
    grid = make_grid(glider, n)
    after4 = step_n(grid, n, 4)
    expected = {((r + 1) % n, (c + 1) % n) for (r, c) in glider}
    after4_live = live_set(after4, n)
    assert after4_live == expected
    assert len(after4_live) == 5  # still a 5-cell glider


def test_block_is_still_life_with_no_births():
    n = 6
    block = {(2, 2), (2, 3), (3, 2), (3, 3)}
    grid = make_grid(block, n)
    nxt, births, _ = life_core.step(grid, n)
    assert live_set(nxt, n) == block  # survives unchanged
    assert births == {}  # a stable block produces no births
