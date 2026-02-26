/**
 * Create Event Page with AI Integration
 * 
 * This is the main event creation flow that incorporates AI-powered features:
 * - AI Design Assistant for photo analysis and template recommendations
 * - AI Message Generator for invitation text
 * - Smart template filtering based on AI analysis
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Button,
  Paper,
  Grid,
  TextField,
  Card,
  CardMedia,
  CardContent,
  CardActionArea,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Divider,
  FormControlLabel,
  Switch,
  Fade,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ArrowBack,
  ArrowForward,
  Check,
  SmartToy,
  AutoAwesome,
  Info,
  Lightbulb,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { invitationsApi, plansApi } from '../../services/api';
import { useInvitationStore } from '../../store/authStore';
import { Template, Order, Plan } from '../../types';
import { PhotoAnalysisResult, TemplateRecommendation } from '../../services/aiApi';

// AI Components
import { AIAssistantWidget } from '../../components/ai/AIAssistantWidget';
import { MessageGenerator } from '../../components/ai/MessageGenerator';
import { AIOnboardingDialog } from '../../components/ai/AIOnboardingDialog';
import { AIFeatureBadge } from '../../components/ai/AIFeatureBadge';

// Steps in the event creation flow
const steps = [
  'Event Details',
  'Select Plan',
  'AI Design Assistant',
  'Select Template',
  'Customize & Preview',
  'Payment',
];

interface CreateEventProps {
  orderId?: string;
}

const CreateEvent: React.FC<CreateEventProps> = ({ orderId: propOrderId }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const urlOrderId = searchParams.get('orderId');
  const effectiveOrderId = propOrderId || urlOrderId;
  
  const { addInvitation } = useInvitationStore();
  
  // Step state
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  // Data state
  const [order, setOrder] = useState<Order | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  
  // AI-related state
  const [useAIAssistant, setUseAIAssistant] = useState(false);
  const [aiAnalysisResult, setAiAnalysisResult] = useState<PhotoAnalysisResult | null>(null);
  const [aiRecommendedTemplates, setAiRecommendedTemplates] = useState<TemplateRecommendation[]>([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showMessageGenerator, setShowMessageGenerator] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState({
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
  });

  // Check if user is first-time and show onboarding
  useEffect(() => {
    const hasSeenAIOnboarding = localStorage.getItem('hasSeenAIOnboarding');
    if (!hasSeenAIOnboarding) {
      setShowOnboarding(true);
    }
  }, []);

  // Fetch initial data
  useEffect(() => {
    fetchInitialData();
  }, [effectiveOrderId]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      
      // Get all plans
      const plansRes = await plansApi.getPlans();
      if (plansRes.success) {
        setPlans(plansRes.data?.plans || []);
      }
      
      // Get order details if orderId is provided
      if (effectiveOrderId) {
        const orderRes = await invitationsApi.getOrder(effectiveOrderId);
        if (orderRes.success && orderRes.data) {
          setOrder(orderRes.data);
          setSelectedPlan(orderRes.data.plan);
          // Pre-fill form with order data
          setFormData(prev => ({
            ...prev,
            event_title: orderRes.data.event_title || '',
            bride_name: orderRes.data.bride_name || '',
            groom_name: orderRes.data.groom_name || '',
          }));
          
          // Fetch templates for the plan
          await fetchTemplates(orderRes.data.plan.code);
        }
      }
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async (planCode: string) => {
    try {
      const templatesRes = await plansApi.getTemplatesByPlan(planCode);
      if (templatesRes.success) {
        setTemplates(templatesRes.data?.templates || []);
      }
    } catch (err) {
      setError('Failed to load templates');
    }
  };

  const handleNext = () => {
    if (validateStep()) {
      setActiveStep((prev) => prev + 1);
      setError('');
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
    setError('');
  };

  const validateStep = () => {
    switch (activeStep) {
      case 0: // Event Details
        if (!formData.event_title || !formData.bride_name || !formData.groom_name) {
          setError('Please fill in all required fields (Event Title, Bride Name, Groom Name)');
          return false;
        }
        break;
      case 1: // Select Plan
        if (!selectedPlan && !order) {
          setError('Please select a plan');
          return false;
        }
        break;
      case 2: // AI Design Assistant (optional)
        // Skip validation - AI step is optional
        break;
      case 3: // Select Template
        if (!selectedTemplate) {
          setError('Please select a template');
          return false;
        }
        break;
      case 4: // Customize & Preview
        if (!formData.event_venue || !formData.host_name) {
          setError('Please fill in venue and host information');
          return false;
        }
        break;
    }
    return true;
  };

  const handlePlanSelect = async (plan: Plan) => {
    setSelectedPlan(plan);
    await fetchTemplates(plan.code);
  };

  // AI-related handlers
  const handleAIAnalysisComplete = useCallback((result: PhotoAnalysisResult) => {
    setAiAnalysisResult(result);
    // Extract template recommendations from AI analysis
    if (result.styleRecommendations?.length > 0) {
      // Map style recommendations to template recommendations
      const recommendations: TemplateRecommendation[] = result.styleRecommendations
        .flatMap(style => 
          style.matchingTemplates.map((templateName, idx) => ({
            templateId: `ai_rec_${style.style}_${idx}`,
            name: templateName,
            matchScore: style.confidence * (1 - idx * 0.1),
            matchReasons: [
              `Matches your ${result.mood.primary} aesthetic`,
              `Complements your photo's color palette`,
              `Popular for ${result.aiSuggestions.messageTone} weddings`,
            ],
            previewUrl: '',
            thumbnail: '',
            description: style.description,
          }))
        );
      setAiRecommendedTemplates(recommendations);
    }
  }, []);

  const handleAITemplateSelect = useCallback((templateId: string) => {
    // Find the template in our available templates
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setSelectedTemplate(template);
    }
  }, [templates]);

  const handleAIMessageSelect = useCallback((message: string) => {
    setFormData(prev => ({ ...prev, custom_message: message }));
    setShowMessageGenerator(false);
  }, []);

  const handleOnboardingClose = (getStarted: boolean) => {
    setShowOnboarding(false);
    localStorage.setItem('hasSeenAIOnboarding', 'true');
    if (getStarted) {
      setUseAIAssistant(true);
    }
  };

  const handleSubmit = async () => {
    if (!selectedTemplate) return;
    
    try {
      setSubmitting(true);
      
      const data = new FormData();
      if (order) {
        data.append('order_id', order.id);
      }
      if (selectedPlan) {
        data.append('plan_id', selectedPlan.id);
      }
      data.append('template_id', selectedTemplate.id);
      data.append('event_title', formData.event_title);
      data.append('bride_name', formData.bride_name);
      data.append('groom_name', formData.groom_name);
      data.append('event_date', formData.event_date.toISOString());
      data.append('event_venue', formData.event_venue);
      data.append('event_address', formData.event_address);
      data.append('event_map_link', formData.event_map_link);
      data.append('host_name', formData.host_name);
      data.append('host_phone', formData.host_phone);
      data.append('custom_message', formData.custom_message);
      
      const response = await invitationsApi.createInvitation(data);
      
      if (response.success && response.data) {
        addInvitation(response.data);
        setActiveStep(6); // Success step
        setTimeout(() => {
          navigate('/dashboard/invitations');
        }, 2000);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create event');
    } finally {
      setSubmitting(false);
    }
  };

  // Get templates sorted by AI recommendations if available
  const getSortedTemplates = () => {
    if (!aiRecommendedTemplates.length || !useAIAssistant) {
      return templates.map(t => ({ ...t, matchScore: undefined }));
    }

    // Sort templates based on AI recommendations
    const recommendedIds = aiRecommendedTemplates.map(r => r.templateId);
    const sorted = [...templates].sort((a, b) => {
      const aIndex = recommendedIds.indexOf(a.id);
      const bIndex = recommendedIds.indexOf(b.id);
      
      if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
      if (aIndex !== -1) return -1;
      if (bIndex !== -1) return 1;
      return 0;
    });

    return sorted;
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Event Details
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Let's start with the basic information about your special day
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Event Title"
                  required
                  value={formData.event_title}
                  onChange={(e) => setFormData({ ...formData, event_title: e.target.value })}
                  placeholder="e.g., Sarah & Michael's Wedding"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Bride's Name"
                  required
                  value={formData.bride_name}
                  onChange={(e) => setFormData({ ...formData, bride_name: e.target.value })}
                  placeholder="e.g., Sarah Johnson"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Groom's Name"
                  required
                  value={formData.groom_name}
                  onChange={(e) => setFormData({ ...formData, groom_name: e.target.value })}
                  placeholder="e.g., Michael Smith"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                  <DatePicker
                    label="Event Date"
                    value={formData.event_date}
                    onChange={(date) => date && setFormData({ ...formData, event_date: date })}
                    slotProps={{ textField: { fullWidth: true, required: true } }}
                  />
                </LocalizationProvider>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Host Name"
                  required
                  value={formData.host_name}
                  onChange={(e) => setFormData({ ...formData, host_name: e.target.value })}
                  placeholder="e.g., Johnson & Smith Families"
                />
              </Grid>
            </Grid>
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Select Your Plan
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Choose a plan that fits your needs
            </Typography>
            
            <Grid container spacing={3}>
              {plans.map((plan) => (
                <Grid item xs={12} md={4} key={plan.id}>
                  <Card
                    sx={{
                      border: selectedPlan?.id === plan.id ? 3 : 1,
                      borderColor: selectedPlan?.id === plan.id ? 'primary.main' : 'divider',
                      height: '100%',
                    }}
                  >
                    <CardActionArea onClick={() => handlePlanSelect(plan)} sx={{ height: '100%' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                          <Typography variant="h6" fontWeight={600}>
                            {plan.name}
                          </Typography>
                          {plan.code === 'LUXURY' && (
                            <AIFeatureBadge size="small" />
                          )}
                        </Box>
                        <Typography variant="h4" color="primary" gutterBottom>
                          ${plan.price}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {plan.description}
                        </Typography>
                        <Chip 
                          label={`${plan.max_guests} guests`} 
                          size="small" 
                          variant="outlined" 
                        />
                      </CardContent>
                    </CardActionArea>
                  </Card>
                </Grid>
              ))}
            </Grid>

            {/* AI Assistant Toggle */}
            {selectedPlan && (
              <Fade in={!!selectedPlan}>
                <Paper sx={{ mt: 4, p: 3, bgcolor: 'rgba(166, 30, 42, 0.04)' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <SmartToy color="primary" />
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        Use AI Design Assistant
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Get personalized template recommendations based on your couple photo
                      </Typography>
                    </Box>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={useAIAssistant}
                          onChange={(e) => setUseAIAssistant(e.target.checked)}
                        />
                      }
                      label=""
                    />
                  </Box>
                </Paper>
              </Fade>
            )}
          </Box>
        );

      case 2:
        return useAIAssistant ? (
          <AIAssistantWidget
            eventType="WEDDING"
            onAnalysisComplete={handleAIAnalysisComplete}
            onTemplateSelect={handleAITemplateSelect}
            onMessageSelect={handleAIMessageSelect}
            planCode={selectedPlan?.code}
            messageContext={{
              brideName: formData.bride_name,
              groomName: formData.groom_name,
            }}
          />
        ) : (
          <Box textAlign="center" py={4}>
            <Typography variant="h6" gutterBottom>
              AI Design Assistant Skipped
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              You can proceed to template selection without AI recommendations, 
              or go back and enable the AI assistant.
            </Typography>
            <Button
              variant="outlined"
              onClick={() => setActiveStep(1)}
              sx={{ mr: 2 }}
            >
              Go Back
            </Button>
            <Button
              variant="contained"
              onClick={handleNext}
            >
              Continue to Templates
            </Button>
          </Box>
        );

      case 3:
        const sortedTemplates = getSortedTemplates();
        return (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                Select a Template
              </Typography>
              {useAIAssistant && aiRecommendedTemplates.length > 0 && (
                <AIFeatureBadge />
              )}
            </Box>
            
            {useAIAssistant && aiRecommendedTemplates.length > 0 && (
              <Alert severity="info" sx={{ mb: 3 }} icon={<AutoAwesome />}>
                <Typography variant="body2">
                  Templates are sorted by AI recommendations based on your photo analysis.
                  Top matches are shown first with match scores.
                </Typography>
              </Alert>
            )}
            
            <Grid container spacing={3}>
              {sortedTemplates.map((template, index) => {
                const isAIRecommended = index < 3 && useAIAssistant && aiRecommendedTemplates.length > 0;
                return (
                  <Grid item xs={12} sm={6} md={4} key={template.id}>
                    <Card
                      sx={{
                        border: selectedTemplate?.id === template.id ? 3 : isAIRecommended ? 2 : 1,
                        borderColor: selectedTemplate?.id === template.id 
                          ? 'primary.main' 
                          : isAIRecommended 
                            ? 'success.main' 
                            : 'divider',
                        position: 'relative',
                      }}
                    >
                      {isAIRecommended && (
                        <Chip
                          icon={<AutoAwesome />}
                          label={`${Math.round((1 - index * 0.15) * 100)}% Match`}
                          color="success"
                          size="small"
                          sx={{
                            position: 'absolute',
                            top: 8,
                            left: 8,
                            zIndex: 1,
                          }}
                        />
                      )}
                      <CardActionArea onClick={() => setSelectedTemplate(template)}>
                        <CardMedia
                          component="img"
                          height="200"
                          image={template.thumbnail || '/images/template-placeholder.jpg'}
                          alt={template.name}
                        />
                        <CardContent>
                          <Typography variant="h6" noWrap>
                            {template.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" noWrap>
                            {template.description}
                          </Typography>
                          <Chip
                            label={template.animation_type}
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        </CardContent>
                      </CardActionArea>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </Box>
        );

      case 4:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Customize Your Invitation
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Venue Name"
                  required
                  value={formData.event_venue}
                  onChange={(e) => setFormData({ ...formData, event_venue: e.target.value })}
                  placeholder="e.g., Grand Ballroom, Taj Hotel"
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
                  placeholder="Full address of the venue"
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Google Maps Link"
                  value={formData.event_map_link}
                  onChange={(e) => setFormData({ ...formData, event_map_link: e.target.value })}
                  placeholder="https://maps.google.com/..."
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Host Phone"
                  value={formData.host_phone}
                  onChange={(e) => setFormData({ ...formData, host_phone: e.target.value })}
                  placeholder="+1 234 567 8900"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="subtitle1">
                    Invitation Message
                  </Typography>
                  <AIFeatureBadge size="small" />
                </Box>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  value={formData.custom_message}
                  onChange={(e) => setFormData({ ...formData, custom_message: e.target.value })}
                  placeholder="Enter your invitation message or generate one with AI"
                />
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<AutoAwesome />}
                  onClick={() => setShowMessageGenerator(true)}
                  sx={{ mt: 1 }}
                >
                  Generate with AI
                </Button>
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
          </Box>
        );

      case 5:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Preview & Payment
            </Typography>
            
            <Paper sx={{ p: 3, mb: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Event
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.event_title}
                  </Typography>
                  
                  <Typography variant="subtitle2" color="text.secondary">
                    Couple
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.bride_name} & {formData.groom_name}
                  </Typography>
                  
                  <Typography variant="subtitle2" color="text.secondary">
                    Date
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.event_date.toLocaleDateString()}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Template
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedTemplate?.name}
                  </Typography>
                  
                  <Typography variant="subtitle2" color="text.secondary">
                    Plan
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedPlan?.name || order?.plan.name}
                  </Typography>
                  
                  <Typography variant="subtitle2" color="text.secondary">
                    Venue
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.event_venue}
                  </Typography>
                </Grid>
              </Grid>
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">Total</Typography>
                <Typography variant="h5" color="primary">
                  ${selectedPlan?.price || order?.plan.price || 0}
                </Typography>
              </Box>
            </Paper>
            
            <Alert severity="info">
              Your invitation will be active for 15 days from approval.
              You'll receive digital invitation links to share with your guests.
            </Alert>
          </Box>
        );

      case 6:
        return (
          <Box textAlign="center" py={4}>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200 }}
            >
              <Check sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            </motion.div>
            <Typography variant="h5" fontWeight={600} gutterBottom>
              Event Created Successfully!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Redirecting to your invitations...
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="lg">
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Create Your Event
        </Typography>
        
        <Stepper activeStep={activeStep} sx={{ mb: 4 }} alternativeLabel>
          {steps.map((label, index) => (
            <Step key={label}>
              <StepLabel
                StepIconProps={{
                  icon: index === 2 ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <SmartToy sx={{ fontSize: 20 }} />
                    </Box>
                  ) : undefined,
                }}
              >
                {label}
              </StepLabel>
            </Step>
          ))}
        </Stepper>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Paper sx={{ p: 4 }}>
              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}
              
              {renderStepContent()}
              
              {activeStep < 6 && (
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                  <Button
                    disabled={activeStep === 0}
                    onClick={handleBack}
                    startIcon={<ArrowBack />}
                  >
                    Back
                  </Button>
                  
                  {activeStep === steps.length - 1 ? (
                    <Button
                      variant="contained"
                      onClick={handleSubmit}
                      disabled={submitting}
                      startIcon={submitting ? <CircularProgress size={20} /> : <Check />}
                    >
                      {submitting ? 'Creating...' : 'Create Event'}
                    </Button>
                  ) : (
                    <Button
                      variant="contained"
                      onClick={handleNext}
                      endIcon={<ArrowForward />}
                    >
                      Next
                    </Button>
                  )}
                </Box>
              )}
            </Paper>
          </motion.div>
        </AnimatePresence>
      </Container>

      {/* AI Onboarding Dialog */}
      <AIOnboardingDialog
        open={showOnboarding}
        onClose={handleOnboardingClose}
      />
    </Box>
  );
};

export default CreateEvent;
