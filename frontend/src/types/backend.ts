import type { DeviceStatus } from './device';

export type BackendRiskLevel = 'low' | 'medium' | 'high';

export interface BackendPrediction {
  id: number;
  device_code: string;
  model_id: number;
  risk_policy_id: number | null;
  predicted_at: string;
  telemetry_until: string | null;
  rul_cycles: number;
  risk_level: BackendRiskLevel;
  features: Record<string, unknown> | null;
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
