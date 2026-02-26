/**
 * Plan Card Skeleton
 */
import React from 'react';
import { Grid, Card, CardContent, Skeleton, Box } from '@mui/material';

interface PlanCardSkeletonProps {
  count?: number;
}

const PlanCardSkeleton: React.FC<PlanCardSkeletonProps> = ({ count = 3 }) => {
  return (
    <Grid container spacing={4} justifyContent="center">
      {Array.from({ length: count }).map((_, index) => (
        <Grid item xs={12} md={4} key={index}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 4 }}>
              {/* Icon */}
              <Skeleton variant="circular" width={60} height={60} sx={{ mb: 2 }} />

              {/* Plan Name */}
              <Skeleton variant="text" width="60%" height={36} sx={{ mb: 1 }} />

              {/* Description */}
              <Skeleton variant="text" width="100%" height={20} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="80%" height={20} sx={{ mb: 3 }} />

              {/* Price */}
              <Skeleton variant="text" width="50%" height={48} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="40%" height={20} sx={{ mb: 4 }} />

              {/* Features */}
              <Box sx={{ mb: 3 }}>
                {Array.from({ length: 5 }).map((_, i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Skeleton variant="circular" width={24} height={24} sx={{ mr: 1 }} />
                    <Skeleton variant="text" width="70%" height={20} />
                  </Box>
                ))}
              </Box>

              {/* Button */}
              <Skeleton variant="rectangular" width="100%" height={42} sx={{ borderRadius: 1 }} />
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default PlanCardSkeleton;
