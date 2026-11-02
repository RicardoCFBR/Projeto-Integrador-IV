import { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined';
import PlayArrowOutlinedIcon from '@mui/icons-material/PlayArrowOutlined';
import { useTheme } from '@mui/material/styles';
import { DeviceStatusCard } from '../components/cards/DeviceStatusCard';
import { ChartCard } from '../components/cards/ChartCard';
import { DeviceMetrics } from '../components/devices/DeviceMetrics';
import { SohTrendChart } from '../components/charts/SohTrendChart';
import { FeatureImportanceChart } from '../components/charts/FeatureImportanceChart';
import {
  describeApiError,
  getDeviceById,
  getDeviceRulHistory,
  getDeviceTelemetryHistory,
  getModelInfo,
  runPrediction,
} from '../services/api';
import { useDeviceStore } from '../stores/deviceStore';
import type { Device, DeviceTelemetryPoint, RulHistoryPoint } from '../types/device';
import type { FeatureImportance } from '../types/prediction';

interface DeviceData {
  device: Device | undefined;
  history: DeviceTelemetryPoint[];
  rulHistory: RulHistoryPoint[];
  featureImportances: FeatureImportance[];
}

interface RunFeedback {
  severity: 'success' | 'warning';
  message: string;
}

async function fetchDeviceData(id: string): Promise<DeviceData> {
  const [device, history, rulHistory, modelInfo] = await Promise.all([
    getDeviceById(id),
    getDeviceTelemetryHistory(id),
    getDeviceRulHistory(id),
    getModelInfo(),
  ]);
  return { device, history, rulHistory, featureImportances: modelInfo.featureImportances.slice(0, 6) };
}

export function DeviceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const theme = useTheme();
  const invalidateDevices = useDeviceStore((state) => state.invalidate);

  const [data, setData] = useState<DeviceData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [runFeedback, setRunFeedback] = useState<RunFeedback | null>(null);

  useEffect(() => {
    if (!id) return;
    let isMounted = true;
    setIsLoading(true);
    setError(null);
    setRunFeedback(null);

    fetchDeviceData(id)
      .then((result) => {
        if (!isMounted) return;
        setData(result);
        setIsLoading(false);
      })
      .catch((requestError: unknown) => {
        if (!isMounted) return;
        setError(describeApiError(requestError));
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [id]);

  const handleRunPrediction = async () => {
    if (!id) return;
    setIsRunning(true);
    setRunFeedback(null);
    try {
      const prediction = await runPrediction(id);
      invalidateDevices();
      setData(await fetchDeviceData(id));
      setRunFeedback({
        severity: 'success',
        message: `Predição registrada com o modelo ${prediction.modelVersion}: ${prediction.predictedRulCycles.toLocaleString('pt-BR')} ciclos.`,
      });
    } catch (requestError) {
      setRunFeedback({ severity: 'warning', message: describeApiError(requestError) });
    } finally {
      setIsRunning(false);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  const device = data?.device;

  if (!data || !device) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'flex-start' }}>
        <Alert severity="warning">Dispositivo "{id}" não foi encontrado.</Alert>
        <Button component={RouterLink} to="/devices" startIcon={<ArrowBackOutlinedIcon />}>
          Voltar para Dispositivos
        </Button>
      </Box>
    );
  }

  const sohSeries = data.history.map((point) => ({ date: point.date, value: point.sohPercent }));
  const temperatureSeries = data.history.map((point) => ({ date: point.date, value: point.temperatureMeanC }));
  const rulSeries = data.rulHistory.map((point) => ({ date: point.date, value: point.predictedRulCycles }));

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 1 }}>
        <Button component={RouterLink} to="/devices" startIcon={<ArrowBackOutlinedIcon />} size="small">
          Voltar para Dispositivos
        </Button>
        <Button
          variant="contained"
          size="small"
          startIcon={<PlayArrowOutlinedIcon />}
          onClick={handleRunPrediction}
          disabled={isRunning}
        >
          {isRunning ? 'Rodando...' : 'Rodar predição'}
        </Button>
      </Box>

      {runFeedback ? (
        <Alert severity={runFeedback.severity} onClose={() => setRunFeedback(null)}>
          {runFeedback.message}
        </Alert>
      ) : null}

      <DeviceStatusCard device={device} />

      <DeviceMetrics
        items={[
          { label: 'SoH atual', value: `${device.sohPercent}%` },
          { label: 'Temperatura média 7 dias', value: `${device.temperatureMean7d}°C` },
          { label: 'Temperatura média 30 dias', value: `${device.temperatureMean30d}°C` },
          { label: 'Ciclos acumulados', value: device.cycleCount.toLocaleString('pt-BR') },
          { label: 'Ciclos médios (30d)', value: `${device.dailyCyclesMean30d}/dia` },
          { label: 'Dias quentes (30d)', value: `${device.hotDays30d}` },
          { label: 'Descargas profundas (30d)', value: `${device.deepDischargeEvents30d}` },
        ]}
      />

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 2 }}>
        <ChartCard title="SoH ao longo do tempo" subtitle="Últimos 30 dias de telemetria">
          <SohTrendChart data={sohSeries} label="SoH" unit="%" color={theme.palette.success.main} />
        </ChartCard>
        <ChartCard title="Temperatura ao longo do tempo" subtitle="Últimos 30 dias de telemetria">
          <SohTrendChart data={temperatureSeries} label="Temperatura" unit="°C" color={theme.palette.warning.main} />
        </ChartCard>
        <ChartCard title="RUL estimado ao longo do tempo" subtitle="Predições registradas pelo modelo">
          <SohTrendChart data={rulSeries} label="RUL previsto" unit=" ciclos" color={theme.palette.primary.main} />
        </ChartCard>
        <ChartCard
          title="Fatores associados à previsão"
          subtitle="Características com maior contribuição relativa para as decisões do modelo"
        >
          <FeatureImportanceChart features={data.featureImportances} height={240} />
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Esses valores não representam relações causais com a degradação da bateria.
          </Typography>
        </ChartCard>
      </Box>
    </Box>
  );
}
