import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
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
import { formatDate, formatDateTime, getStatusColor } from '@/lib/utils';
import { 
  Activity, Heart, Pill, AlertTriangle, FileText, Calendar,
  MessageSquare, Video, RefreshCw, User, LogOut, Send, Clock
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

export default function MyChartPortal() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [activeTab, setActiveTab] = useState('records');
  
  // Data states
  const [healthRecords, setHealthRecords] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [refillRequests, setRefillRequests] = useState([]);
  const [providers, setProviders] = useState([]);
  const [labResults, setLabResults] = useState([]);
  
  // Form states
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ 
    patient_id: '', email: '', password: '', date_of_birth: '' 
  });
  const [messageForm, setMessageForm] = useState({ subject: '', body: '', provider_id: '' });
  const [showRegister, setShowRegister] = useState(false);
  const [messageDialogOpen, setMessageDialogOpen] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('mychart_token');
    const savedUser = localStorage.getItem('mychart_user');
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setIsLoggedIn(true);
    }
    setLoading(false);
  }, []);

  const fetchData = useCallback(async () => {
    if (!token) return;
    
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [recordsRes, apptsRes, messagesRes, refillsRes, providersRes, resultsRes] = await Promise.all([
        fetch(`${API_BASE}/api/mychart/records`, { headers }),
        fetch(`${API_BASE}/api/mychart/appointments`, { headers }),
        fetch(`${API_BASE}/api/mychart/messages`, { headers }),
        fetch(`${API_BASE}/api/mychart/refills`, { headers }),
        fetch(`${API_BASE}/api/mychart/providers`, { headers }),
        fetch(`${API_BASE}/api/mychart/results`, { headers }),
      ]);
      
      if (recordsRes.ok) setHealthRecords(await recordsRes.json());
      if (apptsRes.ok) setAppointments(await apptsRes.json());
      if (messagesRes.ok) setMessages(await messagesRes.json());
      if (refillsRes.ok) setRefillRequests(await refillsRes.json());
      if (providersRes.ok) setProviders(await providersRes.json());
      if (resultsRes.ok) setLabResults(await resultsRes.json());
    } catch (err) {
      console.error('Error fetching MyChart data:', err);
    }
  }, [token]);

  useEffect(() => {
    if (isLoggedIn && token) {
      fetchData();
    }
  }, [isLoggedIn, token, fetchData]);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/mychart/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      });
      
      if (res.ok) {
        const data = await res.json();
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem('mychart_token', data.token);
        localStorage.setItem('mychart_user', JSON.stringify(data.user));
        setIsLoggedIn(true);
        toast.success('Welcome to MyChart!');
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Login failed');
      }
    } catch (err) {
      toast.error('Connection error');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/mychart/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerForm)
      });
      
      if (res.ok) {
        const data = await res.json();
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem('mychart_token', data.token);
        localStorage.setItem('mychart_user', JSON.stringify(data.user));
        setIsLoggedIn(true);
        toast.success('Welcome to MyChart!');
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Registration failed');
      }
    } catch (err) {
      toast.error('Connection error');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('mychart_token');
    localStorage.removeItem('mychart_user');
    setToken(null);
    setUser(null);
    setIsLoggedIn(false);
    toast.success('Logged out');
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/mychart/messages`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(messageForm)
      });
      
      if (res.ok) {
        toast.success('Message sent');
        setMessageDialogOpen(false);
        setMessageForm({ subject: '', body: '', provider_id: '' });
        fetchData();
      } else {
        toast.error('Failed to send message');
      }
    } catch (err) {
      toast.error('Connection error');
    }
  };

  const handleRequestRefill = async (medicationId, medicationName) => {
    try {
      const res = await fetch(`${API_BASE}/api/mychart/refills`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ medication_id: medicationId })
      });
      
      if (res.ok) {
        toast.success(`Refill requested for ${medicationName}`);
        fetchData();
      } else {
        toast.error('Failed to request refill');
      }
    } catch (err) {
      toast.error('Connection error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sky-50 to-blue-100">
        <Activity className="w-12 h-12 text-sky-600 animate-pulse" />
      </div>
    );
  }

  // Login/Register View
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sky-50 to-blue-100 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center">
                <Heart className="w-5 h-5 text-white" />
              </div>
              <span className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
                MyChart
              </span>
            </div>
            <CardDescription>Access your health records, appointments, and more</CardDescription>
          </CardHeader>
          <CardContent>
            {!showRegister ? (
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input 
                    type="email" 
                    value={loginForm.email}
                    onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Password</Label>
                  <Input 
                    type="password"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    required
                  />
                </div>
                <Button type="submit" className="w-full bg-sky-600 hover:bg-sky-700">Sign In</Button>
                <p className="text-center text-sm text-slate-500">
                  New to MyChart?{' '}
                  <button type="button" onClick={() => setShowRegister(true)} className="text-sky-600 hover:underline">
                    Register
                  </button>
                </p>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-2">
                  <Label>Medical Record Number (MRN)</Label>
                  <Input 
                    value={registerForm.patient_id}
                    onChange={(e) => setRegisterForm({ ...registerForm, patient_id: e.target.value })}
                    placeholder="Enter your MRN"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Date of Birth (for verification)</Label>
                  <Input 
                    type="date"
                    value={registerForm.date_of_birth}
                    onChange={(e) => setRegisterForm({ ...registerForm, date_of_birth: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input 
                    type="email"
                    value={registerForm.email}
                    onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Create Password</Label>
                  <Input 
                    type="password"
                    value={registerForm.password}
                    onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                    required
                  />
                </div>
                <Button type="submit" className="w-full bg-sky-600 hover:bg-sky-700">Register</Button>
                <p className="text-center text-sm text-slate-500">
                  Already have an account?{' '}
                  <button type="button" onClick={() => setShowRegister(false)} className="text-sky-600 hover:underline">
                    Sign In
                  </button>
                </p>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main Portal View
  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 to-blue-100">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
              MyChart
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600">Welcome, {user?.first_name}</span>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-1" /> Sign Out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-5 w-full max-w-2xl mb-6">
            <TabsTrigger value="records">Health Records</TabsTrigger>
            <TabsTrigger value="appointments">Appointments</TabsTrigger>
            <TabsTrigger value="messages">Messages</TabsTrigger>
            <TabsTrigger value="medications">Medications</TabsTrigger>
            <TabsTrigger value="results">Lab Results</TabsTrigger>
          </TabsList>

          {/* Health Records Tab */}
          <TabsContent value="records">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Vitals */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-sky-600" /> Recent Vitals
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {healthRecords?.vitals?.length > 0 ? (
                    <div className="space-y-3">
                      {healthRecords.vitals.slice(0, 3).map((v, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-xs text-slate-500 mb-2">{formatDateTime(v.recorded_at)}</p>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {v.blood_pressure_systolic && (
                              <div>BP: {v.blood_pressure_systolic}/{v.blood_pressure_diastolic} mmHg</div>
                            )}
                            {v.heart_rate && <div>HR: {v.heart_rate} bpm</div>}
                            {v.temperature && <div>Temp: {v.temperature}°F</div>}
                            {v.oxygen_saturation && <div>SpO2: {v.oxygen_saturation}%</div>}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-center py-4">No vitals recorded</p>
                  )}
                </CardContent>
              </Card>

              {/* Problems */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-amber-600" /> Health Conditions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {healthRecords?.problems?.length > 0 ? (
                    <div className="space-y-2">
                      {healthRecords.problems.map((p, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                          <span>{p.description}</span>
                          <Badge className={getStatusColor(p.status)}>{p.status}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-center py-4">No conditions on file</p>
                  )}
                </CardContent>
              </Card>

              {/* Allergies */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-600" /> Allergies
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {healthRecords?.allergies?.length > 0 ? (
                    <div className="space-y-2">
                      {healthRecords.allergies.map((a, idx) => (
                        <div key={idx} className="p-2 bg-red-50 rounded border border-red-100">
                          <p className="font-medium text-red-900">{a.allergen}</p>
                          <p className="text-sm text-red-700">Reaction: {a.reaction}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-center py-4">No known allergies</p>
                  )}
                </CardContent>
              </Card>

              {/* Demographics */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="w-5 h-5 text-slate-600" /> My Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {healthRecords?.patient ? (
                    <div className="space-y-2 text-sm">
                      <p><span className="text-slate-500">Name:</span> {healthRecords.patient.first_name} {healthRecords.patient.last_name}</p>
                      <p><span className="text-slate-500">DOB:</span> {formatDate(healthRecords.patient.date_of_birth)}</p>
                      <p><span className="text-slate-500">MRN:</span> {healthRecords.patient.mrn}</p>
                      <p><span className="text-slate-500">Phone:</span> {healthRecords.patient.phone || 'Not provided'}</p>
                      <p><span className="text-slate-500">Email:</span> {healthRecords.patient.email || 'Not provided'}</p>
                    </div>
                  ) : (
                    <Skeleton className="h-32 w-full" />
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Appointments Tab */}
          <TabsContent value="appointments">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>My Appointments</CardTitle>
                <Button variant="outline" className="gap-2">
                  <Calendar className="w-4 h-4" /> Request Appointment
                </Button>
              </CardHeader>
              <CardContent>
                {appointments.length > 0 ? (
                  <div className="space-y-3">
                    {appointments.map((appt) => (
                      <div key={appt.id} className="p-4 rounded-lg border border-slate-200">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{appt.appointment_type}</p>
                            <p className="text-sm text-slate-500">{appt.provider_name || 'Provider'}</p>
                            <p className="text-sm text-slate-600 mt-1">
                              <Clock className="w-3 h-3 inline mr-1" />
                              {formatDate(appt.date)} at {appt.start_time}
                            </p>
                          </div>
                          <Badge className={getStatusColor(appt.status)}>{appt.status}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-center py-8">No upcoming appointments</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Messages Tab */}
          <TabsContent value="messages">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Messages</CardTitle>
                <Dialog open={messageDialogOpen} onOpenChange={setMessageDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="gap-2 bg-sky-600 hover:bg-sky-700">
                      <Send className="w-4 h-4" /> New Message
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Send Message to Care Team</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleSendMessage} className="space-y-4 mt-4">
                      <div className="space-y-2">
                        <Label>To (Provider)</Label>
                        <Select value={messageForm.provider_id} onValueChange={(v) => setMessageForm({ ...messageForm, provider_id: v })}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select provider" />
                          </SelectTrigger>
                          <SelectContent>
                            {providers.map((p) => (
                              <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Subject</Label>
                        <Input 
                          value={messageForm.subject}
                          onChange={(e) => setMessageForm({ ...messageForm, subject: e.target.value })}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Message</Label>
                        <Textarea 
                          value={messageForm.body}
                          onChange={(e) => setMessageForm({ ...messageForm, body: e.target.value })}
                          rows={5}
                          required
                        />
                      </div>
                      <Button type="submit" className="w-full">Send Message</Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                {messages.length > 0 ? (
                  <div className="space-y-3">
                    {messages.map((msg) => (
                      <div key={msg.id} className={`p-4 rounded-lg border ${msg.is_read ? 'border-slate-200' : 'border-sky-300 bg-sky-50'}`}>
                        <div className="flex items-center justify-between mb-2">
                          <p className="font-medium">{msg.subject}</p>
                          <span className="text-xs text-slate-500">{formatDateTime(msg.created_at)}</span>
                        </div>
                        <p className="text-sm text-slate-600 line-clamp-2">{msg.body}</p>
                        <p className="text-xs text-slate-400 mt-2">
                          {msg.is_from_patient ? 'Sent by you' : `From: ${msg.provider_name || 'Care Team'}`}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-center py-8">No messages</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Medications Tab */}
          <TabsContent value="medications">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Pill className="w-5 h-5 text-blue-600" /> My Medications
                </CardTitle>
                <CardDescription>Request refills for your medications</CardDescription>
              </CardHeader>
              <CardContent>
                {healthRecords?.medications?.length > 0 ? (
                  <div className="space-y-3">
                    {healthRecords.medications.map((med) => (
                      <div key={med.id} className="p-4 rounded-lg border border-slate-200 flex items-center justify-between">
                        <div>
                          <p className="font-medium text-slate-900">{med.name}</p>
                          <p className="text-sm text-slate-500">{med.dosage} - {med.frequency}</p>
                          <p className="text-xs text-slate-400">Route: {med.route}</p>
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="gap-1"
                          onClick={() => handleRequestRefill(med.id, med.name)}
                        >
                          <RefreshCw className="w-3 h-3" /> Request Refill
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-center py-8">No active medications</p>
                )}

                {refillRequests.length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-medium text-slate-900 mb-3">Recent Refill Requests</h4>
                    <div className="space-y-2">
                      {refillRequests.map((req) => (
                        <div key={req.id} className="p-3 bg-slate-50 rounded-lg flex items-center justify-between">
                          <div>
                            <p className="font-medium">{req.medication_name}</p>
                            <p className="text-xs text-slate-500">{formatDateTime(req.created_at)}</p>
                          </div>
                          <Badge className={getStatusColor(req.status)}>{req.status}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Lab Results Tab */}
          <TabsContent value="results">
            <Card>
              <CardHeader>
                <CardTitle>Lab Results</CardTitle>
                <CardDescription>View your completed lab test results</CardDescription>
              </CardHeader>
              <CardContent>
                {labResults.length > 0 ? (
                  <div className="space-y-3">
                    {labResults.map((result) => (
                      <div key={result.id} className="p-4 rounded-lg border border-slate-200">
                        <div className="flex items-center justify-between mb-2">
                          <p className="font-medium text-slate-900">{result.description}</p>
                          <span className="text-sm text-slate-500">{formatDate(result.completed_at || result.created_at)}</span>
                        </div>
                        {result.result && (
                          <div className="p-3 bg-slate-50 rounded mt-2">
                            <p className="text-sm">{result.result}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-center py-8">No lab results available</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
