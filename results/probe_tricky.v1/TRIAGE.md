# When to trust an answer, and when to ask Jev

Probe tricky.v1: 105 messages. Everything here replays saved predictions, so it calls no model and costs nothing.

## Jev: route only its confident answers

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 94.3% | 100.0% | 0 | 6 |
| 0.99 | 99.0% | 100.0% | 0 | 1 |
| 0.95 | 100.0% | 100.0% | 0 | 0 |
| 0.90 | 100.0% | 100.0% | 0 | 0 |
| 0.80 | 100.0% | 100.0% | 0 | 0 |
| 0.50 | 100.0% | 100.0% | 0 | 0 |

Jev got 0 of 105 messages wrong in total.

## Classifier (method E): the same, with its own probabilities

With 5 past examples per category, pooled over 3 random draws (315 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 315 |
| 0.99 | 0.0% | – | 0 | 315 |
| 0.95 | 0.0% | – | 0 | 315 |
| 0.90 | 1.0% | 100.0% | 0 | 312 |
| 0.80 | 3.8% | 83.3% | 2 | 303 |
| 0.50 | 27.6% | 80.5% | 17 | 228 |

With 35 past examples per category, pooled over 3 random draws (315 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 315 |
| 0.99 | 1.3% | 100.0% | 0 | 311 |
| 0.95 | 7.9% | 84.0% | 4 | 290 |
| 0.90 | 19.0% | 85.0% | 9 | 255 |
| 0.80 | 34.3% | 84.3% | 17 | 207 |
| 0.50 | 67.0% | 78.7% | 45 | 104 |

## Cheap first, Jev only when needed

| Strategy | Past examples per category | Accuracy | Messages sent to Jev |
|---|---|---|---|
| Jev alone | 0 | 100.0% | 100.0% |
| Classifier alone | 5 | 64.1% | 0.0% |
| Cosine voting and classifier agree, else Jev | 5 | 82.5% | 30.2% |
| Classifier confidence at least 0.9, else Jev | 5 | 100.0% | 99.0% |
| Classifier confidence at least 0.7, else Jev | 5 | 98.7% | 89.5% |
| Classifier confidence at least 0.5, else Jev | 5 | 94.6% | 72.4% |
| Classifier alone | 35 | 64.1% | 0.0% |
| Cosine voting and classifier agree, else Jev | 35 | 82.9% | 29.5% |
| Classifier confidence at least 0.9, else Jev | 35 | 97.1% | 81.0% |
| Classifier confidence at least 0.7, else Jev | 35 | 91.7% | 53.7% |
| Classifier confidence at least 0.5, else Jev | 35 | 85.7% | 33.0% |

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
