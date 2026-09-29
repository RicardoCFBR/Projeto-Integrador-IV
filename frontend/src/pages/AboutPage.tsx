import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';

const SECTIONS: { title: string; body: string }[] = [
  {
    title: 'Problema',
    body: 'O monitoramento de baterias em frotas corporativas de smartphones tende a ser majoritariamente reativo, identificando degradações apenas quando já afetam o uso do dispositivo.',
  },
  {
    title: 'Objetivo',
    body: 'Antecipar sinais de degradação da bateria utilizando telemetria histórica e aprendizado de máquina, permitindo ações preventivas antes de falhas ou perda relevante de autonomia.',
  },
  {
    title: 'Dados',
    body: 'Nesta fase foram utilizados dados sintéticos, gerados de forma parametrizada, para validar o pipeline técnico de ponta a ponta antes de qualquer integração com telemetria real.',
  },
  {
    title: 'Modelo',
    body: 'Um RandomForestRegressor é utilizado para estimar o RUL (Remaining Useful Life — vida útil restante) de cada dispositivo a partir de variáveis de temperatura, ciclos de carga e uso.',
  },
  {
    title: 'Limitações',
    body: 'Os resultados apresentados ainda não foram validados sobre uma frota real e não devem ser interpretados como diagnóstico operacional de dispositivos em produção.',
  },
  {
    title: 'Próxima evolução',
    body: 'As próximas etapas incluem a integração com telemetria real de dispositivos, validação operacional dos resultados e evolução do backend e da API que hoje são simulados pela camada de mocks do frontend.',
  },
];

export function AboutPage() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, maxWidth: 820 }}>
      <Typography variant="h5">Sobre a PoC</Typography>

      {SECTIONS.map((section) => (
        <Card key={section.title}>
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              {section.title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {section.body}
            </Typography>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
}
