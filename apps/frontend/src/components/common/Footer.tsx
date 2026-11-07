/**
 * Footer Component
 */
import React from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Typography,
  IconButton,
  Divider,
} from '@mui/material';
import {
  CardGiftcard,
  Facebook,
  Instagram,
  Twitter,
  WhatsApp,
} from '@mui/icons-material';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    product: [
      { label: 'Plans', path: '/plans' },
      { label: 'Templates', path: '/templates' },
      { label: 'How it Works', path: '/#how-it-works' },
      { label: 'Pricing', path: '/plans' },
    ],
    support: [
      { label: 'Help Center', path: '/help' },
      { label: 'Contact Us', path: '/contact' },
      { label: 'FAQ', path: '/faq' },
    ],
    legal: [
      { label: 'Privacy Policy', path: '/privacy' },
      { label: 'Terms of Service', path: '/terms' },
      { label: 'Refund Policy', path: '/refund' },
    ],
  };

  const socialLinks = [
    { icon: Facebook, href: '#', label: 'Facebook' },
    { icon: Instagram, href: '#', label: 'Instagram' },
    { icon: Twitter, href: '#', label: 'Twitter' },
    { icon: WhatsApp, href: '#', label: 'WhatsApp' },
  ];

  return (
    <Box
      component="footer"
      sx={{
        bgcolor: 'background.paper',
        borderTop: '1px solid',
        borderColor: 'divider',
        pt: 6,
        pb: 3,
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          {/* Brand */}
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <CardGiftcard color="primary" fontSize="large" />
              <Typography variant="h5" fontWeight={700} color="primary.main">
                InviteMe
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 300 }}>
              Create beautiful, animated digital invitations for weddings, 
              birthdays, and special occasions. Share the joy with your loved ones.
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {socialLinks.map((social) => (
                <IconButton
                  key={social.label}
                  component="a"
                  href={social.href}
                  size="small"
                  sx={{
                    color: 'text.secondary',
                    '&:hover': { color: 'primary.main' },
                  }}
                  aria-label={social.label}
                >
                  <social.icon />
                </IconButton>
              ))}
            </Box>
          </Grid>

          {/* Links */}
          <Grid item xs={6} sm={3} md={2}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Product
            </Typography>
            <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
              {footerLinks.product.map((link) => (
                <Box component="li" key={link.label} sx={{ mb: 1 }}>
                  <Typography
                    component={Link}
                    to={link.path}
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      textDecoration: 'none',
                      '&:hover': { color: 'primary.main' },
                    }}
                  >
                    {link.label}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Grid>

          <Grid item xs={6} sm={3} md={2}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Support
            </Typography>
            <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
              {footerLinks.support.map((link) => (
                <Box component="li" key={link.label} sx={{ mb: 1 }}>
                  <Typography
                    component={Link}
                    to={link.path}
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      textDecoration: 'none',
                      '&:hover': { color: 'primary.main' },
                    }}
                  >
                    {link.label}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Grid>

          <Grid item xs={6} sm={3} md={2}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Legal
            </Typography>
            <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
              {footerLinks.legal.map((link) => (
                <Box component="li" key={link.label} sx={{ mb: 1 }}>
                  <Typography
                    component={Link}
                    to={link.path}
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      textDecoration: 'none',
                      '&:hover': { color: 'primary.main' },
                    }}
                  >
                    {link.label}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Grid>

          {/* Contact */}
          <Grid item xs={6} sm={3} md={2}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Contact
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              support@inviteme.in
            </Typography>
            <Typography variant="body2" color="text.secondary">
              +91 98765 43210
            </Typography>
          </Grid>
        </Grid>

        <Divider sx={{ my: 4 }} />

        {/* Copyright */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {currentYear} InviteMe. All rights reserved.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Made with love in India
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;
