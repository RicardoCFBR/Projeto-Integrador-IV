import type { Device, DeviceTelemetryPoint, RulHistoryPoint } from '../types/device';
import type { Alert } from '../types/alert';
import type { ModelInfo, Prediction } from '../types/prediction';
import { generateDeviceHistory, generateFleetSohTrend, mockDevices } from '../mocks/devices';
import { mockPredictions } from '../mocks/predictions';
import { mockAlerts } from '../mocks/alerts';
import { mockModelInfo } from '../mocks/modelInfo';
import { summarizeDevices, type DashboardSummary } from './summary';

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

export function getDeviceRulHistory(id: string): Promise<RulHistoryPoint[]> {
  const device = mockDevices.find((item) => item.id === id);
  return resolveAfterDelay(
    device
      ? generateDeviceHistory(device).map((point) => ({
          date: point.date,
          predictedRulCycles: point.predictedRulCycles ?? 0,
        }))
      : [],
  );
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

export function getDashboardSummary(): Promise<DashboardSummary> {
  return resolveAfterDelay(summarizeDevices(mockDevices));
}

export function runPrediction(id: string): Promise<Prediction> {
  const device = mockDevices.find((item) => item.id === id);
  return resolveAfterDelay({
    deviceId: id,
    predictedRulCycles: device?.predictedRulCycles ?? 0,
    status: device?.status ?? 'healthy',
    predictedAt: new Date().toISOString(),
    modelVersion: mockModelInfo.version,
  });
}
