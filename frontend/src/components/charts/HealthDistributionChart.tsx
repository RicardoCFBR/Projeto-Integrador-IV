import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { useTheme } from '@mui/material/styles';
import type { DashboardSummary } from '../../services/api';

interface HealthDistributionChartProps {
  summary: DashboardSummary;
  height?: number;
}

export function HealthDistributionChart({ summary, height = 260 }: HealthDistributionChartProps) {
  const theme = useTheme();

  const data = [
    { name: 'Saudável', value: summary.healthyCount, color: theme.palette.success.main },
    { name: 'Atenção', value: summary.attentionCount, color: theme.palette.warning.main },
    { name: 'Risco', value: summary.riskCount, color: theme.palette.error.main },
  ];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={58} outerRadius={88} paddingAngle={2}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
        <Legend verticalAlign="bottom" height={32} />
      </PieChart>
    </ResponsiveContainer>
  );
}
