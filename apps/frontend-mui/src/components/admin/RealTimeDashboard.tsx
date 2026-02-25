/**
 * Real-Time Admin Dashboard Component
 * 
 * This component provides a real-time view of pending approvals,
 * recent activity, and admin notifications with WebSocket updates.
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Badge,
  Chip,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Snackbar,
  Alert,
  Paper,
  LinearProgress,
  Fade,
  Slide,
} from '@mui/material';
import {
  Notifications,
  CheckCircle,
  Cancel,
  Person,
  AccessTime,
  Phone,
  Email,
  Refresh,
  FiberManualRecord,
  Check,
  Close,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useWebSocket, ApprovalUpdateMessage, WebSocketData } from '../../hooks/useWebSocket';
import { adminApi } from '../../services/api';

// Types
interface PendingUser {
  id: string;
  username: string;
  full_name?: string;
  phone: string;
  email?: string;
  created_at: string;
  signup_ip?: string;
  current_plan?: {
    code: string;
    name: string;
    price_inr: number;
    regular_links: number;
    test_links: number;
  };
  latest_order?: {
    id: string;
    order_number: string;
    status: string;
    payment_amount: number;
    payment_method: string;
  };
}

interface RecentActivity {
  id: string;
  action: 'APPROVED' | 'REJECTED';
  user: {
    id: string;
    username: string;
    full_name?: string;
    phone: string;
  };
  performed_by?: {
    id: string;
    username: string;
  };
  notes?: string;
  created_at: string;
}

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

// Props
interface RealTimeDashboardProps {
  onStatsUpdate?: (stats: any) => void;
}

export const RealTimeDashboard: React.FC<RealTimeDashboardProps> = ({ onStatsUpdate }) => {
  // State
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [selectedUser, setSelectedUser] = useState<PendingUser | null>(null);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [rejectionDialogOpen, setRejectionDialogOpen] = useState(false);
  const [notes, setNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // WebSocket hook
  const { 
    state: wsState, 
    pendingCount, 
    recentApprovals, 
    connectedAdmins,
    lastMessage 
  } = useWebSocket({
    onMessage: handleWebSocketMessage,
  });

  // Handle WebSocket messages
  function handleWebSocketMessage(data: WebSocketData) {
    switch (data.type) {
      case 'approval_update':
        // Remove user from pending list if approved/rejected
        const approvalData = data as ApprovalUpdateMessage;
        setPendingUsers(prev => prev.filter(u => u.id !== approvalData.user.id));
        // Refresh recent activity
        fetchRecentActivity();
        break;
      
      case 'new_user':
        // Refresh pending users list
        fetchPendingUsers();
        break;
      
      case 'new_notification':
        // Add new notification
        setNotifications(prev => [data.notification, ...prev]);
        break;
    }
  }

  // Fetch pending users
  const fetchPendingUsers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await adminApi.getPendingUsers();
      if (response.success) {
        setPendingUsers(response.data || []);
      }
    } catch (error) {
      console.error('Failed to fetch pending users:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch recent activity
  const fetchRecentActivity = useCallback(async () => {
    try {
      const response = await adminApi.getRecentApprovals();
      if (response.success) {
        setRecentActivity(response.data || []);
      }
    } catch (error) {
      console.error('Failed to fetch recent activity:', error);
    }
  }, []);

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    try {
      const response = await adminApi.getNotifications();
      if (response.success) {
        setNotifications(response.data || []);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchPendingUsers();
    fetchRecentActivity();
    fetchNotifications();
  }, [fetchPendingUsers, fetchRecentActivity, fetchNotifications]);

  // Handle approve
  const handleApprove = async () => {
    if (!selectedUser) return;

    try {
      setLoading(true);
      const response = await adminApi.approveUser(selectedUser.id, { notes });
      
      if (response.success) {
        setSnackbar({
          open: true,
          message: `User ${selectedUser.username} approved successfully`,
          severity: 'success'
        });
        setPendingUsers(prev => prev.filter(u => u.id !== selectedUser.id));
        fetchRecentActivity();
      } else {
        setSnackbar({
          open: true,
          message: response.message || 'Failed to approve user',
          severity: 'error'
        });
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'An error occurred while approving user',
        severity: 'error'
      });
    } finally {
      setLoading(false);
      setApprovalDialogOpen(false);
      setNotes('');
      setSelectedUser(null);
    }
  };

  // Handle reject
  const handleReject = async () => {
    if (!selectedUser || !rejectionReason) return;

    try {
      setLoading(true);
      const response = await adminApi.rejectUser(selectedUser.id, { 
        reason: rejectionReason,
        block_user: true 
      });
      
      if (response.success) {
        setSnackbar({
          open: true,
          message: `User ${selectedUser.username} rejected`,
          severity: 'success'
        });
        setPendingUsers(prev => prev.filter(u => u.id !== selectedUser.id));
        fetchRecentActivity();
      } else {
        setSnackbar({
          open: true,
          message: response.message || 'Failed to reject user',
          severity: 'error'
        });
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'An error occurred while rejecting user',
        severity: 'error'
      });
    } finally {
      setLoading(false);
      setRejectionDialogOpen(false);
      setRejectionReason('');
      setSelectedUser(null);
    }
  };

  // Format relative time
  const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Get connection status color
  const getConnectionStatusColor = () => {
    switch (wsState) {
      case 'connected': return '#4caf50';
      case 'connecting': return '#ff9800';
      case 'error': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  return (
    <Box sx={{ py: 3 }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" fontWeight={700}>
            Real-Time Admin Dashboard
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Connection Status */}
            <Tooltip title={`WebSocket: ${wsState}`}>
              <Chip
                size="small"
                icon={<FiberManualRecord sx={{ color: getConnectionStatusColor() }} />}
                label={wsState}
                sx={{ 
                  bgcolor: `${getConnectionStatusColor()}20`,
                  color: getConnectionStatusColor(),
                  fontWeight: 600
                }}
              />
            </Tooltip>

            {/* Connected Admins */}
            <Tooltip title={`${connectedAdmins.length} admin(s) online`}>
              <Chip
                size="small"
                icon={<Person />}
                label={`${connectedAdmins.length} online`}
                variant="outlined"
              />
            </Tooltip>

            {/* Notifications Badge */}
            <IconButton color="primary">
              <Badge badgeContent={notifications.filter(n => !n.is_read).length} color="error">
                <Notifications />
              </Badge>
            </IconButton>

            <IconButton onClick={() => { fetchPendingUsers(); fetchRecentActivity(); }}>
              <Refresh />
            </IconButton>
          </Box>
        </Box>

        {/* Pending Approvals Counter */}
        <Card sx={{ mb: 3, bgcolor: pendingCount > 0 ? 'warning.light' : 'success.light' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="h6" fontWeight={600}>
                  Pending Approvals
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Users waiting for plan approval
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="h3" fontWeight={700} color={pendingCount > 0 ? 'warning.dark' : 'success.dark'}>
                  {pendingCount || pendingUsers.length}
                </Typography>
                {pendingCount > 0 && (
                  <Chip 
                    size="small" 
                    color="warning" 
                    label="Action Required" 
                    sx={{ mt: 1 }}
                  />
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Grid container spacing={3}>
          {/* Pending Users List */}
          <Grid item xs={12} lg={7}>
            <Paper sx={{ p: 2, height: '600px', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Pending Users
              </Typography>
              
              {loading && <LinearProgress sx={{ mb: 2 }} />}

              <List sx={{ flex: 1, overflow: 'auto' }}>
                <AnimatePresence>
                  {pendingUsers.map((user, index) => (
                    <motion.div
                      key={user.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <ListItem
                        sx={{
                          mb: 1,
                          bgcolor: 'background.paper',
                          borderRadius: 2,
                          border: '1px solid',
                          borderColor: 'divider',
                          '&:hover': { bgcolor: 'action.hover' }
                        }}
                        secondaryAction={
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Button
                              size="small"
                              variant="contained"
                              color="success"
                              startIcon={<Check />}
                              onClick={() => {
                                setSelectedUser(user);
                                setApprovalDialogOpen(true);
                              }}
                            >
                              Approve
                            </Button>
                            <Button
                              size="small"
                              variant="outlined"
                              color="error"
                              startIcon={<Close />}
                              onClick={() => {
                                setSelectedUser(user);
                                setRejectionDialogOpen(true);
                              }}
                            >
                              Reject
                            </Button>
                          </Box>
                        }
                      >
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'primary.main' }}>
                            <Person />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography fontWeight={600}>
                                {user.full_name || user.username}
                              </Typography>
                              {user.current_plan && (
                                <Chip 
                                  size="small" 
                                  label={user.current_plan.name}
                                  color={user.current_plan.code === 'LUXURY' ? 'secondary' : 'primary'}
                                  sx={{ height: 20 }}
                                />
                              )}
                            </Box>
                          }
                          secondary={
                            <Box sx={{ mt: 0.5 }}>
                              <Typography variant="body2" component="span" display="flex" alignItems="center" gap={0.5}>
                                <Phone fontSize="small" />
                                {user.phone}
                              </Typography>
                              {user.email && (
                                <Typography variant="body2" component="span" display="flex" alignItems="center" gap={0.5} sx={{ ml: 2 }}>
                                  <Email fontSize="small" />
                                  {user.email}
                                </Typography>
                              )}
                              <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
                                <AccessTime fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                                Registered {formatRelativeTime(user.created_at)}
                              </Typography>
                              {user.current_plan && (
                                <Typography variant="caption" display="block" color="text.secondary">
                                  Plan: ₹{user.current_plan.price_inr} | {user.current_plan.regular_links} links
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {pendingUsers.length === 0 && !loading && (
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <CheckCircle sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
                    <Typography color="text.secondary">
                      No pending approvals!
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      All users have been processed.
                    </Typography>
                  </Box>
                )}
              </List>
            </Paper>
          </Grid>

          {/* Recent Activity */}
          <Grid item xs={12} lg={5}>
            <Paper sx={{ p: 2, height: '600px', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Recent Activity
              </Typography>

              <List sx={{ flex: 1, overflow: 'auto' }}>
                {recentActivity.map((activity, index) => (
                  <React.Fragment key={activity.id}>
                    <ListItem alignItems="flex-start">
                      <ListItemAvatar>
                        <Avatar sx={{ 
                          bgcolor: activity.action === 'APPROVED' ? 'success.main' : 'error.main' 
                        }}>
                          {activity.action === 'APPROVED' ? <CheckCircle /> : <Cancel />}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Typography fontWeight={600}>
                            {activity.user.full_name || activity.user.username}
                            {' '}
                            <Typography 
                              component="span" 
                              color={activity.action === 'APPROVED' ? 'success.main' : 'error.main'}
                            >
                              {activity.action.toLowerCase()}
                            </Typography>
                          </Typography>
                        }
                        secondary={
                          <>
                            <Typography variant="body2" component="span">
                              by {activity.performed_by?.username || 'System'}
                            </Typography>
                            <Typography variant="caption" display="block" color="text.secondary">
                              {formatRelativeTime(activity.created_at)}
                            </Typography>
                            {activity.notes && (
                              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                                Note: {activity.notes}
                              </Typography>
                            )}
                          </>
                        }
                      />
                    </ListItem>
                    {index < recentActivity.length - 1 && <Divider variant="inset" component="li" />}
                  </React.Fragment>
                ))}

                {recentActivity.length === 0 && (
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <Typography color="text.secondary">
                      No recent activity
                    </Typography>
                  </Box>
                )}
              </List>
            </Paper>
          </Grid>
        </Grid>

        {/* Approval Dialog */}
        <Dialog open={approvalDialogOpen} onClose={() => setApprovalDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            Approve User: {selectedUser?.full_name || selectedUser?.username}
          </DialogTitle>
          <DialogContent>
            {selectedUser?.current_plan && (
              <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" fontWeight={600}>Plan Details:</Typography>
                <Typography variant="body2">Plan: {selectedUser.current_plan.name}</Typography>
                <Typography variant="body2">Price: ₹{selectedUser.current_plan.price_inr}</Typography>
                <Typography variant="body2">Links: {selectedUser.current_plan.regular_links} regular + {selectedUser.current_plan.test_links} test</Typography>
              </Box>
            )}
            <TextField
              label="Approval Notes (Optional)"
              multiline
              rows={3}
              fullWidth
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any notes about this approval..."
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setApprovalDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleApprove} 
              variant="contained" 
              color="success"
              disabled={loading}
            >
              {loading ? 'Approving...' : 'Approve User'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Rejection Dialog */}
        <Dialog open={rejectionDialogOpen} onClose={() => setRejectionDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            Reject User: {selectedUser?.full_name || selectedUser?.username}
          </DialogTitle>
          <DialogContent>
            <TextField
              label="Rejection Reason (Required)"
              multiline
              rows={3}
              fullWidth
              required
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Provide a reason for rejection..."
              error={!rejectionReason}
              helperText={!rejectionReason ? 'Rejection reason is required' : ''}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setRejectionDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleReject} 
              variant="contained" 
              color="error"
              disabled={loading || !rejectionReason}
            >
              {loading ? 'Rejecting...' : 'Reject User'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert 
            severity={snackbar.severity} 
            onClose={() => setSnackbar({ ...snackbar, open: false })}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Box>
  );
};

export default RealTimeDashboard;
