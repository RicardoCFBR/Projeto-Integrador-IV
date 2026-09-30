from pathlib import Path

import numpy as np
import pandas as pd


# CAMINHOS

project_root = Path(__file__).resolve().parents[2]

input_file = (
    project_root
    / "data"
    / "synthetic"
    / "battery_telemetry.csv"
)

output_dir = (
    project_root
    / "data"
    / "processed"
)

output_dir.mkdir(
    parents=True,
    exist_ok=True,
)

output_file = (
    output_dir
    / "battery_features.csv"
)


# CARREGAMENTO

print("FEATURE ENGINEERING - BATERIA")

df = pd.read_csv(
    input_file,
    parse_dates=["date"],
)

print()
print(f"Registros RAW: {len(df):,}")
print(f"Dispositivos: {df['device_id'].nunique()}")


# ORDENAÇÃO TEMPORAL

df = df.sort_values(
    ["device_id", "date"]
).reset_index(drop=True)


# DESCARGAS PROFUNDAS DO DIA

# deep_discharge_count é acumulativo.
# Portanto precisamos descobrir quantos eventos ocorreram
# especificamente em cada dia.

df["deep_discharge_today"] = (
    df.groupby("device_id")[
        "deep_discharge_count"
    ]
    .diff()
    .fillna(0)
    .clip(lower=0)
)


# TEMPERATURA - JANELA DE 7 DIAS

df["temperature_mean_7d"] = (
    df.groupby("device_id")[
        "battery_temperature_c"
    ]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=7,
        ).mean()
    )
)

df["temperature_max_7d"] = (
    df.groupby("device_id")[
        "battery_temperature_c"
    ]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=7,
        ).max()
    )
)


# CICLOS

df["daily_cycles_mean_7d"] = (
    df.groupby("device_id")[
        "daily_cycles"
    ]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=7,
        ).mean()
    )
)

df["daily_cycles_sum_30d"] = (
    df.groupby("device_id")[
        "daily_cycles"
    ]
    .transform(
        lambda x: x.rolling(
            window=30,
            min_periods=30,
        ).sum()
    )
)


# DESCARGAS PROFUNDAS - 30 DIAS

df["deep_discharge_events_30d"] = (
    df.groupby("device_id")[
        "deep_discharge_today"
    ]
    .transform(
        lambda x: x.rolling(
            window=30,
            min_periods=30,
        ).sum()
    )
)


# NÍVEL DA BATERIA - 7 DIAS

df["battery_level_mean_7d"] = (
    df.groupby("device_id")[
        "battery_level_pct"
    ]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=7,
        ).mean()
    )
)


# VOLTAGEM - 7 DIAS

df["voltage_mean_7d"] = (
    df.groupby("device_id")[
        "voltage_mv"
    ]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=7,
        ).mean()
    )
)

df["voltage_std_7d"] = (
    df.groupby("device_id")[
        "voltage_mv"
    ]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=7,
        ).std()
    )
)


# IDADE DA OBSERVAÇÃO

first_date = (
    df.groupby("device_id")["date"]
    .transform("min")
)

df["observation_age_days"] = (
    df["date"] - first_date
).dt.days


# FEATURES BASEADAS EM SoH
#
# Não entram no primeiro modelo.
# São mantidas para um experimento posterior.

df["soh_change_7d"] = (
    df.groupby("device_id")[
        "soh_percent"
    ]
    .diff(7)
)

df["soh_change_30d"] = (
    df.groupby("device_id")[
        "soh_percent"
    ]
    .diff(30)
)


# REMOVER PERÍODO SEM HISTÓRICO SUFICIENTE

required_features = [
    "temperature_mean_7d",
    "temperature_max_7d",
    "daily_cycles_mean_7d",
    "daily_cycles_sum_30d",
    "deep_discharge_events_30d",
    "battery_level_mean_7d",
    "voltage_mean_7d",
    "voltage_std_7d",
]

before = len(df)

df = df.dropna(
    subset=required_features
).copy()

after = len(df)


# SALVAR

df.to_csv(
    output_file,
    index=False,
)


# RESUMO

print()
print("FEATURE ENGINEERING CONCLUÍDO")

print()
print(f"Registros antes: {before:,}")
print(f"Registros depois: {after:,}")
print(
    f"Registros removidos pela janela inicial: "
    f"{before - after:,}"
)

print()
print("Features criadas:")

for feature in required_features:
    print(f" - {feature}")

print()
print(f"Dataset salvo em:")
print(output_file)

print()
print("Amostra:")

columns_to_show = [
    "device_id",
    "date",
    "cycle_count",
    "temperature_mean_7d",
    "temperature_max_7d",
    "daily_cycles_mean_7d",
    "daily_cycles_sum_30d",
    "deep_discharge_events_30d",
    "soh_percent",
    "rul_cycles",
]

print(
    df[columns_to_show]
    .head(10)
    .to_string(index=False)
)