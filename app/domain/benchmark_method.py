"""The three methods the benchmark compares."""

from enum import StrEnum


class BenchmarkMethod(StrEnum):
    """A: cosine vs descriptions, B: Jev, C: cosine vs past examples (top-k vote)."""

    COSINE_DESCRIPTIONS = "A_cosine_descriptions"
    JEV = "B_jev"
    COSINE_EXAMPLES = "C_cosine_examples"
