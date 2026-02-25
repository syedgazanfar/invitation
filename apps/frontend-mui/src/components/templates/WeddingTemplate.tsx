/**
 * Wedding Invitation Template
 * Elegant, Royal, and Floral animation styles
 */
import React, { useEffect, useState, useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Chip,
  Fade,
} from '@mui/material';
import {
  Favorite,
  LocationOn,
  CalendarToday,
  AccessTime,
} from '@mui/icons-material';
import { motion, useScroll, useTransform } from 'framer-motion';

interface WeddingTemplateProps {
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

// Floating hearts animation component
const FloatingHearts: React.FC = () => {
  const hearts = Array.from({ length: 15 }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 5,
    duration: 5 + Math.random() * 5,
    size: 10 + Math.random() * 20,
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
      {hearts.map((heart) => (
        <motion.div
          key={heart.id}
          style={{
            position: 'absolute',
            left: `${heart.left}%`,
            bottom: -50,
            fontSize: heart.size,
          }}
          animate={{
            y: [0, -window.innerHeight - 100],
            opacity: [0, 1, 1, 0],
            rotate: [0, 360],
          }}
          transition={{
            duration: heart.duration,
            delay: heart.delay,
            repeat: Infinity,
            ease: 'linear',
          }}
        >
          <Favorite sx={{ color: 'rgba(255, 107, 107, 0.3)' }} />
        </motion.div>
      ))}
    </Box>
  );
};

const WeddingTemplate: React.FC<WeddingTemplateProps> = ({
  invitation,
  onOpenRegistration,
  alreadyRegistered,
  guestName,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  const backgroundY = useTransform(scrollYProgress, [0, 1], ['0%', '30%']);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0.5]);

  // Auto-rotate gallery images
  useEffect(() => {
    if (invitation.gallery_images.length > 1) {
      const interval = setInterval(() => {
        setCurrentImageIndex((prev) => (prev + 1) % invitation.gallery_images.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [invitation.gallery_images]);

  const theme = invitation.template_theme || {
    primary: '#A61E2A',
    secondary: '#2E2E2E',
    accent: '#D9D9D9',
    background: '#F5F2ED',
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        minHeight: '100vh',
        bgcolor: '#FFF8F0',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <FloatingHearts />

      {/* Hero Section */}
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          background: `linear-gradient(180deg, ${theme.background} 0%, #ffffff 100%)`,
          px: 3,
        }}
      >
        {/* Decorative Elements */}
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 1.5, type: 'spring' }}
          style={{
            position: 'absolute',
            top: '10%',
            left: '5%',
          }}
        >
          <Box
            component="img"
            src="/images/floral-decoration.png"
            alt=""
            sx={{ width: 150, opacity: 0.6 }}
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
          />
        </motion.div>

        <motion.div
          initial={{ scale: 0, rotate: 180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 1.5, type: 'spring' }}
          style={{
            position: 'absolute',
            top: '10%',
            right: '5%',
          }}
        >
          <Box
            component="img"
            src="/images/floral-decoration.png"
            alt=""
            sx={{ width: 150, opacity: 0.6, transform: 'scaleX(-1)' }}
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
          />
        </motion.div>

        {/* Main Content */}
        <Container maxWidth="md" sx={{ textAlign: 'center', zIndex: 1 }}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.5 }}
          >
            <Typography
              variant="h6"
              sx={{
                color: theme.secondary,
                letterSpacing: 4,
                textTransform: 'uppercase',
                mb: 2,
              }}
            >
              You're Invited To
            </Typography>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.8 }}
          >
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '2.5rem', md: '4.5rem' },
                fontWeight: 700,
                color: theme.primary,
                fontFamily: '"Playfair Display", serif',
                mb: 2,
                textShadow: '2px 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              {invitation.event_title}
            </Typography>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 1.2 }}
          >
            <Typography
              variant="h5"
              sx={{
                color: theme.secondary,
                mb: 4,
                fontStyle: 'italic',
              }}
            >
              Hosted by {invitation.host_name}
            </Typography>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 1.5 }}
          >
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 2,
                bgcolor: 'white',
                px: 4,
                py: 2,
                borderRadius: 4,
                boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
              }}
            >
              <CalendarToday sx={{ color: theme.primary }} />
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

          {/* Scroll Indicator */}
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{ marginTop: 60 }}
          >
            <Typography variant="body2" color="text.secondary">
              Scroll down for more details
            </Typography>
          </motion.div>
        </Container>
      </Box>

      {/* Details Section */}
      <Container maxWidth="md" sx={{ py: 8, position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <Paper
            elevation={0}
            sx={{
              p: { xs: 3, md: 6 },
              borderRadius: 4,
              bgcolor: 'white',
              textAlign: 'center',
            }}
          >
            <Typography variant="h4" fontWeight={700} gutterBottom color={theme.primary}>
              Event Details
            </Typography>

            <Box sx={{ my: 4 }}>
              <LocationOn sx={{ fontSize: 40, color: theme.primary, mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                {invitation.event_venue}
              </Typography>
              {invitation.event_address && (
                <Typography variant="body1" color="text.secondary">
                  {invitation.event_address}
                </Typography>
              )}
              {invitation.event_map_link && (
                <Button
                  variant="outlined"
                  href={invitation.event_map_link}
                  target="_blank"
                  sx={{ mt: 2 }}
                >
                  View on Map
                </Button>
              )}
            </Box>

            {invitation.custom_message && (
              <Box sx={{ mt: 4, p: 3, bgcolor: `${theme.primary}10`, borderRadius: 2 }}>
                <Typography variant="body1" fontStyle="italic">
                  "{invitation.custom_message}"
                </Typography>
              </Box>
            )}
          </Paper>
        </motion.div>
      </Container>

      {/* Gallery Section */}
      {invitation.gallery_images.length > 0 && (
        <Box sx={{ py: 8, bgcolor: `${theme.primary}10` }}>
          <Container maxWidth="lg">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
            >
              <Typography variant="h4" textAlign="center" fontWeight={700} gutterBottom>
                Gallery
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
            </motion.div>
          </Container>
        </Box>
      )}

      {/* RSVP Section */}
      <Box sx={{ py: 8, textAlign: 'center' }}>
        <Container maxWidth="sm">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <Typography variant="h4" fontWeight={700} gutterBottom>
              We would love to see you there!
            </Typography>
            
            {alreadyRegistered ? (
              <Box sx={{ mt: 4 }}>
                <Typography variant="h5" color={theme.primary} gutterBottom>
                  Welcome back, {guestName}!
                </Typography>
                <Chip
                  label="You're on the guest list"
                  color="success"
                  size="large"
                  sx={{ fontSize: '1.1rem', py: 2, px: 3 }}
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
                  '&:hover': { bgcolor: theme.secondary },
                }}
              >
                RSVP Now
              </Button>
            )}
          </motion.div>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ py: 4, textAlign: 'center', bgcolor: `${theme.primary}10` }}>
        <Typography variant="body2" color="text.secondary">
          Created with InviteMe | Digital Invitation Platform
        </Typography>
      </Box>
    </Box>
  );
};

// Need to import Paper
import { Paper } from '@mui/material';

export default WeddingTemplate;
