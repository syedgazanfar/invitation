/**
 * User Profile Page
 *
 * Allows users to view and edit their account information.
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Divider,
  Avatar,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert as MuiAlert,
} from '@mui/material';
import {
  Person,
  Email,
  Phone,
  Edit,
  Lock,
  Delete,
  CheckCircle,
  Cancel,
  Save,
} from '@mui/icons-material';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../services/api';
import {
  FormInput,
  EmailInput,
  PhoneInput,
  PasswordInput,
  Alert,
  LoadingSpinner,
} from '../../components/ui';

const Profile: React.FC = () => {
  const { user, loadUser } = useAuthStore();

  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [deleteAccountOpen, setDeleteAccountOpen] = useState(false);

  // Form states
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
  });

  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      setLoading(true);
      await loadUser();
      if (user) {
        setFormData({
          username: user.username || '',
          email: user.email || '',
          full_name: user.full_name || '',
        });
      }
    } catch (err) {
      console.error('Failed to load user data:', err);
      setError('Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    setError('');
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordData({ ...passwordData, [name]: value });
    setError('');
  };

  const handleSaveProfile = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');

      const response = await authApi.updateProfile(formData);

      if (response.success) {
        setSuccess('Profile updated successfully');
        setEditMode(false);
        await loadUser(); // Refresh user data
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    try {
      if (passwordData.new_password.length < 8) {
        setError('Password must be at least 8 characters');
        return;
      }
      if (passwordData.new_password !== passwordData.new_password_confirm) {
        setError('New passwords do not match');
        return;
      }

      setSaving(true);
      setError('');
      setSuccess('');

      const response = await authApi.changePassword(passwordData);

      if (response.success) {
        setSuccess('Password changed successfully');
        setChangePasswordOpen(false);
        setPasswordData({
          old_password: '',
          new_password: '',
          new_password_confirm: '',
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditMode(false);
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || '',
        full_name: user.full_name || '',
      });
    }
    setError('');
  };

  if (loading || !user) {
    return <LoadingSpinner />;
  }

  const getInitials = () => {
    if (user.full_name) {
      return user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    return user.username.slice(0, 2).toUpperCase();
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight={700}>
        My Profile
      </Typography>

      {/* Success/Error Alerts */}
      {success && (
        <MuiAlert severity="success" onClose={() => setSuccess('')} sx={{ mb: 3 }}>
          {success}
        </MuiAlert>
      )}
      {error && !changePasswordOpen && (
        <MuiAlert severity="error" onClose={() => setError('')} sx={{ mb: 3 }}>
          {error}
        </MuiAlert>
      )}

      <Grid container spacing={3}>
        {/* Profile Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <Avatar
                sx={{
                  width: 100,
                  height: 100,
                  mx: 'auto',
                  mb: 2,
                  bgcolor: 'primary.main',
                  fontSize: '2rem',
                  fontWeight: 700,
                }}
              >
                {getInitials()}
              </Avatar>

              <Typography variant="h6" fontWeight={600} gutterBottom>
                {user.full_name || user.username}
              </Typography>

              <Typography variant="body2" color="text.secondary" gutterBottom>
                @{user.username}
              </Typography>

              <Box sx={{ mt: 2, mb: 3, display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                {user.is_phone_verified && (
                  <Chip
                    icon={<CheckCircle />}
                    label="Verified"
                    size="small"
                    color="success"
                  />
                )}
                {user.current_plan && (
                  <Chip
                    label={user.current_plan.name}
                    size="small"
                    color="primary"
                  />
                )}
                {user.is_blocked && (
                  <Chip
                    icon={<Cancel />}
                    label="Blocked"
                    size="small"
                    color="error"
                  />
                )}
              </Box>

              <Typography variant="caption" color="text.secondary">
                Member since {new Date(user.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Quick Actions
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Lock />}
                  onClick={() => setChangePasswordOpen(true)}
                >
                  Change Password
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  color="error"
                  startIcon={<Delete />}
                  onClick={() => setDeleteAccountOpen(true)}
                >
                  Delete Account
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Profile Information */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" fontWeight={600}>
                  Profile Information
                </Typography>
                {!editMode ? (
                  <Button
                    variant="outlined"
                    startIcon={<Edit />}
                    onClick={() => setEditMode(true)}
                  >
                    Edit
                  </Button>
                ) : (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      startIcon={<Cancel />}
                      onClick={handleCancelEdit}
                      disabled={saving}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<Save />}
                      onClick={handleSaveProfile}
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : 'Save'}
                    </Button>
                  </Box>
                )}
              </Box>

              <Divider sx={{ mb: 3 }} />

              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <FormInput
                    label="Username"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    disabled={!editMode || saving}
                    startIcon={<Person color="action" />}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormInput
                    label="Full Name"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    disabled={!editMode || saving}
                    startIcon={<Person color="action" />}
                    placeholder="Enter your full name"
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <EmailInput
                    label="Email Address"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    disabled={!editMode || saving}
                    placeholder="Enter your email"
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Box sx={{ position: 'relative' }}>
                    <PhoneInput
                      label="Phone Number"
                      value={user.phone}
                      disabled
                      helperText="Phone number cannot be changed"
                    />
                  </Box>
                </Grid>
              </Grid>

              {/* Account Status */}
              <Box sx={{ mt: 4 }}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Account Status
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Phone Status
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {user.is_phone_verified ? 'Verified' : 'Not Verified'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Account Status
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {user.is_approved ? 'Approved' : 'Pending'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Payment Status
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {user.payment_verified ? 'Verified' : 'Pending'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Current Plan
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {user.current_plan?.name || 'No Plan'}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Change Password Dialog */}
      <Dialog
        open={changePasswordOpen}
        onClose={() => !saving && setChangePasswordOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Lock />
            <Typography variant="h6">Change Password</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" message={error} onClose={() => setError('')} open />
          )}
          <Box sx={{ mt: 2 }}>
            <PasswordInput
              label="Current Password"
              name="old_password"
              value={passwordData.old_password}
              onChange={handlePasswordChange}
              required
              disabled={saving}
            />
            <PasswordInput
              label="New Password"
              name="new_password"
              value={passwordData.new_password}
              onChange={handlePasswordChange}
              required
              helperText="At least 8 characters"
              disabled={saving}
            />
            <PasswordInput
              label="Confirm New Password"
              name="new_password_confirm"
              value={passwordData.new_password_confirm}
              onChange={handlePasswordChange}
              required
              disabled={saving}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChangePasswordOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleChangePassword}
            disabled={saving}
          >
            {saving ? 'Changing...' : 'Change Password'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Account Dialog */}
      <Dialog
        open={deleteAccountOpen}
        onClose={() => setDeleteAccountOpen(false)}
        maxWidth="sm"
      >
        <DialogTitle>Delete Account</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to delete your account?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This action cannot be undone. All your invitations and data will be permanently deleted.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteAccountOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error">
            Delete Account
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Profile;
