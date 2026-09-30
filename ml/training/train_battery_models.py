from pathlib import Path
import json

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# CONFIGURAÇÕES

RANDOM_SEED = 42
TRAIN_RATIO = 0.80

"""
IMPORTANTE:
 Essas são as features do Experimento A.

 Não incluímos:
 - soh_percent
 - battery_current_capacity_mah
 - battery_design_capacity_mah
 - usage_profile

 O objetivo é reduzir o risco de data leakage e avaliar
 inicialmente o quanto a telemetria operacional consegue
 explicar o RUL sintético.
"""

FEATURES = [
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

TARGET = "rul_cycles"


# CAMINHOS

project_root = Path(__file__).resolve().parents[2]

input_file = (
    project_root
    / "data"
    / "processed"
    / "battery_features.csv"
)

artifacts_dir = (
    project_root
    / "ml"
    / "artifacts"
)

outputs_dir = (
    project_root
    / "ml"
    / "outputs"
)

artifacts_dir.mkdir(
    parents=True,
    exist_ok=True,
)

outputs_dir.mkdir(
    parents=True,
    exist_ok=True,
)


# CARREGAMENTO DOS DADOS

print("PROJETO INTEGRADOR IV")
print("TREINAMENTO INICIAL - PREDIÇÃO DE RUL")

df = pd.read_csv(
    input_file,
    parse_dates=["date"],
)

print()
print(f"Registros carregados: {len(df):,}")
print(f"Dispositivos: {df['device_id'].nunique()}")


# VALIDAÇÃO DAS COLUNAS

required_columns = (
    ["device_id", "date", TARGET]
    + FEATURES
)

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        "As seguintes colunas estão ausentes no dataset: "
        + ", ".join(missing_columns)
    )


# VALIDAÇÃO DE VALORES AUSENTES

missing_values = (
    df[FEATURES + [TARGET]]
    .isnull()
    .sum()
)

if missing_values.sum() > 0:
    print()
    print("ATENÇÃO: valores ausentes encontrados:")
    print(
        missing_values[
            missing_values > 0
        ]
    )

    df = df.dropna(
        subset=FEATURES + [TARGET]
    ).copy()


# SEPARAÇÃO DOS DISPOSITIVOS

device_ids = np.array(
    sorted(
        df["device_id"]
        .unique()
    )
)

rng = np.random.default_rng(
    RANDOM_SEED
)

rng.shuffle(device_ids)

train_size = int(
    len(device_ids)
    * TRAIN_RATIO
)

train_devices = device_ids[
    :train_size
]

test_devices = device_ids[
    train_size:
]

train_df = df[
    df["device_id"].isin(
        train_devices
    )
].copy()

test_df = df[
    df["device_id"].isin(
        test_devices
    )
].copy()


# VERIFICAÇÃO CONTRA LEAKAGE ENTRE DISPOSITIVOS

overlap = (
    set(train_devices)
    .intersection(
        set(test_devices)
    )
)

if overlap:
    raise RuntimeError(
        "Erro: existem dispositivos simultaneamente "
        "no treino e no teste."
    )


print()

print("DIVISÃO DOS DADOS")

print(
    f"Dispositivos de treino: "
    f"{len(train_devices)}"
)

print(
    f"Dispositivos de teste: "
    f"{len(test_devices)}"
)

print(
    f"Registros de treino: "
    f"{len(train_df):,}"
)

print(
    f"Registros de teste: "
    f"{len(test_df):,}"
)


# MATRIZES X E y

X_train = train_df[
    FEATURES
].copy()

y_train = train_df[
    TARGET
].copy()

X_test = test_df[
    FEATURES
].copy()

y_test = test_df[
    TARGET
].copy()


print()
print("Features utilizadas:")

for feature in FEATURES:
    print(
        f" - {feature}"
    )

print()
print(
    f"Variável alvo: {TARGET}"
)


# FUNÇÃO DE AVALIAÇÃO

def evaluate_model(
    model_name,
    model,
    X_train,
    y_train,
    X_test,
    y_test,
):
    """
    Treina o modelo e retorna métricas
    sobre o conjunto de teste.
    """

    print()
    print("-" * 60)
    print(
        f"Treinando: {model_name}"
    )
    print("-" * 60)

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_test
    )

    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    mse = mean_squared_error(
        y_test,
        predictions,
    )

    rmse = np.sqrt(
        mse
    )

    r2 = r2_score(
        y_test,
        predictions,
    )

    print(
        f"MAE  : {mae:.4f} ciclos"
    )

    print(
        f"RMSE : {rmse:.4f} ciclos"
    )

    print(
        f"R²   : {r2:.6f}"
    )

    return {
        "model_name": model_name,
        "model": model,
        "predictions": predictions,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }


# 1. BASELINE - DUMMY REGRESSOR

dummy_model = DummyRegressor(
    strategy="mean"
)

dummy_result = evaluate_model(
    model_name="DummyRegressor",
    model=dummy_model,
    X_train=X_train,
    y_train=y_train,
    X_test=X_test,
    y_test=y_test,
)


# 2. REGRESSÃO LINEAR

linear_model = LinearRegression()

linear_result = evaluate_model(
    model_name="LinearRegression",
    model=linear_model,
    X_train=X_train,
    y_train=y_train,
    X_test=X_test,
    y_test=y_test,
)


# 3. RANDOM FOREST

random_forest_model = (
    RandomForestRegressor(
        n_estimators=200,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
)

random_forest_result = evaluate_model(
    model_name="RandomForestRegressor",
    model=random_forest_model,
    X_train=X_train,
    y_train=y_train,
    X_test=X_test,
    y_test=y_test,
)


# RESULTADOS

results = [
    dummy_result,
    linear_result,
    random_forest_result,
]

metrics_df = pd.DataFrame(
    [
        {
            "model": result[
                "model_name"
            ],
            "mae_cycles": round(
                result["mae"],
                6,
            ),
            "rmse_cycles": round(
                result["rmse"],
                6,
            ),
            "r2": round(
                result["r2"],
                6,
            ),
        }
        for result in results
    ]
)

print()
print("COMPARAÇÃO DOS MODELOS")

print(
    metrics_df.to_string(
        index=False
    )
)


# SALVAR MÉTRICAS

metrics_file = (
    outputs_dir
    / "battery_model_metrics.csv"
)

metrics_df.to_csv(
    metrics_file,
    index=False,
)


# ESCOLHA DO MELHOR MODELO

best_result = min(
    results,
    key=lambda result: result["mae"],
)

best_model = best_result[
    "model"
]

best_model_name = best_result[
    "model_name"
]


print()
print("MELHOR MODELO DA PRIMEIRA RODADA")

print(
    f"Modelo: {best_model_name}"
)

print(
    f"MAE: {best_result['mae']:.4f} ciclos"
)

print(
    f"RMSE: {best_result['rmse']:.4f} ciclos"
)

print(
    f"R²: {best_result['r2']:.6f}"
)


# SALVAR RANDOM FOREST

rf_model_file = (
    artifacts_dir
    / "battery_rul_random_forest.joblib"
)

joblib.dump(
    random_forest_result[
        "model"
    ],
    rf_model_file,
)


# SALVAR METADADOS DO MODELO

metadata = {
    "model_name": (
        "RandomForestRegressor"
    ),
    "target": TARGET,
    "features": FEATURES,
    "random_seed": RANDOM_SEED,
    "train_devices": int(
        len(train_devices)
    ),
    "test_devices": int(
        len(test_devices)
    ),
    "train_rows": int(
        len(train_df)
    ),
    "test_rows": int(
        len(test_df)
    ),
    "metrics": {
        "mae_cycles": float(
            random_forest_result[
                "mae"
            ]
        ),
        "rmse_cycles": float(
            random_forest_result[
                "rmse"
            ]
        ),
        "r2": float(
            random_forest_result[
                "r2"
            ]
        ),
    },
}

metadata_file = (
    artifacts_dir
    / "battery_rul_random_forest_metadata.json"
)

with open(
    metadata_file,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        metadata,
        file,
        ensure_ascii=False,
        indent=4,
    )


# PREDIÇÕES DO RANDOM FOREST

prediction_df = test_df[
    [
        "device_id",
        "date",
        TARGET,
    ]
].copy()

prediction_df[
    "predicted_rul_cycles"
] = random_forest_result[
    "predictions"
]

prediction_df[
    "absolute_error_cycles"
] = np.abs(
    prediction_df[TARGET]
    - prediction_df[
        "predicted_rul_cycles"
    ]
)

predictions_file = (
    outputs_dir
    / "battery_test_predictions.csv"
)

prediction_df.to_csv(
    predictions_file,
    index=False,
)


# AMOSTRA DAS PREDIÇÕES

print()
print("AMOSTRA DE PREDIÇÕES")

sample_predictions = (
    prediction_df
    .sample(
        n=min(
            15,
            len(prediction_df),
        ),
        random_state=RANDOM_SEED,
    )
    .sort_values(
        "device_id"
    )
)

print(
    sample_predictions
    .round(2)
    .to_string(
        index=False
    )
)


# FEATURE IMPORTANCE - RANDOM FOREST

feature_importance_df = (
    pd.DataFrame(
        {
            "feature": FEATURES,
            "importance": (
                random_forest_result[
                    "model"
                ]
                .feature_importances_
            ),
        }
    )
    .sort_values(
        "importance",
        ascending=False,
    )
)

print()
print("IMPORTÂNCIA DAS FEATURES - RANDOM FOREST")

print(
    feature_importance_df
    .to_string(
        index=False
    )
)

feature_importance_file = (
    outputs_dir
    / "battery_feature_importance.csv"
)

feature_importance_df.to_csv(
    feature_importance_file,
    index=False,
)


# GRÁFICO 1
# COMPARAÇÃO DO MAE

plt.figure(
    figsize=(9, 6)
)

plt.bar(
    metrics_df["model"],
    metrics_df["mae_cycles"],
)

plt.title(
    "Comparação do MAE entre os modelos"
)

plt.xlabel(
    "Modelo"
)

plt.ylabel(
    "MAE (ciclos)"
)

plt.xticks(
    rotation=10
)

plt.tight_layout()

mae_chart_file = (
    outputs_dir
    / "model_mae_comparison.png"
)

plt.savefig(
    mae_chart_file,
    dpi=150,
)

plt.close()


# GRÁFICO 2
# VALOR REAL × VALOR PREVISTO

plt.figure(
    figsize=(8, 8)
)

plt.scatter(
    y_test,
    random_forest_result[
        "predictions"
    ],
    alpha=0.20,
    s=12,
)

min_value = min(
    y_test.min(),
    random_forest_result[
        "predictions"
    ].min(),
)

max_value = max(
    y_test.max(),
    random_forest_result[
        "predictions"
    ].max(),
)

plt.plot(
    [min_value, max_value],
    [min_value, max_value],
    linestyle="--",
)

plt.title(
    "RUL real versus RUL previsto - Random Forest"
)

plt.xlabel(
    "RUL real (ciclos)"
)

plt.ylabel(
    "RUL previsto (ciclos)"
)

plt.grid(
    alpha=0.3
)

plt.tight_layout()

prediction_chart_file = (
    outputs_dir
    / "random_forest_real_vs_predicted.png"
)

plt.savefig(
    prediction_chart_file,
    dpi=150,
)

plt.close()


# GRÁFICO 3
# FEATURE IMPORTANCE

plot_df = (
    feature_importance_df
    .sort_values(
        "importance",
        ascending=True,
    )
)

plt.figure(
    figsize=(10, 7)
)

plt.barh(
    plot_df["feature"],
    plot_df["importance"],
)

plt.title(
    "Importância das variáveis - Random Forest"
)

plt.xlabel(
    "Importância relativa"
)

plt.ylabel(
    "Feature"
)

plt.tight_layout()

importance_chart_file = (
    outputs_dir
    / "random_forest_feature_importance.png"
)

plt.savefig(
    importance_chart_file,
    dpi=150,
)

plt.close()


# RESUMO DOS ARQUIVOS GERADOS

print()
print("TREINAMENTO CONCLUÍDO")

print()
print("Arquivos gerados:")

print(
    f"Modelo Random Forest:\n"
    f"{rf_model_file}"
)

print()
print(
    f"Metadados:\n"
    f"{metadata_file}"
)

print()
print(
    f"Métricas:\n"
    f"{metrics_file}"
)

print()
print(
    f"Predições:\n"
    f"{predictions_file}"
)

print()
print(
    f"Feature importance:\n"
    f"{feature_importance_file}"
)

print()
print(
    f"Gráfico MAE:\n"
    f"{mae_chart_file}"
)

print()
print(
    f"Gráfico real × previsto:\n"
    f"{prediction_chart_file}"
)

print()
print(
    f"Gráfico feature importance:\n"
    f"{importance_chart_file}"
)