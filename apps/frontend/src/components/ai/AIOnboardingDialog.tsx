/**
 * AI Onboarding Dialog
 * 
 * First-time user onboarding for AI features.
 * Explains the AI Design Assistant capabilities and encourages users to try it.
 */
import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Fade,
  useTheme,
} from '@mui/material';
import {
  SmartToy,
  PhotoLibrary,
  Palette,
  AutoAwesome,
  ArrowForward,
  Check,
  Sparkles,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface AIOnboardingDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: (getStarted: boolean) => void;
}

interface OnboardingStep {
  icon: React.ReactNode;
  title: string;
  description: string;
}

const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    icon: <PhotoLibrary sx={{ fontSize: 40 }} />,
    title: 'Upload a Photo',
    description: 'Share a photo of you and your partner. Our AI will analyze the colors, mood, and style to understand your unique aesthetic.',
  },
  {
    icon: <Palette sx={{ fontSize: 40 }} />,
    title: 'AI Analyzes Colors & Mood',
    description: 'Our advanced AI extracts the dominant colors from your photo and detects the overall mood - whether it\'s romantic, fun, elegant, or modern.',
  },
  {
    icon: <AutoAwesome sx={{ fontSize: 40 }} />,
    title: 'Get Tailored Suggestions',
    description: 'Receive personalized template recommendations, style suggestions, and even AI-generated invitation messages that match your vibe.',
  },
];

export const AIOnboardingDialog: React.FC<AIOnboardingDialogProps> = ({
  open,
  onClose,
}) => {
  const theme = useTheme();
  const [activeStep, setActiveStep] = React.useState(0);

  const handleNext = () => {
    if (activeStep < ONBOARDING_STEPS.length - 1) {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep((prev) => prev - 1);
    }
  };

  const handleGetStarted = () => {
    setActiveStep(0);
    onClose(true);
  };

  const handleMaybeLater = () => {
    setActiveStep(0);
    onClose(false);
  };

  return (
    <Dialog
      open={open}
      onClose={() => onClose(false)}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          overflow: 'hidden',
        },
      }}
    >
      {/* Header with gradient */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
          color: 'white',
          p: 4,
          textAlign: 'center',
        }}
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              bgcolor: 'rgba(255,255,255,0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 2,
            }}
          >
            <Sparkles sx={{ fontSize: 40 }} />
          </Box>
        </motion.div>
        
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Meet Your AI Design Assistant
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.9, maxWidth: 500, mx: 'auto' }}>
          Get personalized recommendations in seconds and create the perfect invitation 
          that matches your unique style.
        </Typography>
      </Box>

      <DialogContent sx={{ p: 4 }}>
        {/* Stepper */}
        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
          {ONBOARDING_STEPS.map((step, index) => (
            <Step key={index}>
              <StepLabel>{`Step ${index + 1}`}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* Current Step Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Paper
              elevation={0}
              sx={{
                p: 4,
                textAlign: 'center',
                bgcolor: 'rgba(166, 30, 42, 0.04)',
                borderRadius: 3,
                border: '2px dashed',
                borderColor: 'rgba(166, 30, 42, 0.2)',
              }}
            >
              <Box
                sx={{
                  color: 'primary.main',
                  mb: 3,
                }}
              >
                {ONBOARDING_STEPS[activeStep].icon}
              </Box>
              
              <Typography variant="h5" fontWeight={600} gutterBottom>
                {ONBOARDING_STEPS[activeStep].title}
              </Typography>
              
              <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 400, mx: 'auto' }}>
                {ONBOARDING_STEPS[activeStep].description}
              </Typography>
            </Paper>
          </motion.div>
        </AnimatePresence>

        {/* Features List */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom align="center">
            What you'll get:
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 2,
              justifyContent: 'center',
              mt: 2,
            }}
          >
            {[
              { icon: <Palette fontSize="small" />, label: 'Color palette extraction' },
              { icon: <SmartToy fontSize="small" />, label: 'Mood detection' },
              { icon: <AutoAwesome fontSize="small" />, label: 'Template recommendations' },
              { icon: <Check fontSize="small" />, label: 'AI message generation' },
            ].map((feature, index) => (
              <Paper
                key={index}
                sx={{
                  px: 2,
                  py: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  bgcolor: 'background.paper',
                }}
              >
                <Box sx={{ color: 'primary.main' }}>{feature.icon}</Box>
                <Typography variant="body2">{feature.label}</Typography>
              </Paper>
            ))}
          </Box>
        </Box>

        {/* Reassurance */}
        <Box
          sx={{
            mt: 3,
            p: 2,
            bgcolor: 'grey.50',
            borderRadius: 2,
            textAlign: 'center',
          }}
        >
          <Typography variant="caption" color="text.secondary">
            Don't worry - you can always change your selections later. 
            The AI assistant is here to help, not to limit your choices.
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3, justifyContent: 'space-between' }}>
        <Box>
          {activeStep > 0 ? (
            <Button onClick={handleBack}>
              Back
            </Button>
          ) : (
            <Button onClick={handleMaybeLater} color="inherit">
              Maybe Later
            </Button>
          )}
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          {activeStep < ONBOARDING_STEPS.length - 1 ? (
            <Button
              variant="contained"
              onClick={handleNext}
              endIcon={<ArrowForward />}
            >
              Next
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleGetStarted}
              startIcon={<Sparkles />}
              size="large"
            >
              Get Started
            </Button>
          )}
        </Box>
      </DialogActions>
    </Dialog>
  );
};

export default AIOnboardingDialog;
