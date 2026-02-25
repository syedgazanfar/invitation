/**
 * Photo Analysis Hook
 * 
 * Provides state management and progress tracking for AI photo analysis.
 * Handles the upload, analysis, and error states with a smooth progress animation.
 * 
 * @example
 * ```tsx
 * const { analyzePhoto, result, loading, progress, error, reset } = usePhotoAnalysis();
 * 
 * const handleUpload = async (file: File) => {
 *   const result = await analyzePhoto(file, 'WEDDING');
 *   if (result) {
 *     console.log('Colors:', result.primaryColors);
 *   }
 * };
 * ```
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import {
  analyzePhoto as analyzePhotoApi,
  extractColors as extractColorsApi,
  detectMood as detectMoodApi,
  PhotoAnalysisRequest,
  PhotoAnalysisResult,
  ColorExtractionResult,
  MoodAnalysis,
  EventType,
} from '../services/aiApi';

export interface UsePhotoAnalysisReturn {
  /** Whether analysis is in progress */
  loading: boolean;
  /** Progress percentage (0-100) */
  progress: number;
  /** Analysis result after successful completion */
  result: PhotoAnalysisResult | null;
  /** Error object if analysis failed */
  error: Error | null;
  /** Analyze a photo file */
  analyzePhoto: (file: File, eventType: EventType, eventId?: number) => Promise<PhotoAnalysisResult | null>;
  /** Extract colors only from a photo */
  extractColors: (file: File) => Promise<ColorExtractionResult | null>;
  /** Detect mood only from a photo */
  detectMood: (file: File) => Promise<MoodAnalysis | null>;
  /** Reset all state */
  reset: () => void;
  /** Cancel ongoing analysis */
  cancel: () => void;
}

/**
 * Progress animation configuration
 */
const PROGRESS_CONFIG = {
  /** Initial progress value */
  initial: 0,
  /** Maximum progress during processing (leaves room for completion) */
  maxDuringProcessing: 90,
  /** Progress increment per tick */
  increment: 2,
  /** Tick interval in milliseconds */
  tickInterval: 100,
  /** Progress value to set on error */
  onError: 0,
  /** Progress value to set on success */
  onSuccess: 100,
};

/**
 * Hook for AI-powered photo analysis
 * 
 * @returns Photo analysis state and control functions
 */
export const usePhotoAnalysis = (): UsePhotoAnalysisReturn => {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<PhotoAnalysisResult | null>(null);
  const [error, setError] = useState<Error | null>(null);
  
  // Use refs to track interval and abort controller for cleanup
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Clear progress interval safely
   */
  const clearProgressInterval = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
  }, []);

  /**
   * Start progress animation
   */
  const startProgressAnimation = useCallback(() => {
    clearProgressInterval();
    setProgress(PROGRESS_CONFIG.initial);
    
    progressIntervalRef.current = setInterval(() => {
      setProgress((prev) => {
        // Slow down progress as it gets closer to max
        const remaining = PROGRESS_CONFIG.maxDuringProcessing - prev;
        const increment = Math.max(1, Math.min(PROGRESS_CONFIG.increment, remaining / 5));
        return Math.min(prev + increment, PROGRESS_CONFIG.maxDuringProcessing);
      });
    }, PROGRESS_CONFIG.tickInterval);
  }, [clearProgressInterval]);

  /**
   * Stop progress animation and set final value
   */
  const stopProgressAnimation = useCallback((finalValue: number) => {
    clearProgressInterval();
    setProgress(finalValue);
  }, [clearProgressInterval]);

  /**
   * Reset all state to initial values
   */
  const reset = useCallback(() => {
    clearProgressInterval();
    setLoading(false);
    setProgress(0);
    setResult(null);
    setError(null);
    abortControllerRef.current = null;
  }, [clearProgressInterval]);

  /**
   * Cancel ongoing analysis
   */
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    clearProgressInterval();
    setLoading(false);
    setProgress(0);
  }, [clearProgressInterval]);

  /**
   * Clean up on unmount
   */
  useEffect(() => {
    return () => {
      clearProgressInterval();
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [clearProgressInterval]);

  /**
   * Get user-friendly error message
   */
  const getErrorMessage = (err: unknown): string => {
    if (err instanceof Error) {
      // Handle specific error types
      if (err.message.includes('Network Error')) {
        return 'Network connection failed. Please check your internet connection and try again.';
      }
      if (err.message.includes('timeout')) {
        return 'Photo analysis took too long. Please try with a smaller image or try again later.';
      }
      if (err.message.includes('413')) {
        return 'Image file is too large. Please upload an image smaller than 10MB.';
      }
      if (err.message.includes('415')) {
        return 'Unsupported image format. Please upload JPG, PNG, or WebP images only.';
      }
      return err.message;
    }
    return 'An unexpected error occurred during photo analysis. Please try again.';
  };

  /**
   * Analyze a photo using AI
   * 
   * @param file - The photo file to analyze
   * @param eventType - Type of event for context-aware analysis
   * @param eventId - Optional event ID for saving results
   * @returns Promise resolving to analysis result or null on error
   */
  const analyzePhoto = useCallback(async (
    file: File,
    eventType: EventType,
    eventId?: number
  ): Promise<PhotoAnalysisResult | null> => {
    // Reset state before starting
    setLoading(true);
    setError(null);
    setResult(null);
    
    // Validate file
    if (!file) {
      setError(new Error('Please select a photo to analyze.'));
      setLoading(false);
      return null;
    }

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setError(new Error('Please upload a valid image file (JPG, PNG, or WebP).'));
      setLoading(false);
      return null;
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setError(new Error('Image file is too large. Please upload an image smaller than 10MB.'));
      setLoading(false);
      return null;
    }

    // Create abort controller for cancellation support
    abortControllerRef.current = new AbortController();
    
    // Start progress animation
    startProgressAnimation();

    try {
      const request: PhotoAnalysisRequest = {
        photo: file,
        eventType,
        eventId,
      };

      const analysisResult = await analyzePhotoApi(request);
      
      // Complete progress animation
      stopProgressAnimation(PROGRESS_CONFIG.onSuccess);
      setResult(analysisResult);
      return analysisResult;
    } catch (err: unknown) {
      // Don't update state if request was cancelled
      if (err instanceof Error && err.name === 'CanceledError') {
        return null;
      }

      stopProgressAnimation(PROGRESS_CONFIG.onError);
      const errorMessage = getErrorMessage(err);
      const errorObj = new Error(errorMessage);
      setError(errorObj);
      return null;
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [startProgressAnimation, stopProgressAnimation]);

  /**
   * Extract colors only from a photo
   * 
   * @param file - The photo file to analyze
   * @returns Promise resolving to color extraction result or null on error
   */
  const extractColors = useCallback(async (
    file: File
  ): Promise<ColorExtractionResult | null> => {
    setLoading(true);
    setError(null);

    try {
      const result = await extractColorsApi(file);
      return result;
    } catch (err: unknown) {
      const errorMessage = getErrorMessage(err);
      setError(new Error(errorMessage));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Detect mood only from a photo
   * 
   * @param file - The photo file to analyze
   * @returns Promise resolving to mood analysis or null on error
   */
  const detectMood = useCallback(async (
    file: File
  ): Promise<MoodAnalysis | null> => {
    setLoading(true);
    setError(null);

    try {
      const result = await detectMoodApi(file);
      return result.mood;
    } catch (err: unknown) {
      const errorMessage = getErrorMessage(err);
      setError(new Error(errorMessage));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    progress,
    result,
    error,
    analyzePhoto,
    extractColors,
    detectMood,
    reset,
    cancel,
  };
};

export default usePhotoAnalysis;
