from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import joblib
import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent  # ml/inference
ML_DIR = CURRENT_DIR.parent  # ml
PROJECT_ROOT = ML_DIR.parent  # Projeto-Integrador-IV

MODEL_PATH = (
    ML_DIR
    / "artifacts"
    / "v2_2_tuned"
    / "battery_rul_random_forest_v2_2_tuned.joblib"
)
METADATA_PATH = (
    ML_DIR
    / "artifacts"
    / "v2_2_tuned"
    / "battery_rul_random_forest_v2_2_tuned_metadata.json"
)
FEATURES_CSV_PATH = (
    PROJECT_ROOT / "data" / "processed" / "battery_features_v2_1.csv"
)


@lru_cache(maxsize=1)
def get_model_and_features() -> Tuple[Any, List[str]]:
    """Carrega o modelo e a lista de features sob demanda (uma única vez por processo)

    e garante que o modelo .joblib e o arquivo de metadados JSON estão sincronizados.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Modelo não encontrado em: {MODEL_PATH}")

    loaded_model = joblib.load(MODEL_PATH)

    model_features: List[str] | None = None
    if hasattr(loaded_model, "feature_names_in_"):
        model_features = [str(f) for f in loaded_model.feature_names_in_]

    meta_features: List[str] | None = None
    if METADATA_PATH.exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
            if "features" in meta and isinstance(meta["features"], list):
                meta_features = [str(f) for f in meta["features"]]

    if model_features is not None and meta_features is not None:
        if model_features != meta_features:
            raise ValueError(
                "Inconsistência crítica: as features do modelo (.joblib) não correspondem "
                f"exatamente às features do metadata (.json).\n"
                f"Modelo: {model_features}\nMetadata: {meta_features}"
            )

    features = model_features if model_features is not None else meta_features
    if not features:
        raise RuntimeError(
            "Não foi possível recuperar a lista de features do modelo nem do metadata."
        )

    return loaded_model, features


def validate_and_prepare_input(
    data: Union[pd.DataFrame, Dict[str, Any], List[float]],
    feature_names: List[str],
) -> pd.DataFrame:
    """Valida se a entrada contém exatamente 1 observação, todas as 17 features

    e apenas valores numéricos finitos (sem NaN ou infinito).
    """
    if isinstance(data, dict):
        df_input = pd.DataFrame([data])
    elif isinstance(data, list):
        if len(data) != len(feature_names):
            raise ValueError(
                f"A lista de entrada possui {len(data)} elementos, "
                f"mas o modelo espera {len(feature_names)} features."
            )
        df_input = pd.DataFrame([data], columns=feature_names)
    elif isinstance(data, pd.DataFrame):
        df_input = data.copy()
    else:
        raise TypeError(
            "Entrada inválida. Envie um dict, list ou pandas.DataFrame."
        )

    if len(df_input) != 1:
        raise ValueError(
            f"A função espera exatamente 1 observação para inferência, "
            f"mas recebeu {len(df_input)} linhas."
        )

    missing_cols = [
        col for col in feature_names if col not in df_input.columns
    ]
    if missing_cols:
        raise ValueError(
            f"Faltam features obrigatórias na entrada: {missing_cols}"
        )

    X = df_input[feature_names].copy()

    for col in feature_names:
        try:
            X[col] = pd.to_numeric(X[col], errors="raise")
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"A feature '{col}' contém um valor não numérico: {X[col].values[0]!r}"
            ) from exc

    values_matrix = X.to_numpy(dtype=float)
    if not np.isfinite(values_matrix).all():
        invalid_cols = [
            col
            for col in feature_names
            if not np.isfinite(float(X[col].iloc[0]))
        ]
        raise ValueError(
            f"As seguintes features contêm valores ausentes (NaN) ou infinitos: {invalid_cols}"
        )

    return X


def predict_rul(data: Union[pd.DataFrame, Dict[str, Any], List[float]]) -> float:
    """Carrega modelo/features (via cache), valida a entrada, executa a inferência

    e valida se a saída é um número finito.
    """
    loaded_model, feature_names = get_model_and_features()
    X = validate_and_prepare_input(data, feature_names)
    predictions = loaded_model.predict(X)

    if predictions is None or len(predictions) != 1:
        raise RuntimeError(
            f"Saída inesperada do modelo: esperava 1 predição, recebeu "
            f"{len(predictions) if predictions is not None else 0}."
        )

    try:
        rul_value = float(predictions[0])
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            f"O modelo retornou um valor não numérico: {predictions[0]!r}"
        ) from exc

    if not np.isfinite(rul_value):
        raise RuntimeError(
            f"O modelo produziu uma predição inválida (NaN ou infinito): {rul_value}"
        )

    return rul_value


if __name__ == "__main__":
    model_obj, features_list = get_model_and_features()
    print("Carregamento do modelo:")
    print(type(model_obj).__name__)
    print("\nQuantidade de features esperadas:")
    print(len(features_list))
    print("\nStatus:")
    print("Modelo e metadados validados com sucesso!")

    if FEATURES_CSV_PATH.exists():
        df_sample = pd.read_csv(FEATURES_CSV_PATH)
        first_row = df_sample.iloc[[0]]

        device_ids = np.array(sorted(df_sample["device_id"].unique()))

        rng = np.random.default_rng(42)
        rng.shuffle(device_ids)

        train_size = int(len(device_ids) * 0.80)

        development_devices = device_ids[:train_size]
        test_devices = device_ids[train_size:]

        test_device_id = test_devices[0]

        print(f"\nDispositivo escolhido para teste: {test_device_id}")

        test_device_df = df_sample[
                df_sample["device_id"] == test_device_id
        ]
        test_row = test_device_df.iloc[[0]]

        # Executar a previsão para o dispositivo de teste
        test_rul_predito = predict_rul(test_row)
        
        test_rul_sintetico = float(test_row["rul_cycles"].iloc[0])
        
        test_erro_absoluto = abs(test_rul_sintetico - test_rul_predito)

        print("\n========== DISPOSITIVO DE TESTE ==========")
        print(f"Dispositivo: {test_device_id}")
        print(f"Data da observação: {test_row['date'].iloc[0]}")
        print(f"RUL sintético: {test_rul_sintetico:.2f} ciclos")
        print(f"RUL previsto: {test_rul_predito:.2f} ciclos")
        print(f"Erro absoluto: {test_erro_absoluto:.2f} ciclos")
        print("==========================================")

        device_id = first_row["device_id"].iloc[0]
        observation_date = first_row["date"].iloc[0]

        if device_id in development_devices:
            print(f"\n{device_id}: CONJUNTO DE DESENVOLVIMENTO")
        elif device_id in test_devices:
            print(f"\n{device_id}: CONJUNTO DE TESTE")
        else:
            raise ValueError(f"Dispositivo não identificado: {device_id}")

        print(f"Total de dispositivos: {len(device_ids)}")
        print(f"Dispositivos de desenvolvimento: {len(development_devices)}")
        print(f"Dispositivos de teste: {len(test_devices)}")

        print("\nColunas disponíveis no CSV:")
        print(df_sample.columns.tolist())
        
        rul = predict_rul(first_row)
        rul_sintetico = float(first_row["rul_cycles"].iloc[0])
        erro_absoluto = abs(rul_sintetico - rul)

        print(f"\nPredição de teste (linha 0 do CSV): RUL = {rul:.2f}")
        print("\n========== RESULTADO DA INFERÊNCIA ==========")
        print(f"Dispositivo: {device_id}")
        print(f"Data da observação: {observation_date}")
        print(f"RUL sintético: {rul_sintetico:.2f} ciclos")
        print(f"RUL previsto: {rul:.2f} ciclos")
        print(f"Erro absoluto: {erro_absoluto:.2f} ciclos")
        print("============================================")

        print("\nTestando travas de validação (Ajuste A):")
        try:
            bad_row = first_row.drop(columns=[features_list[0]])
            predict_rul(bad_row)
            raise AssertionError("FALHA: Deveria ter rejeitado coluna faltante")
        except ValueError as e:
            print(f"  [OK] Coluna faltante detectada -> {e}")

        try:
            nan_row = first_row.copy()
            nan_row[features_list[0]] = np.nan
            predict_rul(nan_row)
            raise AssertionError("FALHA: Deveria ter rejeitado valor NaN")
        except ValueError as e:
            print(f"  [OK] Valor NaN detectado -> {e}")

        try:
            predict_rul(df_sample.iloc[0:2])
            raise AssertionError(
                "FALHA: Deveria ter rejeitado múltiplas linhas"
            )
        except ValueError as e:
            print(f"  [OK] Múltiplas linhas bloqueadas -> {e}")
    else:
        print(f"\nCSV de teste não encontrado em: {FEATURES_CSV_PATH}")