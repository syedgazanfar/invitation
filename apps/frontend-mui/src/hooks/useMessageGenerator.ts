/**
 * Message Generator Hook
 * 
 * Provides state management for AI-powered invitation message generation.
 * Handles generating multiple message options and tracking user selection.
 * 
 * @example
 * ```tsx
 * const { 
 *   generateMessages, 
 *   messages, 
 *   selectedMessage, 
 *   selectMessage, 
 *   loading,
 *   error 
 * } = useMessageGenerator();
 * 
 * const handleGenerate = async () => {
 *   await generateMessages({
 *     brideName: 'Priya',
 *     groomName: 'Rahul',
 *     eventType: 'WEDDING',
 *     tone: 'warm',
 *     details: 'Childhood sweethearts'
 *   });
 * };
 * ```
 */
import { useState, useCallback, useRef } from 'react';
import {
  generateMessages as generateMessagesApi,
  MessageGenerationRequest,
  GeneratedMessage,
  MessageGenerationResult,
  MessageTone,
} from '../services/aiApi';

export interface MessageGenerationParams {
  /** Bride's name */
  brideName: string;
  /** Groom's name */
  groomName: string;
  /** Event type */
  eventType: string;
  /** Wedding/event style */
  style?: string;
  /** Cultural context */
  culture?: string;
  /** Desired tone for the message */
  tone?: MessageTone;
  /** Additional details */
  details?: string;
  /** Wedding date */
  weddingDate?: string;
}

export interface UseMessageGeneratorReturn {
  /** Whether message generation is in progress */
  loading: boolean;
  /** Array of generated message options */
  messages: GeneratedMessage[];
  /** Currently selected message content */
  selectedMessage: string | null;
  /** Error object if generation failed */
  error: Error | null;
  /** Information about the last generation (tokens used, time taken) */
  generationInfo: {
    tokensUsed: number;
    generationTimeMs: number;
  } | null;
  /** Generate messages based on provided context */
  generateMessages: (params: MessageGenerationParams) => Promise<GeneratedMessage[] | null>;
  /** Select a message from the generated options */
  selectMessage: (message: string | GeneratedMessage) => void;
  /** Select a message by its index in the messages array */
  selectMessageByIndex: (index: number) => void;
  /** Get the selected message as a GeneratedMessage object */
  getSelectedMessageObject: () => GeneratedMessage | null;
  /** Reset all state */
  reset: () => void;
  /** Clear only the error state */
  clearError: () => void;
  /** Regenerate messages with the same parameters */
  regenerate: () => Promise<GeneratedMessage[] | null>;
}

/**
 * Hook for AI-powered message generation
 * 
 * @returns Message generation state and control functions
 */
export const useMessageGenerator = (): UseMessageGeneratorReturn => {
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<GeneratedMessage[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<string | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [generationInfo, setGenerationInfo] = useState<{
    tokensUsed: number;
    generationTimeMs: number;
  } | null>(null);

  // Store last parameters for regeneration
  const lastParamsRef = useRef<MessageGenerationParams | null>(null);
  // Store abort controller for cancellation
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Get user-friendly error message
   */
  const getErrorMessage = (err: unknown): string => {
    if (err instanceof Error) {
      if (err.message.includes('Network Error')) {
        return 'Network connection failed. Please check your internet connection and try again.';
      }
      if (err.message.includes('429')) {
        return 'You have reached the message generation limit. Please try again later.';
      }
      if (err.message.includes('quota')) {
        return 'AI service quota exceeded. Please try again later or contact support.';
      }
      return err.message;
    }
    return 'Failed to generate messages. Please try again.';
  };

  /**
   * Generate invitation messages using AI
   * 
   * @param params - Message generation parameters
   * @returns Promise resolving to generated messages array or null on error
   */
  const generateMessages = useCallback(async (
    params: MessageGenerationParams
  ): Promise<GeneratedMessage[] | null> => {
    // Store params for potential regeneration
    lastParamsRef.current = params;

    // Reset state
    setLoading(true);
    setError(null);
    setMessages([]);
    setSelectedMessage(null);
    setGenerationInfo(null);

    // Validate required parameters
    if (!params.brideName?.trim() || !params.groomName?.trim()) {
      setError(new Error('Please provide both bride and groom names.'));
      setLoading(false);
      return null;
    }

    // Create abort controller
    abortControllerRef.current = new AbortController();

    try {
      const request: MessageGenerationRequest = {
        brideName: params.brideName.trim(),
        groomName: params.groomName.trim(),
        eventType: params.eventType,
        style: params.style,
        culture: params.culture,
        tone: params.tone,
        details: params.details,
        weddingDate: params.weddingDate,
      };

      const result: MessageGenerationResult = await generateMessagesApi(request);

      setMessages(result.options);
      setGenerationInfo({
        tokensUsed: result.tokensUsed,
        generationTimeMs: result.generationTimeMs,
      });

      return result.options;
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
   * Select a message from the generated options
   * 
   * @param message - The message content string or GeneratedMessage object to select
   */
  const selectMessage = useCallback((message: string | GeneratedMessage) => {
    if (typeof message === 'string') {
      setSelectedMessage(message);
    } else {
      setSelectedMessage(message.message);
    }
  }, []);

  /**
   * Select a message by its index in the messages array
   * 
   * @param index - The index of the message to select
   */
  const selectMessageByIndex = useCallback((index: number) => {
    if (index >= 0 && index < messages.length) {
      setSelectedMessage(messages[index].message);
    }
  }, [messages]);

  /**
   * Get the selected message as a GeneratedMessage object
   * 
   * @returns The selected message object or null if not found
   */
  const getSelectedMessageObject = useCallback((): GeneratedMessage | null => {
    if (!selectedMessage) return null;
    return messages.find(m => m.message === selectedMessage) || null;
  }, [messages, selectedMessage]);

  /**
   * Reset all state to initial values
   */
  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
    setMessages([]);
    setSelectedMessage(null);
    setError(null);
    setGenerationInfo(null);
    lastParamsRef.current = null;
  }, []);

  /**
   * Clear only the error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Regenerate messages with the same parameters
   * 
   * @returns Promise resolving to generated messages array or null on error
   */
  const regenerate = useCallback(async (): Promise<GeneratedMessage[] | null> => {
    if (!lastParamsRef.current) {
      setError(new Error('No previous generation parameters found. Please generate messages first.'));
      return null;
    }
    return generateMessages(lastParamsRef.current);
  }, [generateMessages]);

  return {
    loading,
    messages,
    selectedMessage,
    error,
    generationInfo,
    generateMessages,
    selectMessage,
    selectMessageByIndex,
    getSelectedMessageObject,
    reset,
    clearError,
    regenerate,
  };
};

export default useMessageGenerator;
