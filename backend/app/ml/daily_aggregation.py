
from collections import defaultdict
from datetime import timezone

from app.models import BatteryTelemetry


def aggregate_daily_readings(
    readings: list[BatteryTelemetry],
) -> list[dict]:
    """Agrupa leituras de um dispositivo por dia UTC."""

    daily_aggregates = defaultdict(lambda: {
        "date": None,
        "device_id": None,
        "battery_level_pct": 0.0,
        "battery_temp_c": 0.0,
        "voltage_mv": 0.0,
        "is_charging": False,
        "cycle_count": None,
        "deep_discharge_count": None,
        "estimated_capacity_pct": 0.0,
        "ram_available_mb": 0.0,
        "count": 0,
        "capacity_count": 0,
        "ram_count": 0,
        "last_recorded_at": None,
    })

    for reading in sorted(readings, key=lambda r: r.recorded_at):

        date_key = reading.recorded_at.astimezone(
            timezone.utc
        ).date().isoformat()

        aggregate = daily_aggregates[date_key]

        if aggregate["date"] is None:
            aggregate["date"] = date_key
            aggregate["device_id"] = reading.device_id

        aggregate["battery_level_pct"] += reading.battery_level_pct
        aggregate["battery_temp_c"] += float(reading.battery_temp_c)
        aggregate["voltage_mv"] += reading.voltage_mv
        aggregate["is_charging"] |= reading.is_charging

        # Contadores acumulados: utilizar última leitura do dia.
        aggregate["cycle_count"] = float(reading.cycle_count)
        aggregate["deep_discharge_count"] = reading.deep_discharge_count
        aggregate["last_recorded_at"] = reading.recorded_at

        if reading.estimated_capacity_pct is not None:
            aggregate["estimated_capacity_pct"] += float(
                reading.estimated_capacity_pct
            )
            aggregate["capacity_count"] += 1

        if reading.ram_available_mb is not None:
            aggregate["ram_available_mb"] += reading.ram_available_mb
            aggregate["ram_count"] += 1

        aggregate["count"] += 1

    results = []

    for agg in daily_aggregates.values():
        count = agg.pop("count")
        capacity_count = agg.pop("capacity_count")
        ram_count = agg.pop("ram_count")
        agg.pop("last_recorded_at")

        agg["battery_level_pct"] /= count
        agg["battery_temp_c"] /= count
        agg["voltage_mv"] /= count

        agg["estimated_capacity_pct"] = (
            agg["estimated_capacity_pct"] / capacity_count
            if capacity_count > 0 else None
        )

        agg["ram_available_mb"] = (
            agg["ram_available_mb"] / ram_count
            if ram_count > 0 else None
        )

        results.append(agg)

    return sorted(results, key=lambda row: row["date"])
