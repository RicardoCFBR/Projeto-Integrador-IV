import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

export interface DeviceMetricItem {
  label: string;
  value: string;
}

interface DeviceMetricsProps {
  items: DeviceMetricItem[];
}

export function DeviceMetrics({ items }: DeviceMetricsProps) {
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 2 }}>
      {items.map((item) => (
        <Paper key={item.label} variant="outlined" sx={{ p: 2 }}>
          <Typography variant="caption" color="text.secondary">
            {item.label}
          </Typography>
          <Typography variant="h6">{item.value}</Typography>
        </Paper>
      ))}
    </Box>
  );
}
