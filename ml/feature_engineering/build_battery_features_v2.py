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
    / "battery_features_v2.csv"
)


# CARREGAMENTO

print("PROJETO INTEGRADOR IV")
print("FEATURE ENGINEERING - BATERIA V2")

df = pd.read_csv(
    input_file,
    parse_dates=["date"],
)

df = df.sort_values(
    ["device_id", "date"]
).reset_index(drop=True)

print()
print(
    f"Registros RAW: {len(df):,}"
)

print(
    f"Dispositivos: "
    f"{df['device_id'].nunique()}"
)


# DESCARGA PROFUNDA DIÁRIA
# deep_discharge_count é acumulativo.
# Calculamos quantos eventos aconteceram em cada dia.

df["deep_discharge_today"] = (
    df.groupby("device_id")[
        "deep_discharge_count"
    ]
    .diff()
    .fillna(0)
    .clip(lower=0)
)


# JANELAS DE 7 DIAS

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


# JANELAS DE 30 DIAS

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


# IDADE DA OBSERVAÇÃO
# Quantidade de dias desde o primeiro registro do dispositivo.

df["observation_age_days"] = (
    df["date"]
    - df.groupby("device_id")[
        "date"
    ].transform("min")
).dt.days


# FEATURES DE SOH
# Criamos essas colunas para análise futura.
# IMPORTANTE:
# elas NÃO serão utilizadas no primeiro treinamento V2,
# para evitar que o modelo receba diretamente informações
# muito próximas da variável-alvo.

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


# FEATURES NECESSÁRIAS PARA O EXPERIMENTO

required_features = [
    "cycle_count",
    "temperature_mean_7d",
    "temperature_max_7d",
    "daily_cycles_mean_7d",
    "daily_cycles_sum_30d",
    "deep_discharge_events_30d",
    "battery_level_mean_7d",
    "voltage_mean_7d",
    "voltage_std_7d",
    "observation_age_days",
]


# REMOÇÃO DE REGISTROS SEM HISTÓRICO COMPLETO
# A maior janela é de 30 dias.
# Portanto, os primeiros 29 registros de cada dispositivo
# não possuem histórico suficiente.

records_before = len(df)

processed_df = df.dropna(
    subset=required_features
).copy()

records_after = len(
    processed_df
)

records_removed = (
    records_before
    - records_after
)


# VERIFICAÇÃO DE COLUNAS SIM_*
# Elas permanecem no dataset apenas para auditoria,
# mas NÃO devem ser usadas como features do modelo.

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
        "Colunas internas encontradas "
        "(não utilizar no treinamento):"
    )

    for column in sim_columns:
        print(
            f" - {column}"
        )

else:
    print()
    print(
        "Nenhuma coluna sim_* encontrada."
    )


# SALVAR

processed_df.to_csv(
    output_file,
    index=False,
)


# RESUMO

print()
print("FEATURE ENGINEERING V2 CONCLUÍDO")

print()
print(
    f"Registros antes: "
    f"{records_before:,}"
)

print(
    f"Registros depois: "
    f"{records_after:,}"
)

print(
    f"Registros removidos pela janela inicial: "
    f"{records_removed:,}"
)

print()

print(
    "Features criadas:"
)

created_features = [
    "temperature_mean_7d",
    "temperature_max_7d",
    "daily_cycles_mean_7d",
    "daily_cycles_sum_30d",
    "deep_discharge_events_30d",
    "battery_level_mean_7d",
    "voltage_mean_7d",
    "voltage_std_7d",
    "observation_age_days",
    "soh_change_7d",
    "soh_change_30d",
]

for feature in created_features:

    print(
        f" - {feature}"
    )


# VALIDAÇÃO FINAL

print()
print("VALIDAÇÃO DO DATASET PROCESSADO")

print()

print(
    f"Dispositivos após processamento: "
    f"{processed_df['device_id'].nunique()}"
)

print(
    f"Valores ausentes nas features utilizadas: "
    f"{processed_df[required_features].isnull().sum().sum()}"
)

rows_per_device = (
    processed_df
    .groupby("device_id")
    .size()
)

print()
print(
    "Registros processados por dispositivo:"
)

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
    "cycle_count",
    "temperature_mean_7d",
    "temperature_max_7d",
    "daily_cycles_mean_7d",
    "daily_cycles_sum_30d",
    "deep_discharge_events_30d",
    "battery_level_mean_7d",
    "voltage_mean_7d",
    "voltage_std_7d",
    "observation_age_days",
    "soh_percent",
    "rul_cycles",
]

print()
print("AMOSTRA")

print()

print(
    processed_df[
        sample_columns
    ]
    .head(10)
    .round(3)
    .to_string(
        index=False
    )
)


# CAMINHO DO ARQUIVO

print()
print(
    "Dataset salvo em:"
)

print(
    output_file
)