"""Registry / signature / promotion / myth tests (handover section 12).

No Gradio or network: the model backend defaults to its deterministic local fallback.
"""

import config
import model_backend
import semantics
from semantics import Game, parent_signature, tier_for_progeny


def test_parent_signature_preserves_duplicates():
    a = parent_signature(["fire", "fire", "smoke"])
    b = parent_signature(["fire", "smoke", "smoke"])
    assert a != b  # duplicates are not collapsed (unlike a frozenset)
    assert a == ("fire", "fire", "smoke")
    # orientation independent
    assert parent_signature(["smoke", "fire", "fire"]) == a


def test_signature_cache_avoids_repeated_model_calls(monkeypatch):
    sent_sigs = []

    real = model_backend.generate_births

    def spy(batch):
        for item in batch:
            sent_sigs.append("+".join(sorted(item["parents"])))
        return real(batch)

    monkeypatch.setattr(model_backend, "generate_births", spy)

    g = Game()
    g.seed(config.DEMO_SEED, is_demo=True)
    for _ in range(15):
        g.step()

    # no signature is ever sent to the model twice; the cache absorbs repeats
    assert len(sent_sigs) == len(set(sent_sigs))
    assert g.model_calls == len(sent_sigs)


def test_cache_overflow_uses_inheritance_fallback(monkeypatch):
    monkeypatch.setattr(config, "CALL_CAP", 0)  # no novel model calls allowed
    g = Game()
    g.seed(config.DEMO_SEED, is_demo=True)
    snap = g.step()
    # with the cache empty and a cap of 0, every fresh birth must inherit
    assert g.model_calls == 0
    sources = {b["source"] for b in snap["new_births"]}
    assert sources and sources <= {"inherit", "cache"}
    assert "inherit" in sources


def test_progeny_promotion_story_legend_myth_thresholds():
    assert tier_for_progeny(0) == "mundane"
    assert tier_for_progeny(config.STORY_THRESH) == "story"
    assert tier_for_progeny(config.LEGEND_THRESH) == "legend"
    assert tier_for_progeny(config.MYTH_THRESH) == "myth"


def test_reaching_myth_threshold_ascends_into_pool():
    g = Game()
    g.generation = 1
    rec = g._ensure_record("relic", "#888888", "mundane")
    rec["progeny"] = config.MYTH_THRESH
    ascensions = g._recompute_tiers()
    assert rec["tier"] == "myth"
    assert any(m["word"] == "relic" for m in g.myth_pool)
    assert any(a["word"] == "relic" for a in ascensions)


def test_myth_ttl_decrements_and_evicts_expired():
    g = Game()
    # a pool entry whose registry word is NOT a myth, so it is never refreshed
    g._ensure_record("x", "#888888", "mundane")["progeny"] = 0
    g.myth_pool = [{"word": "x", "color": "#888888", "ttl": 2}]
    g._recompute_tiers()
    assert g.myth_pool[0]["ttl"] == 1  # decremented
    g._recompute_tiers()
    assert g.myth_pool == []  # evicted once expired


def test_myth_cap_evicts_lowest_remaining_ttl():
    g = Game()
    pool = []
    for i in range(config.MYTH_CAP + 2):
        w = f"w{i}"
        g._ensure_record(w, "#888888", "mundane")["progeny"] = 0  # stays mundane, no refresh
        pool.append({"word": w, "color": "#888888", "ttl": i + 5})
    g.myth_pool = pool
    g._recompute_tiers()
    assert len(g.myth_pool) == config.MYTH_CAP
    survivors = {m["word"] for m in g.myth_pool}
    assert "w0" not in survivors  # lowest ttl evicted
    assert "w1" not in survivors


def test_bad_json_model_output_falls_back_without_crashing(monkeypatch):
    monkeypatch.setattr(model_backend, "_real_model_id", lambda: "fake/model")

    class _Msg:
        content = "not json at all {oops"

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]

    class _Client:
        def chat_completion(self, **kwargs):
            return _Resp()

    monkeypatch.setattr(model_backend, "_client", lambda: _Client())

    batch = [
        {"parents": ["fire", "fire", "smoke"], "parent_colors": ["#e8743b", "#e8743b", "#b7c7cf"]}
    ]
    out = model_backend.generate_births(batch)
    assert len(out) == 1
    assert isinstance(out[0]["word"], str) and out[0]["word"].isalpha()
    assert model_backend.is_valid_hex(out[0]["color"])


def test_strongest_parent_prefers_higher_tier():
    g = Game()
    g._ensure_record("a", "#111111", "mundane")["progeny"] = 1
    g._ensure_record("b", "#222222", "legend")["progeny"] = 8
    g._ensure_record("c", "#333333", "mundane")["progeny"] = 2
    assert g._strongest_parent(["a", "b", "c"]) == "b"


def test_module_aliases_present():
    assert hasattr(semantics, "Game")
