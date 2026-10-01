from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# CONFIGURAÇÃO

RANDOM_SEED = 42

NUM_DEVICES = 400
NUM_DAYS = 180

# Critério experimental da PoC.
# Não representa um limite universal para smartphones.

EOL_SOH_PERCENT = 70.0

np.random.seed(RANDOM_SEED)


# FUNÇÕES AUXILIARES

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def classify_usage_profile(daily_cycles_mean, base_temperature):
    """
    Perfil usado apenas para análise e visualização.

    Diferentemente da V1, o perfil NÃO controla diretamente a degradação.
    Ele é derivado dos parâmetros contínuos do dispositivo.
    """

    score = 0

    if daily_cycles_mean >= 0.85:
        score += 1

    if base_temperature >= 34.0:
        score += 1

    if score == 0:
        return "light"

    if score == 1:
        return "normal"

    return "heavy"


def generate_device(device_number: int) -> list[dict]:
    """
    Gera histórico sintético de bateria para um dispositivo.

    V2:
    - parâmetros individuais contínuos;
    - múltiplos fatores de degradação;
    - maior heterogeneidade entre dispositivos;
    - perfis light/normal/heavy apenas derivados para análise.
    """

    device_id = f"DEVICE-{device_number:04d}"

    # PARÂMETROS INDIVIDUAIS DO DISPOSITIVO

    # Capacidade nominal.
    design_capacity = np.random.randint(4000, 5501)

    # Intensidade média de uso: valor contínuo.
    daily_cycles_mean = np.random.uniform(
        0.35,
        1.20,
    )

    # Temperatura operacional média própria do aparelho.
    base_temperature = np.random.uniform(
        29.0,
        37.0,
    )

    # Probabilidade individual de descarga profunda.
    deep_discharge_probability = np.random.uniform(
        0.015,
        0.12,
    )

    # Sensibilidade individual à degradação.
    degradation_sensitivity = np.random.uniform(
        0.80,
        1.25,
    )

    # Sensibilidade térmica individual.
    temperature_sensitivity = np.random.uniform(
        0.85,
        1.20,
    )

    # Pequena diferença de envelhecimento natural entre aparelhos.
    calendar_aging_factor = np.random.uniform(
        0.0008,
        0.0018,
    )

    usage_profile = classify_usage_profile(
        daily_cycles_mean,
        base_temperature,
    )

    # ESTADO INICIAL

    current_soh = np.random.uniform(
        98.5,
        100.0,
    )

    cycle_count = np.random.uniform(
        0,
        80,
    )

    deep_discharge_count = 0

    start_date = datetime(
        2026,
        1,
        1,
    )

    rows = []

    # SIMULAÇÃO DIÁRIA

    for day in range(NUM_DAYS):

        date = start_date + timedelta(
            days=day
        )

        # VARIAÇÃO DE USO DIÁRIO

        daily_cycles = np.random.normal(
            daily_cycles_mean,
            0.18,
        )

        daily_cycles = clamp(
            daily_cycles,
            0.05,
            1.60,
        )

        cycle_count += daily_cycles

        # TEMPERATURA
        # A temperatura varia em torno de uma média própria
        # e recebe influência do uso diário.

        temperature = (
            np.random.normal(
                base_temperature,
                2.2,
            )
            + (daily_cycles - 0.70) * 1.8
        )

        temperature = clamp(
            temperature,
            22.0,
            48.0,
        )

        # DESCARGA PROFUNDA

        deep_discharge = (
            np.random.random()
            < deep_discharge_probability
        )

        if deep_discharge:
            deep_discharge_count += 1

        # COMPONENTE 1: DESGASTE POR CICLOS
        # Mais ciclos => maior desgaste.

        cycle_degradation = (
            daily_cycles
            * 0.018
            * degradation_sensitivity
        )

        # COMPONENTE 2: ESTRESSE TÉRMICO
        # Só cresce de forma relevante acima de 33 °C.

        if temperature <= 33.0:
            thermal_degradation = 0.0

        else:
            thermal_degradation = (
                (temperature - 33.0)
                * 0.0025
                * temperature_sensitivity
            )

        # COMPONENTE 3: DESCARGA PROFUNDA

        deep_discharge_degradation = (
            0.015
            * degradation_sensitivity
            if deep_discharge
            else 0.0
        )

        # COMPONENTE 4: ENVELHECIMENTO CALENDÁRIO
        # Pequeno desgaste diário mesmo com pouco uso.

        calendar_degradation = (
            calendar_aging_factor
        )

        # COMPONENTE 5: RUÍDO
        # Evita trajetórias excessivamente determinísticas.

        random_noise = np.random.normal(
            0.0,
            0.0025,
        )

        # DEGRADAÇÃO TOTAL DO DIA

        soh_loss = (
            cycle_degradation
            + thermal_degradation
            + deep_discharge_degradation
            + calendar_degradation
            + random_noise
        )

        # Impede crescimento artificial do SoH por ruído negativo.
        soh_loss = max(
            soh_loss,
            0.0001,
        )

        current_soh -= soh_loss

        current_soh = max(
            current_soh,
            50.0,
        )

        # CAPACIDADE ATUAL

        current_capacity = (
            design_capacity
            * current_soh
            / 100.0
        )

        # NÍVEL DE BATERIA
        # Continua sendo uma leitura de momento, não indicador
        # de saúde.

        battery_level = np.random.randint(
            15,
            101,
        )

        # TENSÃO
        # Pequena influência do nível instantâneo da bateria.

        voltage_mv = (
            3500
            + battery_level * 7
            + np.random.normal(
                0,
                85,
            )
        )

        voltage_mv = int(
            clamp(
                voltage_mv,
                3300,
                4400,
            )
        )

        # RUL SINTÉTICO
        # Na V2, estimamos o RUL usando uma taxa de degradação
        # esperada construída a partir dos parâmetros internos
        # do dispositivo.
        # Essa taxa NÃO será fornecida ao modelo de ML.

        expected_daily_cycles = (
            daily_cycles_mean
        )

        expected_cycle_degradation = (
            expected_daily_cycles
            * 0.018
            * degradation_sensitivity
        )

        expected_temperature_excess = max(
            0.0,
            base_temperature - 33.0,
        )

        expected_thermal_degradation = (
            expected_temperature_excess
            * 0.0025
            * temperature_sensitivity
        )

        expected_deep_discharge_degradation = (
            deep_discharge_probability
            * 0.015
            * degradation_sensitivity
        )

        expected_daily_soh_loss = (
            expected_cycle_degradation
            + expected_thermal_degradation
            + expected_deep_discharge_degradation
            + calendar_aging_factor
        )

        remaining_soh = max(
            0.0,
            current_soh - EOL_SOH_PERCENT,
        )

        # Dias restantes estimados até EOL.
        if expected_daily_soh_loss > 0:
            rul_days = (
                remaining_soh
                / expected_daily_soh_loss
            )
        else:
            rul_days = 0.0

        # Conversão aproximada para ciclos.
        rul_cycles = (
            rul_days
            * expected_daily_cycles
        )

        # REGISTRO

        rows.append(
            {
                "device_id": device_id,
                "date": date.date(),

                # Perfil mantido apenas para análise.
                "usage_profile": usage_profile,

                # Telemetria observável.
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

                # Parâmetros internos do simulador.
                # Estes campos são úteis para auditoria da geração,
                # mas NÃO devem ser usados como features do modelo.
                "sim_daily_cycles_mean": round(
                    daily_cycles_mean,
                    4,
                ),
                "sim_base_temperature": round(
                    base_temperature,
                    4,
                ),
                "sim_deep_discharge_probability": round(
                    deep_discharge_probability,
                    5,
                ),
                "sim_degradation_sensitivity": round(
                    degradation_sensitivity,
                    5,
                ),
                "sim_temperature_sensitivity": round(
                    temperature_sensitivity,
                    5,
                ),
                "sim_calendar_aging_factor": round(
                    calendar_aging_factor,
                    6,
                ),
            }
        )

    return rows


# EXECUÇÃO

def main():

    print("=" * 60)
    print("PROJETO INTEGRADOR IV")
    print("GERADOR DE TELEMETRIA SINTÉTICA - V2")
    print("=" * 60)

    print()
    print(
        f"Gerando {NUM_DEVICES} dispositivos..."
    )

    print(
        f"Histórico: {NUM_DAYS} dias"
    )

    all_rows = []

    for device_number in range(
        1,
        NUM_DEVICES + 1,
    ):

        device_rows = generate_device(
            device_number
        )

        all_rows.extend(
            device_rows
        )

    df = pd.DataFrame(
        all_rows
    )

    # CAMINHO DE SAÍDA

    project_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

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
        / "battery_telemetry_v2.csv"
    )

    df.to_csv(
        output_file,
        index=False,
    )

    # RESUMO

    print()
    print("=" * 60)
    print("SIMULAÇÃO V2 CONCLUÍDA")
    print("=" * 60)

    print(
        f"Dispositivos: "
        f"{df['device_id'].nunique()}"
    )

    print(
        f"Registros: "
        f"{len(df):,}"
    )

    print()
    print("Perfis derivados:")

    print(
        df.groupby(
            "usage_profile"
        )["device_id"]
        .nunique()
    )

    print()
    print(
        "Resumo dos parâmetros individuais:"
    )

    parameters = [
        "sim_daily_cycles_mean",
        "sim_base_temperature",
        "sim_deep_discharge_probability",
        "sim_degradation_sensitivity",
        "sim_temperature_sensitivity",
        "sim_calendar_aging_factor",
    ]

    print(
        df.groupby(
            "device_id"
        )[parameters]
        .first()
        .describe()
        .round(4)
    )

    print()
    print("SoH:")

    print(
        df["soh_percent"]
        .describe()
        .round(3)
    )

    print()
    print("RUL:")

    print(
        df["rul_cycles"]
        .describe()
        .round(2)
    )

    print()
    print(
        "Arquivo salvo em:"
    )

    print(
        output_file
    )

    print()
    print(
        "Primeiros registros:"
    )

    columns_to_show = [
        "device_id",
        "date",
        "usage_profile",
        "battery_temperature_c",
        "daily_cycles",
        "cycle_count",
        "deep_discharge_count",
        "soh_percent",
        "rul_cycles",
    ]

    print(
        df[columns_to_show]
        .head(10)
        .to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()