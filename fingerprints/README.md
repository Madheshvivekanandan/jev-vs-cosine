# Route fingerprints

The benchmark calls Jev through a third party, OpenCode Zen's free `jev-1.13-free`, not
TypeSafe's own API. `typesafe_reference.v1.json` holds six **published** request/response
pairs that TypeSafe-served Jev 1.13 produced. `python -m app.main verify-route` replays them
through the configured route and compares:

- **input tokens, exactly:** the same prompt template and tokenizer give the same count;
- **every decision:** the chosen option, the rounded score, the yes/no side;
- **every probability, within 0.05:** Jev is consistent but not deterministic, with a
  run-to-run spread of about 0.01.

Each run saves the raw responses to `results/route_verification/<UTC time>.json`.
`scripts/run_jev_daily.sh` runs the full check once, then 1 case per day as a drift canary
before spending that day's quota.

| Case | Source | Reference tokens |
|---|---|---|
| `opencode_recording_bridge` | OpenCode's own live recording of TypeSafe direct (`jev-1.13.0`), 2026-09-22 | 422 |
| `typesafe_quickstart` | docs.typesafe.ai quickstart | 392 |
| `openrouter_tutorial` | OpenRouter's Jev tutorial (TypeSafe as provider) | 476 |
| `typesafe_docs_choice` / `_noul` / `_score` | docs.typesafe.ai primitive pages | 328 / 360 / 332 |

## What a match does and does not prove

A match is strong evidence that the route serves the same model with the same prompt
template. It cannot rule out an exact copy of the weights served by someone else. What we
know as of 2026-09-24:

- OpenCode's docs call `jev-1.13-free` a limited-time free version of TypeSafe's Jev 1.13.
- OpenCode's repository records the same request sent to TypeSafe (`jev-1.13.0`) and to Zen
  29 seconds apart, with identical token counts (422/69), the same decisions, and
  probabilities within 0.01. That recording used a keyed route, not the anonymous one this
  benchmark uses.
- TypeSafe's own docs list only OpenRouter and Vercel as gateways and do not mention Zen.
- Zen likely maps to TypeSafe's `jev-latest` alias, which moves when TypeSafe ships a new
  version. The daily canary is there to catch that.
