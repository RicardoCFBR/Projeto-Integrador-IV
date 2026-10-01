import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ZAxis } from 'recharts';
import type { Device } from '../../types/device';

interface TemperatureRulChartProps {
  devices: Device[];
  height?: number;
}

export function TemperatureRulChart({ devices, height = 260 }: TemperatureRulChartProps) {
  const data = devices.map((device) => ({
    temperatura: device.temperatureMean30d,
    rul: device.predictedRulCycles,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E2E5E9" />
        <XAxis type="number" dataKey="temperatura" name="Temperatura média" unit="°C" tick={{ fontSize: 12 }} />
        <YAxis type="number" dataKey="rul" name="RUL previsto" unit=" ciclos" tick={{ fontSize: 12 }} width={56} />
        <ZAxis range={[36, 36]} />
        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
        <Scatter data={data} fill="#1E4E8C" fillOpacity={0.55} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
