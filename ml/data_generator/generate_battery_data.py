from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# CONFIGURAÇÃO DA SIMULAÇÃO

RANDOM_SEED = 42

NUM_DEVICES = 400
NUM_DAYS = 180

# Critério experimental utilizado nesta PoC.
# 70% de SoH NÃO deve ser interpretado como limite universal.

EOL_SOH_PERCENT = 70.0

np.random.seed(RANDOM_SEED)

# PERFIS DE UTILIZAÇÃO

PROFILES = {
    "light": {
        "daily_cycles_mean": 0.45,
        "temperature_mean": 30.0,
        "degradation_per_cycle": 0.020,
        "deep_discharge_probability": 0.02,
    },
    "normal": {
        "daily_cycles_mean": 0.75,
        "temperature_mean": 33.0,
        "degradation_per_cycle": 0.028,
        "deep_discharge_probability": 0.05,
    },
    "heavy": {
        "daily_cycles_mean": 1.10,
        "temperature_mean": 36.0,
        "degradation_per_cycle": 0.038,
        "deep_discharge_probability": 0.10,
    },
}


def generate_device(device_number: int) -> list[dict]:
    
    device_id = f"DEVICE-{device_number:04d}"

    # Escolhe perfil de utilização.

    profile_name = np.random.choice(
        ["light", "normal", "heavy"],
        p=[0.25, 0.55, 0.20],
    )

    profile = PROFILES[profile_name]

    # Capacidade original da bateria.

    design_capacity = np.random.randint(4000, 5501)

    # Pequena variação entre dispositivos do mesmo perfil.

    degradation_rate = profile["degradation_per_cycle"] * np.random.uniform(
        0.85,
        1.15,
    )

    current_soh = np.random.uniform(98.5, 100.0)

    cycle_count = np.random.randint(0, 80)

    deep_discharge_count = 0

    start_date = datetime(2026, 1, 1)

    rows = []

    for day in range(NUM_DAYS):

        date = start_date + timedelta(days=day)

        # USO DIÁRIO

        daily_cycles = max(
            0.05,
            np.random.normal(
                profile["daily_cycles_mean"],
                0.15,
            ),
        )

        cycle_count += daily_cycles

        # TEMPERATURA

        temperature = np.random.normal(
            profile["temperature_mean"],
            2.0,
        )

        temperature = np.clip(
            temperature,
            22.0,
            48.0,
        )

        # DESCARGA PROFUNDA

        deep_discharge = (
            np.random.random()
            < profile["deep_discharge_probability"]
        )

        if deep_discharge:
            deep_discharge_count += 1

        # FATORES DE ESTRESSE

        temperature_stress = 1.0

        if temperature > 35:
            temperature_stress += (temperature - 35) * 0.025

        deep_discharge_stress = 1.15 if deep_discharge else 1.0

        # Pequeno ruído para evitar trajetórias idênticas.

        random_stress = np.random.normal(1.0, 0.03)

        # DEGRADAÇÃO

        soh_loss = (
            daily_cycles
            * degradation_rate
            * temperature_stress
            * deep_discharge_stress
            * random_stress
        )

        current_soh -= soh_loss

        current_soh = max(current_soh, 50.0)

        # CAPACIDADE ATUAL

        current_capacity = (
            design_capacity
            * current_soh
            / 100.0
        )

        # NÍVEL DA BATERIA NO MOMENTO DA LEITURA

        battery_level = np.random.randint(15, 101)

        # TENSÃO SIMPLIFICADA

        voltage_mv = np.random.normal(
            3800,
            120,
        )

        voltage_mv = int(
            np.clip(
                voltage_mv,
                3300,
                4400,
            )
        )

        # RUL SINTÉTICO

        remaining_soh = max(
            0,
            current_soh - EOL_SOH_PERCENT,
        )

        if degradation_rate > 0:
            rul_cycles = remaining_soh / degradation_rate
        else:
            rul_cycles = 0

        # REGISTRO

        rows.append(
            {
                "device_id": device_id,
                "date": date.date(),
                "usage_profile": profile_name,
                "battery_design_capacity_mah": design_capacity,
                "battery_current_capacity_mah": round(
                    current_capacity,
                    2,
                ),
                "battery_temperature_c": round(
                    temperature,
                    2,
                ),
                "battery_level_pct": battery_level,
                "voltage_mv": voltage_mv,
                "daily_cycles": round(
                    daily_cycles,
                    3,
                ),
                "cycle_count": round(
                    cycle_count,
                    2,
                ),
                "deep_discharge_count": deep_discharge_count,
                "soh_percent": round(
                    current_soh,
                    3,
                ),
                "rul_cycles": round(
                    rul_cycles,
                    2,
                ),
            }
        )

    return rows


def main():

    print("Gerador de Telemetria Sintética")

    print()
    print(f"Gerando {NUM_DEVICES} dispositivos...")
    print(f"Histórico: {NUM_DAYS} dias")

    all_rows = []

    for device_number in range(1, NUM_DEVICES + 1):

        device_rows = generate_device(device_number)

        all_rows.extend(device_rows)

    df = pd.DataFrame(all_rows)

    project_root = Path(__file__).resolve().parents[2]

    output_dir = (
        project_root
        / "data"
        / "synthetic"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_dir
        / "battery_telemetry.csv"
    )

    df.to_csv(
        output_file,
        index=False,
    )

    print()
    print("SIMULAÇÃO CONCLUÍDA")

    print(f"Dispositivos: {df['device_id'].nunique()}")
    print(f"Registros: {len(df):,}")

    print()
    print("Perfis:")
    print(
        df.groupby("usage_profile")["device_id"]
        .nunique()
    )

    print()
    print("SoH:")
    print(df["soh_percent"].describe())

    print()
    print(f"Arquivo salvo em:")
    print(output_file)

    print()
    print("Primeiros registros:")

    print(
        df.head(10).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()