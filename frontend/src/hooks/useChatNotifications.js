import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export function useChatNotifications() {
  const { user, token } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const wsRef = useRef(null);
  const audioRef = useRef(null);

  // Initialize audio for notification sound
  useEffect(() => {
    // Simple beep sound as base64
    const beepSound = 'data:audio/wav;base64,UklGRl9vT19teleQQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU'+Array(300).fill('A').join('');
    audioRef.current = new Audio(beepSound);
    audioRef.current.volume = 0.5;
  }, []);

  // Request browser notification permission
  const requestNotificationPermission = useCallback(async () => {
    if (!('Notification' in window)) {
      console.log('Browser does not support notifications');
      return false;
    }
    
    if (Notification.permission === 'granted') {
      setNotificationsEnabled(true);
      return true;
    }
    
    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      const enabled = permission === 'granted';
      setNotificationsEnabled(enabled);
      return enabled;
    }
    
    return false;
  }, []);

  // Show browser notification
  const showBrowserNotification = useCallback((title, body, onClick) => {
    if (notificationsEnabled && Notification.permission === 'granted') {
      const notification = new Notification(title, {
        body,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: 'chat-notification',
        renotify: true
      });
      
      notification.onclick = () => {
        window.focus();
        if (onClick) onClick();
        notification.close();
      };
      
      // Auto close after 5 seconds
      setTimeout(() => notification.close(), 5000);
    }
  }, [notificationsEnabled]);

  // Play notification sound
  const playNotificationSound = useCallback(() => {
    if (soundEnabled && audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {});
    }
  }, [soundEnabled]);

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    if (!token) return;
    try {
      const response = await api.get('/chat/unread-count');
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  }, [token]);

  // Handle incoming WebSocket message
  const handleWebSocketMessage = useCallback((data) => {
    if (data.type === 'message') {
      // Increment unread count
      setUnreadCount(prev => prev + 1);
      
      // Play sound
      playNotificationSound();
      
      // Show toast notification
      toast.info(`New message from ${data.message?.sender_name || 'Staff'}`, {
        description: data.message?.content?.substring(0, 50) + (data.message?.content?.length > 50 ? '...' : ''),
        action: {
          label: 'View',
          onClick: () => window.location.href = '/staff-chat'
        }
      });
      
      // Show browser notification if page is not focused
      if (document.hidden) {
        showBrowserNotification(
          `Message from ${data.message?.sender_name || 'Staff'}`,
          data.message?.content?.substring(0, 100),
          () => window.location.href = '/staff-chat'
        );
      }
    }
  }, [playNotificationSound, showBrowserNotification]);

  // WebSocket connection
  useEffect(() => {
    if (!token || !user) return;
    
    // Don't connect for super_admin (they don't have chat access)
    if (user.role === 'super_admin') return;

    const wsUrl = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    
    const connectWebSocket = () => {
      const ws = new WebSocket(`${wsUrl}/ws/chat/${token}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Chat notifications WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Only handle messages when NOT on the staff-chat page
          if (data.type === 'message' && !window.location.pathname.includes('/staff-chat')) {
            handleWebSocketMessage(data);
          }
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };

      ws.onclose = () => {
        console.log('Chat notifications WebSocket disconnected');
        setIsConnected(false);
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connectWebSocket();

    // Ping/pong keepalive
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [token, user, handleWebSocketMessage]);

  // Fetch initial unread count
  useEffect(() => {
    fetchUnreadCount();
    
    // Refresh unread count every 60 seconds
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  // Request notification permission on mount
  useEffect(() => {
    requestNotificationPermission();
  }, [requestNotificationPermission]);

  return {
    unreadCount,
    setUnreadCount,
    isConnected,
    soundEnabled,
    setSoundEnabled,
    notificationsEnabled,
    requestNotificationPermission,
    fetchUnreadCount
  };
}
