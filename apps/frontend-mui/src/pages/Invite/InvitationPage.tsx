/**
 * Public Invitation Page
 * This is the page guests see when they open the invitation link
 */
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Fade,
  Chip,
  IconButton,
} from '@mui/material';
import {
  LocationOn,
  CalendarToday,
  AccessTime,
  Person,
  MusicNote,
  Share,
  Close,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { publicApi } from '../../services/api';
import { useFingerprint } from '../../hooks/useFingerprint';
import WeddingTemplate from '../../components/templates/WeddingTemplate';
import BirthdayTemplate from '../../components/templates/BirthdayTemplate';
import FestivalTemplate from '../../components/templates/FestivalTemplate';
import PartyTemplate from '../../components/templates/PartyTemplate';

interface InvitationData {
  event_title: string;
  event_date: string;
  event_venue: string;
  event_address?: string;
  event_map_link?: string;
  host_name: string;
  custom_message?: string;
  banner_image: string;
  gallery_images: string[];
  background_music?: string;
  template_animation: string;
  template_theme: Record<string, string>;
  template_config: Record<string, any>;
}

const InvitationPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const { fingerprint } = useFingerprint();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [invitation, setInvitation] = useState<InvitationData | null>(null);
  const [canRegister, setCanRegister] = useState(true);
  const [alreadyRegistered, setAlreadyRegistered] = useState(false);
  const [guestName, setGuestName] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const [remainingLinks, setRemainingLinks] = useState(0);

  useEffect(() => {
    if (slug && fingerprint) {
      fetchInvitation();
    }
  }, [slug, fingerprint]);

  const fetchInvitation = async () => {
    try {
      setLoading(true);
      
      // Fetch invitation data
      const response = await publicApi.getInvitation(slug!);
      
      if (response.data?.success) {
        setInvitation(response.data.data.invitation);
        setCanRegister(response.data.data.can_register);
        setRemainingLinks(response.data.data.remaining_links);
        
        // Check if already registered
        if (fingerprint) {
          const checkRes = await publicApi.checkGuestStatus(slug!, fingerprint);
          if (checkRes.data?.success) {
            setAlreadyRegistered(checkRes.data.data.already_registered);
            if (checkRes.data.data.already_registered) {
              setGuestName(checkRes.data.data.guest_name);
            }
          }
        }
      } else {
        setError(response.data?.message || 'Invitation not found');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load invitation');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!guestName.trim() || !fingerprint) return;
    
    try {
      const response = await publicApi.registerGuest(slug!, {
        name: guestName,
        fingerprint,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        timezone_offset: new Date().getTimezoneOffset().toString(),
        languages: navigator.language,
      });
      
      if (response.data?.success) {
        setRegistrationSuccess(true);
        setAlreadyRegistered(true);
        setShowDialog(false);
      } else {
        setError(response.data?.message || 'Registration failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Registration failed');
    }
  };

  const getTemplateComponent = () => {
    if (!invitation) return null;
    
    const templateProps = {
      invitation,
      onOpenRegistration: () => setShowDialog(true),
      alreadyRegistered,
      guestName,
    };
    
    // Select template based on animation type
    switch (invitation.template_animation) {
      case 'elegant':
      case 'royal':
      case 'floral':
        return <WeddingTemplate {...templateProps} />;
      case 'fun':
      case 'modern':
        return <BirthdayTemplate {...templateProps} />;
      case 'traditional':
        return <FestivalTemplate {...templateProps} />;
      default:
        return <PartyTemplate {...templateProps} />;
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.default',
        }}
      >
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          <Typography variant="h4" color="primary">
            Loading...
          </Typography>
        </motion.div>
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 3,
        }}
      >
        <Alert severity="error" sx={{ maxWidth: 500 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {/* Template Display */}
      {getTemplateComponent()}
      
      {/* Registration Dialog */}
      <Dialog open={showDialog} onClose={() => setShowDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              RSVP
            </Typography>
            <IconButton onClick={() => setShowDialog(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {registrationSuccess ? (
            <Alert severity="success" sx={{ mb: 2 }}>
              Thank you for your response! We look forward to seeing you.
            </Alert>
          ) : (
            <>
              <Typography variant="body1" paragraph>
                Please enter your name to confirm your attendance:
              </Typography>
              <TextField
                fullWidth
                label="Your Name"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
                autoFocus
                margin="normal"
                placeholder="Enter your full name"
              />
              <Typography variant="caption" color="text.secondary">
                {remainingLinks} spots remaining
              </Typography>
            </>
          )}
        </DialogContent>
        {!registrationSuccess && (
          <DialogActions>
            <Button onClick={() => setShowDialog(false)}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleRegister}
              disabled={!guestName.trim()}
            >
              Confirm
            </Button>
          </DialogActions>
        )}
      </Dialog>
    </Box>
  );
};

export default InvitationPage;
