/**
 * AI Feature Badge
 * 
 * A small badge component that promotes AI-powered features throughout the app.
 * Features a sparkle animation and can be clicked to open AI assistant features.
 */
import React from 'react';
import {
  Chip,
  Tooltip,
  Box,
  keyframes,
  styled,
} from '@mui/material';
import {
  AutoAwesome,
  SmartToy,
} from '@mui/icons-material';

// Sparkle animation
const sparkle = keyframes`
  0%, 100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1) rotate(10deg);
  }
`;

const pulse = keyframes`
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(166, 30, 42, 0.4);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(166, 30, 42, 0);
  }
`;

const AnimatedIcon = styled(AutoAwesome)(({ theme }) => ({
  animation: `${sparkle} 2s ease-in-out infinite`,
  fontSize: '16px',
}));

export interface AIFeatureBadgeProps {
  /** Size of the badge */
  size?: 'small' | 'medium';
  /** Variant style */
  variant?: 'default' | 'outlined' | 'filled';
  /** Optional click handler */
  onClick?: () => void;
  /** Custom tooltip text */
  tooltipText?: string;
  /** Whether to show pulse animation */
  pulse?: boolean;
}

export const AIFeatureBadge: React.FC<AIFeatureBadgeProps> = ({
  size = 'medium',
  variant = 'default',
  onClick,
  tooltipText = 'Powered by AI - Click to learn more',
  pulse: shouldPulse = false,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'outlined':
        return {
          bgcolor: 'transparent',
          color: 'primary.main',
          border: '1px solid',
          borderColor: 'primary.main',
        };
      case 'filled':
        return {
          bgcolor: 'primary.main',
          color: 'white',
        };
      default:
        return {
          bgcolor: 'rgba(166, 30, 42, 0.08)',
          color: 'primary.main',
        };
    }
  };

  const chip = (
    <Chip
      icon={<AnimatedIcon />}
      label="AI Powered"
      size={size}
      onClick={onClick}
      sx={{
        ...getVariantStyles(),
        fontWeight: 600,
        cursor: onClick ? 'pointer' : 'default',
        animation: shouldPulse ? `${pulse} 2s infinite` : 'none',
        '&:hover': onClick ? {
          bgcolor: variant === 'filled' ? 'primary.dark' : 'rgba(166, 30, 42, 0.12)',
        } : {},
        '& .MuiChip-icon': {
          ml: '8px',
        },
      }}
    />
  );

  if (onClick || tooltipText) {
    return (
      <Tooltip title={tooltipText} arrow placement="top">
        {chip}
      </Tooltip>
    );
  }

  return chip;
};

/**
 * Compact AI indicator for use in tight spaces
 */
export interface AIIndicatorProps {
  /** Size of the indicator */
  size?: 'small' | 'medium';
  /** Optional tooltip text */
  tooltipText?: string;
}

export const AIIndicator: React.FC<AIIndicatorProps> = ({
  size = 'small',
  tooltipText = 'AI Powered',
}) => {
  const sizePx = size === 'small' ? 16 : 20;

  const indicator = (
    <Box
      sx={{
        width: sizePx,
        height: sizePx,
        borderRadius: '50%',
        bgcolor: 'primary.main',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        animation: `${sparkle} 2s ease-in-out infinite`,
      }}
    >
      <AutoAwesome sx={{ fontSize: sizePx * 0.6, color: 'white' }} />
    </Box>
  );

  return (
    <Tooltip title={tooltipText} arrow>
      {indicator}
    </Tooltip>
  );
};

/**
 * AI Assistant button for floating action or toolbar use
 */
export interface AIAssistantButtonProps {
  /** Click handler */
  onClick: () => void;
  /** Button size */
  size?: 'small' | 'medium' | 'large';
  /** Whether the button is extended with label */
  extended?: boolean;
}

export const AIAssistantButton: React.FC<AIAssistantButtonProps> = ({
  onClick,
  size = 'medium',
  extended = false,
}) => {
  const sizeMap = {
    small: { px: 1.5, py: 0.5, fontSize: '0.75rem' },
    medium: { px: 2, py: 1, fontSize: '0.875rem' },
    large: { px: 3, py: 1.5, fontSize: '1rem' },
  };

  const { px, py, fontSize } = sizeMap[size];

  return (
    <Box
      onClick={onClick}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 1,
        px,
        py,
        bgcolor: 'primary.main',
        color: 'white',
        borderRadius: 2,
        cursor: 'pointer',
        fontSize,
        fontWeight: 600,
        boxShadow: '0 4px 14px rgba(166, 30, 42, 0.4)',
        transition: 'all 0.2s ease',
        animation: `${pulse} 2s infinite`,
        '&:hover': {
          bgcolor: 'primary.dark',
          transform: 'translateY(-2px)',
          boxShadow: '0 6px 20px rgba(166, 30, 42, 0.5)',
        },
      }}
    >
      <SmartToy sx={{ fontSize: fontSize }} />
      {extended && <span>AI Assistant</span>}
    </Box>
  );
};

export default AIFeatureBadge;
