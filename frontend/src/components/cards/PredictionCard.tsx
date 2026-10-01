import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import type { ModelInfo } from '../../types/prediction';

interface PredictionCardProps {
  modelInfo: ModelInfo;
}

export function PredictionCard({ modelInfo }: PredictionCardProps) {
  return (
    <Card>
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          Modelo atual
        </Typography>
        <Typography variant="h6">{modelInfo.version}</Typography>
        <Typography variant="body2" color="text.secondary">
          {modelInfo.algorithm}
        </Typography>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              MAE
            </Typography>
            <Typography variant="h6">{modelInfo.metrics.maeCycles.toFixed(2)} ciclos</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              RMSE
            </Typography>
            <Typography variant="h6">{modelInfo.metrics.rmseCycles.toFixed(2)} ciclos</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              R²
            </Typography>
            <Typography variant="h6">{modelInfo.metrics.r2.toFixed(3)}</Typography>
          </Box>
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
          Métricas obtidas em conjunto sintético de teste da prova de conceito.
        </Typography>
      </CardContent>
    </Card>
  );
}
