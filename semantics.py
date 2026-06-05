"""Registry, signatures, promotion, myths, story, and the Game orchestrator.

Keeps the meaning layer independent of Conway mechanics (``life_core``) and of Gradio.
``Game`` owns the full state (handover section 5), advances it one generation at a
time, and emits a plain-dict snapshot the renderer consumes.

Duplicate-safe signatures (handover section 4) use ``tuple(sorted(parents))`` so
``("fire","fire","smoke")`` stays distinct from ``("fire","smoke","smoke")``.
"""

from __future__ import annotations

import config
import life_core
import model_backend as mb

TIER_RANK = config.TIER_RANK


def parent_signature(parent_words: list[str]) -> tuple[str, ...]:
    """Duplicate-preserving, orientation-independent signature for a birth."""
    return tuple(sorted(parent_words))


def _sig_key(parent_words: list[str]) -> str:
    return "+".join(sorted(parent_words))


def tier_for_progeny(progeny: int) -> str:
    if progeny >= config.MYTH_THRESH:
        return "myth"
    if progeny >= config.LEGEND_THRESH:
        return "legend"
    if progeny >= config.STORY_THRESH:
        return "story"
    return "mundane"


class Game:
    """Toroidal Conway core + semantic layer. Framework-agnostic and unit-testable."""

    def __init__(self, board: int = config.BOARD):
        self.N = board
        self.reset()

    # -- lifecycle ---------------------------------------------------------------------
    def reset(self) -> None:
        n2 = self.N * self.N
        self.grid = [0] * n2
        self.words: list[str | None] = [None] * n2
        self.born = [-1] * n2
        self.registry: dict[str, dict] = {}
        self.pantheon: list[str] = []
        self.myth_pool: list[dict] = []
        self.story: list[str] = []
        self.generation = 0
        self.births: list[dict] = []
        self.sig_cache: dict[str, dict] = {}
        self.model_calls = 0
        self.stable_steps = 0
        self.prev_pop_hash = ""
        self.ended = False

    def _ensure_record(self, word: str, color: str | None = None, tier: str = "mundane") -> dict:
        rec = self.registry.get(word)
        if rec is None:
            rec = {
                "word": word,
                "color": color or mb.base_color(word),
                "tier": tier,
                "progeny": 0,
                "first_seen_gen": self.generation,
            }
            self.registry[word] = rec
        return rec

    def _push_story(self, line: str) -> None:
        self.story.append(line)
        if len(self.story) > config.STORY_WINDOW:
            del self.story[: len(self.story) - config.STORY_WINDOW]

    # -- seeding -----------------------------------------------------------------------
    def seed(self, text: str, is_demo: bool = False) -> dict:
        from seed_patterns import demo_layout, parse_seed

        self.reset()
        wlist = parse_seed(text) or parse_seed(config.DEMO_SEED)

        uniq: list[str] = []
        seen: set[str] = set()
        for w in wlist:
            if w not in seen:
                seen.add(w)
                uniq.append(w)
        self.pantheon = uniq[: config.SEED_MAX]
        for w in self.pantheon:
            self._ensure_record(w, mb.base_color(w), "pantheon")["tier"] = "pantheon"

        cells = demo_layout(self.grid, self.born, self.N, is_demo)
        for i, idx in enumerate(cells):
            self.words[idx] = self.pantheon[i % len(self.pantheon)]

        self.generation = 0
        self.births = []
        self._push_story(
            "In the beginning there are "
            + _list_words(self.pantheon)
            + ", and the rules that move them."
        )
        return self.snapshot()

    # -- one generation ----------------------------------------------------------------
    def step(self) -> dict:
        if self.ended:
            return self.snapshot()
        n = self.N
        nxt, births_map, deaths = life_core.step(self.grid, n)
        next_words: list[str | None] = [None] * (n * n)
        next_born = [-1] * (n * n)

        # survivors keep their word/born; collect birth resolution plans
        plans = []  # (idx, parents)
        queue: dict[str, list[str]] = {}  # sig_key -> parents (novel, within cap)
        calls_this_gen = 0
        for idx in range(n * n):
            if not nxt[idx]:
                continue
            if self.grid[idx]:  # survivor
                next_words[idx] = self.words[idx]
                next_born[idx] = self.born[idx]
                continue
            # birth: exactly 3 live parents (B3); preserve duplicates
            parents = [self.words[j] for j in births_map[idx] if self.words[j]]
            while len(parents) < 3:
                parents.append(parents[-1] if parents else "dust")
            parents = parents[:3]
            key = _sig_key(parents)
            plans.append((idx, parents, key))
            if key not in self.sig_cache and key not in queue and calls_this_gen < config.CALL_CAP:
                queue[key] = parents
                calls_this_gen += 1

        # one batched model call for the novel signatures (handover step 5/6)
        if queue:
            batch_keys = list(queue.keys())
            batch = [
                {"parents": queue[k], "parent_colors": [self._color_of(p) for p in queue[k]]}
                for k in batch_keys
            ]
            results = mb.generate_births(batch)
            for k, res in zip(batch_keys, results, strict=False):
                self.sig_cache[k] = res
                self.model_calls += 1

        # apply resolutions
        new_births: list[dict] = []
        for idx, parents, key in plans:
            if key in self.sig_cache:
                res = self.sig_cache[key]
                source = "cache" if key not in queue else "model"
            else:
                sp = self._strongest_parent(parents)
                res = {"word": sp, "color": self._color_of(sp)}
                source = "inherit"
            child, color = res["word"], res["color"]
            next_words[idx] = child
            next_born[idx] = self.generation + 1
            self._ensure_record(child, color, "mundane")
            for p in parents:
                if p in self.registry:
                    self.registry[p]["progeny"] += 1
            new_births.append(
                {
                    "pos": [idx // n, idx % n],
                    "parents": parents,
                    "child": child,
                    "color": color,
                    "source": source,
                }
            )

        self.grid, self.words, self.born = nxt, next_words, next_born
        self.generation += 1
        self.births = new_births

        ascensions = self._recompute_tiers()
        line = self._narrate(new_births, ascensions)
        self._detect_end()
        return self.snapshot(new_births, ascensions, deaths, line)

    # -- helpers -----------------------------------------------------------------------
    def _color_of(self, word: str) -> str:
        rec = self.registry.get(word)
        return rec["color"] if rec else mb.base_color(word)

    def _strongest_parent(self, parents: list[str]) -> str:
        def key(w: str):
            rec = self.registry.get(w, {"tier": "mundane", "progeny": 0})
            return (TIER_RANK.get(rec["tier"], 1), rec["progeny"], w)

        return max(parents, key=key)

    def _recompute_tiers(self) -> list[dict]:
        ascensions = []
        for w, rec in self.registry.items():
            if rec["tier"] == "pantheon":
                continue
            rec["tier"] = tier_for_progeny(rec["progeny"])
            if rec["tier"] == "myth":
                existing = next((m for m in self.myth_pool if m["word"] == w), None)
                if existing:
                    existing["ttl"] = config.MYTH_TTL
                else:
                    self.myth_pool.append(
                        {"word": w, "color": rec["color"], "ttl": config.MYTH_TTL}
                    )
                    ascensions.append({"word": w, "color": rec["color"], "pos": self._find_cell(w)})
        for m in self.myth_pool:
            m["ttl"] -= 1
        self.myth_pool = [m for m in self.myth_pool if m["ttl"] > 0]
        if len(self.myth_pool) > config.MYTH_CAP:
            self.myth_pool.sort(key=lambda m: m["ttl"], reverse=True)
            self.myth_pool = self.myth_pool[: config.MYTH_CAP]
        return ascensions

    def _narrate(self, new_births: list[dict], ascensions: list[dict]) -> str | None:
        if not (self.generation % config.NARRATE_EVERY == 0 or ascensions):
            return None
        salient = sorted(new_births, key=self._rank_source, reverse=True)[: config.SALIENT_BIRTHS]
        line = mb.narrate_step(
            {
                "gen": self.generation,
                "new_words": [{"child": b["child"], "parents": b["parents"]} for b in salient],
                "myths": [m["word"] for m in self.myth_pool],
                "pantheon": self.pantheon,
                "ascended": [a["word"] for a in ascensions],
                "story_so_far": self.story,
            }
        )
        self._push_story(line)
        return line

    def _rank_source(self, b: dict) -> int:
        rec = self.registry.get(b["child"])
        return (TIER_RANK.get(rec["tier"], 1) * 100 + rec["progeny"]) if rec else 0

    def _find_cell(self, word: str) -> list[int]:
        n = self.N
        for idx in range(n * n):
            if self.grid[idx] and self.words[idx] == word:
                return [idx // n, idx % n]
        return [n // 2, n // 2]

    def _count_live(self) -> int:
        return sum(self.grid)

    def _pop_hash(self) -> str:
        h = 0
        for i, v in enumerate(self.grid):
            if v:
                h = (h * 31 + i) & 0xFFFFFFFF
        return str(h)

    def _survivor_words(self) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for i, v in enumerate(self.grid):
            if v and self.words[i] and self.words[i] not in seen:
                seen.add(self.words[i])
                out.append(self.words[i])
        return out

    def _detect_end(self) -> None:
        pop = self._count_live()
        ph = self._pop_hash()
        self.stable_steps = self.stable_steps + 1 if ph == self.prev_pop_hash else 0
        self.prev_pop_hash = ph
        if pop == 0 or self.stable_steps >= 6:
            self.ended = True
            epi = mb.write_epitaph(
                {
                    "survivors": self._survivor_words(),
                    "pantheon": self.pantheon,
                    "myths": [m["word"] for m in self.myth_pool],
                    "story_tail": self.story[-4:],
                }
            )
            self._push_story(epi)

    # -- snapshot ----------------------------------------------------------------------
    def snapshot(self, new_births=None, ascensions=None, deaths=None, line=None) -> dict:
        return {
            "N": self.N,
            "grid": self.grid,
            "words": self.words,
            "born": self.born,
            "generation": self.generation,
            "live": self._count_live(),
            "registry": self.registry,
            "pantheon": self.pantheon,
            "myth_pool": [dict(m) for m in self.myth_pool],
            "story": list(self.story),
            "births": list(self.births),
            "new_births": new_births or [],
            "ascensions": ascensions or [],
            "deaths": deaths or [],
            "line": line,
            "model_calls": self.model_calls,
            "ended": self.ended,
        }


def _list_words(ws: list[str]) -> str:
    if len(ws) <= 1:
        return ws[0] if ws else "nothing"
    return ", ".join(ws[:-1]) + " and " + ws[-1]
