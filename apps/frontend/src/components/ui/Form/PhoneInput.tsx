/**
 * Phone Input Component
 *
 * Phone number input with icon
 *
 * @example
 * ```tsx
 * <PhoneInput
 *   label="Phone Number"
 *   name="phone"
 *   value={formData.phone}
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
import { Phone } from '@mui/icons-material';

export interface PhoneInputProps extends Omit<TextFieldProps, 'type' | 'variant'> {}

export const PhoneInput: React.FC<PhoneInputProps> = ({
  placeholder = '+91 98765 43210',
  InputProps,
  ...props
}) => {
  const inputProps = {
    ...InputProps,
    startAdornment: (
      <InputAdornment position="start">
        <Phone color="action" />
      </InputAdornment>
    ),
  };

  return (
    <TextField
      fullWidth
      margin="normal"
      type="tel"
      placeholder={placeholder}
      {...props}
      InputProps={inputProps}
    />
  );
};

export default PhoneInput;
