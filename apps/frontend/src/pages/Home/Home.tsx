/**
 * Home Page
 */
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  useTheme,
} from '@mui/material';
import {
  AutoAwesome,
  Share,
  Security,
  Speed,
  Celebration,
  Favorite,
  Cake,
  Mosque,
  TempleHindu,
  Church,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { plansApi } from '../../services/api';
import { Plan, Template } from '../../types';

const Home: React.FC = () => {
  const theme = useTheme();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [featuredTemplates, setFeaturedTemplates] = useState<Template[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [plansRes, templatesRes] = await Promise.all([
          plansApi.getPlans(),
          plansApi.getFeaturedTemplates(),
        ]);
        if (plansRes.success) setPlans(plansRes.data || []);
        if (templatesRes.success) setFeaturedTemplates(templatesRes.data || []);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      }
    };
    fetchData();
  }, []);

  const features = [
    {
      icon: AutoAwesome,
      title: 'Beautiful Animations',
      description: 'Stunning animated templates that bring your invitations to life.',
    },
    {
      icon: Share,
      title: 'Easy Sharing',
      description: 'Share your invitation with a unique link via WhatsApp, email, or social media.',
    },
    {
      icon: Security,
      title: 'Secure & Private',
      description: 'Your data is safe with us. Control who can view your invitations.',
    },
    {
      icon: Speed,
      title: 'Quick Setup',
      description: 'Create and share your invitation in minutes with our easy-to-use builder.',
    },
  ];

  const categories = [
    { icon: Favorite, name: 'Wedding', color: '#E91E63' },
    { icon: Cake, name: 'Birthday', color: '#9C27B0' },
    { icon: Celebration, name: 'Party', color: '#FF9800' },
    { icon: Mosque, name: 'Eid', color: '#4CAF50' },
    { icon: TempleHindu, name: 'Diwali', color: '#FF5722' },
    { icon: Church, name: 'Christmas', color: '#2196F3' },
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.main}15 0%, ${theme.palette.secondary.main}15 100%)`,
          pt: { xs: 8, md: 12 },
          pb: { xs: 8, md: 12 },
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="center">
            <Grid item xs={12} md={6}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
              >
                <Chip
                  label="India's #1 Digital Invitation Platform"
                  color="primary"
                  size="small"
                  sx={{ mb: 2, fontWeight: 600 }}
                />
                <Typography
                  variant="h1"
                  sx={{
                    fontSize: { xs: '2.5rem', md: '3.5rem' },
                    fontWeight: 800,
                    lineHeight: 1.2,
                    mb: 3,
                  }}
                >
                  Create Beautiful{' '}
                  <Box component="span" color="primary.main">
                    Digital Invitations
                  </Box>{' '}
                  in Minutes
                </Typography>
                <Typography variant="h5" color="text.secondary" sx={{ mb: 4, maxWidth: 500 }}>
                  Wedding, Birthday, Festivals & more. Share animated invitations 
                  with your loved ones through unique links.
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    component={Link}
                    to="/plans"
                    variant="contained"
                    size="large"
                    sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
                  >
                    Get Started
                  </Button>
                  <Button
                    component={Link}
                    to="/templates"
                    variant="outlined"
                    size="large"
                    sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
                  >
                    View Templates
                  </Button>
                </Box>
              </motion.div>
            </Grid>
            <Grid item xs={12} md={6}>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8, delay: 0.2 }}
              >
                <Box
                  component="img"
                  src="/images/hero-invitation.png"
                  alt="Digital Invitation Preview"
                  sx={{
                    width: '100%',
                    maxWidth: 600,
                    borderRadius: 4,
                    boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
                  }}
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'https://via.placeholder.com/600x400/7B2CBF/FFFFFF?text=Beautiful+Invitations';
                  }}
                />
              </motion.div>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Categories Section */}
      <Box sx={{ py: 8, bgcolor: 'background.paper' }}>
        <Container maxWidth="lg">
          <Typography variant="h2" textAlign="center" gutterBottom>
            Choose Your Occasion
          </Typography>
          <Typography variant="h6" color="text.secondary" textAlign="center" sx={{ mb: 6 }}>
            We have templates for every special moment
          </Typography>
          
          <Grid container spacing={3} justifyContent="center">
            {categories.map((category, index) => (
              <Grid item key={category.name}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Card
                    component={Link}
                    to={`/templates?category=${category.name.toUpperCase()}`}
                    sx={{
                      width: 140,
                      height: 140,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      textDecoration: 'none',
                      transition: 'transform 0.3s, box-shadow 0.3s',
                      '&:hover': {
                        transform: 'translateY(-8px)',
                        boxShadow: theme.shadows[8],
                      },
                    }}
                  >
                    <Box
                      sx={{
                        width: 60,
                        height: 60,
                        borderRadius: '50%',
                        bgcolor: `${category.color}20`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mb: 1,
                      }}
                    >
                      <category.icon sx={{ color: category.color, fontSize: 32 }} />
                    </Box>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {category.name}
                    </Typography>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Box sx={{ py: 8 }}>
        <Container maxWidth="lg">
          <Typography variant="h2" textAlign="center" gutterBottom>
            Why Choose Us
          </Typography>
          <Typography variant="h6" color="text.secondary" textAlign="center" sx={{ mb: 6 }}>
            Everything you need to create stunning invitations
          </Typography>

          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={3} key={feature.title}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Card sx={{ height: '100%', textAlign: 'center', p: 3 }}>
                    <Box
                      sx={{
                        width: 80,
                        height: 80,
                        borderRadius: '50%',
                        bgcolor: 'primary.main',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mx: 'auto',
                        mb: 2,
                      }}
                    >
                      <feature.icon sx={{ color: 'white', fontSize: 40 }} />
                    </Box>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Pricing Section */}
      <Box sx={{ py: 8, bgcolor: 'background.paper' }}>
        <Container maxWidth="lg">
          <Typography variant="h2" textAlign="center" gutterBottom>
            Simple Pricing
          </Typography>
          <Typography variant="h6" color="text.secondary" textAlign="center" sx={{ mb: 6 }}>
            Choose the plan that fits your needs
          </Typography>

          <Grid container spacing={4} justifyContent="center">
            {plans.map((plan, index) => (
              <Grid item xs={12} md={4} key={plan.code}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Card
                    sx={{
                      height: '100%',
                      position: 'relative',
                      border: plan.code === 'PREMIUM' ? 2 : 0,
                      borderColor: 'primary.main',
                    }}
                  >
                    {plan.code === 'PREMIUM' && (
                      <Chip
                        label="Most Popular"
                        color="primary"
                        size="small"
                        sx={{
                          position: 'absolute',
                          top: -12,
                          left: '50%',
                          transform: 'translateX(-50%)',
                          fontWeight: 600,
                        }}
                      />
                    )}
                    <CardContent sx={{ p: 4, textAlign: 'center' }}>
                      <Typography variant="h5" fontWeight={700} gutterBottom>
                        {plan.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        {plan.description}
                      </Typography>
                      
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="h3" fontWeight={800} color="primary.main">
                          Rs. {plan.price_inr}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          one-time payment
                        </Typography>
                      </Box>

                      <Box sx={{ mb: 3, textAlign: 'left' }}>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>{plan.regular_links}</strong> Invitation Links
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>{plan.test_links}</strong> Test Links
                        </Typography>
                        {plan.features.map((feature: string, i: number) => (
                          <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>
                            {feature}
                          </Typography>
                        ))}
                      </Box>

                      <Button
                        component={Link}
                        to="/register"
                        variant={plan.code === 'PREMIUM' ? 'contained' : 'outlined'}
                        fullWidth
                        size="large"
                      >
                        Get Started
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box
        sx={{
          py: 8,
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h2" color="white" gutterBottom>
            Ready to Create Your Invitation?
          </Typography>
          <Typography variant="h6" color="rgba(255,255,255,0.9)" sx={{ mb: 4 }}>
            Join thousands of happy users who created beautiful invitations with us
          </Typography>
          <Button
            component={Link}
            to="/register"
            variant="contained"
            size="large"
            sx={{
              bgcolor: 'white',
              color: 'primary.main',
              px: 6,
              py: 1.5,
              fontSize: '1.1rem',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.9)',
              },
            }}
          >
            Create Your Invitation Now
          </Button>
        </Container>
      </Box>
    </Box>
  );
};

export default Home;
