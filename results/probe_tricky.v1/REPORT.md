# Results: Jev vs cosine similarity on Banking77

**With no examples, Jev leads cosine by 35.2 points; cosine vs past examples does not reach Jev within the tested range.**

A classifier trained on the same past examples (method E) does not reach Jev within the tested range, and scores 64.1% with 35 per category.

A local cross-encoder that reads each message together with each description (method D) scores **79.0%**, -21.0 points vs Jev, at 1115 ms per message on CPU.

![Accuracy vs past examples per category](accuracy_vs_examples.png)

| Method | Past examples per category | Accuracy (95% CI) | Median latency | p95 latency | Input tokens | List-price cost |
|---|---|---|---|---|---|---|
| A · cosine vs descriptions | 0 | 64.8% (55.3%–73.2%) | 7 ms | 8 ms | 0 | $0.0000 |
| B · Jev | 0 | 100.0% (96.5%–100.0%) | 591 ms | 696 ms | 251,051 | $0.0105 |
| D · cross-encoder vs descriptions | 0 | 79.0% (70.3%–85.7%) | 1115 ms | 1213 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 1 | 48.9% (range 46.7%–50.5% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 5 | 61.3% (range 57.1%–64.8% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 10 | 56.2% (range 51.4%–60.0% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 20 | 61.9% (range 59.0%–63.8% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 35 | 60.6% (range 59.0%–61.9% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 1 | 50.2% (range 47.6%–51.4% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 5 | 64.1% (range 58.1%–68.6% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 10 | 62.5% (range 59.0%–66.7% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 20 | 65.7% (range 63.8%–68.6% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 35 | 64.1% (range 62.9%–65.7% over 3 draws) | 7 ms | 8 ms | 0 | $0.0000 |

## How to read this

- Every method answered the same 105 messages of probe `tricky.v1`; `probes/README.md` explains how they were built and checked.
- A embeds each category's name plus its one-line description. B (Jev) gets the same names and descriptions as Choice options, plus a one-sentence instruction. C compares against past customer messages from the training split (1, 5, 10, 20, 35 per category), drawn with 3 random seeds; 7 training rows that duplicated a test message (ignoring case and whitespace) were removed first.
- Prompt catalog: `banking77_intents.v1`. Embedding model: `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, run locally on CPU (free). Jev: `opencode.ai/jev-1.13-free` (model reported: jev-1.13-free).
- D scores (message, name + description) for every category with a cross-encoder reranker (`BAAI/bge-reranker-v2-m3@953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`), 77 pairs per message, locally on CPU, with no examples. Its latency is all 77 pairs for one message.
- E trains a logistic-regression classifier on the embeddings of the same past examples C votes with (same seeds, same messages). Training is offline and untimed.
- B+ appends the seed-1 past examples C and E use at that setting to each of Jev's category descriptions, so its catalog, token count and cache namespace differ from B.
- Latency for A and C is local embedding plus scoring per message. For Jev it is the full network round trip, including retry waits on routes with retries enabled.
- List-price cost is what the run would cost at $0.042 per million input tokens, even when the route used was free.
