/**
 * Party Invitation Template
 * Modern and Minimal animation styles
 */
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Chip,
} from '@mui/material';
import {
  LocationOn,
  CalendarToday,
  AccessTime,
  MusicNote,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

interface PartyTemplateProps {
  invitation: {
    event_title: string;
    event_date: string;
    event_venue: string;
    event_address?: string;
    event_map_link?: string;
    host_name: string;
    custom_message?: string;
    banner_image: string;
    gallery_images: string[];
    template_theme: Record<string, string>;
  };
  onOpenRegistration: () => void;
  alreadyRegistered: boolean;
  guestName: string;
}

const PartyTemplate: React.FC<PartyTemplateProps> = ({
  invitation,
  onOpenRegistration,
  alreadyRegistered,
  guestName,
}) => {
  const theme = invitation.template_theme || {
    primary: '#9B59B6',
    secondary: '#3498DB',
    accent: '#E74C3C',
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: '#0f0f1e',
        color: 'white',
        position: 'relative',
      }}
    >
      {/* Gradient Background */}
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            linear-gradient(135deg, ${theme.primary}30 0%, transparent 50%),
            linear-gradient(225deg, ${theme.secondary}30 0%, transparent 50%),
            #0f0f1e
          `,
          zIndex: 0,
        }}
      />

      {/* Animated Background Circles */}
      <Box sx={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
        {[...Array(5)].map((_, i) => (
          <motion.div
            key={i}
            style={{
              position: 'absolute',
              width: 300 + i * 100,
              height: 300 + i * 100,
              borderRadius: '50%',
              border: `1px solid ${theme.primary}20`,
              top: `${20 + i * 15}%`,
              left: `${10 + i * 20}%`,
            }}
            animate={{ rotate: 360 }}
            transition={{ duration: 20 + i * 5, repeat: Infinity, ease: 'linear' }}
          />
        ))}
      </Box>

      {/* Hero Section */}
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          px: 3,
          zIndex: 1,
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          {/* Music Icon */}
          <motion.div
            animate={{ 
              scale: [1, 1.2, 1],
              rotate: [0, 10, -10, 0],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <MusicNote sx={{ fontSize: 80, color: theme.primary, mb: 3 }} />
          </motion.div>

          {/* Title */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '3rem', md: '5rem' },
                fontWeight: 800,
                textTransform: 'uppercase',
                letterSpacing: { xs: 4, md: 8 },
                background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.secondary} 50%, ${theme.accent} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 2,
              }}
            >
              {invitation.event_title}
            </Typography>
          </motion.div>

          {/* Subtitle */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <Typography variant="h5" sx={{ color: 'rgba(255,255,255,0.7)', mb: 4 }}>
              Hosted by {invitation.host_name}
            </Typography>
          </motion.div>

          {/* Date & Time */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            style={{ marginTop: 40 }}
          >
            <Box
              sx={{
                display: 'inline-flex',
                flexDirection: { xs: 'column', sm: 'row' },
                gap: 2,
                alignItems: 'center',
              }}
            >
              <Box
                sx={{
                  bgcolor: 'rgba(255,255,255,0.1)',
                  backdropFilter: 'blur(10px)',
                  px: 4,
                  py: 2,
                  borderRadius: 2,
                  border: `1px solid ${theme.primary}50`,
                }}
              >
                <CalendarToday sx={{ color: theme.primary, mb: 1 }} />
                <Typography variant="h6">
                  {new Date(invitation.event_date).toLocaleDateString('en-IN', {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                  })}
                </Typography>
              </Box>
              <Box
                sx={{
                  bgcolor: 'rgba(255,255,255,0.1)',
                  backdropFilter: 'blur(10px)',
                  px: 4,
                  py: 2,
                  borderRadius: 2,
                  border: `1px solid ${theme.secondary}50`,
                }}
              >
                <AccessTime sx={{ color: theme.secondary, mb: 1 }} />
                <Typography variant="h6">
                  {new Date(invitation.event_date).toLocaleTimeString('en-IN', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Typography>
              </Box>
            </Box>
          </motion.div>
        </Container>
      </Box>

      {/* Venue Section */}
      <Container maxWidth="md" sx={{ py: 8, position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <Box
            sx={{
              bgcolor: 'rgba(255,255,255,0.05)',
              backdropFilter: 'blur(10px)',
              p: { xs: 4, md: 6 },
              borderRadius: 4,
              textAlign: 'center',
              border: `1px solid rgba(255,255,255,0.1)`,
            }}
          >
            <LocationOn sx={{ fontSize: 50, color: theme.accent, mb: 2 }} />
            <Typography variant="h4" fontWeight={700} gutterBottom>
              {invitation.event_venue}
            </Typography>
            {invitation.event_address && (
              <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)', mb: 3 }}>
                {invitation.event_address}
              </Typography>
            )}
            {invitation.event_map_link && (
              <Button
                variant="outlined"
                href={invitation.event_map_link}
                target="_blank"
                sx={{
                  borderColor: theme.primary,
                  color: theme.primary,
                  '&:hover': {
                    borderColor: theme.secondary,
                    color: theme.secondary,
                  },
                }}
              >
                Get Directions
              </Button>
            )}

            {invitation.custom_message && (
              <Box
                sx={{
                  mt: 4,
                  p: 3,
                  bgcolor: 'rgba(255,255,255,0.05)',
                  borderRadius: 2,
                  borderLeft: `4px solid ${theme.primary}`,
                }}
              >
                <Typography variant="body1" fontStyle="italic" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                  "{invitation.custom_message}"
                </Typography>
              </Box>
            )}
          </Box>
        </motion.div>
      </Container>

      {/* Gallery */}
      {invitation.gallery_images.length > 0 && (
        <Box sx={{ py: 8, position: 'relative', zIndex: 1 }}>
          <Container maxWidth="lg">
            <Typography
              variant="h4"
              textAlign="center"
              fontWeight={700}
              gutterBottom
              sx={{ textTransform: 'uppercase', letterSpacing: 4 }}
            >
              Gallery
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: 2,
                mt: 4,
              }}
            >
              {invitation.gallery_images.map((image, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  whileHover={{ scale: 1.02 }}
                >
                  <Box
                    component="img"
                    src={image}
                    alt={`Gallery ${index + 1}`}
                    sx={{
                      width: '100%',
                      height: 300,
                      objectFit: 'cover',
                      borderRadius: 2,
                    }}
                  />
                </motion.div>
              ))}
            </Box>
          </Container>
        </Box>
      )}

      {/* RSVP Section */}
      <Box
        sx={{
          py: 10,
          textAlign: 'center',
          position: 'relative',
          zIndex: 1,
          background: `linear-gradient(180deg, transparent 0%, ${theme.primary}20 100%)`,
        }}
      >
        <Container maxWidth="sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <Typography
              variant="h4"
              fontWeight={700}
              gutterBottom
              sx={{ textTransform: 'uppercase', letterSpacing: 2 }}
            >
              Let's Party!
            </Typography>

            {alreadyRegistered ? (
              <Box sx={{ mt: 4 }}>
                <Typography variant="h5" sx={{ color: theme.primary }} gutterBottom>
                  See you there, {guestName}!
                </Typography>
                <Chip
                  label="You're on the guest list"
                  sx={{
                    bgcolor: `${theme.primary}30`,
                    color: 'white',
                    fontSize: '1.1rem',
                    py: 2,
                  }}
                />
              </Box>
            ) : (
              <Button
                variant="contained"
                size="large"
                onClick={onOpenRegistration}
                sx={{
                  mt: 4,
                  px: 8,
                  py: 2,
                  fontSize: '1.2rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: 2,
                  bgcolor: theme.primary,
                  background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.accent} 100%)`,
                  '&:hover': {
                    transform: 'scale(1.05)',
                  },
                  transition: 'all 0.3s',
                }}
              >
                I'm In!
              </Button>
            )}
          </motion.div>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ py: 4, textAlign: 'center', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)' }}>
          Powered by InviteMe | Digital Invitations
        </Typography>
      </Box>
    </Box>
  );
};

export default PartyTemplate;
