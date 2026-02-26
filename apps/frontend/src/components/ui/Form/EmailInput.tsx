/**
 * Email Input Component
 *
 * Email input with icon
 *
 * @example
 * ```tsx
 * <EmailInput
 *   label="Email Address"
 *   name="email"
 *   value={formData.email}
 *   onChange={handleChange}
 *   required
 * />
 * ```
 */
import React from 'react';
import {
  TextField,
  TextFieldProps,
  InputAdornment,
} from '@mui/material';
import { Email } from '@mui/icons-material';

export interface EmailInputProps extends Omit<TextFieldProps, 'type' | 'variant'> {}

export const EmailInput: React.FC<EmailInputProps> = ({
  InputProps,
  ...props
}) => {
  const inputProps = {
    ...InputProps,
    startAdornment: (
      <InputAdornment position="start">
        <Email color="action" />
      </InputAdornment>
    ),
  };

  return (
    <TextField
      fullWidth
      margin="normal"
      type="email"
      {...props}
      InputProps={inputProps}
    />
  );
};

export default EmailInput;
