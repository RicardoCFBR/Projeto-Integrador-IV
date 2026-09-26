export type DeviceStatus = 'healthy' | 'attention' | 'risk';

export interface Device {
  id: string;
  status: DeviceStatus;

  sohPercent: number;
  predictedRulCycles: number;

  temperatureMean7d: number;
  temperatureMean30d: number;
  temperatureMax7d: number;
  hotDays30d: number;

  cycleCount: number;
  dailyCyclesMean7d: number;
  dailyCyclesMean30d: number;
  cycleCountChange30d: number;

  deepDischargeEvents30d: number;

  lastTelemetryAt: string;
}

export interface DeviceTelemetryPoint {
  date: string;
  sohPercent: number;
  temperatureMeanC: number;
  predictedRulCycles: number;
}
