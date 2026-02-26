/**
 * Style Recommendation Card Component
 * 
 * Displays AI-generated style recommendations with confidence scores,
 * color palettes, and template matching information.
 */
import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle,
  Palette,
  Style,
  ArrowForward,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

export interface StyleRecommendationCardProps {
  /** Style recommendation data */
  style: {
    name: string;
    confidence: number;
    description: string;
    colorPalette: string[];
    matchingTemplates: string[];
  };
  /** Whether this style is currently selected */
  isSelected?: boolean;
  /** Callback when user selects this style */
  onSelect?: () => void;
}

export const StyleRecommendationCard: React.FC<StyleRecommendationCardProps> = ({
  style,
  isSelected = false,
  onSelect,
}) => {
  const confidencePercentage = Math.round(style.confidence * 100);

  // Get confidence color based on score
  const getConfidenceColor = (score: number): 'success' | 'warning' | 'info' => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'info';
  };

  const confidenceColor = getConfidenceColor(style.confidence);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ y: -4 }}
    >
      <Paper
        elevation={isSelected ? 4 : 1}
        sx={{
          p: 3,
          borderRadius: 3,
          border: 2,
          borderColor: isSelected ? 'primary.main' : 'transparent',
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.2s ease',
          '&:hover': {
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
          },
        }}
      >
        {/* Selected indicator */}
        {isSelected && (
          <Box
            sx={{
              position: 'absolute',
              top: 12,
              right: 12,
              color: 'primary.main',
            }}
          >
            <CheckCircle sx={{ fontSize: 24 }} />
          </Box>
        )}

        {/* Header with style name and confidence */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              bgcolor: 'rgba(166, 30, 42, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Style sx={{ color: 'primary.main' }} />
          </Box>
          
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              {style.name}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                icon={<CheckCircle fontSize="small" />}
                label={`${confidencePercentage}% Match`}
                size="small"
                color={confidenceColor}
                sx={{ fontWeight: 500 }}
              />
              
              {style.matchingTemplates.length > 0 && (
                <Tooltip title={`${style.matchingTemplates.length} templates match this style`}>
                  <Chip
                    label={`${style.matchingTemplates.length} templates`}
                    size="small"
                    variant="outlined"
                    sx={{ fontWeight: 500 }}
                  />
                </Tooltip>
              )}
            </Box>
          </Box>
        </Box>

        {/* Confidence progress bar */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              Confidence Score
            </Typography>
            <Typography variant="caption" fontWeight={500}>
              {confidencePercentage}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={confidencePercentage}
            sx={{
              height: 6,
              borderRadius: 3,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                bgcolor: confidenceColor === 'success' ? 'success.main' : 
                         confidenceColor === 'warning' ? 'warning.main' : 'info.main',
                borderRadius: 3,
              },
            }}
          />
        </Box>

        {/* Description */}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, lineHeight: 1.6 }}>
          {style.description}
        </Typography>

        {/* Color palette preview */}
        {style.colorPalette.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Palette fontSize="small" color="action" />
              <Typography variant="caption" color="text.secondary">
                Recommended Colors
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {style.colorPalette.slice(0, 5).map((color, index) => (
                <Tooltip key={index} title={color} arrow>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: 1.5,
                      bgcolor: color,
                      border: '2px solid',
                      borderColor: 'background.paper',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    }}
                  />
                </Tooltip>
              ))}
              {style.colorPalette.length > 5 && (
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: 1.5,
                    bgcolor: 'grey.100',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '2px solid',
                    borderColor: 'grey.200',
                  }}
                >
                  <Typography variant="caption" color="text.secondary" fontWeight={600}>
                    +{style.colorPalette.length - 5}
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        )}

        {/* Action button */}
        <Button
          variant={isSelected ? 'contained' : 'outlined'}
          fullWidth
          onClick={onSelect}
          endIcon={<ArrowForward />}
          sx={{
            mt: 1,
            borderRadius: 2,
            textTransform: 'none',
            fontWeight: 600,
          }}
        >
          {isSelected ? 'Selected' : 'Select This Style'}
        </Button>
      </Paper>
    </motion.div>
  );
};

export default StyleRecommendationCard;
