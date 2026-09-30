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
    / "battery_features_v2.csv"
)

artifacts_dir = (
    project_root
    / "ml"
    / "artifacts"
    / "v2"
)

outputs_dir = (
    project_root
    / "ml"
    / "outputs"
    / "v2_training"
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
print("TREINAMENTO V2 - PREDIÇÃO DE RUL")

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
# Verificamos se colunas internas do simulador estão presentes.
# Elas podem permanecer no dataset para auditoria, mas NÃO são
# utilizadas pelo modelo.

sim_columns = [
    column
    for column in df.columns
    if column.startswith("sim_")
]

print()
print("CONTROLE DE DATA LEAKAGE")

if sim_columns:

    print()
    print(
        "Colunas internas encontradas no dataset "
        "(não utilizadas no treinamento):"
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


excluded_columns = [
    "usage_profile",
    "battery_design_capacity_mah",
    "battery_current_capacity_mah",
    "soh_percent",
    "soh_change_7d",
    "soh_change_30d",
]

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
# Mesma estratégia do Experimento V1:
# 80% dos dispositivos para treino
# 20% dos dispositivos para teste
# Um mesmo aparelho nunca aparece nos dois conjuntos.

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
        "no treino e no teste."
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
    Treina o modelo e calcula as métricas
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
# Mantemos os mesmos parâmetros básicos do V1
# para permitir comparação direta.

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
            "model": result["model_name"],
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
print("COMPARAÇÃO DOS MODELOS - V2")

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
print("MELHOR MODELO DA RODADA V2")

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


# SALVAR MÉTRICAS

metrics_file = (
    outputs_dir
    / "battery_model_metrics_v2.csv"
)

metrics_df.to_csv(
    metrics_file,
    index=False,
)


# SALVAR RANDOM FOREST

rf_model_file = (
    artifacts_dir
    / "battery_rul_random_forest_v2.joblib"
)

joblib.dump(
    random_forest_result[
        "model"
    ],
    rf_model_file,
)


# METADADOS

metadata = {
    "experiment": "V2",
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
}

metadata_file = (
    artifacts_dir
    / "battery_rul_random_forest_v2_metadata.json"
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
    / "battery_test_predictions_v2.csv"
)

prediction_df.to_csv(
    predictions_file,
    index=False,
)


# AMOSTRA DE PREDIÇÕES
# Evitamos chamar .round() na coluna date.

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
print("AMOSTRA DE PREDIÇÕES - V2")

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
print("IMPORTÂNCIA DAS FEATURES - RANDOM FOREST V2")

print()
print(
    feature_importance_df
    .to_string(
        index=False
    )
)


feature_importance_file = (
    outputs_dir
    / "battery_feature_importance_v2.csv"
)

feature_importance_df.to_csv(
    feature_importance_file,
    index=False,
)


# ANÁLISE DE CONCENTRAÇÃO DA FEATURE MAIS IMPORTANTE

top_feature = (
    feature_importance_df.iloc[0]
)

print()
print(
    "Feature mais importante:"
)

print(
    f"{top_feature['feature']} "
    f"= "
    f"{top_feature['importance']:.4f}"
)

print()
print(
    "Referência do Experimento V1:"
)

print(
    "daily_cycles_sum_30d "
    "≈ 0.8886"
)

print()
print(
    "Essa comparação será usada para avaliar "
    "se o V2 reduziu a concentração de importância "
    "em uma única variável."
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
    "Comparação do MAE entre os modelos - V2"
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
    / "v2_model_mae_comparison.png"
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
    "RUL real versus RUL previsto - Random Forest V2"
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
    / "v2_random_forest_real_vs_predicted.png"
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
    "Importância das variáveis - Random Forest V2"
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
    / "v2_random_forest_feature_importance.png"
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
    "Distribuição do erro absoluto - Random Forest V2"
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
    / "v2_random_forest_error_distribution.png"
)

plt.savefig(
    error_distribution_file,
    dpi=150,
)

plt.close()


# RESUMO FINAL

print()
print("TREINAMENTO V2 CONCLUÍDO")

print()
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

print()
print(
    f"Distribuição dos erros:\n"
    f"{error_distribution_file}"
)