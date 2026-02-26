/**
 * AI Components Module
 * 
 * This module exports all AI-related UI components for the wedding invitation platform.
 * These components provide the interface for AI-powered features including photo analysis,
 * style recommendations, template matching, and message generation.
 */

// Main AI Assistant Widget
export { AIAssistantWidget } from './AIAssistantWidget';
export type { AIAssistantWidgetProps } from './AIAssistantWidget';

// Photo Upload Component
export { PhotoUploadZone } from './PhotoUploadZone';
export type { PhotoUploadZoneProps } from './PhotoUploadZone';

// Analysis Progress Indicator
export { AnalysisProgress, DEFAULT_ANALYSIS_STEPS } from './AnalysisProgress';
export type { AnalysisProgressProps } from './AnalysisProgress';

// Color Palette Display
export { ColorPaletteDisplay } from './ColorPaletteDisplay';
export type { ColorPaletteDisplayProps } from './ColorPaletteDisplay';

// Style Recommendation Card
export { StyleRecommendationCard } from './StyleRecommendationCard';
export type { StyleRecommendationCardProps } from './StyleRecommendationCard';

// Template Recommendation Grid
export { TemplateRecommendationGrid } from './TemplateRecommendationGrid';
export type { TemplateRecommendationGridProps } from './TemplateRecommendationGrid';

// Message Generator
export { MessageGenerator } from './MessageGenerator';
export type { MessageGeneratorProps } from './MessageGenerator';

// AI Onboarding Dialog
export { AIOnboardingDialog } from './AIOnboardingDialog';
export type { AIOnboardingDialogProps } from './AIOnboardingDialog';

// AI Feature Badge
export { AIFeatureBadge, AIIndicator, AIAssistantButton } from './AIFeatureBadge';
export type { AIFeatureBadgeProps, AIIndicatorProps, AIAssistantButtonProps } from './AIFeatureBadge';
