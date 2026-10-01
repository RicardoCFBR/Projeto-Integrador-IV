import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import type { Device } from '../../types/device';

const BUCKETS = [
  { label: '< 500', min: -Infinity, max: 500 },
  { label: '500–800', min: 500, max: 800 },
  { label: '800–1100', min: 800, max: 1100 },
  { label: '1100–1400', min: 1100, max: 1400 },
  { label: '> 1400', min: 1400, max: Infinity },
];

interface RulDistributionChartProps {
  devices: Device[];
  height?: number;
}

export function RulDistributionChart({ devices, height = 260 }: RulDistributionChartProps) {
  const data = BUCKETS.map((bucket) => ({
    range: bucket.label,
    dispositivos: devices.filter(
      (device) => device.predictedRulCycles >= bucket.min && device.predictedRulCycles < bucket.max,
    ).length,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E2E5E9" />
        <XAxis dataKey="range" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} width={40} allowDecimals={false} />
        <Tooltip formatter={(value) => [value, 'Dispositivos']} />
        <Bar dataKey="dispositivos" fill="#1E4E8C" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
