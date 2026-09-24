# Probe sets

Small test sets that target specific weaknesses. Every method runs on them the same way it
runs on the Banking77 sample: `python -m app.main <command> --probe <name>`. Results go
to `results/probe_<name>/`. Each line is `{"text", "label", ...}`; the extra fields only
document how the item was built.

| Probe | Items | What it tests |
|---|---|---|
| `tricky.v1` | 105 | Messages whose surface words point to the wrong category |
| `english_source.v1` | 144 | The English originals of the two code-mixed sets |
| `hinglish.v1` | 144 | The same 144 messages in romanised Hindi-English code-mixing |
| `tanglish.v1` | 144 | The same 144 messages in romanised Tamil-English code-mixing |

## `tricky.v1`: messages built to mislead surface matching

Three generator agents each wrote 35 new messages for one trap family:

- **negation** (35): "My card isn't lost or stolen, ... but the chip seems dead" → `card_not_working`
- **distractor** (35): another category's key words appear as background or a resolved event
- **indirect** (28) and **two_topics** (7): the request uses none of its category's obvious
  words, or one of two topics is plainly the request

Each item records the wrong category a keyword matcher would likely pick (`distractor_label`).
Three independent labeler agents then labelled every message **blind**: they saw the 77
categories but not the intended answer. An item was kept only if all three chose the
intended category and none marked it ambiguous. All 105 passed. The set covers 53
categories.

This set is adversarial **by construction** for methods that match surface words (A, C, E).
Read its numbers as "how badly does each method fail on these patterns", not as typical
accuracy.

## `hinglish.v1` / `tanglish.v1`: code-mixed Indian English

`english_source.v1` is 144 messages from the first 249 of the Banking77 test sample: up to
two per category, all 77 categories. Jev had already answered all of them, so the English
baseline costs no extra quota. One translator agent per language rewrote each message as
natural romanised code-mixed chat, keeping banking terms such as card, transfer, top up and
PIN in English, as real users do. Two independent judge agents per language compared every
rewrite with its original. A rewrite was kept only if both judged the request and facts
unchanged and at least one judged it natural. All 144 passed in both languages.
`source_text` links each rewrite to its original.

## Limitations

- **Generated and checked by LLM agents (Claude models), not by people.** Unanimous blind
  agreement and meaning checks reduce errors, but the generators and checkers share a model
  family. A 100% pass rate also means the checks may have been lenient.
- A native-speaker spot check of the Hinglish and Tanglish rewrites would strengthen them.
  Corrections are welcome as a new version (`*.v2.jsonl`); never edit a released version.
- The code-mixed sets reuse Banking77 content under CC BY 4.0 (PolyAI). The tricky set is new
  text written for this benchmark.
