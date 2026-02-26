/**
 * Alert Component
 *
 * Alert message with auto-dismiss functionality
 *
 * @example
 * ```tsx
 * <Alert
 *   severity="error"
 *   message="Invalid credentials"
 *   onClose={() => setError('')}
 * />
 * ```
 */
import React, { useEffect } from 'react';
import {
  Alert as MuiAlert,
  AlertProps as MuiAlertProps,
  AlertTitle,
  Collapse,
} from '@mui/material';

export interface AlertProps extends MuiAlertProps {
  /**
   * The alert message
   */
  message?: string;
  /**
   * Optional title
   */
  title?: string;
  /**
   * Auto-dismiss after this many milliseconds (0 = no auto-dismiss)
   */
  autoDismiss?: number;
  /**
   * Callback when alert is closed
   */
  onClose?: () => void;
  /**
   * Whether the alert is visible
   */
  open?: boolean;
}

export const Alert: React.FC<AlertProps> = ({
  message,
  title,
  autoDismiss = 0,
  onClose,
  open = true,
  children,
  ...props
}) => {
  useEffect(() => {
    if (autoDismiss > 0 && onClose) {
      const timer = setTimeout(() => {
        onClose();
      }, autoDismiss);
      return () => clearTimeout(timer);
    }
  }, [autoDismiss, onClose]);

  return (
    <Collapse in={open}>
      <MuiAlert
        {...props}
        onClose={onClose}
        sx={{ mb: 3, ...props.sx }}
      >
        {title && <AlertTitle>{title}</AlertTitle>}
        {message || children}
      </MuiAlert>
    </Collapse>
  );
};

export default Alert;
