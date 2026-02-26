/**
 * Dashboard Stats Cards Skeleton
 */
import React from 'react';
import { Grid, Card, CardContent, Skeleton, Box } from '@mui/material';

interface DashboardSkeletonProps {
  cards?: number;
}

const DashboardSkeleton: React.FC<DashboardSkeletonProps> = ({ cards = 4 }) => {
  return (
    <Grid container spacing={3}>
      {Array.from({ length: cards }).map((_, index) => (
        <Grid item xs={12} sm={6} md={3} key={index}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
                <Skeleton variant="text" width="60%" height={24} />
              </Box>
              <Skeleton variant="text" width="40%" height={40} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="70%" height={20} />
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default DashboardSkeleton;
