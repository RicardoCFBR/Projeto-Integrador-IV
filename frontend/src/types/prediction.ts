import type { DeviceStatus } from './device';

export interface Prediction {
  deviceId: string;
  predictedRulCycles: number;
  status: DeviceStatus;
  predictedAt: string;
  modelVersion: string;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface ModelMetrics {
  maeCycles: number;
  rmseCycles: number;
  r2: number;
}

export interface ModelInfo {
  algorithm: string;
  version: string;
  hyperparameters: Record<string, string | number | boolean>;
  metrics: ModelMetrics;
  featureImportances: FeatureImportance[];
}
