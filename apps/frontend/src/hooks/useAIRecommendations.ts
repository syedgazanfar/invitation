/**
 * AI Recommendations Hook
 * 
 * Provides state management for AI-powered template and style recommendations.
 * Fetches recommendations based on photo analysis results and user preferences.
 * 
 * @example
 * ```tsx
 * const { recommendations, getRecommendations, loading, error } = useAIRecommendations();
 * 
 * // After photo analysis
 * useEffect(() => {
 *   if (photoAnalysisResult) {
 *     getRecommendations({
 *       analysisId: photoAnalysisResult.analysisId,
 *       eventType: 'WEDDING',
 *       planCode: 'PREMIUM'
 *     });
 *   }
 * }, [photoAnalysisResult]);
 * ```
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import {
  getStyleRecommendations as getStyleRecommendationsApi,
  getTemplateRecommendations as getTemplateRecommendationsApi,
  PhotoAnalysisResult,
  StyleRecommendation,
  TemplateRecommendation,
  TemplateRecommendationsResult,
  PersonalizationFactors,
  EventType,
} from '../services/aiApi';

export interface RecommendationParams {
  /** Photo analysis ID from previous analysis */
  analysisId?: string;
  /** Type of event */
  eventType: EventType;
  /** User's plan code for filtering */
  planCode?: string;
  /** Number of recommendations to fetch (default: 5) */
  limit?: number;
}

export interface StyleRecommendationParams {
  /** Photo analysis ID */
  analysisId: string;
  /** Optional event type filter */
  eventType?: EventType;
}

export interface UseAIRecommendationsReturn {
  /** Whether recommendations are being fetched */
  loading: boolean;
  /** Template recommendations */
  templateRecommendations: TemplateRecommendation[];
  /** Style recommendations */
  styleRecommendations: StyleRecommendation[];
  /** Personalization factors from the recommendation engine */
  personalizationFactors: PersonalizationFactors | null;
  /** Error object if fetching failed */
  error: Error | null;
  /** Get template recommendations based on analysis and preferences */
  getTemplateRecommendations: (params: RecommendationParams) => Promise<TemplateRecommendation[] | null>;
  /** Get style recommendations based on photo analysis */
  getStyleRecommendations: (params: StyleRecommendationParams) => Promise<StyleRecommendation[] | null>;
  /** Get recommendations based on a complete photo analysis result */
  getRecommendations: (analysisResult: PhotoAnalysisResult, eventType: EventType, planCode?: string) => Promise<void>;
  /** Select a template by ID */
  selectTemplate: (templateId: string) => void;
  /** Currently selected template ID */
  selectedTemplateId: string | null;
  /** Reset all state */
  reset: () => void;
  /** Clear error state */
  clearError: () => void;
  /** Refresh recommendations with current parameters */
  refresh: () => Promise<void>;
}

/**
 * Hook for AI-powered template and style recommendations
 * 
 * @returns Recommendations state and control functions
 */
export const useAIRecommendations = (): UseAIRecommendationsReturn => {
  const [loading, setLoading] = useState(false);
  const [templateRecommendations, setTemplateRecommendations] = useState<TemplateRecommendation[]>([]);
  const [styleRecommendations, setStyleRecommendations] = useState<StyleRecommendation[]>([]);
  const [personalizationFactors, setPersonalizationFactors] = useState<PersonalizationFactors | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);

  // Store last params for refresh functionality
  const lastParamsRef = useRef<{
    templateParams?: RecommendationParams;
    styleParams?: StyleRecommendationParams;
    analysisResult?: PhotoAnalysisResult;
  }>({});

  // Abort controller for cancellation
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Clean up abort controller on unmount
   */
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  /**
   * Get user-friendly error message
   */
  const getErrorMessage = (err: unknown): string => {
    if (err instanceof Error) {
      if (err.message.includes('Network Error')) {
        return 'Network connection failed. Please check your internet connection and try again.';
      }
      if (err.message.includes('404')) {
        return 'Analysis not found. Please analyze a photo first.';
      }
      return err.message;
    }
    return 'Failed to get recommendations. Please try again.';
  };

  /**
   * Get template recommendations based on analysis and preferences
   * 
   * @param params - Recommendation parameters
   * @returns Promise resolving to template recommendations or null on error
   */
  const getTemplateRecommendations = useCallback(async (
    params: RecommendationParams
  ): Promise<TemplateRecommendation[] | null> => {
    lastParamsRef.current.templateParams = params;

    setLoading(true);
    setError(null);

    // Validate required parameters
    if (!params.eventType) {
      setError(new Error('Event type is required.'));
      setLoading(false);
      return null;
    }

    abortControllerRef.current = new AbortController();

    try {
      const result: TemplateRecommendationsResult = await getTemplateRecommendationsApi({
        analysisId: params.analysisId,
        eventType: params.eventType,
        planCode: params.planCode,
        limit: params.limit,
      });

      setTemplateRecommendations(result.recommendations);
      setPersonalizationFactors(result.personalizationFactors);

      return result.recommendations;
    } catch (err: unknown) {
      const errorMessage = getErrorMessage(err);
      const errorObj = new Error(errorMessage);
      setError(errorObj);
      return null;
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, []);

  /**
   * Get style recommendations based on photo analysis
   * 
   * @param params - Style recommendation parameters
   * @returns Promise resolving to style recommendations or null on error
   */
  const getStyleRecommendations = useCallback(async (
    params: StyleRecommendationParams
  ): Promise<StyleRecommendation[] | null> => {
    lastParamsRef.current.styleParams = params;

    setLoading(true);
    setError(null);

    // Validate required parameters
    if (!params.analysisId) {
      setError(new Error('Analysis ID is required.'));
      setLoading(false);
      return null;
    }

    abortControllerRef.current = new AbortController();

    try {
      const result = await getStyleRecommendationsApi({
        analysisId: params.analysisId,
        eventType: params.eventType,
      });

      setStyleRecommendations(result.recommendations);
      return result.recommendations;
    } catch (err: unknown) {
      const errorMessage = getErrorMessage(err);
      const errorObj = new Error(errorMessage);
      setError(errorObj);
      return null;
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, []);

  /**
   * Get recommendations based on a complete photo analysis result
   * Convenience method that fetches both style and template recommendations
   * 
   * @param analysisResult - The photo analysis result
   * @param eventType - Type of event
   * @param planCode - Optional plan code for filtering
   */
  const getRecommendations = useCallback(async (
    analysisResult: PhotoAnalysisResult,
    eventType: EventType,
    planCode?: string
  ): Promise<void> => {
    lastParamsRef.current.analysisResult = analysisResult;

    setLoading(true);
    setError(null);

    try {
      // Use style recommendations from analysis result if available
      if (analysisResult.styleRecommendations?.length > 0) {
        setStyleRecommendations(analysisResult.styleRecommendations);
      } else if (analysisResult.analysisId) {
        // Fetch style recommendations separately if not included
        await getStyleRecommendations({
          analysisId: analysisResult.analysisId,
          eventType,
        });
      }

      // Always fetch template recommendations
      await getTemplateRecommendations({
        analysisId: analysisResult.analysisId,
        eventType,
        planCode,
        limit: 5,
      });
    } catch (err: unknown) {
      const errorMessage = getErrorMessage(err);
      setError(new Error(errorMessage));
    } finally {
      setLoading(false);
    }
  }, [getStyleRecommendations, getTemplateRecommendations]);

  /**
   * Select a template by ID
   * 
   * @param templateId - The ID of the template to select
   */
  const selectTemplate = useCallback((templateId: string) => {
    setSelectedTemplateId(templateId);
  }, []);

  /**
   * Reset all state to initial values
   */
  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
    setTemplateRecommendations([]);
    setStyleRecommendations([]);
    setPersonalizationFactors(null);
    setError(null);
    setSelectedTemplateId(null);
    lastParamsRef.current = {};
  }, []);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Refresh recommendations with current parameters
   */
  const refresh = useCallback(async (): Promise<void> => {
    const { templateParams, styleParams, analysisResult } = lastParamsRef.current;

    if (analysisResult) {
      // Use the analysis result to refresh
      const eventType = templateParams?.eventType || 'WEDDING';
      const planCode = templateParams?.planCode;
      await getRecommendations(analysisResult, eventType, planCode);
    } else {
      // Refresh individual recommendation types
      const promises: Promise<unknown>[] = [];

      if (templateParams) {
        promises.push(getTemplateRecommendations(templateParams));
      }
      if (styleParams) {
        promises.push(getStyleRecommendations(styleParams));
      }

      if (promises.length === 0) {
        setError(new Error('No previous parameters found. Please fetch recommendations first.'));
        return;
      }

      await Promise.all(promises);
    }
  }, [getRecommendations, getTemplateRecommendations, getStyleRecommendations]);

  return {
    loading,
    templateRecommendations,
    styleRecommendations,
    personalizationFactors,
    error,
    getTemplateRecommendations,
    getStyleRecommendations,
    getRecommendations,
    selectTemplate,
    selectedTemplateId,
    reset,
    clearError,
    refresh,
  };
};

export default useAIRecommendations;
