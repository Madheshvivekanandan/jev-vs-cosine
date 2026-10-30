# Results: Jev vs cosine similarity on Banking77

_Jev (method B) has not been run yet; only the cosine methods are shown._

A classifier trained on the same past examples (method E) reaches **93.5%** with 35 per category.

![Accuracy vs past examples per category](accuracy_vs_examples.png)

| Method | Past examples per category | Accuracy (95% CI) | Median latency | p95 latency | Input tokens | List-price cost |
|---|---|---|---|---|---|---|
| A · cosine vs descriptions | 0 | 68.8% (60.8%–75.8%) | 50 ms | 59 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 1 | 64.1% (range 57.6%–68.8% over 3 draws) | 50 ms | 59 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 5 | 82.6% (range 79.2%–84.7% over 3 draws) | 50 ms | 59 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 10 | 88.7% (range 86.8%–91.7% over 3 draws) | 50 ms | 59 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 20 | 91.2% (range 89.6%–92.4% over 3 draws) | 50 ms | 59 ms | 0 | $0.0000 |
| C · cosine vs past examples (top-5 vote) | 35 | 93.8% (range 93.8%–93.8% over 3 draws) | 50 ms | 60 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 1 | 65.3% (range 59.0%–68.8% over 3 draws) | 53 ms | 67 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 5 | 90.7% (range 90.3%–91.0% over 3 draws) | 53 ms | 67 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 10 | 91.7% (range 91.0%–93.1% over 3 draws) | 53 ms | 67 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 20 | 92.6% (range 90.3%–94.4% over 3 draws) | 53 ms | 67 ms | 0 | $0.0000 |
| E · classifier trained on past examples | 35 | 93.5% (range 93.1%–93.8% over 3 draws) | 53 ms | 67 ms | 0 | $0.0000 |

## How to read this

- Every method answered the same 144 messages of probe `english_source.v1`; `probes/README.md` explains how they were built and checked.
- A embeds each category's name plus its one-line description. B (Jev) gets the same names and descriptions as Choice options, plus a one-sentence instruction. C compares against past customer messages from the training split (1, 5, 10, 20, 35 per category), drawn with 3 random seeds; 7 training rows that duplicated a test message (ignoring case and whitespace) were removed first.
- Prompt catalog: `banking77_intents.v1`. Embedding model: `BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181`, run locally on CPU (free). Jev: not run.
- D scores (message, name + description) for every category with a cross-encoder reranker (`not run`), 77 pairs per message, locally on CPU, with no examples. Its latency is all 77 pairs for one message.
- E trains a logistic-regression classifier on the embeddings of the same past examples C votes with (same seeds, same messages). Training is offline and untimed.
- B+ appends the seed-1 past examples C and E use at that setting to each of Jev's category descriptions, so its catalog, token count and cache namespace differ from B.
- Latency for A and C is local embedding plus scoring per message. For Jev it is the full network round trip, including retry waits on routes with retries enabled.
- List-price cost is what the run would cost at $0.042 per million input tokens, even when the route used was free.
