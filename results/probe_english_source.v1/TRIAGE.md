# When to trust an answer, and when to ask Jev

Probe english_source.v1: 144 messages. Everything here replays saved predictions, so it calls no model and costs nothing.

## Jev: route only its confident answers

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 50.0% | 98.6% | 1 | 72 |
| 0.99 | 59.0% | 94.1% | 5 | 59 |
| 0.95 | 72.2% | 93.3% | 7 | 40 |
| 0.90 | 77.1% | 93.7% | 7 | 33 |
| 0.80 | 85.4% | 92.7% | 9 | 21 |
| 0.50 | 97.9% | 87.2% | 18 | 3 |

Jev got 20 of 144 messages wrong in total.

## Classifier (method E): the same, with its own probabilities

With 5 past examples per category, pooled over 3 random draws (432 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 432 |
| 0.99 | 0.0% | – | 0 | 432 |
| 0.95 | 1.9% | 100.0% | 0 | 424 |
| 0.90 | 12.5% | 100.0% | 0 | 378 |
| 0.80 | 31.2% | 99.3% | 1 | 297 |
| 0.50 | 69.2% | 97.7% | 7 | 133 |

With 35 past examples per category, pooled over 3 random draws (432 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 432 |
| 0.99 | 16.4% | 100.0% | 0 | 361 |
| 0.95 | 49.1% | 100.0% | 0 | 220 |
| 0.90 | 68.1% | 100.0% | 0 | 138 |
| 0.80 | 78.7% | 99.4% | 2 | 92 |
| 0.50 | 93.3% | 95.5% | 18 | 29 |

## Cheap first, Jev only when needed

| Strategy | Past examples per category | Accuracy | Messages sent to Jev |
|---|---|---|---|
| Jev alone | 0 | 86.1% | 100.0% |
| Classifier alone | 5 | 88.7% | 0.0% |
| Cosine voting and classifier agree, else Jev | 5 | 89.4% | 15.5% |
| Classifier confidence at least 0.9, else Jev | 5 | 86.3% | 87.5% |
| Classifier confidence at least 0.7, else Jev | 5 | 88.0% | 54.2% |
| Classifier confidence at least 0.5, else Jev | 5 | 89.6% | 30.8% |
| Classifier alone | 35 | 93.1% | 0.0% |
| Cosine voting and classifier agree, else Jev | 35 | 95.4% | 6.2% |
| Classifier confidence at least 0.9, else Jev | 35 | 91.4% | 31.9% |
| Classifier confidence at least 0.7, else Jev | 35 | 92.6% | 13.7% |
| Classifier confidence at least 0.5, else Jev | 35 | 92.1% | 6.7% |

## How to read this

- The thresholds are a fixed grid, not tuned on this sample, so no row is a best case picked
  after the fact. Choose the row that matches how many wrong answers you can let through.
- "Sent to a person" and "Messages sent to Jev" are what a live system would escalate.
  Jev's cost and latency apply only to the messages sent to it.
- Rows with past examples are pooled over the same random draws as REPORT.md, so their
  accuracy is the mean over draws. A cascade pairs each draw of the classifier with the same
  draw of cosine voting.
- Jev's confidence is its probability for the chosen option. The classifier's is scikit-learn's
  predicted probability for its top label. The two are not on the same scale, so compare
  each method's rows with each other, not across methods.
