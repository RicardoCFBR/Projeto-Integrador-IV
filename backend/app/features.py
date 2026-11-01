from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

import pandas as pd

FEATURES = (
    "cycle_count",
    "temperature_mean_7d",
    "temperature_max_7d",
    "temperature_std_7d",
    "temperature_mean_30d",
    "temperature_std_30d",
    "hot_days_30d",
    "daily_cycles_mean_7d",
    "daily_cycles_std_7d",
    "daily_cycles_mean_30d",
    "daily_cycles_std_30d",
    "deep_discharge_events_30d",
    "cycle_count_change_30d",
    "battery_level_mean_7d",
    "voltage_mean_7d",
    "voltage_std_7d",
    "observation_age_days",
)

# The 30-day change and the daily cycles are differences, so 30 days need one more reading.
REQUIRED_DAYS = 31
HOT_DAY_CELSIUS = 35.0


class TelemetryReading(Protocol):
    recorded_at: datetime
    battery_temp_c: Decimal
    battery_level_pct: int
    voltage_mv: int
    cycle_count: Decimal
    deep_discharge_count: int


class InsufficientHistoryError(ValueError):
    pass


@dataclass(frozen=True)
class FeatureSnapshot:
    values: dict[str, float]
    telemetry_until: datetime


def _daily_frame(readings: Sequence[TelemetryReading]) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "recorded_at": pd.to_datetime([row.recorded_at for row in readings], utc=True),
            "temperature": [float(row.battery_temp_c) for row in readings],
            "level": [float(row.battery_level_pct) for row in readings],
            "voltage": [float(row.voltage_mv) for row in readings],
            "cycle_count": [float(row.cycle_count) for row in readings],
            "deep_discharge_count": [float(row.deep_discharge_count) for row in readings],
        }
    ).sort_values("recorded_at")
    return frame.groupby(frame["recorded_at"].dt.normalize()).agg(
        temperature=("temperature", "mean"),
        level=("level", "mean"),
        voltage=("voltage", "mean"),
        cycle_count=("cycle_count", "last"),
        deep_discharge_count=("deep_discharge_count", "last"),
    )


def _required_window(daily: pd.DataFrame) -> pd.DataFrame:
    if len(daily) < REQUIRED_DAYS:
        raise InsufficientHistoryError(
            f"history has {len(daily)} days of telemetry; {REQUIRED_DAYS} are required"
        )
    window = daily.tail(REQUIRED_DAYS)
    if (window.index[-1] - window.index[0]).days != REQUIRED_DAYS - 1:
        raise InsufficientHistoryError(
            f"the latest {REQUIRED_DAYS} days of telemetry must be consecutive"
        )
    return window


def build_features(readings: Sequence[TelemetryReading]) -> FeatureSnapshot:
    """Compute the model inputs from a device history with the same windows used in training."""
    if not readings:
        raise InsufficientHistoryError(
            f"history has 0 days of telemetry; {REQUIRED_DAYS} are required"
        )
    daily = _daily_frame(readings)
    window = _required_window(daily)

    last_30 = window.tail(30)
    last_7 = window.tail(7)
    daily_cycles = window["cycle_count"].diff().dropna()
    deep_discharges = window["deep_discharge_count"].diff().dropna().clip(lower=0)

    values = {
        "cycle_count": window["cycle_count"].iloc[-1],
        "temperature_mean_7d": last_7["temperature"].mean(),
        "temperature_max_7d": last_7["temperature"].max(),
        "temperature_std_7d": last_7["temperature"].std(),
        "temperature_mean_30d": last_30["temperature"].mean(),
        "temperature_std_30d": last_30["temperature"].std(),
        "hot_days_30d": (last_30["temperature"] >= HOT_DAY_CELSIUS).sum(),
        "daily_cycles_mean_7d": daily_cycles.tail(7).mean(),
        "daily_cycles_std_7d": daily_cycles.tail(7).std(),
        "daily_cycles_mean_30d": daily_cycles.mean(),
        "daily_cycles_std_30d": daily_cycles.std(),
        "deep_discharge_events_30d": deep_discharges.sum(),
        "cycle_count_change_30d": window["cycle_count"].iloc[-1] - window["cycle_count"].iloc[0],
        "battery_level_mean_7d": last_7["level"].mean(),
        "voltage_mean_7d": last_7["voltage"].mean(),
        "voltage_std_7d": last_7["voltage"].std(),
        "observation_age_days": (daily.index[-1] - daily.index[0]).days,
    }
    return FeatureSnapshot(
        values={name: float(values[name]) for name in FEATURES},
        telemetry_until=max(row.recorded_at for row in readings),
    )
