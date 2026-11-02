
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.ml.daily_aggregation import aggregate_daily_readings


def test_daily_aggregation_preserves_cumulative_counters():
    def sample(hour, cycles, discharges):
        return SimpleNamespace(
            device_id=1,
            recorded_at=datetime(
                2026, 11, 1, hour, tzinfo=timezone.utc
            ),
            battery_level_pct=80,
            battery_temp_c=Decimal("32.00"),
            voltage_mv=3900,
            is_charging=False,
            cycle_count=Decimal(str(cycles)),
            deep_discharge_count=discharges,
            estimated_capacity_pct=None,
            ram_available_mb=None,
        )

    readings = [
        sample(18, "120.75", 4),
        sample(8, "120.15", 3),
        sample(12, "120.40", 3),
    ]

    result = aggregate_daily_readings(readings)

    assert len(result) == 1
    assert result[0]["date"] == "2026-11-01"
    assert result[0]["cycle_count"] == 120.75
    assert result[0]["deep_discharge_count"] == 4
    assert result[0]["battery_temp_c"] == 32.0
    assert result[0]["voltage_mv"] == 3900.0
