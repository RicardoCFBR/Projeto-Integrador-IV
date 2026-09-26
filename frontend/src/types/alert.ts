export type AlertType = 'rul_low' | 'high_temperature' | 'accelerated_degradation';
export type AlertSeverity = 'low' | 'medium' | 'high';
export type AlertStatus = 'new' | 'viewed' | 'resolved';

export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  deviceId: string;
  message: string;
  createdAt: string;
  status: AlertStatus;
}
