from datetime import date


def calculate_daily_cycles(
    daily_records: list[dict],
) -> list[dict]:
    """Calcula a variação diária do contador acumulado de ciclos."""

    results = []
    previous = None

    for record in sorted(daily_records, key=lambda row: row["date"]):
        current = record.copy()
        current["daily_cycles"] = None

        if previous is not None:
            previous_date = date.fromisoformat(previous["date"])
            current_date = date.fromisoformat(current["date"])

            if (current_date - previous_date).days == 1:
                difference = (
                    current["cycle_count"] - previous["cycle_count"]
                )
    
                if difference >= 0:
                    current["daily_cycles"] = difference
    
    results.append(current)
    previous = current

return results

    