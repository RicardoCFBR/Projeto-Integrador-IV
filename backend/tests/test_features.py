import csv
import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app.config import get_settings
from app.features import FEATURES, REQUIRED_DAYS, InsufficientHistoryError, build_features

FIXTURES = Path(__file__).parent / "fixtures"
EXPECTED = json.loads((FIXTURES / "expected_features.json").read_text())
# The dataset rounds cycle_count to two decimals, so differences drift from daily_cycles.
# 0.006 covers the largest gap measured over the 400 synthetic devices.
ROUNDED_CYCLE_TOLERANCE = 6e-3
ROUNDED_CYCLE_FEATURES = {
    "daily_cycles_mean_7d",
    "daily_cycles_std_7d",
    "daily_cycles_mean_30d",
    "daily_cycles_std_30d",
}


@dataclass(frozen=True)
class Reading:
    recorded_at: datetime
    battery_temp_c: Decimal
    battery_level_pct: int
    voltage_mv: int
    cycle_count: Decimal
    deep_discharge_count: int


def _pipeline_history() -> list[Reading]:
    with (FIXTURES / "device_history.csv").open(encoding="utf-8") as file:
        return [
            Reading(
                recorded_at=datetime.fromisoformat(row["date"]).replace(tzinfo=UTC),
                battery_temp_c=Decimal(row["battery_temperature_c"]),
                battery_level_pct=int(row["battery_level_pct"]),
                voltage_mv=int(row["voltage_mv"]),
                cycle_count=Decimal(row["cycle_count"]),
                deep_discharge_count=int(row["deep_discharge_count"]),
            )
            for row in csv.DictReader(file)
        ]


def _flat_history(days: int) -> list[Reading]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        Reading(
            recorded_at=start + timedelta(days=day),
            battery_temp_c=Decimal("30"),
            battery_level_pct=50,
            voltage_mv=3900,
            cycle_count=Decimal(day),
            deep_discharge_count=0,
        )
        for day in range(days)
    ]


@pytest.mark.parametrize("day", sorted(EXPECTED))
def test_features_match_the_ml_pipeline(day):
    cutoff = datetime.fromisoformat(day).replace(tzinfo=UTC)
    history = [row for row in _pipeline_history() if row.recorded_at <= cutoff]

    snapshot = build_features(history)

    assert set(snapshot.values) == set(FEATURES)
    for name, expected in EXPECTED[day].items():
        tolerance = ROUNDED_CYCLE_TOLERANCE if name in ROUNDED_CYCLE_FEATURES else 1e-6
        assert snapshot.values[name] == pytest.approx(expected, abs=tolerance), name
    assert snapshot.telemetry_until == cutoff


def test_feature_order_matches_the_trained_model():
    metadata = json.loads(get_settings().rul_metadata_path.read_text())
    assert list(FEATURES) == metadata["features"]


def test_readings_are_aggregated_per_day():
    base = _flat_history(REQUIRED_DAYS)
    last = base[-1]
    earlier_same_day = replace(
        last,
        recorded_at=last.recorded_at - timedelta(hours=6),
        battery_temp_c=Decimal("40"),
        cycle_count=last.cycle_count - Decimal("0.5"),
    )
    later_same_day = replace(last, battery_temp_c=Decimal("30"))

    snapshot = build_features([*base[:-1], earlier_same_day, later_same_day])

    # Daily mean of 40 and 30 replaces the flat 30 on the last of the seven days.
    assert snapshot.values["temperature_mean_7d"] == pytest.approx((6 * 30 + 35) / 7)
    assert snapshot.values["temperature_max_7d"] == pytest.approx(35)
    assert snapshot.values["hot_days_30d"] == 1
    assert snapshot.values["cycle_count"] == float(last.cycle_count)
    assert snapshot.telemetry_until == last.recorded_at


def test_short_history_is_rejected():
    with pytest.raises(InsufficientHistoryError) as error:
        build_features(_flat_history(REQUIRED_DAYS - 1))
    assert str(REQUIRED_DAYS - 1) in str(error.value)
    assert str(REQUIRED_DAYS) in str(error.value)


def test_empty_history_is_rejected():
    with pytest.raises(InsufficientHistoryError):
        build_features([])


def test_gap_inside_the_window_is_rejected():
    history = _flat_history(REQUIRED_DAYS + 5)
    del history[-10]
    with pytest.raises(InsufficientHistoryError, match="consecutive"):
        build_features(history)


def test_gap_before_the_window_is_accepted():
    history = _flat_history(REQUIRED_DAYS + 5)
    del history[1]
    snapshot = build_features(history)
    assert snapshot.values["observation_age_days"] == REQUIRED_DAYS + 4
