/**
 * WebSocket Hook for Real-time Admin Dashboard
 * 
 * This hook provides WebSocket connectivity for the admin dashboard,
 * including automatic reconnection, heartbeat/ping-pong, and
 * message handling for approval updates.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '../store/authStore';

// WebSocket connection states
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error';

// Message types from server
export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface ApprovalUpdateMessage extends WebSocketMessage {
  type: 'approval_update';
  action: 'approved' | 'rejected';
  user: {
    id: string;
    username: string;
    full_name?: string;
    phone?: string;
    email?: string;
    is_approved: boolean;
    current_plan?: {
      code: string;
      name: string;
    };
  };
  performed_by?: {
    id: string;
    username: string;
  };
  timestamp: string;
  notes?: string;
}

export interface PendingCountMessage extends WebSocketMessage {
  type: 'pending_count_update';
  count: number;
  change: number;
}

export interface NewUserMessage extends WebSocketMessage {
  type: 'new_user';
  user: {
    id: string;
    username: string;
    full_name?: string;
    phone: string;
    email?: string;
    created_at: string;
  };
  timestamp: string;
}

export interface OrderUpdateMessage extends WebSocketMessage {
  type: 'order_update';
  order_id: string;
  status: string;
  previous_status?: string;
  timestamp: string;
}

export interface ConnectionMessage extends WebSocketMessage {
  type: 'connection_established';
  message: string;
  user: {
    id: string;
    username: string;
    is_staff: boolean;
  };
}

export type WebSocketData = 
  | ApprovalUpdateMessage 
  | PendingCountMessage 
  | NewUserMessage 
  | OrderUpdateMessage
  | ConnectionMessage
  | WebSocketMessage;

// Hook options interface
interface UseWebSocketOptions {
  url?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  onMessage?: (data: WebSocketData) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

// Hook return interface
interface UseWebSocketReturn {
  state: WebSocketState;
  lastMessage: WebSocketData | null;
  pendingCount: number;
  recentApprovals: ApprovalUpdateMessage[];
  sendMessage: (message: object) => void;
  connect: () => void;
  disconnect: () => void;
  connectedAdmins: string[];
}

/**
 * WebSocket Hook for real-time admin dashboard updates
 * 
 * @param options - Configuration options
 * @returns WebSocket state and control functions
 */
export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    url: customUrl,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const { accessToken } = useAuthStore();
  
  // State
  const [state, setState] = useState<WebSocketState>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketData | null>(null);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [recentApprovals, setRecentApprovals] = useState<ApprovalUpdateMessage[]>([]);
  const [connectedAdmins, setConnectedAdmins] = useState<string[]>([]);

  // Refs for managing WebSocket instance and timers
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isManualDisconnectRef = useRef<boolean>(false);

  // Determine WebSocket URL
  const getWebSocketUrl = useCallback((): string => {
    if (customUrl) return customUrl;
    
    const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
    // Convert HTTP URL to WebSocket URL
    const wsProtocol = apiUrl.startsWith('https') ? 'wss' : 'ws';
    const wsHost = apiUrl.replace(/^https?:\/\//, '').replace(/\/api\/v1$/, '');
    return `${wsProtocol}://${wsHost}/ws/admin/dashboard/`;
  }, [customUrl]);

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  // Send heartbeat/ping
  const sendHeartbeat = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'ping',
        timestamp: Date.now()
      }));
    }
  }, []);

  // Handle incoming messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data: WebSocketData = JSON.parse(event.data);
      setLastMessage(data);

      switch (data.type) {
        case 'connection_established':
          console.log('[WebSocket] Connected:', data.message);
          break;

        case 'approval_update':
          const approvalData = data as ApprovalUpdateMessage;
          setRecentApprovals(prev => [approvalData, ...prev].slice(0, 50));
          break;

        case 'pending_count_update':
          const countData = data as PendingCountMessage;
          setPendingCount(countData.count);
          break;

        case 'new_user':
          // Increment pending count when new user registers
          setPendingCount(prev => prev + 1);
          break;

        case 'order_update':
          // Handle order updates
          break;

        case 'admin_joined':
          setConnectedAdmins(prev => [...new Set([...prev, data.username])]);
          break;

        case 'admin_left':
          setConnectedAdmins(prev => prev.filter(name => name !== data.username));
          break;

        case 'pong':
          // Heartbeat response received
          break;

        case 'error':
          console.error('[WebSocket] Server error:', data.message);
          break;

        default:
          console.log('[WebSocket] Unknown message type:', data.type);
      }

      // Call external message handler
      if (onMessage) {
        onMessage(data);
      }
    } catch (error) {
      console.error('[WebSocket] Failed to parse message:', error);
    }
  }, [onMessage]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Don't connect if no token or already connecting/connected
    if (!accessToken) {
      console.warn('[WebSocket] No access token available');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.CONNECTING ||
        wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    isManualDisconnectRef.current = false;
    setState('connecting');

    const wsUrl = `${getWebSocketUrl()}?token=${accessToken}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setState('connected');
        reconnectAttemptsRef.current = 0;
        
        // Start heartbeat
        heartbeatTimerRef.current = setInterval(sendHeartbeat, heartbeatInterval);
        
        // Request initial pending count
        wsRef.current?.send(JSON.stringify({
          type: 'get_pending_count'
        }));

        if (onConnect) onConnect();
      };

      wsRef.current.onmessage = handleMessage;

      wsRef.current.onclose = (event) => {
        setState('disconnected');
        clearTimers();

        if (!isManualDisconnectRef.current && 
            reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(`[WebSocket] Reconnecting... Attempt ${reconnectAttemptsRef.current}`);
          
          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }

        if (onDisconnect) onDisconnect();
      };

      wsRef.current.onerror = (error) => {
        setState('error');
        console.error('[WebSocket] Error:', error);
        if (onError) onError(error);
      };

    } catch (error) {
      setState('error');
      console.error('[WebSocket] Failed to connect:', error);
    }
  }, [
    accessToken, 
    getWebSocketUrl, 
    handleMessage, 
    sendHeartbeat, 
    heartbeatInterval, 
    reconnectInterval, 
    maxReconnectAttempts,
    onConnect, 
    onDisconnect, 
    onError,
    clearTimers
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    isManualDisconnectRef.current = true;
    clearTimers();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setState('disconnected');
    reconnectAttemptsRef.current = 0;
  }, [clearTimers]);

  // Send message through WebSocket
  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message - not connected');
    }
  }, []);

  // Auto-connect when token is available
  useEffect(() => {
    if (accessToken && state === 'disconnected') {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [accessToken]); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [clearTimers]);

  return {
    state,
    lastMessage,
    pendingCount,
    recentApprovals,
    sendMessage,
    connect,
    disconnect,
    connectedAdmins,
  };
};

export default useWebSocket;
