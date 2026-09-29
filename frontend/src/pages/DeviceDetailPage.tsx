import { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined';
import { useTheme } from '@mui/material/styles';
import { DeviceStatusCard } from '../components/cards/DeviceStatusCard';
import { ChartCard } from '../components/cards/ChartCard';
import { DeviceMetrics } from '../components/devices/DeviceMetrics';
import { SohTrendChart } from '../components/charts/SohTrendChart';
import { FeatureImportanceChart } from '../components/charts/FeatureImportanceChart';
import { getDeviceById, getDeviceTelemetryHistory, getModelInfo } from '../services/api';
import type { Device, DeviceTelemetryPoint } from '../types/device';
import type { FeatureImportance } from '../types/prediction';

export function DeviceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const theme = useTheme();

  const [device, setDevice] = useState<Device | undefined>(undefined);
  const [history, setHistory] = useState<DeviceTelemetryPoint[]>([]);
  const [featureImportances, setFeatureImportances] = useState<FeatureImportance[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    let isMounted = true;
    setIsLoading(true);

    Promise.all([getDeviceById(id), getDeviceTelemetryHistory(id), getModelInfo()]).then(
      ([deviceResult, historyResult, modelInfo]) => {
        if (!isMounted) return;
        setDevice(deviceResult);
        setHistory(historyResult);
        setFeatureImportances(modelInfo.featureImportances.slice(0, 6));
        setIsLoading(false);
      },
    );

    return () => {
      isMounted = false;
    };
  }, [id]);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!device) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'flex-start' }}>
        <Alert severity="warning">Dispositivo "{id}" não foi encontrado.</Alert>
        <Button component={RouterLink} to="/devices" startIcon={<ArrowBackOutlinedIcon />}>
          Voltar para Dispositivos
        </Button>
      </Box>
    );
  }

  const sohSeries = history.map((point) => ({ date: point.date, value: point.sohPercent }));
  const temperatureSeries = history.map((point) => ({ date: point.date, value: point.temperatureMeanC }));
  const rulSeries = history.map((point) => ({ date: point.date, value: point.predictedRulCycles }));

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Button
        component={RouterLink}
        to="/devices"
        startIcon={<ArrowBackOutlinedIcon />}
        size="small"
        sx={{ alignSelf: 'flex-start' }}
      >
        Voltar para Dispositivos
      </Button>

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
        <ChartCard title="SoH ao longo do tempo" subtitle="Últimos 30 dias">
          <SohTrendChart data={sohSeries} label="SoH" unit="%" color={theme.palette.success.main} />
        </ChartCard>
        <ChartCard title="Temperatura ao longo do tempo" subtitle="Últimos 30 dias">
          <SohTrendChart data={temperatureSeries} label="Temperatura" unit="°C" color={theme.palette.warning.main} />
        </ChartCard>
        <ChartCard title="RUL estimado ao longo do tempo" subtitle="Últimos 30 dias">
          <SohTrendChart data={rulSeries} label="RUL previsto" unit=" ciclos" color={theme.palette.primary.main} />
        </ChartCard>
        <ChartCard
          title="Fatores associados à previsão"
          subtitle="Características com maior contribuição relativa para as decisões do modelo"
        >
          <FeatureImportanceChart features={featureImportances} height={240} />
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Esses valores não representam relações causais com a degradação da bateria.
          </Typography>
        </ChartCard>
      </Box>
    </Box>
  );
}
