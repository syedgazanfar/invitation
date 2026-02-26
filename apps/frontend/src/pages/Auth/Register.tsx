/**
 * Register Page
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
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import {
  Person,
  ArrowForward,
  CheckCircle,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../store/authStore';
import {
  AuthLayout,
  PhoneInput,
  EmailInput,
  FormInput,
  PasswordInput,
  Alert,
} from '../../components/ui';

const steps = ['Account Info', 'Personal Details', 'Complete'];

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading } = useAuthStore();

  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState({
    phone: '',
    username: '',
    email: '',
    full_name: '',
    password: '',
    password_confirm: '',
    agreeTerms: false,
  });
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked } = e.target;
    setFormData({ 
      ...formData, 
      [name]: name === 'agreeTerms' ? checked : value 
    });
    setError('');
  };

  const validateStep = () => {
    if (activeStep === 0) {
      if (!formData.phone || formData.phone.length < 10) {
        setError('Please enter a valid phone number');
        return false;
      }
      if (!formData.password || formData.password.length < 8) {
        setError('Password must be at least 8 characters');
        return false;
      }
      if (formData.password !== formData.password_confirm) {
        setError('Passwords do not match');
        return false;
      }
    }
    if (activeStep === 1) {
      if (!formData.username) {
        setError('Please enter a username');
        return false;
      }
      if (!formData.agreeTerms) {
        setError('Please agree to the terms and conditions');
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep()) {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep()) return;
    
    try {
      await register({
        phone: formData.phone,
        username: formData.username,
        email: formData.email,
        full_name: formData.full_name,
        password: formData.password,
        password_confirm: formData.password_confirm,
      });
      setActiveStep(2);
      setTimeout(() => navigate('/dashboard'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Registration failed. Please try again.');
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <PhoneInput
              label="Phone Number"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              required
              placeholder="+91 98765 43210"
              helperText="We'll send an OTP to verify your number"
            />

            <PasswordInput
              label="Password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              helperText="At least 8 characters"
            />

            <PasswordInput
              label="Confirm Password"
              name="password_confirm"
              value={formData.password_confirm}
              onChange={handleChange}
              required
            />
          </Box>
        );

      case 1:
        return (
          <Box>
            <FormInput
              label="Username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              startIcon={<Person color="action" />}
            />

            <FormInput
              label="Full Name"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="Optional"
              startIcon={<Person color="action" />}
            />

            <EmailInput
              label="Email Address"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Optional"
            />

            <FormControlLabel
              control={
                <Checkbox
                  name="agreeTerms"
                  checked={formData.agreeTerms}
                  onChange={handleChange}
                  required
                />
              }
              label={
                <Typography variant="body2">
                  I agree to the{' '}
                  <Link to="/terms" style={{ color: 'inherit' }}>
                    Terms of Service
                  </Link>
                  {' '}and{' '}
                  <Link to="/privacy" style={{ color: 'inherit' }}>
                    Privacy Policy
                  </Link>
                </Typography>
              }
              sx={{ mt: 2 }}
            />
          </Box>
        );

      case 2:
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
              Registration Complete!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Redirecting to your dashboard...
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <AuthLayout
      title="Create Account"
      subtitle="Join thousands of happy users"
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

      {activeStep < 2 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button disabled={activeStep === 0} onClick={handleBack}>
            Back
          </Button>
          {activeStep === steps.length - 2 ? (
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={isLoading}
              endIcon={<CheckCircle />}
            >
              {isLoading ? 'Creating Account...' : 'Complete Registration'}
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleNext}
              endIcon={<ArrowForward />}
            >
              Next
            </Button>
          )}
        </Box>
      )}

      {activeStep === 0 && (
        <Box textAlign="center" mt={3}>
          <Typography variant="body2" color="text.secondary">
            Already have an account?{' '}
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

export default Register;
