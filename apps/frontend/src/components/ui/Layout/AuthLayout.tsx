/**
 * Auth Layout Component
 *
 * Standard layout for authentication pages (Login, Register, etc.)
 *
 * @example
 * ```tsx
 * <AuthLayout
 *   title="Welcome Back"
 *   subtitle="Sign in to manage your invitations"
 *   maxWidth="sm"
 * >
 *   <LoginForm />
 * </AuthLayout>
 * ```
 */
import React from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  useTheme,
} from '@mui/material';
import { motion } from 'framer-motion';

export interface AuthLayoutProps {
  /**
   * Page title
   */
  title?: string;
  /**
   * Page subtitle
   */
  subtitle?: string;
  /**
   * Maximum width of the form container
   */
  maxWidth?: 'xs' | 'sm' | 'md';
  /**
   * Background gradient colors
   */
  gradientColors?: [string, string];
  /**
   * Content to display
   */
  children: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  title,
  subtitle,
  maxWidth = 'sm',
  gradientColors,
  children,
}) => {
  const theme = useTheme();

  const defaultGradient = [
    `${theme.palette.primary.main}10`,
    `${theme.palette.secondary.main}10`,
  ];

  const [color1, color2] = gradientColors || defaultGradient;

  return (
    <Box
      sx={{
        minHeight: 'calc(100vh - 64px)',
        display: 'flex',
        alignItems: 'center',
        py: 8,
        background: `linear-gradient(135deg, ${color1} 0%, ${color2} 100%)`,
      }}
    >
      <Container maxWidth={maxWidth}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Paper elevation={0} sx={{ p: { xs: 3, md: 5 }, borderRadius: 4 }}>
            {(title || subtitle) && (
              <Box textAlign="center" mb={4}>
                {title && (
                  <Typography variant="h4" fontWeight={700} gutterBottom>
                    {title}
                  </Typography>
                )}
                {subtitle && (
                  <Typography variant="body1" color="text.secondary">
                    {subtitle}
                  </Typography>
                )}
              </Box>
            )}

            {children}
          </Paper>
        </motion.div>
      </Container>
    </Box>
  );
};

export default AuthLayout;
