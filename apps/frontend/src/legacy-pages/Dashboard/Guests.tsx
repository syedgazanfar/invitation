/**
 * Guest Management Page
 *
 * View and manage guests who registered for invitations.
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
  Chip,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Download,
  Visibility,
  CheckCircle,
  Cancel,
  People,
  Event,
  Phone,
  Message,
} from '@mui/icons-material';
import { invitationsApi } from '../../services/api';
import { useInvitationStore } from '../../store/authStore';
import { Guest, Invitation } from '../../types';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/Feedback/EmptyState';

const Guests: React.FC = () => {
  const { invitations, setInvitations } = useInvitationStore();
  const [guests, setGuests] = useState<Guest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedInvitation, setSelectedInvitation] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedGuest, setSelectedGuest] = useState<Guest | null>(null);
  const [guestDialogOpen, setGuestDialogOpen] = useState(false);

  useEffect(() => {
    fetchInvitations();
  }, []);

  useEffect(() => {
    if (invitations.length > 0) {
      fetchGuests();
    }
  }, [selectedInvitation, invitations]);

  const fetchInvitations = async () => {
    try {
      setLoading(true);
      const response = await invitationsApi.getInvitations();
      if (response.success) {
        setInvitations(response.data || []);
        if (response.data && response.data.length > 0) {
          setSelectedInvitation('all');
        }
      }
    } catch (err) {
      setError('Failed to load invitations');
    } finally {
      setLoading(false);
    }
  };

  const fetchGuests = async () => {
    try {
      setLoading(true);
      setError('');

      if (selectedInvitation === 'all') {
        // Fetch guests from all invitations
        const allGuests: Guest[] = [];
        for (const invitation of invitations) {
          const response = await invitationsApi.getGuests(invitation.slug);
          if (response.success && response.data) {
            allGuests.push(...response.data);
          }
        }
        setGuests(allGuests);
      } else {
        // Fetch guests from specific invitation
        const invitation = invitations.find(inv => inv.slug === selectedInvitation);
        if (invitation) {
          const response = await invitationsApi.getGuests(invitation.slug);
          if (response.success && response.data) {
            setGuests(response.data);
          }
        }
      }
    } catch (err: any) {
      console.error('Failed to fetch guests:', err);
      setError('Failed to load guests');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      if (selectedInvitation === 'all') {
        // Export all guests (would need backend support)
        alert('Export all guests feature coming soon');
        return;
      }

      const invitation = invitations.find(inv => inv.slug === selectedInvitation);
      if (invitation) {
        const response = await invitationsApi.exportGuests(invitation.slug);
        const blob = new Blob([response.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `guests_${invitation.event_title.replace(/\s+/g, '_')}.csv`;
        a.click();
      }
    } catch (err) {
      console.error('Export failed:', err);
      setError('Failed to export guests');
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleViewGuest = (guest: Guest) => {
    setSelectedGuest(guest);
    setGuestDialogOpen(true);
  };

  // Filter guests based on search query
  const filteredGuests = guests.filter((guest) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      guest.name?.toLowerCase().includes(query) ||
      guest.phone?.toLowerCase().includes(query) ||
      guest.message?.toLowerCase().includes(query)
    );
  });

  // Paginate guests
  const paginatedGuests = filteredGuests.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Calculate statistics
  const stats = {
    total: filteredGuests.length,
    attending: filteredGuests.filter(g => g.attending === true).length,
    notAttending: filteredGuests.filter(g => g.attending === false).length,
    noResponse: filteredGuests.filter(g => g.attending === undefined).length,
  };

  if (loading && invitations.length === 0) {
    return <LoadingSpinner />;
  }

  if (invitations.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <EmptyState
          icon={People}
          title="No Invitations Yet"
          message="Create an invitation to start collecting guest responses"
          action={
            <Button variant="contained" href="/plans">
              Browse Plans
            </Button>
          }
        />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Guest Management
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <People sx={{ fontSize: 32, color: 'primary.main', mr: 2 }} />
                <Typography variant="h4" fontWeight={700}>
                  {stats.total}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Guests
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircle sx={{ fontSize: 32, color: 'success.main', mr: 2 }} />
                <Typography variant="h4" fontWeight={700}>
                  {stats.attending}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Attending
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Cancel sx={{ fontSize: 32, color: 'error.main', mr: 2 }} />
                <Typography variant="h4" fontWeight={700}>
                  {stats.notAttending}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Not Attending
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Event sx={{ fontSize: 32, color: 'warning.main', mr: 2 }} />
                <Typography variant="h4" fontWeight={700}>
                  {stats.noResponse}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                No Response
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              select
              fullWidth
              label="Filter by Invitation"
              value={selectedInvitation}
              onChange={(e) => setSelectedInvitation(e.target.value)}
            >
              <MenuItem value="all">All Invitations</MenuItem>
              {invitations.map((invitation) => (
                <MenuItem key={invitation.id} value={invitation.slug}>
                  {invitation.event_title}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Search guests"
              placeholder="Name, phone, or message..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Download />}
              onClick={handleExport}
              disabled={selectedInvitation === 'all' || guests.length === 0}
            >
              Export to CSV
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Guests Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>RSVP Status</TableCell>
              <TableCell>Device</TableCell>
              <TableCell>Viewed At</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedGuests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Box py={4}>
                    <Typography variant="body1" color="text.secondary">
                      {searchQuery ? 'No guests match your search' : 'No guests yet'}
                    </Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ) : (
              paginatedGuests.map((guest) => (
                <TableRow key={guest.id}>
                  <TableCell>
                    <Typography variant="body2" fontWeight={600}>
                      {guest.name || 'Anonymous'}
                    </Typography>
                  </TableCell>
                  <TableCell>{guest.phone || '-'}</TableCell>
                  <TableCell>
                    {guest.attending === true && (
                      <Chip label="Attending" color="success" size="small" />
                    )}
                    {guest.attending === false && (
                      <Chip label="Not Attending" color="error" size="small" />
                    )}
                    {guest.attending === undefined && (
                      <Chip label="No Response" color="default" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" display="block">
                      {guest.device_type}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {guest.browser} / {guest.os}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {new Date(guest.viewed_at).toLocaleDateString()}
                    <Typography variant="caption" display="block" color="text.secondary">
                      {new Date(guest.viewed_at).toLocaleTimeString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="View Details">
                      <IconButton size="small" onClick={() => handleViewGuest(guest)}>
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        {filteredGuests.length > 0 && (
          <TablePagination
            rowsPerPageOptions={[5, 10, 25, 50]}
            component="div"
            count={filteredGuests.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        )}
      </TableContainer>

      {/* Guest Details Dialog */}
      <Dialog
        open={guestDialogOpen}
        onClose={() => setGuestDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Guest Details</DialogTitle>
        <DialogContent>
          {selectedGuest && (
            <Box>
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Name
                </Typography>
                <Typography variant="h6">{selectedGuest.name || 'Anonymous'}</Typography>
              </Box>

              {selectedGuest.phone && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Phone Number
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Phone sx={{ mr: 1, fontSize: 20 }} />
                    <Typography variant="body1">{selectedGuest.phone}</Typography>
                  </Box>
                </Box>
              )}

              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  RSVP Status
                </Typography>
                {selectedGuest.attending === true && (
                  <Chip label="Attending" color="success" icon={<CheckCircle />} />
                )}
                {selectedGuest.attending === false && (
                  <Chip label="Not Attending" color="error" icon={<Cancel />} />
                )}
                {selectedGuest.attending === undefined && (
                  <Chip label="No Response" color="default" />
                )}
              </Box>

              {selectedGuest.message && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Message
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                      <Message sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
                      <Typography variant="body2">{selectedGuest.message}</Typography>
                    </Box>
                  </Paper>
                </Box>
              )}

              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Device Information
                </Typography>
                <Typography variant="body2">
                  <strong>Type:</strong> {selectedGuest.device_type}
                </Typography>
                <Typography variant="body2">
                  <strong>Browser:</strong> {selectedGuest.browser}
                </Typography>
                <Typography variant="body2">
                  <strong>OS:</strong> {selectedGuest.os}
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Viewed At
                </Typography>
                <Typography variant="body2">
                  {new Date(selectedGuest.viewed_at).toLocaleString()}
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGuestDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Guests;
