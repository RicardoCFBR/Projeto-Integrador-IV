from pathlib import Path

import numpy as np
import pandas as pd

# Reproduces the experimental policy seeded in backend/db/schema.sql, using only the
# development devices of the training split. The thresholds rank devices within the
# synthetic fleet; they are not a replacement rule validated with the operator.

RANDOM_SEED = 42
TRAIN_RATIO = 0.80
HIGH_PERCENTILE = 0.10
MEDIUM_PERCENTILE = 0.33

project_root = Path(__file__).resolve().parents[2]
input_file = project_root / "data" / "processed" / "battery_features_v2_1.csv"

df = pd.read_csv(input_file)

device_ids = np.array(sorted(df["device_id"].unique()))
np.random.default_rng(RANDOM_SEED).shuffle(device_ids)
development_devices = device_ids[: int(len(device_ids) * TRAIN_RATIO)]

rul = df.loc[df["device_id"].isin(development_devices), "rul_cycles"]

print("PROJETO INTEGRADOR IV")
print("CALIBRAÇÃO DA POLÍTICA DE RISCO EXPERIMENTAL")
print()
print(f"Dispositivos de desenvolvimento: {len(development_devices)}")
print(f"Registros: {len(rul):,}")
print(f"RUL mínimo: {rul.min():.2f} ciclos")
print()
print(f"high_below_cycles (p{HIGH_PERCENTILE:.0%}): {rul.quantile(HIGH_PERCENTILE):.0f}")
print(f"medium_below_cycles (p{MEDIUM_PERCENTILE:.0%}): {rul.quantile(MEDIUM_PERCENTILE):.0f}")
