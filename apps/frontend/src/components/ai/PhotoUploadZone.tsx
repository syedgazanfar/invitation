/**
 * Photo Upload Zone Component
 * 
 * Provides drag-and-drop photo upload with file validation, preview,
 * and progress indication for the AI photo analysis feature.
 */
import React, { useCallback, useState, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  LinearProgress,
  IconButton,
  Fade,
  Alert,
} from '@mui/material';
import {
  CloudUpload,
  Image as ImageIcon,
  Close,
  CheckCircle,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

export interface PhotoUploadZoneProps {
  /** Callback when a valid photo is selected */
  onPhotoSelect: (file: File) => void;
  /** Whether the component is in loading state */
  isLoading?: boolean;
  /** Accepted MIME types */
  acceptedTypes?: string[];
  /** Maximum file size in MB */
  maxSizeMB?: number;
}

const DEFAULT_ACCEPTED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
const DEFAULT_MAX_SIZE_MB = 10;

export const PhotoUploadZone: React.FC<PhotoUploadZoneProps> = ({
  onPhotoSelect,
  isLoading = false,
  acceptedTypes = DEFAULT_ACCEPTED_TYPES,
  maxSizeMB = DEFAULT_MAX_SIZE_MB,
}) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  const validateFile = (file: File): string | null => {
    if (!acceptedTypes.includes(file.type)) {
      return `Invalid file type. Please upload ${acceptedTypes.map(t => t.replace('image/', '').toUpperCase()).join(', ')} images only.`;
    }
    if (file.size > maxSizeBytes) {
      return `File too large. Maximum size is ${maxSizeMB}MB.`;
    }
    return null;
  };

  const createPreview = (file: File) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleFile = useCallback((file: File) => {
    setError(null);
    const validationError = validateFile(file);
    
    if (validationError) {
      setError(validationError);
      return;
    }

    setSelectedFile(file);
    createPreview(file);
    onPhotoSelect(file);
  }, [acceptedTypes, maxSizeBytes, maxSizeMB, onPhotoSelect]);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isLoading) {
      setIsDragActive(true);
    }
  }, [isLoading]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (isLoading) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile, isLoading]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  const handleClick = () => {
    if (!isLoading && inputRef.current) {
      inputRef.current.click();
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreview(null);
    setSelectedFile(null);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const getAcceptedExtensions = () => {
    return acceptedTypes.map(type => `.${type.split('/')[1]}`).join(',');
  };

  return (
    <Box sx={{ width: '100%' }}>
      <input
        ref={inputRef}
        type="file"
        accept={acceptedTypes.join(',')}
        onChange={handleInputChange}
        style={{ display: 'none' }}
        aria-label="Upload photo"
      />

      <AnimatePresence mode="wait">
        {preview ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            <Paper
              elevation={2}
              sx={{
                position: 'relative',
                borderRadius: 3,
                overflow: 'hidden',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.7 : 1,
              }}
              onClick={handleClick}
            >
              <Box
                component="img"
                src={preview}
                alt="Selected photo preview"
                sx={{
                  width: '100%',
                  height: 250,
                  objectFit: 'cover',
                }}
              />
              
              {/* Overlay with file info */}
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
                  p: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Box sx={{ color: 'white' }}>
                  <Typography variant="body2" fontWeight={500}>
                    {selectedFile?.name}
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.8 }}>
                    {(selectedFile!.size / 1024 / 1024).toFixed(2)} MB
                  </Typography>
                </Box>
                
                {!isLoading && (
                  <IconButton
                    size="small"
                    onClick={handleClear}
                    sx={{
                      color: 'white',
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
                    }}
                  >
                    <Close fontSize="small" />
                  </IconButton>
                )}
              </Box>

              {/* Success indicator */}
              {isLoading && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 16,
                    right: 16,
                    bgcolor: 'success.main',
                    borderRadius: '50%',
                    p: 0.5,
                  }}
                >
                  <CheckCircle sx={{ color: 'white', fontSize: 20 }} />
                </Box>
              )}
            </Paper>
          </motion.div>
        ) : (
          <motion.div
            key="upload"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            <Paper
              elevation={isDragActive ? 4 : 1}
              onClick={handleClick}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              sx={{
                border: 2,
                borderStyle: 'dashed',
                borderColor: isDragActive ? 'primary.main' : error ? 'error.main' : 'divider',
                borderRadius: 3,
                p: 4,
                textAlign: 'center',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                backgroundColor: isDragActive ? 'rgba(166, 30, 42, 0.04)' : 'background.paper',
                transition: 'all 0.2s ease',
                '&:hover': {
                  borderColor: isLoading ? 'divider' : 'primary.main',
                  backgroundColor: isLoading ? 'background.paper' : 'rgba(166, 30, 42, 0.02)',
                },
              }}
            >
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  bgcolor: 'rgba(166, 30, 42, 0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                {isDragActive ? (
                  <ImageIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                ) : (
                  <CloudUpload sx={{ fontSize: 40, color: 'primary.main' }} />
                )}
              </Box>

              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                {isDragActive ? 'Drop your photo here' : 'Upload a photo'}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Drag and drop or click to browse
              </Typography>
              
              <Typography variant="caption" color="text.secondary" display="block">
                Supported: {acceptedTypes.map(t => t.replace('image/', '').toUpperCase()).join(', ')} • Max {maxSizeMB}MB
              </Typography>
            </Paper>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error message */}
      <Fade in={!!error}>
        <Box sx={{ mt: 2 }}>
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </Box>
      </Fade>

      {/* Loading progress */}
      {isLoading && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress 
            sx={{
              height: 6,
              borderRadius: 3,
              bgcolor: 'rgba(166, 30, 42, 0.1)',
              '& .MuiLinearProgress-bar': {
                bgcolor: 'primary.main',
              },
            }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block', textAlign: 'center' }}>
            Processing your photo...
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default PhotoUploadZone;
