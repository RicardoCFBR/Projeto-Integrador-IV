import type { Device, DeviceStatus, DeviceTelemetryPoint } from '../types/device';
import { createSeededRandom, randomBetween, round1 } from './random';

const DEVICE_COUNT = 400;

/**
 * Regra simples de classificação de status a partir de SoH e RUL previsto.
 * Puramente para fins de demonstração — não reflete a lógica real do modelo.
 */
export function deriveDeviceStatus(sohPercent: number, predictedRulCycles: number): DeviceStatus {
  if (sohPercent < 82 || predictedRulCycles < 500) return 'risk';
  if (sohPercent < 90 || predictedRulCycles < 900) return 'attention';
  return 'healthy';
}

function buildDevice(index: number): Device {
  const rand = createSeededRandom(1000 + index * 97);
  const id = `DEVICE-${String(index).padStart(4, '0')}`;

  const sohPercent = round1(randomBetween(rand, 78, 99));
  const predictedRulCycles = Math.round(randomBetween(rand, 350, 1800));

  const temperatureMean7d = round1(randomBetween(rand, 27, 39));
  const temperatureMean30d = round1(temperatureMean7d + randomBetween(rand, -1.5, 1.5));
  const temperatureMax7d = round1(temperatureMean7d + randomBetween(rand, 2, 8));
  const hotDays30d = Math.round(randomBetween(rand, 0, 22));

  const cycleCount = Math.round(randomBetween(rand, 60, 1500));
  const dailyCyclesMean7d = round1(randomBetween(rand, 1, 6));
  const dailyCyclesMean30d = round1(dailyCyclesMean7d + randomBetween(rand, -0.5, 0.5));
  const cycleCountChange30d = Math.round(randomBetween(rand, 0, 55));

  const deepDischargeEvents30d = Math.round(randomBetween(rand, 0, 14));

  const minutesAgo = Math.round(randomBetween(rand, 5, 60 * 36));
  const lastTelemetryAt = new Date(Date.now() - minutesAgo * 60_000).toISOString();

  return {
    id,
    status: deriveDeviceStatus(sohPercent, predictedRulCycles),
    sohPercent,
    predictedRulCycles,
    temperatureMean7d,
    temperatureMean30d,
    temperatureMax7d,
    hotDays30d,
    cycleCount,
    dailyCyclesMean7d,
    dailyCyclesMean30d,
    cycleCountChange30d,
    deepDischargeEvents30d,
    lastTelemetryAt,
  };
}

export const mockDevices: Device[] = Array.from({ length: DEVICE_COUNT }, (_, i) => buildDevice(i + 1));

/**
 * Histórico simulado de 30 dias para os gráficos da tela de detalhe do dispositivo.
 * Gerado sob demanda (não é pré-computado para os 400 dispositivos).
 */
export function generateDeviceHistory(device: Device, days = 30): DeviceTelemetryPoint[] {
  const rand = createSeededRandom(device.id.length * 7919 + device.cycleCount);
  const points: DeviceTelemetryPoint[] = [];

  let soh = Math.min(99, device.sohPercent + randomBetween(rand, 1.5, 3));
  let rul = device.predictedRulCycles + Math.round(randomBetween(rand, 40, 90));

  for (let i = days; i >= 0; i -= 1) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

    soh = Math.max(70, soh - randomBetween(rand, 0.02, 0.12));
    rul = Math.max(100, rul - randomBetween(rand, 1, 4));
    const temperatureMeanC = round1(device.temperatureMean30d + randomBetween(rand, -2.5, 2.5));

    points.push({
      date,
      sohPercent: round1(soh),
      temperatureMeanC,
      predictedRulCycles: Math.round(rul),
    });
  }

  return points;
}

export function generateFleetSohTrend(days = 30): DeviceTelemetryPoint[] {
  const rand = createSeededRandom(42);
  const points: DeviceTelemetryPoint[] = [];
  let soh = 93.5;

  for (let i = days; i >= 0; i -= 1) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    soh = Math.max(88, soh - randomBetween(rand, 0.01, 0.09));

    points.push({
      date,
      sohPercent: round1(soh),
      temperatureMeanC: 0,
      predictedRulCycles: 0,
    });
  }

  return points;
}
