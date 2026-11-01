import type { Device, DeviceStatus } from '../types/device';
import { round1 } from '../mocks/random';

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

export function summarizeDevices(devices: Device[]): DashboardSummary {
  const total = devices.length;
  const countByStatus = (status: DeviceStatus) => devices.filter((device) => device.status === status).length;
  const percentOf = (count: number) => (total === 0 ? 0 : round1((count / total) * 100));
  const averageOf = (values: number[]) =>
    total === 0 ? 0 : values.reduce((sum, value) => sum + value, 0) / total;

  const healthyCount = countByStatus('healthy');
  const attentionCount = countByStatus('attention');
  const riskCount = countByStatus('risk');

  return {
    totalDevices: total,
    healthyCount,
    attentionCount,
    riskCount,
    healthyPercent: percentOf(healthyCount),
    attentionPercent: percentOf(attentionCount),
    riskPercent: percentOf(riskCount),
    averageRulCycles: Math.round(averageOf(devices.map((device) => device.predictedRulCycles))),
    averageTemperatureC: round1(averageOf(devices.map((device) => device.temperatureMean30d))),
  };
}
