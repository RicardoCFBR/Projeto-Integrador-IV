from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Protocol


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThresholdSource(Protocol):
    high_below_cycles: Decimal
    medium_below_cycles: Decimal


DEFAULT_HIGH_BELOW_CYCLES = Decimal("50")
DEFAULT_MEDIUM_BELOW_CYCLES = Decimal("150")


@dataclass(frozen=True)
class RiskClassifier:
    """Maps an estimated remaining useful life, in charge cycles, to a risk band.

    The default thresholds are experimental placeholders and must be replaced by the
    values agreed with the fleet operator.
    """

    high_below_cycles: Decimal = DEFAULT_HIGH_BELOW_CYCLES
    medium_below_cycles: Decimal = DEFAULT_MEDIUM_BELOW_CYCLES

    def __post_init__(self) -> None:
        if self.medium_below_cycles <= self.high_below_cycles:
            raise ValueError("medium_below_cycles must be greater than high_below_cycles")

    @classmethod
    def from_policy(cls, policy: ThresholdSource) -> "RiskClassifier":
        return cls(
            high_below_cycles=Decimal(policy.high_below_cycles),
            medium_below_cycles=Decimal(policy.medium_below_cycles),
        )

    def classify(self, rul_cycles: Decimal) -> RiskLevel:
        if rul_cycles < self.high_below_cycles:
            return RiskLevel.HIGH
        if rul_cycles < self.medium_below_cycles:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
