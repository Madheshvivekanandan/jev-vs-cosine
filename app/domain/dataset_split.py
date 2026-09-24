"""The two Banking77 splits."""

from enum import StrEnum


class DatasetSplit(StrEnum):
    """Which Banking77 file to read: examples come from TRAIN, graded messages from TEST."""

    TRAIN = "train"
    TEST = "test"
