import type { Alert } from '../types/alert';
import {
  mapRiskLevelToDeviceStatus,
  type BackendAlert,
  type BackendDeviceOverview,
  type BackendFleetTrendPoint,
  type BackendModel,
  type BackendPrediction,
  type BackendPredictionPreview,
  type BackendTelemetry,
} from '../types/backend';
import type { Device, DeviceTelemetryPoint, RulHistoryPoint } from '../types/device';
import type { ModelInfo, Prediction } from '../types/prediction';
import { round1 } from '../mocks/random';
import { summarizeDevices, type DashboardSummary } from './summary';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const TELEMETRY_WINDOW_DAYS = 30;
const TOP_FEATURES = 7;

const ERROR_MESSAGES: Record<number, string> = {
  404: 'Dispositivo não encontrado na API.',
  422: 'O dispositivo precisa de 31 dias consecutivos de telemetria para gerar a predição.',
  503: 'O modelo não está disponível na API.',
};

class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new ApiError(ERROR_MESSAGES[response.status] ?? `A API respondeu com o status ${response.status}.`);
  }
  return (await response.json()) as T;
}

export function describeApiError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return `Não foi possível conectar à API em ${API_BASE_URL}.`;
}

function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

function feature(prediction: BackendPrediction, name: string): number {
  return Number(prediction.features?.[name] ?? 0);
}

function toDevice(row: BackendDeviceOverview, prediction: BackendPrediction): Device {
  return {
    id: row.code,
    status: mapRiskLevelToDeviceStatus(prediction.risk_level),
    sohPercent: round1(Number(row.estimated_capacity_pct ?? 0)),
    predictedRulCycles: Math.round(Number(prediction.rul_cycles)),
    temperatureMean7d: round1(feature(prediction, 'temperature_mean_7d')),
    temperatureMean30d: round1(feature(prediction, 'temperature_mean_30d')),
    temperatureMax7d: round1(feature(prediction, 'temperature_max_7d')),
    hotDays30d: feature(prediction, 'hot_days_30d'),
    cycleCount: Math.round(Number(row.cycle_count ?? 0)),
    dailyCyclesMean7d: round2(feature(prediction, 'daily_cycles_mean_7d')),
    dailyCyclesMean30d: round2(feature(prediction, 'daily_cycles_mean_30d')),
    cycleCountChange30d: round1(feature(prediction, 'cycle_count_change_30d')),
    deepDischargeEvents30d: feature(prediction, 'deep_discharge_events_30d'),
    lastTelemetryAt: row.last_telemetry_at ?? prediction.predicted_at,
  };
}

function toPrediction(prediction: BackendPrediction, models: BackendModel[]): Prediction {
  return {
    deviceId: prediction.device_code,
    predictedRulCycles: Math.round(Number(prediction.rul_cycles)),
    status: mapRiskLevelToDeviceStatus(prediction.risk_level),
    predictedAt: prediction.predicted_at,
    modelVersion: models.find((model) => model.id === prediction.model_id)?.version ?? '',
  };
}

function toAlert(alert: BackendAlert): Alert {
  const isHigh = alert.risk_level === 'high';
  const threshold = isHigh ? alert.high_below_cycles : alert.medium_below_cycles;
  const thresholdLabel = alert.policy_source === 'experimental' ? 'limiar experimental' : 'limiar';
  const rul = Math.round(Number(alert.rul_cycles)).toLocaleString('pt-BR');
  const reason = threshold
    ? `RUL previsto de ${rul} ciclos, abaixo do ${thresholdLabel} de ${Math.round(Number(threshold)).toLocaleString('pt-BR')}.`
    : `RUL previsto de ${rul} ciclos.`;

  return {
    id: `ALERT-${alert.device_code}`,
    type: 'rul_low',
    severity: isHigh ? 'high' : 'medium',
    deviceId: alert.device_code,
    message: `${reason} ${isHigh ? 'Priorizar inspeção do dispositivo.' : 'Acompanhar nas próximas leituras.'}`,
    createdAt: alert.predicted_at,
    status: 'new',
  };
}

function fetchModels(): Promise<BackendModel[]> {
  return request<BackendModel[]>('/models');
}

async function fetchPredictedRows(): Promise<[BackendDeviceOverview, BackendPrediction][]> {
  const rows = await request<BackendDeviceOverview[]>('/devices/overview');
  return rows.flatMap((row): [BackendDeviceOverview, BackendPrediction][] =>
    row.latest_prediction ? [[row, row.latest_prediction]] : [],
  );
}

export async function getDevices(): Promise<Device[]> {
  const rows = await fetchPredictedRows();
  return rows.map(([row, prediction]) => toDevice(row, prediction));
}

export async function getDeviceById(id: string): Promise<Device | undefined> {
  const devices = await getDevices();
  return devices.find((device) => device.id === id);
}

export async function getDeviceTelemetryHistory(id: string): Promise<DeviceTelemetryPoint[]> {
  const readings = await request<BackendTelemetry[]>(
    `/devices/${encodeURIComponent(id)}/telemetry?limit=${TELEMETRY_WINDOW_DAYS}`,
  );
  return [...readings].reverse().map((reading) => ({
    date: reading.recorded_at.slice(0, 10),
    sohPercent: round2(Number(reading.estimated_capacity_pct ?? 0)),
    temperatureMeanC: round1(Number(reading.battery_temp_c)),
  }));
}

export async function getDeviceRulHistory(id: string): Promise<RulHistoryPoint[]> {
  const predictions = await request<BackendPrediction[]>(`/devices/${encodeURIComponent(id)}/predictions?limit=1000`);
  const rulByDay = new Map<string, number>();
  for (const prediction of [...predictions].reverse()) {
    if (prediction.telemetry_until) {
      rulByDay.set(prediction.telemetry_until.slice(0, 10), Math.round(Number(prediction.rul_cycles)));
    }
  }
  return [...rulByDay.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([date, predictedRulCycles]) => ({ date, predictedRulCycles }));
}

export async function getFleetSohTrend(): Promise<DeviceTelemetryPoint[]> {
  const points = await request<BackendFleetTrendPoint[]>(`/fleet/trend?days=${TELEMETRY_WINDOW_DAYS}`);
  return points.map((point) => ({ date: point.day, sohPercent: round2(point.soh_percent), temperatureMeanC: 0 }));
}

export async function getPredictions(): Promise<Prediction[]> {
  const [rows, models] = await Promise.all([fetchPredictedRows(), fetchModels()]);
  return rows.map(([, prediction]) => toPrediction(prediction, models));
}

export async function getAlerts(): Promise<Alert[]> {
  const alerts = await request<BackendAlert[]>('/alerts');
  return alerts.map(toAlert);
}

export async function getModelInfo(): Promise<ModelInfo> {
  const models = await fetchModels();
  const model = models.at(-1);
  if (!model) {
    throw new ApiError('Nenhum modelo registrado. Execute o comando de demonstração do backend.');
  }
  return {
    algorithm: model.algorithm,
    version: model.version,
    hyperparameters: model.hyperparameters ?? {},
    metrics: {
      maeCycles: model.metrics?.mae_cycles ?? 0,
      rmseCycles: model.metrics?.rmse_cycles ?? 0,
      r2: model.metrics?.r2 ?? 0,
    },
    featureImportances: Object.entries(model.metrics?.feature_importances ?? {})
      .map(([name, importance]) => ({ feature: name, importance }))
      .sort((left, right) => right.importance - left.importance)
      .slice(0, TOP_FEATURES),
  };
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return summarizeDevices(await getDevices());
}

export async function runPrediction(id: string): Promise<Prediction> {
  if (import.meta.env.VITE_READ_ONLY_DEMO === 'true') {
    const preview = await request<BackendPredictionPreview>(
      `/devices/${encodeURIComponent(id)}/predictions/preview`,
    );
    return {
      deviceId: preview.device_code,
      predictedRulCycles: Math.round(Number(preview.rul_cycles)),
      status: mapRiskLevelToDeviceStatus(preview.risk_level),
      predictedAt: preview.predicted_at,
      modelVersion: preview.model_version,
    };
  }
  const prediction = await request<BackendPrediction>(`/devices/${encodeURIComponent(id)}/predictions/run`, {
    method: 'POST',
  });
  return toPrediction(prediction, await fetchModels());
}
