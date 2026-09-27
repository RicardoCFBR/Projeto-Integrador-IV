import type { Alert } from '../types/alert';
import { mockDevices } from './devices';
import { createSeededRandom, randomBetween } from './random';

function hoursAgoIso(hours: number): string {
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
}

const curatedAlerts: Alert[] = [
  {
    id: 'ALERT-0001',
    type: 'rul_low',
    severity: 'high',
    deviceId: 'DEVICE-0312',
    message: 'RUL previsto abaixo de 600 ciclos.',
    createdAt: hoursAgoIso(3),
    status: 'new',
  },
  {
    id: 'ALERT-0002',
    type: 'high_temperature',
    severity: 'medium',
    deviceId: 'DEVICE-0087',
    message: 'Alta frequência de dias com temperatura elevada nos últimos 30 dias.',
    createdAt: hoursAgoIso(9),
    status: 'viewed',
  },
  {
    id: 'ALERT-0003',
    type: 'accelerated_degradation',
    severity: 'high',
    deviceId: 'DEVICE-0194',
    message: 'Redução de SoH acima do padrão observado recentemente.',
    createdAt: hoursAgoIso(20),
    status: 'new',
  },
];

const riskDevices = mockDevices.filter((device) => device.status === 'risk').slice(0, 12);
const attentionDevices = mockDevices.filter((device) => device.status === 'attention').slice(0, 10);

const generatedAlerts: Alert[] = [
  ...riskDevices.map((device, index) => {
    const rand = createSeededRandom(index + 500);
    return {
      id: `ALERT-${String(100 + index).padStart(4, '0')}`,
      type: 'rul_low' as const,
      severity: 'high' as const,
      deviceId: device.id,
      message: `RUL previsto de ${device.predictedRulCycles} ciclos, abaixo do limite de segurança.`,
      createdAt: hoursAgoIso(randomBetween(rand, 1, 72)),
      status: rand() > 0.5 ? ('new' as const) : ('viewed' as const),
    };
  }),
  ...attentionDevices.map((device, index) => {
    const rand = createSeededRandom(index + 700);
    return {
      id: `ALERT-${String(200 + index).padStart(4, '0')}`,
      type: 'high_temperature' as const,
      severity: 'medium' as const,
      deviceId: device.id,
      message: `${device.hotDays30d} dias com temperatura elevada nos últimos 30 dias.`,
      createdAt: hoursAgoIso(randomBetween(rand, 1, 96)),
      status: rand() > 0.7 ? ('resolved' as const) : ('new' as const),
    };
  }),
];

export const mockAlerts: Alert[] = [...curatedAlerts, ...generatedAlerts].sort(
  (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
);
