import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import type { FeatureImportance } from '../../types/prediction';

interface FeatureImportanceChartProps {
  features: FeatureImportance[];
  height?: number;
}

export function FeatureImportanceChart({ features, height = 280 }: FeatureImportanceChartProps) {
  const data = [...features]
    .sort((a, b) => b.importance - a.importance)
    .map((item) => ({ feature: item.feature, percentual: Math.round(item.importance * 1000) / 10 }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, left: 24, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E2E5E9" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 12 }} unit="%" />
        <YAxis type="category" dataKey="feature" width={190} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(value) => [`${value}%`, 'Importância']} />
        <Bar dataKey="percentual" fill="#1E4E8C" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
