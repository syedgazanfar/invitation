/**
 * Birthday Invitation Template
 * Fun and Modern animation styles
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Chip,
} from '@mui/material';
import {
  Cake,
  LocationOn,
  CalendarToday,
  Celebration,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface BirthdayTemplateProps {
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

// Confetti component
const Confetti: React.FC = () => {
  const colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#FF6B9D', '#C9B1FF'];
  const confetti = Array.from({ length: 50 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    color: colors[Math.floor(Math.random() * colors.length)],
    delay: Math.random() * 3,
    duration: 3 + Math.random() * 2,
    size: 5 + Math.random() * 10,
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
      {confetti.map((piece) => (
        <motion.div
          key={piece.id}
          style={{
            position: 'absolute',
            left: `${piece.x}%`,
            top: -20,
            width: piece.size,
            height: piece.size,
            backgroundColor: piece.color,
            borderRadius: Math.random() > 0.5 ? '50%' : 0,
          }}
          animate={{
            y: [0, window.innerHeight + 50],
            rotate: [0, 720],
            opacity: [1, 1, 0],
          }}
          transition={{
            duration: piece.duration,
            delay: piece.delay,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      ))}
    </Box>
  );
};

const BirthdayTemplate: React.FC<BirthdayTemplateProps> = ({
  invitation,
  onOpenRegistration,
  alreadyRegistered,
  guestName,
}) => {
  const [countdown, setCountdown] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });

  useEffect(() => {
    const eventDate = new Date(invitation.event_date);
    
    const updateCountdown = () => {
      const now = new Date();
      const diff = eventDate.getTime() - now.getTime();
      
      if (diff > 0) {
        setCountdown({
          days: Math.floor(diff / (1000 * 60 * 60 * 24)),
          hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
          minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
          seconds: Math.floor((diff % (1000 * 60)) / 1000),
        });
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [invitation.event_date]);

  const theme = invitation.template_theme || {
    primary: '#FF6B6B',
    secondary: '#4ECDC4',
    accent: '#FFE66D',
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${theme.primary}20 0%, ${theme.secondary}20 50%, ${theme.accent}20 100%)`,
        position: 'relative',
      }}
    >
      <Confetti />

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
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: 'center', zIndex: 1 }}>
          {/* Cake Icon Animation */}
          <motion.div
            animate={{ 
              y: [0, -20, 0],
              rotate: [0, 5, -5, 0],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Cake sx={{ fontSize: 100, color: theme.primary, mb: 3 }} />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, type: 'spring' }}
          >
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '3rem', md: '5rem' },
                fontWeight: 800,
                background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.secondary} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 2,
              }}
            >
              {invitation.event_title}
            </Typography>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Typography variant="h5" color="text.secondary" gutterBottom>
              Hosted by {invitation.host_name}
            </Typography>
          </motion.div>

          {/* Countdown */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            style={{ marginTop: 40 }}
          >
            <Typography variant="h6" gutterBottom color="text.secondary">
              Party starts in:
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
              {[
                { value: countdown.days, label: 'Days' },
                { value: countdown.hours, label: 'Hours' },
                { value: countdown.minutes, label: 'Minutes' },
                { value: countdown.seconds, label: 'Seconds' },
              ].map((item, index) => (
                <Box
                  key={index}
                  sx={{
                    bgcolor: 'white',
                    px: 3,
                    py: 2,
                    borderRadius: 2,
                    boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
                    textAlign: 'center',
                    minWidth: 80,
                  }}
                >
                  <Typography variant="h4" fontWeight={700} color={theme.primary}>
                    {String(item.value).padStart(2, '0')}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {item.label}
                  </Typography>
                </Box>
              ))}
            </Box>
          </motion.div>
        </Container>
      </Box>

      {/* Event Details */}
      <Container maxWidth="md" sx={{ py: 8 }}>
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <Box
            sx={{
              bgcolor: 'white',
              p: { xs: 3, md: 6 },
              borderRadius: 4,
              boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
            }}
          >
            <Typography variant="h4" textAlign="center" fontWeight={700} gutterBottom>
              <Celebration sx={{ color: theme.primary, mr: 1, verticalAlign: 'middle' }} />
              Party Details
            </Typography>

            <Box sx={{ mt: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <CalendarToday sx={{ color: theme.primary, mr: 2, fontSize: 30 }} />
                <Box>
                  <Typography variant="h6">Date & Time</Typography>
                  <Typography color="text.secondary">
                    {new Date(invitation.event_date).toLocaleDateString('en-IN', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <LocationOn sx={{ color: theme.primary, mr: 2, fontSize: 30 }} />
                <Box>
                  <Typography variant="h6">Venue</Typography>
                  <Typography color="text.secondary">{invitation.event_venue}</Typography>
                  {invitation.event_address && (
                    <Typography variant="body2" color="text.secondary">
                      {invitation.event_address}
                    </Typography>
                  )}
                </Box>
              </Box>

              {invitation.custom_message && (
                <Box
                  sx={{
                    mt: 4,
                    p: 3,
                    bgcolor: `${theme.primary}10`,
                    borderRadius: 2,
                    borderLeft: `4px solid ${theme.primary}`,
                  }}
                >
                  <Typography variant="body1" fontStyle="italic">
                    "{invitation.custom_message}"
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        </motion.div>
      </Container>

      {/* RSVP Section */}
      <Box sx={{ py: 8, textAlign: 'center', bgcolor: 'white' }}>
        <Container maxWidth="sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Let's Celebrate Together!
            </Typography>
            
            {alreadyRegistered ? (
              <Box sx={{ mt: 4 }}>
                <Typography variant="h5" color={theme.primary} gutterBottom>
                  Hey {guestName}! You're on the list!
                </Typography>
                <Chip
                  label="See you at the party!"
                  color="success"
                  sx={{ fontSize: '1.1rem', py: 2 }}
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
                  '&:hover': {
                    bgcolor: theme.secondary,
                    transform: 'scale(1.05)',
                  },
                  transition: 'all 0.3s',
                }}
              >
                I'm Coming!
              </Button>
            )}
          </motion.div>
        </Container>
      </Box>

      {/* Gallery */}
      {invitation.gallery_images.length > 0 && (
        <Box sx={{ py: 8 }}>
          <Container maxWidth="lg">
            <Typography variant="h4" textAlign="center" fontWeight={700} gutterBottom>
              Photo Gallery
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: 2,
                mt: 4,
              }}
            >
              {invitation.gallery_images.map((image, index) => (
                <motion.div
                  key={index}
                  whileHover={{ scale: 1.05 }}
                  transition={{ duration: 0.3 }}
                >
                  <Box
                    component="img"
                    src={image}
                    alt={`Gallery ${index + 1}`}
                    sx={{
                      width: '100%',
                      height: 250,
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
    </Box>
  );
};

export default BirthdayTemplate;
