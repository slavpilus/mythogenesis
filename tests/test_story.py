"""Rolling story window tests (handover section 12). No Gradio or network."""

import config
from semantics import Game


def test_story_trimming_keeps_newest_sentences():
    g = Game()
    for i in range(config.STORY_WINDOW + 12):
        g._push_story(f"line {i}")
    assert len(g.story) == config.STORY_WINDOW
    # the newest line is retained; the oldest are forgotten
    assert g.story[-1] == f"line {config.STORY_WINDOW + 11}"
    assert g.story[0] == f"line {12}"


def test_seed_opens_with_a_story_line():
    g = Game()
    g.seed(config.DEMO_SEED, is_demo=True)
    assert g.story and g.story[0].startswith("In the beginning")


def test_narration_cadence_respects_narrate_every():
    g = Game()
    g.seed(config.DEMO_SEED, is_demo=True)
    start = len(g.story)
    g.step()  # generation 1: odd, NARRATE_EVERY=2 -> only narrates if an ascension occurred
    g.step()  # generation 2: even -> narrates
    assert len(g.story) > start
