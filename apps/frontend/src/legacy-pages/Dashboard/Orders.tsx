/**
 * Orders Page
 */
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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
  TablePagination,
  Chip,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Visibility,
  Add,
  CheckCircle,
  Pending,
  Cancel,
  Payment,
} from '@mui/icons-material';
import { invitationsApi } from '../../services/api';
import { useInvitationStore } from '../../store/authStore';
import { Order } from '../../types';

const Orders: React.FC = () => {
  const { orders, setOrders } = useInvitationStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await invitationsApi.getOrders();
      if (response.success) {
        setOrders(response.data || []);
      }
    } catch (err) {
      setError('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'success';
      case 'PENDING_APPROVAL':
        return 'warning';
      case 'PENDING_PAYMENT':
        return 'info';
      case 'REJECTED':
      case 'CANCELLED':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatStatus = (status: string) => {
    return status.replace(/_/g, ' ');
  };

  const handleViewDetails = (order: Order) => {
    setSelectedOrder(order);
    setOpenDialog(true);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Paginate orders
  const paginatedOrders = orders.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" fontWeight={700}>
            My Orders
          </Typography>
          <Button
            component={Link}
            to="/plans"
            variant="contained"
            startIcon={<Add />}
          >
            New Order
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Order Number</TableCell>
                <TableCell>Plan</TableCell>
                <TableCell>Event Type</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Date</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {orders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Box py={4}>
                      <Typography variant="body1" color="text.secondary" gutterBottom>
                        No orders found
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
                  </TableCell>
                </TableRow>
              ) : (
                paginatedOrders.map((order: Order) => (
                  <TableRow key={order.id}>
                    <TableCell>{order.order_number}</TableCell>
                    <TableCell>{order.plan_name || order.plan?.name}</TableCell>
                    <TableCell>{order.event_type_name}</TableCell>
                    <TableCell>Rs. {order.payment_amount}</TableCell>
                    <TableCell>
                      <Chip
                        label={formatStatus(order.status)}
                        color={getStatusColor(order.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(order.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton onClick={() => handleViewDetails(order)}>
                        <Visibility />
                      </IconButton>
                      {order.status === 'APPROVED' && !order.has_invitation && (
                        <Button
                          component={Link}
                          to={`/invitation/builder/${order.id}`}
                          size="small"
                          variant="contained"
                          sx={{ ml: 1 }}
                        >
                          Create Invitation
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
          {orders.length > 0 && (
            <TablePagination
              rowsPerPageOptions={[5, 10, 25, 50]}
              component="div"
              count={orders.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          )}
        </TableContainer>

        {/* Order Details Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Order Details</DialogTitle>
          <DialogContent>
            {selectedOrder && (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Order Number
                </Typography>
                <Typography variant="h6" gutterBottom>
                  {selectedOrder.order_number}
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  Plan
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {selectedOrder.plan_name || selectedOrder.plan?.name}
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  Event Type
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {selectedOrder.event_type_name}
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  Amount
                </Typography>
                <Typography variant="body1" gutterBottom>
                  Rs. {selectedOrder.payment_amount}
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  Status
                </Typography>
                <Chip
                  label={formatStatus(selectedOrder.status)}
                  color={getStatusColor(selectedOrder.status) as any}
                />

                <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  Links Granted
                </Typography>
                <Typography variant="body1">
                  {selectedOrder.granted_regular_links} Regular + {selectedOrder.granted_test_links} Test
                </Typography>

                {selectedOrder.invitation_slug && (
                  <>
                    <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                      Invitation
                    </Typography>
                    <Button
                      component={Link}
                      to={`/invitation/${selectedOrder.invitation_slug}`}
                      size="small"
                      variant="outlined"
                    >
                      View Invitation
                    </Button>
                  </>
                )}

                {selectedOrder.admin_notes && (
                  <>
                    <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                      Admin Notes
                    </Typography>
                    <Alert severity="info">{selectedOrder.admin_notes}</Alert>
                  </>
                )}
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
};

export default Orders;
