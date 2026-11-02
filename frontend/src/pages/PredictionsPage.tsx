import { useEffect, useMemo, useState } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import Paper from '@mui/material/Paper';
import { PredictionCard } from '../components/cards/PredictionCard';
import { DeviceStatusChip } from '../components/devices/DeviceStatusChip';
import type { StatusFilter } from '../stores/deviceStore';
import { describeApiError, getModelInfo, getPredictions } from '../services/api';
import type { ModelInfo, Prediction } from '../types/prediction';

const STATUS_FILTERS: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'Todas' },
  { value: 'risk', label: 'Risco' },
  { value: 'attention', label: 'Atenção' },
  { value: 'healthy', label: 'Saudável' },
];

export function PredictionsPage() {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getModelInfo(), getPredictions()])
      .then(([modelInfoResult, predictionsResult]) => {
        setModelInfo(modelInfoResult);
        setPredictions(predictionsResult);
      })
      .catch((requestError: unknown) => setError(describeApiError(requestError)))
      .finally(() => setIsLoading(false));
  }, []);

  const filteredPredictions = useMemo(
    () => predictions.filter((prediction) => statusFilter === 'all' || prediction.status === statusFilter),
    [predictions, statusFilter],
  );

  const paginatedPredictions = filteredPredictions.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (isLoading || !modelInfo) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Typography variant="h5">Predições</Typography>

      <PredictionCard modelInfo={modelInfo} />

      <ToggleButtonGroup
        value={statusFilter}
        exclusive
        size="small"
        onChange={(_, value: StatusFilter | null) => {
          if (value) {
            setStatusFilter(value);
            setPage(0);
          }
        }}
      >
        {STATUS_FILTERS.map((filter) => (
          <ToggleButton key={filter.value} value={filter.value}>
            {filter.label}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>

      <Paper variant="outlined">
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Dispositivo</TableCell>
                <TableCell>RUL previsto</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Data da previsão</TableCell>
                <TableCell>Versão do modelo</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedPredictions.map((prediction) => (
                <TableRow key={prediction.deviceId} hover>
                  <TableCell sx={{ fontWeight: 600 }}>{prediction.deviceId}</TableCell>
                  <TableCell>{prediction.predictedRulCycles.toLocaleString('pt-BR')} ciclos</TableCell>
                  <TableCell>
                    <DeviceStatusChip status={prediction.status} />
                  </TableCell>
                  <TableCell>{new Date(prediction.predictedAt).toLocaleDateString('pt-BR')}</TableCell>
                  <TableCell>{prediction.modelVersion}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={filteredPredictions.length}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 25, 50]}
          labelRowsPerPage="Linhas por página"
          labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${count}`}
        />
      </Paper>
    </Box>
  );
}
