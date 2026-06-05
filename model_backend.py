"""LLM calls and deterministic local fallback (handover section 9).

All provider-specific code (Hugging Face Inference API) stays behind the three
public functions: ``generate_births``, ``narrate_step`` and ``write_epitaph``.

The app MUST run with no working model. The fallback here is a curated word-genetics
lexicon ported from the design handoff: each word belongs to one or two elemental
clusters, a child is grown from the dominant cluster pair of its three parents via a
blend table (deterministic, so it behaves like a cache), and colours are blended from
the parents and nudged toward the child's cluster hue. This is what makes the piece
work offline, in tests, and on Space startup; the optional real model only refines it.

Real model path: set ``MODEL_ID`` (a <=32B model) and ``HF_TOKEN`` to call the Hugging
Face Inference API for births and narration. Any error falls back silently.
"""

from __future__ import annotations

import json
import os

# --------------------------------------------------------------------------------------
# Cluster base colours (dark-canvas friendly, shared chroma band)
# --------------------------------------------------------------------------------------
CLUSTER = {
    "FIRE": "#e8743b",
    "WATER": "#4a86c8",
    "EARTH": "#a07d4c",
    "WOOD": "#6fae5a",
    "STONE": "#8b8f96",
    "BONE": "#d9d2bf",
    "LIGHT": "#e9c46a",
    "DARK": "#6a6280",
    "METAL": "#9aa6b2",
    "FLESH": "#c97f6d",
    "AIR": "#b7c7cf",
    "MIND": "#a98bc2",
    "BEAST": "#b5733f",
    "TIME": "#7d7a86",
    "ASH": "#6b6b6b",
}

# Word -> clusters. Colour is derived from clusters + a stable per-word jitter.
WORDS = {
    "moss": ["WOOD", "EARTH"],
    "lantern": ["LIGHT", "METAL"],
    "ember": ["FIRE"],
    "river": ["WATER"],
    "bone": ["BONE"],
    "orchard": ["WOOD", "LIGHT"],
    "ash": ["ASH"],
    "smoke": ["AIR"],
    "soot": ["ASH"],
    "char": ["ASH"],
    "cinder": ["FIRE"],
    "flame": ["FIRE"],
    "coal": ["STONE", "FIRE"],
    "spark": ["FIRE", "LIGHT"],
    "rain": ["WATER"],
    "mist": ["AIR"],
    "fog": ["AIR"],
    "dew": ["WATER"],
    "brook": ["WATER"],
    "tide": ["WATER"],
    "silt": ["EARTH"],
    "pool": ["WATER"],
    "reed": ["WOOD"],
    "murk": ["DARK"],
    "clay": ["EARTH"],
    "mud": ["EARTH"],
    "loam": ["EARTH"],
    "dust": ["ASH"],
    "sand": ["EARTH"],
    "marsh": ["WATER", "EARTH"],
    "furrow": ["EARTH"],
    "root": ["WOOD"],
    "bark": ["WOOD"],
    "leaf": ["WOOD"],
    "thorn": ["WOOD"],
    "briar": ["WOOD"],
    "vine": ["WOOD"],
    "bloom": ["WOOD", "LIGHT"],
    "husk": ["WOOD", "ASH"],
    "seed": ["WOOD"],
    "bough": ["WOOD"],
    "fern": ["WOOD"],
    "stone": ["STONE"],
    "flint": ["STONE"],
    "slate": ["STONE"],
    "gravel": ["STONE"],
    "cairn": ["STONE"],
    "marrow": ["BONE", "FLESH"],
    "antler": ["BONE"],
    "skull": ["BONE"],
    "tusk": ["BONE"],
    "horn": ["BONE"],
    "glow": ["LIGHT"],
    "dawn": ["LIGHT"],
    "gleam": ["LIGHT"],
    "halo": ["LIGHT"],
    "candle": ["LIGHT", "METAL"],
    "beacon": ["LIGHT"],
    "shadow": ["DARK"],
    "gloam": ["DARK"],
    "dusk": ["DARK", "LIGHT"],
    "night": ["DARK"],
    "hollow": ["DARK"],
    "iron": ["METAL"],
    "rust": ["METAL", "ASH"],
    "nail": ["METAL"],
    "wire": ["METAL"],
    "bell": ["METAL"],
    "sinew": ["FLESH"],
    "pelt": ["FLESH", "BEAST"],
    "vein": ["FLESH"],
    "breath": ["AIR"],
    "cloud": ["AIR"],
    "wind": ["AIR"],
    "steam": ["AIR"],
    "dream": ["MIND"],
    "omen": ["MIND"],
    "name": ["MIND"],
    "song": ["MIND", "LIGHT"],
    "rune": ["MIND"],
    "prayer": ["MIND"],
    "crow": ["BEAST"],
    "wolf": ["BEAST"],
    "moth": ["BEAST"],
    "hare": ["BEAST"],
    "stag": ["BEAST", "BONE"],
    "relic": ["TIME", "STONE"],
    "ruin": ["TIME", "STONE"],
    "echo": ["TIME", "MIND"],
}

# Blend table: sorted "CLUSTER|CLUSTER" -> candidate children.
BLEND = {
    "FIRE|FIRE": ["ember", "ash", "cinder", "flame", "coal"],
    "FIRE|WATER": ["steam", "mist", "smoke", "fog"],
    "FIRE|WOOD": ["ash", "ember", "char", "soot", "smoke"],
    "AIR|FIRE": ["smoke", "spark", "cinder"],
    "BONE|FIRE": ["char", "ash", "ember"],
    "EARTH|FIRE": ["coal", "soot", "cinder", "clay"],
    "FIRE|LIGHT": ["beacon", "flame", "glow", "halo"],
    "FIRE|STONE": ["flint", "spark", "coal"],
    "FIRE|METAL": ["iron", "rust", "coal", "spark"],
    "WATER|WATER": ["river", "tide", "pool", "brook", "rain"],
    "WATER|WOOD": ["reed", "moss", "fern", "marsh", "silt"],
    "EARTH|WATER": ["silt", "mud", "clay", "marsh", "loam"],
    "BONE|WATER": ["marrow", "silt", "dew"],
    "AIR|WATER": ["mist", "fog", "cloud", "dew", "rain"],
    "STONE|WATER": ["pool", "gravel", "slate"],
    "LIGHT|WATER": ["dew", "gleam", "dawn"],
    "DARK|WATER": ["murk", "pool", "gloam"],
    "WOOD|WOOD": ["bloom", "vine", "briar", "bough", "fern", "root"],
    "EARTH|WOOD": ["root", "loam", "moss", "furrow", "seed"],
    "BONE|WOOD": ["marrow", "antler", "husk", "root"],
    "LIGHT|WOOD": ["bloom", "dawn", "orchard", "gleam"],
    "STONE|WOOD": ["cairn", "root", "bark"],
    "AIR|WOOD": ["leaf", "fern", "seed"],
    "DARK|WOOD": ["hollow", "briar", "thorn", "shadow"],
    "BONE|BONE": ["skull", "antler", "tusk", "marrow", "horn"],
    "BONE|EARTH": ["marrow", "dust", "relic", "cairn"],
    "BONE|LIGHT": ["halo", "relic", "gleam"],
    "BONE|STONE": ["cairn", "relic", "skull", "ruin"],
    "BONE|METAL": ["nail", "relic", "bell"],
    "LIGHT|LIGHT": ["dawn", "halo", "beacon", "gleam", "glow"],
    "DARK|LIGHT": ["dusk", "gloam", "ember", "candle"],
    "LIGHT|METAL": ["lantern", "candle", "bell", "beacon"],
    "AIR|LIGHT": ["dawn", "halo", "cloud"],
    "LIGHT|MIND": ["song", "omen", "prayer", "dream"],
    "DARK|DARK": ["night", "hollow", "murk", "gloam", "shadow"],
    "EARTH|EARTH": ["loam", "clay", "mud", "dust", "furrow"],
    "EARTH|STONE": ["gravel", "flint", "cairn", "slate"],
    "EARTH|LIGHT": ["dawn", "loam", "bloom"],
    "METAL|METAL": ["iron", "nail", "bell", "wire", "rust"],
    "METAL|WATER": ["rust", "iron"],
    "AIR|AIR": ["wind", "cloud", "breath", "mist"],
    "MIND|MIND": ["dream", "omen", "rune", "prayer", "name", "song"],
    "DARK|MIND": ["omen", "dream", "shadow", "rune"],
    "BEAST|BEAST": ["crow", "moth", "hare", "wolf", "stag"],
    "FLESH|FLESH": ["sinew", "vein", "marrow", "pelt"],
    "TIME|TIME": ["relic", "ruin", "echo"],
}

# Per-cluster fallback pools (computed from WORDS).
POOL: dict[str, list[str]] = {}
for _w, _cs in WORDS.items():
    for _c in _cs:
        POOL.setdefault(_c, []).append(_w)

# Priority for resolving dominant clusters when tied.
CLUSTER_PRIORITY = [
    "FIRE",
    "WATER",
    "WOOD",
    "BONE",
    "LIGHT",
    "DARK",
    "MIND",
    "METAL",
    "STONE",
    "BEAST",
    "FLESH",
    "AIR",
    "EARTH",
    "TIME",
    "ASH",
]


# --------------------------------------------------------------------------------------
# Hashing (stable, deterministic; FNV-1a, matches the design's JS)
# --------------------------------------------------------------------------------------
def hash_str(s: str) -> int:
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h & 0xFFFFFFFF


# --------------------------------------------------------------------------------------
# Colour helpers
# --------------------------------------------------------------------------------------
def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    m = hex_color.lstrip("#")
    return int(m[0:2], 16), int(m[2:4], 16), int(m[4:6], 16)


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    def c(v: float) -> str:
        return f"{max(0, min(255, round(v))):02x}"

    return "#" + c(r) + c(g) + c(b)


def mix(a: str, b: str, t: float) -> str:
    ra, rb = _hex_to_rgb(a), _hex_to_rgb(b)
    return _rgb_to_hex(
        ra[0] + (rb[0] - ra[0]) * t,
        ra[1] + (rb[1] - ra[1]) * t,
        ra[2] + (rb[2] - ra[2]) * t,
    )


def avg_colors(cols: list[str]) -> str:
    r = g = b = 0
    for col in cols:
        rr, gg, bb = _hex_to_rgb(col)
        r += rr
        g += gg
        b += bb
    n = len(cols) or 1
    return _rgb_to_hex(r / n, g / n, b / n)


def base_color(word: str) -> str:
    """Cluster hue plus a stable per-word jitter so siblings differ slightly."""
    cs = WORDS.get(word, ["STONE"])
    col = CLUSTER[cs[0]]
    if len(cs) > 1:
        col = mix(col, CLUSTER[cs[1]], 0.4)
    h = hash_str(word)
    jr = ((h & 0xFF) - 128) * 0.06
    jg = (((h >> 8) & 0xFF) - 128) * 0.06
    jb = (((h >> 16) & 0xFF) - 128) * 0.06
    r, g, b = _hex_to_rgb(col)
    return _rgb_to_hex(r + jr, g + jg, b + jb)


def clusters_of(word: str) -> list[str]:
    return WORDS.get(word, ["STONE"])


def is_valid_hex(color: str) -> bool:
    if not isinstance(color, str) or not color.startswith("#") or len(color) != 7:
        return False
    try:
        int(color[1:], 16)
    except ValueError:
        return False
    return True


# --------------------------------------------------------------------------------------
# The genetics (deterministic fallback child word + colour)
# --------------------------------------------------------------------------------------
def grow_child(parents: list[str], parent_colors: list[str]) -> dict:
    """Grow one ``{"word", "color"}`` child from exactly 3 parents (dups preserved)."""
    tally: dict[str, int] = {}
    for p in parents:
        for c in clusters_of(p):
            tally[c] = tally.get(c, 0) + 1
    ranked = sorted(tally.keys(), key=lambda c: (-tally[c], CLUSTER_PRIORITY.index(c)))
    c1 = ranked[0]
    c2 = ranked[1] if len(ranked) > 1 else ranked[0]
    key = "|".join(sorted([c1, c2]))

    pool = (
        BLEND.get(key) or BLEND.get(c1 + "|" + c1) or POOL.get(c1) or POOL.get("STONE") or ["dust"]
    )

    sig = "+".join(sorted(parents))
    idx = hash_str(sig) % len(pool)
    child = pool[idx]
    # avoid trivially echoing a parent when alternatives exist
    if child in parents and len(pool) > 1:
        child = pool[(idx + 1) % len(pool)]

    avg = avg_colors(parent_colors) if parent_colors else base_color(child)
    color = mix(avg, base_color(child), 0.45)
    return {"word": child, "color": color}


# --------------------------------------------------------------------------------------
# Narrator templates
# --------------------------------------------------------------------------------------
_T_BIRTH = [
    "Where {a} meets {b}, {child} takes shape and holds.",
    "Out of {a} and {b}, a {child} surfaces and stays a while.",
    "{child} forms in the seam between {a} and {b}.",
    "The board folds {a} into {b} and calls the result {child}.",
    "Quietly, {child} grows where {a} and {b} pressed together.",
    "A {child} answers the meeting of {a} and {b}.",
]
_T_MULTI = [
    "{count} small things are born this turn, and only {child} keeps its colour.",
    "Several shapes flicker up at once; {child} is the one that lasts.",
    "The grid is busy with birth, and {child} stands clearest among them.",
]
_T_ASCEND = [
    "{child} climbs off the board and settles in the sky as a fixed thing.",
    "The board lets {child} go upward, and it becomes a name the night keeps.",
    "{child} rises past the living cells and joins the older lights above.",
    "What began as {child} is now too remembered to stay on the grid.",
]
_T_MYTH_TOUCH = [
    "Under the watch of {myth}, the small lives keep their patient work.",
    "{myth} still leans on the story, and the new words lean back.",
    "The light of {myth} has not gone out; it colours what is said here.",
]
_T_PANTHEON = [
    "The {pantheon} hold their places while everything beneath them turns over.",
    "Nothing the board makes forgets the {pantheon} that started it.",
    "Above the churn, the {pantheon} stay lit and unmoved.",
]
_T_IDLE = [
    "The board breathes once, and little changes.",
    "For a turn the wood is still, holding what it has.",
    "A quiet pass; the living cells keep their ground.",
]
_NUM_WORD = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


def _pick(arr: list[str], salt: str) -> str:
    return arr[hash_str(salt) % len(arr)]


def _join_list(words: list[str]) -> str:
    if not words:
        return "old lights"
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return words[0] + " and " + words[1]
    return ", ".join(words[:-1]) + " and " + words[-1]


def _fill(tmpl: str, variables: dict) -> str:
    out = tmpl
    for k, v in variables.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def _fallback_narrate(payload: dict) -> str:
    new_words = payload.get("new_words") or payload.get("newWords") or []
    ascended = payload.get("ascended") or []
    myths = payload.get("myths") or []
    pantheon = payload.get("pantheon") or []
    gen = payload.get("gen", 0)
    salt = (
        "g"
        + str(gen)
        + (new_words[0]["child"] if new_words else "")
        + (ascended[0] if ascended else "")
    )

    if ascended:
        return _fill(_pick(_T_ASCEND, salt), {"child": ascended[0]})
    if new_words:
        nw = new_words[0]
        if len(new_words) >= 3:
            return _fill(
                _pick(_T_MULTI, salt),
                {
                    "child": nw["child"],
                    "count": _NUM_WORD[len(new_words)]
                    if len(new_words) < len(_NUM_WORD)
                    else len(new_words),
                },
            )
        parents = nw.get("parents", [])
        return _fill(
            _pick(_T_BIRTH, salt),
            {
                "a": parents[0] if parents else "dust",
                "b": parents[1] if len(parents) > 1 else (parents[0] if parents else "dust"),
                "child": nw["child"],
            },
        )
    if myths:
        return _fill(_pick(_T_MYTH_TOUCH, salt), {"myth": myths[0]})
    if pantheon:
        return _fill(_pick(_T_PANTHEON, salt), {"pantheon": _join_list(pantheon[:3])})
    return _pick(_T_IDLE, salt)


def _fallback_epitaph(survivors: list[str]) -> list[str]:
    s = list(survivors[:5])
    while len(s) < 3:
        s.append("dust")
    return [
        "what is left: " + (s[0] or "dust"),
        "beside " + (s[1] or "ash") + ", a little " + (s[2] or "stone"),
        (s[3] + " keeps its name") if len(s) > 3 and s[3] else "the names keep still",
        ("and " + s[4] + " goes quiet") if len(s) > 4 and s[4] else "and the rest goes quiet",
    ]


# --------------------------------------------------------------------------------------
# Optional real model (Hugging Face Inference API). Off unless MODEL_ID is set.
# --------------------------------------------------------------------------------------
def _real_model_id() -> str | None:
    mid = os.environ.get("MODEL_ID")
    return mid if (mid and os.environ.get("HF_TOKEN")) else None


def _client():
    from huggingface_hub import InferenceClient

    return InferenceClient(model=os.environ["MODEL_ID"], token=os.environ["HF_TOKEN"], timeout=20)


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1] if "\n" in t else t
        if t.endswith("```"):
            t = t[:-3]
        t = t.replace("```json", "").replace("```", "")
    return t.strip()


_BIRTH_SYSTEM = (
    "You grow one new word from three parent words, like a child resembling its parents.\n"
    "Return strict JSON only. No prose.\n"
    "Each output word must be a single common, evocative, lowercase English word.\n"
    "Each color must be a valid hex color."
)
_NARRATOR_SYSTEM = (
    "You are a quiet observational narrator of a small living wood.\n"
    "Write exactly one present-tense sentence.\n"
    "Keep the voice steady, spare, and concrete.\n"
    "Weave in gods and myths only when natural.\n"
    "Do not explain the game.\n"
    "Return the sentence only."
)


# --------------------------------------------------------------------------------------
# Public API (handover section 9)
# --------------------------------------------------------------------------------------
def generate_births(batch: list[dict]) -> list[dict]:
    """One child ``{"word", "color"}`` per ``{"parents", "parent_colors"}`` item.

    Never raises. Tries the real model when configured, validates defensively, and
    falls back to the deterministic lexicon per item on any failure.
    """
    fallback = [grow_child(item["parents"], item.get("parent_colors", [])) for item in batch]
    if not batch or _real_model_id() is None:
        return fallback

    try:
        payload = json.dumps([{"parents": item["parents"]} for item in batch])
        resp = _client().chat_completion(
            messages=[
                {"role": "system", "content": _BIRTH_SYSTEM},
                {"role": "user", "content": payload},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        text = _strip_fences(resp.choices[0].message.content or "")
        parsed = json.loads(text)
        if not isinstance(parsed, list) or len(parsed) != len(batch):
            return fallback
        out = []
        for got, fb in zip(parsed, fallback, strict=False):
            word = got.get("word") if isinstance(got, dict) else None
            color = got.get("color") if isinstance(got, dict) else None
            if isinstance(word, str) and word.isalpha() and word.islower() and is_valid_hex(color):
                out.append({"word": word, "color": color})
            else:
                out.append(fb)
        return out
    except Exception:
        return fallback


def narrate_step(payload: dict) -> str:
    """Return exactly one present-tense sentence about the latest births/myths."""
    if _real_model_id() is None:
        return _fallback_narrate(payload)
    try:
        user = json.dumps(
            {
                "new_words": payload.get("new_words") or payload.get("newWords") or [],
                "myths": payload.get("myths", []),
                "pantheon": payload.get("pantheon", []),
                "story_so_far": payload.get("story_so_far", [])[-4:],
            }
        )
        resp = _client().chat_completion(
            messages=[
                {"role": "system", "content": _NARRATOR_SYSTEM},
                {"role": "user", "content": user},
            ],
            max_tokens=60,
            temperature=0.8,
        )
        line = (resp.choices[0].message.content or "").strip().replace("\n", " ")
        return line or _fallback_narrate(payload)
    except Exception:
        return _fallback_narrate(payload)


def write_epitaph(payload: dict) -> str:
    """Return a short found poem (3-5 lines, joined by ' / ') from surviving words."""
    survivors = payload.get("survivors", [])
    return " / ".join(_fallback_epitaph(survivors))
