import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import { getAlerts } from '../services/api';
import type { Alert, AlertSeverity, AlertStatus, AlertType } from '../types/alert';

const TYPE_LABELS: Record<AlertType, string> = {
  rul_low: 'RUL reduzido',
  high_temperature: 'Temperatura elevada persistente',
  accelerated_degradation: 'Degradação acelerada',
};

const SEVERITY_CONFIG: Record<AlertSeverity, { label: string; color: 'success' | 'warning' | 'error' }> = {
  low: { label: 'Baixa', color: 'success' },
  medium: { label: 'Média', color: 'warning' },
  high: { label: 'Alta', color: 'error' },
};

const STATUS_LABELS: Record<AlertStatus, string> = {
  new: 'Novo',
  viewed: 'Visualizado',
  resolved: 'Resolvido',
};

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getAlerts().then((result) => {
      setAlerts(result);
      setIsLoading(false);
    });
  }, []);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box>
        <Typography variant="h5">Alertas</Typography>
        <Typography variant="body2" color="text.secondary">
          {alerts.length.toLocaleString('pt-BR')} alertas gerados a partir de regras sobre os dados sintéticos.
        </Typography>
      </Box>

      <Paper variant="outlined">
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Tipo</TableCell>
                <TableCell>Gravidade</TableCell>
                <TableCell>Dispositivo</TableCell>
                <TableCell>Mensagem</TableCell>
                <TableCell>Data</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {alerts.map((alert) => (
                <TableRow key={alert.id} hover>
                  <TableCell>{TYPE_LABELS[alert.type]}</TableCell>
                  <TableCell>
                    <Chip
                      label={SEVERITY_CONFIG[alert.severity].label}
                      color={SEVERITY_CONFIG[alert.severity].color}
                      size="small"
                    />
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{alert.deviceId}</TableCell>
                  <TableCell sx={{ maxWidth: 320 }}>{alert.message}</TableCell>
                  <TableCell>{new Date(alert.createdAt).toLocaleString('pt-BR')}</TableCell>
                  <TableCell>
                    <Chip label={STATUS_LABELS[alert.status]} size="small" variant="outlined" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}
