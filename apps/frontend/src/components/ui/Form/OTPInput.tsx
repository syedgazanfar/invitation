/**
 * OTP Input Component
 *
 * A component for entering 6-digit OTP codes with auto-focus and paste support.
 */
import React, { useRef, useState, KeyboardEvent, ClipboardEvent } from 'react';
import { Box, TextField, Typography } from '@mui/material';

interface OTPInputProps {
  length?: number;
  value: string;
  onChange: (otp: string) => void;
  error?: boolean;
  helperText?: string;
  disabled?: boolean;
}

const OTPInput: React.FC<OTPInputProps> = ({
  length = 6,
  value,
  onChange,
  error = false,
  helperText,
  disabled = false,
}) => {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const [otp, setOtp] = useState<string[]>(value.split('').slice(0, length));

  React.useEffect(() => {
    setOtp(value.split('').slice(0, length));
  }, [value, length]);

  const handleChange = (index: number, newValue: string) => {
    // Only allow digits
    if (newValue && !/^\d$/.test(newValue)) return;

    const newOtp = [...otp];
    newOtp[index] = newValue;
    setOtp(newOtp);

    // Call parent onChange
    onChange(newOtp.join(''));

    // Auto-focus next input
    if (newValue && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLDivElement>) => {
    // Handle backspace
    if (e.key === 'Backspace') {
      if (!otp[index] && index > 0) {
        // Move to previous input if current is empty
        inputRefs.current[index - 1]?.focus();
      } else {
        // Clear current input
        const newOtp = [...otp];
        newOtp[index] = '';
        setOtp(newOtp);
        onChange(newOtp.join(''));
      }
    }
    // Handle left arrow
    else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    // Handle right arrow
    else if (e.key === 'ArrowRight' && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLDivElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text/plain').trim();

    // Only process if it's all digits
    if (!/^\d+$/.test(pastedData)) return;

    const digits = pastedData.slice(0, length).split('');
    const newOtp = [...otp];

    digits.forEach((digit, i) => {
      newOtp[i] = digit;
    });

    setOtp(newOtp);
    onChange(newOtp.join(''));

    // Focus the next empty input or last input
    const nextEmptyIndex = newOtp.findIndex((digit) => !digit);
    if (nextEmptyIndex !== -1) {
      inputRefs.current[nextEmptyIndex]?.focus();
    } else {
      inputRefs.current[length - 1]?.focus();
    }
  };

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          gap: 1,
          justifyContent: 'center',
          mb: helperText ? 1 : 0,
        }}
      >
        {Array.from({ length }).map((_, index) => (
          <TextField
            key={index}
            inputRef={(el) => (inputRefs.current[index] = el)}
            value={otp[index] || ''}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e as any)}
            onPaste={handlePaste}
            disabled={disabled}
            error={error}
            inputProps={{
              maxLength: 1,
              style: {
                textAlign: 'center',
                fontSize: '1.5rem',
                fontWeight: 600,
                padding: '12px 0',
              },
            }}
            sx={{
              width: 50,
              '& input': {
                textAlign: 'center',
              },
            }}
          />
        ))}
      </Box>
      {helperText && (
        <Typography
          variant="caption"
          color={error ? 'error' : 'text.secondary'}
          sx={{ display: 'block', textAlign: 'center', mt: 1 }}
        >
          {helperText}
        </Typography>
      )}
    </Box>
  );
};

export default OTPInput;
