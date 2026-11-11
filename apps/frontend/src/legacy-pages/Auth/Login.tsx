/**
 * Login Page
 */
import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Box, Typography, Divider } from '@mui/material';
import { Login as LoginIcon } from '@mui/icons-material';
import { useAuthStore } from '../../store/authStore';
import {
  AuthLayout,
  PhoneInput,
  PasswordInput,
  LoadingButton,
  Alert,
} from '../../components/ui';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading } = useAuthStore();

  const [formData, setFormData] = useState({
    phone: '',
    password: '',
  });
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      await login(formData.phone, formData.password);
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.message || 'Login failed. Please try again.');
    }
  };

  return (
    <AuthLayout
      title="Welcome Back"
      subtitle="Sign in to manage your invitations"
      maxWidth="sm"
    >
      <Alert
        severity="error"
        message={error}
        onClose={() => setError('')}
        open={!!error}
      />

      <form onSubmit={handleSubmit}>
        <PhoneInput
          label="Phone Number"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          required
          placeholder="+91 98765 43210"
        />

        <PasswordInput
          label="Password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          required
        />

        <Box textAlign="right" mt={1}>
          <Typography
            component={Link}
            to="/forgot-password"
            variant="body2"
            color="primary"
            sx={{ textDecoration: 'none' }}
          >
            Forgot Password?
          </Typography>
        </Box>

        <LoadingButton
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          loading={isLoading}
          startIcon={<LoginIcon />}
          sx={{ mt: 3, mb: 2, py: 1.5 }}
        >
          Sign In
        </LoadingButton>
      </form>

      <Divider sx={{ my: 3 }}>
        <Typography variant="body2" color="text.secondary">
          or
        </Typography>
      </Divider>

      <Box textAlign="center">
        <Typography variant="body2" color="text.secondary">
          Don't have an account?{' '}
          <Typography
            component={Link}
            to="/register"
            color="primary"
            fontWeight={600}
            sx={{ textDecoration: 'none' }}
          >
            Create Account
          </Typography>
        </Typography>
      </Box>
    </AuthLayout>
  );
};

export default Login;
