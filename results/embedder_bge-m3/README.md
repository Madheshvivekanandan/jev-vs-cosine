# Embedder swap: `bge-m3` instead of `bge-small-en-v1.5`

Methods A, C and E embed text with `BAAI/bge-small-en-v1.5`, an English-only model. This folder
re-runs those three methods with `BAAI/bge-m3@5617a9f`, a multilingual model about 17 times
larger, to test whether the drop on Hinglish and Tanglish comes only from the English model.
Nothing else changes: same samples, same descriptions, same past examples and seeds.

Jev and the cross-encoder are not re-run (they do not use this embedder), so the `REPORT.md`
files here say Jev "has not been run". Compare with the matching folder one level up.

| Sample | Method | `bge-small-en` | `bge-m3` | Jev, no examples |
|---|---|---|---|---|
| English, 1,001 | A · cosine vs descriptions | 73.2% | 67.5% | 83.3% |
| English, 1,001 | E · classifier, 35 examples | 91.3% | 92.1% | |
| English originals, 144 | Best of C and E, 35 examples | 93.8% | 93.8% | 86.1% |
| Hinglish, 144 | A · cosine vs descriptions | 47.9% | 49.3% | 85.4% |
| Hinglish, 144 | Best of C and E, 35 examples | 63.7% | 69.9% | |
| Tanglish, 144 | A · cosine vs descriptions | 41.7% | 50.7% | 77.1% |
| Tanglish, 144 | Best of C and E, 35 examples | 64.6% | 67.6% | |
| Trick questions, 105 | A · cosine vs descriptions | 64.8% | 72.4% | 100.0% |
| Trick questions, 105 | Best of C and E, 35 examples | 64.1% | 76.5% | |

The multilingual model narrows the gap on code-mixed and trick messages but stays 8 to 16
points below Jev, and it is worse than the English model at matching one-line descriptions on
English. C and E accuracies are means over the same 3 random draws as everywhere else.

Reproduce (local, free; downloads about 2.3 GB once):

```bash
export RESULTS_DIR=results/embedder_bge-m3 EMBEDDING_MODEL_NAME=BAAI/bge-m3 \
  EMBEDDING_MODEL_REVISION=5617a9f61b028005a4858fdac845db406aefb181
.venv/bin/python -m app.main run-cosine --probe hinglish.v1    # and the other samples
.venv/bin/python -m app.main run-trained --probe hinglish.v1
.venv/bin/python -m app.main report --probe hinglish.v1
```
