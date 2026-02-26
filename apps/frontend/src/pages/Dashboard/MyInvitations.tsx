/**
 * My Invitations Page
 */
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Alert,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  Visibility,
  Share,
  MoreVert,
  FileDownload,
  Edit,
  ContentCopy,
  Delete,
  AccessTime,
  People,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { invitationsApi } from '../../services/api';
import { useInvitationStore } from '../../store/authStore';
import { Invitation } from '../../types';

const MyInvitations: React.FC = () => {
  const { invitations, setInvitations } = useInvitationStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedInvitation, setSelectedInvitation] = useState<Invitation | null>(null);

  useEffect(() => {
    fetchInvitations();
  }, []);

  const fetchInvitations = async () => {
    try {
      setLoading(true);
      const response = await invitationsApi.getInvitations();
      if (response.success) {
        setInvitations(response.data || []);
      }
    } catch (err) {
      setError('Failed to load invitations');
    } finally {
      setLoading(false);
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, invitation: Invitation) => {
    setAnchorEl(event.currentTarget);
    setSelectedInvitation(invitation);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedInvitation(null);
  };

  const handleCopyLink = () => {
    if (selectedInvitation) {
      navigator.clipboard.writeText(selectedInvitation.share_url);
      handleMenuClose();
    }
  };

  const handleExportGuests = async () => {
    if (selectedInvitation) {
      try {
        const response = await invitationsApi.exportGuests(selectedInvitation.slug);
        const blob = new Blob([response.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `guests_${selectedInvitation.slug}.csv`;
        a.click();
      } catch (err) {
        console.error('Export failed:', err);
      }
      handleMenuClose();
    }
  };

  const getStatusChip = (invitation: Invitation) => {
    if (invitation.is_expired) {
      return <Chip label="Expired" color="error" size="small" />;
    }
    if (invitation.is_active) {
      return <Chip label="Active" color="success" size="small" />;
    }
    return <Chip label="Inactive" color="default" size="small" />;
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
        <Typography variant="h4" fontWeight={700} gutterBottom>
          My Invitations
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {invitations.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              No invitations yet
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              Create your first invitation to get started
            </Typography>
            <Button
              component={Link}
              to="/plans"
              variant="contained"
            >
              Browse Plans
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {invitations.map((invitation: Invitation, index: number) => (
              <Grid item xs={12} md={6} lg={4} key={invitation.id}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Box
                      sx={{
                        height: 140,
                        background: `linear-gradient(135deg, ${invitation.template?.theme_colors?.primary || '#7B2CBF'} 0%, ${invitation.template?.theme_colors?.secondary || '#9D4EDD'} 100%)`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Typography variant="h4" color="white" fontWeight={700}>
                        {invitation.event_title.charAt(0)}
                      </Typography>
                    </Box>
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="h6" fontWeight={600} noWrap sx={{ maxWidth: '70%' }}>
                          {invitation.event_title}
                        </Typography>
                        {getStatusChip(invitation)}
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {new Date(invitation.event_date).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric',
                        })}
                      </Typography>

                      <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                        <Chip
                          icon={<VisibilityIcon fontSize="small" />}
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
                      </Box>

                      {invitation.link_expires_at && (
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                          <AccessTime fontSize="small" color="action" sx={{ mr: 0.5 }} />
                          <Typography variant="caption" color="text.secondary">
                            Expires: {new Date(invitation.link_expires_at).toLocaleDateString()}
                          </Typography>
                        </Box>
                      )}
                    </CardContent>
                    <CardActions>
                      <Button
                        component={Link}
                        to={`/invite/${invitation.slug}`}
                        target="_blank"
                        size="small"
                        startIcon={<Visibility />}
                      >
                        View
                      </Button>
                      <Tooltip title="Copy Link">
                        <IconButton
                          size="small"
                          onClick={() => navigator.clipboard.writeText(invitation.share_url)}
                        >
                          <ContentCopy />
                        </IconButton>
                      </Tooltip>
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, invitation)}
                      >
                        <MoreVert />
                      </IconButton>
                    </CardActions>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Action Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleCopyLink}>
            <ListItemIcon>
              <Share fontSize="small" />
            </ListItemIcon>
            <ListItemText>Copy Link</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleExportGuests}>
            <ListItemIcon>
              <FileDownload fontSize="small" />
            </ListItemIcon>
            <ListItemText>Export Guests</ListItemText>
          </MenuItem>
        </Menu>
      </Container>
    </Box>
  );
};

// Import Paper
import { Paper } from '@mui/material';

export default MyInvitations;
