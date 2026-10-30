# When to trust an answer, and when to ask Jev

Probe tanglish.v1: 144 messages. Everything here replays saved predictions, so it calls no model and costs nothing.

## Jev: route only its confident answers

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 22.2% | 100.0% | 0 | 112 |
| 0.99 | 28.5% | 100.0% | 0 | 103 |
| 0.95 | 41.0% | 96.6% | 2 | 85 |
| 0.90 | 43.1% | 96.8% | 2 | 82 |
| 0.80 | 52.8% | 92.1% | 6 | 68 |
| 0.50 | 84.0% | 81.8% | 22 | 23 |

Jev got 33 of 144 messages wrong in total.

## Classifier (method E): the same, with its own probabilities

With 5 past examples per category, pooled over 3 random draws (432 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 432 |
| 0.99 | 0.0% | – | 0 | 432 |
| 0.95 | 0.0% | – | 0 | 432 |
| 0.90 | 0.7% | 100.0% | 0 | 429 |
| 0.80 | 0.7% | 100.0% | 0 | 429 |
| 0.50 | 13.7% | 94.9% | 3 | 373 |

With 35 past examples per category, pooled over 3 random draws (432 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 432 |
| 0.99 | 0.7% | 100.0% | 0 | 429 |
| 0.95 | 4.9% | 100.0% | 0 | 411 |
| 0.90 | 9.0% | 100.0% | 0 | 393 |
| 0.80 | 17.4% | 96.0% | 3 | 357 |
| 0.50 | 42.8% | 87.6% | 23 | 247 |

## Cheap first, Jev only when needed

| Strategy | Past examples per category | Accuracy | Messages sent to Jev |
|---|---|---|---|
| Jev alone | 0 | 77.1% | 100.0% |
| Classifier alone | 5 | 51.4% | 0.0% |
| Cosine voting and classifier agree, else Jev | 5 | 70.8% | 37.5% |
| Classifier confidence at least 0.9, else Jev | 5 | 77.1% | 99.3% |
| Classifier confidence at least 0.7, else Jev | 5 | 77.5% | 95.6% |
| Classifier confidence at least 0.5, else Jev | 5 | 77.5% | 86.3% |
| Classifier alone | 35 | 52.8% | 0.0% |
| Cosine voting and classifier agree, else Jev | 35 | 75.9% | 38.9% |
| Classifier confidence at least 0.9, else Jev | 35 | 78.2% | 91.0% |
| Classifier confidence at least 0.7, else Jev | 35 | 78.7% | 74.5% |
| Classifier confidence at least 0.5, else Jev | 35 | 78.5% | 57.2% |

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
