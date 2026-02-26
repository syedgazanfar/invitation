/**
 * Password Input Component
 *
 * Password field with show/hide toggle
 *
 * @example
 * ```tsx
 * <PasswordInput
 *   label="Password"
 *   name="password"
 *   value={formData.password}
 *   onChange={handleChange}
 *   required
 * />
 * ```
 */
import React, { useState } from 'react';
import {
  TextField,
  TextFieldProps,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Visibility, VisibilityOff, Lock } from '@mui/icons-material';

export interface PasswordInputProps extends Omit<TextFieldProps, 'type' | 'variant'> {
  /**
   * Whether to show the lock icon
   */
  showLockIcon?: boolean;
}

export const PasswordInput: React.FC<PasswordInputProps> = ({
  showLockIcon = true,
  InputProps,
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false);

  const handleToggleVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  const inputProps = {
    ...InputProps,
    ...(showLockIcon && {
      startAdornment: (
        <InputAdornment position="start">
          <Lock color="action" />
        </InputAdornment>
      ),
    }),
    endAdornment: (
      <InputAdornment position="end">
        <IconButton
          onClick={handleToggleVisibility}
          edge="end"
          aria-label={showPassword ? 'Hide password' : 'Show password'}
          tabIndex={-1}
        >
          {showPassword ? <VisibilityOff /> : <Visibility />}
        </IconButton>
      </InputAdornment>
    ),
  };

  return (
    <TextField
      fullWidth
      margin="normal"
      type={showPassword ? 'text' : 'password'}
      {...props}
      InputProps={inputProps}
    />
  );
};

export default PasswordInput;
