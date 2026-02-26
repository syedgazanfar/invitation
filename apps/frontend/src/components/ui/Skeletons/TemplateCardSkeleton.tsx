/**
 * Template Card Skeleton
 */
import React from 'react';
import { Grid, Card, CardContent, Skeleton, Box } from '@mui/material';

interface TemplateCardSkeletonProps {
  count?: number;
}

const TemplateCardSkeleton: React.FC<TemplateCardSkeletonProps> = ({ count = 9 }) => {
  return (
    <Grid container spacing={3}>
      {Array.from({ length: count }).map((_, index) => (
        <Grid item xs={12} sm={6} md={4} key={index}>
          <Card>
            <Skeleton variant="rectangular" height={200} />
            <CardContent>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 1 }} />
                <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 1 }} />
              </Box>
              <Skeleton variant="text" width="80%" height={28} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="100%" height={20} sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', gap: 0.5, mb: 2 }}>
                <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 1 }} />
                <Skeleton variant="rectangular" width={50} height={24} sx={{ borderRadius: 1 }} />
              </Box>
              <Skeleton variant="text" width="40%" height={16} sx={{ mb: 2 }} />
              <Skeleton variant="rectangular" width="100%" height={36} sx={{ borderRadius: 1 }} />
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default TemplateCardSkeleton;
