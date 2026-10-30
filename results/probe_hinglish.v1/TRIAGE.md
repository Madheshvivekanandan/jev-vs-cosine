# When to trust an answer, and when to ask Jev

Probe hinglish.v1: 144 messages. Everything here replays saved predictions, so it calls no model and costs nothing.

## Jev: route only its confident answers

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 43.8% | 100.0% | 0 | 81 |
| 0.99 | 53.5% | 97.4% | 2 | 67 |
| 0.95 | 67.4% | 94.8% | 5 | 47 |
| 0.90 | 74.3% | 94.4% | 6 | 37 |
| 0.80 | 81.9% | 91.5% | 10 | 26 |
| 0.50 | 97.2% | 87.9% | 17 | 4 |

Jev got 21 of 144 messages wrong in total.

## Classifier (method E): the same, with its own probabilities

With 5 past examples per category, pooled over 3 random draws (432 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 432 |
| 0.99 | 0.0% | – | 0 | 432 |
| 0.95 | 0.0% | – | 0 | 432 |
| 0.90 | 0.5% | 100.0% | 0 | 430 |
| 0.80 | 2.5% | 100.0% | 0 | 421 |
| 0.50 | 13.4% | 94.8% | 3 | 374 |

With 35 past examples per category, pooled over 3 random draws (432 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 432 |
| 0.99 | 0.5% | 100.0% | 0 | 430 |
| 0.95 | 6.7% | 100.0% | 0 | 403 |
| 0.90 | 10.6% | 100.0% | 0 | 386 |
| 0.80 | 18.1% | 97.4% | 2 | 354 |
| 0.50 | 43.1% | 84.4% | 29 | 246 |

## Cheap first, Jev only when needed

| Strategy | Past examples per category | Accuracy | Messages sent to Jev |
|---|---|---|---|
| Jev alone | 0 | 85.4% | 100.0% |
| Classifier alone | 5 | 52.5% | 0.0% |
| Cosine voting and classifier agree, else Jev | 5 | 75.2% | 38.0% |
| Classifier confidence at least 0.9, else Jev | 5 | 85.4% | 99.5% |
| Classifier confidence at least 0.7, else Jev | 5 | 85.4% | 93.8% |
| Classifier confidence at least 0.5, else Jev | 5 | 85.0% | 86.6% |
| Classifier alone | 35 | 56.2% | 0.0% |
| Cosine voting and classifier agree, else Jev | 35 | 80.3% | 34.7% |
| Classifier confidence at least 0.9, else Jev | 35 | 85.6% | 89.4% |
| Classifier confidence at least 0.7, else Jev | 35 | 84.5% | 73.1% |
| Classifier confidence at least 0.5, else Jev | 35 | 82.9% | 56.9% |

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
