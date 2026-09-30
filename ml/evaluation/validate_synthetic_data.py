from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# CAMINHOS

project_root = Path(__file__).resolve().parents[2]

data_file = (
    project_root
    / "data"
    / "synthetic"
    / "battery_telemetry.csv"
)

output_dir = (
    project_root
    / "ml"
    / "outputs"
)

output_dir.mkdir(
    parents=True,
    exist_ok=True,
)


# CARREGAR DATASET

df = pd.read_csv(
    data_file,
    parse_dates=["date"],
)

print("VALIDAÇÃO DO DATASET SINTÉTICO")

print()
print(f"Registros: {len(df):,}")
print(f"Dispositivos: {df['device_id'].nunique()}")

print()
print("Perfis:")
print(
    df.groupby("usage_profile")["device_id"]
    .nunique()
)

print()
print("Valores ausentes:")
print(df.isnull().sum())


# 1. GRÁFICO DE SoH DE ALGUNS DISPOSITIVOS

selected_devices = [
    "DEVICE-0001",
    "DEVICE-0100",
    "DEVICE-0300",
]

plt.figure(figsize=(10, 6))

for device_id in selected_devices:

    device_df = df[
        df["device_id"] == device_id
    ]

    plt.plot(
        device_df["date"],
        device_df["soh_percent"],
        label=device_id,
    )


plt.axhline(
    y=70,
    linestyle="--",
    label="EOL experimental (70%)",
)

plt.title("Evolução do SoH por dispositivo")
plt.xlabel("Data")
plt.ylabel("SoH (%)")
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()

plt.savefig(
    output_dir / "soh_devices.png",
    dpi=150,
)

plt.show()


# 2. SoH MÉDIO POR PERFIL

profile_daily = (
    df.groupby(
        ["date", "usage_profile"]
    )["soh_percent"]
    .mean()
    .reset_index()
)

plt.figure(figsize=(10, 6))

for profile in [
    "light",
    "normal",
    "heavy",
]:

    profile_df = profile_daily[
        profile_daily["usage_profile"] == profile
    ]

    plt.plot(
        profile_df["date"],
        profile_df["soh_percent"],
        label=profile,
    )


plt.axhline(
    y=70,
    linestyle="--",
    label="EOL experimental (70%)",
)

plt.title("SoH médio por perfil de utilização")
plt.xlabel("Data")
plt.ylabel("SoH médio (%)")
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()

plt.savefig(
    output_dir / "soh_profiles.png",
    dpi=150,
)

plt.show()


# 3. TEMPERATURA MÉDIA POR PERFIL

temperature_by_profile = (
    df.groupby("usage_profile")[
        "battery_temperature_c"
    ]
    .mean()
    .sort_values()
)

print()
print("Temperatura média por perfil:")
print(temperature_by_profile)

plt.figure(figsize=(8, 5))

temperature_by_profile.plot(
    kind="bar",
)

plt.title("Temperatura média por perfil")
plt.xlabel("Perfil")
plt.ylabel("Temperatura média (°C)")
plt.xticks(rotation=0)

plt.tight_layout()

plt.savefig(
    output_dir / "temperature_profiles.png",
    dpi=150,
)

plt.show()


# 4. SoH FINAL POR PERFIL

final_records = (
    df.sort_values("date")
    .groupby("device_id")
    .tail(1)
)

final_soh = (
    final_records
    .groupby("usage_profile")[
        "soh_percent"
    ]
    .mean()
    .sort_values(ascending=False)
)

print()
print("SoH médio ao final dos 180 dias:")
print(final_soh)

plt.figure(figsize=(8, 5))

final_soh.plot(
    kind="bar",
)

plt.title("SoH médio final por perfil")
plt.xlabel("Perfil")
plt.ylabel("SoH médio (%)")
plt.xticks(rotation=0)

plt.tight_layout()

plt.savefig(
    output_dir / "final_soh_profiles.png",
    dpi=150,
)

plt.show()


# 5. RESUMO FINAL

print()
print("RESUMO DOS DISPOSITIVOS NO DIA FINAL")

print(
    final_records[
        [
            "device_id",
            "usage_profile",
            "cycle_count",
            "battery_temperature_c",
            "soh_percent",
            "rul_cycles",
        ]
    ]
    .sort_values("soh_percent")
    .head(20)
    .to_string(index=False)
)