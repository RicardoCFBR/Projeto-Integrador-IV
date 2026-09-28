import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import type { Device } from '../../types/device';
import { DeviceStatusChip } from '../devices/DeviceStatusChip';

interface DeviceStatusCardProps {
  device: Device;
}

export function DeviceStatusCard({ device }: DeviceStatusCardProps) {
  return (
    <Card>
      <CardContent>
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 2,
          }}
        >
          <Box>
            <Typography variant="overline" color="text.secondary">
              Dispositivo
            </Typography>
            <Typography variant="h5">{device.id}</Typography>
            <Box sx={{ mt: 1 }}>
              <DeviceStatusChip status={device.status} />
            </Box>
          </Box>

          <Box sx={{ textAlign: { xs: 'left', sm: 'right' } }}>
            <Typography variant="overline" color="text.secondary">
              RUL previsto
            </Typography>
            <Typography variant="h4" color="primary.main">
              {device.predictedRulCycles.toLocaleString('pt-BR')}
              <Typography component="span" variant="body1" color="text.secondary" sx={{ ml: 0.5 }}>
                ciclos
              </Typography>
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
