import type { ModelInfo } from '../types/prediction';

export const mockModelInfo: ModelInfo = {
  algorithm: 'RandomForestRegressor',
  version: 'RF-V2.2-TUNED',
  hyperparameters: {
    n_estimators: 500,
    max_depth: 8,
    min_samples_split: 2,
    min_samples_leaf: 8,
    max_features: 'sqrt',
    bootstrap: true,
  },
  metrics: {
    maeCycles: 126.84,
    rmseCycles: 156.45,
    r2: 0.578,
  },
  featureImportances: [
    { feature: 'temperature_mean_30d', importance: 0.2796 },
    { feature: 'hot_days_30d', importance: 0.2155 },
    { feature: 'temperature_mean_7d', importance: 0.151 },
    { feature: 'daily_cycles_mean_30d', importance: 0.0889 },
    { feature: 'cycle_count_change_30d', importance: 0.0802 },
    { feature: 'temperature_max_7d', importance: 0.0767 },
    { feature: 'daily_cycles_mean_7d', importance: 0.049 },
  ],
};
