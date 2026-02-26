/**
 * Loading Spinner Component
 *
 * Centered loading indicator
 *
 * @example
 * ```tsx
 * <LoadingSpinner message="Loading..." />
 * ```
 */
import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
} from '@mui/material';

export interface LoadingSpinnerProps {
  /**
   * Size of the spinner
   */
  size?: number;
  /**
   * Optional loading message
   */
  message?: string;
  /**
   * Whether to center the spinner
   */
  centered?: boolean;
  /**
   * Minimum height for centered spinner
   */
  minHeight?: string | number;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 40,
  message,
  centered = true,
  minHeight = 200,
}) => {
  const content = (
    <>
      <CircularProgress size={size} />
      {message && (
        <Typography
          variant="body2"
          color="text.secondary"
          mt={2}
        >
          {message}
        </Typography>
      )}
    </>
  );

  if (centered) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight={minHeight}
      >
        {content}
      </Box>
    );
  }

  return content;
};

export default LoadingSpinner;
