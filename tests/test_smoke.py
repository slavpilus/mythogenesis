"""Smoke tests: scaffold imports cleanly and config is sane.

These pass today so CI is green on the empty scaffold. Real mechanics live in the
skipped stubs in test_life_core / test_semantics / test_story (handover section 12).
"""

import config


def test_modules_import():
    import life_core  # noqa: F401
    import model_backend  # noqa: F401
    import render  # noqa: F401
    import seed_patterns  # noqa: F401
    import semantics  # noqa: F401


def test_config_thresholds_are_ordered():
    assert config.STORY_THRESH < config.LEGEND_THRESH < config.MYTH_THRESH


def test_config_seed_bounds():
    assert config.SEED_MIN <= config.SEED_MAX
    assert config.SEED_MIN >= 5  # a glider has 5 live cells (handover section 6)


def test_tier_rank_covers_all_tiers():
    assert set(config.TIER_RANK) == {"pantheon", "myth", "legend", "story", "mundane"}
