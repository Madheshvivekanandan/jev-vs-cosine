# jev-vs-cosine

**Do you need Jev, or is cosine similarity enough?** A small, reproducible benchmark
comparing [TypeSafe AI's Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
(a "System One" model that returns a typed choice with probabilities instead of text)
against plain embedding cosine similarity, on the
[Banking77](https://github.com/PolyAI-LDN/task-specific-datasets) intent-routing dataset.

It runs at **$0**: cosine similarity and a cross-encoder run locally, and Jev is called
through a free route.

## Results so far

Jev has answered **249 of the 1,001** test messages. OpenCode's free route allows about 250
requests per IP per day, so the run resumes each day. Scored on those same 249 messages
([`results/first_249/REPORT.md`](results/first_249/REPORT.md)):

![Accuracy vs past examples per category, first 249 messages](results/first_249/accuracy_vs_examples.png)

- **With no examples, Jev (83.1%) beats cosine-vs-descriptions (72.3%) by about 11 points.**
- **With just 5 labelled examples per category, a free logistic-regression classifier matches
  Jev** (method E, about 84%). Plain cosine voting (method C) needs about 10 (86.6%). Both reach
  92-93% with 35.
- **One example per category (64%) does worse than a one-line description (72%).**
- **A cross-encoder reranker doesn't close the gap.** `bge-reranker-v2-m3` reads each message
  together with each description, much as Jev reads a message with its options, yet it scores
  70.7% (71.1% on all 1,001 messages, against 73.2% for cosine). That is no better than plain
  cosine and 12 points below Jev, at the same ~0.8 s per message (on a laptop CPU).

The cosine and cross-encoder methods on all 1,001 messages are in [`results/REPORT.md`](results/REPORT.md).
These numbers are preliminary until Jev finishes the full sample.

## The question, in plain English

A bank's support inbox gets a message like *"I paid at the supermarket and it said
transaction refused."* Which of 77 categories is it (`declined_card_payment`,
`card_arrival`, ...)? Five ways to answer:

| Method | What it compares the message against | Past examples used |
|---|---|---|
| **A: cosine vs descriptions** | A one-line description of each category, e.g. *"A card payment at a shop or online was declined"*. The closest one by meaning wins. | 0 |
| **B: Jev** | The same 77 descriptions, sent to Jev as one `Choice` question. Jev reads the message and picks one. | 0 |
| **C: cosine vs past examples** | Real past customer messages whose category is known. The 5 most similar ones vote. | 1, 5, 10, 20, 35 per category |
| **E: classifier on past examples** | The same past examples as C, used to train a logistic-regression classifier on their embeddings. | 1, 5, 10, 20, 35 per category |
| **D: cross-encoder vs descriptions** | The same 77 descriptions, but a reranker model ([`bge-reranker-v2-m3`](https://huggingface.co/BAAI/bge-reranker-v2-m3)) reads the message and each description *together* and scores the pair. | 0 |

A, B and D get the same category names and descriptions (Jev also receives a one-sentence
instruction), so the difference comes from the method. A encodes the message and each
description *separately*, while D and Jev read them *together*. C shows how many labelled
examples a free, local approach needs before it matches Jev.

## Quickstart

Needs Python 3.12+.

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env               # the default block is the free Jev route

.venv/bin/python -m app.main download       # Banking77, pinned commit + SHA-256 checked
.venv/bin/python -m app.main run-cosine     # methods A and C, local and free (~1 min)
.venv/bin/python -m app.main run-cross-encoder   # method D, local and free (~15 min, 2.3 GB model)
.venv/bin/python -m app.main run-trained    # method E, local and free (~30 s)
.venv/bin/python -m app.main run-jev --limit 20 --dry-run   # estimate, calls nothing
.venv/bin/python -m app.main run-jev --limit 20             # pilot
.venv/bin/python -m app.main run-jev                        # all 1,001 test messages
.venv/bin/python -m app.main report         # results/REPORT.md + the chart
```

`run-jev` caches every answer as it goes. If a run stops (rate limit, daily cap, budget),
run it again and it resumes without paying twice for any message.

## Free ways to call Jev (checked 2026-09-24)

| Route | Cost | Needs | Notes |
|---|---|---|---|
| **OpenCode Zen** `jev-1.13-free` (default) | $0 | nothing (anonymous) | Per-IP daily request cap, value unpublished, resets 00:00 UTC; "limited time" |
| Vercel AI Gateway `typesafe-ai/jev` | $0 from the $5/month free credit | a credit card on file | Heavily throttled on the free tier; model id is unversioned |
| TypeSafe direct `jev-1.13.0` | $5 signup credit | an existing console account | New signups paused since 2026-09-22 |
| OpenRouter, Cloudflare | paid | credits | Not free for Jev |

Beware of lookalike "Jev API" sites and packages. The only official packages are PyPI
`typesafe-sdk` / `system-one-adapter` and npm `@typesafe-ai/sdk`. `JEV_BASE_URL` is checked
against an allow-list so a key can't be sent to a typo or a reseller.

## How the experiment stays fair and reproducible

- **Same test set for every method:** 13 messages from each of the 77 categories
  (1,001 total) from the Banking77 *test* split, fixed seed.
- **Same category text for A and B:** names and one-line descriptions live in one
  versioned file, [`prompts/banking77_intents.v1.json`](prompts/banking77_intents.v1.json).
  A embeds "name: description". Jev gets the same names and descriptions as `Choice` options,
  plus the file's one-sentence instruction. The descriptions were written from the category
  names only, without looking at any test message.
- **Tuned only on training data:** method E's regularisation (`C=100`) was chosen on 1,500
  held-out *training* messages, never on the test set. The scikit-learn default `C=1` underfit
  by 2-4 points there.
- **No train/test leaks:** 7 training rows that duplicate a test message (ignoring case and
  whitespace, an upstream Banking77 quirk) are removed before any past examples are drawn.
- **Nested, repeated examples for C:** the 5 examples used at 5-per-category are also among
  the 10 used at 10-per-category, so the curve measures *more* examples, not *different*
  ones. Every size is drawn with 3 random seeds, and the chart shows the range. The grid
  stops at 35 because the smallest Banking77 training category has 35 messages.
- **Everything pinned:** the dataset commit plus file checksums, the embedding and reranker
  model revisions (`BAAI/bge-small-en-v1.5@5c38ec7`, `BAAI/bge-reranker-v2-m3@953dc6f`), the
  prompt version, and the Jev route. Each run saves
  its route, the model the route reported, the prompt version and the price next to its
  results (`*.meta.json`), and the report reads them from there, not from your current `.env`.
- **Latency:** A and C time local CPU embedding plus scoring per message. Reference texts are
  pre-embedded, as a live system would do. D times all 77 (message, description) pairs for
  one message on CPU; nothing can be precomputed, because each pair includes the message. Jev time is the full network round trip from
  wherever you run it, including any retry waits on routes with retries enabled (the
  default free route has them off).

## Safety rails for a free budget

- **Hard token ceiling** (`JEV_MAX_TOTAL_INPUT_TOKENS`, default 3M). It counts earlier cached
  runs too, and refuses the call that would cross it rather than warning after.
- **Answer cache** (`.cache/jev_decisions.jsonl`), append-only and keyed by route, model,
  prompt fingerprint and message. It stores no message text.
- **Pacing and retries** are configurable per route, because OpenCode counts retries
  against its daily cap.
- **The key never leaves `.env`:** it is held in a `SecretStr`, masked by a logging filter,
  and TypeSafe SDK body logging is silenced.

## Project layout

```
app/
  domain/        pure types and scoring (stdlib only): metrics, catalog, results
  services/      use cases: sampling, cosine voting, cross-encoder, trained classifier, Jev
                 runner, budget, report, chart
  services/ports Protocols (Embedder, PairScorer, ClassifierTrainer, JevDecider)
  repositories/  dataset files, prompt catalog, Jev answer cache, results
  clients/       adapters: TypeSafe SDK, sentence-transformers, scikit-learn
  core/          settings, logging, run id
  main.py        CLI: download | run-cosine | run-cross-encoder | run-trained | run-jev | report
prompts/         versioned category descriptions (the "prompt")
results/         committed outputs: REPORT.md, chart, per-message predictions
tests/unit/      pytest suite mirroring app/
```

## Quality gates

```bash
.venv/bin/ruff format --check . && .venv/bin/ruff check .
.venv/bin/mypy --strict app
.venv/bin/pytest -q --cov=app --cov-fail-under=85
.venv/bin/pip-audit --skip-editable
```

CI runs the same gates on every push and pull request (`.github/workflows/ci.yml`).

## Data and credits

[Banking77](https://github.com/PolyAI-LDN/task-specific-datasets) is by PolyAI (Casanueva et
al., 2020), licensed CC BY 4.0. `results/predictions/` repeats test-split messages next to
each method's answers, for error analysis.

## Limitations

- One dataset (English banking intents, mostly topic-like categories, where cosine is
  strong). Judgement-heavy tasks may look very different.
- One embedding model (`bge-small`, chosen for speed on a laptop). Larger ones may score higher.
- One cross-encoder (`bge-reranker-v2-m3`, trained for search relevance, not classification).
  A 2026 zero-shot benchmark ([BTZSC](https://arxiv.org/abs/2603.11991)) found larger rerankers
  such as Qwen3-Reranker-8B do much better, so D is a lower bound for the approach.
- Jev results come from a free route. If you change the route, compare within one route,
  not across routes.
- Jev latency depends heavily on distance to its US-hosted servers.
