/**
 * User Dashboard
 */
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Add,
  CardGiftcard,
  People,
  Visibility,
  AccessTime,
  TrendingUp,
  CheckCircle,
  Pending,
  Cancel,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../store/authStore';
import { useInvitationStore } from '../../store/authStore';
import { invitationsApi } from '../../services/api';
import { Order, Invitation } from '../../types';

const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const { orders, invitations, setOrders, setInvitations } = useInvitationStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    totalInvitations: 0,
    totalViews: 0,
    totalGuests: 0,
    activeInvitations: 0,
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [ordersRes, invitationsRes] = await Promise.all([
        invitationsApi.getOrders(),
        invitationsApi.getInvitations(),
      ]);

      if (ordersRes.success) {
        setOrders(ordersRes.data || []);
      }
      if (invitationsRes.success) {
        setInvitations(invitationsRes.data || []);
        
        // Calculate stats
        const totalViews = invitationsRes.data?.reduce((sum: number, inv: Invitation) => sum + (inv.total_views || 0), 0) || 0;
        const totalGuests = invitationsRes.data?.reduce((sum: number, inv: Invitation) => sum + (inv.unique_guests || 0), 0) || 0;
        const activeInvitations = invitationsRes.data?.filter((inv: Invitation) => inv.is_active && !inv.is_expired).length || 0;
        
        setStats({
          totalInvitations: invitationsRes.data?.length || 0,
          totalViews,
          totalGuests,
          activeInvitations,
        });
      }
    } catch (err) {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <CheckCircle color="success" />;
      case 'PENDING_APPROVAL':
      case 'PENDING_PAYMENT':
        return <Pending color="warning" />;
      case 'REJECTED':
      case 'CANCELLED':
        return <Cancel color="error" />;
      default:
        return <Pending color="info" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'success';
      case 'PENDING_APPROVAL':
      case 'PENDING_PAYMENT':
        return 'warning';
      case 'REJECTED':
      case 'CANCELLED':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Welcome back, {user?.full_name || user?.username}!
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your invitations and track their performance
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {[
            { label: 'Total Invitations', value: stats.totalInvitations, icon: CardGiftcard, color: '#7B2CBF' },
            { label: 'Total Views', value: stats.totalViews, icon: Visibility, color: '#3498DB' },
            { label: 'Total Guests', value: stats.totalGuests, icon: People, color: '#27AE60' },
            { label: 'Active Links', value: stats.activeInvitations, icon: TrendingUp, color: '#E74C3C' },
          ].map((stat, index) => (
            <Grid item xs={6} md={3} key={stat.label}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Box
                        sx={{
                          width: 48,
                          height: 48,
                          borderRadius: 2,
                          bgcolor: `${stat.color}20`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mr: 2,
                        }}
                      >
                        <stat.icon sx={{ color: stat.color }} />
                      </Box>
                    </Box>
                    <Typography variant="h4" fontWeight={700}>
                      {stat.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {stat.label}
                    </Typography>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        <Grid container spacing={4}>
          {/* Recent Orders */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>
                  Recent Orders
                </Typography>
                <Button
                  component={Link}
                  to="/dashboard/orders"
                  size="small"
                >
                  View All
                </Button>
              </Box>
              <Divider sx={{ mb: 2 }} />
              
              {orders.length === 0 ? (
                <Box textAlign="center" py={4}>
                  <Typography variant="body1" color="text.secondary">
                    No orders yet
                  </Typography>
                  <Button
                    component={Link}
                    to="/plans"
                    variant="contained"
                    sx={{ mt: 2 }}
                  >
                    Browse Plans
                  </Button>
                </Box>
              ) : (
                <List>
                  {orders.slice(0, 5).map((order: Order) => (
                    <ListItem key={order.id} divider>
                      <ListItemIcon>
                        {getStatusIcon(order.status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={order.plan_name || order.plan?.name}
                        secondary={
                          <Box>
                            <Typography variant="body2" component="span">
                              {order.order_number}
                            </Typography>
                            <Chip
                              label={order.status.replace(/_/g, ' ')}
                              size="small"
                              color={getStatusColor(order.status) as any}
                              sx={{ ml: 1 }}
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>
          </Grid>

          {/* Recent Invitations */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>
                  Recent Invitations
                </Typography>
                <Button
                  component={Link}
                  to="/dashboard/invitations"
                  size="small"
                >
                  View All
                </Button>
              </Box>
              <Divider sx={{ mb: 2 }} />
              
              {invitations.length === 0 ? (
                <Box textAlign="center" py={4}>
                  <Typography variant="body1" color="text.secondary">
                    No invitations created yet
                  </Typography>
                  {orders.some((o: Order) => o.status === 'APPROVED') && (
                    <Button
                      component={Link}
                      to="/invitation/builder"
                      variant="contained"
                      sx={{ mt: 2 }}
                      startIcon={<Add />}
                    >
                      Create Invitation
                    </Button>
                  )}
                </Box>
              ) : (
                <List>
                  {invitations.slice(0, 5).map((invitation: Invitation) => (
                    <ListItem
                      key={invitation.id}
                      divider
                      component={Link}
                      to={`/invitation/${invitation.slug}`}
                      sx={{ textDecoration: 'none', color: 'inherit' }}
                    >
                      <ListItemText
                        primary={invitation.event_title}
                        secondary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                            <Chip
                              icon={<Visibility fontSize="small" />}
                              label={invitation.total_views}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              icon={<People fontSize="small" />}
                              label={invitation.unique_guests}
                              size="small"
                              variant="outlined"
                            />
                            {invitation.is_expired && (
                              <Chip
                                icon={<AccessTime fontSize="small" />}
                                label="Expired"
                                size="small"
                                color="error"
                              />
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>
          </Grid>
        </Grid>

        {/* Quick Actions */}
        <Paper sx={{ p: 3, mt: 4 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Quick Actions
          </Typography>
          <Grid container spacing={2}>
            <Grid item>
              <Button
                component={Link}
                to="/plans"
                variant="outlined"
                startIcon={<CardGiftcard />}
              >
                Buy New Plan
              </Button>
            </Grid>
            <Grid item>
              <Button
                component={Link}
                to="/dashboard/invitations"
                variant="outlined"
                startIcon={<Visibility />}
              >
                View All Invitations
              </Button>
            </Grid>
            <Grid item>
              <Button
                component={Link}
                to="/templates"
                variant="outlined"
                startIcon={<TrendingUp />}
              >
                Browse Templates
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </Container>
    </Box>
  );
};

export default Dashboard;
