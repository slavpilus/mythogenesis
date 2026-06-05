---
title: Mythogenesis
emoji: 🌲
colorFrom: green
colorTo: indigo
sdk: gradio
sdk_version: 6.16.0
app_file: app.py
python_version: "3.11"
pinned: false
license: mit
short_description: A symbolic Game of Life where rules become folklore.
tags:
  - game-of-life
  - generative
  - creative
  - build-small-hackathon
---

# Mythogenesis

Gradio Space for the Build Small Hackathon creative track, "An Adventure in Thousand Token Wood".

## Try It

- Space: https://huggingface.co/spaces/SlavPilus/mythogenesis
- Demo video: TODO (add the demo video link)
- Model: pluggable <=32B model via the Hugging Face Inference API (set `MODEL_ID` + `HF_TOKEN`);
  a deterministic word-genetics engine drives births and narration when no model is configured,
  so the Space stays alive offline and in tests. TODO: pin the exact model id + parameter count.

## One Sentence

A symbolic Game of Life where rules become folklore.

## Why AI Is Load-Bearing

The model creates every novel child word from its parent words and narrates the
evolving memory of the board. Without the model this is only Conway's Game of Life;
with the model it becomes a semantic ecosystem where living symbols reproduce under
finite rules until a few become myth.

## Rubric Fit

| Criterion | How this project satisfies it |
|---|---|
| Delight | Spectators watch words move, mutate, and ascend into a sky of myths. |
| AI centrality | The model performs the core creative act: word genetics and narration. |
| Originality | Conway physics becomes a metaphor for cultural memory and forgetting. |
| Gradio polish | Custom SVG sky, grid, and story bands inside a single Gradio Space. |

## Run Locally

This project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync                 # create the environment and install dependencies
uv run python app.py    # launch the Gradio app locally
uv run pytest           # run the core unit tests
uv run ruff check .     # lint
```

Optional: set `HF_TOKEN` (a Hugging Face token) to enable the Inference API backend.
The app runs without it using a deterministic local fallback.

```bash
cp .env.example .env     # then add your token
```

## Demo Seed

Press "Plant demo" in the app, or use the seed:

```
moss lantern ember river bone orchard
```

## Status

Playable. The front-end design (ported from a Claude Design handoff) is implemented:
a living toroidal board, an emerging sky of pantheon and myth words, a rolling story
with a birth ticker and transparency chips, three moods, and the full control strip.
The demo seed is planted and running on load. Core mechanics are covered by unit tests
(`uv run pytest`), and CI/CD mirrors `main` to the Space.

Remaining before submission: pin a concrete `<=32B` model id, record the demo video,
and draft the social post.
