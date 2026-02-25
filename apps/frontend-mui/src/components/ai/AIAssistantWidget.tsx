/**
 * AI Assistant Widget Component
 * 
 * Main interface for AI-powered features in the wedding invitation platform.
 * Combines photo upload, analysis, style recommendations, template recommendations,
 * and message generation into a cohesive user experience.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Button,
  Divider,
  Alert,
  AlertTitle,
  Chip,
  IconButton,
  Tooltip,
  Fade,
  CircularProgress,
} from '@mui/material';
import {
  SmartToy,
  PhotoLibrary,
  Palette,
  Message,
  Refresh,
  ExpandMore,
  ExpandLess,
  AutoAwesome,
  CheckCircle,
  Warning,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { PhotoAnalysisResult, EventType } from '../../services/aiApi';
import { usePhotoAnalysis, useAIRecommendations, useAIUsage } from '../../hooks';

// Sub-components
import { PhotoUploadZone } from './PhotoUploadZone';
import { AnalysisProgress, DEFAULT_ANALYSIS_STEPS } from './AnalysisProgress';
import { ColorPaletteDisplay } from './ColorPaletteDisplay';
import { StyleRecommendationCard } from './StyleRecommendationCard';
import { TemplateRecommendationGrid } from './TemplateRecommendationGrid';
import { MessageGenerator } from './MessageGenerator';

export interface AIAssistantWidgetProps {
  /** Type of event being created */
  eventType?: EventType;
  /** Optional event ID for saving results */
  eventId?: number;
  /** Callback when photo analysis is complete */
  onAnalysisComplete?: (result: PhotoAnalysisResult) => void;
  /** Callback when a generated message is selected */
  onMessageSelect?: (message: string) => void;
  /** Callback when a template is selected */
  onTemplateSelect?: (templateId: string) => void;
  /** Optional plan code for filtering templates */
  planCode?: string;
  /** Whether to show the message generator section */
  showMessageGenerator?: boolean;
  /** Context for message generation (required if showMessageGenerator is true) */
  messageContext?: {
    brideName: string;
    groomName: string;
    details?: string;
  };
}

type WidgetStep = 'upload' | 'analyzing' | 'results' | 'templates' | 'messages';

export const AIAssistantWidget: React.FC<AIAssistantWidgetProps> = ({
  eventType = 'WEDDING',
  eventId,
  onAnalysisComplete,
  onMessageSelect,
  onTemplateSelect,
  planCode,
  showMessageGenerator = true,
  messageContext,
}) => {
  // Hooks
  const {
    analyzePhoto,
    result: analysisResult,
    loading: isAnalyzing,
    progress: analysisProgress,
    error: analysisError,
    reset: resetAnalysis,
  } = usePhotoAnalysis();

  const {
    templateRecommendations,
    styleRecommendations,
    loading: isLoadingRecommendations,
    getRecommendations,
    selectTemplate,
    selectedTemplateId,
  } = useAIRecommendations();

  const { usage, limits, checkFeature } = useAIUsage();

  // Local state
  const [currentStep, setCurrentStep] = useState<WidgetStep>('upload');
  const [selectedStyle, setSelectedStyle] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    colors: true,
    styles: true,
    templates: true,
    messages: true,
  });
  const [featureAvailable, setFeatureAvailable] = useState<boolean>(true);

  // Check AI feature availability on mount
  useEffect(() => {
    const verifyFeature = async () => {
      const available = await checkFeature('photo_analysis');
      setFeatureAvailable(available);
    };
    verifyFeature();
  }, [checkFeature]);

  // Handle analysis completion
  useEffect(() => {
    if (analysisResult && !isAnalyzing) {
      setCurrentStep('results');
      onAnalysisComplete?.(analysisResult);
      
      // Fetch recommendations
      getRecommendations(analysisResult, eventType, planCode);
    }
  }, [analysisResult, isAnalyzing, eventType, planCode, getRecommendations, onAnalysisComplete]);

  // Calculate current analysis step
  const getCurrentAnalysisStep = (): number => {
    if (analysisProgress < 25) return 0;
    if (analysisProgress < 50) return 1;
    if (analysisProgress < 75) return 2;
    return 3;
  };

  // Handle photo upload
  const handlePhotoSelect = useCallback(async (file: File) => {
    setCurrentStep('analyzing');
    await analyzePhoto(file, eventType, eventId);
  }, [analyzePhoto, eventType, eventId]);

  // Handle style selection
  const handleStyleSelect = useCallback((styleName: string) => {
    setSelectedStyle(styleName);
  }, []);

  // Handle template selection
  const handleTemplateSelect = useCallback((templateId: string) => {
    selectTemplate(templateId);
    onTemplateSelect?.(templateId);
  }, [selectTemplate, onTemplateSelect]);

  // Handle message selection
  const handleMessageSelect = useCallback((message: string) => {
    onMessageSelect?.(message);
  }, [onMessageSelect]);

  // Toggle section expansion
  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  // Reset widget
  const handleReset = () => {
    resetAnalysis();
    setCurrentStep('upload');
    setSelectedStyle(null);
  };

  // Render upload section
  const renderUploadSection = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Paper elevation={2} sx={{ p: 3, borderRadius: 3 }}>
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Box
            sx={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              bgcolor: 'rgba(166, 30, 42, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 2,
            }}
          >
            <SmartToy sx={{ fontSize: 32, color: 'primary.main' }} />
          </Box>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            AI Design Assistant
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 400, mx: 'auto' }}>
            Upload a photo to get personalized color palettes, style recommendations, and template suggestions powered by AI.
          </Typography>
        </Box>

        <PhotoUploadZone
          onPhotoSelect={handlePhotoSelect}
          isLoading={isAnalyzing}
        />

        {analysisError && (
          <Fade in={!!analysisError}>
            <Alert severity="error" sx={{ mt: 2 }}>
              <AlertTitle>Analysis Failed</AlertTitle>
              {analysisError.message}
            </Alert>
          </Fade>
        )}
      </Paper>
    </motion.div>
  );

  // Render analyzing section
  const renderAnalyzingSection = () => (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <AnalysisProgress
        progress={analysisProgress}
        steps={DEFAULT_ANALYSIS_STEPS}
        currentStep={getCurrentAnalysisStep()}
      />
    </motion.div>
  );

  // Render results section
  const renderResultsSection = () => {
    if (!analysisResult) return null;

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {/* Success header */}
        <Paper
          elevation={2}
          sx={{
            p: 3,
            mb: 3,
            borderRadius: 3,
            bgcolor: 'success.light',
            color: 'success.contrastText',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CheckCircle sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h6" fontWeight={600}>
                Analysis Complete!
              </Typography>
              <Typography variant="body2">
                We've analyzed your photo and generated personalized recommendations.
              </Typography>
            </Box>
          </Box>
        </Paper>

        {/* Color palette section */}
        <Paper elevation={2} sx={{ p: 3, borderRadius: 3, mb: 3 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
            }}
            onClick={() => toggleSection('colors')}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PhotoLibrary color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Extracted Colors
              </Typography>
            </Box>
            <IconButton size="small">
              {expandedSections.colors ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
          </Box>
          
          <AnimatePresence>
            {expandedSections.colors && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <Box sx={{ mt: 2 }}>
                  <ColorPaletteDisplay
                    colors={analysisResult.primaryColors.map(c => ({
                      color: c.color,
                      name: c.name,
                      percentage: c.percentage,
                    }))}
                  />
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </Paper>

        {/* Style recommendations section */}
        {styleRecommendations.length > 0 && (
          <Paper elevation={2} sx={{ p: 3, borderRadius: 3, mb: 3 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
              }}
              onClick={() => toggleSection('styles')}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Palette color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Style Recommendations
                </Typography>
                <Chip
                  label={`${styleRecommendations.length}`}
                  size="small"
                  color="primary"
                  sx={{ ml: 1 }}
                />
              </Box>
              <IconButton size="small">
                {expandedSections.styles ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>

            <AnimatePresence>
              {expandedSections.styles && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <Box
                    sx={{
                      mt: 3,
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                      gap: 2,
                    }}
                  >
                    {styleRecommendations.map((style, index) => (
                      <StyleRecommendationCard
                        key={`${style.style}-${index}`}
                        style={{
                          name: style.style,
                          confidence: style.confidence,
                          description: style.description,
                          colorPalette: style.colorPalette,
                          matchingTemplates: style.matchingTemplates,
                        }}
                        isSelected={selectedStyle === style.style}
                        onSelect={() => handleStyleSelect(style.style)}
                      />
                    ))}
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>
          </Paper>
        )}

        {/* Template recommendations section */}
        <Paper elevation={2} sx={{ p: 3, borderRadius: 3, mb: 3 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
            }}
            onClick={() => toggleSection('templates')}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoAwesome color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Template Recommendations
              </Typography>
            </Box>
            <IconButton size="small">
              {expandedSections.templates ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
          </Box>

          <AnimatePresence>
            {expandedSections.templates && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <Box sx={{ mt: 3 }}>
                  <TemplateRecommendationGrid
                    recommendations={templateRecommendations}
                    onTemplateSelect={handleTemplateSelect}
                    selectedTemplateId={selectedTemplateId || undefined}
                    loading={isLoadingRecommendations}
                  />
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </Paper>

        {/* Message generator section */}
        {showMessageGenerator && messageContext && (
          <Paper elevation={2} sx={{ p: 3, borderRadius: 3, mb: 3 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
              }}
              onClick={() => toggleSection('messages')}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Message color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Message Generator
                </Typography>
              </Box>
              <IconButton size="small">
                {expandedSections.messages ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>

            <AnimatePresence>
              {expandedSections.messages && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <Box sx={{ mt: 3 }}>
                    <MessageGenerator
                      context={{
                        brideName: messageContext.brideName,
                        groomName: messageContext.groomName,
                        eventType,
                        details: messageContext.details,
                      }}
                      onMessageSelect={handleMessageSelect}
                    />
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>
          </Paper>
        )}

        {/* Reset button */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleReset}
            sx={{ borderRadius: 2, textTransform: 'none' }}
          >
            Analyze Another Photo
          </Button>
        </Box>
      </motion.div>
    );
  };

  // Feature unavailable warning
  if (!featureAvailable) {
    return (
      <Paper elevation={2} sx={{ p: 4, borderRadius: 3 }}>
        <Alert severity="warning">
          <AlertTitle>AI Features Unavailable</AlertTitle>
          AI-powered features are currently unavailable. This could be due to:
          <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
            <li>Monthly usage limit reached</li>
            <li>Temporary service disruption</li>
            <li>Plan restrictions</li>
          </ul>
          Please try again later or contact support for assistance.
        </Alert>
      </Paper>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Widget header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <SmartToy color="primary" sx={{ fontSize: 28 }} />
        <Box>
          <Typography variant="h5" fontWeight={600}>
            AI Assistant
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Smart recommendations for your {eventType.toLowerCase()} invitation
          </Typography>
        </Box>
      </Box>

      {/* Main content */}
      <AnimatePresence mode="wait">
        {currentStep === 'upload' && renderUploadSection()}
        {currentStep === 'analyzing' && renderAnalyzingSection()}
        {currentStep === 'results' && renderResultsSection()}
      </AnimatePresence>
    </Box>
  );
};

export default AIAssistantWidget;
