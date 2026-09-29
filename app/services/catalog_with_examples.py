"""Method B+: give Jev a few real past messages inside each category description."""

from collections.abc import Mapping, Sequence

from app.domain.intent_catalog import IntentCatalog
from app.domain.labeled_message import LabeledMessage


def catalog_with_examples(
    catalog: IntentCatalog,
    pools: Mapping[str, Sequence[LabeledMessage]],
    *,
    per_label: int,
    seed: int,
) -> IntentCatalog:
    """Return a copy of `catalog` whose descriptions end with `per_label` example messages.

    The examples are the first `per_label` of each seeded pool, the very messages methods C
    and E use at that setting and seed, so B+ is comparable with them point for point. The
    version records the examples, so cached Jev answers never mix with plain B.

    Raises:
        KeyError: If a catalog label has no pool.
    """
    descriptions = {
        label: _with_examples(description, [m.text for m in pools[label][:per_label]])
        for label, description in catalog.descriptions.items()
    }
    return IntentCatalog(
        version=f"{catalog.version}+examples{per_label}_seed{seed}",
        instructions=catalog.instructions,
        descriptions=descriptions,
    )


def _with_examples(description: str, examples: Sequence[str]) -> str:
    quoted = " | ".join(f'"{" ".join(text.split())}"' for text in examples)
    return f"{description}. Example customer messages: {quoted}"
