import * as httpApi from './httpApi';
import * as mockApi from './mockApi';

export type { DashboardSummary } from './summary';
export { describeApiError } from './httpApi';

/**
 * Data access layer. Reads the FastAPI backend by default; VITE_USE_MOCKS=true switches to
 * the demo mocks, and the screens stay the same in both modes. The backend owns the risk
 * policy: the frontend only translates low/medium/high into presentation labels.
 */
const source = import.meta.env.VITE_USE_MOCKS === 'true' ? mockApi : httpApi;

export const {
  getAlerts,
  getDashboardSummary,
  getDeviceById,
  getDeviceRulHistory,
  getDevices,
  getDeviceTelemetryHistory,
  getFleetSohTrend,
  getModelInfo,
  getPredictions,
  runPrediction,
} = source;
