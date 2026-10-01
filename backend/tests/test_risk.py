from decimal import Decimal

import pytest

from app.risk import RiskClassifier, RiskLevel


def test_default_thresholds_are_the_experimental_placeholders():
    classifier = RiskClassifier()
    assert classifier.high_below_cycles == Decimal("50")
    assert classifier.medium_below_cycles == Decimal("150")


@pytest.mark.parametrize(
    ("rul", "expected"),
    [
        ("0", RiskLevel.HIGH),
        ("24", RiskLevel.HIGH),
        ("49.99", RiskLevel.HIGH),
        ("50", RiskLevel.MEDIUM),
        ("103", RiskLevel.MEDIUM),
        ("149.99", RiskLevel.MEDIUM),
        ("150", RiskLevel.LOW),
        ("284", RiskLevel.LOW),
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
