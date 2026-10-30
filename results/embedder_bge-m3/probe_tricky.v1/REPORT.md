# Results: Jev vs cosine similarity on Banking77

_This result set has no Jev (method B) run; only the methods run here are shown._

A classifier trained on the same past examples (method E) reaches **76.5%** with 35 per category.

![Accuracy vs past examples per category](accuracy_vs_examples.png)

| Method | Past examples per category | Accuracy (95% CI) | Median latency | p95 latency | Input tokens | List-price cost |
|---|---|---|---|---|---|---|
| A · cosine vs descriptions | 0 | 72.4% (63.2%–80.0%) | 43 ms | 58 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 1 | 54.6% (range 51.4%–60.0% over 3 draws) | 43 ms | 58 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 5 | 67.9% (range 65.7%–71.4% over 3 draws) | 43 ms | 58 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 10 | 71.1% (range 68.6%–73.3% over 3 draws) | 43 ms | 58 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 20 | 74.6% (range 73.3%–75.2% over 3 draws) | 43 ms | 58 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 35 | 73.7% (range 72.4%–76.2% over 3 draws) | 43 ms | 58 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 1 | 56.8% (range 53.3%–59.0% over 3 draws) | 39 ms | 52 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 5 | 72.4% (range 70.5%–76.2% over 3 draws) | 39 ms | 52 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 10 | 72.7% (range 72.4%–73.3% over 3 draws) | 39 ms | 52 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 20 | 73.0% (range 72.4%–73.3% over 3 draws) | 39 ms | 52 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 35 | 76.5% (range 76.2%–77.1% over 3 draws) | 39 ms | 52 ms | 0 | $0.0000 |

## How to read this

- Every method answered the same 105 messages of probe `tricky.v1`; `probes/README.md` explains how they were built and checked.
- A embeds each category's name plus its one-line description. B (Jev) gets the same names and descriptions as Choice options, plus a one-sentence instruction. C compares against past customer messages from the training split (1, 5, 10, 20, 35 per category), drawn with 3 random seeds; 7 training rows that duplicated a test message (ignoring case and whitespace) were removed first.
- Prompt catalog: `banking77_intents.v1`. Embedding model: `BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181`, run locally on CPU (free). Jev: not run.
- D scores (message, name + description) for every category with a cross-encoder reranker (`not run`), 77 pairs per message, locally on CPU, with no examples. Its latency is all 77 pairs for one message.
- E trains a logistic-regression classifier on the embeddings of the same past examples C votes with (same seeds, same messages). Training is offline and untimed.
- B+ appends the seed-1 past examples C and E use at that setting to each of Jev's category descriptions, so its catalog, token count and cache namespace differ from B.
- Latency for A and C is local embedding plus scoring per message. For Jev it is the full network round trip, including retry waits on routes with retries enabled.
- List-price cost is what the run would cost at $0.042 per million input tokens, even when the route used was free.
