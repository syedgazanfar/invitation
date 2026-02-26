/**
 * Empty State Component
 *
 * Display when there's no data to show
 *
 * @example
 * ```tsx
 * <EmptyState
 *   icon={<InboxIcon />}
 *   title="No invitations yet"
 *   description="Create your first invitation to get started"
 *   action={<Button onClick={handleCreate}>Create Invitation</Button>}
 * />
 * ```
 */
import React from 'react';
import {
  Box,
  Typography,
} from '@mui/material';

export interface EmptyStateProps {
  /**
   * Icon to display
   */
  icon?: React.ReactNode;
  /**
   * Title text
   */
  title: string;
  /**
   * Description text
   */
  description?: string;
  /**
   * Optional action button
   */
  action?: React.ReactNode;
  /**
   * Minimum height
   */
  minHeight?: string | number;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  minHeight = 300,
}) => {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight={minHeight}
      textAlign="center"
      py={6}
    >
      {icon && (
        <Box
          sx={{
            fontSize: 80,
            color: 'text.disabled',
            mb: 2,
          }}
        >
          {icon}
        </Box>
      )}

      <Typography variant="h6" fontWeight={600} gutterBottom>
        {title}
      </Typography>

      {description && (
        <Typography
          variant="body2"
          color="text.secondary"
          maxWidth={400}
          mb={3}
        >
          {description}
        </Typography>
      )}

      {action}
    </Box>
  );
};

export default EmptyState;
