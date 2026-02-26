/**
 * Message Generator Component
 * 
 * Provides an interface for AI-powered invitation message generation
 * with customizable tone, style options, and message selection.
 */
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Chip,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  IconButton,
  Tooltip,
  CircularProgress,
  Fade,
  Skeleton,
} from '@mui/material';
import {
  AutoAwesome,
  Refresh,
  ContentCopy,
  Check,
  Send,
  Lightbulb,
  Message,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { GeneratedMessage, MessageTone } from '../../services/aiApi';
import { useMessageGenerator } from '../../hooks';

export interface MessageGeneratorProps {
  /** Context for message generation */
  context: {
    brideName: string;
    groomName: string;
    eventType: string;
    details?: string;
  };
  /** Callback when a message is selected */
  onMessageSelect: (message: string) => void;
  /** Optional callback when messages are generated */
  onMessagesGenerated?: (messages: GeneratedMessage[]) => void;
}

type MessageStyle = 'traditional' | 'warm' | 'fun';

interface MessageCardProps {
  message: GeneratedMessage;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
}

const MessageCard: React.FC<MessageCardProps> = ({
  message,
  index,
  isSelected,
  onSelect,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(message.message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getStyleIcon = (style: string) => {
    if (style.includes('traditional')) return '🏛️';
    if (style.includes('fun') || style.includes('casual')) return '🎉';
    if (style.includes('warm') || style.includes('poetic')) return '💕';
    return '✨';
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1, duration: 0.3 }}
    >
      <Paper
        elevation={isSelected ? 4 : 1}
        onClick={onSelect}
        sx={{
          p: 3,
          borderRadius: 3,
          cursor: 'pointer',
          border: 2,
          borderColor: isSelected ? 'primary.main' : 'transparent',
          position: 'relative',
          transition: 'all 0.2s ease',
          '&:hover': {
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)',
          },
        }}
      >
        {/* Selection indicator */}
        {isSelected && (
          <Box
            sx={{
              position: 'absolute',
              top: -1,
              right: -1,
              bgcolor: 'primary.main',
              color: 'white',
              px: 1.5,
              py: 0.5,
              borderBottomLeftRadius: 12,
              borderTopRightRadius: 11,
            }}
          >
            <Typography variant="caption" fontWeight={600}>
              Selected
            </Typography>
          </Box>
        )}

        {/* Header with style badge */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Chip
            icon={<span style={{ fontSize: 16 }}>{getStyleIcon(message.style)}</span>}
            label={message.style.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            size="small"
            color={isSelected ? 'primary' : 'default'}
            variant={isSelected ? 'filled' : 'outlined'}
          />
          <Tooltip title={copied ? 'Copied!' : 'Copy to clipboard'}>
            <IconButton
              size="small"
              onClick={handleCopy}
              color={copied ? 'success' : 'default'}
            >
              {copied ? <Check fontSize="small" /> : <ContentCopy fontSize="small" />}
            </IconButton>
          </Tooltip>
        </Box>

        {/* Message content */}
        <Typography
          variant="body1"
          sx={{
            lineHeight: 1.8,
            fontStyle: message.style.includes('poetic') ? 'italic' : 'normal',
            color: 'text.primary',
          }}
        >
          {message.message}
        </Typography>

        {/* Word count */}
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Typography variant="caption" color="text.secondary">
            {message.wordCount} words
          </Typography>
        </Box>
      </Paper>
    </motion.div>
  );
};

export const MessageGenerator: React.FC<MessageGeneratorProps> = ({
  context,
  onMessageSelect,
  onMessagesGenerated,
}) => {
  const {
    loading,
    messages,
    selectedMessage,
    error,
    generateMessages,
    regenerate,
    selectMessage,
    clearError,
  } = useMessageGenerator();

  const [messageStyle, setMessageStyle] = useState<MessageStyle>('warm');
  const [details, setDetails] = useState(context.details || '');
  const [hasGenerated, setHasGenerated] = useState(false);

  const handleStyleChange = (
    event: React.MouseEvent<HTMLElement>,
    newStyle: MessageStyle,
  ) => {
    if (newStyle !== null) {
      setMessageStyle(newStyle);
    }
  };

  const handleGenerate = async () => {
    clearError();
    
    const toneMap: Record<MessageStyle, MessageTone> = {
      traditional: 'traditional',
      warm: 'warm',
      fun: 'funny',
    };

    const result = await generateMessages({
      brideName: context.brideName,
      groomName: context.groomName,
      eventType: context.eventType,
      tone: toneMap[messageStyle],
      details: details,
    });

    if (result) {
      setHasGenerated(true);
      onMessagesGenerated?.(result);
    }
  };

  const handleRegenerate = async () => {
    const result = await regenerate();
    if (result) {
      onMessagesGenerated?.(result);
    }
  };

  const handleSelectMessage = (message: string) => {
    selectMessage(message);
    onMessageSelect(message);
  };

  const getStyleDescription = (style: MessageStyle): string => {
    switch (style) {
      case 'traditional':
        return 'Classic, formal language with timeless elegance';
      case 'warm':
        return 'Heartfelt and personal with emotional warmth';
      case 'fun':
        return 'Playful and light-hearted with personality';
      default:
        return '';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <AutoAwesome color="primary" />
        <Typography variant="h6" fontWeight={600}>
          AI Message Generator
        </Typography>
      </Box>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Generate personalized invitation messages using AI
      </Typography>

      {/* Error alert */}
      <Fade in={!!error}>
        <Box sx={{ mb: 2 }}>
          <Alert severity="error" onClose={clearError}>
            {error?.message}
          </Alert>
        </Box>
      </Fade>

      {/* Generation form */}
      <Paper elevation={1} sx={{ p: 3, borderRadius: 3, mb: 3 }}>
        {/* Couple info summary */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            Generating for:
          </Typography>
          <Typography variant="subtitle1" fontWeight={600}>
            {context.brideName} & {context.groomName}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {context.eventType}
          </Typography>
        </Box>

        {/* Style selector */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Choose a Tone
          </Typography>
          <ToggleButtonGroup
            value={messageStyle}
            exclusive
            onChange={handleStyleChange}
            fullWidth
            sx={{ mb: 1 }}
          >
            <ToggleButton value="traditional">
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" fontWeight={600}>🏛️ Traditional</Typography>
              </Box>
            </ToggleButton>
            <ToggleButton value="warm">
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" fontWeight={600}>💕 Warm</Typography>
              </Box>
            </ToggleButton>
            <ToggleButton value="fun">
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" fontWeight={600}>🎉 Fun</Typography>
              </Box>
            </ToggleButton>
          </ToggleButtonGroup>
          <Typography variant="caption" color="text.secondary">
            {getStyleDescription(messageStyle)}
          </Typography>
        </Box>

        {/* Additional details */}
        <TextField
          fullWidth
          multiline
          rows={2}
          label="Additional Details (Optional)"
          placeholder="E.g., childhood sweethearts, destination wedding, etc."
          value={details}
          onChange={(e) => setDetails(e.target.value)}
          sx={{ mb: 2 }}
        />

        {/* Generate button */}
        <Button
          variant="contained"
          fullWidth
          size="large"
          onClick={handleGenerate}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <AutoAwesome />}
          sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}
        >
          {loading ? 'Generating...' : hasGenerated ? 'Generate New Messages' : 'Generate Messages'}
        </Button>
      </Paper>

      {/* Generated messages */}
      <AnimatePresence>
        {messages.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="subtitle1" fontWeight={600}>
                Generated Messages
              </Typography>
              <Button
                size="small"
                startIcon={<Refresh />}
                onClick={handleRegenerate}
                disabled={loading}
              >
                Regenerate
              </Button>
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {messages.map((message, index) => (
                <MessageCard
                  key={`${message.style}-${index}`}
                  message={message}
                  index={index}
                  isSelected={selectedMessage === message.message}
                  onSelect={() => handleSelectMessage(message.message)}
                />
              ))}
            </Box>

            {/* Apply button */}
            {selectedMessage && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Button
                  variant="contained"
                  fullWidth
                  size="large"
                  sx={{ mt: 3, borderRadius: 2 }}
                  startIcon={<Send />}
                  onClick={() => onMessageSelect(selectedMessage)}
                >
                  Use Selected Message
                </Button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tips section */}
      {!hasGenerated && !loading && (
        <Paper
          elevation={0}
          sx={{
            p: 2,
            mt: 3,
            bgcolor: 'rgba(166, 30, 42, 0.04)',
            borderRadius: 2,
            border: '1px dashed',
            borderColor: 'rgba(166, 30, 42, 0.2)',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
            <Lightbulb color="primary" fontSize="small" />
            <Box>
              <Typography variant="caption" fontWeight={600} display="block" color="primary">
                Tip
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Adding details about how you met or your relationship story helps create more personalized messages.
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default MessageGenerator;
