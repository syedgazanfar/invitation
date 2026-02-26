/**
 * AI API Service
 * 
 * Provides methods for interacting with AI-powered features including
 * photo analysis, message generation, template recommendations, and usage tracking.
 */
import api from './api';
import { apiService } from './api';

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Event types supported for AI analysis
 */
export type EventType = 'WEDDING' | 'BIRTHDAY' | 'PARTY' | 'FESTIVAL' | 'CORPORATE';

/**
 * Message tone options
 */
export type MessageTone = 'warm' | 'formal' | 'casual' | 'funny' | 'poetic' | 'traditional';

/**
 * Request payload for photo analysis
 */
export interface PhotoAnalysisRequest {
  /** The photo file to analyze */
  photo: File;
  /** Type of event for context-aware analysis */
  eventType: EventType;
  /** Optional event ID for saving analysis results */
  eventId?: number;
  /** Optional language for suggestions (default: 'en') */
  language?: string;
}

/**
 * Color information extracted from a photo
 */
export interface ExtractedColor {
  /** Hex color code (e.g., '#A61E2A') */
  color: string;
  /** Human-readable color name */
  name: string;
  /** Percentage of image covered by this color (0-100) */
  percentage: number;
  /** Role of the color in the palette (primary, secondary, accent) */
  role?: 'primary' | 'secondary' | 'accent';
}

/**
 * Mood analysis result
 */
export interface MoodAnalysis {
  /** Primary detected mood */
  primary: string;
  /** Confidence score (0-1) */
  confidence: number;
  /** Secondary moods detected */
  secondary: string[];
  /** All mood scores for reference */
  allScores?: Record<string, number>;
}

/**
 * Style recommendation from photo analysis
 */
export interface StyleRecommendation {
  /** Style name (e.g., 'Romantic Elegance') */
  style: string;
  /** Confidence score (0-1) */
  confidence: number;
  /** Recommended color palette */
  colorPalette: string[];
  /** Matching template IDs */
  matchingTemplates: string[];
  /** Human-readable description */
  description: string;
}

/**
 * AI suggestions for various aspects
 */
export interface AISuggestions {
  /** Recommended message tone */
  messageTone: string;
  /** Generated hashtag ideas */
  hashtagIdeas: string[];
  /** Recommended music mood */
  musicMood: string;
}

/**
 * Complete photo analysis result
 */
export interface PhotoAnalysisResult {
  /** Unique analysis ID for reference */
  analysisId: string;
  /** Primary colors extracted from the photo */
  primaryColors: ExtractedColor[];
  /** Mood analysis result */
  mood: MoodAnalysis;
  /** Style recommendations based on photo */
  styleRecommendations: StyleRecommendation[];
  /** Additional AI suggestions */
  aiSuggestions: AISuggestions;
}

/**
 * Request payload for message generation
 */
export interface MessageGenerationRequest {
  /** Bride's name */
  brideName: string;
  /** Groom's name */
  groomName: string;
  /** Event type */
  eventType: string;
  /** Wedding/event style (e.g., 'traditional_indian', 'modern') */
  style?: string;
  /** Cultural context (e.g., 'north_indian', 'western') */
  culture?: string;
  /** Desired tone for the message */
  tone?: MessageTone;
  /** Additional details about the couple/story */
  details?: string;
  /** Wedding date (optional) */
  weddingDate?: string;
}

/**
 * Generated message option
 */
export interface GeneratedMessage {
  /** Style/type of message (e.g., 'traditional_formal') */
  style: string;
  /** The generated message text */
  message: string;
  /** Word count of the message */
  wordCount: number;
}

/**
 * Message generation result
 */
export interface MessageGenerationResult {
  /** Generated message options */
  options: GeneratedMessage[];
  /** Number of tokens used for generation */
  tokensUsed: number;
  /** Time taken for generation in milliseconds */
  generationTimeMs: number;
}

/**
 * Template recommendation from AI
 */
export interface TemplateRecommendation {
  /** Template ID */
  templateId: string;
  /** Template name */
  name: string;
  /** Match score (0-1) */
  matchScore: number;
  /** Reasons for recommendation */
  matchReasons: string[];
  /** Preview URL */
  previewUrl: string;
  /** Thumbnail URL */
  thumbnail: string;
  /** Template description */
  description?: string;
  /** Animation type */
  animationType?: string;
}

/**
 * Personalization factors for recommendations
 */
export interface PersonalizationFactors {
  /** Color match score (0-1) */
  colorMatch: number;
  /** Mood match score (0-1) */
  moodMatch: number;
  /** Popularity score (0-1) */
  popularity: number;
}

/**
 * Template recommendations result
 */
export interface TemplateRecommendationsResult {
  /** List of recommended templates */
  recommendations: TemplateRecommendation[];
  /** Personalization factors */
  personalizationFactors: PersonalizationFactors;
}

/**
 * Color palette suggestion
 */
export interface ColorPalette {
  /** Palette name */
  name: string;
  /** Colors in the palette */
  colors: string[];
  /** Description of the palette */
  description: string;
  /** Suitable event types */
  suitableFor?: string[];
}

/**
 * Color extraction result
 */
export interface ColorExtractionResult {
  /** Extracted colors from the photo */
  extractedColors: ExtractedColor[];
  /** Suggested color palettes */
  suggestedPalettes: ColorPalette[];
}

/**
 * Hashtag generation result
 */
export interface HashtagGenerationResult {
  /** Classic style hashtags */
  classic: string[];
  /** Fun style hashtags */
  fun: string[];
  /** Trending style hashtags */
  trending: string[];
  /** Personalized hashtags with names */
  personalized: string[];
}

/**
 * RSVP prediction result
 */
export interface RSVPPrediction {
  /** Probability the guest will attend (0-1) */
  willAttendProbability: number;
  /** Confidence level of prediction */
  confidence: 'high' | 'medium' | 'low';
  /** Expected response time in days */
  expectedResponseTimeDays: number;
}

/**
 * AI feature usage statistics
 */
export interface UsageStats {
  /** Photo analyses used this month */
  photoAnalysisUsed: number;
  /** Message generations used this month */
  messageGenerationUsed: number;
  /** Hashtag generations used this month */
  hashtagGenerationUsed: number;
  /** Template recommendations used this month */
  templateRecommendationsUsed: number;
  /** Total AI API calls made */
  totalApiCalls: number;
  /** Current billing period start */
  billingPeriodStart: string;
  /** Current billing period end */
  billingPeriodEnd: string;
}

/**
 * AI feature usage limits
 */
export interface UsageLimits {
  /** Maximum photo analyses allowed per month */
  photoAnalysisLimit: number;
  /** Maximum message generations allowed per month */
  messageGenerationLimit: number;
  /** Maximum hashtag generations allowed per month */
  hashtagGenerationLimit: number;
  /** Maximum template recommendations allowed per month */
  templateRecommendationsLimit: number;
  /** User's plan tier */
  planTier: 'BASIC' | 'PREMIUM' | 'LUXURY';
  /** Whether unlimited AI is enabled */
  unlimitedAI: boolean;
}

/**
 * Combined usage information
 */
export interface UsageInfo {
  /** Current usage statistics */
  stats: UsageStats;
  /** Usage limits for the user's plan */
  limits: UsageLimits;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Analyze a photo to extract colors, mood, and style recommendations
 * 
 * @param data - Photo analysis request data
 * @returns Promise with photo analysis results
 * @throws Error if analysis fails
 */
export const analyzePhoto = async (data: PhotoAnalysisRequest): Promise<PhotoAnalysisResult> => {
  const formData = new FormData();
  formData.append('photo', data.photo);
  formData.append('event_type', data.eventType);
  
  if (data.eventId) {
    formData.append('event_id', data.eventId.toString());
  }
  if (data.language) {
    formData.append('language', data.language);
  }

  const response = await api.post('/ai/analyze-photo/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000, // 60 second timeout for image processing
  });

  return response.data.data;
};

/**
 * Extract dominant colors from a photo
 * 
 * @param photo - The photo file to analyze
 * @returns Promise with extracted colors
 */
export const extractColors = async (photo: File): Promise<ColorExtractionResult> => {
  const formData = new FormData();
  formData.append('photo', photo);

  const response = await api.post('/ai/extract-colors/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 30000,
  });

  return response.data.data;
};

/**
 * Detect mood from a photo
 * 
 * @param photo - The photo file to analyze
 * @returns Promise with mood analysis
 */
export const detectMood = async (photo: File): Promise<{ mood: MoodAnalysis }> => {
  const formData = new FormData();
  formData.append('photo', photo);

  const response = await api.post('/ai/detect-mood/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 30000,
  });

  return response.data.data;
};

/**
 * Generate invitation messages based on couple details
 * 
 * @param data - Message generation request parameters
 * @returns Promise with generated message options
 */
export const generateMessages = async (
  data: MessageGenerationRequest
): Promise<MessageGenerationResult> => {
  const response = await apiService.post<MessageGenerationResult>('/ai/generate-message/', {
    bride_name: data.brideName,
    groom_name: data.groomName,
    event_type: data.eventType,
    style: data.style,
    culture: data.culture,
    tone: data.tone,
    details: data.details,
    wedding_date: data.weddingDate,
  });

  return response.data!;
};

/**
 * Get style recommendations based on photo analysis
 * 
 * @param analysisId - The photo analysis ID
 * @param eventType - Optional event type filter
 * @returns Promise with style recommendations
 */
export const getStyleRecommendations = async (params: {
  analysisId: string;
  eventType?: EventType;
}): Promise<{ recommendations: StyleRecommendation[] }> => {
  const response = await apiService.post<{ recommendations: StyleRecommendation[] }>(
    '/ai/style-recommendations/',
    {
      analysis_id: params.analysisId,
      event_type: params.eventType,
    }
  );

  return response.data!;
};

/**
 * Get template recommendations based on photo analysis and user preferences
 * 
 * @param params - Recommendation parameters
 * @returns Promise with template recommendations
 */
export const getTemplateRecommendations = async (params: {
  analysisId?: string;
  eventType: EventType;
  planCode?: string;
  limit?: number;
}): Promise<TemplateRecommendationsResult> => {
  const response = await apiService.get<TemplateRecommendationsResult>(
    '/ai/template-recommendations/',
    {
      analysis_id: params.analysisId,
      event_type: params.eventType,
      plan_code: params.planCode,
      limit: params.limit || 5,
    }
  );

  return response.data!;
};

/**
 * Generate creative hashtags based on couple names
 * 
 * @param params - Hashtag generation parameters
 * @returns Promise with generated hashtags
 */
export const generateHashtags = async (params: {
  brideName: string;
  groomName: string;
  weddingDate?: string;
  style?: 'classic' | 'fun' | 'trending' | 'all';
  count?: number;
}): Promise<HashtagGenerationResult> => {
  const response = await apiService.get<HashtagGenerationResult>('/ai/generate-hashtags/', {
    bride: params.brideName,
    groom: params.groomName,
    date: params.weddingDate,
    style: params.style || 'all',
    count: params.count || 10,
  });

  return response.data!;
};

/**
 * Predict RSVP likelihood for a guest
 * 
 * @param guestId - The guest ID
 * @param eventId - The event ID
 * @returns Promise with RSVP prediction
 */
export const predictRSVP = async (guestId: string, eventId: string): Promise<RSVPPrediction> => {
  const response = await apiService.post<RSVPPrediction>('/ai/predict-rsvp/', {
    guest_id: guestId,
    event_id: eventId,
  });

  return response.data!;
};

/**
 * Get AI feature usage statistics for the current user
 * 
 * @returns Promise with usage statistics
 */
export const getAIUsageStats = async (): Promise<UsageStats> => {
  const response = await apiService.get<UsageStats>('/ai/usage/stats/');
  return response.data!;
};

/**
 * Get AI feature usage limits for the current user's plan
 * 
 * @returns Promise with usage limits
 */
export const getAIUsageLimits = async (): Promise<UsageLimits> => {
  const response = await apiService.get<UsageLimits>('/ai/usage/limits/');
  return response.data!;
};

/**
 * Get combined AI usage information (stats and limits)
 * 
 * @returns Promise with complete usage information
 */
export const getAIUsage = async (): Promise<UsageInfo> => {
  const response = await apiService.get<UsageInfo>('/ai/usage/');
  return response.data!;
};

/**
 * Check if a specific AI feature is available for use
 * 
 * @param feature - The feature to check ('photo_analysis', 'message_generation', etc.)
 * @returns Promise with availability status
 */
export const checkAIFeatureAvailability = async (feature: string): Promise<{
  available: boolean;
  reason?: string;
  remaining?: number;
}> => {
  const response = await apiService.get<{
    available: boolean;
    reason?: string;
    remaining?: number;
  }>('/ai/check-availability/', { feature });

  return response.data!;
};

// ============================================================================
// AI API Service Object
// ============================================================================

/**
 * AI API service - organized collection of all AI-related API methods
 */
export const aiApi = {
  analyzePhoto,
  extractColors,
  detectMood,
  generateMessages,
  getStyleRecommendations,
  getTemplateRecommendations,
  generateHashtags,
  predictRSVP,
  getAIUsageStats,
  getAIUsageLimits,
  getAIUsage,
  checkAIFeatureAvailability,
};

export default aiApi;
