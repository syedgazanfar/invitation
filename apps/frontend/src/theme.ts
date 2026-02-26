/**
 * Material-UI Theme Configuration
 * Color Palette:
 * - Deep Red: #A61E2A (Buttons / CTAs)
 * - Off-White: #F5F2ED (Background)
 * - Charcoal Gray: #2E2E2E (Headings)
 * - Light Gray: #D9D9D9 (Borders / dividers)
 */
import { createTheme, ThemeOptions } from '@mui/material/styles';

// Define custom colors
const colors = {
  deepRed: '#A61E2A',
  deepRedDark: '#8a1823',
  deepRedLight: '#c42835',
  offWhite: '#F5F2ED',
  charcoal: '#2E2E2E',
  lightGray: '#D9D9D9',
  mediumGray: '#999999',
};

// Create base theme
const baseTheme: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: colors.deepRed,
      light: colors.deepRedLight,
      dark: colors.deepRedDark,
      contrastText: colors.offWhite,
    },
    secondary: {
      main: colors.charcoal,
      light: '#4a4a4a',
      dark: '#1a1a1a',
      contrastText: colors.offWhite,
    },
    background: {
      default: colors.offWhite,
      paper: '#ffffff',
    },
    text: {
      primary: colors.charcoal,
      secondary: '#666666',
    },
    divider: colors.lightGray,
  },
  typography: {
    fontFamily: '"Poppins", "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '3rem',
      lineHeight: 1.2,
      color: colors.charcoal,
    },
    h2: {
      fontWeight: 600,
      fontSize: '2.25rem',
      lineHeight: 1.3,
      color: colors.charcoal,
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.875rem',
      lineHeight: 1.4,
      color: colors.charcoal,
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.4,
      color: colors.charcoal,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.5,
      color: colors.charcoal,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
      lineHeight: 1.5,
      color: colors.charcoal,
    },
    subtitle1: {
      fontSize: '1.125rem',
      fontWeight: 500,
      color: colors.charcoal,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      color: colors.mediumGray,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      color: colors.charcoal,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
      color: '#666666',
    },
    button: {
      fontWeight: 600,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 24px',
          fontSize: '1rem',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(166, 30, 42, 0.3)',
          },
        },
        contained: {
          backgroundColor: colors.deepRed,
          color: colors.offWhite,
          '&:hover': {
            backgroundColor: colors.deepRedDark,
            boxShadow: '0 6px 20px rgba(166, 30, 42, 0.4)',
          },
        },
        outlined: {
          borderColor: colors.deepRed,
          color: colors.deepRed,
          '&:hover': {
            backgroundColor: 'rgba(166, 30, 42, 0.05)',
            borderColor: colors.deepRedDark,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
          border: `1px solid ${colors.lightGray}`,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            backgroundColor: '#ffffff',
            '& fieldset': {
              borderColor: colors.lightGray,
            },
            '&:hover fieldset': {
              borderColor: colors.mediumGray,
            },
            '&.Mui-focused fieldset': {
              borderColor: colors.deepRed,
            },
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: colors.charcoal,
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
          borderBottom: `1px solid ${colors.lightGray}`,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: 500,
        },
        filled: {
          backgroundColor: 'rgba(166, 30, 42, 0.1)',
          color: colors.deepRed,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: `1px solid ${colors.lightGray}`,
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: colors.lightGray,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          border: `1px solid ${colors.lightGray}`,
        },
      },
    },
  },
};

// Create the theme
export const theme = createTheme(baseTheme);

// Template-specific themes using the same palette
export const weddingTheme = createTheme({
  ...baseTheme,
  palette: {
    ...baseTheme.palette,
    primary: {
      main: colors.deepRed,
      light: colors.deepRedLight,
      dark: colors.deepRedDark,
      contrastText: colors.offWhite,
    },
  },
});

export const birthdayTheme = createTheme({
  ...baseTheme,
  palette: {
    ...baseTheme.palette,
    primary: {
      main: colors.deepRed,
      light: colors.deepRedLight,
      dark: colors.deepRedDark,
      contrastText: colors.offWhite,
    },
    secondary: {
      main: colors.charcoal,
      contrastText: colors.offWhite,
    },
  },
});

export default theme;
