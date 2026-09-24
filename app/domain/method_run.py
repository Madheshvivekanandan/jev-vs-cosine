"""A method's scores together with the per-message predictions behind them."""

from dataclasses import dataclass

from app.domain.method_result import MethodResult
from app.domain.prediction import Prediction


@dataclass(frozen=True, slots=True)
class MethodRun:
    """Keeps predictions next to their summary so errors can be inspected later."""

    result: MethodResult
    predictions: tuple[Prediction, ...]
