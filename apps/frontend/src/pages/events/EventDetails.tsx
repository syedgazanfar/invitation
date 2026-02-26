/**
 * Event Details Page
 * 
 * Allows users to view and edit event details with AI-powered features:
 * - AI Message Generator integration for invitation text
 * - Smart suggestions for event improvements
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  Fade,
  InputAdornment,
} from '@mui/material';
import {
  ArrowBack,
  Save,
  AutoAwesome,
  ContentCopy,
  Check,
  Edit,
  CalendarToday,
  LocationOn,
  Phone,
  Person,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { invitationsApi } from '../../services/api';
import { Invitation, EventDetails as EventDetailsType } from '../../types';
import { MessageGenerator } from '../../components/ai/MessageGenerator';
import { AIFeatureBadge, AIIndicator } from '../../components/ai/AIFeatureBadge';
import { aiApi } from '../../services/aiApi';

interface EventDetailsProps {
  eventId?: string;
}

const EventDetails: React.FC<EventDetailsProps> = ({ eventId: propEventId }) => {
  const { id: urlEventId } = useParams<{ id: string }>();
  const eventId = propEventId || urlEventId;
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  
  // AI-related state
  const [showMessageGenerator, setShowMessageGenerator] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<any>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  
  // Form data
  const [formData, setFormData] = useState<EventDetailsType>({
    id: '',
    event_title: '',
    bride_name: '',
    groom_name: '',
    event_date: new Date(),
    event_venue: '',
    event_address: '',
    event_map_link: '',
    host_name: '',
    host_phone: '',
    custom_message: '',
    template_id: '',
    status: 'DRAFT',
  });

  useEffect(() => {
    if (eventId) {
      fetchEventDetails();
    }
  }, [eventId]);

  const fetchEventDetails = async () => {
    try {
      setLoading(true);
      const response = await invitationsApi.getInvitation(eventId!);
      
      if (response.success && response.data) {
        setInvitation(response.data);
        setFormData({
          id: response.data.id,
          event_title: response.data.event_title || '',
          bride_name: response.data.bride_name || '',
          groom_name: response.data.groom_name || '',
          event_date: new Date(response.data.event_date),
          event_venue: response.data.event_venue || '',
          event_address: response.data.event_address || '',
          event_map_link: response.data.event_map_link || '',
          host_name: response.data.host_name || '',
          host_phone: response.data.host_phone || '',
          custom_message: response.data.custom_message || '',
          template_id: response.data.template_id,
          status: response.data.status,
        });
      } else {
        setError('Failed to load event details');
      }
    } catch (err) {
      setError('An error occurred while loading event details');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');
      
      const response = await invitationsApi.updateInvitation(eventId!, {
        ...formData,
        event_date: formData.event_date.toISOString(),
      });
      
      if (response.success) {
        setSuccess('Event details saved successfully');
        setIsEditing(false);
        fetchEventDetails();
      } else {
        setError(response.message || 'Failed to save event details');
      }
    } catch (err) {
      setError('An error occurred while saving');
    } finally {
      setSaving(false);
    }
  };

  const handleAIMessageSelect = (message: string) => {
    setFormData(prev => ({ ...prev, custom_message: message }));
    setShowMessageGenerator(false);
    setIsEditing(true);
  };

  const handleCopy = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const fetchAISuggestions = async () => {
    if (!formData.bride_name || !formData.groom_name) return;
    
    try {
      setLoadingSuggestions(true);
      const suggestions = await aiApi.generateHashtags({
        brideName: formData.bride_name,
        groomName: formData.groom_name,
        weddingDate: formData.event_date.toISOString(),
        style: 'all',
        count: 9,
      });
      setAiSuggestions(suggestions);
    } catch (err) {
      console.error('Failed to fetch AI suggestions:', err);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  useEffect(() => {
    if (formData.bride_name && formData.groom_name && !aiSuggestions) {
      fetchAISuggestions();
    }
  }, [formData.bride_name, formData.groom_name]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (!invitation) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Event not found</Alert>
      </Container>
    );
  }

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/dashboard/invitations')}
            sx={{ mr: 2 }}
          >
            Back
          </Button>
          <Typography variant="h4" fontWeight={700} sx={{ flex: 1 }}>
            Event Details
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            {isEditing ? (
              <>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setIsEditing(false);
                    fetchEventDetails();
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? <CircularProgress size={20} /> : 'Save Changes'}
                </Button>
              </>
            ) : (
              <Button
                variant="contained"
                startIcon={<Edit />}
                onClick={() => setIsEditing(true)}
              >
                Edit
              </Button>
            )}
          </Box>
        </Box>

        {/* Alerts */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
            {success}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Main Form */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 4 }}>
              <Typography variant="h6" gutterBottom>
                Event Information
              </Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Event Title"
                    value={formData.event_title}
                    onChange={(e) => setFormData({ ...formData, event_title: e.target.value })}
                    disabled={!isEditing}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Person color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Bride's Name"
                    value={formData.bride_name}
                    onChange={(e) => setFormData({ ...formData, bride_name: e.target.value })}
                    disabled={!isEditing}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Groom's Name"
                    value={formData.groom_name}
                    onChange={(e) => setFormData({ ...formData, groom_name: e.target.value })}
                    disabled={!isEditing}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <DatePicker
                      label="Event Date"
                      value={formData.event_date}
                      onChange={(date) => date && setFormData({ ...formData, event_date: date })}
                      disabled={!isEditing}
                      slotProps={{ textField: { fullWidth: true } }}
                    />
                  </LocalizationProvider>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Host Name"
                    value={formData.host_name}
                    onChange={(e) => setFormData({ ...formData, host_name: e.target.value })}
                    disabled={!isEditing}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Venue Name"
                    value={formData.event_venue}
                    onChange={(e) => setFormData({ ...formData, event_venue: e.target.value })}
                    disabled={!isEditing}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <LocationOn color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Venue Address"
                    multiline
                    rows={2}
                    value={formData.event_address}
                    onChange={(e) => setFormData({ ...formData, event_address: e.target.value })}
                    disabled={!isEditing}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Google Maps Link"
                    value={formData.event_map_link}
                    onChange={(e) => setFormData({ ...formData, event_map_link: e.target.value })}
                    disabled={!isEditing}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Host Phone"
                    value={formData.host_phone}
                    onChange={(e) => setFormData({ ...formData, host_phone: e.target.value })}
                    disabled={!isEditing}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Phone color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
              </Grid>

              {/* Invitation Message Section with AI */}
              <Box sx={{ mt: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Typography variant="h6">
                    Invitation Message
                  </Typography>
                  <AIFeatureBadge size="small" />
                </Box>
                <Divider sx={{ mb: 2 }} />
                
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  value={formData.custom_message}
                  onChange={(e) => setFormData({ ...formData, custom_message: e.target.value })}
                  disabled={!isEditing}
                  placeholder="Enter your invitation message or generate one with AI"
                  InputProps={{
                    endAdornment: formData.custom_message && (
                      <InputAdornment position="end">
                        <Tooltip title={copiedField === 'message' ? 'Copied!' : 'Copy to clipboard'}>
                          <IconButton
                            onClick={() => handleCopy(formData.custom_message, 'message')}
                            edge="end"
                          >
                            {copiedField === 'message' ? <Check color="success" /> : <ContentCopy />}
                          </IconButton>
                        </Tooltip>
                      </InputAdornment>
                    ),
                  }}
                />
                
                {isEditing && (
                  <Button
                    variant="outlined"
                    startIcon={<AutoAwesome />}
                    onClick={() => setShowMessageGenerator(true)}
                    sx={{ mt: 2 }}
                    disabled={!formData.bride_name || !formData.groom_name}
                  >
                    Generate with AI
                  </Button>
                )}
                
                {!formData.bride_name || !formData.groom_name ? (
                  <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                    (Enter bride and groom names to use AI generation)
                  </Typography>
                ) : null}
              </Box>
            </Paper>
          </Grid>

          {/* Sidebar */}
          <Grid item xs={12} md={4}>
            {/* Status Card */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Event Status
              </Typography>
              <Chip
                label={formData.status}
                color={formData.status === 'ACTIVE' ? 'success' : formData.status === 'DRAFT' ? 'default' : 'primary'}
                sx={{ textTransform: 'uppercase', fontWeight: 600 }}
              />
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Created
                </Typography>
                <Typography variant="body1">
                  {invitation.created_at 
                    ? new Date(invitation.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })
                    : 'N/A'
                  }
                </Typography>
              </Box>
              
              {invitation.template && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Template
                  </Typography>
                  <Typography variant="body1">
                    {invitation.template.name}
                  </Typography>
                </Box>
              )}
            </Paper>

            {/* AI Suggestions Card */}
            <Paper sx={{ p: 3, bgcolor: 'rgba(166, 30, 42, 0.04)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <AutoAwesome color="primary" />
                <Typography variant="h6">
                  AI Suggestions
                </Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              
              {loadingSuggestions ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : aiSuggestions ? (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Suggested Hashtags
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                    {aiSuggestions.hashtags?.slice(0, 6).map((hashtag: string, idx: number) => (
                      <Chip
                        key={idx}
                        label={hashtag}
                        size="small"
                        onClick={() => handleCopy(hashtag, `hashtag_${idx}`)}
                        icon={copiedField === `hashtag_${idx}` ? <Check fontSize="small" /> : undefined}
                        sx={{ cursor: 'pointer' }}
                      />
                    ))}
                  </Box>
                  
                  <Typography variant="caption" color="text.secondary">
                    Top Pick: {aiSuggestions.top_pick}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Enter bride and groom names to get AI-powered hashtag suggestions.
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>

        {/* Message Generator Dialog */}
        <Dialog
          open={showMessageGenerator}
          onClose={() => setShowMessageGenerator(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoAwesome color="primary" />
              Generate Invitation Message
            </Box>
          </DialogTitle>
          <DialogContent>
            <MessageGenerator
              context={{
                brideName: formData.bride_name,
                groomName: formData.groom_name,
                eventType: 'WEDDING',
                details: formData.event_venue,
              }}
              onMessageSelect={handleAIMessageSelect}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowMessageGenerator(false)}>
              Cancel
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
};

export default EventDetails;
