import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3861fb',
      light: '#5c7cfc',
      dark: '#2847d9',
    },
    secondary: {
      main: '#9c4bff',
      light: '#b06fff',
      dark: '#7c3acc',
    },
    background: {
      default: '#0b0e11',
      paper: '#1e2329',
    },
    success: {
      main: '#0ecb81',
      light: '#2ed99a',
      dark: '#0aa868',
    },
    error: {
      main: '#f6465d',
      light: '#f76b7e',
      dark: '#d63648',
    },
    warning: {
      main: '#f0b90b',
      light: '#f2c73c',
      dark: '#d1a009',
    },
    info: {
      main: '#3861fb',
      light: '#5c7cfc',
      dark: '#2847d9',
    },
    text: {
      primary: '#eaecef',
      secondary: '#b7bdc6',
      disabled: '#5e6673',
    },
    divider: '#2b3139',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
    body1: {
      fontSize: '0.875rem',
    },
    body2: {
      fontSize: '0.75rem',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8,
          transition: 'all 0.3s ease',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          borderRadius: 6,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

export const glassmorphismStyle = {
  backgroundColor: 'rgba(30, 35, 41, 0.6)',
  backdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.05)',
  boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
};
