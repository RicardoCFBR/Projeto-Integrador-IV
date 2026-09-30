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

TARGET = "rul_cycles"


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
    / "v2_1"
)

outputs_dir = (
    project_root
    / "ml"
    / "outputs"
    / "v2_1_training"
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
print("TREINAMENTO V2.1 - PREDIÇÃO DE RUL")

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
]

print()
print("CONTROLE DE DATA LEAKAGE")

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
    "Outras colunas explicitamente excluídas:"
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


# X E y

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
    Treina o modelo e calcula métricas
    no conjunto de teste.
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


# 1. BASELINE

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
# Mantemos a mesma configuração básica do V2
# para que a comparação seja justa.

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


# TABELA DE RESULTADOS

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
print("COMPARAÇÃO DOS MODELOS - V2.1")

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
print("MELHOR MODELO DA RODADA V2.1")

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


# COMPARAÇÃO COM V2

V2_RF_MAE = 140.6047
V2_RF_RMSE = 173.2937
V2_RF_R2 = 0.482582

v21_mae = (
    random_forest_result["mae"]
)

v21_rmse = (
    random_forest_result["rmse"]
)

v21_r2 = (
    random_forest_result["r2"]
)

mae_difference = (
    v21_mae
    - V2_RF_MAE
)

rmse_difference = (
    v21_rmse
    - V2_RF_RMSE
)

r2_difference = (
    v21_r2
    - V2_RF_R2
)

mae_improvement_pct = (
    (V2_RF_MAE - v21_mae)
    / V2_RF_MAE
    * 100
)

rmse_improvement_pct = (
    (V2_RF_RMSE - v21_rmse)
    / V2_RF_RMSE
    * 100
)


print()
print("COMPARAÇÃO RANDOM FOREST: V2 × V2.1")

print()
print(
    f"MAE V2   : "
    f"{V2_RF_MAE:.4f}"
)

print(
    f"MAE V2.1 : "
    f"{v21_mae:.4f}"
)

print(
    f"Diferença: "
    f"{mae_difference:+.4f}"
)

print(
    f"Variação percentual do MAE: "
    f"{mae_improvement_pct:+.2f}%"
)

print()

print(
    f"RMSE V2   : "
    f"{V2_RF_RMSE:.4f}"
)

print(
    f"RMSE V2.1 : "
    f"{v21_rmse:.4f}"
)

print(
    f"Diferença: "
    f"{rmse_difference:+.4f}"
)

print(
    f"Variação percentual do RMSE: "
    f"{rmse_improvement_pct:+.2f}%"
)

print()

print(
    f"R² V2   : "
    f"{V2_RF_R2:.6f}"
)

print(
    f"R² V2.1 : "
    f"{v21_r2:.6f}"
)

print(
    f"Diferença no R²: "
    f"{r2_difference:+.6f}"
)


# SALVAR MÉTRICAS

metrics_file = (
    outputs_dir
    / "battery_model_metrics_v2_1.csv"
)

metrics_df.to_csv(
    metrics_file,
    index=False,
)


# SALVAR RANDOM FOREST

rf_model_file = (
    artifacts_dir
    / "battery_rul_random_forest_v2_1.joblib"
)

joblib.dump(
    random_forest_result[
        "model"
    ],
    rf_model_file,
)


# METADADOS

metadata = {
    "experiment": "V2.1",
    "model_name": "RandomForestRegressor",
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
    "excluded_from_training": (
        excluded_columns
        + sim_columns
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
    "comparison_with_v2": {
        "v2_mae": V2_RF_MAE,
        "v2_rmse": V2_RF_RMSE,
        "v2_r2": V2_RF_R2,
        "mae_difference": float(
            mae_difference
        ),
        "rmse_difference": float(
            rmse_difference
        ),
        "r2_difference": float(
            r2_difference
        ),
        "mae_improvement_pct": float(
            mae_improvement_pct
        ),
        "rmse_improvement_pct": float(
            rmse_improvement_pct
        ),
    },
}

metadata_file = (
    artifacts_dir
    / "battery_rul_random_forest_v2_1_metadata.json"
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

prediction_df[
    "signed_error_cycles"
] = (
    prediction_df[
        "predicted_rul_cycles"
    ]
    - prediction_df[TARGET]
)

predictions_file = (
    outputs_dir
    / "battery_test_predictions_v2_1.csv"
)

prediction_df.to_csv(
    predictions_file,
    index=False,
)


# AMOSTRA DE PREDIÇÕES

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
    .copy()
)

numeric_prediction_columns = [
    "rul_cycles",
    "predicted_rul_cycles",
    "absolute_error_cycles",
    "signed_error_cycles",
]

sample_predictions[
    numeric_prediction_columns
] = (
    sample_predictions[
        numeric_prediction_columns
    ]
    .round(2)
)


print()
print("AMOSTRA DE PREDIÇÕES - V2.1")

print()
print(
    sample_predictions
    .to_string(
        index=False
    )
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
print("IMPORTÂNCIA DAS FEATURES - RANDOM FOREST V2.1")

print()
print(
    feature_importance_df
    .to_string(
        index=False
    )
)

feature_importance_file = (
    outputs_dir
    / "battery_feature_importance_v2_1.csv"
)

feature_importance_df.to_csv(
    feature_importance_file,
    index=False,
)


# TOP FEATURES

print()
print("5 features mais importantes:")

top_5_features = (
    feature_importance_df
    .head(5)
)

for _, row in top_5_features.iterrows():

    print(
        f" - {row['feature']}: "
        f"{row['importance']:.4f}"
    )


# CONCENTRAÇÃO DAS FEATURES
# Mede quanto da importância total está concentrada
# nas principais variáveis.

top_1_importance = (
    feature_importance_df[
        "importance"
    ]
    .iloc[0]
)

top_3_importance = (
    feature_importance_df[
        "importance"
    ]
    .head(3)
    .sum()
)

top_5_importance = (
    feature_importance_df[
        "importance"
    ]
    .head(5)
    .sum()
)

print()
print("CONCENTRAÇÃO DA IMPORTÂNCIA")

print()
print(
    f"Top 1: "
    f"{top_1_importance:.4f}"
)

print(
    f"Top 3: "
    f"{top_3_importance:.4f}"
)

print(
    f"Top 5: "
    f"{top_5_importance:.4f}"
)


# GRÁFICO 1
# MAE DOS MODELOS V2.1

plt.figure(
    figsize=(9, 6)
)

plt.bar(
    metrics_df["model"],
    metrics_df["mae_cycles"],
)

plt.title(
    "Comparação do MAE entre os modelos - V2.1"
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
    / "v2_1_model_mae_comparison.png"
)

plt.savefig(
    mae_chart_file,
    dpi=150,
)

plt.close()


# GRÁFICO 2
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
    "RUL real versus RUL previsto - Random Forest V2.1"
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
    / "v2_1_random_forest_real_vs_predicted.png"
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
    figsize=(11, 9)
)

plt.barh(
    plot_df["feature"],
    plot_df["importance"],
)

plt.title(
    "Importância das variáveis - Random Forest V2.1"
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
    / "v2_1_random_forest_feature_importance.png"
)

plt.savefig(
    importance_chart_file,
    dpi=150,
)

plt.close()


# GRÁFICO 4
# DISTRIBUIÇÃO DO ERRO ABSOLUTO

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
    "Distribuição do erro absoluto - Random Forest V2.1"
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

error_distribution_file = (
    outputs_dir
    / "v2_1_random_forest_error_distribution.png"
)

plt.savefig(
    error_distribution_file,
    dpi=150,
)

plt.close()


# GRÁFICO 5
# V2 × V2.1 - RANDOM FOREST

comparison_df = pd.DataFrame(
    {
        "experiment": [
            "V2",
            "V2.1",
        ],
        "mae": [
            V2_RF_MAE,
            v21_mae,
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
    "MAE do Random Forest - V2 versus V2.1"
)

plt.xlabel(
    "Experimento"
)

plt.ylabel(
    "MAE (ciclos)"
)

plt.tight_layout()

v2_comparison_chart_file = (
    outputs_dir
    / "random_forest_v2_vs_v2_1_mae.png"
)

plt.savefig(
    v2_comparison_chart_file,
    dpi=150,
)

plt.close()


# RESUMO FINAL

print()
print("TREINAMENTO V2.1 CONCLUÍDO")

print()
print("Arquivos gerados:")

generated_files = [
    rf_model_file,
    metadata_file,
    metrics_file,
    predictions_file,
    feature_importance_file,
    mae_chart_file,
    prediction_chart_file,
    importance_chart_file,
    error_distribution_file,
    v2_comparison_chart_file,
]

for file_path in generated_files:
    print(
        f" - {file_path}"
    )