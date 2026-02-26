/**
 * Loading Button Component
 *
 * Button with built-in loading state and spinner
 *
 * @example
 * ```tsx
 * <LoadingButton loading={isSubmitting} onClick={handleSubmit}>
 *   Submit Form
 * </LoadingButton>
 * ```
 */
import React from 'react';
import {
  Button as MuiButton,
  ButtonProps as MuiButtonProps,
  CircularProgress,
} from '@mui/material';

export interface LoadingButtonProps extends Omit<MuiButtonProps, 'disabled'> {
  /**
   * Whether the button is in a loading state
   */
  loading?: boolean;
  /**
   * Size of the loading spinner
   */
  loadingSize?: number;
}

export const LoadingButton: React.FC<LoadingButtonProps> = ({
  loading = false,
  loadingSize = 20,
  children,
  startIcon,
  endIcon,
  disabled,
  ...props
}) => {
  return (
    <MuiButton
      {...props}
      disabled={loading || disabled}
      startIcon={loading ? undefined : startIcon}
      endIcon={loading ? undefined : endIcon}
    >
      {loading ? (
        <>
          <CircularProgress
            size={loadingSize}
            color="inherit"
            sx={{ mr: 1 }}
          />
          {children}
        </>
      ) : (
        children
      )}
    </MuiButton>
  );
};

export default LoadingButton;
