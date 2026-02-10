import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import {
  MessageCircle, Send, Search, Plus, Users, User, ChevronLeft,
  Loader2, Circle, Check, CheckCheck, Clock, Paperclip, MoreVertical,
  MessageSquare, Hash, Bell
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function StaffChatPage() {
  const { user, token } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [showNewChat, setShowNewChat] = useState(false);
  const [userSearch, setUserSearch] = useState('');
  const [searchedUsers, setSearchedUsers] = useState([]);
  const [searchingUsers, setSearchingUsers] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [typingUsers, setTypingUsers] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Fetch conversations
  const fetchConversations = useCallback(async () => {
    try {
      const response = await api.get('/api/chat/conversations');
      setConversations(response.data.conversations || []);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await api.get('/api/chat/unread-count');
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  }, []);

  // Fetch messages for a conversation
  const fetchMessages = useCallback(async (conversationId) => {
    try {
      const response = await api.get(`/api/chat/conversations/${conversationId}/messages`);
      setMessages(response.data.messages || []);
      setTimeout(scrollToBottom, 100);
    } catch (error) {
      console.error('Error fetching messages:', error);
      toast.error('Failed to load messages');
    }
  }, []);

  // Search users for new chat
  const searchUsers = useCallback(async (query) => {
    if (query.length < 2) {
      setSearchedUsers([]);
      return;
    }
    setSearchingUsers(true);
    try {
      const response = await api.get(`/api/chat/users/search?query=${encodeURIComponent(query)}`);
      setSearchedUsers(response.data.users || []);
    } catch (error) {
      console.error('Error searching users:', error);
    } finally {
      setSearchingUsers(false);
    }
  }, []);

  // Create new conversation
  const createConversation = async (participantId) => {
    try {
      const response = await api.post('/api/chat/conversations', {
        chat_type: 'direct',
        participant_ids: [participantId]
      });
      
      const conversation = response.data.conversation;
      if (!response.data.existing) {
        setConversations(prev => [conversation, ...prev]);
      }
      setSelectedConversation(conversation);
      fetchMessages(conversation.id);
      setShowNewChat(false);
      setUserSearch('');
      setSearchedUsers([]);
      toast.success('Conversation started');
    } catch (error) {
      console.error('Error creating conversation:', error);
      toast.error('Failed to start conversation');
    }
  };

  // Send message
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!messageInput.trim() || !selectedConversation) return;

    setSendingMessage(true);
    try {
      const response = await api.post(
        `/api/chat/conversations/${selectedConversation.id}/messages`,
        { content: messageInput.trim(), message_type: 'text' }
      );
      
      const newMessage = response.data.message;
      setMessages(prev => [...prev, newMessage]);
      setMessageInput('');
      setTimeout(scrollToBottom, 100);
      
      // Update conversation's last message
      setConversations(prev => prev.map(conv => 
        conv.id === selectedConversation.id 
          ? { ...conv, last_message: newMessage.content, last_message_at: newMessage.sent_at }
          : conv
      ));
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
    } finally {
      setSendingMessage(false);
    }
  };

  // Mark conversation as read
  const markAsRead = async (conversationId) => {
    try {
      await api.post(`/api/chat/conversations/${conversationId}/read`);
      setConversations(prev => prev.map(conv =>
        conv.id === conversationId ? { ...conv, unread_count: 0 } : conv
      ));
      fetchUnreadCount();
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  // Select conversation
  const selectConversation = (conversation) => {
    setSelectedConversation(conversation);
    fetchMessages(conversation.id);
    if (conversation.unread_count > 0) {
      markAsRead(conversation.id);
    }
  };

  // WebSocket connection
  useEffect(() => {
    if (!token) return;

    const wsUrl = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    const ws = new WebSocket(`${wsUrl}/ws/chat/${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Chat WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'message') {
          // New message received
          if (selectedConversation?.id === data.conversation_id) {
            setMessages(prev => [...prev, data.message]);
            setTimeout(scrollToBottom, 100);
            markAsRead(data.conversation_id);
          } else {
            // Update unread count for other conversations
            setConversations(prev => prev.map(conv =>
              conv.id === data.conversation_id
                ? { ...conv, unread_count: (conv.unread_count || 0) + 1, last_message: data.message.content }
                : conv
            ));
            fetchUnreadCount();
          }
        } else if (data.type === 'typing') {
          // Typing indicator
          setTypingUsers(prev => ({
            ...prev,
            [data.conversation_id]: data.is_typing ? data.user_name : null
          }));
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    ws.onclose = () => {
      console.log('Chat WebSocket disconnected');
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    // Ping/pong keepalive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [token, selectedConversation?.id]);

  // Initial data fetch
  useEffect(() => {
    fetchConversations();
    fetchUnreadCount();
  }, [fetchConversations, fetchUnreadCount]);

  // Debounced user search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (userSearch) {
        searchUsers(userSearch);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [userSearch, searchUsers]);

  // Format time
  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    if (isToday) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  // Get initials
  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  // Get conversation display name
  const getConversationName = (conversation) => {
    if (conversation.chat_type === 'direct') {
      const otherParticipant = conversation.participants?.find(p => p.id !== user?.id);
      return otherParticipant?.name || conversation.name || 'Unknown';
    }
    return conversation.name || 'Group Chat';
  };

  // Get role color
  const getRoleColor = (role) => {
    const colors = {
      physician: 'bg-emerald-100 text-emerald-800',
      nurse: 'bg-rose-100 text-rose-800',
      nursing_supervisor: 'bg-rose-100 text-rose-800',
      pharmacist: 'bg-purple-100 text-purple-800',
      radiologist: 'bg-indigo-100 text-indigo-800',
      hospital_admin: 'bg-blue-100 text-blue-800',
      biller: 'bg-green-100 text-green-800',
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  // Filtered conversations
  const filteredConversations = conversations.filter(conv => {
    if (!searchQuery) return true;
    const name = getConversationName(conv).toLowerCase();
    return name.includes(searchQuery.toLowerCase());
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-sky-500" />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-120px)] flex bg-gray-50" data-testid="staff-chat-page">
      {/* Conversations List */}
      <div className={`w-full md:w-80 lg:w-96 border-r bg-white flex flex-col ${selectedConversation ? 'hidden md:flex' : 'flex'}`}>
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <MessageCircle className="w-6 h-6 text-sky-500" />
              <h1 className="text-xl font-semibold">Staff Chat</h1>
              {unreadCount > 0 && (
                <Badge variant="destructive" className="ml-2">{unreadCount}</Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              {isConnected ? (
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                  <Circle className="w-2 h-2 fill-green-500 mr-1" /> Live
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-gray-50 text-gray-500">
                  Offline
                </Badge>
              )}
              <Button size="icon" variant="ghost" onClick={() => setShowNewChat(true)} data-testid="new-chat-btn">
                <Plus className="w-5 h-5" />
              </Button>
            </div>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
              data-testid="search-conversations"
            />
          </div>
        </div>

        {/* Conversations */}
        <ScrollArea className="flex-1">
          {filteredConversations.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="font-medium">No conversations yet</p>
              <p className="text-sm">Start a new chat with a colleague</p>
              <Button className="mt-4" onClick={() => setShowNewChat(true)}>
                <Plus className="w-4 h-4 mr-2" /> New Chat
              </Button>
            </div>
          ) : (
            <div className="divide-y">
              {filteredConversations.map((conv) => {
                const name = getConversationName(conv);
                const otherParticipant = conv.participants?.find(p => p.id !== user?.id);
                const isSelected = selectedConversation?.id === conv.id;
                const isTyping = typingUsers[conv.id];
                
                return (
                  <button
                    key={conv.id}
                    onClick={() => selectConversation(conv)}
                    className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${isSelected ? 'bg-sky-50 border-r-2 border-sky-500' : ''}`}
                    data-testid={`conversation-${conv.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <Avatar className="w-12 h-12">
                        <AvatarFallback className={`${isSelected ? 'bg-sky-100 text-sky-700' : 'bg-gray-100'}`}>
                          {conv.chat_type === 'group' ? <Users className="w-5 h-5" /> : getInitials(name)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium truncate">{name}</span>
                          <span className="text-xs text-gray-400">{formatTime(conv.last_message_at)}</span>
                        </div>
                        {otherParticipant?.role && (
                          <Badge variant="outline" className={`text-xs mt-1 ${getRoleColor(otherParticipant.role)}`}>
                            {otherParticipant.role.replace('_', ' ')}
                          </Badge>
                        )}
                        <p className="text-sm text-gray-500 truncate mt-1">
                          {isTyping ? (
                            <span className="text-sky-500 italic">typing...</span>
                          ) : (
                            conv.last_message || 'No messages yet'
                          )}
                        </p>
                      </div>
                      {conv.unread_count > 0 && (
                        <Badge className="bg-sky-500">{conv.unread_count}</Badge>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Chat Area */}
      <div className={`flex-1 flex flex-col ${!selectedConversation ? 'hidden md:flex' : 'flex'}`}>
        {selectedConversation ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b bg-white flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                onClick={() => setSelectedConversation(null)}
              >
                <ChevronLeft className="w-5 h-5" />
              </Button>
              <Avatar className="w-10 h-10">
                <AvatarFallback className="bg-sky-100 text-sky-700">
                  {selectedConversation.chat_type === 'group' 
                    ? <Users className="w-5 h-5" /> 
                    : getInitials(getConversationName(selectedConversation))}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <h2 className="font-semibold">{getConversationName(selectedConversation)}</h2>
                {selectedConversation.participants && (
                  <p className="text-sm text-gray-500">
                    {selectedConversation.participants.length} participants
                  </p>
                )}
              </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((msg, idx) => {
                  const isOwn = msg.sender_id === user?.id;
                  const showAvatar = idx === 0 || messages[idx - 1]?.sender_id !== msg.sender_id;
                  
                  return (
                    <div
                      key={msg.id}
                      className={`flex items-end gap-2 ${isOwn ? 'justify-end' : 'justify-start'}`}
                    >
                      {!isOwn && showAvatar && (
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="bg-gray-100 text-xs">
                            {getInitials(msg.sender_name)}
                          </AvatarFallback>
                        </Avatar>
                      )}
                      {!isOwn && !showAvatar && <div className="w-8" />}
                      
                      <div className={`max-w-[70%] ${isOwn ? 'order-first' : ''}`}>
                        {!isOwn && showAvatar && (
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-medium text-gray-700">{msg.sender_name}</span>
                            {msg.sender_role && (
                              <Badge variant="outline" className={`text-xs ${getRoleColor(msg.sender_role)}`}>
                                {msg.sender_role.replace('_', ' ')}
                              </Badge>
                            )}
                          </div>
                        )}
                        <div
                          className={`p-3 rounded-2xl ${
                            isOwn 
                              ? 'bg-sky-500 text-white rounded-br-none' 
                              : 'bg-white border rounded-bl-none'
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                        </div>
                        <div className={`flex items-center gap-1 mt-1 ${isOwn ? 'justify-end' : ''}`}>
                          <span className="text-xs text-gray-400">{formatTime(msg.sent_at)}</span>
                          {isOwn && (
                            msg.read_by?.length > 1 
                              ? <CheckCheck className="w-3 h-3 text-sky-500" />
                              : <Check className="w-3 h-3 text-gray-400" />
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
                
                {/* Typing indicator */}
                {typingUsers[selectedConversation.id] && (
                  <div className="flex items-center gap-2 text-gray-500 text-sm">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span>{typingUsers[selectedConversation.id]} is typing...</span>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Message Input */}
            <form onSubmit={sendMessage} className="p-4 border-t bg-white">
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Type a message..."
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  className="flex-1"
                  disabled={sendingMessage}
                  data-testid="message-input"
                />
                <Button 
                  type="submit" 
                  disabled={!messageInput.trim() || sendingMessage}
                  className="bg-sky-500 hover:bg-sky-600"
                  data-testid="send-message-btn"
                >
                  {sendingMessage ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </Button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center p-8">
              <MessageCircle className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <h2 className="text-xl font-semibold text-gray-700 mb-2">Welcome to Staff Chat</h2>
              <p className="text-gray-500 mb-4">Select a conversation or start a new one</p>
              <Button onClick={() => setShowNewChat(true)} className="bg-sky-500 hover:bg-sky-600">
                <Plus className="w-4 h-4 mr-2" /> Start New Chat
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* New Chat Dialog */}
      <Dialog open={showNewChat} onOpenChange={setShowNewChat}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-sky-500" />
              New Conversation
            </DialogTitle>
            <DialogDescription>
              Search for a colleague to start a conversation
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search by name or email..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="pl-9"
                autoFocus
                data-testid="search-users-input"
              />
            </div>
            
            <ScrollArea className="h-64">
              {searchingUsers ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-sky-500" />
                </div>
              ) : searchedUsers.length > 0 ? (
                <div className="space-y-2">
                  {searchedUsers.map((searchUser) => (
                    <button
                      key={searchUser.id}
                      onClick={() => createConversation(searchUser.id)}
                      className="w-full p-3 flex items-center gap-3 rounded-lg hover:bg-gray-50 transition-colors text-left"
                      data-testid={`user-option-${searchUser.id}`}
                    >
                      <Avatar>
                        <AvatarFallback className="bg-sky-100 text-sky-700">
                          {getInitials(searchUser.name)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{searchUser.name}</p>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className={`text-xs ${getRoleColor(searchUser.role)}`}>
                            {searchUser.role?.replace('_', ' ')}
                          </Badge>
                          {searchUser.department && (
                            <span className="text-xs text-gray-500">{searchUser.department}</span>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : userSearch.length >= 2 ? (
                <div className="text-center py-8 text-gray-500">
                  <User className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p>No users found</p>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Search className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p>Type at least 2 characters to search</p>
                </div>
              )}
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
