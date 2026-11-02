from decimal import Decimal

import pytest

from app.risk import RiskClassifier, RiskLevel


def test_default_thresholds_are_the_experimental_fleet_percentiles():
    classifier = RiskClassifier()
    assert classifier.high_below_cycles == Decimal("776")
    assert classifier.medium_below_cycles == Decimal("983")


@pytest.mark.parametrize(
    ("rul", "expected"),
    [
        ("0", RiskLevel.HIGH),
        ("700", RiskLevel.HIGH),
        ("775.99", RiskLevel.HIGH),
        ("776", RiskLevel.MEDIUM),
        ("900", RiskLevel.MEDIUM),
        ("982.99", RiskLevel.MEDIUM),
        ("983", RiskLevel.LOW),
        ("1200", RiskLevel.LOW),
    ],
)
def test_classify_uses_lower_bound_inclusive(rul, expected):
    assert RiskClassifier().classify(Decimal(rul)) is expected


def test_negative_rul_is_high_risk():
    assert RiskClassifier().classify(Decimal("-5")) is RiskLevel.HIGH


def test_custom_thresholds_are_respected():
    classifier = RiskClassifier(
        high_below_cycles=Decimal("100"), medium_below_cycles=Decimal("300")
    )
    assert classifier.classify(Decimal("99")) is RiskLevel.HIGH
    assert classifier.classify(Decimal("299")) is RiskLevel.MEDIUM
    assert classifier.classify(Decimal("300")) is RiskLevel.LOW


def test_medium_threshold_must_be_above_high_threshold():
    with pytest.raises(ValueError):
        RiskClassifier(high_below_cycles=Decimal("200"), medium_below_cycles=Decimal("100"))
    with pytest.raises(ValueError):
        RiskClassifier(high_below_cycles=Decimal("100"), medium_below_cycles=Decimal("100"))
