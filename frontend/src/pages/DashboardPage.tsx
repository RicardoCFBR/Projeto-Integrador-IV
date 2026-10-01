import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import PhoneIphoneOutlinedIcon from '@mui/icons-material/PhoneIphoneOutlined';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import ErrorOutlineOutlinedIcon from '@mui/icons-material/ErrorOutlineOutlined';
import BatteryChargingFullOutlinedIcon from '@mui/icons-material/BatteryChargingFullOutlined';
import ThermostatOutlinedIcon from '@mui/icons-material/ThermostatOutlined';
import { useTheme } from '@mui/material/styles';
import { KpiCard } from '../components/cards/KpiCard';
import { ChartCard } from '../components/cards/ChartCard';
import { HealthDistributionChart } from '../components/charts/HealthDistributionChart';
import { RulDistributionChart } from '../components/charts/RulDistributionChart';
import { SohTrendChart } from '../components/charts/SohTrendChart';
import { TemperatureRulChart } from '../components/charts/TemperatureRulChart';
import { getDashboardSummary, getDevices, getFleetSohTrend, type DashboardSummary } from '../services/api';
import type { Device } from '../types/device';

export function DashboardPage() {
  const theme = useTheme();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [sohTrend, setSohTrend] = useState<{ date: string; value: number }[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    Promise.all([getDashboardSummary(), getDevices(), getFleetSohTrend()]).then(
      ([summaryResult, devicesResult, trendResult]) => {
        if (!isMounted) return;
        setSummary(summaryResult);
        setDevices(devicesResult);
        setSohTrend(trendResult.map((point) => ({ date: point.date, value: point.sohPercent })));
        setIsLoading(false);
      },
    );

    return () => {
      isMounted = false;
    };
  }, []);

  if (isLoading || !summary) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Alert severity="info" variant="outlined">
        Ambiente demonstrativo — dados sintéticos utilizados para validação da prova de conceito.
      </Alert>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
          gap: 2,
        }}
      >
        <KpiCard
          label="Dispositivos monitorados"
          value={summary.totalDevices.toLocaleString('pt-BR')}
          icon={PhoneIphoneOutlinedIcon}
          accentColor={theme.palette.primary.main}
        />
        <KpiCard
          label="Dispositivos saudáveis"
          value={summary.healthyCount.toLocaleString('pt-BR')}
          caption={`${summary.healthyPercent}%`}
          icon={CheckCircleOutlineIcon}
          accentColor={theme.palette.success.main}
        />
        <KpiCard
          label="Dispositivos em atenção"
          value={summary.attentionCount.toLocaleString('pt-BR')}
          caption={`${summary.attentionPercent}%`}
          icon={WarningAmberOutlinedIcon}
          accentColor={theme.palette.warning.main}
        />
        <KpiCard
          label="Dispositivos em risco"
          value={summary.riskCount.toLocaleString('pt-BR')}
          caption={`${summary.riskPercent}%`}
          icon={ErrorOutlineOutlinedIcon}
          accentColor={theme.palette.error.main}
        />
        <KpiCard
          label="RUL médio da frota"
          value={`${summary.averageRulCycles.toLocaleString('pt-BR')} ciclos`}
          icon={BatteryChargingFullOutlinedIcon}
          accentColor={theme.palette.primary.main}
        />
        <KpiCard
          label="Temperatura média"
          value={`${summary.averageTemperatureC}°C`}
          icon={ThermostatOutlinedIcon}
          accentColor={theme.palette.primary.main}
        />
      </Box>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
          gap: 2,
        }}
      >
        <ChartCard title="Distribuição da saúde da bateria">
          <HealthDistributionChart summary={summary} />
        </ChartCard>
        <ChartCard title="Distribuição do RUL previsto" subtitle="Faixas de ciclos restantes por dispositivo">
          <RulDistributionChart devices={devices} />
        </ChartCard>
        <ChartCard title="Evolução média do SoH" subtitle="Últimos 30 dias — média da frota">
          <SohTrendChart data={sohTrend} label="SoH" unit="%" color={theme.palette.primary.main} />
        </ChartCard>
        <ChartCard title="Temperatura × RUL" subtitle="Temperatura média (30d) vs. RUL previsto">
          <TemperatureRulChart devices={devices} />
        </ChartCard>
      </Box>
    </Box>
  );
}
