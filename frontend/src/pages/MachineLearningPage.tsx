import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { ChartCard } from '../components/cards/ChartCard';
import { PredictionCard } from '../components/cards/PredictionCard';
import { FeatureImportanceChart } from '../components/charts/FeatureImportanceChart';
import { getModelInfo } from '../services/api';
import type { ModelInfo } from '../types/prediction';

const PIPELINE_STEPS = [
  'Telemetria',
  'Pré-processamento',
  'Feature Engineering',
  'Random Forest',
  'Predição de RUL',
  'Dashboard / Alertas',
];

export function MachineLearningPage() {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);

  useEffect(() => {
    getModelInfo().then(setModelInfo);
  }, []);

  if (!modelInfo) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Typography variant="h5">Machine Learning</Typography>

      <Card>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Fluxo da prova de conceito
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}>
            {PIPELINE_STEPS.map((step, index) => (
              <Box key={step} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label={step} variant="outlined" />
                {index < PIPELINE_STEPS.length - 1 ? (
                  <ArrowForwardIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                ) : null}
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>

      <PredictionCard modelInfo={modelInfo} />

      <Card>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Hiperparâmetros
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 2 }}>
            {Object.entries(modelInfo.hyperparameters).map(([key, value]) => (
              <Box key={key}>
                <Typography variant="caption" color="text.secondary">
                  {key}
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {String(value)}
                </Typography>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>

      <ChartCard
        title="Importância das características"
        subtitle="Contribuição relativa de cada variável nas decisões do modelo"
      >
        <FeatureImportanceChart features={modelInfo.featureImportances} />
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          A importância das características representa sua contribuição relativa nas decisões do modelo dentro do
          conjunto sintético utilizado na prova de conceito. Esses valores não representam relações causais.
        </Typography>
      </ChartCard>
    </Box>
  );
}
