# When to trust an answer, and when to ask Jev

Banking77 test sample: 1,001 messages. Everything here replays saved predictions, so it calls no model and costs nothing.

## Jev: route only its confident answers

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 50.6% | 98.0% | 10 | 494 |
| 0.99 | 58.8% | 96.1% | 23 | 412 |
| 0.95 | 70.6% | 93.8% | 44 | 294 |
| 0.90 | 75.5% | 92.3% | 58 | 245 |
| 0.80 | 82.9% | 90.6% | 78 | 171 |
| 0.50 | 96.5% | 85.1% | 144 | 35 |

Jev got 167 of 1,001 messages wrong in total.

## Classifier (method E): the same, with its own probabilities

With 5 past examples per category, pooled over 3 random draws (3,003 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 3,003 |
| 0.99 | 0.0% | – | 0 | 3,003 |
| 0.95 | 2.7% | 100.0% | 0 | 2,922 |
| 0.90 | 12.4% | 100.0% | 0 | 2,631 |
| 0.80 | 33.8% | 98.5% | 15 | 1,988 |
| 0.50 | 69.1% | 94.9% | 105 | 927 |

With 35 past examples per category, pooled over 3 random draws (3,003 answers):

| Route automatically when confidence is at least | Messages routed automatically | Accuracy of those | Wrong answers routed automatically | Sent to a person |
|---|---|---|---|---|
| 1.00 | 0.0% | – | 0 | 3,003 |
| 0.99 | 16.8% | 99.8% | 1 | 2,497 |
| 0.95 | 51.7% | 99.4% | 10 | 1,451 |
| 0.90 | 66.8% | 99.1% | 19 | 996 |
| 0.80 | 77.8% | 98.5% | 35 | 668 |
| 0.50 | 92.8% | 94.7% | 147 | 216 |

## Cheap first, Jev only when needed

| Strategy | Past examples per category | Accuracy | Messages sent to Jev |
|---|---|---|---|
| Jev alone | 0 | 83.3% | 100.0% |
| Classifier alone | 5 | 84.2% | 0.0% |
| Cosine voting and classifier agree, else Jev | 5 | 86.2% | 15.8% |
| Classifier confidence at least 0.9, else Jev | 5 | 83.8% | 87.6% |
| Classifier confidence at least 0.7, else Jev | 5 | 86.1% | 52.1% |
| Classifier confidence at least 0.5, else Jev | 5 | 86.7% | 30.9% |
| Classifier alone | 35 | 91.3% | 0.0% |
| Cosine voting and classifier agree, else Jev | 35 | 92.5% | 6.7% |
| Classifier confidence at least 0.9, else Jev | 35 | 89.1% | 33.2% |
| Classifier confidence at least 0.7, else Jev | 35 | 91.6% | 15.6% |
| Classifier confidence at least 0.5, else Jev | 35 | 91.8% | 7.2% |

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
