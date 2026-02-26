/**
 * Analysis Progress Component
 * 
 * Displays animated progress indicator with step-by-step visualization
 * during AI photo analysis operations.
 */
import React from 'react';
import {
  Box,
  Typography,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
  Paper,
  Fade,
  Chip,
} from '@mui/material';
import {
  CloudUpload,
  Palette,
  Mood,
  AutoAwesome,
  CheckCircle,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

export interface AnalysisProgressProps {
  /** Progress percentage (0-100) */
  progress: number;
  /** Array of step labels */
  steps: string[];
  /** Index of current active step */
  currentStep: number;
}

// Step icons mapping
const stepIcons = [
  <CloudUpload key="upload" />,
  <Palette key="palette" />,
  <Mood key="mood" />,
  <AutoAwesome key="recommendations" />,
];

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  progress,
  steps,
  currentStep,
}) => {
  const getStepIcon = (index: number) => {
    const iconIndex = Math.min(index, stepIcons.length - 1);
    return stepIcons[iconIndex];
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        borderRadius: 3,
        bgcolor: 'background.paper',
      }}
    >
      {/* Header with progress percentage */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h6" fontWeight={600}>
          AI Analysis in Progress
        </Typography>
        <Chip
          label={`${Math.round(progress)}%`}
          color="primary"
          size="small"
          sx={{ fontWeight: 600, minWidth: 50 }}
        />
      </Box>

      {/* Animated progress bar */}
      <Box sx={{ position: 'relative', mb: 4 }}>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: 'rgba(166, 30, 42, 0.1)',
            '& .MuiLinearProgress-bar': {
              bgcolor: 'primary.main',
              borderRadius: 4,
              transition: 'transform 0.5s ease-in-out',
            },
          }}
        />
        
        {/* Animated pulse effect at progress position */}
        <AnimatePresence>
          {progress < 100 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'absolute',
                top: -4,
                left: `${progress}%`,
                transform: 'translateX(-50%)',
              }}
            >
              <Box
                component={motion.div}
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
                sx={{
                  width: 16,
                  height: 16,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  boxShadow: '0 0 12px rgba(166, 30, 42, 0.5)',
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </Box>

      {/* Stepper with icons */}
      <Stepper 
        activeStep={currentStep} 
        alternativeLabel
        sx={{
          '& .MuiStepLabel-root': {
            cursor: 'default',
          },
          '& .MuiStepLabel-iconContainer': {
            '& .Mui-active': {
              color: 'primary.main',
            },
            '& .Mui-completed': {
              color: 'success.main',
            },
          },
        }}
      >
        {steps.map((label, index) => (
          <Step key={label} completed={index < currentStep}>
            <StepLabel
              StepIconComponent={() => (
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: index <= currentStep ? 'primary.main' : 'grey.200',
                    color: index <= currentStep ? 'white' : 'text.secondary',
                    transition: 'all 0.3s ease',
                  }}
                >
                  {index < currentStep ? (
                    <CheckCircle sx={{ fontSize: 24 }} />
                  ) : (
                    React.cloneElement(getStepIcon(index), { sx: { fontSize: 20 } })
                  )}
                </Box>
              )}
            >
              <Typography
                variant="body2"
                sx={{
                  fontWeight: index === currentStep ? 600 : 400,
                  color: index <= currentStep ? 'text.primary' : 'text.secondary',
                }}
              >
                {label}
              </Typography>
            </StepLabel>
          </Step>
        ))}
      </Stepper>

      {/* Current step description */}
      <Fade in={true}>
        <Box
          sx={{
            mt: 3,
            p: 2,
            borderRadius: 2,
            bgcolor: 'rgba(166, 30, 42, 0.04)',
            border: '1px solid',
            borderColor: 'rgba(166, 30, 42, 0.1)',
          }}
        >
          <Typography variant="body2" color="primary" fontWeight={500}>
            {steps[currentStep] || 'Finishing up...'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Please wait while our AI processes your photo
          </Typography>
        </Box>
      </Fade>

      {/* Fun fact or tip */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
        >
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              {getTipForStep(currentStep)}
            </Typography>
          </Box>
        </motion.div>
      </AnimatePresence>
    </Paper>
  );
};

// Helper function to get tips for each step
const getTipForStep = (step: number): string => {
  const tips = [
    'Uploading high-quality photos gives better color analysis results',
    'Our AI can detect over 16 million colors in your photos',
    'Mood detection analyzes lighting, composition, and colors',
    'Personalized recommendations based on your unique style',
    'Almost there! Finalizing your custom recommendations...',
  ];
  return tips[Math.min(step, tips.length - 1)];
};

// Default steps for photo analysis
export const DEFAULT_ANALYSIS_STEPS = [
  'Uploading photo...',
  'Analyzing colors...',
  'Detecting mood...',
  'Generating recommendations...',
];

export default AnalysisProgress;
