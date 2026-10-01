import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import type { SvgIconComponent } from '@mui/icons-material';

interface KpiCardProps {
  label: string;
  value: string;
  caption?: string;
  icon?: SvgIconComponent;
  accentColor?: string;
}

export function KpiCard({ label, value, caption, icon: Icon, accentColor }: KpiCardProps) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          {Icon ? (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 32,
                height: 32,
                borderRadius: '50%',
                bgcolor: accentColor ? `${accentColor}1A` : 'action.hover',
              }}
            >
              <Icon fontSize="small" sx={{ color: accentColor ?? 'text.secondary' }} />
            </Box>
          ) : null}
        </Box>
        <Typography variant="h5" sx={{ mt: 1 }}>
          {value}
        </Typography>
        {caption ? (
          <Typography variant="caption" color="text.secondary">
            {caption}
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  );
}
