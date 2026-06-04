"""Central configuration for Mythogenesis.

Single obvious config block (handover section 6). Import these constants
everywhere rather than hard-coding values, so behaviour is easy to audit and tune.
"""

# --- Board ---
BOARD = 64  # toroidal grid is BOARD x BOARD

# --- Seeding ---
SEED_MIN = 5  # a glider has 5 live cells; fewer is awkward for known patterns
SEED_MAX = 12

# --- Model call budgeting ---
CALL_CAP = 8  # max novel birth signatures sent to the model per generation
REROLL_PROB = 0.0

# --- Story window ---
STORY_WINDOW = 30
WINDOW_UNIT = "sentences"  # simpler and more robust than approximate tokens

# --- Promotion ladder (progeny thresholds) ---
STORY_THRESH = 3
LEGEND_THRESH = 7
MYTH_THRESH = 12

# --- Myth pool ---
MYTH_CAP = 7
MYTH_TTL = 20

# --- Narration ---
SALIENT_BIRTHS = 3
NARRATE_EVERY = 2

# --- Demo ---
DEMO_SEED = "moss lantern ember river bone orchard"

# --- Tier ranking (used to pick the strongest neighbour for inheritance) ---
TIER_RANK = {
    "pantheon": 5,
    "myth": 4,
    "legend": 3,
    "story": 2,
    "mundane": 1,
}
