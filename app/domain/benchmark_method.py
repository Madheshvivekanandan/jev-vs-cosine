"""The methods the benchmark compares."""

from enum import StrEnum


class BenchmarkMethod(StrEnum):
    """A: cosine vs descriptions, B: Jev, C: cosine vs past examples (top-k vote),
    D: cross-encoder (reranker) vs descriptions, E: classifier trained on past examples,
    B+: Jev with past examples added to its descriptions."""

    COSINE_DESCRIPTIONS = "A_cosine_descriptions"
    JEV = "B_jev"
    JEV_WITH_EXAMPLES = "B_plus_jev_with_examples"
    COSINE_EXAMPLES = "C_cosine_examples"
    CROSS_ENCODER_DESCRIPTIONS = "D_cross_encoder_descriptions"
    TRAINED_CLASSIFIER = "E_trained_classifier"
