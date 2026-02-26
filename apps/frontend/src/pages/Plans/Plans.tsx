/**
 * Plans/Pricing Page
 *
 * Displays all available plans with pricing, features, and limits.
 * Users can select a plan to create an order.
 */
import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  CircularProgress,
  useTheme,
} from '@mui/material';
import {
  CheckCircle,
  Stars,
  Info,
  ArrowForward,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { plansApi, invitationsApi } from '../../services/api';
import { Plan } from '../../types';
import { useAuthStore } from '../../store/authStore';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

const Plans: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [creatingOrder, setCreatingOrder] = useState(false);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const response = await plansApi.getPlans();
      if (response.success && response.data) {
        // Sort plans by price
        const sortedPlans = response.data.sort((a: Plan, b: Plan) => a.price_inr - b.price_inr);
        setPlans(sortedPlans);
      }
    } catch (err: any) {
      console.error('Failed to fetch plans:', err);
      setError('Failed to load plans. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = async (planCode: string) => {
    if (!isAuthenticated) {
      // Redirect to login with return URL
      navigate('/login?redirect=/plans');
      return;
    }

    try {
      setCreatingOrder(true);
      setSelectedPlan(planCode);

      // Create order with this plan
      const response = await invitationsApi.createOrder({
        plan_code: planCode,
        event_type: 'GENERAL',
        event_type_name: 'General Event',
      });

      if (response.success && response.data) {
        // Redirect to payment/order details
        navigate(`/dashboard/orders`);
      }
    } catch (err: any) {
      console.error('Failed to create order:', err);
      setError(err.response?.data?.message || 'Failed to create order. Please try again.');
    } finally {
      setCreatingOrder(false);
      setSelectedPlan(null);
    }
  };

  const getPlanIcon = (code: string) => {
    switch (code) {
      case 'PREMIUM':
        return Stars;
      default:
        return CheckCircle;
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.main}15 0%, ${theme.palette.secondary.main}15 100%)`,
          pt: { xs: 6, md: 8 },
          pb: { xs: 6, md: 8 },
        }}
      >
        <Container maxWidth="lg">
          <Box textAlign="center" maxWidth={800} mx="auto">
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '2rem', md: '3rem' },
                fontWeight: 800,
                mb: 2,
              }}
            >
              Choose Your Perfect Plan
            </Typography>
            <Typography variant="h5" color="text.secondary" sx={{ mb: 1 }}>
              Simple, transparent pricing for beautiful digital invitations
            </Typography>
            <Typography variant="body1" color="text.secondary">
              One-time payment. No subscriptions. Full access to all features.
            </Typography>
          </Box>
        </Container>
      </Box>

      {/* Error Alert */}
      {error && (
        <Container maxWidth="lg" sx={{ mt: 4 }}>
          <Alert severity="error" onClose={() => setError('')}>
            {error}
          </Alert>
        </Container>
      )}

      {/* Plans Grid */}
      <Box sx={{ py: 8 }}>
        <Container maxWidth="lg">
          {plans.length === 0 ? (
            <Box textAlign="center" py={8}>
              <Info sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No plans available at the moment.
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={4} justifyContent="center">
              {plans.map((plan, index) => {
                const Icon = getPlanIcon(plan.code);
                const isPopular = plan.code === 'PREMIUM';
                const isProcessing = creatingOrder && selectedPlan === plan.code;

                return (
                  <Grid item xs={12} md={4} key={plan.code}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                    >
                      <Card
                        sx={{
                          height: '100%',
                          position: 'relative',
                          border: isPopular ? 2 : 1,
                          borderColor: isPopular ? 'primary.main' : 'divider',
                          boxShadow: isPopular ? theme.shadows[8] : theme.shadows[2],
                          transition: 'transform 0.3s, box-shadow 0.3s',
                          '&:hover': {
                            transform: 'translateY(-8px)',
                            boxShadow: theme.shadows[12],
                          },
                        }}
                      >
                        {isPopular && (
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
                              zIndex: 1,
                            }}
                          />
                        )}

                        <CardContent sx={{ p: 4 }}>
                          {/* Icon */}
                          <Box
                            sx={{
                              width: 60,
                              height: 60,
                              borderRadius: '50%',
                              bgcolor: `${theme.palette.primary.main}15`,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              mb: 2,
                            }}
                          >
                            <Icon sx={{ color: 'primary.main', fontSize: 32 }} />
                          </Box>

                          {/* Plan Name */}
                          <Typography variant="h4" fontWeight={700} gutterBottom>
                            {plan.name}
                          </Typography>

                          {/* Description */}
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 3, minHeight: 40 }}>
                            {plan.description}
                          </Typography>

                          {/* Price */}
                          <Box sx={{ mb: 4 }}>
                            <Typography variant="h2" fontWeight={800} color="primary.main">
                              ₹{plan.price_inr}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              one-time payment
                            </Typography>
                          </Box>

                          {/* Features */}
                          <List sx={{ mb: 3 }}>
                            {/* Links Info */}
                            <ListItem disablePadding sx={{ mb: 1 }}>
                              <ListItemIcon sx={{ minWidth: 36 }}>
                                <CheckCircle color="success" />
                              </ListItemIcon>
                              <ListItemText
                                primary={`${plan.regular_links} Invitation Links`}
                                primaryTypographyProps={{ fontWeight: 600 }}
                              />
                            </ListItem>

                            <ListItem disablePadding sx={{ mb: 1 }}>
                              <ListItemIcon sx={{ minWidth: 36 }}>
                                <CheckCircle color="success" />
                              </ListItemIcon>
                              <ListItemText
                                primary={`${plan.test_links} Test Links`}
                                primaryTypographyProps={{ fontWeight: 600 }}
                              />
                            </ListItem>

                            {/* Plan Features */}
                            {plan.features.map((feature: string, i: number) => (
                              <ListItem key={i} disablePadding sx={{ mb: 0.5 }}>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                  <CheckCircle color="success" fontSize="small" />
                                </ListItemIcon>
                                <ListItemText
                                  primary={feature}
                                  primaryTypographyProps={{ variant: 'body2' }}
                                />
                              </ListItem>
                            ))}
                          </List>

                          {/* CTA Button */}
                          <Button
                            variant={isPopular ? 'contained' : 'outlined'}
                            fullWidth
                            size="large"
                            endIcon={isProcessing ? <CircularProgress size={20} color="inherit" /> : <ArrowForward />}
                            onClick={() => handleSelectPlan(plan.code)}
                            disabled={isProcessing || !plan.is_active}
                          >
                            {isProcessing ? 'Creating Order...' : 'Select Plan'}
                          </Button>

                          {!isAuthenticated && (
                            <Typography variant="caption" color="text.secondary" display="block" textAlign="center" mt={1}>
                              You'll be asked to login first
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                );
              })}
            </Grid>
          )}

          {/* Additional Info */}
          <Box sx={{ mt: 8, textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom fontWeight={600}>
              Not sure which plan to choose?
            </Typography>
            <Typography variant="body1" color="text.secondary" mb={3}>
              All plans include access to our beautiful templates, AI features, and guest management.
              Choose based on how many invitations you need.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button
                component={Link}
                to="/templates"
                variant="outlined"
                size="large"
              >
                View Templates
              </Button>
              <Button
                component={Link}
                to="/register"
                variant="contained"
                size="large"
              >
                Get Started Free
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* FAQ Section */}
      <Box sx={{ py: 8, bgcolor: 'background.paper' }}>
        <Container maxWidth="md">
          <Typography variant="h4" textAlign="center" gutterBottom fontWeight={700}>
            Frequently Asked Questions
          </Typography>

          <Box sx={{ mt: 4 }}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                What's included in all plans?
              </Typography>
              <Typography variant="body2" color="text.secondary">
                All plans include access to all templates, AI message generation, animated invitations,
                guest RSVP tracking, and unlimited views on your invitations.
              </Typography>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                How do test links work?
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Test links let you preview your invitation and share it with family to get feedback
                before sending the final version to all guests. They don't count toward your plan limit.
              </Typography>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                Can I upgrade later?
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Yes! You can purchase additional links or upgrade to a higher plan anytime.
                Contact our support for assistance.
              </Typography>
            </Box>

            <Box>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                Is there a free trial?
              </Typography>
              <Typography variant="body2" color="text.secondary">
                You can create an account for free and explore all features. Test links are available
                on all plans so you can try before committing to your final invitation.
              </Typography>
            </Box>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default Plans;
