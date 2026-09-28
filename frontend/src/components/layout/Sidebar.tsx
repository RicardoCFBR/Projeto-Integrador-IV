import { Link, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import PhoneIphoneOutlinedIcon from '@mui/icons-material/PhoneIphoneOutlined';
import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined';
import NotificationsActiveOutlinedIcon from '@mui/icons-material/NotificationsActiveOutlined';
import MemoryOutlinedIcon from '@mui/icons-material/MemoryOutlined';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import BatteryChargingFullOutlinedIcon from '@mui/icons-material/BatteryChargingFullOutlined';
import {
  SIDEBAR_BACKGROUND,
  SIDEBAR_BACKGROUND_HOVER,
  SIDEBAR_TEXT,
  SIDEBAR_TEXT_ACTIVE,
} from '../../theme/theme';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard', icon: DashboardOutlinedIcon },
  { label: 'Dispositivos', path: '/devices', icon: PhoneIphoneOutlinedIcon },
  { label: 'Predições', path: '/predictions', icon: InsightsOutlinedIcon },
  { label: 'Alertas', path: '/alerts', icon: NotificationsActiveOutlinedIcon },
  { label: 'Machine Learning', path: '/ml', icon: MemoryOutlinedIcon },
  { label: 'Sobre a PoC', path: '/about', icon: InfoOutlinedIcon },
];

const DRAWER_WIDTH = 248;

export function Sidebar() {
  const location = useLocation();

  return (
    <Box
      component="nav"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        position: 'sticky',
        top: 0,
        height: '100vh',
        bgcolor: SIDEBAR_BACKGROUND,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2.5, py: 2.5 }}>
        <BatteryChargingFullOutlinedIcon sx={{ color: SIDEBAR_TEXT_ACTIVE }} />
        <Typography variant="subtitle1" sx={{ color: SIDEBAR_TEXT_ACTIVE, fontWeight: 700, lineHeight: 1.2 }}>
          Battery Health
          <Typography component="span" variant="caption" sx={{ display: 'block', color: SIDEBAR_TEXT }}>
            Monitoramento preditivo
          </Typography>
        </Typography>
      </Box>

      <List sx={{ px: 1.5, flexGrow: 1 }}>
        {NAV_ITEMS.map(({ label, path, icon: Icon }) => {
          const isActive = location.pathname.startsWith(path);
          return (
            <ListItemButton
              key={path}
              component={Link}
              to={path}
              selected={isActive}
              sx={{
                borderRadius: 1.5,
                mb: 0.5,
                color: isActive ? SIDEBAR_TEXT_ACTIVE : SIDEBAR_TEXT,
                '&:hover': { bgcolor: SIDEBAR_BACKGROUND_HOVER },
                '&.Mui-selected': {
                  bgcolor: SIDEBAR_BACKGROUND_HOVER,
                  color: SIDEBAR_TEXT_ACTIVE,
                },
                '&.Mui-selected:hover': { bgcolor: SIDEBAR_BACKGROUND_HOVER },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: 'inherit' }}>
                <Icon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={label}
                slotProps={{ primary: { sx: { fontSize: 14, fontWeight: isActive ? 600 : 500 } } }}
              />
            </ListItemButton>
          );
        })}
      </List>

      <Typography variant="caption" sx={{ color: SIDEBAR_TEXT, px: 2.5, py: 2, opacity: 0.7 }}>
        Projeto Integrador IV — UNIVESP
      </Typography>
    </Box>
  );
}
