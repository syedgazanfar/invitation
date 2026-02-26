/**
 * Invitation Builder Page
 */
import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
} from '@mui/material';
import {
  ArrowBack,
  ArrowForward,
  Check,
  CloudUpload,
  Image as ImageIcon,
  Preview,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { invitationsApi, plansApi } from '../../services/api';
import { useInvitationStore } from '../../store/authStore';
import { Template, Order } from '../../types';

const steps = ['Select Template', 'Event Details', 'Upload Media', 'Preview & Create'];

const InvitationBuilder: React.FC = () => {
  const navigate = useNavigate();
  const { orderId } = useParams();
  const { addInvitation } = useInvitationStore();
  
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [order, setOrder] = useState<Order | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    event_title: '',
    event_date: new Date(),
    event_venue: '',
    event_address: '',
    event_map_link: '',
    host_name: '',
    host_phone: '',
    custom_message: '',
    banner_image: null as File | null,
    gallery_images: [] as File[],
  });

  useEffect(() => {
    fetchData();
  }, [orderId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Get order details
      if (orderId) {
        const orderRes = await invitationsApi.getOrder(orderId);
        if (orderRes.success && orderRes.data) {
          setOrder(orderRes.data);
          
          // Get templates for this plan
          const templatesRes = await plansApi.getTemplatesByPlan(
            orderRes.data.plan.code,
            orderRes.data.event_type
          );
          if (templatesRes.success) {
            setTemplates(templatesRes.data?.templates || []);
          }
        }
      }
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const onDropBanner = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFormData({ ...formData, banner_image: acceptedFiles[0] });
      setPreviewImage(URL.createObjectURL(acceptedFiles[0]));
    }
  }, [formData]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onDropBanner,
    accept: { 'image/*': [] },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024, // 5MB
  });

  const handleNext = () => {
    if (validateStep()) {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const validateStep = () => {
    setError('');
    
    switch (activeStep) {
      case 0:
        if (!selectedTemplate) {
          setError('Please select a template');
          return false;
        }
        break;
      case 1:
        if (!formData.event_title || !formData.event_venue || !formData.host_name) {
          setError('Please fill in all required fields');
          return false;
        }
        break;
      case 2:
        if (!formData.banner_image) {
          setError('Please upload a banner image');
          return false;
        }
        break;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!order || !selectedTemplate) return;
    
    try {
      setSubmitting(true);
      
      const data = new FormData();
      data.append('order_id', order.id);
      data.append('template_id', selectedTemplate.id);
      data.append('event_title', formData.event_title);
      data.append('event_date', formData.event_date.toISOString());
      data.append('event_venue', formData.event_venue);
      data.append('event_address', formData.event_address);
      data.append('event_map_link', formData.event_map_link);
      data.append('host_name', formData.host_name);
      data.append('host_phone', formData.host_phone);
      data.append('custom_message', formData.custom_message);
      if (formData.banner_image) {
        data.append('banner_image', formData.banner_image);
      }
      
      const response = await invitationsApi.createInvitation(data);
      
      if (response.success && response.data) {
        addInvitation(response.data);
        setActiveStep(4); // Success step
        setTimeout(() => {
          navigate('/dashboard/invitations');
        }, 2000);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create invitation');
    } finally {
      setSubmitting(false);
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Choose a Template
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Select a template that matches your event style
            </Typography>
            
            <Grid container spacing={3}>
              {templates.map((template) => (
                <Grid item xs={12} sm={6} md={4} key={template.id}>
                  <Card
                    sx={{
                      border: selectedTemplate?.id === template.id ? 3 : 0,
                      borderColor: 'primary.main',
                    }}
                  >
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
              ))}
            </Grid>
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Event Details
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Event Title"
                  required
                  value={formData.event_title}
                  onChange={(e) => setFormData({ ...formData, event_title: e.target.value })}
                  placeholder="e.g., John & Jane's Wedding"
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
                  placeholder="e.g., Smith Family"
                />
              </Grid>
              
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
                  placeholder="+91 98765 43210"
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Custom Message"
                  multiline
                  rows={3}
                  value={formData.custom_message}
                  onChange={(e) => setFormData({ ...formData, custom_message: e.target.value })}
                  placeholder="A special message for your guests"
                />
              </Grid>
            </Grid>
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Upload Media
            </Typography>
            
            <Paper
              {...getRootProps()}
              sx={{
                p: 4,
                textAlign: 'center',
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'divider',
                bgcolor: isDragActive ? 'primary.50' : 'background.paper',
                cursor: 'pointer',
                mb: 3,
              }}
            >
              <input {...getInputProps()} />
              <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {isDragActive ? 'Drop the image here' : 'Drag & drop banner image'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                or click to select file (max 5MB)
              </Typography>
            </Paper>
            
            {previewImage && (
              <Box mt={2}>
                <Typography variant="subtitle2" gutterBottom>
                  Preview:
                </Typography>
                <Box
                  component="img"
                  src={previewImage}
                  alt="Preview"
                  sx={{
                    maxWidth: '100%',
                    maxHeight: 300,
                    borderRadius: 2,
                  }}
                />
              </Box>
            )}
          </Box>
        );

      case 3:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Preview & Create
            </Typography>
            
            <Paper sx={{ p: 3, mb: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Event Title
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.event_title}
                  </Typography>
                  
                  <Typography variant="subtitle2" color="text.secondary">
                    Date
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.event_date.toLocaleDateString()}
                  </Typography>
                  
                  <Typography variant="subtitle2" color="text.secondary">
                    Venue
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.event_venue}
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
                    Host
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formData.host_name}
                  </Typography>
                  
                  {previewImage && (
                    <Box
                      component="img"
                      src={previewImage}
                      alt="Banner"
                      sx={{ width: 100, height: 100, objectFit: 'cover', borderRadius: 1, mt: 1 }}
                    />
                  )}
                </Grid>
              </Grid>
            </Paper>
            
            <Alert severity="info">
              Your invitation will be active for 15 days from approval. 
              You will receive {order?.granted_regular_links} regular links and {order?.granted_test_links} test links.
            </Alert>
          </Box>
        );

      case 4:
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
              Invitation Created Successfully!
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
          Create Invitation
        </Typography>
        
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
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
              
              {activeStep < 4 && (
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
                      {submitting ? 'Creating...' : 'Create Invitation'}
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
    </Box>
  );
};

export default InvitationBuilder;
