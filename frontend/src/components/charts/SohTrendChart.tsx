import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export interface TrendPoint {
  date: string;
  value: number;
}

interface SohTrendChartProps {
  data: TrendPoint[];
  label: string;
  unit?: string;
  color?: string;
  height?: number;
}

/**
 * Gráfico de linha genérico para séries temporais (SoH, temperatura, RUL, ...).
 * Reutilizado nas telas de Dashboard e Detalhe do Dispositivo.
 */
export function SohTrendChart({ data, label, unit = '', color = '#1E4E8C', height = 260 }: SohTrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E2E5E9" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
        <YAxis tick={{ fontSize: 12 }} width={48} domain={['auto', 'auto']} />
        <Tooltip formatter={(value) => [`${value}${unit}`, label]} labelFormatter={(value) => `Data: ${value}`} />
        <Line type="monotone" dataKey="value" name={label} stroke={color} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
