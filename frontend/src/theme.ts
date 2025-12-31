import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#0056b3', // deep blue, you can customize
    },
    secondary: {
      main: '#009688', // teal
    },
    background: {
      default: '#f5f7fa',
      paper: '#fff'
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
    h3: { fontWeight: 700, letterSpacing: 0.5 },
    h4: { fontWeight: 700 },
    h6: { fontWeight: 700 },
    subtitle1: { fontWeight: 500 }
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 8, fontWeight: 600 },
      }
    },
    MuiPaper: {
      styleOverrides: {
        root: { borderRadius: 12 }
      }
    },
  },
});

export default theme;

