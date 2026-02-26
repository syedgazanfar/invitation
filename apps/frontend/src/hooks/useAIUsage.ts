/**
 * AI Usage Hook
 * 
 * Provides state management for tracking AI feature usage and limits.
 * Helps monitor quota consumption and check feature availability.
 * 
 * @example
 * ```tsx
 * const { usage, limits, fetchUsage, canUseFeature, checkFeature } = useAIUsage();
 * 
 * // Fetch usage on mount
 * useEffect(() => {
 *   fetchUsage();
 * }, []);
 * 
 * // Check before using a feature
 * const handleAnalyze = async () => {
 *   const canUse = await checkFeature('photo_analysis');
 *   if (canUse) {
 *     // Proceed with photo analysis
 *   }
 * };
 * ```
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import {
  getAIUsageStats,
  getAIUsageLimits,
  getAIUsage,
  checkAIFeatureAvailability,
  UsageStats,
  UsageLimits,
  UsageInfo,
} from '../services/aiApi';

/**
 * Available AI features for usage tracking
 */
export type AIFeature = 
  | 'photo_analysis' 
  | 'message_generation' 
  | 'hashtag_generation' 
  | 'template_recommendations' 
  | 'rsvp_prediction';

export interface FeatureAvailability {
  /** Whether the feature is available for use */
  available: boolean;
  /** Reason if not available */
  reason?: string;
  /** Number of remaining uses */
  remaining?: number;
}

export interface UsageBreakdown {
  /** Feature name */
  feature: AIFeature;
  /** Used count */
  used: number;
  /** Limit count */
  limit: number;
  /** Percentage used (0-100) */
  percentage: number;
  /** Whether the limit has been reached */
  limitReached: boolean;
}

export interface UseAIUsageReturn {
  /** Current usage statistics */
  usage: UsageStats | null;
  /** Usage limits for the user's plan */
  limits: UsageLimits | null;
  /** Whether usage data is being fetched */
  loading: boolean;
  /** Error object if fetching failed */
  error: Error | null;
  /** Feature availability map */
  featureAvailability: Record<AIFeature, FeatureAvailability>;
  /** Fetch current usage statistics */
  fetchUsage: () => Promise<UsageStats | null>;
  /** Fetch usage limits */
  fetchLimits: () => Promise<UsageLimits | null>;
  /** Fetch both usage and limits */
  fetchAll: () => Promise<UsageInfo | null>;
  /** Check if a specific feature can be used */
  canUseFeature: (feature: AIFeature) => boolean;
  /** Check feature availability with server verification */
  checkFeature: (feature: AIFeature) => Promise<boolean>;
  /** Get usage breakdown for a specific feature */
  getFeatureUsage: (feature: AIFeature) => UsageBreakdown | null;
  /** Get usage breakdown for all features */
  getAllFeatureUsage: () => UsageBreakdown[];
  /** Reset all state */
  reset: () => void;
  /** Refresh usage data */
  refresh: () => Promise<void>;
}

/**
 * Feature name mapping for display purposes
 */
export const FEATURE_DISPLAY_NAMES: Record<AIFeature, string> = {
  photo_analysis: 'Photo Analysis',
  message_generation: 'Message Generation',
  hashtag_generation: 'Hashtag Generation',
  template_recommendations: 'Template Recommendations',
  rsvp_prediction: 'RSVP Prediction',
};

/**
 * Hook for tracking AI feature usage and limits
 * 
 * @returns AI usage state and control functions
 */
export const useAIUsage = (): UseAIUsageReturn => {
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [limits, setLimits] = useState<UsageLimits | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [featureAvailability, setFeatureAvailability] = useState<Record<AIFeature, FeatureAvailability>>({
    photo_analysis: { available: false },
    message_generation: { available: false },
    hashtag_generation: { available: false },
    template_recommendations: { available: false },
    rsvp_prediction: { available: false },
  });

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
        return 'Network connection failed. Please check your internet connection.';
      }
      return err.message;
    }
    return 'Failed to fetch usage information. Please try again.';
  };

  /**
   * Update feature availability based on usage and limits
   */
  const updateFeatureAvailability = useCallback((
    currentUsage: UsageStats | null,
    currentLimits: UsageLimits | null
  ): void => {
    if (!currentUsage || !currentLimits) return;

    const availability: Record<AIFeature, FeatureAvailability> = {
      photo_analysis: { available: true },
      message_generation: { available: true },
      hashtag_generation: { available: true },
      template_recommendations: { available: true },
      rsvp_prediction: { available: true },
    };

    // Check photo analysis
    if (!currentLimits.unlimitedAI) {
      const photoRemaining = currentLimits.photoAnalysisLimit - currentUsage.photoAnalysisUsed;
      availability.photo_analysis.remaining = photoRemaining;
      if (photoRemaining <= 0) {
        availability.photo_analysis.available = false;
        availability.photo_analysis.reason = 'Photo analysis limit reached for this billing period.';
      }

      // Check message generation
      const msgRemaining = currentLimits.messageGenerationLimit - currentUsage.messageGenerationUsed;
      availability.message_generation.remaining = msgRemaining;
      if (msgRemaining <= 0) {
        availability.message_generation.available = false;
        availability.message_generation.reason = 'Message generation limit reached for this billing period.';
      }

      // Check hashtag generation
      const tagRemaining = currentLimits.hashtagGenerationLimit - currentUsage.hashtagGenerationUsed;
      availability.hashtag_generation.remaining = tagRemaining;
      if (tagRemaining <= 0) {
        availability.hashtag_generation.available = false;
        availability.hashtag_generation.reason = 'Hashtag generation limit reached for this billing period.';
      }

      // Check template recommendations
      const recRemaining = currentLimits.templateRecommendationsLimit - currentUsage.templateRecommendationsUsed;
      availability.template_recommendations.remaining = recRemaining;
      if (recRemaining <= 0) {
        availability.template_recommendations.available = false;
        availability.template_recommendations.reason = 'Template recommendation limit reached for this billing period.';
      }
    }

    setFeatureAvailability(availability);
  }, []);

  /**
   * Fetch current usage statistics
   * 
   * @returns Promise resolving to usage stats or null on error
   */
  const fetchUsage = useCallback(async (): Promise<UsageStats | null> => {
    setLoading(true);
    setError(null);

    abortControllerRef.current = new AbortController();

    try {
      const stats = await getAIUsageStats();
      setUsage(stats);
      updateFeatureAvailability(stats, limits);
      return stats;
    } catch (err: unknown) {
      const errorMessage = getErrorMessage(err);
      const errorObj = new Error(errorMessage);
      setError(errorObj);
      return null;
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [limits, updateFeatureAvailability]);

  /**
   * Fetch usage limits
   * 
   * @returns Promise resolving to usage limits or null on error
   */
  const fetchLimits = useCallback(async (): Promise<UsageLimits | null> => {
    setLoading(true);
    setError(null);

    abortControllerRef.current = new AbortController();

    try {
      const limitsData = await getAIUsageLimits();
      setLimits(limitsData);
      updateFeatureAvailability(usage, limitsData);
      return limitsData;
    } catch (err: unknown) {
      const errorMessage = getErrorMessage(err);
      const errorObj = new Error(errorMessage);
      setError(errorObj);
      return null;
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [usage, updateFeatureAvailability]);

  /**
   * Fetch both usage and limits
   * 
   * @returns Promise resolving to usage info or null on error
   */
  const fetchAll = useCallback(async (): Promise<UsageInfo | null> => {
    setLoading(true);
    setError(null);

    abortControllerRef.current = new AbortController();

    try {
      const info = await getAIUsage();
      setUsage(info.stats);
      setLimits(info.limits);
      updateFeatureAvailability(info.stats, info.limits);
      return info;
    } catch (err: unknown) {
      const errorMessage = getErrorMessage(err);
      const errorObj = new Error(errorMessage);
      setError(errorObj);
      return null;
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [updateFeatureAvailability]);

  /**
   * Check if a specific feature can be used based on local state
   * 
   * @param feature - The feature to check
   * @returns Whether the feature is available
   */
  const canUseFeature = useCallback((feature: AIFeature): boolean => {
    return featureAvailability[feature]?.available ?? false;
  }, [featureAvailability]);

  /**
   * Check feature availability with server verification
   * 
   * @param feature - The feature to check
   * @returns Promise resolving to whether the feature is available
   */
  const checkFeature = useCallback(async (feature: AIFeature): Promise<boolean> => {
    try {
      const result = await checkAIFeatureAvailability(feature);
      
      // Update local state
      setFeatureAvailability((prev) => ({
        ...prev,
        [feature]: {
          available: result.available,
          reason: result.reason,
          remaining: result.remaining,
        },
      }));

      return result.available;
    } catch (err) {
      // Fall back to local check
      return canUseFeature(feature);
    }
  }, [canUseFeature]);

  /**
   * Get usage breakdown for a specific feature
   * 
   * @param feature - The feature to get usage for
   * @returns Usage breakdown or null if data unavailable
   */
  const getFeatureUsage = useCallback((feature: AIFeature): UsageBreakdown | null => {
    if (!usage || !limits) return null;

    let used = 0;
    let limit = 0;

    switch (feature) {
      case 'photo_analysis':
        used = usage.photoAnalysisUsed;
        limit = limits.photoAnalysisLimit;
        break;
      case 'message_generation':
        used = usage.messageGenerationUsed;
        limit = limits.messageGenerationLimit;
        break;
      case 'hashtag_generation':
        used = usage.hashtagGenerationUsed;
        limit = limits.hashtagGenerationLimit;
        break;
      case 'template_recommendations':
        used = usage.templateRecommendationsUsed;
        limit = limits.templateRecommendationsLimit;
        break;
      case 'rsvp_prediction':
        // RSVP prediction might not have a limit
        used = 0;
        limit = Infinity;
        break;
      default:
        return null;
    }

    const percentage = limit === Infinity ? 0 : (used / limit) * 100;

    return {
      feature,
      used,
      limit,
      percentage,
      limitReached: limit !== Infinity && used >= limit,
    };
  }, [usage, limits]);

  /**
   * Get usage breakdown for all features
   * 
   * @returns Array of usage breakdowns for all features
   */
  const getAllFeatureUsage = useCallback((): UsageBreakdown[] => {
    const features: AIFeature[] = [
      'photo_analysis',
      'message_generation',
      'hashtag_generation',
      'template_recommendations',
      'rsvp_prediction',
    ];

    return features
      .map((feature) => getFeatureUsage(feature))
      .filter((breakdown): breakdown is UsageBreakdown => breakdown !== null);
  }, [getFeatureUsage]);

  /**
   * Reset all state to initial values
   */
  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setUsage(null);
    setLimits(null);
    setLoading(false);
    setError(null);
    setFeatureAvailability({
      photo_analysis: { available: false },
      message_generation: { available: false },
      hashtag_generation: { available: false },
      template_recommendations: { available: false },
      rsvp_prediction: { available: false },
    });
  }, []);

  /**
   * Refresh usage data
   */
  const refresh = useCallback(async (): Promise<void> => {
    await fetchAll();
  }, [fetchAll]);

  return {
    usage,
    limits,
    loading,
    error,
    featureAvailability,
    fetchUsage,
    fetchLimits,
    fetchAll,
    canUseFeature,
    checkFeature,
    getFeatureUsage,
    getAllFeatureUsage,
    reset,
    refresh,
  };
};

export default useAIUsage;
