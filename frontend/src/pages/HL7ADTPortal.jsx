import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Dialog, DialogContent, DialogDescription, 
  DialogHeader, DialogTitle, DialogFooter 
} from '@/components/ui/dialog';
import { 
  Select, SelectContent, SelectItem, 
  SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { 
  Table, TableBody, TableCell, 
  TableHead, TableHeader, TableRow 
} from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { 
  Activity, RefreshCw, Search, CheckCircle, XCircle, AlertCircle,
  Loader2, FileText, Send, Download, Clock, User, Building2, 
  ArrowUpRight, ArrowDownLeft, Bed, Stethoscope, ClipboardList,
  Network, Settings, Eye, Copy
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

// ADT Event Types with descriptions
const ADT_EVENTS = {
  A01: { name: 'Admit', description: 'Patient admission notification', color: 'bg-green-500' },
  A02: { name: 'Transfer', description: 'Patient transfer notification', color: 'bg-blue-500' },
  A03: { name: 'Discharge', description: 'Patient discharge notification', color: 'bg-amber-500' },
  A04: { name: 'Register', description: 'Patient registration', color: 'bg-sky-500' },
  A05: { name: 'Pre-Admit', description: 'Pre-admission notification', color: 'bg-purple-500' },
  A08: { name: 'Update', description: 'Patient information update', color: 'bg-indigo-500' },
  A11: { name: 'Cancel Admit', description: 'Cancel admission', color: 'bg-red-500' },
  A13: { name: 'Cancel Discharge', description: 'Cancel discharge', color: 'bg-orange-500' },
};

export default function HL7ADTPortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('events');
  
  // Data
  const [adtEvents, setAdtEvents] = useState([]);
  const [hl7Messages, setHl7Messages] = useState([]);
  const [bedCensus, setBedCensus] = useState([]);
  const [stats, setStats] = useState({
    totalEvents: 0,
    todayAdmissions: 0,
    todayDischarges: 0,
    todayTransfers: 0,
    pendingMessages: 0
  });
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [eventFilter, setEventFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('today');
  
  // Dialogs
  const [viewMessageOpen, setViewMessageOpen] = useState(false);
  const [sendMessageOpen, setSendMessageOpen] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(null);
  
  // Forms
  const [newMessage, setNewMessage] = useState({
    event_type: 'A01',
    patient_id: '',
    patient_name: '',
    mrn: '',
    ward: '',
    room: '',
    bed: '',
    notes: ''
  });
  
  const [config, setConfig] = useState({
    hl7_version: '2.5',
    sending_application: 'YACCO_EMR',
    sending_facility: '',
    receiving_application: '',
    receiving_facility: '',
    socket_port: 2575,
    enabled: true
  });
  
  const isITAdmin = user?.role === 'hospital_it_admin' || user?.role === 'hospital_admin';

  // Check role access
  const allowedRoles = ['hospital_it_admin', 'nursing_supervisor', 'physician', 'nurse', 'floor_supervisor', 'hospital_admin'];
  const hasAccess = user && allowedRoles.includes(user.role);

  const fetchData = useCallback(async () => {
    if (!hasAccess) return;
    
    try {
      setLoading(true);
      const token = localStorage.getItem('yacco_token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Fetch ADT events
      const eventsRes = await fetch(`${API_BASE}/api/hl7/adt/events?limit=100`, { headers });
      if (eventsRes.ok) {
        const eventsData = await eventsRes.json();
        setAdtEvents(eventsData);
      }
      
      // Fetch HL7 messages
      const messagesRes = await fetch(`${API_BASE}/api/hl7/messages?limit=50`, { headers });
      if (messagesRes.ok) {
        const messagesData = await messagesRes.json();
        setHl7Messages(messagesData);
      }
      
      // Fetch bed census
      const bedsRes = await fetch(`${API_BASE}/api/hl7/beds`, { headers });
      if (bedsRes.ok) {
        const bedsData = await bedsRes.json();
        setBedCensus(bedsData);
      }
      
      // Calculate stats
      const today = new Date().toISOString().split('T')[0];
      const todayEvents = adtEvents.filter(e => e.created_at?.startsWith(today));
      setStats({
        totalEvents: adtEvents.length,
        todayAdmissions: todayEvents.filter(e => e.event_type === 'A01').length,
        todayDischarges: todayEvents.filter(e => e.event_type === 'A03').length,
        todayTransfers: todayEvents.filter(e => e.event_type === 'A02').length,
        pendingMessages: hl7Messages.filter(m => m.status === 'pending').length
      });
      
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to fetch HL7/ADT data');
    } finally {
      setLoading(false);
    }
  }, [hasAccess]);

  useEffect(() => {
    fetchData();
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleViewMessage = (message) => {
    setSelectedMessage(message);
    setViewMessageOpen(true);
  };

  const handleCopyMessage = (message) => {
    navigator.clipboard.writeText(message.raw_message || '');
    toast.success('HL7 message copied to clipboard');
  };

  const handleSendMessage = async () => {
    try {
      const token = localStorage.getItem('yacco_token');
      
      // Create ADT event based on type
      let endpoint = '';
      let payload = {};
      
      switch (newMessage.event_type) {
        case 'A01':
          endpoint = '/api/hl7/adt/admit';
          payload = {
            patient_id: newMessage.patient_id,
            patient_class: 'I',
            ward: newMessage.ward,
            room: newMessage.room,
            bed: newMessage.bed,
            admitting_diagnosis: newMessage.notes
          };
          break;
        case 'A02':
          endpoint = '/api/hl7/adt/transfer';
          payload = {
            patient_id: newMessage.patient_id,
            from_location: 'current',
            to_ward: newMessage.ward,
            to_room: newMessage.room,
            to_bed: newMessage.bed,
            reason: newMessage.notes
          };
          break;
        case 'A03':
          endpoint = '/api/hl7/adt/discharge';
          payload = {
            patient_id: newMessage.patient_id,
            discharge_disposition: 'home',
            discharge_diagnosis: newMessage.notes
          };
          break;
        default:
          toast.error('Invalid event type');
          return;
      }
      
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        toast.success(`${ADT_EVENTS[newMessage.event_type].name} event created successfully`);
        setSendMessageOpen(false);
        setNewMessage({
          event_type: 'A01',
          patient_id: '',
          patient_name: '',
          mrn: '',
          ward: '',
          room: '',
          bed: '',
          notes: ''
        });
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to create ADT event');
      }
    } catch (error) {
      console.error('Error creating ADT event:', error);
      toast.error('Failed to create ADT event');
    }
  };

  const filteredEvents = adtEvents.filter(event => {
    if (eventFilter !== 'all' && event.event_type !== eventFilter) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        event.patient_name?.toLowerCase().includes(query) ||
        event.mrn?.toLowerCase().includes(query) ||
        event.location?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  if (!hasAccess) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="max-w-md">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="w-12 h-12 mx-auto text-amber-500 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Access Restricted</h3>
            <p className="text-muted-foreground">
              HL7/ADT module is available for IT Admins, Nursing Supervisors, Physicians, Nurses, and Floor Supervisors.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="hl7-adt-portal">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Network className="w-6 h-6 text-sky-500" />
            HL7 ADT Integration
          </h1>
          <p className="text-slate-500 mt-1">
            Admission, Discharge, and Transfer messaging system
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            onClick={fetchData}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {isITAdmin && (
            <>
              <Button 
                variant="outline"
                onClick={() => setConfigOpen(true)}
              >
                <Settings className="w-4 h-4 mr-2" />
                Configure
              </Button>
              <Button onClick={() => setSendMessageOpen(true)}>
                <Send className="w-4 h-4 mr-2" />
                Create ADT Event
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Events</p>
                <p className="text-2xl font-bold">{stats.totalEvents}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-100">
                <Activity className="w-5 h-5 text-slate-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Today Admissions</p>
                <p className="text-2xl font-bold text-green-600">{stats.todayAdmissions}</p>
              </div>
              <div className="p-3 rounded-xl bg-green-100">
                <ArrowDownLeft className="w-5 h-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Today Discharges</p>
                <p className="text-2xl font-bold text-amber-600">{stats.todayDischarges}</p>
              </div>
              <div className="p-3 rounded-xl bg-amber-100">
                <ArrowUpRight className="w-5 h-5 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Today Transfers</p>
                <p className="text-2xl font-bold text-blue-600">{stats.todayTransfers}</p>
              </div>
              <div className="p-3 rounded-xl bg-blue-100">
                <Bed className="w-5 h-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Pending Messages</p>
                <p className="text-2xl font-bold text-purple-600">{stats.pendingMessages}</p>
              </div>
              <div className="p-3 rounded-xl bg-purple-100">
                <Clock className="w-5 h-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <CardTitle>ADT Events & Messages</CardTitle>
              <CardDescription>
                View and manage HL7 v2 ADT messages for patient flow
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Search patient, MRN..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 w-[200px]"
                />
              </div>
              <Select value={eventFilter} onValueChange={setEventFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Event Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Events</SelectItem>
                  <SelectItem value="A01">Admissions</SelectItem>
                  <SelectItem value="A02">Transfers</SelectItem>
                  <SelectItem value="A03">Discharges</SelectItem>
                  <SelectItem value="A08">Updates</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="events">ADT Events</TabsTrigger>
              <TabsTrigger value="messages">HL7 Messages</TabsTrigger>
              <TabsTrigger value="census">Bed Census</TabsTrigger>
            </TabsList>

            <TabsContent value="events" className="mt-4">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-sky-500" />
                </div>
              ) : filteredEvents.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Activity className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p>No ADT events found</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Event</TableHead>
                        <TableHead>Patient</TableHead>
                        <TableHead>MRN</TableHead>
                        <TableHead>Location</TableHead>
                        <TableHead>Timestamp</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredEvents.map((event) => (
                        <TableRow key={event.id}>
                          <TableCell>
                            <Badge className={`${ADT_EVENTS[event.event_type]?.color || 'bg-slate-500'} text-white`}>
                              {event.event_type} - {ADT_EVENTS[event.event_type]?.name || 'Unknown'}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-medium">{event.patient_name}</TableCell>
                          <TableCell>{event.mrn}</TableCell>
                          <TableCell>{event.location?.replace(/\^/g, ' - ')}</TableCell>
                          <TableCell>
                            {event.created_at ? new Date(event.created_at).toLocaleString() : '-'}
                          </TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm">
                              <Eye className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </TabsContent>

            <TabsContent value="messages" className="mt-4">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-sky-500" />
                </div>
              ) : hl7Messages.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p>No HL7 messages found</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead>Event</TableHead>
                        <TableHead>Sending App</TableHead>
                        <TableHead>Receiving App</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Timestamp</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {hl7Messages.map((msg) => (
                        <TableRow key={msg.id}>
                          <TableCell className="font-medium">{msg.message_type}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{msg.event_type}</Badge>
                          </TableCell>
                          <TableCell>{msg.sending_application}</TableCell>
                          <TableCell>{msg.receiving_application}</TableCell>
                          <TableCell>
                            <Badge variant={msg.status === 'generated' ? 'default' : msg.status === 'error' ? 'destructive' : 'secondary'}>
                              {msg.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {msg.created_at ? new Date(msg.created_at).toLocaleString() : '-'}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleViewMessage(msg)}
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleCopyMessage(msg)}
                              >
                                <Copy className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </TabsContent>

            <TabsContent value="census" className="mt-4">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-sky-500" />
                </div>
              ) : bedCensus.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Bed className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p>No occupied beds found</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Patient</TableHead>
                        <TableHead>Ward</TableHead>
                        <TableHead>Room</TableHead>
                        <TableHead>Bed</TableHead>
                        <TableHead>Admitted</TableHead>
                        <TableHead>Attending</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bedCensus.map((bed) => (
                        <TableRow key={bed.id}>
                          <TableCell className="font-medium">{bed.patient_name}</TableCell>
                          <TableCell>{bed.ward}</TableCell>
                          <TableCell>{bed.room}</TableCell>
                          <TableCell>{bed.bed}</TableCell>
                          <TableCell>
                            {bed.admit_datetime ? new Date(bed.admit_datetime).toLocaleDateString() : '-'}
                          </TableCell>
                          <TableCell>{bed.attending_physician || '-'}</TableCell>
                          <TableCell>
                            <Badge variant={bed.status === 'occupied' ? 'default' : 'secondary'}>
                              {bed.status}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* View Message Dialog */}
      <Dialog open={viewMessageOpen} onOpenChange={setViewMessageOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>HL7 Message Details</DialogTitle>
            <DialogDescription>
              Raw HL7 v2 message content
            </DialogDescription>
          </DialogHeader>
          {selectedMessage && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Message Type</Label>
                  <p className="font-medium">{selectedMessage.message_type}^{selectedMessage.event_type}</p>
                </div>
                <div>
                  <Label>Control ID</Label>
                  <p className="font-medium">{selectedMessage.message_control_id}</p>
                </div>
                <div>
                  <Label>Sending Application</Label>
                  <p className="font-medium">{selectedMessage.sending_application}</p>
                </div>
                <div>
                  <Label>Receiving Application</Label>
                  <p className="font-medium">{selectedMessage.receiving_application}</p>
                </div>
              </div>
              <Separator />
              <div>
                <Label>Raw Message</Label>
                <pre className="mt-2 p-4 bg-slate-900 text-green-400 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap font-mono">
                  {selectedMessage.raw_message?.replace(/\r/g, '\n') || 'No message content'}
                </pre>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewMessageOpen(false)}>
              Close
            </Button>
            {selectedMessage && (
              <Button onClick={() => handleCopyMessage(selectedMessage)}>
                <Copy className="w-4 h-4 mr-2" />
                Copy Message
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create ADT Event Dialog - IT Admin Only */}
      {isITAdmin && (
        <Dialog open={sendMessageOpen} onOpenChange={setSendMessageOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Create ADT Event</DialogTitle>
              <DialogDescription>
                Generate and send an HL7 ADT message
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Event Type</Label>
                <Select 
                  value={newMessage.event_type} 
                  onValueChange={(v) => setNewMessage(prev => ({ ...prev, event_type: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="A01">A01 - Admit Patient</SelectItem>
                    <SelectItem value="A02">A02 - Transfer Patient</SelectItem>
                    <SelectItem value="A03">A03 - Discharge Patient</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Patient ID</Label>
                <Input
                  value={newMessage.patient_id}
                  onChange={(e) => setNewMessage(prev => ({ ...prev, patient_id: e.target.value }))}
                  placeholder="Enter patient ID"
                />
              </div>
              {newMessage.event_type !== 'A03' && (
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <Label>Ward</Label>
                    <Input
                      value={newMessage.ward}
                      onChange={(e) => setNewMessage(prev => ({ ...prev, ward: e.target.value }))}
                      placeholder="ICU"
                    />
                  </div>
                  <div>
                    <Label>Room</Label>
                    <Input
                      value={newMessage.room}
                      onChange={(e) => setNewMessage(prev => ({ ...prev, room: e.target.value }))}
                      placeholder="101"
                    />
                  </div>
                  <div>
                    <Label>Bed</Label>
                    <Input
                      value={newMessage.bed}
                      onChange={(e) => setNewMessage(prev => ({ ...prev, bed: e.target.value }))}
                      placeholder="A"
                    />
                  </div>
                </div>
              )}
              <div>
                <Label>Notes / Diagnosis</Label>
                <Textarea
                  value={newMessage.notes}
                  onChange={(e) => setNewMessage(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="Enter diagnosis or notes..."
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSendMessageOpen(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleSendMessage}
                disabled={!newMessage.patient_id}
              >
                <Send className="w-4 h-4 mr-2" />
                Create Event
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Configuration Dialog - IT Admin Only */}
      {isITAdmin && (
        <Dialog open={configOpen} onOpenChange={setConfigOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>HL7 Configuration</DialogTitle>
              <DialogDescription>
                Configure HL7 v2 messaging settings
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <Alert>
                <AlertCircle className="w-4 h-4" />
                <AlertDescription>
                  These settings control how HL7 messages are generated and sent. 
                  Contact your IT department before making changes.
                </AlertDescription>
              </Alert>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>HL7 Version</Label>
                  <Select value={config.hl7_version}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2.3">v2.3</SelectItem>
                      <SelectItem value="2.4">v2.4</SelectItem>
                      <SelectItem value="2.5">v2.5</SelectItem>
                      <SelectItem value="2.5.1">v2.5.1</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Socket Port</Label>
                  <Input 
                    type="number" 
                    value={config.socket_port}
                    onChange={(e) => setConfig(prev => ({ ...prev, socket_port: parseInt(e.target.value) }))}
                  />
                </div>
              </div>
              <div>
                <Label>Sending Application</Label>
                <Input 
                  value={config.sending_application}
                  onChange={(e) => setConfig(prev => ({ ...prev, sending_application: e.target.value }))}
                />
              </div>
              <div>
                <Label>Sending Facility</Label>
                <Input 
                  value={config.sending_facility}
                  onChange={(e) => setConfig(prev => ({ ...prev, sending_facility: e.target.value }))}
                  placeholder="Hospital name or ID"
                />
              </div>
              <div>
                <Label>Receiving Application</Label>
                <Input 
                  value={config.receiving_application}
                  onChange={(e) => setConfig(prev => ({ ...prev, receiving_application: e.target.value }))}
                  placeholder="External system name"
                />
              </div>
              <div>
                <Label>Receiving Facility</Label>
                <Input 
                  value={config.receiving_facility}
                  onChange={(e) => setConfig(prev => ({ ...prev, receiving_facility: e.target.value }))}
                  placeholder="External facility name"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setConfigOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => {
                toast.success('Configuration saved');
                setConfigOpen(false);
              }}>
                Save Configuration
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
