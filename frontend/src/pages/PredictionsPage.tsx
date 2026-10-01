import { useEffect, useMemo, useState } from 'react';
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
import { matchesRulRange, type RulRangeFilter } from '../stores/deviceStore';
import { getModelInfo, getPredictions } from '../services/api';
import type { ModelInfo, Prediction } from '../types/prediction';

const RUL_FILTERS: { value: RulRangeFilter; label: string }[] = [
  { value: 'all', label: 'Todas' },
  { value: 'low', label: 'RUL baixo' },
  { value: 'medium', label: 'RUL intermediário' },
  { value: 'high', label: 'RUL alto' },
];

export function PredictionsPage() {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [rulFilter, setRulFilter] = useState<RulRangeFilter>('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([getModelInfo(), getPredictions()]).then(([modelInfoResult, predictionsResult]) => {
      setModelInfo(modelInfoResult);
      setPredictions(predictionsResult);
      setIsLoading(false);
    });
  }, []);

  const filteredPredictions = useMemo(
    () => predictions.filter((prediction) => matchesRulRange(prediction.predictedRulCycles, rulFilter)),
    [predictions, rulFilter],
  );

  const paginatedPredictions = filteredPredictions.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

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
        value={rulFilter}
        exclusive
        size="small"
        onChange={(_, value: RulRangeFilter | null) => {
          if (value) {
            setRulFilter(value);
            setPage(0);
          }
        }}
      >
        {RUL_FILTERS.map((filter) => (
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
