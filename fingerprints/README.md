# Route fingerprints

The benchmark calls Jev through a third party, OpenCode Zen's free `jev-1.13-free`, not
TypeSafe's own API. `typesafe_reference.v2.json` holds six **published** request/response
pairs that TypeSafe-served Jev 1.13 produced. v1 is the same six cases without the `strict_tokens`
flag, and is kept as released. `python -m app.main verify-route` replays them
through the configured route and compares:

- **input tokens, exactly**, for the two *dated live recordings* (`strict_tokens: true`): the same
  prompt template and tokenizer give the same count;
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

## First live check (2026-09-25)

`results/route_verification/20260925T044523Z.json`:

| Case | Tokens, reference / ours | Decisions | Max probability gap |
|---|---|---|---|
| OpenCode recording (strict) | **422 / 422** | same | 0.01 |
| OpenRouter tutorial (strict) | **476 / 476** | same | 0.01 |
| TypeSafe quickstart | 392 / 425 | same | 0.02 |
| TypeSafe docs: Choice | 328 / 357 | same | 0.00 |
| TypeSafe docs: Noul | 360 / 344 | same | 0.01 |
| TypeSafe docs: Score | 332 / 341 | same | 0.00 |

Both dated live recordings match token for token. All six agree on every decision, with
probabilities within 0.02. The four undated docs examples differ **only** in token count, in
both directions. That fits examples generated under an earlier prompt template (TypeSafe's
cookbooks are known to have run on jev-1.12), but it could not be checked against TypeSafe's
own API without a key. So v2 requires exact tokens only for the dated recordings, and
decisions and probabilities for all six. Under v2 this run passes 6 of 6. The run's file still
records `matches: false` for the four docs cases under the v1 rule, unchanged.

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
