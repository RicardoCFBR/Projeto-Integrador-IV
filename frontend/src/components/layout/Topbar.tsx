import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Box from '@mui/material/Box';
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined';

export function Topbar() {
  return (
    <AppBar position="sticky" color="inherit" sx={{ bgcolor: 'background.paper' }}>
      <Toolbar sx={{ gap: 2 }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Monitoramento Preditivo de Saúde de Baterias
        </Typography>
        <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
          <Typography variant="caption" color="text.secondary">
            Ambiente demonstrativo — dados sintéticos utilizados para validação da prova de conceito.
          </Typography>
        </Box>
        <Chip
          icon={<ScienceOutlinedIcon fontSize="small" />}
          label="PoC acadêmica"
          size="small"
          color="primary"
          variant="outlined"
        />
      </Toolbar>
    </AppBar>
  );
}
