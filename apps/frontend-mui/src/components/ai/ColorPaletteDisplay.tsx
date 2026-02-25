/**
 * Color Palette Display Component
 * 
 * Displays extracted color palette from photo analysis with interactive
 * color swatches, copy-to-clipboard functionality, and percentage indicators.
 */
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tooltip,
  IconButton,
  Fade,
  Chip,
} from '@mui/material';
import {
  ContentCopy,
  Check,
  Palette,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

export interface ColorPaletteDisplayProps {
  /** Array of extracted colors */
  colors: Array<{
    color: string;
    name: string;
    percentage: number;
  }>;
  /** Callback when a color is clicked */
  onColorClick?: (color: string) => void;
}

interface ColorSwatchProps {
  color: string;
  name: string;
  percentage: number;
  index: number;
  onColorClick?: (color: string) => void;
}

const ColorSwatch: React.FC<ColorSwatchProps> = ({
  color,
  name,
  percentage,
  index,
  onColorClick,
}) => {
  const [copied, setCopied] = useState(false);

  const handleClick = async () => {
    try {
      await navigator.clipboard.writeText(color);
      setCopied(true);
      onColorClick?.(color);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy color:', err);
    }
  };

  const isLight = isLightColor(color);

  return (
    <Tooltip
      title={copied ? 'Copied!' : `Click to copy ${color}`}
      placement="top"
      arrow
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: index * 0.1, duration: 0.3 }}
      >
        <Paper
          elevation={2}
          onClick={handleClick}
          sx={{
            cursor: 'pointer',
            borderRadius: 2,
            overflow: 'hidden',
            transition: 'transform 0.2s ease, box-shadow 0.2s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
            },
          }}
        >
          {/* Color preview */}
          <Box
            sx={{
              height: 80,
              bgcolor: color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
            }}
          >
            <Fade in={copied}>
              <Box
                sx={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: 'rgba(0,0,0,0.3)',
                }}
              >
                <Check sx={{ color: 'white', fontSize: 32 }} />
              </Box>
            </Fade>
            
            {!copied && (
              <IconButton
                size="small"
                sx={{
                  opacity: 0,
                  transition: 'opacity 0.2s',
                  color: isLight ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.8)',
                  '&:hover': {
                    opacity: 1,
                    bgcolor: isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.2)',
                  },
                  '.MuiPaper-root:hover &': {
                    opacity: 1,
                  },
                }}
              >
                <ContentCopy fontSize="small" />
              </IconButton>
            )}
          </Box>

          {/* Color info */}
          <Box sx={{ p: 1.5 }}>
            <Typography
              variant="body2"
              fontWeight={600}
              sx={{ fontFamily: 'monospace', letterSpacing: '0.5px' }}
            >
              {color.toUpperCase()}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              {name}
            </Typography>
            
            {/* Percentage bar */}
            <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  flex: 1,
                  height: 4,
                  bgcolor: 'grey.200',
                  borderRadius: 2,
                  overflow: 'hidden',
                }}
              >
                <Box
                  sx={{
                    height: '100%',
                    width: `${percentage}%`,
                    bgcolor: color,
                    borderRadius: 2,
                    transition: 'width 0.5s ease-out',
                  }}
                />
              </Box>
              <Typography variant="caption" color="text.secondary" fontWeight={500}>
                {Math.round(percentage)}%
              </Typography>
            </Box>
          </Box>
        </Paper>
      </motion.div>
    </Tooltip>
  );
};

export const ColorPaletteDisplay: React.FC<ColorPaletteDisplayProps> = ({
  colors,
  onColorClick,
}) => {
  if (!colors || colors.length === 0) {
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
        <Palette sx={{ fontSize: 48, color: 'grey.300', mb: 1 }} />
        <Typography variant="body2" color="text.secondary">
          No colors extracted yet
        </Typography>
      </Paper>
    );
  }

  // Sort colors by percentage (descending)
  const sortedColors = [...colors].sort((a, b) => b.percentage - a.percentage);

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6" fontWeight={600}>
          Color Palette
        </Typography>
        <Chip
          label={`${colors.length} colors`}
          size="small"
          color="primary"
          variant="outlined"
        />
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Click any color to copy its hex code
      </Typography>

      {/* Color grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
          gap: 2,
        }}
      >
        {sortedColors.map((color, index) => (
          <ColorSwatch
            key={`${color.color}-${index}`}
            color={color.color}
            name={color.name}
            percentage={color.percentage}
            index={index}
            onColorClick={onColorClick}
          />
        ))}
      </Box>

      {/* Primary colors summary */}
      {sortedColors.length >= 3 && (
        <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Primary Colors
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {sortedColors.slice(0, 3).map((color, index) => {
              const roles = ['Primary', 'Secondary', 'Accent'];
              return (
                <Chip
                  key={`primary-${index}`}
                  label={roles[index]}
                  sx={{
                    bgcolor: color.color,
                    color: isLightColor(color.color) ? 'rgba(0,0,0,0.87)' : 'white',
                    fontWeight: 500,
                    '& .MuiChip-label': {
                      px: 2,
                    },
                  }}
                />
              );
            })}
          </Box>
        </Box>
      )}
    </Box>
  );
};

// Helper function to determine if a color is light or dark
function isLightColor(color: string): boolean {
  // Remove # if present
  const hex = color.replace('#', '');
  
  // Parse RGB values
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  // Calculate relative luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  
  return luminance > 0.5;
}

export default ColorPaletteDisplay;
