/**
 * Template Recommendation Grid Component
 * 
 * Displays a grid of AI-recommended templates with match scores,
 * selection states, and plan badges.
 */
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  Tooltip,
  IconButton,
  Badge,
  Skeleton,
} from '@mui/material';
import {
  CheckCircle,
  Info,
  Star,
  LocalOffer,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { TemplateRecommendation } from '../../services/aiApi';

export interface TemplateRecommendationGridProps {
  /** Array of template recommendations */
  recommendations: TemplateRecommendation[];
  /** Callback when a template is selected */
  onTemplateSelect: (templateId: string) => void;
  /** Currently selected template ID */
  selectedTemplateId?: string;
  /** Whether data is loading */
  loading?: boolean;
}

// Plan badge colors
const PLAN_COLORS = {
  BASIC: { bg: '#e3f2fd', color: '#1565c0', label: 'Basic' },
  PREMIUM: { bg: '#fff3e0', color: '#e65100', label: 'Premium' },
  LUXURY: { bg: '#f3e5f5', color: '#7b1fa2', label: 'Luxury' },
};

interface TemplateCardProps {
  template: TemplateRecommendation;
  isSelected: boolean;
  onSelect: () => void;
  index: number;
}

const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  isSelected,
  onSelect,
  index,
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [showReasons, setShowReasons] = useState(false);

  const matchScorePercentage = Math.round(template.matchScore * 100);
  
  // Get match score color
  const getMatchColor = (score: number): 'success' | 'warning' | 'default' => {
    if (score >= 0.85) return 'success';
    if (score >= 0.7) return 'warning';
    return 'default';
  };

  const matchColor = getMatchColor(template.matchScore);

  // Extract plan code from description or default to BASIC
  const planCode: keyof typeof PLAN_COLORS = 'BASIC'; // This should come from template data
  const planInfo = PLAN_COLORS[planCode];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.3 }}
      whileHover={{ y: -4 }}
    >
      <Paper
        elevation={isSelected ? 4 : 1}
        onClick={onSelect}
        sx={{
          cursor: 'pointer',
          borderRadius: 3,
          overflow: 'hidden',
          border: 2,
          borderColor: isSelected ? 'primary.main' : 'transparent',
          position: 'relative',
          transition: 'all 0.2s ease',
          '&:hover': {
            boxShadow: '0 12px 32px rgba(0, 0, 0, 0.15)',
          },
        }}
      >
        {/* Thumbnail container */}
        <Box sx={{ position: 'relative', aspectRatio: '4/3' }}>
          {/* Loading skeleton */}
          {!imageLoaded && (
            <Skeleton
              variant="rectangular"
              sx={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
              }}
            />
          )}
          
          {/* Template image */}
          <Box
            component="img"
            src={template.thumbnail}
            alt={template.name}
            onLoad={() => setImageLoaded(true)}
            sx={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              display: imageLoaded ? 'block' : 'none',
            }}
          />

          {/* Match score badge */}
          <Box
            sx={{
              position: 'absolute',
              top: 8,
              left: 8,
            }}
          >
            <Chip
              icon={<Star sx={{ fontSize: '14px !important' }} />}
              label={`${matchScorePercentage}% Match`}
              size="small"
              color={matchColor}
              sx={{
                fontWeight: 600,
                boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
              }}
            />
          </Box>

          {/* Plan badge */}
          <Box
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
            }}
          >
            <Chip
              icon={<LocalOffer sx={{ fontSize: '14px !important' }} />}
              label={planInfo.label}
              size="small"
              sx={{
                fontWeight: 600,
                bgcolor: planInfo.bg,
                color: planInfo.color,
                boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
              }}
            />
          </Box>

          {/* Selected indicator */}
          <AnimatePresence>
            {isSelected && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <Box
                  sx={{
                    position: 'absolute',
                    inset: 0,
                    bgcolor: 'rgba(166, 30, 42, 0.8)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 1,
                  }}
                >
                  <CheckCircle sx={{ color: 'white', fontSize: 48 }} />
                  <Typography variant="h6" color="white" fontWeight={600}>
                    Selected
                  </Typography>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Hover overlay with reasons */}
          {!isSelected && (
            <Box
              onMouseEnter={() => setShowReasons(true)}
              onMouseLeave={() => setShowReasons(false)}
              sx={{
                position: 'absolute',
                inset: 0,
                bgcolor: 'rgba(0, 0, 0, 0.7)',
                opacity: showReasons ? 1 : 0,
                transition: 'opacity 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-end',
                p: 2,
              }}
            >
              <Typography variant="caption" color="white" fontWeight={600} gutterBottom>
                Why this matches:
              </Typography>
              {template.matchReasons.slice(0, 3).map((reason, idx) => (
                <Typography
                  key={idx}
                  variant="caption"
                  color="rgba(255,255,255,0.9)"
                  sx={{ display: 'block', mb: 0.25 }}
                >
                  • {reason}
                </Typography>
              ))}
            </Box>
          )}
        </Box>

        {/* Template info */}
        <Box sx={{ p: 2 }}>
          <Typography variant="subtitle1" fontWeight={600} noWrap>
            {template.name}
          </Typography>
          
          {template.description && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                mt: 0.5,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
              }}
            >
              {template.description}
            </Typography>
          )}

          {/* Match reasons tooltip trigger */}
          <Box sx={{ mt: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip
              title={
                <Box>
                  <Typography variant="caption" fontWeight={600}>
                    Match Reasons:
                  </Typography>
                  {template.matchReasons.map((reason, idx) => (
                    <Typography key={idx} variant="caption" display="block">
                      • {reason}
                    </Typography>
                  ))}
                </Box>
              }
              arrow
              placement="bottom"
            >
              <Chip
                icon={<Info sx={{ fontSize: '14px !important' }} />}
                label={`${template.matchReasons.length} reasons`}
                size="small"
                variant="outlined"
                sx={{ height: 24, cursor: 'help' }}
              />
            </Tooltip>

            {template.animationType && (
              <Chip
                label={template.animationType}
                size="small"
                color="secondary"
                variant="outlined"
                sx={{ height: 24 }}
              />
            )}
          </Box>
        </Box>
      </Paper>
    </motion.div>
  );
};

export const TemplateRecommendationGrid: React.FC<TemplateRecommendationGridProps> = ({
  recommendations,
  onTemplateSelect,
  selectedTemplateId,
  loading = false,
}) => {
  if (loading) {
    return (
      <Box>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Recommended Templates
        </Typography>
        <Grid container spacing={2}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 3 }} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <Paper
        elevation={1}
        sx={{
          p: 4,
          textAlign: 'center',
          borderRadius: 3,
          bgcolor: 'grey.50',
        }}
      >
        <Star sx={{ fontSize: 48, color: 'grey.300', mb: 1 }} />
        <Typography variant="body2" color="text.secondary">
          No template recommendations yet
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
          Upload a photo to get personalized template recommendations
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h6" fontWeight={600}>
            Recommended Templates
          </Typography>
          <Typography variant="body2" color="text.secondary">
            AI-picked templates based on your photo analysis
          </Typography>
        </Box>
        <Chip
          label={`${recommendations.length} found`}
          size="small"
          color="primary"
          variant="outlined"
        />
      </Box>

      {/* Grid */}
      <Grid container spacing={2}>
        {recommendations.map((template, index) => (
          <Grid item xs={12} sm={6} md={4} key={template.templateId}>
            <TemplateCard
              template={template}
              isSelected={selectedTemplateId === template.templateId}
              onSelect={() => onTemplateSelect(template.templateId)}
              index={index}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default TemplateRecommendationGrid;
