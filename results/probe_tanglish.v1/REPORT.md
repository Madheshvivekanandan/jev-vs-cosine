# Results: Jev vs cosine similarity on Banking77

_Jev (method B) has not been run yet; only the cosine methods are shown._

A classifier trained on the same past examples (method E) reaches **52.8%** with 35 per category.

A local cross-encoder that reads each message together with each description (method D) scores **53.5%**, +11.8 points vs cosine vs descriptions, at 874 ms per message on CPU.

![Accuracy vs past examples per category](accuracy_vs_examples.png)

| Method | Past examples per category | Accuracy (95% CI) | Median latency | p95 latency | Input tokens | List-price cost |
|---|---|---|---|---|---|---|
| A · cosine vs descriptions | 0 | 41.7% (33.9%–49.8%) | 7 ms | 9 ms | 0 | $0.0000 |
| D · cross-encoder vs descriptions | 0 | 53.5% (45.3%–61.4%) | 874 ms | 1390 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 1 | 44.2% (range 39.6%–46.5% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 5 | 52.8% (range 52.1%–54.2% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 10 | 56.5% (range 54.9%–58.3% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 20 | 60.0% (range 59.7%–60.4% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 35 | 64.6% (range 61.1%–67.4% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 1 | 42.6% (range 37.5%–45.8% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 5 | 51.4% (range 47.2%–54.2% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 10 | 53.9% (range 50.7%–59.0% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 20 | 53.7% (range 48.6%–57.6% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 35 | 52.8% (range 50.7%–55.6% over 3 draws) | 7 ms | 9 ms | 0 | $0.0000 |

## How to read this

- Every method answered the same 144 messages of probe `tanglish.v1`; `probes/README.md` explains how they were built and checked.
- A embeds each category's name plus its one-line description. B (Jev) gets the same names and descriptions as Choice options, plus a one-sentence instruction. C compares against past customer messages from the training split (1, 5, 10, 20, 35 per category), drawn with 3 random seeds; 7 training rows that duplicated a test message (ignoring case and whitespace) were removed first.
- Prompt catalog: `banking77_intents.v1`. Embedding model: `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, run locally on CPU (free). Jev: not run.
- D scores (message, name + description) for every category with a cross-encoder reranker (`BAAI/bge-reranker-v2-m3@953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`), 77 pairs per message, locally on CPU, with no examples. Its latency is all 77 pairs for one message.
- E trains a logistic-regression classifier on the embeddings of the same past examples C votes with (same seeds, same messages). Training is offline and untimed.
- B+ appends the seed-1 past examples C and E use at that setting to each of Jev's category descriptions, so its catalog, token count and cache namespace differ from B.
- Latency for A and C is local embedding plus scoring per message. For Jev it is the full network round trip, including retry waits on routes with retries enabled.
- List-price cost is what the run would cost at $0.042 per million input tokens, even when the route used was free.
