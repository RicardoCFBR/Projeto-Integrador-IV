import type { DeviceStatus } from './device';

export type BackendRiskLevel = 'low' | 'medium' | 'high';

export interface BackendPrediction {
  id: number;
  device_code: string;
  model_id: number;
  risk_policy_id: number | null;
  predicted_at: string;
  telemetry_until: string | null;
  rul_cycles: string;
  risk_level: BackendRiskLevel;
  features: Record<string, unknown> | null;
}

export interface BackendPredictionPreview {
  device_code: string;
  predicted_at: string;
  telemetry_until: string;
  rul_cycles: string;
  risk_level: BackendRiskLevel;
  model_version: string;
  persisted: false;
}

export interface BackendDeviceOverview {
  code: string;
  latest_prediction: BackendPrediction | null;
  last_telemetry_at: string | null;
  estimated_capacity_pct: string | null;
  cycle_count: string | null;
}

export interface BackendTelemetry {
  recorded_at: string;
  battery_temp_c: string;
  estimated_capacity_pct: string | null;
}

export interface BackendModel {
  id: number;
  version: string;
  algorithm: string;
  hyperparameters: Record<string, string | number | boolean> | null;
  metrics: {
    mae_cycles: number;
    rmse_cycles: number;
    r2: number;
    feature_importances: Record<string, number>;
  } | null;
}

export interface BackendAlert {
  device_code: string;
  risk_level: BackendRiskLevel;
  rul_cycles: string;
  predicted_at: string;
  telemetry_until: string | null;
  policy_name: string | null;
  policy_source: string | null;
  high_below_cycles: string | null;
  medium_below_cycles: string | null;
}

export interface BackendFleetTrendPoint {
  day: string;
  soh_percent: number;
}

/**
 * The backend owns the risk policy/thresholds.
 * The frontend only translates the backend risk band into presentation labels.
 */
export function mapRiskLevelToDeviceStatus(level: BackendRiskLevel): DeviceStatus {
  if (level === 'high') return 'risk';
  if (level === 'medium') return 'attention';
  return 'healthy';
}
