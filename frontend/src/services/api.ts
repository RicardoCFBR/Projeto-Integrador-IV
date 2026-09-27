import type { Device, DeviceTelemetryPoint } from '../types/device';
import type { Alert } from '../types/alert';
import type { ModelInfo, Prediction } from '../types/prediction';
import { generateDeviceHistory, generateFleetSohTrend, mockDevices } from '../mocks/devices';
import { mockPredictions } from '../mocks/predictions';
import { mockAlerts } from '../mocks/alerts';
import { mockModelInfo } from '../mocks/modelInfo';
import { round1 } from '../mocks/random';

/**
 * Camada de acesso a dados. Hoje resolve com dados mockados; quando o backend
 * existir, cada função aqui vira uma chamada `fetch` para o endpoint real,
 * sem que as telas precisem ser alteradas.
 */

const MOCK_LATENCY_MS = 200;

function resolveAfterDelay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), MOCK_LATENCY_MS);
  });
}

export function getDevices(): Promise<Device[]> {
  return resolveAfterDelay(mockDevices);
}

export function getDeviceById(id: string): Promise<Device | undefined> {
  return resolveAfterDelay(mockDevices.find((device) => device.id === id));
}

export function getDeviceTelemetryHistory(id: string): Promise<DeviceTelemetryPoint[]> {
  const device = mockDevices.find((item) => item.id === id);
  return resolveAfterDelay(device ? generateDeviceHistory(device) : []);
}

export function getFleetSohTrend(): Promise<DeviceTelemetryPoint[]> {
  return resolveAfterDelay(generateFleetSohTrend());
}

export function getPredictions(): Promise<Prediction[]> {
  return resolveAfterDelay(mockPredictions);
}

export function getAlerts(): Promise<Alert[]> {
  return resolveAfterDelay(mockAlerts);
}

export function getModelInfo(): Promise<ModelInfo> {
  return resolveAfterDelay(mockModelInfo);
}

export interface DashboardSummary {
  totalDevices: number;
  healthyCount: number;
  attentionCount: number;
  riskCount: number;
  healthyPercent: number;
  attentionPercent: number;
  riskPercent: number;
  averageRulCycles: number;
  averageTemperatureC: number;
}

export function getDashboardSummary(): Promise<DashboardSummary> {
  const total = mockDevices.length;
  const healthyCount = mockDevices.filter((d) => d.status === 'healthy').length;
  const attentionCount = mockDevices.filter((d) => d.status === 'attention').length;
  const riskCount = mockDevices.filter((d) => d.status === 'risk').length;

  const averageRulCycles = Math.round(
    mockDevices.reduce((sum, d) => sum + d.predictedRulCycles, 0) / total,
  );
  const averageTemperatureC = round1(
    mockDevices.reduce((sum, d) => sum + d.temperatureMean30d, 0) / total,
  );

  return resolveAfterDelay({
    totalDevices: total,
    healthyCount,
    attentionCount,
    riskCount,
    healthyPercent: round1((healthyCount / total) * 100),
    attentionPercent: round1((attentionCount / total) * 100),
    riskPercent: round1((riskCount / total) * 100),
    averageRulCycles,
    averageTemperatureC,
  });
}
