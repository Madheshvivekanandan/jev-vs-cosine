"""Shared array type for embeddings."""

import numpy as np
import numpy.typing as npt

type FloatMatrix = npt.NDArray[np.float32]
"""One embedding per row."""
