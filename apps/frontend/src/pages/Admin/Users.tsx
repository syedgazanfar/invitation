/**
 * Admin Users Page
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
  TablePagination,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
} from '@mui/material';
import {
  Block,
  CheckCircle,
  Search,
} from '@mui/icons-material';
import { adminApi } from '../../services/api';
import { useAdminStore } from '../../store/authStore';

interface User {
  id: string;
  phone: string;
  username: string;
  email?: string;
  full_name?: string;
  is_blocked: boolean;
  is_staff: boolean;
  created_at: string;
}

const AdminUsers: React.FC = () => {
  const { users, setUsers } = useAdminStore();
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<'block' | 'unblock'>('block');
  const [blockReason, setBlockReason] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  useEffect(() => {
    fetchUsers();
  }, [searchQuery]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await adminApi.getUsers({ search: searchQuery });
      if (response.success) {
        setUsers(response.data || []);
      }
    } catch (err) {
      console.error('Failed to fetch users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBlockAction = async () => {
    if (!selectedUser) return;
    
    try {
      let response;
      if (dialogType === 'block') {
        response = await adminApi.blockUser(selectedUser.id, blockReason);
      } else {
        response = await adminApi.unblockUser(selectedUser.id);
      }
      
      if (response?.success) {
        fetchUsers();
        setDialogOpen(false);
        setBlockReason('');
      }
    } catch (err) {
      console.error('Action failed:', err);
    }
  };

  const openDialog = (user: User, type: typeof dialogType) => {
    setSelectedUser(user);
    setDialogType(type);
    setDialogOpen(true);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Paginate users
  const paginatedUsers = users.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="xl">
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Manage Users
        </Typography>

        {/* Search */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Search users by phone, name, or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <Search color="action" />,
            }}
          />
        </Paper>

        {/* Users Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Phone</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Username</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Joined</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedUsers.map((user: User) => (
                <TableRow key={user.id}>
                  <TableCell>{user.phone}</TableCell>
                  <TableCell>{user.full_name || '-'}</TableCell>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>
                    {user.is_blocked ? (
                      <Chip label="Blocked" color="error" size="small" />
                    ) : (
                      <Chip label="Active" color="success" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    {user.is_staff ? (
                      <Chip label="Admin" color="primary" size="small" />
                    ) : (
                      <Chip label="User" size="small" variant="outlined" />
                    )}
                  </TableCell>
                  <TableCell>
                    {new Date(user.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {!user.is_staff && (
                      user.is_blocked ? (
                        <Button
                          size="small"
                          color="success"
                          onClick={() => openDialog(user, 'unblock')}
                          startIcon={<CheckCircle />}
                        >
                          Unblock
                        </Button>
                      ) : (
                        <Button
                          size="small"
                          color="error"
                          onClick={() => openDialog(user, 'block')}
                          startIcon={<Block />}
                        >
                          Block
                        </Button>
                      )
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {users.length > 0 && (
            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={users.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          )}
        </TableContainer>

        {/* Block/Unblock Dialog */}
        <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {dialogType === 'block' ? 'Block User' : 'Unblock User'}
          </DialogTitle>
          <DialogContent>
            <Typography paragraph>
              {dialogType === 'block'
                ? `Are you sure you want to block ${selectedUser?.phone}? They will no longer be able to access the platform.`
                : `Are you sure you want to unblock ${selectedUser?.phone}?`}
            </Typography>
            
            {dialogType === 'block' && (
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Reason (optional)"
                value={blockReason}
                onChange={(e) => setBlockReason(e.target.value)}
                margin="normal"
              />
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button
              variant="contained"
              color={dialogType === 'block' ? 'error' : 'success'}
              onClick={handleBlockAction}
            >
              Confirm
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
};

export default AdminUsers;
