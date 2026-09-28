import Chip from '@mui/material/Chip';
import type { DeviceStatus } from '../../types/device';

const STATUS_CONFIG: Record<DeviceStatus, { label: string; color: 'success' | 'warning' | 'error' }> = {
  healthy: { label: 'Saudável', color: 'success' },
  attention: { label: 'Atenção', color: 'warning' },
  risk: { label: 'Risco', color: 'error' },
};

interface DeviceStatusChipProps {
  status: DeviceStatus;
  size?: 'small' | 'medium';
}

export function DeviceStatusChip({ status, size = 'small' }: DeviceStatusChipProps) {
  const config = STATUS_CONFIG[status];
  return <Chip label={config.label} color={config.color} size={size} variant="filled" />;
}
