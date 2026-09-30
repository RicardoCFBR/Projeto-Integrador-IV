from pathlib import Path

import pandas as pd


# CAMINHOS

project_root = Path(__file__).resolve().parents[2]

input_file = (
    project_root
    / "data"
    / "synthetic"
    / "battery_telemetry_v2.csv"
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
    / "battery_features_v2_1.csv"
)


# CARREGAMENTO

print("PROJETO INTEGRADOR IV")
print("FEATURE ENGINEERING - BATERIA V2.1")

df = pd.read_csv(
    input_file,
    parse_dates=["date"],
)

df = df.sort_values(
    ["device_id", "date"]
).reset_index(drop=True)

print()
print(f"Registros RAW: {len(df):,}")
print(f"Dispositivos: {df['device_id'].nunique()}")


# DESCARGAS PROFUNDAS DIÁRIAS

df["deep_discharge_today"] = (
    df.groupby("device_id")[
        "deep_discharge_count"
    ]
    .diff()
    .fillna(0)
    .clip(lower=0)
)


# INDICADOR DE TEMPERATURA ELEVADA
# Limite experimental da PoC.
# Não representa regra universal de degradação.

df["hot_day"] = (
    df["battery_temperature_c"] >= 35.0
).astype(int)


# JANELA DE 7 DIAS

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

df["temperature_std_7d"] = (
    df.groupby("device_id")[
        "battery_temperature_c"
    ]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=7,
        ).std()
    )
)

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

df["daily_cycles_std_7d"] = (
    df.groupby("device_id")[
        "daily_cycles"
    ]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=7,
        ).std()
    )
)

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


# JANELA DE 30 DIAS

df["temperature_mean_30d"] = (
    df.groupby("device_id")[
        "battery_temperature_c"
    ]
    .transform(
        lambda x: x.rolling(
            window=30,
            min_periods=30,
        ).mean()
    )
)

df["temperature_std_30d"] = (
    df.groupby("device_id")[
        "battery_temperature_c"
    ]
    .transform(
        lambda x: x.rolling(
            window=30,
            min_periods=30,
        ).std()
    )
)

df["hot_days_30d"] = (
    df.groupby("device_id")[
        "hot_day"
    ]
    .transform(
        lambda x: x.rolling(
            window=30,
            min_periods=30,
        ).sum()
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

df["daily_cycles_mean_30d"] = (
    df.groupby("device_id")[
        "daily_cycles"
    ]
    .transform(
        lambda x: x.rolling(
            window=30,
            min_periods=30,
        ).mean()
    )
)

df["daily_cycles_std_30d"] = (
    df.groupby("device_id")[
        "daily_cycles"
    ]
    .transform(
        lambda x: x.rolling(
            window=30,
            min_periods=30,
        ).std()
    )
)

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

df["deep_discharge_rate_30d"] = (
    df["deep_discharge_events_30d"]
    / 30.0
)


# VARIAÇÃO DO CYCLE COUNT
# Quanto o contador de ciclos cresceu nos últimos 30 dias.

df["cycle_count_change_30d"] = (
    df.groupby("device_id")[
        "cycle_count"
    ]
    .diff(30)
)


# IDADE DA OBSERVAÇÃO

df["observation_age_days"] = (
    df["date"]
    - df.groupby("device_id")[
        "date"
    ].transform("min")
).dt.days


# FEATURES DE SOH
# Mantidas para análise futura.
# NÃO entram no treinamento V2.1 inicial.

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


# FEATURES DO EXPERIMENTO V2.1

required_features = [
    "cycle_count",

    "temperature_mean_7d",
    "temperature_max_7d",
    "temperature_std_7d",

    "temperature_mean_30d",
    "temperature_std_30d",
    "hot_days_30d",

    "daily_cycles_mean_7d",
    "daily_cycles_std_7d",

    "daily_cycles_sum_30d",
    "daily_cycles_mean_30d",
    "daily_cycles_std_30d",

    "deep_discharge_events_30d",
    "deep_discharge_rate_30d",

    "cycle_count_change_30d",

    "battery_level_mean_7d",

    "voltage_mean_7d",
    "voltage_std_7d",

    "observation_age_days",
]


# REMOÇÃO DOS REGISTROS SEM HISTÓRICO COMPLETO

records_before = len(df)

processed_df = df.dropna(
    subset=required_features
).copy()

records_after = len(processed_df)

records_removed = (
    records_before
    - records_after
)


# CONTROLE DE COLUNAS INTERNAS

sim_columns = [
    column
    for column in processed_df.columns
    if column.startswith("sim_")
]

print()
print("CONTROLE DOS PARÂMETROS INTERNOS DO SIMULADOR")

if sim_columns:
    print()
    print(
        "Colunas sim_* encontradas "
        "(não utilizar no treinamento):"
    )

    for column in sim_columns:
        print(f" - {column}")


# SALVAR

processed_df.to_csv(
    output_file,
    index=False,
)


# RESUMO

print()
print("FEATURE ENGINEERING V2.1 CONCLUÍDO")

print()
print(
    f"Registros antes: {records_before:,}"
)

print(
    f"Registros depois: {records_after:,}"
)

print(
    f"Registros removidos: {records_removed:,}"
)

print()
print("Features utilizadas no experimento:")

for feature in required_features:
    print(f" - {feature}")


# VALIDAÇÃO

print()
print("VALIDAÇÃO DO DATASET PROCESSADO")

print()
print(
    f"Dispositivos: "
    f"{processed_df['device_id'].nunique()}"
)

print(
    f"Missing nas features: "
    f"{processed_df[required_features].isnull().sum().sum()}"
)

rows_per_device = (
    processed_df
    .groupby("device_id")
    .size()
)

print()
print("Registros por dispositivo:")

print(
    rows_per_device
    .describe()
    .round(2)
    .to_string()
)


# AMOSTRA

sample_columns = [
    "device_id",
    "date",

    "temperature_mean_7d",
    "temperature_std_7d",
    "temperature_mean_30d",
    "hot_days_30d",

    "daily_cycles_mean_7d",
    "daily_cycles_std_7d",
    "daily_cycles_sum_30d",
    "daily_cycles_std_30d",

    "deep_discharge_events_30d",
    "deep_discharge_rate_30d",

    "cycle_count_change_30d",

    "rul_cycles",
]

sample_df = (
    processed_df[
        sample_columns
    ]
    .head(10)
    .copy()
)

numeric_columns = [
    column
    for column in sample_df.columns
    if column not in [
        "device_id",
        "date",
    ]
]

sample_df[
    numeric_columns
] = (
    sample_df[
        numeric_columns
    ]
    .round(3)
)

print()
print("AMOSTRA")

print()
print(
    sample_df.to_string(
        index=False
    )
)


print()
print("Dataset salvo em:")
print(output_file)