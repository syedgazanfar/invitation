/**
 * Forgot Password Page
 *
 * Allows users to reset their password using OTP verification.
 */
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
} from '@mui/material';
import {
  Smartphone,
  LockReset,
  CheckCircle,
  ArrowForward,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { authApi } from '../../services/api';
import {
  AuthLayout,
  PhoneInput,
  PasswordInput,
  Alert,
  OTPInput,
} from '../../components/ui';

const steps = ['Enter Phone', 'Verify OTP', 'New Password', 'Complete'];

const ForgotPassword: React.FC = () => {
  const navigate = useNavigate();

  const [activeStep, setActiveStep] = useState(0);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const [sendingOTP, setSendingOTP] = useState(false);
  const [verifyingOTP, setVerifyingOTP] = useState(false);
  const [resettingPassword, setResettingPassword] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);

  // Resend timer countdown
  React.useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const validateStep = () => {
    if (activeStep === 0) {
      if (!phone || phone.length < 10) {
        setError('Please enter a valid phone number');
        return false;
      }
    }
    if (activeStep === 1) {
      if (!otp || otp.length !== 6) {
        setError('Please enter the 6-digit OTP code');
        return false;
      }
    }
    if (activeStep === 2) {
      if (!newPassword || newPassword.length < 8) {
        setError('Password must be at least 8 characters');
        return false;
      }
      if (newPassword !== confirmPassword) {
        setError('Passwords do not match');
        return false;
      }
    }
    return true;
  };

  const handleNext = async () => {
    if (!validateStep()) return;

    // Step 0 -> Step 1: Send OTP
    if (activeStep === 0) {
      await sendOTP();
    }
    // Step 1 -> Step 2: Verify OTP
    else if (activeStep === 1) {
      await verifyOTP();
    }
    // Step 2 -> Step 3: Reset Password
    else if (activeStep === 2) {
      await resetPassword();
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
    setError('');
  };

  const sendOTP = async () => {
    try {
      setSendingOTP(true);
      setError('');

      // Note: The API endpoint might be different - adjust based on your backend
      const response = await authApi.sendOTP(phone);

      if (response.success) {
        setActiveStep(1);
        setResendTimer(60);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to send OTP. Please check your phone number.');
    } finally {
      setSendingOTP(false);
    }
  };

  const verifyOTP = async () => {
    try {
      setVerifyingOTP(true);
      setError('');

      const response = await authApi.verifyOTP({
        phone: phone,
        otp: otp,
      });

      if (response.success) {
        setActiveStep(2);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Invalid OTP. Please try again.');
    } finally {
      setVerifyingOTP(false);
    }
  };

  const resetPassword = async () => {
    try {
      setResettingPassword(true);
      setError('');

      // Note: You may need to add this endpoint to your API service
      const response = await authApi.changePassword({
        old_password: '', // Not needed for forgot password flow
        new_password: newPassword,
        new_password_confirm: confirmPassword,
      });

      if (response.success) {
        setActiveStep(3);
        setTimeout(() => navigate('/login'), 3000);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to reset password. Please try again.');
    } finally {
      setResettingPassword(false);
    }
  };

  const resendOTP = async () => {
    if (resendTimer > 0) return;

    try {
      setSendingOTP(true);
      setError('');
      setOtp('');

      const response = await authApi.sendOTP(phone);

      if (response.success) {
        setResendTimer(60);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to resend OTP. Please try again.');
    } finally {
      setSendingOTP(false);
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Box textAlign="center" mb={4}>
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <LockReset sx={{ fontSize: 40, color: 'white' }} />
              </Box>
              <Typography variant="h6" gutterBottom>
                Reset Your Password
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Enter your phone number to receive an OTP
              </Typography>
            </Box>

            <PhoneInput
              label="Phone Number"
              value={phone}
              onChange={(e) => {
                setPhone(e.target.value);
                setError('');
              }}
              required
              placeholder="+91 98765 43210"
              helperText="Enter the phone number associated with your account"
              disabled={sendingOTP}
            />
          </Box>
        );

      case 1:
        return (
          <Box>
            <Box textAlign="center" mb={4}>
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <Smartphone sx={{ fontSize: 40, color: 'white' }} />
              </Box>
              <Typography variant="h6" gutterBottom>
                Verify Your Identity
              </Typography>
              <Typography variant="body2" color="text.secondary">
                We've sent a 6-digit code to
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {phone}
              </Typography>
            </Box>

            <OTPInput
              value={otp}
              onChange={setOtp}
              disabled={verifyingOTP}
              error={!!error}
              helperText={error || 'Enter the 6-digit code'}
            />

            <Box textAlign="center" mt={3}>
              {resendTimer > 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Resend code in {resendTimer}s
                </Typography>
              ) : (
                <Button
                  variant="text"
                  onClick={resendOTP}
                  disabled={sendingOTP}
                  startIcon={sendingOTP && <CircularProgress size={16} />}
                >
                  {sendingOTP ? 'Sending...' : 'Resend Code'}
                </Button>
              )}
            </Box>
          </Box>
        );

      case 2:
        return (
          <Box>
            <Box textAlign="center" mb={4}>
              <Typography variant="h6" gutterBottom>
                Create New Password
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Choose a strong password for your account
              </Typography>
            </Box>

            <PasswordInput
              label="New Password"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value);
                setError('');
              }}
              required
              helperText="At least 8 characters"
              disabled={resettingPassword}
            />

            <PasswordInput
              label="Confirm New Password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                setError('');
              }}
              required
              disabled={resettingPassword}
            />
          </Box>
        );

      case 3:
        return (
          <Box textAlign="center" py={4}>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200 }}
            >
              <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            </motion.div>
            <Typography variant="h5" fontWeight={600} gutterBottom>
              Password Reset Successful!
            </Typography>
            <Typography variant="body1" color="text.secondary" mb={2}>
              Your password has been updated.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Redirecting to login page...
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <AuthLayout
      title="Forgot Password"
      subtitle="Reset your account password"
      maxWidth="sm"
      gradientColors={['#667eea', '#764ba2']}
    >
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Alert
        severity="error"
        message={error}
        onClose={() => setError('')}
        open={!!error}
      />

      {renderStepContent()}

      {activeStep < 3 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            disabled={activeStep === 0 || sendingOTP || verifyingOTP || resettingPassword}
            onClick={handleBack}
          >
            Back
          </Button>
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={
              sendingOTP ||
              verifyingOTP ||
              resettingPassword ||
              (activeStep === 1 && otp.length !== 6)
            }
            endIcon={
              (sendingOTP || verifyingOTP || resettingPassword) ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <ArrowForward />
              )
            }
          >
            {sendingOTP
              ? 'Sending OTP...'
              : verifyingOTP
              ? 'Verifying...'
              : resettingPassword
              ? 'Resetting...'
              : activeStep === 2
              ? 'Reset Password'
              : 'Next'}
          </Button>
        </Box>
      )}

      {activeStep === 0 && (
        <Box textAlign="center" mt={3}>
          <Typography variant="body2" color="text.secondary">
            Remember your password?{' '}
            <Typography
              component={Link}
              to="/login"
              color="primary"
              fontWeight={600}
              sx={{ textDecoration: 'none' }}
            >
              Sign In
            </Typography>
          </Typography>
        </Box>
      )}
    </AuthLayout>
  );
};

export default ForgotPassword;
