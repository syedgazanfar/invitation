/**
 * Festival Invitation Template (Diwali, Eid, etc.)
 * Traditional animation style
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
  WbSunny,
  Brightness3,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

interface FestivalTemplateProps {
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

// Floating Diya/Lantern animation
const FloatingLanterns: React.FC<{ color: string }> = ({ color }) => {
  const lanterns = Array.from({ length: 12 }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 4,
    duration: 6 + Math.random() * 4,
    size: 20 + Math.random() * 30,
  }));

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
        zIndex: 0,
      }}
    >
      {lanterns.map((lantern) => (
        <motion.div
          key={lantern.id}
          style={{
            position: 'absolute',
            left: `${lantern.left}%`,
            bottom: -60,
          }}
          animate={{
            y: [0, -window.innerHeight - 100],
            x: [0, Math.sin(lantern.id) * 30, 0],
            opacity: [0, 1, 1, 0],
          }}
          transition={{
            duration: lantern.duration,
            delay: lantern.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          <Box
            sx={{
              width: lantern.size,
              height: lantern.size * 1.3,
              bgcolor: color,
              borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
              opacity: 0.6,
              boxShadow: `0 0 30px ${color}`,
            }}
          />
        </motion.div>
      ))}
    </Box>
  );
};

const FestivalTemplate: React.FC<FestivalTemplateProps> = ({
  invitation,
  onOpenRegistration,
  alreadyRegistered,
  guestName,
}) => {
  const theme = invitation.template_theme || {
    primary: '#FF6F00',
    secondary: '#FFD700',
    accent: '#FF4500',
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: '#1a1a2e',
        color: 'white',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <FloatingLanterns color={theme.secondary} />

      {/* Background Pattern */}
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            radial-gradient(circle at 20% 50%, ${theme.primary}20 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, ${theme.secondary}20 0%, transparent 50%)
          `,
          zIndex: 0,
        }}
      />

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
        {/* Decorative Border */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.5 }}
          style={{
            position: 'absolute',
            top: 20,
            left: 20,
            right: 20,
            bottom: 20,
            border: `2px solid ${theme.secondary}`,
            borderRadius: 20,
            pointerEvents: 'none',
          }}
        />

        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          {/* Greeting */}
          <motion.div
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Typography
              variant="h6"
              sx={{
                color: theme.secondary,
                letterSpacing: 8,
                textTransform: 'uppercase',
                mb: 2,
              }}
            >
              Warm Greetings
            </Typography>
          </motion.div>

          {/* Main Title */}
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.3, type: 'spring' }}
          >
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '2.5rem', md: '4.5rem' },
                fontWeight: 700,
                background: `linear-gradient(135deg, ${theme.secondary} 0%, ${theme.primary} 50%, ${theme.accent} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                textShadow: `0 0 40px ${theme.secondary}50`,
                mb: 3,
              }}
            >
              {invitation.event_title}
            </Typography>
          </motion.div>

          {/* Host */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            <Typography variant="h5" sx={{ color: 'rgba(255,255,255,0.8)', mb: 4 }}>
              Hosted by{' '}
              <Box component="span" sx={{ color: theme.secondary, fontWeight: 600 }}>
                {invitation.host_name}
              </Box>
            </Typography>
          </motion.div>

          {/* Date Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.1 }}
          >
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 2,
                bgcolor: 'rgba(0,0,0,0.4)',
                backdropFilter: 'blur(10px)',
                px: 4,
                py: 2,
                borderRadius: 3,
                border: `1px solid ${theme.secondary}50`,
              }}
            >
              <CalendarToday sx={{ color: theme.secondary }} />
              <Typography variant="h6">
                {new Date(invitation.event_date).toLocaleDateString('en-IN', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </Typography>
            </Box>
          </motion.div>
        </Container>
      </Box>

      {/* Event Details */}
      <Container maxWidth="md" sx={{ py: 8, position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <Box
            sx={{
              bgcolor: 'rgba(0,0,0,0.5)',
              backdropFilter: 'blur(10px)',
              p: { xs: 3, md: 6 },
              borderRadius: 4,
              border: `1px solid ${theme.secondary}30`,
              textAlign: 'center',
            }}
          >
            <Typography variant="h4" fontWeight={700} gutterBottom sx={{ color: theme.secondary }}>
              Celebrations At
            </Typography>

            <Box sx={{ my: 4 }}>
              <LocationOn sx={{ fontSize: 50, color: theme.primary, mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                {invitation.event_venue}
              </Typography>
              {invitation.event_address && (
                <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  {invitation.event_address}
                </Typography>
              )}
            </Box>

            {invitation.custom_message && (
              <Box
                sx={{
                  mt: 4,
                  p: 3,
                  bgcolor: `${theme.primary}20`,
                  borderRadius: 2,
                  border: `1px solid ${theme.secondary}30`,
                }}
              >
                <Typography variant="body1" fontStyle="italic" sx={{ color: 'rgba(255,255,255,0.9)' }}>
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
              sx={{ color: theme.secondary }}
            >
              Memories
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: 3,
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
                  whileHover={{ scale: 1.05, zIndex: 10 }}
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
                      border: `2px solid ${theme.secondary}50`,
                    }}
                  />
                </motion.div>
              ))}
            </Box>
          </Container>
        </Box>
      )}

      {/* RSVP */}
      <Box sx={{ py: 8, textAlign: 'center', position: 'relative', zIndex: 1 }}>
        <Container maxWidth="sm">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <Typography variant="h4" fontWeight={700} gutterBottom sx={{ color: theme.secondary }}>
              Bless Us With Your Presence
            </Typography>

            {alreadyRegistered ? (
              <Box sx={{ mt: 4 }}>
                <Typography variant="h5" sx={{ color: theme.primary }} gutterBottom>
                  Namaste, {guestName}!
                </Typography>
                <Chip
                  label="We eagerly await your arrival"
                  sx={{
                    bgcolor: `${theme.secondary}30`,
                    color: theme.secondary,
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
                  px: 6,
                  py: 2,
                  fontSize: '1.2rem',
                  bgcolor: theme.primary,
                  color: 'white',
                  '&:hover': {
                    bgcolor: theme.accent,
                  },
                  boxShadow: `0 10px 30px ${theme.primary}50`,
                }}
              >
                Accept Invitation
              </Button>
            )}
          </motion.div>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ py: 4, textAlign: 'center', borderTop: `1px solid ${theme.secondary}30` }}>
        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)' }}>
          Wishing you joy and prosperity | Created with InviteMe
        </Typography>
      </Box>
    </Box>
  );
};

export default FestivalTemplate;
