"""Helpers for applying bounded changes to the global detection level."""

from dataclasses import dataclass
from typing import Protocol


class DetectionModel(Protocol):
    detection_level: float
    config: object


@dataclass(frozen=True)
class DetectionUpdate:
    """The actual detection change after applying the configured upper bound."""

    previous: float
    current: float

    @property
    def delta(self) -> float:
        return self.current - self.previous


def apply_detection(model: DetectionModel, amount: float) -> DetectionUpdate:
    """Increase detection and clamp it to the model's configured maximum."""
    if amount < 0:
        raise ValueError("detection amount cannot be negative")

    previous = float(model.detection_level)
    maximum = float(getattr(model.config, "max_detection_level"))
    model.detection_level = min(maximum, max(0.0, previous + amount))
    return DetectionUpdate(previous=previous, current=model.detection_level)
