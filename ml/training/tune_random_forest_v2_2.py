from pathlib import Path
import json
import time

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import (
    GroupKFold,
    RandomizedSearchCV,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# CONFIGURAÇÕES

RANDOM_SEED = 42
TRAIN_RATIO = 0.80

N_ITER_SEARCH = 30
N_SPLITS_CV = 5


# FEATURES SELECIONADAS NO V2.2

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


# REFERÊNCIA DO V2.2 SEM TUNING

BASELINE_RF_MAE = 133.7345
BASELINE_RF_RMSE = 166.0096
BASELINE_RF_R2 = 0.524853


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
    / "v2_2_tuned"
)

outputs_dir = (
    project_root
    / "ml"
    / "outputs"
    / "v2_2_tuning"
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
print("AJUSTE DE HIPERPARÂMETROS - RANDOM FOREST V2.2")

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
        "Colunas ausentes: "
        + ", ".join(missing_columns)
    )


# SPLIT FINAL
# IMPORTANTE:
# O conjunto de teste NÃO participa da busca.

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

development_devices = device_ids[
    :train_size
]

test_devices = device_ids[
    train_size:
]


development_df = df[
    df["device_id"].isin(
        development_devices
    )
].copy()

test_df = df[
    df["device_id"].isin(
        test_devices
    )
].copy()


# VERIFICAÇÃO DE SOBREPOSIÇÃO

overlap = (
    set(development_devices)
    .intersection(
        set(test_devices)
    )
)

if overlap:
    raise RuntimeError(
        "Erro: dispositivos aparecem "
        "simultaneamente em desenvolvimento e teste."
    )


print()
print("DIVISÃO FINAL DOS DADOS")

print()
print(
    f"Dispositivos de desenvolvimento: "
    f"{len(development_devices)}"
)

print(
    f"Dispositivos de teste final: "
    f"{len(test_devices)}"
)

print(
    f"Registros de desenvolvimento: "
    f"{len(development_df):,}"
)

print(
    f"Registros de teste final: "
    f"{len(test_df):,}"
)


# MATRIZES

X_dev = development_df[
    FEATURES
].copy()

y_dev = development_df[
    TARGET
].copy()

groups_dev = development_df[
    "device_id"
].copy()


X_test = test_df[
    FEATURES
].copy()

y_test = test_df[
    TARGET
].copy()


# MODELO BASE PARA A BUSCA

rf = RandomForestRegressor(
    random_state=RANDOM_SEED,
    n_jobs=-1,
)


# ESPAÇO DE HIPERPARÂMETROS
# Não exageramos no espaço de busca.
# É suficiente para a PoC e mantém custo computacional
# controlado.

param_distributions = {
    "n_estimators": [
        100,
        200,
        300,
        500,
    ],

    "max_depth": [
        None,
        8,
        12,
        16,
        24,
        32,
    ],

    "min_samples_split": [
        2,
        4,
        8,
        12,
    ],

    "min_samples_leaf": [
        1,
        2,
        4,
        8,
    ],

    "max_features": [
        1.0,
        "sqrt",
        0.7,
        0.5,
    ],

    "bootstrap": [
        True,
    ],
}


# GROUP KFOLD
# Cada fold mantém devices inteiros.

group_kfold = GroupKFold(
    n_splits=N_SPLITS_CV
)


# RANDOMIZED SEARCH
# scoring negativo porque o sklearn maximiza a métrica.
# Depois convertemos para MAE positivo.

search = RandomizedSearchCV(
    estimator=rf,
    param_distributions=param_distributions,
    n_iter=N_ITER_SEARCH,

    scoring="neg_mean_absolute_error",

    cv=group_kfold,

    random_state=RANDOM_SEED,

    n_jobs=-1,

    verbose=2,

    return_train_score=True,
)


# EXECUÇÃO DA BUSCA

print()
print("INICIANDO BUSCA DE HIPERPARÂMETROS")

print()
print(
    f"Combinações testadas: "
    f"{N_ITER_SEARCH}"
)

print(
    f"Folds por combinação: "
    f"{N_SPLITS_CV}"
)

print(
    f"Treinamentos aproximados: "
    f"{N_ITER_SEARCH * N_SPLITS_CV}"
)

start_time = time.time()


search.fit(
    X_dev,
    y_dev,
    groups=groups_dev,
)


elapsed_time = (
    time.time()
    - start_time
)


# MELHORES PARÂMETROS

best_params = search.best_params_

best_cv_mae = (
    -search.best_score_
)


print()
print("MELHOR CONFIGURAÇÃO ENCONTRADA")

print()

for key, value in best_params.items():
    print(
        f"{key}: {value}"
    )

print()
print(
    f"MAE médio da validação cruzada: "
    f"{best_cv_mae:.4f} ciclos"
)

print(
    f"Tempo total da busca: "
    f"{elapsed_time:.2f} segundos"
)


# RESULTADOS COMPLETOS DA BUSCA

cv_results = pd.DataFrame(
    search.cv_results_
)

cv_results["mean_test_mae"] = (
    -cv_results[
        "mean_test_score"
    ]
)

cv_results["std_test_mae"] = (
    cv_results[
        "std_test_score"
    ]
)

cv_results["mean_train_mae"] = (
    -cv_results[
        "mean_train_score"
    ]
)

columns_to_save = [
    "rank_test_score",
    "mean_test_mae",
    "std_test_mae",
    "mean_train_mae",

    "param_n_estimators",
    "param_max_depth",
    "param_min_samples_split",
    "param_min_samples_leaf",
    "param_max_features",
    "param_bootstrap",

    "mean_fit_time",
]

cv_results_export = (
    cv_results[
        columns_to_save
    ]
    .sort_values(
        "rank_test_score"
    )
)

cv_results_file = (
    outputs_dir
    / "random_forest_tuning_results.csv"
)

cv_results_export.to_csv(
    cv_results_file,
    index=False,
)


# MELHOR MODELO
# RandomizedSearchCV com refit=True por padrão já treinou
# novamente o melhor modelo usando TODO o conjunto dev.

best_model = search.best_estimator_


# AVALIAÇÃO FINAL
# Somente agora tocamos no conjunto de teste final.

print()
print("AVALIAÇÃO FINAL NO CONJUNTO DE TESTE")

test_predictions = best_model.predict(
    X_test
)

test_mae = mean_absolute_error(
    y_test,
    test_predictions,
)

test_mse = mean_squared_error(
    y_test,
    test_predictions,
)

test_rmse = np.sqrt(
    test_mse
)

test_r2 = r2_score(
    y_test,
    test_predictions,
)


print()
print(
    f"MAE  : {test_mae:.4f} ciclos"
)

print(
    f"RMSE : {test_rmse:.4f} ciclos"
)

print(
    f"R²   : {test_r2:.6f}"
)


# COMPARAÇÃO COM RANDOM FOREST V2.2 PADRÃO

mae_difference = (
    test_mae
    - BASELINE_RF_MAE
)

rmse_difference = (
    test_rmse
    - BASELINE_RF_RMSE
)

r2_difference = (
    test_r2
    - BASELINE_RF_R2
)

mae_improvement_pct = (
    (BASELINE_RF_MAE - test_mae)
    / BASELINE_RF_MAE
    * 100
)

rmse_improvement_pct = (
    (BASELINE_RF_RMSE - test_rmse)
    / BASELINE_RF_RMSE
    * 100
)


print()
print("COMPARAÇÃO: V2.2 PADRÃO × V2.2 AJUSTADO")

print()

print(
    f"MAE padrão   : "
    f"{BASELINE_RF_MAE:.4f}"
)

print(
    f"MAE ajustado : "
    f"{test_mae:.4f}"
)

print(
    f"Diferença    : "
    f"{mae_difference:+.4f}"
)

print(
    f"Melhoria MAE : "
    f"{mae_improvement_pct:+.2f}%"
)

print()

print(
    f"RMSE padrão   : "
    f"{BASELINE_RF_RMSE:.4f}"
)

print(
    f"RMSE ajustado : "
    f"{test_rmse:.4f}"
)

print(
    f"Diferença     : "
    f"{rmse_difference:+.4f}"
)

print(
    f"Melhoria RMSE : "
    f"{rmse_improvement_pct:+.2f}%"
)

print()

print(
    f"R² padrão   : "
    f"{BASELINE_RF_R2:.6f}"
)

print(
    f"R² ajustado : "
    f"{test_r2:.6f}"
)

print(
    f"Diferença   : "
    f"{r2_difference:+.6f}"
)


# SALVAR MODELO AJUSTADO

model_file = (
    artifacts_dir
    / "battery_rul_random_forest_v2_2_tuned.joblib"
)

joblib.dump(
    best_model,
    model_file,
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
] = test_predictions

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

prediction_file = (
    outputs_dir
    / "battery_test_predictions_tuned.csv"
)

prediction_df.to_csv(
    prediction_file,
    index=False,
)


# FEATURE IMPORTANCE

feature_importance_df = (
    pd.DataFrame(
        {
            "feature": FEATURES,
            "importance": (
                best_model
                .feature_importances_
            ),
        }
    )
    .sort_values(
        "importance",
        ascending=False,
    )
)

feature_importance_file = (
    outputs_dir
    / "battery_feature_importance_tuned.csv"
)

feature_importance_df.to_csv(
    feature_importance_file,
    index=False,
)


print()
print("IMPORTÂNCIA DAS FEATURES - MODELO AJUSTADO")

print()

print(
    feature_importance_df
    .to_string(
        index=False
    )
)


# METADADOS

metadata = {
    "experiment": (
        "Random Forest V2.2 Tuned"
    ),

    "target": TARGET,

    "features": FEATURES,

    "feature_count": len(FEATURES),

    "random_seed": RANDOM_SEED,

    "search": {
        "method": "RandomizedSearchCV",
        "n_iter": N_ITER_SEARCH,
        "cv_method": "GroupKFold",
        "cv_splits": N_SPLITS_CV,
        "scoring": "neg_mean_absolute_error",
        "best_cv_mae": float(
            best_cv_mae
        ),
        "best_params": best_params,
    },

    "dataset": {
        "development_devices": int(
            len(development_devices)
        ),
        "test_devices": int(
            len(test_devices)
        ),
        "development_rows": int(
            len(development_df)
        ),
        "test_rows": int(
            len(test_df)
        ),
    },

    "test_metrics": {
        "mae_cycles": float(
            test_mae
        ),
        "rmse_cycles": float(
            test_rmse
        ),
        "r2": float(
            test_r2
        ),
    },

    "comparison_with_default": {
        "default_mae": BASELINE_RF_MAE,
        "default_rmse": BASELINE_RF_RMSE,
        "default_r2": BASELINE_RF_R2,

        "mae_improvement_pct": float(
            mae_improvement_pct
        ),

        "rmse_improvement_pct": float(
            rmse_improvement_pct
        ),
    },

    "elapsed_seconds": float(
        elapsed_time
    ),
}

metadata_file = (
    artifacts_dir
    / "battery_rul_random_forest_v2_2_tuned_metadata.json"
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
        default=str,
    )


# GRÁFICO 1
# PADRÃO × AJUSTADO

comparison_df = pd.DataFrame(
    {
        "model": [
            "RF V2.2 padrão",
            "RF V2.2 ajustado",
        ],

        "mae": [
            BASELINE_RF_MAE,
            test_mae,
        ],
    }
)

plt.figure(
    figsize=(8, 6)
)

plt.bar(
    comparison_df["model"],
    comparison_df["mae"],
)

plt.title(
    "MAE do Random Forest antes e após ajuste"
)

plt.ylabel(
    "MAE (ciclos)"
)

plt.xlabel(
    "Modelo"
)

plt.tight_layout()

comparison_chart_file = (
    outputs_dir
    / "rf_default_vs_tuned_mae.png"
)

plt.savefig(
    comparison_chart_file,
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
    test_predictions,
    alpha=0.20,
    s=12,
)

min_value = min(
    y_test.min(),
    test_predictions.min(),
)

max_value = max(
    y_test.max(),
    test_predictions.max(),
)

plt.plot(
    [min_value, max_value],
    [min_value, max_value],
    linestyle="--",
)

plt.title(
    "RUL real versus RUL previsto - Random Forest ajustado"
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
    / "rf_tuned_real_vs_predicted.png"
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
    figsize=(11, 8)
)

plt.barh(
    plot_df["feature"],
    plot_df["importance"],
)

plt.title(
    "Importância das variáveis - Random Forest ajustado"
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
    / "rf_tuned_feature_importance.png"
)

plt.savefig(
    importance_chart_file,
    dpi=150,
)

plt.close()


# GRÁFICO 4
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
    "Distribuição do erro absoluto - Random Forest ajustado"
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
    / "rf_tuned_error_distribution.png"
)

plt.savefig(
    error_chart_file,
    dpi=150,
)

plt.close()


# GRÁFICO 5
# TOP RESULTADOS DA BUSCA

top_results = (
    cv_results_export
    .head(10)
    .copy()
)

top_results[
    "configuration"
] = [
    f"Config {i + 1}"
    for i in range(
        len(top_results)
    )
]

plt.figure(
    figsize=(10, 6)
)

plt.bar(
    top_results[
        "configuration"
    ],
    top_results[
        "mean_test_mae"
    ],
)

plt.title(
    "Melhores configurações da busca de hiperparâmetros"
)

plt.xlabel(
    "Configuração"
)

plt.ylabel(
    "MAE médio da validação cruzada"
)

plt.xticks(
    rotation=45
)

plt.tight_layout()

search_chart_file = (
    outputs_dir
    / "rf_tuning_top10_mae.png"
)

plt.savefig(
    search_chart_file,
    dpi=150,
)

plt.close()


# RESUMO

print()
print("AJUSTE DE HIPERPARÂMETROS CONCLUÍDO")

print()
print("Arquivos gerados:")

generated_files = [
    model_file,
    metadata_file,
    cv_results_file,
    prediction_file,
    feature_importance_file,
    comparison_chart_file,
    prediction_chart_file,
    importance_chart_file,
    error_chart_file,
    search_chart_file,
]

for file_path in generated_files:
    print(
        f" - {file_path}"
    )