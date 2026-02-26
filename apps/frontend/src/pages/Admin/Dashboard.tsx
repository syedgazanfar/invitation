/**
 * Admin Dashboard
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  Button,
} from '@mui/material';
import {
  People,
  ShoppingCart,
  TrendingUp,
  CardGiftcard,
  AttachMoney,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { motion } from 'framer-motion';
import { adminApi } from '../../services/api';
import { useAdminStore } from '../../store/authStore';
import { DashboardStats } from '../../types';

const COLORS = ['#7B2CBF', '#FF6B6B', '#4ECDC4', '#FFE66D'];

const AdminDashboard: React.FC = () => {
  const { dashboardStats, setDashboardStats } = useAdminStore();
  const [statistics, setStatistics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, detailsRes] = await Promise.all([
        adminApi.getDashboardStats(),
        adminApi.getStatistics(30),
      ]);
      
      if (statsRes.success) {
        setDashboardStats(statsRes.data);
      }
      if (detailsRes.success) {
        setStatistics(detailsRes.data);
      }
    } catch (err) {
      console.error('Failed to fetch admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const stats = dashboardStats || {
    users: { total: 0, new_today: 0 },
    orders: { total: 0, pending_approval: 0, pending_payment: 0, approved: 0 },
    revenue: { total: 0, this_month: 0 },
    invitations: { total: 0, active: 0 },
    guests: { total: 0 },
  };

  const statCards = [
    { title: 'Total Users', value: stats.users.total, icon: People, color: '#7B2CBF', newToday: stats.users.new_today },
    { title: 'Total Orders', value: stats.orders.total, icon: ShoppingCart, color: '#FF6B6B', pending: stats.orders.pending_approval },
    { title: 'Active Invitations', value: stats.invitations.active, icon: CardGiftcard, color: '#4ECDC4' },
    { title: 'Total Revenue', value: `Rs. ${stats.revenue.total.toLocaleString()}`, icon: AttachMoney, color: '#27AE60', thisMonth: stats.revenue.this_month },
  ];

  const dailyData = statistics?.daily_stats?.map((day: any) => ({
    date: new Date(day.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
    users: day.users,
    orders: day.orders,
    guests: day.guests,
  })) || [];

  const planData = statistics?.plan_distribution?.map((plan: any) => ({
    name: plan.name,
    value: plan.order_count,
  })) || [];

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="xl">
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Admin Dashboard
        </Typography>

        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {statCards.map((stat, index) => (
            <Grid item xs={12} sm={6} md={3} key={stat.title}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          {stat.title}
                        </Typography>
                        <Typography variant="h4" fontWeight={700}>
                          {stat.value}
                        </Typography>
                        {'newToday' in stat && (
                          <Typography variant="caption" color="success.main">
                            +{stat.newToday} today
                          </Typography>
                        )}
                        {'pending' in stat && stat.pending! > 0 && (
                          <Typography variant="caption" color="warning.main" display="block">
                            {stat.pending} pending approval
                          </Typography>
                        )}
                        {'thisMonth' in stat && (
                          <Typography variant="caption" color="text.secondary">
                            Rs. {stat.thisMonth?.toLocaleString()} this month
                          </Typography>
                        )}
                      </Box>
                      <Box
                        sx={{
                          width: 56,
                          height: 56,
                          borderRadius: 2,
                          bgcolor: `${stat.color}20`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <stat.icon sx={{ color: stat.color, fontSize: 28 }} />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        <Grid container spacing={4}>
          {/* Charts */}
          <Grid item xs={12} lg={8}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Activity (Last 30 Days)
              </Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={dailyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="users" stroke="#7B2CBF" name="Users" />
                    <Line type="monotone" dataKey="orders" stroke="#FF6B6B" name="Orders" />
                    <Line type="monotone" dataKey="guests" stroke="#4ECDC4" name="Guests" />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Orders by Plan
              </Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={planData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {planData.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Quick Actions */}
        <Paper sx={{ p: 3, mt: 4 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Quick Actions
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button variant="contained" href="/admin/orders">
              Manage Orders ({stats.orders.pending_approval} pending)
            </Button>
            <Button variant="outlined" href="/admin/users">
              Manage Users
            </Button>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default AdminDashboard;
