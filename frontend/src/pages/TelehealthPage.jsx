import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { telehealthAPI, patientAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { formatDateTime } from '@/lib/utils';
import {
  Video, VideoOff, Mic, MicOff, Phone, PhoneOff, Monitor,
  MessageSquare, Users, Settings, ArrowLeft, Clock, Calendar,
  User, Send, Maximize2, Minimize2, Volume2, VolumeX
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function TelehealthPage() {
  const { sessionId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Session state
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [inCall, setInCall] = useState(false);
  const [callEnded, setCallEnded] = useState(false);
  
  // Video state
  const [localStream, setLocalStream] = useState(null);
  const [remoteStream, setRemoteStream] = useState(null);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [screenSharing, setScreenSharing] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  
  // Chat state
  const [showChat, setShowChat] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  
  // WebRTC state
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const websocketRef = useRef(null);
  const [participants, setParticipants] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // Schedule dialog
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [newSession, setNewSession] = useState({
    patient_id: '',
    patient_name: '',
    scheduled_time: '',
    duration_minutes: 30,
    reason: ''
  });
  const [patients, setPatients] = useState([]);
  const [upcomingSessions, setUpcomingSessions] = useState([]);

  // ICE servers config
  const iceServers = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ];

  // Fetch session details if sessionId is provided
  useEffect(() => {
    if (sessionId) {
      fetchSession();
    } else {
      fetchUpcomingSessions();
      setLoading(false);
    }
  }, [sessionId]);

  const fetchSession = async () => {
    try {
      const res = await telehealthAPI.getSession(sessionId);
      setSession(res.data.session);
      setParticipants(res.data.participants || []);
    } catch (err) {
      toast.error('Failed to load session');
      navigate('/telehealth');
    } finally {
      setLoading(false);
    }
  };

  const fetchUpcomingSessions = async () => {
    try {
      const res = await telehealthAPI.getUpcoming();
      setUpcomingSessions(res.data.sessions || []);
    } catch (err) {
      console.error('Failed to fetch upcoming sessions', err);
    }
  };

  const fetchPatients = async () => {
    try {
      const res = await patientAPI.getAll();
      setPatients(res.data.patients || []);
    } catch (err) {
      console.error('Failed to fetch patients', err);
    }
  };

  // Initialize WebRTC
  const initializeWebRTC = useCallback(async () => {
    try {
      // Get local media stream
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      
      setLocalStream(stream);
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // Create peer connection
      const pc = new RTCPeerConnection({ iceServers });
      peerConnectionRef.current = pc;

      // Add local tracks to peer connection
      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
      });

      // Handle remote stream
      pc.ontrack = (event) => {
        const [remoteStreamObj] = event.streams;
        setRemoteStream(remoteStreamObj);
        if (remoteVideoRef.current) {
          remoteVideoRef.current.srcObject = remoteStreamObj;
        }
      };

      // Handle ICE candidates
      pc.onicecandidate = (event) => {
        if (event.candidate && websocketRef.current) {
          websocketRef.current.send(JSON.stringify({
            type: 'ice-candidate',
            candidate: event.candidate
          }));
        }
      };

      // Connection state changes
      pc.onconnectionstatechange = () => {
        setConnectionStatus(pc.connectionState);
        if (pc.connectionState === 'connected') {
          toast.success('Connected to remote peer');
        } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
          toast.error('Connection lost');
        }
      };

      return pc;
    } catch (err) {
      console.error('Failed to initialize WebRTC:', err);
      toast.error('Failed to access camera/microphone. Please check permissions.');
      return null;
    }
  }, []);

  // Connect to signaling server
  const connectWebSocket = useCallback(async (roomId) => {
    const wsUrl = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    const ws = new WebSocket(`${wsUrl}/api/telehealth/ws/${roomId}/${user.id}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connecting');
    };

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      const pc = peerConnectionRef.current;

      switch (data.type) {
        case 'room-info':
          setParticipants(data.participants);
          break;

        case 'user-joined':
          setParticipants(prev => [...new Set([...prev, data.user_id])]);
          toast.info('Participant joined');
          // Create and send offer to new user
          if (pc && data.user_id !== user.id) {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            ws.send(JSON.stringify({
              type: 'offer',
              sdp: pc.localDescription,
              to_user: data.user_id
            }));
          }
          break;

        case 'user-left':
          setParticipants(data.participants || []);
          toast.info('Participant left');
          break;

        case 'offer':
          if (pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            ws.send(JSON.stringify({
              type: 'answer',
              sdp: pc.localDescription,
              to_user: data.from_user
            }));
          }
          break;

        case 'answer':
          if (pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
          }
          break;

        case 'ice-candidate':
          if (pc && data.candidate) {
            try {
              await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (err) {
              console.error('Error adding ICE candidate:', err);
            }
          }
          break;

        case 'chat':
          setChatMessages(prev => [...prev, {
            from: data.from_user,
            message: data.message,
            timestamp: data.timestamp
          }]);
          break;

        default:
          break;
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast.error('Connection error');
    };

    websocketRef.current = ws;
    return ws;
  }, [user]);

  // Start call
  const startCall = async () => {
    if (!session) return;

    try {
      // Join session
      await telehealthAPI.joinSession(sessionId, {
        user_id: user.id,
        user_name: `${user.first_name} ${user.last_name}`,
        role: user.role === 'physician' ? 'provider' : 'patient'
      });

      // Initialize WebRTC
      await initializeWebRTC();

      // Connect to signaling server
      await connectWebSocket(session.room_id);

      // Update session status
      await telehealthAPI.startSession(sessionId);

      setInCall(true);
      toast.success('Call started');
    } catch (err) {
      console.error('Failed to start call:', err);
      toast.error('Failed to start call');
    }
  };

  // End call
  const endCall = async () => {
    try {
      // Close WebRTC
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
      }

      // Close WebSocket
      if (websocketRef.current) {
        websocketRef.current.close();
      }

      // Stop local stream
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
      }

      // Update session status
      if (sessionId) {
        await telehealthAPI.endSession(sessionId);
      }

      setInCall(false);
      setCallEnded(true);
      setLocalStream(null);
      setRemoteStream(null);
      toast.success('Call ended');
    } catch (err) {
      console.error('Failed to end call:', err);
    }
  };

  // Toggle video
  const toggleVideo = () => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setVideoEnabled(videoTrack.enabled);
      }
    }
  };

  // Toggle audio
  const toggleAudio = () => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setAudioEnabled(audioTrack.enabled);
      }
    }
  };

  // Screen share
  const toggleScreenShare = async () => {
    if (screenSharing) {
      // Stop screen share
      if (localStream) {
        const videoTrack = localStream.getVideoTracks()[0];
        if (videoTrack) {
          videoTrack.stop();
        }
      }
      // Re-enable camera
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setLocalStream(stream);
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
      // Replace track in peer connection
      const sender = peerConnectionRef.current?.getSenders().find(s => s.track?.kind === 'video');
      if (sender) {
        sender.replaceTrack(stream.getVideoTracks()[0]);
      }
      setScreenSharing(false);
    } else {
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        const screenTrack = screenStream.getVideoTracks()[0];
        
        // Replace video track in peer connection
        const sender = peerConnectionRef.current?.getSenders().find(s => s.track?.kind === 'video');
        if (sender) {
          sender.replaceTrack(screenTrack);
        }
        
        // Update local video preview
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = screenStream;
        }
        
        screenTrack.onended = () => {
          toggleScreenShare();
        };
        
        setScreenSharing(true);
      } catch (err) {
        console.error('Failed to share screen:', err);
        toast.error('Failed to share screen');
      }
    }
  };

  // Send chat message
  const sendChatMessage = () => {
    if (!chatInput.trim() || !websocketRef.current) return;
    
    websocketRef.current.send(JSON.stringify({
      type: 'chat',
      message: chatInput
    }));
    
    setChatMessages(prev => [...prev, {
      from: user.id,
      message: chatInput,
      timestamp: new Date().toISOString(),
      isOwn: true
    }]);
    
    setChatInput('');
  };

  // Schedule new session
  const handleScheduleSession = async (e) => {
    e.preventDefault();
    try {
      const res = await telehealthAPI.createSession({
        ...newSession,
        provider_id: user.id,
        provider_name: `${user.first_name} ${user.last_name}`
      });
      toast.success('Telehealth session scheduled');
      setScheduleDialogOpen(false);
      setNewSession({
        patient_id: '',
        patient_name: '',
        scheduled_time: '',
        duration_minutes: 30,
        reason: ''
      });
      fetchUpcomingSessions();
    } catch (err) {
      toast.error('Failed to schedule session');
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
      }
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [localStream]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  // Session list view (no sessionId)
  if (!sessionId) {
    return (
      <div className="space-y-6 animate-fade-in" data-testid="telehealth-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
              Telehealth Center
            </h1>
            <p className="text-slate-500 mt-1">Manage video consultations</p>
          </div>
          <Dialog open={scheduleDialogOpen} onOpenChange={(open) => {
            setScheduleDialogOpen(open);
            if (open) fetchPatients();
          }}>
            <DialogTrigger asChild>
              <Button className="gap-2 bg-sky-600 hover:bg-sky-700" data-testid="schedule-btn">
                <Video className="w-4 h-4" /> Schedule Session
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Schedule Telehealth Session</DialogTitle>
                <DialogDescription>Create a new video consultation</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleScheduleSession} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Patient</Label>
                  <Select 
                    value={newSession.patient_id}
                    onValueChange={(v) => {
                      const patient = patients.find(p => p.id === v);
                      setNewSession({
                        ...newSession,
                        patient_id: v,
                        patient_name: patient ? `${patient.first_name} ${patient.last_name}` : ''
                      });
                    }}
                  >
                    <SelectTrigger data-testid="patient-select">
                      <SelectValue placeholder="Select patient" />
                    </SelectTrigger>
                    <SelectContent>
                      {patients.map(p => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.first_name} {p.last_name} - {p.mrn}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Scheduled Time</Label>
                  <Input
                    type="datetime-local"
                    required
                    value={newSession.scheduled_time}
                    onChange={(e) => setNewSession({ ...newSession, scheduled_time: e.target.value })}
                    data-testid="scheduled-time"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Duration (minutes)</Label>
                  <Select
                    value={String(newSession.duration_minutes)}
                    onValueChange={(v) => setNewSession({ ...newSession, duration_minutes: parseInt(v) })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">15 minutes</SelectItem>
                      <SelectItem value="30">30 minutes</SelectItem>
                      <SelectItem value="45">45 minutes</SelectItem>
                      <SelectItem value="60">60 minutes</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Reason for Visit</Label>
                  <Textarea
                    value={newSession.reason}
                    onChange={(e) => setNewSession({ ...newSession, reason: e.target.value })}
                    placeholder="Brief description of visit reason"
                    data-testid="reason"
                  />
                </div>
                <Button type="submit" className="w-full bg-sky-600 hover:bg-sky-700">
                  Schedule Session
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Upcoming Sessions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" /> Upcoming Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {upcomingSessions.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <Video className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>No upcoming telehealth sessions</p>
                <p className="text-sm mt-1">Schedule a new session to get started</p>
              </div>
            ) : (
              <div className="space-y-3">
                {upcomingSessions.map((s) => (
                  <Card key={s.id} className="border-l-4 border-l-sky-500">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-full bg-sky-100 flex items-center justify-center">
                            <Video className="w-6 h-6 text-sky-600" />
                          </div>
                          <div>
                            <p className="font-medium">{s.patient_name}</p>
                            <div className="flex items-center gap-2 text-sm text-slate-500">
                              <Clock className="w-3 h-3" />
                              <span>{formatDateTime(s.scheduled_time)}</span>
                              <span>•</span>
                              <span>{s.duration_minutes} min</span>
                            </div>
                            {s.reason && (
                              <p className="text-sm text-slate-600 mt-1">{s.reason}</p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={s.status === 'waiting' ? 'default' : 'outline'}>
                            {s.status}
                          </Badge>
                          <Button
                            onClick={() => navigate(`/telehealth/${s.id}`)}
                            className="gap-2 bg-green-600 hover:bg-green-700"
                            data-testid={`join-session-${s.id}`}
                          >
                            <Phone className="w-4 h-4" /> Join
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <Video className="w-8 h-8 text-sky-600 mx-auto mb-2" />
              <h3 className="font-medium">WebRTC Video</h3>
              <p className="text-sm text-slate-500">Peer-to-peer encrypted calls</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Monitor className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <h3 className="font-medium">Screen Share</h3>
              <p className="text-sm text-slate-500">Share your screen with patients</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <MessageSquare className="w-8 h-8 text-amber-600 mx-auto mb-2" />
              <h3 className="font-medium">In-Call Chat</h3>
              <p className="text-sm text-slate-500">Text chat during video calls</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Call ended view
  if (callEnded) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-8 pb-6">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <PhoneOff className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-xl font-bold mb-2">Call Ended</h2>
            <p className="text-slate-500 mb-6">
              Your telehealth session has been completed.
            </p>
            <div className="space-y-3">
              <Button 
                onClick={() => navigate('/telehealth')}
                className="w-full"
              >
                Back to Telehealth Center
              </Button>
              <Button 
                variant="outline"
                onClick={() => navigate(`/patients/${session?.patient_id}`)}
                className="w-full"
              >
                View Patient Chart
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Waiting room / Pre-call view
  if (!inCall && session) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/telehealth')}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
              Telehealth Session
            </h1>
            <p className="text-slate-500">Waiting Room</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Session Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" /> Session Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Patient</p>
                  <p className="font-medium">{session.patient_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Provider</p>
                  <p className="font-medium">{session.provider_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Scheduled</p>
                  <p className="font-medium">{formatDateTime(session.scheduled_time)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Duration</p>
                  <p className="font-medium">{session.duration_minutes} minutes</p>
                </div>
              </div>
              {session.reason && (
                <div>
                  <p className="text-sm text-slate-500">Reason</p>
                  <p className="font-medium">{session.reason}</p>
                </div>
              )}
              <Badge variant="outline" className="mt-2">
                Status: {session.status}
              </Badge>
            </CardContent>
          </Card>

          {/* Camera Preview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Video className="w-5 h-5" /> Camera Preview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="aspect-video bg-slate-900 rounded-lg overflow-hidden relative">
                <video
                  ref={localVideoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
                {!localStream && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <p className="text-white">Camera will activate when you join</p>
                  </div>
                )}
              </div>
              <div className="flex justify-center gap-4 mt-4">
                <Button
                  size="lg"
                  className="gap-2 bg-green-600 hover:bg-green-700"
                  onClick={startCall}
                  data-testid="start-call-btn"
                >
                  <Phone className="w-5 h-5" /> Start Call
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // In-call view
  return (
    <div className={`${fullscreen ? 'fixed inset-0 z-50 bg-slate-900' : ''}`}>
      <div className={`${fullscreen ? 'h-screen' : 'min-h-[600px]'} flex flex-col`}>
        {/* Video Area */}
        <div className="flex-1 relative bg-slate-900 rounded-lg overflow-hidden">
          {/* Remote Video (main) */}
          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            className="w-full h-full object-cover"
          />
          
          {/* No remote stream placeholder */}
          {!remoteStream && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center text-white">
                <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">Waiting for other participant...</p>
                <p className="text-sm text-slate-400 mt-2">
                  Connection status: {connectionStatus}
                </p>
              </div>
            </div>
          )}

          {/* Local Video (picture-in-picture) */}
          <div className="absolute bottom-4 right-4 w-48 h-36 bg-slate-800 rounded-lg overflow-hidden shadow-lg border-2 border-slate-700">
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            {!videoEnabled && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-800">
                <VideoOff className="w-8 h-8 text-slate-400" />
              </div>
            )}
          </div>

          {/* Top Bar */}
          <div className="absolute top-4 left-4 right-4 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Badge className="bg-red-600 text-white px-3 py-1">
                <span className="animate-pulse mr-2">●</span> LIVE
              </Badge>
              <Badge variant="outline" className="bg-black/50 text-white border-0">
                {participants.length} participant(s)
              </Badge>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/20"
              onClick={() => setFullscreen(!fullscreen)}
            >
              {fullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </Button>
          </div>

          {/* Patient Info */}
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2">
            <div className="bg-black/50 rounded-lg px-4 py-2 text-white text-center">
              <p className="font-medium">{session?.patient_name}</p>
              <p className="text-sm text-slate-300">{session?.reason || 'Telehealth Visit'}</p>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-slate-800 p-4 flex items-center justify-center gap-4 rounded-b-lg">
          <Button
            variant={audioEnabled ? "outline" : "destructive"}
            size="icon"
            className="w-12 h-12 rounded-full"
            onClick={toggleAudio}
            data-testid="toggle-audio"
          >
            {audioEnabled ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
          </Button>
          
          <Button
            variant={videoEnabled ? "outline" : "destructive"}
            size="icon"
            className="w-12 h-12 rounded-full"
            onClick={toggleVideo}
            data-testid="toggle-video"
          >
            {videoEnabled ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
          </Button>
          
          <Button
            variant={screenSharing ? "default" : "outline"}
            size="icon"
            className="w-12 h-12 rounded-full"
            onClick={toggleScreenShare}
            data-testid="toggle-screen"
          >
            <Monitor className="w-5 h-5" />
          </Button>
          
          <Button
            variant={showChat ? "default" : "outline"}
            size="icon"
            className="w-12 h-12 rounded-full"
            onClick={() => setShowChat(!showChat)}
          >
            <MessageSquare className="w-5 h-5" />
          </Button>
          
          <Button
            variant="destructive"
            size="icon"
            className="w-14 h-14 rounded-full bg-red-600 hover:bg-red-700"
            onClick={endCall}
            data-testid="end-call"
          >
            <PhoneOff className="w-6 h-6" />
          </Button>
        </div>

        {/* Chat Panel */}
        {showChat && (
          <div className="fixed right-4 bottom-24 w-80 bg-white rounded-lg shadow-xl border">
            <div className="p-3 border-b flex items-center justify-between">
              <h3 className="font-medium">Chat</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowChat(false)}>×</Button>
            </div>
            <ScrollArea className="h-64 p-3">
              {chatMessages.length === 0 ? (
                <p className="text-center text-slate-400 text-sm">No messages yet</p>
              ) : (
                <div className="space-y-2">
                  {chatMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`p-2 rounded-lg text-sm ${
                        msg.isOwn || msg.from === user.id
                          ? 'bg-sky-100 ml-8'
                          : 'bg-slate-100 mr-8'
                      }`}
                    >
                      <p>{msg.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
            <div className="p-3 border-t flex gap-2">
              <Input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Type a message..."
                onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
              />
              <Button size="icon" onClick={sendChatMessage}>
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
