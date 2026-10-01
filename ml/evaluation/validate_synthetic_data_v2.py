from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# CONFIGURAÇÕES

RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


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
    / "ml"
    / "outputs"
    / "v2_validation"
)

output_dir.mkdir(
    parents=True,
    exist_ok=True,
)


# CARREGAMENTO

print("PROJETO INTEGRADOR IV")
print("VALIDAÇÃO DOS DADOS SINTÉTICOS - V2")

df = pd.read_csv(
    input_file,
    parse_dates=["date"],
)

df = df.sort_values(
    ["device_id", "date"]
).reset_index(drop=True)


print()
print(f"Registros: {len(df):,}")
print(f"Dispositivos: {df['device_id'].nunique()}")

print(
    f"Período: "
    f"{df['date'].min().date()} "
    f"até "
    f"{df['date'].max().date()}"
)


# 1. VALIDAÇÃO ESTRUTURAL

print()
print("1. VALIDAÇÃO ESTRUTURAL")

print()
print("Valores ausentes por coluna:")

missing_values = (
    df.isnull()
    .sum()
    .sort_values(
        ascending=False
    )
)

print(
    missing_values.to_string()
)

duplicate_count = df.duplicated(
    subset=[
        "device_id",
        "date",
    ]
).sum()

print()
print(
    f"Registros duplicados "
    f"(device_id + date): "
    f"{duplicate_count}"
)

rows_per_device = (
    df.groupby("device_id")
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


# 2. PERFIS DERIVADOS

print()
print("2. PERFIS DERIVADOS")

profiles = (
    df.groupby(
        "usage_profile"
    )["device_id"]
    .nunique()
    .sort_values(
        ascending=False
    )
)

print()
print(
    profiles.to_string()
)


# 3. PARÂMETROS INDIVIDUAIS

print()
print("3. PARÂMETROS INDIVIDUAIS")

sim_columns = [
    "sim_daily_cycles_mean",
    "sim_base_temperature",
    "sim_deep_discharge_probability",
    "sim_degradation_sensitivity",
    "sim_temperature_sensitivity",
    "sim_calendar_aging_factor",
]

device_parameters = (
    df.groupby(
        "device_id"
    )[sim_columns]
    .first()
)

print()
print(
    device_parameters
    .describe()
    .round(4)
    .to_string()
)


# 4. DISTRIBUIÇÃO DAS VARIÁVEIS PRINCIPAIS

print()
print("4. DISTRIBUIÇÃO DAS VARIÁVEIS PRINCIPAIS")

main_columns = [
    "battery_temperature_c",
    "daily_cycles",
    "cycle_count",
    "deep_discharge_count",
    "soh_percent",
    "rul_cycles",
]

print()
print(
    df[main_columns]
    .describe()
    .round(3)
    .to_string()
)


# 5. ESTADO FINAL DOS DISPOSITIVOS

final_state = (
    df.sort_values(
        "date"
    )
    .groupby(
        "device_id"
    )
    .tail(1)
    .copy()
)

print()
print("5. ESTADO FINAL DOS DISPOSITIVOS")

print()
print("SoH final:")

print(
    final_state[
        "soh_percent"
    ]
    .describe()
    .round(3)
    .to_string()
)

print()
print("RUL final:")

print(
    final_state[
        "rul_cycles"
    ]
    .describe()
    .round(2)
    .to_string()
)


# 6. DISPOSITIVOS COM MENOR SOH FINAL

worst_devices = (
    final_state[
        [
            "device_id",
            "usage_profile",
            "soh_percent",
            "rul_cycles",
            "cycle_count",
            "deep_discharge_count",
            "sim_daily_cycles_mean",
            "sim_base_temperature",
            "sim_degradation_sensitivity",
        ]
    ]
    .sort_values(
        "soh_percent"
    )
    .head(10)
)

print()
print("6. 10 DISPOSITIVOS COM MENOR SOH FINAL")

print()
print(
    worst_devices
    .round(3)
    .to_string(
        index=False
    )
)


# 7. CORRELAÇÕES
# Importante:
# correlação não significa causalidade.
# É apenas uma ferramenta exploratória.

correlation_columns = [
    "battery_temperature_c",
    "daily_cycles",
    "cycle_count",
    "deep_discharge_count",
    "soh_percent",
    "rul_cycles",
]

correlation_matrix = (
    df[correlation_columns]
    .corr()
)

print()
print("7. MATRIZ DE CORRELAÇÃO")

print()
print(
    correlation_matrix
    .round(4)
    .to_string()
)

correlation_file = (
    output_dir
    / "v2_correlation_matrix.csv"
)

correlation_matrix.to_csv(
    correlation_file
)


# 8. AMOSTRA DE DISPOSITIVOS PARA TRAJETÓRIA

all_devices = (
    df["device_id"]
    .drop_duplicates()
    .to_numpy()
)

sample_devices = np.random.choice(
    all_devices,
    size=min(
        8,
        len(all_devices),
    ),
    replace=False,
)

sample_df = df[
    df["device_id"].isin(
        sample_devices
    )
].copy()


# GRÁFICO 1
# TRAJETÓRIAS DE SOH

plt.figure(
    figsize=(12, 7)
)

for device_id in sample_devices:

    device_data = sample_df[
        sample_df[
            "device_id"
        ] == device_id
    ]

    plt.plot(
        device_data["date"],
        device_data["soh_percent"],
        label=device_id,
        linewidth=1.5,
    )

plt.axhline(
    y=70,
    linestyle="--",
    linewidth=1.5,
    label="EOL experimental (70%)",
)

plt.title(
    "Evolução do SoH em dispositivos selecionados - V2"
)

plt.xlabel(
    "Data"
)

plt.ylabel(
    "SoH (%)"
)

plt.legend(
    fontsize=8,
    ncol=2,
)

plt.grid(
    alpha=0.3
)

plt.tight_layout()

soh_devices_file = (
    output_dir
    / "v2_soh_devices.png"
)

plt.savefig(
    soh_devices_file,
    dpi=150,
)

plt.close()


# GRÁFICO 2
# DISTRIBUIÇÃO DO SOH FINAL

plt.figure(
    figsize=(10, 6)
)

plt.hist(
    final_state[
        "soh_percent"
    ],
    bins=25,
)

plt.title(
    "Distribuição do SoH final dos dispositivos - V2"
)

plt.xlabel(
    "SoH final (%)"
)

plt.ylabel(
    "Quantidade de dispositivos"
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

soh_distribution_file = (
    output_dir
    / "v2_soh_distribution.png"
)

plt.savefig(
    soh_distribution_file,
    dpi=150,
)

plt.close()


# GRÁFICO 3
# DISTRIBUIÇÃO DO RUL FINAL

plt.figure(
    figsize=(10, 6)
)

plt.hist(
    final_state[
        "rul_cycles"
    ],
    bins=25,
)

plt.title(
    "Distribuição do RUL final dos dispositivos - V2"
)

plt.xlabel(
    "RUL (ciclos)"
)

plt.ylabel(
    "Quantidade de dispositivos"
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

rul_distribution_file = (
    output_dir
    / "v2_rul_distribution.png"
)

plt.savefig(
    rul_distribution_file,
    dpi=150,
)

plt.close()


# GRÁFICO 4
# DISTRIBUIÇÃO DOS CICLOS MÉDIOS INDIVIDUAIS

plt.figure(
    figsize=(10, 6)
)

plt.hist(
    device_parameters[
        "sim_daily_cycles_mean"
    ],
    bins=25,
)

plt.title(
    "Distribuição da intensidade média de ciclos - V2"
)

plt.xlabel(
    "Ciclos médios por dia"
)

plt.ylabel(
    "Quantidade de dispositivos"
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

cycles_distribution_file = (
    output_dir
    / "v2_cycles_distribution.png"
)

plt.savefig(
    cycles_distribution_file,
    dpi=150,
)

plt.close()


# GRÁFICO 5
# DISTRIBUIÇÃO DA TEMPERATURA-BASE

plt.figure(
    figsize=(10, 6)
)

plt.hist(
    device_parameters[
        "sim_base_temperature"
    ],
    bins=25,
)

plt.title(
    "Distribuição da temperatura-base dos dispositivos - V2"
)

plt.xlabel(
    "Temperatura-base (°C)"
)

plt.ylabel(
    "Quantidade de dispositivos"
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

temperature_distribution_file = (
    output_dir
    / "v2_temperature_distribution.png"
)

plt.savefig(
    temperature_distribution_file,
    dpi=150,
)

plt.close()


# GRÁFICO 6
# CICLOS MÉDIOS × RUL FINAL
# Este é um dos gráficos mais importantes para comparar
# com o comportamento do V1.

device_summary = (
    df.groupby(
        "device_id"
    )
    .agg(
        mean_daily_cycles=(
            "daily_cycles",
            "mean",
        ),
        mean_temperature=(
            "battery_temperature_c",
            "mean",
        ),
        total_deep_discharges=(
            "deep_discharge_count",
            "max",
        ),
        final_soh=(
            "soh_percent",
            "last",
        ),
        final_rul=(
            "rul_cycles",
            "last",
        ),
    )
    .reset_index()
)

plt.figure(
    figsize=(10, 7)
)

plt.scatter(
    device_summary[
        "mean_daily_cycles"
    ],
    device_summary[
        "final_rul"
    ],
    alpha=0.6,
)

plt.title(
    "Ciclos médios diários versus RUL final - V2"
)

plt.xlabel(
    "Ciclos médios por dia"
)

plt.ylabel(
    "RUL final (ciclos)"
)

plt.grid(
    alpha=0.3
)

plt.tight_layout()

cycles_vs_rul_file = (
    output_dir
    / "v2_cycles_vs_rul.png"
)

plt.savefig(
    cycles_vs_rul_file,
    dpi=150,
)

plt.close()


# GRÁFICO 7
# TEMPERATURA MÉDIA × RUL FINAL

plt.figure(
    figsize=(10, 7)
)

plt.scatter(
    device_summary[
        "mean_temperature"
    ],
    device_summary[
        "final_rul"
    ],
    alpha=0.6,
)

plt.title(
    "Temperatura média versus RUL final - V2"
)

plt.xlabel(
    "Temperatura média (°C)"
)

plt.ylabel(
    "RUL final (ciclos)"
)

plt.grid(
    alpha=0.3
)

plt.tight_layout()

temperature_vs_rul_file = (
    output_dir
    / "v2_temperature_vs_rul.png"
)

plt.savefig(
    temperature_vs_rul_file,
    dpi=150,
)

plt.close()


# GRÁFICO 8
# DESCARGAS PROFUNDAS × RUL FINAL

plt.figure(
    figsize=(10, 7)
)

plt.scatter(
    device_summary[
        "total_deep_discharges"
    ],
    device_summary[
        "final_rul"
    ],
    alpha=0.6,
)

plt.title(
    "Descargas profundas versus RUL final - V2"
)

plt.xlabel(
    "Quantidade acumulada de descargas profundas"
)

plt.ylabel(
    "RUL final (ciclos)"
)

plt.grid(
    alpha=0.3
)

plt.tight_layout()

deep_discharge_vs_rul_file = (
    output_dir
    / "v2_deep_discharge_vs_rul.png"
)

plt.savefig(
    deep_discharge_vs_rul_file,
    dpi=150,
)

plt.close()


# GRÁFICO 9
# MATRIZ DE CORRELAÇÃO
# Sem seaborn, para manter dependências simples.

plt.figure(
    figsize=(9, 8)
)

plt.imshow(
    correlation_matrix,
    aspect="auto",
)

plt.colorbar(
    label="Correlação"
)

plt.xticks(
    range(
        len(correlation_columns)
    ),
    correlation_columns,
    rotation=45,
    ha="right",
)

plt.yticks(
    range(
        len(correlation_columns)
    ),
    correlation_columns,
)

for i in range(
    len(correlation_columns)
):
    for j in range(
        len(correlation_columns)
    ):

        value = correlation_matrix.iloc[
            i,
            j
        ]

        plt.text(
            j,
            i,
            f"{value:.2f}",
            ha="center",
            va="center",
        )

plt.title(
    "Matriz de correlação das variáveis - V2"
)

plt.tight_layout()

correlation_chart_file = (
    output_dir
    / "v2_correlation_matrix.png"
)

plt.savefig(
    correlation_chart_file,
    dpi=150,
)

plt.close()


# SALVAR RESUMO POR DISPOSITIVO

device_summary_file = (
    output_dir
    / "v2_device_summary.csv"
)

device_summary.to_csv(
    device_summary_file,
    index=False,
)


# VALIDAÇÕES AUTOMÁTICAS

print()
print("8. VERIFICAÇÕES AUTOMÁTICAS")

checks = {
    "Nenhum valor ausente": (
        df.isnull().sum().sum() == 0
    ),

    "Nenhum device/date duplicado": (
        duplicate_count == 0
    ),

    "400 dispositivos": (
        df["device_id"].nunique()
        == 400
    ),

    "72.000 registros": (
        len(df)
        == 72000
    ),

    "180 registros por dispositivo": (
        rows_per_device.min() == 180
        and rows_per_device.max() == 180
    ),

    "SoH entre 50% e 100%": (
        df["soh_percent"].between(
            50,
            100,
        ).all()
    ),

    "Temperatura entre 22°C e 48°C": (
        df[
            "battery_temperature_c"
        ].between(
            22,
            48,
        ).all()
    ),

    "RUL não negativo": (
        (
            df[
                "rul_cycles"
            ]
            >= 0
        ).all()
    ),
}

print()

for check_name, result in checks.items():

    status = (
        "OK"
        if result
        else "FALHOU"
    )

    print(
        f"[{status}] {check_name}"
    )


# ARQUIVOS GERADOS

print()
print("VALIDAÇÃO V2 CONCLUÍDA")

print()
print("Arquivos gerados:")

generated_files = [
    soh_devices_file,
    soh_distribution_file,
    rul_distribution_file,
    cycles_distribution_file,
    temperature_distribution_file,
    cycles_vs_rul_file,
    temperature_vs_rul_file,
    deep_discharge_vs_rul_file,
    correlation_chart_file,
    correlation_file,
    device_summary_file,
]

for file_path in generated_files:

    print(
        f" - {file_path}"
    )