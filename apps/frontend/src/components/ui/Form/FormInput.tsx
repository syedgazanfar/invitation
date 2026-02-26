/**
 * Form Input Component
 *
 * Reusable text input with icon, label, and validation support
 *
 * @example
 * ```tsx
 * <FormInput
 *   label="Username"
 *   name="username"
 *   value={formData.username}
 *   onChange={handleChange}
 *   startIcon={<Person />}
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

export interface FormInputProps extends Omit<TextFieldProps, 'variant'> {
  /**
   * Icon to display at the start of the input
   */
  startIcon?: React.ReactNode;
  /**
   * Icon to display at the end of the input
   */
  endIcon?: React.ReactNode;
}

export const FormInput: React.FC<FormInputProps> = ({
  startIcon,
  endIcon,
  InputProps,
  ...props
}) => {
  const inputProps = {
    ...InputProps,
    ...(startIcon && {
      startAdornment: (
        <InputAdornment position="start">
          {startIcon}
        </InputAdornment>
      ),
    }),
    ...(endIcon && {
      endAdornment: (
        <InputAdornment position="end">
          {endIcon}
        </InputAdornment>
      ),
    }),
  };

  return (
    <TextField
      fullWidth
      margin="normal"
      {...props}
      InputProps={inputProps}
    />
  );
};

export default FormInput;
