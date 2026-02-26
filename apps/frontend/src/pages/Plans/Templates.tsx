/**
 * Templates Showcase Page
 *
 * Displays all available templates with filtering by category and plan.
 * Users can preview templates and select one to create an invitation.
 */
import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  CardActionArea,
  Chip,
  Button,
  ToggleButton,
  ToggleButtonGroup,
  TextField,
  InputAdornment,
  MenuItem,
  Alert,
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  IconButton,
  useTheme,
} from '@mui/material';
import {
  Search,
  FilterList,
  Close,
  ArrowForward,
  Star,
  Favorite,
  Cake,
  Celebration,
  Mosque,
  TempleHindu,
  Church,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { plansApi } from '../../services/api';
import { Template, InvitationCategory } from '../../types';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/EmptyState';

const Templates: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [templates, setTemplates] = useState<Template[]>([]);
  const [categories, setCategories] = useState<InvitationCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>(searchParams.get('category') || 'ALL');
  const [selectedPlan, setSelectedPlan] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<string>('popular');

  // Preview Dialog
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    // Update category from URL params
    const categoryParam = searchParams.get('category');
    if (categoryParam) {
      setSelectedCategory(categoryParam.toUpperCase());
    }
  }, [searchParams]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [templatesRes, categoriesRes] = await Promise.all([
        plansApi.getTemplates(),
        plansApi.getCategories(),
      ]);

      if (templatesRes.success && templatesRes.data) {
        setTemplates(templatesRes.data);
      }
      if (categoriesRes.success && categoriesRes.data) {
        setCategories(categoriesRes.data);
      }
    } catch (err: any) {
      console.error('Failed to fetch data:', err);
      setError('Failed to load templates. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (name: string) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('wedding')) return Favorite;
    if (lowerName.includes('birthday')) return Cake;
    if (lowerName.includes('party')) return Celebration;
    if (lowerName.includes('eid')) return Mosque;
    if (lowerName.includes('diwali')) return TempleHindu;
    if (lowerName.includes('christmas')) return Church;
    return Star;
  };

  // Filter templates
  const filteredTemplates = templates.filter((template) => {
    // Category filter
    if (selectedCategory !== 'ALL' && template.category_name.toUpperCase() !== selectedCategory) {
      return false;
    }

    // Plan filter
    if (selectedPlan !== 'ALL' && template.plan_code !== selectedPlan) {
      return false;
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        template.name.toLowerCase().includes(query) ||
        template.description.toLowerCase().includes(query) ||
        template.category_name.toLowerCase().includes(query)
      );
    }

    return true;
  });

  // Sort templates
  const sortedTemplates = [...filteredTemplates].sort((a, b) => {
    switch (sortBy) {
      case 'popular':
        return b.use_count - a.use_count;
      case 'name':
        return a.name.localeCompare(b.name);
      case 'newest':
        return b.id.localeCompare(a.id);
      default:
        return 0;
    }
  });

  const handleUseTemplate = (template: Template) => {
    // Navigate to event creation with this template pre-selected
    navigate(`/invitation/builder?template=${template.id}`);
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
          pb: { xs: 4, md: 6 },
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
              Beautiful Invitation Templates
            </Typography>
            <Typography variant="h5" color="text.secondary">
              Choose from our professionally designed animated templates
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

      {/* Filters */}
      <Box sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider', py: 3 }}>
        <Container maxWidth="lg">
          <Grid container spacing={3} alignItems="center">
            {/* Search */}
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search templates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>

            {/* Category Filter */}
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                select
                fullWidth
                size="small"
                label="Category"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                <MenuItem value="ALL">All Categories</MenuItem>
                {categories.map((category) => (
                  <MenuItem key={category.code} value={category.code}>
                    {category.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>

            {/* Sort */}
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                select
                fullWidth
                size="small"
                label="Sort By"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <MenuItem value="popular">Most Popular</MenuItem>
                <MenuItem value="name">Name (A-Z)</MenuItem>
                <MenuItem value="newest">Newest First</MenuItem>
              </TextField>
            </Grid>
          </Grid>

          {/* Category Pills */}
          <Box sx={{ mt: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              label="All"
              onClick={() => setSelectedCategory('ALL')}
              color={selectedCategory === 'ALL' ? 'primary' : 'default'}
              variant={selectedCategory === 'ALL' ? 'filled' : 'outlined'}
            />
            {categories.map((category) => {
              const Icon = getCategoryIcon(category.name);
              return (
                <Chip
                  key={category.code}
                  icon={<Icon />}
                  label={category.name}
                  onClick={() => setSelectedCategory(category.code)}
                  color={selectedCategory === category.code ? 'primary' : 'default'}
                  variant={selectedCategory === category.code ? 'filled' : 'outlined'}
                />
              );
            })}
          </Box>
        </Container>
      </Box>

      {/* Templates Grid */}
      <Box sx={{ py: 6 }}>
        <Container maxWidth="lg">
          {/* Results Count */}
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Showing {sortedTemplates.length} template{sortedTemplates.length !== 1 ? 's' : ''}
            </Typography>
            {(selectedCategory !== 'ALL' || selectedPlan !== 'ALL' || searchQuery) && (
              <Button
                size="small"
                startIcon={<Close />}
                onClick={() => {
                  setSelectedCategory('ALL');
                  setSelectedPlan('ALL');
                  setSearchQuery('');
                }}
              >
                Clear Filters
              </Button>
            )}
          </Box>

          {/* Templates */}
          {sortedTemplates.length === 0 ? (
            <EmptyState
              icon={FilterList}
              title="No templates found"
              message={
                searchQuery || selectedCategory !== 'ALL' || selectedPlan !== 'ALL'
                  ? 'Try adjusting your filters or search query.'
                  : 'No templates available at the moment.'
              }
              action={
                (searchQuery || selectedCategory !== 'ALL' || selectedPlan !== 'ALL') && (
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setSelectedCategory('ALL');
                      setSelectedPlan('ALL');
                      setSearchQuery('');
                    }}
                  >
                    Clear Filters
                  </Button>
                )
              }
            />
          ) : (
            <Grid container spacing={3}>
              {sortedTemplates.map((template, index) => {
                const CategoryIcon = getCategoryIcon(template.category_name);
                return (
                  <Grid item xs={12} sm={6} md={4} key={template.id}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.05 }}
                    >
                      <Card
                        sx={{
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          transition: 'transform 0.3s, box-shadow 0.3s',
                          '&:hover': {
                            transform: 'translateY(-8px)',
                            boxShadow: theme.shadows[8],
                          },
                        }}
                      >
                        <CardActionArea onClick={() => setPreviewTemplate(template)}>
                          <CardMedia
                            component="img"
                            height="200"
                            image={template.thumbnail || 'https://via.placeholder.com/400x300/7B2CBF/FFFFFF?text=Template+Preview'}
                            alt={template.name}
                            sx={{ bgcolor: 'grey.200' }}
                          />
                          <CardContent sx={{ flexGrow: 1 }}>
                            {/* Category & Premium Badge */}
                            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                              <Chip
                                icon={<CategoryIcon />}
                                label={template.category_name}
                                size="small"
                                variant="outlined"
                              />
                              {template.is_premium && (
                                <Chip
                                  icon={<Star />}
                                  label="Premium"
                                  size="small"
                                  color="primary"
                                />
                              )}
                            </Box>

                            {/* Template Name */}
                            <Typography variant="h6" fontWeight={600} gutterBottom>
                              {template.name}
                            </Typography>

                            {/* Description */}
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                              {template.description}
                            </Typography>

                            {/* Features */}
                            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 2 }}>
                              {template.supports_gallery && (
                                <Chip label="Gallery" size="small" variant="outlined" />
                              )}
                              {template.supports_music && (
                                <Chip label="Music" size="small" variant="outlined" />
                              )}
                              {template.supports_video && (
                                <Chip label="Video" size="small" variant="outlined" />
                              )}
                            </Box>

                            {/* Stats */}
                            <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                              Used by {template.use_count} users
                            </Typography>

                            {/* CTA Button */}
                            <Button
                              fullWidth
                              variant="contained"
                              endIcon={<ArrowForward />}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleUseTemplate(template);
                              }}
                            >
                              Use This Template
                            </Button>
                          </CardContent>
                        </CardActionArea>
                      </Card>
                    </motion.div>
                  </Grid>
                );
              })}
            </Grid>
          )}
        </Container>
      </Box>

      {/* Preview Dialog */}
      <Dialog
        open={!!previewTemplate}
        onClose={() => setPreviewTemplate(null)}
        maxWidth="md"
        fullWidth
      >
        {previewTemplate && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h5" fontWeight={600}>
                  {previewTemplate.name}
                </Typography>
                <IconButton onClick={() => setPreviewTemplate(null)}>
                  <Close />
                </IconButton>
              </Box>
            </DialogTitle>
            <DialogContent>
              {/* Preview Image */}
              <Box
                component="img"
                src={previewTemplate.thumbnail || 'https://via.placeholder.com/800x600/7B2CBF/FFFFFF?text=Template+Preview'}
                alt={previewTemplate.name}
                sx={{
                  width: '100%',
                  borderRadius: 2,
                  mb: 3,
                }}
              />

              {/* Details */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="body1" gutterBottom>
                  {previewTemplate.description}
                </Typography>
              </Box>

              {/* Features */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                  Features:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip label={previewTemplate.category_name} size="small" />
                  <Chip label={`${previewTemplate.animation_type} Animation`} size="small" />
                  {previewTemplate.supports_gallery && <Chip label="Photo Gallery" size="small" />}
                  {previewTemplate.supports_music && <Chip label="Background Music" size="small" />}
                  {previewTemplate.supports_video && <Chip label="Video Support" size="small" />}
                  {previewTemplate.is_premium && <Chip label="Premium" size="small" color="primary" />}
                </Box>
              </Box>

              {/* Stats */}
              <Typography variant="caption" color="text.secondary">
                Used by {previewTemplate.use_count} happy users
              </Typography>
            </DialogContent>
            <DialogActions sx={{ px: 3, pb: 3 }}>
              <Button onClick={() => setPreviewTemplate(null)}>
                Close
              </Button>
              <Button
                variant="contained"
                endIcon={<ArrowForward />}
                onClick={() => {
                  handleUseTemplate(previewTemplate);
                  setPreviewTemplate(null);
                }}
              >
                Use This Template
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* CTA Section */}
      <Box
        sx={{
          py: 8,
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h3" color="white" gutterBottom fontWeight={700}>
            Ready to Create Your Invitation?
          </Typography>
          <Typography variant="h6" color="rgba(255,255,255,0.9)" sx={{ mb: 4 }}>
            Select a template and start customizing in minutes
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              component={Link}
              to="/plans"
              variant="contained"
              size="large"
              sx={{
                bgcolor: 'white',
                color: 'primary.main',
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.9)',
                },
              }}
            >
              View Plans
            </Button>
            <Button
              component={Link}
              to="/register"
              variant="outlined"
              size="large"
              sx={{
                color: 'white',
                borderColor: 'white',
                '&:hover': {
                  borderColor: 'rgba(255,255,255,0.9)',
                  bgcolor: 'rgba(255,255,255,0.1)',
                },
              }}
            >
              Sign Up Free
            </Button>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default Templates;
