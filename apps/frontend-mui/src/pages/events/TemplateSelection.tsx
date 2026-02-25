/**
 * Template Selection Page with AI Integration
 * 
 * Displays available templates with AI-powered recommendations.
 * Templates are sorted by AI match scores when AI analysis is available.
 */
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardMedia,
  CardContent,
  CardActionArea,
  Chip,
  Alert,
  CircularProgress,
  Button,
  Paper,
  Tooltip,
  IconButton,
  Fade,
  Divider,
  ToggleButtonGroup,
  ToggleButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  ArrowBack,
  ArrowForward,
  AutoAwesome,
  Info,
  FilterList,
  Sort,
  CheckCircle,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { plansApi } from '../../services/api';
import { Template } from '../../types';
import { TemplateRecommendation } from '../../services/aiApi';
import { AIFeatureBadge } from '../../components/ai/AIFeatureBadge';

export interface TemplateSelectionProps {
  /** AI-recommended template IDs for sorting/prioritizing */
  aiRecommendedIds?: string[];
  /** AI-extracted colors for displaying color hints */
  aiAnalysisColors?: Array<{ color: string; name?: string; percentage?: number }>;
  /** Currently selected template ID */
  selectedTemplateId?: string;
  /** Callback when template is selected */
  onTemplateSelect?: (template: Template) => void;
  /** Plan code to filter templates */
  planCode?: string;
  /** Whether to show AI recommendations section */
  showAIRecommendations?: boolean;
  /** Navigation after selection */
  navigateAfterSelect?: boolean;
  /** Continue button action */
  onContinue?: () => void;
  /** Back button action */
  onBack?: () => void;
}

// Plan badge colors
const PLAN_COLORS = {
  BASIC: { bg: '#e3f2fd', color: '#1565c0', label: 'Basic' },
  PREMIUM: { bg: '#fff3e0', color: '#e65100', label: 'Premium' },
  LUXURY: { bg: '#f3e5f5', color: '#7b1fa2', label: 'Luxury' },
};

type SortOption = 'ai-match' | 'name' | 'newest' | 'popular';
type FilterOption = 'all' | 'romantic' | 'modern' | 'traditional' | 'fun';

export const TemplateSelection: React.FC<TemplateSelectionProps> = ({
  aiRecommendedIds = [],
  aiAnalysisColors = [],
  selectedTemplateId: propSelectedId,
  onTemplateSelect,
  planCode: propPlanCode,
  showAIRecommendations = true,
  navigateAfterSelect = false,
  onContinue,
  onBack,
}) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const urlPlanCode = searchParams.get('plan');
  const effectivePlanCode = propPlanCode || urlPlanCode || 'BASIC';
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>(aiRecommendedIds.length > 0 ? 'ai-match' : 'name');
  const [filterBy, setFilterBy] = useState<FilterOption>('all');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, [effectivePlanCode]);

  useEffect(() => {
    if (propSelectedId) {
      const template = templates.find(t => t.id === propSelectedId);
      if (template) {
        setSelectedTemplate(template);
      }
    }
  }, [propSelectedId, templates]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await plansApi.getTemplatesByPlan(effectivePlanCode);
      
      if (response.success && response.data) {
        setTemplates(response.data.templates || []);
      } else {
        setError('Failed to load templates');
      }
    } catch (err) {
      setError('An error occurred while loading templates');
    } finally {
      setLoading(false);
    }
  };

  // Filter and sort templates
  const filteredAndSortedTemplates = useMemo(() => {
    let result = [...templates];
    
    // Apply filter
    if (filterBy !== 'all') {
      result = result.filter(t => {
        const name = t.name.toLowerCase();
        const desc = (t.description || '').toLowerCase();
        const animation = (t.animation_type || '').toLowerCase();
        
        switch (filterBy) {
          case 'romantic':
            return name.includes('romantic') || name.includes('love') || 
                   desc.includes('romantic') || animation.includes('romantic');
          case 'modern':
            return name.includes('modern') || name.includes('minimal') || 
                   desc.includes('modern') || animation.includes('modern');
          case 'traditional':
            return name.includes('traditional') || name.includes('classic') || 
                   desc.includes('traditional') || animation.includes('traditional');
          case 'fun':
            return name.includes('fun') || name.includes('playful') || 
                   desc.includes('fun') || animation.includes('fun');
          default:
            return true;
        }
      });
    }
    
    // Apply sort
    switch (sortBy) {
      case 'ai-match':
        if (aiRecommendedIds.length > 0) {
          result.sort((a, b) => {
            const aIndex = aiRecommendedIds.indexOf(a.id);
            const bIndex = aiRecommendedIds.indexOf(b.id);
            
            if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
            if (aIndex !== -1) return -1;
            if (bIndex !== -1) return 1;
            return a.name.localeCompare(b.name);
          });
        }
        break;
      case 'name':
        result.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case 'newest':
        result.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
        break;
      case 'popular':
        result.sort((a, b) => (b.use_count || 0) - (a.use_count || 0));
        break;
    }
    
    return result;
  }, [templates, filterBy, sortBy, aiRecommendedIds]);

  // Get AI-recommended templates for display
  const aiRecommendedTemplates = useMemo(() => {
    if (!aiRecommendedIds.length) return [];
    return aiRecommendedIds
      .map(id => templates.find(t => t.id === id))
      .filter((t): t is Template => t !== undefined)
      .slice(0, 3);
  }, [templates, aiRecommendedIds]);

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template);
    onTemplateSelect?.(template);
    
    if (navigateAfterSelect) {
      navigate(`/events/create?templateId=${template.id}`);
    }
  };

  const getMatchScore = (templateId: string): number => {
    const index = aiRecommendedIds.indexOf(templateId);
    if (index === -1) return 0;
    return Math.round((1 - index * 0.15) * 100);
  };

  const getMatchColor = (score: number): 'success' | 'warning' | 'default' => {
    if (score >= 85) return 'success';
    if (score >= 70) return 'warning';
    return 'default';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Select a Template
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Choose a design that matches your style
            {aiRecommendedIds.length > 0 && ' - AI recommendations shown first'}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          {aiRecommendedIds.length > 0 && <AIFeatureBadge />}
          
          <Button
            variant="outlined"
            size="small"
            startIcon={<FilterList />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
          </Button>
        </Box>
      </Box>

      {/* AI Recommendations Section */}
      {showAIRecommendations && aiRecommendedTemplates.length > 0 && (
        <Fade in>
          <Paper sx={{ p: 3, mb: 3, bgcolor: 'rgba(76, 175, 80, 0.04)' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <AutoAwesome color="success" />
              <Typography variant="h6" color="success.main">
                AI Recommended Templates
              </Typography>
              <Tooltip title="These templates are recommended based on your photo analysis">
                <IconButton size="small">
                  <Info fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            
            {aiAnalysisColors.length > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Based on colors from your photo:
                </Typography>
                {aiAnalysisColors.slice(0, 5).map((color, idx) => (
                  <Tooltip key={idx} title={color.name || color.color}>
                    <Box
                      sx={{
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        backgroundColor: color.color,
                        border: '2px solid white',
                        boxShadow: '0 0 0 1px rgba(0,0,0,0.1)',
                      }}
                    />
                  </Tooltip>
                ))}
              </Box>
            )}
            
            <Grid container spacing={2}>
              {aiRecommendedTemplates.map((template, index) => {
                const matchScore = getMatchScore(template.id);
                return (
                  <Grid item xs={12} sm={6} md={4} key={template.id}>
                    <Card
                      sx={{
                        border: selectedTemplate?.id === template.id ? 3 : 2,
                        borderColor: selectedTemplate?.id === template.id ? 'primary.main' : 'success.main',
                        position: 'relative',
                      }}
                    >
                      <Chip
                        icon={<AutoAwesome />}
                        label={`${matchScore}% Match`}
                        color={getMatchColor(matchScore)}
                        size="small"
                        sx={{
                          position: 'absolute',
                          top: 8,
                          left: 8,
                          zIndex: 1,
                          fontWeight: 600,
                        }}
                      />
                      <CardActionArea onClick={() => handleTemplateSelect(template)}>
                        <CardMedia
                          component="img"
                          height="160"
                          image={template.thumbnail || '/images/template-placeholder.jpg'}
                          alt={template.name}
                        />
                        <CardContent>
                          <Typography variant="subtitle1" fontWeight={600} noWrap>
                            {template.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" noWrap>
                            {template.description}
                          </Typography>
                        </CardContent>
                      </CardActionArea>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </Paper>
        </Fade>
      )}

      {/* Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            <Paper sx={{ p: 2, mb: 3 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Sort By</InputLabel>
                    <Select
                      value={sortBy}
                      label="Sort By"
                      onChange={(e) => setSortBy(e.target.value as SortOption)}
                      startAdornment={<Sort sx={{ mr: 1, color: 'action.active' }} />}
                    >
                      {aiRecommendedIds.length > 0 && (
                        <MenuItem value="ai-match">
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <AutoAwesome fontSize="small" />
                            AI Match Score
                          </Box>
                        </MenuItem>
                      )}
                      <MenuItem value="name">Name (A-Z)</MenuItem>
                      <MenuItem value="newest">Newest First</MenuItem>
                      <MenuItem value="popular">Most Popular</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <ToggleButtonGroup
                    value={filterBy}
                    exclusive
                    onChange={(e, value) => value && setFilterBy(value)}
                    size="small"
                    fullWidth
                  >
                    <ToggleButton value="all">All</ToggleButton>
                    <ToggleButton value="romantic">Romantic</ToggleButton>
                    <ToggleButton value="modern">Modern</ToggleButton>
                    <ToggleButton value="traditional">Classic</ToggleButton>
                    <ToggleButton value="fun">Fun</ToggleButton>
                  </ToggleButtonGroup>
                </Grid>
              </Grid>
            </Paper>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* All Templates Grid */}
      <Grid container spacing={3}>
        {filteredAndSortedTemplates.map((template, index) => {
          const isAIRecommended = aiRecommendedIds.indexOf(template.id) !== -1;
          const matchScore = getMatchScore(template.id);
          const planInfo = PLAN_COLORS[template.plan_code as keyof typeof PLAN_COLORS] || PLAN_COLORS.BASIC;
          
          return (
            <Grid item xs={12} sm={6} md={4} key={template.id}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  sx={{
                    border: selectedTemplate?.id === template.id ? 3 : isAIRecommended ? 2 : 1,
                    borderColor: selectedTemplate?.id === template.id 
                      ? 'primary.main' 
                      : isAIRecommended 
                        ? 'success.main' 
                        : 'divider',
                    position: 'relative',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                    },
                  }}
                >
                  {/* Match Score Badge */}
                  {isAIRecommended && matchScore > 0 && (
                    <Chip
                      icon={<AutoAwesome />}
                      label={`${matchScore}% Match`}
                      color={getMatchColor(matchScore)}
                      size="small"
                      sx={{
                        position: 'absolute',
                        top: 8,
                        left: 8,
                        zIndex: 1,
                        fontWeight: 600,
                      }}
                    />
                  )}
                  
                  {/* Plan Badge */}
                  <Chip
                    label={planInfo.label}
                    size="small"
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      zIndex: 1,
                      bgcolor: planInfo.bg,
                      color: planInfo.color,
                      fontWeight: 600,
                    }}
                  />
                  
                  {/* Selected Indicator */}
                  {selectedTemplate?.id === template.id && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        zIndex: 2,
                        bgcolor: 'primary.main',
                        color: 'white',
                        borderRadius: '50%',
                        p: 1,
                      }}
                    >
                      <CheckCircle sx={{ fontSize: 40 }} />
                    </Box>
                  )}
                  
                  <CardActionArea 
                    onClick={() => handleTemplateSelect(template)}
                    sx={{ 
                      opacity: selectedTemplate?.id === template.id ? 0.7 : 1,
                    }}
                  >
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
                      
                      {/* Match reasons tooltip */}
                      {isAIRecommended && (
                        <Tooltip title="AI recommended based on your photo analysis">
                          <Chip
                            icon={<Info fontSize="small" />}
                            label="AI Match"
                            size="small"
                            color="success"
                            variant="outlined"
                            sx={{ mt: 1, height: 24 }}
                          />
                        </Tooltip>
                      )}
                      
                      <Chip
                        label={template.animation_type}
                        size="small"
                        sx={{ mt: 1, ml: isAIRecommended ? 1 : 0 }}
                      />
                    </CardContent>
                  </CardActionArea>
                </Card>
              </motion.div>
            </Grid>
          );
        })}
      </Grid>

      {/* Empty State */}
      {filteredAndSortedTemplates.length === 0 && !loading && (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No templates found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your filters or search criteria
          </Typography>
        </Paper>
      )}

      {/* Navigation Buttons */}
      {(onBack || onContinue) && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          {onBack && (
            <Button
              variant="outlined"
              onClick={onBack}
              startIcon={<ArrowBack />}
            >
              Back
            </Button>
          )}
          
          {onContinue && (
            <Button
              variant="contained"
              onClick={onContinue}
              disabled={!selectedTemplate}
              endIcon={<ArrowForward />}
            >
              Continue
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
};

export default TemplateSelection;
