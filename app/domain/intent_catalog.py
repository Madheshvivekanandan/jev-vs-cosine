"""The versioned intent list that cosine and Jev both receive verbatim."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class IntentCatalog:
    """Intent labels with one-line descriptions, plus the question Jev is asked.

    The same descriptions feed method A (cosine) and method B (Jev), so any difference
    in accuracy comes from the method, not from the wording each one saw.
    """

    version: str
    instructions: str
    descriptions: Mapping[str, str]

    def __post_init__(self) -> None:
        """Reject an empty catalog and freeze the descriptions mapping."""
        if not self.descriptions:
            raise ValueError("an intent catalog needs at least one label")
        object.__setattr__(self, "descriptions", MappingProxyType(dict(self.descriptions)))

    @property
    def labels(self) -> tuple[str, ...]:
        """Return the labels in catalog order."""
        return tuple(self.descriptions)

    def embedding_text(self, label: str) -> str:
        """Return the text embedded for a label: its readable name, then its description."""
        return f"{label.replace('_', ' ')}: {self.descriptions[label]}"

    def fingerprint(self) -> str:
        """Return a hash that changes whenever any wording Jev sees changes."""
        canonical = json.dumps(
            {
                "version": self.version,
                "instructions": self.instructions,
                "descriptions": dict(self.descriptions),
            },
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
