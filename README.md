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

- Space: TODO (add the Hugging Face Space URL)
- Demo video: TODO (add the demo video link)
- Model: TODO model id, TODO parameter count, at or below 32B total parameters

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

Scaffold in place (project structure, tests, CI/CD, credentials wiring). Game logic
is implemented per the build order in `handover.md`.
