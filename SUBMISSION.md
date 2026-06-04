# Submission: Mythogenesis

## Track

Adventure in Thousand Token Wood (creative track), Build Small Hackathon.

## Model Compliance

- Model ID: TODO
- Parameter count: TODO
- Total model capacity at or below 32B: yes (to confirm once the model is fixed)

A single named model is used for birth generation, narration, and epitaph
(handover section 4). The exact model id and parameter count are documented here
and in `README.md`.

## How To Run Locally

```bash
uv sync
uv run python app.py
```

Optionally set `HF_TOKEN` to enable the Hugging Face Inference API backend; without
it the app uses a deterministic local fallback.

## Demo Seed

```
moss lantern ember river bone orchard
```

This seed reliably produces visible collisions and at least one myth quickly.

## Claimed Bonus Badges

Claim only when actually true (handover section 11).

- [ ] Off-Brand: custom SVG sky/grid/story UI is strong.
- [ ] Field Notes: `FIELD_NOTES.md` build report is included.
- [ ] Off the Grid: only if no cloud API is used (note: HF Inference API counts as cloud).
- [ ] Llama Champion: only if actually using llama.cpp.
- [ ] Open Trace: only if an agent trace is actually published.

## Known Limitations

- TODO (fill in before submission).

## Final Checklist (handover section 17)

- [ ] App runs as a Hugging Face Gradio Space.
- [ ] Model ID and parameter count documented.
- [ ] Total model capacity at or below 32B.
- [ ] "Plant demo" creates a compelling first 30 seconds.
- [ ] README includes rubric fit.
- [ ] SUBMISSION includes claimed bonus badges only when true.
- [ ] Demo video link included.
- [ ] Social post copy drafted.
- [ ] Core tests pass.
- [ ] No model parse failure can crash the app.
- [ ] No em dashes in generated docs or prose.
