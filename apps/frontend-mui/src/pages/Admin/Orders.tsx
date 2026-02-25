/**
 * Admin Orders Page
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  IconButton,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Visibility,
  Edit,
  Search,
} from '@mui/icons-material';
import { adminApi } from '../../services/api';
import { useAdminStore } from '../../store/authStore';

interface Order {
  id: string;
  order_number: string;
  user: { phone: string; full_name: string };
  plan: { name: string; code: string };
  event_type_name: string;
  status: string;
  payment_status: string;
  payment_amount: number;
  granted_regular_links: number;
  granted_test_links: number;
  admin_notes: string;
  created_at: string;
}

const AdminOrders: React.FC = () => {
  const { orders, setOrders } = useAdminStore();
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<'view' | 'approve' | 'reject' | 'grant'>('view');
  const [notes, setNotes] = useState('');
  const [grantLinks, setGrantLinks] = useState({ regular: 0, test: 0 });
  const [filters, setFilters] = useState({ status: '', search: '' });

  useEffect(() => {
    fetchOrders();
  }, [filters]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await adminApi.getOrders({
        status: filters.status,
        search: filters.search,
      });
      if (response.success) {
        setOrders(response.data || []);
      }
    } catch (err) {
      console.error('Failed to fetch orders:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async () => {
    if (!selectedOrder) return;
    
    try {
      let response;
      
      switch (dialogType) {
        case 'approve':
          response = await adminApi.approveOrder(selectedOrder.id, notes);
          break;
        case 'reject':
          response = await adminApi.rejectOrder(selectedOrder.id, notes);
          break;
        case 'grant':
          response = await adminApi.grantLinks(selectedOrder.id, grantLinks);
          break;
      }
      
      if (response?.success) {
        fetchOrders();
        setDialogOpen(false);
        setNotes('');
        setGrantLinks({ regular: 0, test: 0 });
      }
    } catch (err) {
      console.error('Action failed:', err);
    }
  };

  const openDialog = (order: Order, type: typeof dialogType) => {
    setSelectedOrder(order);
    setDialogType(type);
    setDialogOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED': return 'success';
      case 'PENDING_APPROVAL': return 'warning';
      case 'PENDING_PAYMENT': return 'info';
      case 'REJECTED': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="xl">
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Manage Orders
        </Typography>

        {/* Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search orders..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                InputProps={{
                  startAdornment: <Search color="action" />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  label="Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="PENDING_PAYMENT">Pending Payment</MenuItem>
                  <MenuItem value="PENDING_APPROVAL">Pending Approval</MenuItem>
                  <MenuItem value="APPROVED">Approved</MenuItem>
                  <MenuItem value="REJECTED">Rejected</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>

        {/* Orders Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Order #</TableCell>
                <TableCell>User</TableCell>
                <TableCell>Plan</TableCell>
                <TableCell>Event</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Links</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {orders.map((order: Order) => (
                <TableRow key={order.id}>
                  <TableCell>{order.order_number}</TableCell>
                  <TableCell>
                    <Typography variant="body2">{order.user?.full_name || 'N/A'}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {order.user?.phone}
                    </Typography>
                  </TableCell>
                  <TableCell>{order.plan?.name}</TableCell>
                  <TableCell>{order.event_type_name}</TableCell>
                  <TableCell>Rs. {order.payment_amount}</TableCell>
                  <TableCell>
                    <Chip
                      label={order.status.replace(/_/g, ' ')}
                      color={getStatusColor(order.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {order.granted_regular_links}R + {order.granted_test_links}T
                  </TableCell>
                  <TableCell>
                    <IconButton size="small" onClick={() => openDialog(order, 'view')}>
                      <Visibility />
                    </IconButton>
                    {order.status === 'PENDING_APPROVAL' && (
                      <>
                        <Button
                          size="small"
                          color="success"
                          onClick={() => openDialog(order, 'approve')}
                          startIcon={<CheckCircle />}
                        >
                          Approve
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => openDialog(order, 'reject')}
                          startIcon={<Cancel />}
                        >
                          Reject
                        </Button>
                      </>
                    )}
                    <Button
                      size="small"
                      onClick={() => openDialog(order, 'grant')}
                      startIcon={<Edit />}
                    >
                      Grant Links
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Action Dialog */}
        <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {dialogType === 'view' && 'Order Details'}
            {dialogType === 'approve' && 'Approve Order'}
            {dialogType === 'reject' && 'Reject Order'}
            {dialogType === 'grant' && 'Grant Additional Links'}
          </DialogTitle>
          <DialogContent>
            {selectedOrder && dialogType === 'view' && (
              <Box>
                <Typography><strong>Order:</strong> {selectedOrder.order_number}</Typography>
                <Typography><strong>User:</strong> {selectedOrder.user?.phone}</Typography>
                <Typography><strong>Plan:</strong> {selectedOrder.plan?.name}</Typography>
                <Typography><strong>Event:</strong> {selectedOrder.event_type_name}</Typography>
                <Typography><strong>Amount:</strong> Rs. {selectedOrder.payment_amount}</Typography>
                <Typography><strong>Status:</strong> {selectedOrder.status}</Typography>
                <Typography><strong>Links:</strong> {selectedOrder.granted_regular_links} Regular + {selectedOrder.granted_test_links} Test</Typography>
              </Box>
            )}
            
            {(dialogType === 'approve' || dialogType === 'reject') && (
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Notes (optional)"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                margin="normal"
              />
            )}
            
            {dialogType === 'grant' && (
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Additional Regular Links"
                    value={grantLinks.regular}
                    onChange={(e) => setGrantLinks({ ...grantLinks, regular: parseInt(e.target.value) || 0 })}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Additional Test Links"
                    value={grantLinks.test}
                    onChange={(e) => setGrantLinks({ ...grantLinks, test: parseInt(e.target.value) || 0 })}
                  />
                </Grid>
              </Grid>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            {dialogType !== 'view' && (
              <Button
                variant="contained"
                color={dialogType === 'reject' ? 'error' : 'primary'}
                onClick={handleAction}
              >
                Confirm
              </Button>
            )}
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
};

export default AdminOrders;
