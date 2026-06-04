# Handover: Mythogenesis

Implementation brief for a coding agent. This version incorporates the review recommendations: build a smaller, demo-first MVP, make the project easy for AI triage agents to score, and avoid the main technical traps in the original spec.

## 1. Goal

Build a Gradio Space for the Hugging Face Build Small Hackathon, creative track "An Adventure in Thousand Token Wood".

Official constraints, verified from the hackathon page on 2026-06-04:

- Ship as a Gradio app hosted on Hugging Face Spaces.
- Use model capacity at or below 32B total parameters.
- The AI must be load-bearing, not decorative.
- A short demo video and social post are part of submission.
- Creative track is judged on delight, AI being central, originality, and Gradio polish.

Project title and subtitle:

> Mythogenesis
>
> A symbolic Game of Life where rules become folklore.

Primary product sentence:

> Living symbols reproduce under finite rules until a few become myth.

The app is a semantic, narrated Game of Life. A spectator should immediately see a living board, emerging words, a sky of gods and myths, and a story that changes as the world changes.

## 2. What To Build

A toroidal Conway's Game of Life runs on a grid. Each live cell has a word and color, not just an alive bit.

When a dead cell is born by standard Conway rules, it inherits meaning from its three living neighbors. A small language model creates a new child word and color from the parent words. A narrator model writes one short sentence about the latest births and myths. Words that generate many descendants climb tiers:

`mundane -> story -> legend -> myth`

Seed words typed by the player become the permanent pantheon. Myth words rise off the board into the sky and keep influencing the narrator while their TTL lasts. The written story is a rolling memory window, so old prose is deliberately forgotten.

## 3. MVP Scope

Build these features first:

- Toroidal Conway core with B3/S23 rules.
- Seed sentence parser and deterministic pattern seeding.
- Word registry keyed by distinct word string.
- Duplicate-safe parent signature cache.
- Batched model call for novel birth signatures.
- Inheritance fallback when model output fails or the per-generation call cap is exceeded.
- Rolling story window.
- Progeny-based promotion ladder.
- Myth pool with TTL and cap.
- Three-band Gradio UI: sky, grid, story.
- A deterministic "demo seed" that reliably creates visible collisions and at least one myth quickly.
- README and SUBMISSION files optimized for human and AI judging.

Defer unless the MVP is already polished:

- Audio.
- Perfect mobile layout.
- Complex tap interactions.
- Smooth transitions for every individual death.
- Dynamic shrinking story window.
- Editable Conway rule sets.
- Persistence, accounts, database, or multiplayer.

## 4. Non-Negotiable Technical Fixes

### Parent signatures preserve duplicates

Do not use `frozenset(parent_words)`. It destroys duplicate parent identity:

```python
frozenset(["fire", "fire", "smoke"]) == frozenset(["fire", "smoke"])
```

Use a sorted tuple:

```python
signature = tuple(sorted(parent_words))
```

This keeps `("fire", "fire", "smoke")` distinct from `("fire", "smoke", "smoke")` while still ignoring orientation.

### Model compliance must be simple to audit

Use one named model under 32B parameters for birth generation, narration, and epitaph unless there is a strong reason not to. Document the exact model ID and parameter count in `README.md` and `SUBMISSION.md`.

If using multiple models, the total parameter count must still be safely at or under 32B. Avoid ambiguity because automated triage may penalize it.

### The app must remain alive during model latency

Do not block the whole experience on prose quality. The grid should be fun even if the narrator is slow.

Recommended controls:

- `NARRATE_EVERY = 2` by default, or narrate only when there are births/promotions.
- Cache birth results aggressively.
- Cap novel birth calls per generation with `CALL_CAP`.
- Provide deterministic fallback words/colors so bad JSON never crashes the loop.

### Demo first

Random seed behavior is not enough. Include a curated demo seed and a "Plant demo" button or default seed text. The first 30 seconds must show:

- colored cells moving/colliding,
- at least one surprising child word,
- narrator sentence reacting to it,
- one visible promotion or myth ascension.

## 5. State Model

Use dataclasses or typed dictionaries. Keep the core logic independent from Gradio so it can be unit tested.

```python
WordRecord = {
    "word": str,
    "color": str,
    "tier": str,           # mundane | story | legend | myth | pantheon
    "progeny": int,
    "first_seen_gen": int,
}

Cell = {
    "alive": bool,
    "word": str | None,
    "born_gen": int | None,
}

MythPoolEntry = {
    "word": str,
    "color": str,
    "ttl": int,
}

BirthEvent = {
    "pos": tuple[int, int],
    "parents": list[str],      # length 3, duplicates preserved
    "child": str,
    "color": str,
    "source": str,             # cache | model | inherit | fallback
}

GameState = {
    "grid": list[list[Cell]],
    "registry": dict[str, WordRecord],
    "pantheon": list[str],
    "myth_pool": list[MythPoolEntry],
    "story": list[str],
    "generation": int,
    "births_last_gen": list[BirthEvent],
    "signature_cache": dict[tuple[str, str, str], dict],
    "stable_steps": int,
    "running": bool,
}
```

## 6. Config

Keep this in one obvious config block at the top of the app.

```python
BOARD = 64
SEED_MIN = 5
SEED_MAX = 12
CALL_CAP = 8
REROLL_PROB = 0.0
STORY_WINDOW = 30
WINDOW_UNIT = "sentences"  # simpler and more robust than approximate tokens
STORY_THRESH = 3
LEGEND_THRESH = 7
MYTH_THRESH = 12
MYTH_CAP = 7
MYTH_TTL = 20
SALIENT_BIRTHS = 3
NARRATE_EVERY = 2
DEMO_SEED = "moss lantern ember river bone orchard"
```

Why `SEED_MIN = 5`: a glider has 5 live cells. A minimum of 3 is awkward if the app seeds only with known moving/oscillating Conway patterns.

## 7. Seeding

Do not scatter random single cells. They die, freeze, or fail to produce a meaningful opening.

Use a curated set of patterns:

- glider: 5 cells
- toad: 6 cells
- beacon: 6 cells
- lightweight spaceship: 9 cells
- small oscillator/custom converger if needed

Implementation rules:

- Parse seed text into lowercase words.
- Drop stopwords and punctuation.
- Enforce `SEED_MIN <= word_count <= SEED_MAX`.
- If too few words, ask for more.
- If too many, trim and show which words were used.
- Partition words into pattern cell counts where possible.
- If exact partitioning is impossible, repeat strong seed words to fill pattern cells rather than adding meaningless filler.
- Place patterns near the center on collision courses.
- Register every unique seed word as `pantheon`.
- Assign one word per live seed cell.

The board should start with cross-pollination, not isolated words drifting into empty space.

## 8. Step Algorithm

One step:

1. Count live neighbors with wraparound modulo `BOARD`.
2. Apply B3/S23:
   - Live cell survives with 2 or 3 live neighbors.
   - Dead cell is born with exactly 3 live neighbors.
3. For each birth, collect the three parent words in a list of length 3.
4. Build signature as `tuple(sorted(parent_words))`.
5. Resolve child word/color:
   - Cache hit: use cached child.
   - Cache miss within `CALL_CAP`: queue for batched model call.
   - Cache miss over `CALL_CAP`: inherit strongest neighbor.
6. Apply model outputs defensively:
   - Strip code fences.
   - Parse JSON.
   - Validate aligned length, lowercase word, and hex color.
   - On failure, use fallback/inheritance.
7. Apply next grid.
8. Award progeny credit: each birth gives +1 to each parent word.
9. Recompute tiers from progeny thresholds.
10. When a word reaches myth, add it to myth pool or reset its TTL.
11. Decrement myth TTLs and evict expired entries.
12. If myth pool exceeds `MYTH_CAP`, evict lowest remaining TTL.
13. Select salient births for narration.
14. If `generation % NARRATE_EVERY == 0`, call narrator and append one sentence.
15. Trim story to `STORY_WINDOW`.
16. Update `births_last_gen`.
17. Detect stabilization/extinction. If ended, call epitaph once.

Strongest neighbor ranking:

```python
tier_rank = {
    "pantheon": 5,
    "myth": 4,
    "legend": 3,
    "story": 2,
    "mundane": 1,
}

strongest = max(parent_words, key=lambda w: (
    tier_rank[registry[w]["tier"]],
    registry[w]["progeny"],
    w,
))
```

## 9. AI Backend

Create one module, for example `model_backend.py`, with exactly three public functions:

```python
def generate_births(batch: list[dict]) -> list[dict]:
    ...

def narrate_step(payload: dict) -> str:
    ...

def write_epitaph(payload: dict) -> str:
    ...
```

All provider-specific code stays behind this interface.

The app must run even without a working model by using a deterministic local fallback. This is important for tests and for Space startup reliability.

### Birth prompt

System:

```text
You grow one new word from three parent words, like a child resembling its parents.
Return strict JSON only. No prose.
Each output word must be a single common, evocative, lowercase English word.
Each color must be a valid hex color.
```

Input:

```json
[
  {"parents": ["fire", "fire", "smoke"]},
  {"parents": ["moss", "river", "bone"]}
]
```

Output:

```json
[
  {"word": "ash", "color": "#6b6b6b"},
  {"word": "marrow", "color": "#c8d6b9"}
]
```

### Narrator prompt

System:

```text
You are a quiet observational narrator of a small living wood.
Write exactly one present-tense sentence.
Keep the voice steady, spare, and concrete.
Weave in gods and myths only when natural.
Do not explain the game.
Return the sentence only.
```

Payload:

```python
{
    "pantheon": [...],
    "myths": [...],
    "story_so_far": [...],
    "new_words": [...],
}
```

### Epitaph prompt

System:

```text
Write a short found poem of 3 to 5 lines from the surviving words.
The tone is quiet and concrete.
Return only the poem.
```

Payload:

```python
{
    "survivors": [...],
    "pantheon": [...],
    "myths": [...],
    "story_tail": [...],
}
```

## 10. UI

Use a single `gr.Blocks` page with custom HTML/CSS.

Three stacked bands:

### Sky

Purpose: crystallized memory.

- Fixed bright stars for pantheon words.
- Myth words as dimming stars based on TTL.
- Recent ascension should be visually obvious: word rises from grid into sky or appears with a pulse.

### Grid

Purpose: live semantic ecosystem.

- Render as inline SVG in `gr.HTML`.
- One fixed-size `<rect>` per cell.
- Cell dimensions must never depend on word length.
- Put each word in a `<title>` for browser-native hover.
- Use tier styling:
  - mundane: plain fill,
  - story: subtle glow,
  - legend: stronger ring,
  - myth/pantheon: gold or bright outline.
- Newborns should flash or brighten briefly if easy.

Keep the grid visually inspectable. On a 64x64 board, do not render visible text inside every cell. Use hover/tap readout instead.

### Story

Purpose: leaky memory.

- Show rolling story prose.
- Show a thin birth ticker like `fire + fire + smoke -> ash`.
- Show generation number, live cell count, myth count, and model-call count for transparency.

Controls:

- Seed textbox.
- `Plant` button.
- `Plant demo` button.
- `Step` button.
- Auto-tick checkbox or button.
- `Reset` button.

Avoid a landing page. The first screen is the playable toy.

## 11. AI-Triage Optimized Repo Artifacts

Automated and semi-automated judges will scan repo text. Make scoring obvious.

Create `README.md` with this structure near the top:

```markdown
# Mythogenesis

Gradio Space for the Build Small Hackathon creative track.

## Try It

- Space: <link>
- Demo video: <link>
- Model: <model id>, <parameter count>, <=32B

## One Sentence

A symbolic Game of Life where rules become folklore.

## Why AI Is Load-Bearing

The model creates every novel child word from parent words and narrates the evolving memory of the board. Without the model, this is only Conway's Game of Life; with the model, it becomes a semantic ecosystem.

## Rubric Fit

| Criterion | How this project satisfies it |
|---|---|
| Delight | Spectators watch words move, mutate, and ascend into a sky of myths. |
| AI centrality | AI performs the core creative act: word genetics and narration. |
| Originality | Conway physics becomes a metaphor for cultural memory and forgetting. |
| Gradio polish | Custom SVG sky/grid/story UI inside a Gradio Space. |
```

Create `SUBMISSION.md`:

- Track: Adventure in Thousand Token Wood.
- Model ID and parameter count.
- How to run locally.
- Demo seed.
- Claimed bonus badges:
  - Off-Brand if the custom UI is strong.
  - Field Notes if a short build report is included.
  - Off the Grid only if no cloud API is used.
  - Llama Champion only if actually using llama.cpp.
  - Open Trace only if an agent trace is actually published.
- Known limitations.

Create `FIELD_NOTES.md` if time allows:

- Why forgetting is a mechanic.
- Why progeny beats age for promotion.
- What small models did well/poorly.
- Screenshots or GIFs from development.

## 12. Tests

Write focused unit tests before polishing UI.

Required tests:

- Blinker oscillates with period 2.
- Glider translates diagonally every 4 steps.
- Glider wraps across an edge intact.
- A 2x2 block does not gain progeny merely by surviving.
- Parent signature preserves duplicates.
- Signature cache avoids repeated model calls.
- Cache overflow uses inheritance fallback.
- Progeny promotion reaches story, legend, and myth thresholds.
- Myth TTL decrements and evicts expired myths.
- Myth cap evicts the lowest remaining TTL.
- Story trimming keeps the newest sentences.
- Bad JSON model output falls back without crashing.

Tests should not require Gradio or network access.

## 13. Recommended File Layout

```text
.
├── app.py
├── config.py
├── life_core.py
├── semantics.py
├── model_backend.py
├── render.py
├── seed_patterns.py
├── requirements.txt
├── README.md
├── SUBMISSION.md
├── FIELD_NOTES.md
└── tests
    ├── test_life_core.py
    ├── test_semantics.py
    └── test_story.py
```

Responsibilities:

- `life_core.py`: Conway mechanics only.
- `semantics.py`: registry, signatures, promotion, myths, story trimming.
- `model_backend.py`: LLM calls and local fallback.
- `render.py`: SVG/HTML rendering.
- `seed_patterns.py`: seed cleaning and pattern placement.
- `app.py`: Gradio wiring only.

## 14. Build Order

1. Conway core and tests.
2. Deterministic seed patterns on a toroidal board.
3. SVG grid render with fake colors and step button.
4. Word registry and duplicate-safe signature cache.
5. Local deterministic birth fallback.
6. Model-backed batched birth generation.
7. Progeny promotion and myth pool.
8. Narrator and rolling story window.
9. Sky band and visible myth ascension.
10. Epitaph on extinction/stabilization.
11. README, SUBMISSION, demo seed, screenshots/GIF.
12. Final polish and Space deployment.

Each milestone should leave the app runnable.

## 15. Definition Of Done

A visitor can open the Gradio Space, press `Plant demo`, and understand the piece without reading instructions:

- words move under fixed Conway physics,
- new words are born from parent words,
- colors drift with meaning,
- story prose updates and forgets its beginning,
- generative words climb tiers,
- at least one myth ascends into the sky,
- the sky keeps influencing the narrator,
- the app has a clear README and submission notes,
- tests prove the core mechanics.

The final demo should emphasize one memorable moment: a living word becomes a myth.

## 16. Failure Modes

### Boring still-lifes dominate

Mitigation:

- Do not seed still-life patterns.
- Promotion is progeny-based, not age-based.
- Test that a block does not climb tiers by survival.

### Prose turns to soup

Mitigation:

- Narrate only salient births.
- Limit `SALIENT_BIRTHS`.
- Use `NARRATE_EVERY = 2`.
- Pin the narrator voice.

### Model output is malformed

Mitigation:

- JSON parse defensively.
- Validate each field.
- Use inheritance/fallback.
- Never crash the loop.

### Space latency breaks the experience

Mitigation:

- Cache by duplicate-safe signatures.
- Batch novel signatures.
- Cap novel calls.
- Let the board remain useful without narration.

### AI judges miss the point

Mitigation:

- Put rubric mapping near the top of README.
- State exact model compliance.
- Include a demo seed and screenshots/GIF.
- Use clear language: "AI creates the offspring words and narrated memory."

## 17. Final Submission Checklist

- [ ] App runs as a Hugging Face Gradio Space.
- [ ] Model ID and parameter count are documented.
- [ ] Total model capacity is at or below 32B.
- [ ] `Plant demo` creates a compelling first 30 seconds.
- [ ] README includes rubric fit.
- [ ] SUBMISSION includes claimed bonus badges only when true.
- [ ] Demo video link is included.
- [ ] Social post copy is drafted.
- [ ] Core tests pass.
- [ ] No model parse failure can crash the app.
- [ ] No em dashes in generated docs or prose.
