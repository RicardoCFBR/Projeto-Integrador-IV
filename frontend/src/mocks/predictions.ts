import type { Prediction } from '../types/prediction';
import { mockDevices } from './devices';
import { createSeededRandom, randomBetween } from './random';

const MODEL_VERSION = 'RF-V2.2-TUNED';

export const mockPredictions: Prediction[] = mockDevices.map((device, index) => {
  const rand = createSeededRandom(index + 1);
  const hoursAgo = Math.round(randomBetween(rand, 1, 96));

  return {
    deviceId: device.id,
    predictedRulCycles: device.predictedRulCycles,
    status: device.status,
    predictedAt: new Date(Date.now() - hoursAgo * 60 * 60 * 1000).toISOString(),
    modelVersion: MODEL_VERSION,
  };
});
