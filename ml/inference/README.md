# Inferência de RUL da bateria

Esta pasta contém a camada de inferência do modelo selecionado para a PoC.

## Modelo

- Algoritmo: RandomForestRegressor
- Versão: RF-V2.2-TUNED
- Target: RUL em ciclos
- Entrada: 17 features temporais/agregadas

O artefato `.joblib` não é versionado no Git e deve existir localmente em:

`ml/artifacts/v2_2_tuned/battery_rul_random_forest_v2_2_tuned.joblib`

## Executar

Na raiz do projeto:

```bash
python ml/inference/predict_battery_rul.py --input ml/inference/example_features.json
```

A saída será um JSON semelhante a:

```json
{
  "predicted_rul_cycles": 742.31,
  "model_version": "RF-V2.2-TUNED",
  "feature_count": 17,
  "device_id": "DEVICE-0001"
}
```

O valor numérico acima é apenas um exemplo de formato. O resultado real depende do artefato treinado.

## Importante

A inferência recebe features já calculadas. Uma leitura isolada de telemetria não é suficiente para
produzir todas as variáveis de 7 e 30 dias exigidas pelo modelo. A próxima etapa de integração deve
buscar o histórico do dispositivo, calcular as 17 features e então chamar esta camada de inferência.
