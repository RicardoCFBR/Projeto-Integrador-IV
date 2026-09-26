import { createTheme } from '@mui/material/styles';

export const SIDEBAR_BACKGROUND = '#111827';
export const SIDEBAR_BACKGROUND_HOVER = '#1F2937';
export const SIDEBAR_TEXT = '#CBD5E1';
export const SIDEBAR_TEXT_ACTIVE = '#FFFFFF';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1E4E8C',
    },
    background: {
      default: '#F3F5F7',
      paper: '#FFFFFF',
    },
    success: {
      main: '#2E7D32',
    },
    warning: {
      main: '#ED6C02',
    },
    error: {
      main: '#D32F2F',
    },
    text: {
      primary: '#1A2027',
      secondary: '#5B6470',
    },
  },
  shape: {
    borderRadius: 8,
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'Segoe UI',
      'Roboto',
      'Helvetica',
      'Arial',
      'sans-serif',
    ].join(','),
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#F3F5F7',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          border: '1px solid #E2E5E9',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          borderBottom: '1px solid #E2E5E9',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
          color: '#5B6470',
          backgroundColor: '#F9FAFB',
        },
      },
    },
  },
});
