"""A customer message paired with its human-assigned intent."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LabeledMessage:
    """One Banking77 row: the customer's text and the correct intent label."""

    text: str
    label: str
