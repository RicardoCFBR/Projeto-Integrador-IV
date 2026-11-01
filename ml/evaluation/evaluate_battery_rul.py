from pathlib import Path

import numpy as np
import pandas as pd
import sys
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "battery_features_v2_1.csv"
)

sys.path.insert(0, str(PROJECT_ROOT))

from ml.inference.predict_battery import get_model_and_features

RANDOM_SEED = 42
TRAIN_RATIO = 0.80

def load_dataset() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo CSV não encontrado em: {CSV_PATH}"
        )
    df = pd.read_csv(CSV_PATH)

    return df

if __name__ == "__main__":
    df = load_dataset()

    print("========== AVALIAÇÃO DO DATASET ==========")
    print(f"Quantidade total de observações: {len(df)}")
    print(f"Quantidade de dispositivos distintos: {df['device_id'].nunique()}")
    print(f"Quantidade de colunas: {len(df.columns)}")
    print("==========================================")

    device_ids = np.array(sorted(df["device_id"].unique()))

    rng = np.random.default_rng(RANDOM_SEED)
    rng.shuffle(device_ids)

    train_size = int(len(device_ids) * TRAIN_RATIO)
    
    development_devices = device_ids[:train_size]
    test_devices = device_ids[train_size:]

    test_df = df[
        df["device_id"].isin(test_devices)
    ].copy()

    model, feature_names = get_model_and_features()

    print(f"\nModelo: {type(model).__name__}")
    print(f"Features esperadas: {len(feature_names)}")

    X_test = test_df[feature_names].copy()
    y_test = test_df["rul_cycles"].copy()

    print(f"Formato X_test: {X_test.shape}")
    print(f"Formato y_test: {y_test.shape}")
    print(f"Valores ausentes em X_test: {X_test.isna().sum().sum()}")
    print(f"Valores ausentes em y_test: {y_test.isna().sum()}")

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)

    mse = mean_squared_error(y_test, y_pred)

    rmse = np.sqrt(mse)

    r2 = r2_score(y_test, y_pred)

    print("\n========== MÉTRICAS DO MODELO ==========")
    print(f"MAE: {mae:.2f} ciclos")
    print(f"RMSE: {rmse:.2f} ciclos")
    print(f"R²: {r2:.4f}")
    print("=======================================")

    print("\n========== CONJUNTO DE TESTE ==========")
    print(f"Dispositivos de desenvolvimento: {len(development_devices)}")
    print(f"Dispositivos de teste: {len(test_devices)}")
    print(f"Observações de teste: {len(test_df)}")
    print(f"Dispositivos únicos no teste: {test_df['device_id'].nunique()}")
    print(f"DEVICE-0360 pertence ao teste: {'DEVICE-0360' in test_devices}")
    print("=======================================")

