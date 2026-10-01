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

# V2.2:
# removemos redundâncias diretas:
# - daily_cycles_sum_30d
#   redundante com daily_cycles_mean_30d
# - deep_discharge_rate_30d
#   redundante com deep_discharge_events_30d
# Mantemos cycle_count_change_30d neste experimento
# para avaliar se ele ainda contribui de forma útil.

FEATURES = [
    "cycle_count",

    "temperature_mean_7d",
    "temperature_max_7d",
    "temperature_std_7d",

    "temperature_mean_30d",
    "temperature_std_30d",
    "hot_days_30d",

    "daily_cycles_mean_7d",
    "daily_cycles_std_7d",

    "daily_cycles_mean_30d",
    "daily_cycles_std_30d",

    "deep_discharge_events_30d",

    "cycle_count_change_30d",

    "battery_level_mean_7d",

    "voltage_mean_7d",
    "voltage_std_7d",

    "observation_age_days",
]

TARGET = "rul_cycles"


# RESULTADOS DE REFERÊNCIA DO V2.1

V21_RF_MAE = 133.6239
V21_RF_RMSE = 165.9761
V21_RF_R2 = 0.525045


# CAMINHOS

project_root = Path(__file__).resolve().parents[2]

input_file = (
    project_root
    / "data"
    / "processed"
    / "battery_features_v2_1.csv"
)

artifacts_dir = (
    project_root
    / "ml"
    / "artifacts"
    / "v2_2"
)

outputs_dir = (
    project_root
    / "ml"
    / "outputs"
    / "v2_2_training"
)

artifacts_dir.mkdir(
    parents=True,
    exist_ok=True,
)

outputs_dir.mkdir(
    parents=True,
    exist_ok=True,
)


# CARREGAMENTO

print("PROJETO INTEGRADOR IV")
print("TREINAMENTO V2.2 - SELEÇÃO DE ATRIBUTOS")

df = pd.read_csv(
    input_file,
    parse_dates=["date"],
)

print()
print(
    f"Registros carregados: {len(df):,}"
)

print(
    f"Dispositivos: {df['device_id'].nunique()}"
)


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


# CONTROLE DE DATA LEAKAGE

sim_columns = [
    column
    for column in df.columns
    if column.startswith("sim_")
]

excluded_columns = [
    "usage_profile",
    "battery_design_capacity_mah",
    "battery_current_capacity_mah",
    "soh_percent",
    "soh_change_7d",
    "soh_change_30d",

    # Removidas por redundância no V2.2
    "daily_cycles_sum_30d",
    "deep_discharge_rate_30d",
]

print()
print("CONTROLE DE DATA LEAKAGE E REDUNDÂNCIA")

if sim_columns:

    print()
    print(
        "Colunas internas sim_* encontradas "
        "(não utilizadas no treinamento):"
    )

    for column in sim_columns:
        print(
            f" - {column}"
        )

print()
print(
    "Colunas explicitamente excluídas:"
)

for column in excluded_columns:

    if column in df.columns:
        print(
            f" - {column}"
        )


# VALORES AUSENTES

missing_values = (
    df[FEATURES + [TARGET]]
    .isnull()
    .sum()
)

if missing_values.sum() > 0:

    print()
    print(
        "ATENÇÃO: valores ausentes encontrados:"
    )

    print(
        missing_values[
            missing_values > 0
        ]
    )

    df = df.dropna(
        subset=FEATURES + [TARGET]
    ).copy()


# SEPARAÇÃO POR DISPOSITIVO
# Mantemos a mesma estratégia e random seed dos experimentos
# anteriores para permitir comparação direta.

device_ids = np.array(
    sorted(
        df["device_id"].unique()
    )
)

rng = np.random.default_rng(
    RANDOM_SEED
)

rng.shuffle(
    device_ids
)

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


# VERIFICAÇÃO DE SOBREPOSIÇÃO

overlap = (
    set(train_devices)
    .intersection(
        set(test_devices)
    )
)

if overlap:
    raise RuntimeError(
        "Erro: existem dispositivos simultaneamente "
        "nos conjuntos de treino e teste."
    )


print()
print("DIVISÃO DOS DADOS")

print()
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
print(
    f"Quantidade de features V2.2: "
    f"{len(FEATURES)}"
)

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
    Treina o modelo e calcula métricas
    sobre o conjunto de teste.
    """

    print()
    print("-" * 70)
    print(
        f"Treinando: {model_name}"
    )
    print("-" * 70)

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


# 1. DUMMY REGRESSOR

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


# 2. LINEAR REGRESSION

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
# Mesma configuração da V2.1.
# Ainda NÃO fazemos tuning.

random_forest_model = RandomForestRegressor(
    n_estimators=200,
    random_state=RANDOM_SEED,
    n_jobs=-1,
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
print("COMPARAÇÃO DOS MODELOS - V2.2")

print()
print(
    metrics_df.to_string(
        index=False
    )
)


# MELHOR MODELO

best_result = min(
    results,
    key=lambda result: result["mae"],
)

print()
print("MELHOR MODELO DA RODADA V2.2")

print()
print(
    f"Modelo: "
    f"{best_result['model_name']}"
)

print(
    f"MAE: "
    f"{best_result['mae']:.4f} ciclos"
)

print(
    f"RMSE: "
    f"{best_result['rmse']:.4f} ciclos"
)

print(
    f"R²: "
    f"{best_result['r2']:.6f}"
)


# COMPARAÇÃO V2.1 × V2.2

v22_mae = random_forest_result[
    "mae"
]

v22_rmse = random_forest_result[
    "rmse"
]

v22_r2 = random_forest_result[
    "r2"
]

mae_difference = (
    v22_mae
    - V21_RF_MAE
)

rmse_difference = (
    v22_rmse
    - V21_RF_RMSE
)

r2_difference = (
    v22_r2
    - V21_RF_R2
)

mae_change_pct = (
    (V21_RF_MAE - v22_mae)
    / V21_RF_MAE
    * 100
)

rmse_change_pct = (
    (V21_RF_RMSE - v22_rmse)
    / V21_RF_RMSE
    * 100
)


print()
print("COMPARAÇÃO RANDOM FOREST: V2.1 × V2.2")

print()

print(
    f"MAE V2.1 : "
    f"{V21_RF_MAE:.4f}"
)

print(
    f"MAE V2.2 : "
    f"{v22_mae:.4f}"
)

print(
    f"Diferença: "
    f"{mae_difference:+.4f}"
)

print(
    f"Variação percentual: "
    f"{mae_change_pct:+.2f}%"
)

print()

print(
    f"RMSE V2.1 : "
    f"{V21_RF_RMSE:.4f}"
)

print(
    f"RMSE V2.2 : "
    f"{v22_rmse:.4f}"
)

print(
    f"Diferença: "
    f"{rmse_difference:+.4f}"
)

print(
    f"Variação percentual: "
    f"{rmse_change_pct:+.2f}%"
)

print()

print(
    f"R² V2.1 : "
    f"{V21_RF_R2:.6f}"
)

print(
    f"R² V2.2 : "
    f"{v22_r2:.6f}"
)

print(
    f"Diferença: "
    f"{r2_difference:+.6f}"
)


# SALVAR MÉTRICAS

metrics_file = (
    outputs_dir
    / "battery_model_metrics_v2_2.csv"
)

metrics_df.to_csv(
    metrics_file,
    index=False,
)


# SALVAR RANDOM FOREST

rf_model_file = (
    artifacts_dir
    / "battery_rul_random_forest_v2_2.joblib"
)

joblib.dump(
    random_forest_result[
        "model"
    ],
    rf_model_file,
)


# METADADOS

metadata = {
    "experiment": "V2.2",
    "description": (
        "Seleção de atributos com remoção "
        "de redundâncias diretas da V2.1."
    ),
    "model_name": "RandomForestRegressor",
    "target": TARGET,
    "features": FEATURES,
    "feature_count": len(FEATURES),
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
    "excluded_columns": (
        excluded_columns
        + sim_columns
    ),
    "metrics": {
        "mae_cycles": float(
            v22_mae
        ),
        "rmse_cycles": float(
            v22_rmse
        ),
        "r2": float(
            v22_r2
        ),
    },
    "comparison_with_v2_1": {
        "v2_1_mae": V21_RF_MAE,
        "v2_1_rmse": V21_RF_RMSE,
        "v2_1_r2": V21_RF_R2,
        "mae_difference": float(
            mae_difference
        ),
        "rmse_difference": float(
            rmse_difference
        ),
        "r2_difference": float(
            r2_difference
        ),
        "mae_change_pct": float(
            mae_change_pct
        ),
        "rmse_change_pct": float(
            rmse_change_pct
        ),
    },
}

metadata_file = (
    artifacts_dir
    / "battery_rul_random_forest_v2_2_metadata.json"
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


# PREDIÇÕES

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

prediction_df[
    "signed_error_cycles"
] = (
    prediction_df[
        "predicted_rul_cycles"
    ]
    - prediction_df[
        TARGET
    ]
)

predictions_file = (
    outputs_dir
    / "battery_test_predictions_v2_2.csv"
)

prediction_df.to_csv(
    predictions_file,
    index=False,
)


# FEATURE IMPORTANCE

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
print("IMPORTÂNCIA DAS FEATURES - RANDOM FOREST V2.2")

print()
print(
    feature_importance_df
    .to_string(
        index=False
    )
)


feature_importance_file = (
    outputs_dir
    / "battery_feature_importance_v2_2.csv"
)

feature_importance_df.to_csv(
    feature_importance_file,
    index=False,
)


# CONCENTRAÇÃO DE IMPORTÂNCIA

top_1 = (
    feature_importance_df[
        "importance"
    ]
    .iloc[0]
)

top_3 = (
    feature_importance_df[
        "importance"
    ]
    .head(3)
    .sum()
)

top_5 = (
    feature_importance_df[
        "importance"
    ]
    .head(5)
    .sum()
)

print()
print("CONCENTRAÇÃO DE IMPORTÂNCIA")

print()
print(
    f"Top 1: {top_1:.4f}"
)

print(
    f"Top 3: {top_3:.4f}"
)

print(
    f"Top 5: {top_5:.4f}"
)


# GRÁFICO 1
# MAE ENTRE MODELOS

plt.figure(
    figsize=(9, 6)
)

plt.bar(
    metrics_df["model"],
    metrics_df["mae_cycles"],
)

plt.title(
    "Comparação do MAE entre os modelos - V2.2"
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

mae_models_chart_file = (
    outputs_dir
    / "v2_2_model_mae_comparison.png"
)

plt.savefig(
    mae_models_chart_file,
    dpi=150,
)

plt.close()


# GRÁFICO 2
# V2.1 × V2.2

comparison_df = pd.DataFrame(
    {
        "experiment": [
            "V2.1",
            "V2.2",
        ],
        "mae": [
            V21_RF_MAE,
            v22_mae,
        ],
    }
)

plt.figure(
    figsize=(7, 6)
)

plt.bar(
    comparison_df[
        "experiment"
    ],
    comparison_df[
        "mae"
    ],
)

plt.title(
    "MAE do Random Forest - V2.1 versus V2.2"
)

plt.xlabel(
    "Experimento"
)

plt.ylabel(
    "MAE (ciclos)"
)

plt.tight_layout()

comparison_chart_file = (
    outputs_dir
    / "random_forest_v2_1_vs_v2_2_mae.png"
)

plt.savefig(
    comparison_chart_file,
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
    figsize=(11, 8)
)

plt.barh(
    plot_df["feature"],
    plot_df["importance"],
)

plt.title(
    "Importância das variáveis - Random Forest V2.2"
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
    / "v2_2_random_forest_feature_importance.png"
)

plt.savefig(
    importance_chart_file,
    dpi=150,
)

plt.close()


# GRÁFICO 4
# REAL × PREVISTO

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
    "RUL real versus RUL previsto - Random Forest V2.2"
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
    / "v2_2_random_forest_real_vs_predicted.png"
)

plt.savefig(
    prediction_chart_file,
    dpi=150,
)

plt.close()


# GRÁFICO 5
# DISTRIBUIÇÃO DO ERRO

plt.figure(
    figsize=(9, 6)
)

plt.hist(
    prediction_df[
        "absolute_error_cycles"
    ],
    bins=30,
)

plt.title(
    "Distribuição do erro absoluto - Random Forest V2.2"
)

plt.xlabel(
    "Erro absoluto (ciclos)"
)

plt.ylabel(
    "Quantidade de observações"
)

plt.grid(
    axis="y",
    alpha=0.3,
)

plt.tight_layout()

error_chart_file = (
    outputs_dir
    / "v2_2_random_forest_error_distribution.png"
)

plt.savefig(
    error_chart_file,
    dpi=150,
)

plt.close()


# RESUMO FINAL

print()
print("TREINAMENTO V2.2 CONCLUÍDO")

print()
print("Arquivos gerados:")

generated_files = [
    rf_model_file,
    metadata_file,
    metrics_file,
    predictions_file,
    feature_importance_file,
    mae_models_chart_file,
    comparison_chart_file,
    importance_chart_file,
    prediction_chart_file,
    error_chart_file,
]

for file_path in generated_files:

    print(
        f" - {file_path}"
    )